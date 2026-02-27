"""OTT Content Metadata MCP Server.

Read-only MCP server exposing the OTT platform's content metadata database
to AI agents via stdio transport.
"""

import os
import sys
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from mcp.server.fastmcp import Context, FastMCP
from sqlalchemy import case, func, literal_column, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from ott_mcp.db import settings as mcp_settings

# ---------------------------------------------------------------------------
# Backend model imports — requires sys.path setup
# ---------------------------------------------------------------------------

# Set dummy env vars so importing app.config.Settings doesn't fail
# (the MCP server never uses JWT or Redis)
os.environ.setdefault("JWT_SECRET", "mcp-server-dummy-not-used")

# Add backend to sys.path so app.models.* imports work
sys.path.insert(0, os.path.abspath(mcp_settings.ott_backend_path))

from app.models.catalog import Episode, Genre, Season, Title, TitleCast, TitleGenre  # noqa: E402
from app.models.entitlement import ContentPackage, PackageContent, TitleOffer  # noqa: E402
from app.models.epg import Channel, ScheduleEntry  # noqa: E402
from app.models.analytics import AnalyticsEvent  # noqa: E402
from app.models.embedding import ContentEmbedding  # noqa: E402
from app.models.tstv import TSTVSession, Recording  # noqa: E402
from app.models.viewing import Rating, WatchlistItem  # noqa: E402
from app.services import catalog_service, epg_service  # noqa: E402

from ott_mcp.db import async_session_factory, engine  # noqa: E402
from ott_mcp.serializers import to_json  # noqa: E402


# ---------------------------------------------------------------------------
# Lifespan & context
# ---------------------------------------------------------------------------


@dataclass
class AppContext:
    session_factory: async_sessionmaker


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage database engine lifecycle."""
    try:
        yield AppContext(session_factory=async_session_factory)
    finally:
        await engine.dispose()


# ---------------------------------------------------------------------------
# FastMCP server instance
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "OTT Content Metadata",
    instructions=(
        "Read-only access to the OTT streaming platform content catalog, "
        "EPG (channels & schedule), and entitlements. "
        "Use list_genres first to get valid genre slugs for filtering."
    ),
    lifespan=app_lifespan,
)


# ---------------------------------------------------------------------------
# Helper: get session from context
# ---------------------------------------------------------------------------


def _get_session_factory(ctx: Context) -> async_sessionmaker:
    app_ctx: AppContext = ctx.request_context.lifespan_context
    return app_ctx.session_factory


def _serialize_title_summary(t: Title) -> dict:
    """Serialize a Title to a compact summary dict."""
    return {
        "id": str(t.id),
        "title": t.title,
        "title_type": t.title_type,
        "synopsis_short": t.synopsis_short,
        "release_year": t.release_year,
        "duration_minutes": t.duration_minutes,
        "age_rating": t.age_rating,
        "genres": [tg.genre.name for tg in t.genres] if t.genres else [],
        "poster_url": t.poster_url,
        "is_featured": t.is_featured,
    }


def _serialize_schedule_entry(e: ScheduleEntry) -> dict:
    """Serialize a ScheduleEntry to a dict."""
    return {
        "id": str(e.id),
        "channel_id": str(e.channel_id),
        "title": e.title,
        "synopsis": e.synopsis,
        "genre": e.genre,
        "start_time": e.start_time.isoformat() if e.start_time else None,
        "end_time": e.end_time.isoformat() if e.end_time else None,
        "age_rating": e.age_rating,
        "is_new": e.is_new,
        "is_repeat": e.is_repeat,
        "catchup_eligible": e.catchup_eligible,
        "startover_eligible": e.startover_eligible,
    }


# ---------------------------------------------------------------------------
# Resources (FR-009)
# ---------------------------------------------------------------------------


@mcp.resource("content://schema")
def get_content_schema() -> str:
    """Database schema reference for the OTT content metadata tables."""
    return """# OTT Platform Content Schema

## Catalog
- **titles**: id (UUID), title (str), title_type (movie|series), synopsis_short (text),
  synopsis_long (text), ai_description (text), release_year (int), duration_minutes (int),
  age_rating (str), country_of_origin (str), language (str), poster_url (str),
  landscape_url (str), logo_url (str), hls_manifest_url (str), is_featured (bool),
  is_educational (bool), mood_tags (text[]), theme_tags (text[]), created_at (timestamptz)
- **genres**: id (UUID), name (str), slug (str)
- **title_genres**: title_id (FK), genre_id (FK), is_primary (bool) — M:M join
- **title_cast**: id (UUID), title_id (FK), person_name (str),
  role (actor|director|writer), character_name (str), sort_order (int)
- **seasons**: id (UUID), title_id (FK), season_number (int), name (str), synopsis (text)
- **episodes**: id (UUID), season_id (FK), episode_number (int), title (str),
  synopsis (text), duration_minutes (int), hls_manifest_url (str)

## EPG (Linear TV)
- **channels**: id (UUID), name (str), channel_number (int), logo_url (str),
  genre (str), is_hd (bool), hls_live_url (str), tstv_enabled (bool),
  startover_enabled (bool), catchup_enabled (bool), catchup_window_hours (int)
- **schedule_entries**: id (UUID), channel_id (FK), title (str), synopsis (text),
  genre (str), start_time (timestamptz), end_time (timestamptz), age_rating (str),
  is_new (bool), is_repeat (bool), series_title (str), season_number (int),
  episode_number (int), catchup_eligible (bool), startover_eligible (bool),
  series_id (str)

## Entitlements
- **content_packages**: id (UUID), name (str), description (text),
  tier (basic|standard|premium), max_streams (int), price_cents (int), currency (str)
- **title_offers**: id (UUID), title_id (FK), offer_type (rent|buy|free),
  price_cents (int), currency (str), rental_window_hours (int), is_active (bool)
- **package_contents**: package_id (FK), content_type (vod_title|channel), content_id (UUID)

## Analytics
- **analytics_events**: id (UUID), event_type (play_start|play_pause|play_complete|browse|search),
  title_id (FK), service_type (Linear|VoD|SVoD|TSTV|Catch_up|Cloud_PVR),
  user_id (FK), profile_id (FK), region (str), occurred_at (timestamptz),
  duration_seconds (int), watch_percentage (int), extra_data (jsonb)

## Viewing & Engagement
- **ratings**: profile_id (FK), title_id (FK), rating (-1 or 1 = thumbs down/up)
- **watchlist**: profile_id (FK), title_id (FK), added_at (timestamptz)

## TSTV & PVR
- **tstv_sessions**: id, user_id (FK), channel_id (str), schedule_entry_id (FK),
  session_type (startover|catchup), started_at, last_position_s, completed (bool)
- **recordings**: id, user_id (FK), schedule_entry_id (FK), channel_id (str),
  requested_at, status (pending|recording|completed|failed)

## AI / Embeddings
- **content_embeddings**: title_id (FK), embedding (vector 384d), model_version (str)
"""


@mcp.resource("content://tools-guide")
def get_tools_guide() -> str:
    """Guide for using the OTT content MCP tools effectively."""
    return """# How to Use the OTT Content MCP Tools

## Finding Content
- Use `list_genres` first to get valid genre slugs for filtering
- Use `search_titles` for keyword-based content discovery (matches title, synopsis, cast)
- Use `list_titles` with genre/type filters for structured browsing
- Use `browse_titles` for advanced filtering: age_rating, language, country, educational, mood/theme tags
- Use `get_title` with a UUID for full detail on any title (cast, seasons, episodes)
- Use `get_featured_titles` to see hero banner content

## Mood & Theme Discovery
- Use `list_mood_tags` to see all mood tags with counts (e.g., "gritty", "epic")
- Use `list_theme_tags` to see all theme tags with counts (e.g., "justice", "family")
- Use `browse_titles` with mood_tag or theme_tag to filter by these tags

## EPG / Linear TV
- Use `list_channels` to see all available channels with TSTV capabilities
- Use `get_schedule` with a channel_id and date for the program guide
- Use `get_now_playing` to see what's currently on across all channels
- Use `search_schedule` to find when a specific show airs across all channels
- Use `get_catchup_available` to see programs still available on catch-up TV

## Cast & Crew
- Use `search_cast` to find actors, directors, or writers by name
- Use `get_person_titles` to get a person's filmography (all titles they appear in)
- Filter by role: "actor", "director", or "writer"

## Packages & Entitlements
- Use `get_packages` to see all content packages with pricing and stream limits
- Use `get_package_contents` to see which titles and channels are in a specific package
- Use `get_title_offers` to understand TVOD pricing and SVOD inclusion for a title

## Analytics & Engagement
- Use `get_title_popularity` to see most-watched titles over a period
- Use `get_service_type_stats` to see play counts by service type (Linear, VoD, TSTV, etc.)
- Use `get_title_ratings` to see audience thumbs up/down for a specific title
- Use `get_most_wishlisted` to see titles with the most watchlist additions

## Operational Health
- Use `get_embedding_status` to check vector embedding coverage for recommendations
- Use `get_tstv_stats` to see Start Over / Catch-up session counts and completion rates
- Use `get_recording_stats` to see Cloud PVR recording counts by status
- Use `get_catalog_stats` for an overview of the content library

## IDs and Filtering
- All entity IDs are UUIDs. Use IDs from one tool's output in another tool's input.
- Genre slugs (e.g., "action", "drama") are used for filtering, not UUIDs.
- Dates for `get_schedule` use YYYY-MM-DD format or "today".
"""


# ---------------------------------------------------------------------------
# US1: Catalog Tools (T007-T011)
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_genres(ctx: Context) -> list[dict]:
    """List all content genres with their slugs (for use as filters in other tools)."""
    session_factory = _get_session_factory(ctx)
    try:
        async with session_factory() as db:
            genres = await catalog_service.get_genres(db)
            return [{"name": g.name, "slug": g.slug} for g in genres]
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def search_titles(
    query: str,
    ctx: Context,
    title_type: str | None = None,
    genre: str | None = None,
    limit: int = 20,
) -> dict:
    """Search the content catalog by keyword. Matches against title, synopsis, and cast names.

    Args:
        query: Search keyword
        title_type: Optional filter — "movie" or "series"
        genre: Optional filter — genre slug (e.g., "action", "drama"). Use list_genres to see valid slugs.
        limit: Maximum results to return (default 20, max 100)
    """
    limit = min(max(1, limit), 100)
    session_factory = _get_session_factory(ctx)
    try:
        async with session_factory() as db:
            titles, total = await catalog_service.get_titles(
                db,
                search_query=query,
                title_type=title_type,
                genre_slug=genre,
                page_size=limit,
            )
            return {
                "titles": [_serialize_title_summary(t) for t in titles],
                "total": total,
            }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def list_titles(
    ctx: Context,
    page: int = 1,
    page_size: int = 20,
    title_type: str | None = None,
    genre: str | None = None,
) -> dict:
    """Browse the content catalog with pagination.

    Args:
        page: Page number (default 1)
        page_size: Items per page (default 20, max 100)
        title_type: Optional filter — "movie" or "series"
        genre: Optional filter — genre slug
    """
    page_size = min(max(1, page_size), 100)
    page = max(1, page)
    session_factory = _get_session_factory(ctx)
    try:
        async with session_factory() as db:
            titles, total = await catalog_service.get_titles(
                db,
                page=page,
                page_size=page_size,
                title_type=title_type,
                genre_slug=genre,
            )
            return {
                "titles": [_serialize_title_summary(t) for t in titles],
                "total": total,
                "page": page,
                "page_size": page_size,
            }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_title(title_id: str, ctx: Context) -> dict:
    """Get full details for a title by its UUID, including cast, genres, seasons, and episodes.

    Args:
        title_id: The UUID of the title to retrieve
    """
    session_factory = _get_session_factory(ctx)
    try:
        tid = uuid.UUID(title_id)
    except ValueError:
        return {"error": f"Invalid UUID: {title_id}"}

    try:
        async with session_factory() as db:
            title = await catalog_service.get_title_detail(db, tid)
            if title is None:
                return {"error": f"Title not found: {title_id}"}

            result = {
                "id": str(title.id),
                "title": title.title,
                "title_type": title.title_type,
                "synopsis_short": title.synopsis_short,
                "synopsis_long": title.synopsis_long,
                "ai_description": title.ai_description,
                "release_year": title.release_year,
                "duration_minutes": title.duration_minutes,
                "age_rating": title.age_rating,
                "country_of_origin": title.country_of_origin,
                "language": title.language,
                "poster_url": title.poster_url,
                "landscape_url": title.landscape_url,
                "logo_url": title.logo_url,
                "mood_tags": list(title.mood_tags) if title.mood_tags else [],
                "theme_tags": list(title.theme_tags) if title.theme_tags else [],
                "is_featured": title.is_featured,
                "is_educational": title.is_educational,
                "genres": [
                    {
                        "name": tg.genre.name,
                        "slug": tg.genre.slug,
                        "is_primary": tg.is_primary,
                    }
                    for tg in title.genres
                ]
                if title.genres
                else [],
                "cast": [
                    {
                        "person_name": c.person_name,
                        "role": c.role,
                        "character_name": c.character_name,
                        "sort_order": c.sort_order,
                    }
                    for c in sorted(title.cast_members, key=lambda c: c.sort_order or 0)
                ]
                if title.cast_members
                else [],
            }

            # Add seasons/episodes for series
            if title.title_type == "series" and title.seasons:
                result["seasons"] = [
                    {
                        "season_number": s.season_number,
                        "name": s.name,
                        "synopsis": s.synopsis,
                        "episodes": [
                            {
                                "episode_number": ep.episode_number,
                                "title": ep.title,
                                "synopsis": ep.synopsis,
                                "duration_minutes": ep.duration_minutes,
                            }
                            for ep in sorted(s.episodes, key=lambda e: e.episode_number)
                        ]
                        if s.episodes
                        else [],
                    }
                    for s in sorted(title.seasons, key=lambda s: s.season_number)
                ]

            return result
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_featured_titles(ctx: Context) -> list[dict]:
    """Get titles flagged as featured for the hero banner."""
    session_factory = _get_session_factory(ctx)
    try:
        async with session_factory() as db:
            titles = await catalog_service.get_featured_titles(db)
            return [_serialize_title_summary(t) for t in titles]
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# US2: EPG Tools (T012-T014)
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_channels(ctx: Context) -> list[dict]:
    """List all TV channels with channel number, genre, HD status, and TSTV capabilities."""
    session_factory = _get_session_factory(ctx)
    try:
        async with session_factory() as db:
            # get_channels returns dicts via _channel_dict() which omits TSTV fields,
            # so we query Channel ORM objects directly for full data
            result = await db.execute(
                select(Channel).order_by(Channel.channel_number)
            )
            channels = result.scalars().all()
            return [
                {
                    "id": str(ch.id),
                    "name": ch.name,
                    "channel_number": ch.channel_number,
                    "logo_url": ch.logo_url,
                    "genre": ch.genre,
                    "is_hd": ch.is_hd,
                    "tstv_enabled": ch.tstv_enabled,
                    "startover_enabled": ch.startover_enabled,
                    "catchup_enabled": ch.catchup_enabled,
                    "catchup_window_hours": ch.catchup_window_hours,
                }
                for ch in channels
            ]
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_schedule(
    channel_id: str,
    ctx: Context,
    date: str = "today",
) -> list[dict] | dict:
    """Get the EPG schedule for a channel on a given date.

    Args:
        channel_id: The UUID of the channel
        date: Date in YYYY-MM-DD format or "today" (default: "today")
    """
    session_factory = _get_session_factory(ctx)

    try:
        cid = uuid.UUID(channel_id)
    except ValueError:
        return {"error": f"Invalid channel UUID: {channel_id}"}

    if date == "today":
        day = datetime.now(timezone.utc).date()
    else:
        try:
            day = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return {"error": f"Invalid date format: {date}. Use YYYY-MM-DD or 'today'."}

    try:
        async with session_factory() as db:
            entries = await epg_service.get_schedule(db, cid, day)
            return [_serialize_schedule_entry(e) for e in entries]
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_now_playing(ctx: Context) -> list[dict]:
    """Get the currently airing program and next program for every channel."""
    session_factory = _get_session_factory(ctx)
    try:
        async with session_factory() as db:
            results = await epg_service.get_now_playing(db)
            output = []
            for item in results:
                ch = item["channel"]
                current = item.get("current_program")
                next_prog = item.get("next_program")
                output.append({
                    "channel": {
                        "name": ch.get("name"),
                        "channel_number": ch.get("channel_number"),
                        "is_hd": ch.get("is_hd"),
                    },
                    "current_program": _serialize_schedule_entry(current) if current else None,
                    "next_program": _serialize_schedule_entry(next_prog) if next_prog else None,
                })
            return output
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# US3: Catalog Statistics (T015)
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_catalog_stats(ctx: Context) -> dict:
    """Get summary statistics: total titles, genre distribution, age ratings, channels, and packages."""
    session_factory = _get_session_factory(ctx)
    try:
        async with session_factory() as db:
            # Title counts
            total_q = await db.execute(select(func.count()).select_from(Title))
            total = total_q.scalar_one()

            movies_q = await db.execute(
                select(func.count()).select_from(Title).where(Title.title_type == "movie")
            )
            movies = movies_q.scalar_one()

            series_q = await db.execute(
                select(func.count()).select_from(Title).where(Title.title_type == "series")
            )
            series = series_q.scalar_one()

            # Genre distribution
            genre_q = await db.execute(
                select(Genre.name, Genre.slug, func.count(TitleGenre.title_id))
                .join(TitleGenre, TitleGenre.genre_id == Genre.id)
                .group_by(Genre.name, Genre.slug)
                .order_by(func.count(TitleGenre.title_id).desc())
            )
            genres = [
                {"name": name, "slug": slug, "count": count}
                for name, slug, count in genre_q.fetchall()
            ]

            # Age rating distribution
            rating_q = await db.execute(
                select(Title.age_rating, func.count())
                .group_by(Title.age_rating)
                .order_by(func.count().desc())
            )
            age_ratings = {rating: count for rating, count in rating_q.fetchall() if rating}

            # Channel count
            channels_q = await db.execute(select(func.count()).select_from(Channel))
            channel_count = channels_q.scalar_one()

            # Content packages
            packages_q = await db.execute(
                select(ContentPackage).order_by(ContentPackage.price_cents)
            )
            packages = [
                {
                    "name": p.name,
                    "tier": p.tier,
                    "price_cents": p.price_cents,
                    "currency": p.currency,
                }
                for p in packages_q.scalars().all()
            ]

            return {
                "titles": {"total": total, "movies": movies, "series": series},
                "genres": genres,
                "age_ratings": age_ratings,
                "channels": {"total": channel_count},
                "packages": packages,
            }
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# US5: Cast & Crew Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def search_cast(
    query: str,
    ctx: Context,
    role: str | None = None,
    limit: int = 20,
) -> dict:
    """Search for actors, directors, or writers by name.

    Args:
        query: Name or partial name to search for
        role: Optional filter — "actor", "director", or "writer"
        limit: Maximum results to return (default 20, max 100)
    """
    limit = min(max(1, limit), 100)
    session_factory = _get_session_factory(ctx)
    try:
        async with session_factory() as db:
            stmt = (
                select(
                    TitleCast.person_name,
                    TitleCast.role,
                    func.count(TitleCast.title_id.distinct()).label("title_count"),
                )
                .where(TitleCast.person_name.ilike(f"%{query}%"))
                .group_by(TitleCast.person_name, TitleCast.role)
                .order_by(func.count(TitleCast.title_id.distinct()).desc())
                .limit(limit)
            )
            if role:
                stmt = stmt.where(TitleCast.role == role)

            result = await db.execute(stmt)
            people = [
                {"person_name": name, "role": r, "title_count": count}
                for name, r, count in result.fetchall()
            ]
            return {"people": people, "total": len(people)}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_person_titles(
    person_name: str,
    ctx: Context,
    role: str | None = None,
) -> dict:
    """Get all titles associated with a person (their filmography).

    Args:
        person_name: Exact person name (use search_cast to find the correct name first)
        role: Optional filter — "actor", "director", or "writer"
    """
    session_factory = _get_session_factory(ctx)
    try:
        async with session_factory() as db:
            stmt = (
                select(TitleCast)
                .join(Title, TitleCast.title_id == Title.id)
                .where(TitleCast.person_name == person_name)
                .order_by(Title.release_year.desc())
            )
            if role:
                stmt = stmt.where(TitleCast.role == role)

            result = await db.execute(stmt.options(
                selectinload(TitleCast.title).selectinload(Title.genres).selectinload(TitleGenre.genre)
            ))
            cast_entries = result.scalars().all()

            titles = [
                {
                    "title_id": str(c.title_id),
                    "title": c.title.title,
                    "title_type": c.title.title_type,
                    "release_year": c.title.release_year,
                    "role": c.role,
                    "character_name": c.character_name,
                    "genres": [tg.genre.name for tg in c.title.genres] if c.title.genres else [],
                }
                for c in cast_entries
            ]

            return {
                "person_name": person_name,
                "titles": titles,
                "total": len(titles),
            }
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# US4: Title Offers (T016)
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_title_offers(title_id: str, ctx: Context) -> dict:
    """Get pricing and availability for a specific title (TVOD offers and SVOD package inclusion).

    Args:
        title_id: The UUID of the title
    """
    session_factory = _get_session_factory(ctx)

    try:
        tid = uuid.UUID(title_id)
    except ValueError:
        return {"error": f"Invalid UUID: {title_id}"}

    try:
        async with session_factory() as db:
            # Active TVOD offers
            offers_q = await db.execute(
                select(TitleOffer).where(
                    TitleOffer.title_id == tid,
                    TitleOffer.is_active.is_(True),
                )
            )
            offers = [
                {
                    "offer_type": o.offer_type,
                    "price_cents": o.price_cents,
                    "currency": o.currency,
                    "rental_window_hours": o.rental_window_hours,
                }
                for o in offers_q.scalars().all()
            ]

            # SVOD packages that include this title
            packages_q = await db.execute(
                select(ContentPackage)
                .join(
                    PackageContent,
                    PackageContent.package_id == ContentPackage.id,
                )
                .where(
                    PackageContent.content_id == tid,
                    PackageContent.content_type == "vod_title",
                )
            )
            packages = [
                {"name": p.name, "tier": p.tier}
                for p in packages_q.scalars().all()
            ]

            return {
                "title_id": str(tid),
                "offers": offers,
                "included_in_packages": packages,
            }
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# US6: Advanced Catalog Discovery
# ---------------------------------------------------------------------------


@mcp.tool()
async def browse_titles(
    ctx: Context,
    age_rating: str | None = None,
    language: str | None = None,
    country: str | None = None,
    is_educational: bool | None = None,
    mood_tag: str | None = None,
    theme_tag: str | None = None,
    title_type: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """Browse titles with advanced filters not available in list_titles.

    Args:
        age_rating: Filter by age rating (e.g., "TV-MA", "TV-PG", "TV-14")
        language: Filter by language code (e.g., "en", "no", "es")
        country: Filter by country of origin (e.g., "US", "NO", "GB")
        is_educational: Filter to educational content only (true/false)
        mood_tag: Filter by mood tag (e.g., "gritty", "epic", "heartwarming")
        theme_tag: Filter by theme tag (e.g., "justice", "survival", "family")
        title_type: Filter by "movie" or "series"
        page: Page number (default 1)
        page_size: Items per page (default 20, max 100)
    """
    page_size = min(max(1, page_size), 100)
    page = max(1, page)
    session_factory = _get_session_factory(ctx)
    try:
        async with session_factory() as db:
            base = select(Title).options(
                selectinload(Title.genres).selectinload(TitleGenre.genre),
            )
            count_q = select(func.count()).select_from(Title)

            if age_rating:
                base = base.where(Title.age_rating == age_rating)
                count_q = count_q.where(Title.age_rating == age_rating)
            if language:
                base = base.where(Title.language == language)
                count_q = count_q.where(Title.language == language)
            if country:
                base = base.where(Title.country_of_origin == country)
                count_q = count_q.where(Title.country_of_origin == country)
            if is_educational is not None:
                base = base.where(Title.is_educational.is_(is_educational))
                count_q = count_q.where(Title.is_educational.is_(is_educational))
            if title_type:
                base = base.where(Title.title_type == title_type)
                count_q = count_q.where(Title.title_type == title_type)
            if mood_tag:
                base = base.where(Title.mood_tags.any(mood_tag))
                count_q = count_q.where(Title.mood_tags.any(mood_tag))
            if theme_tag:
                base = base.where(Title.theme_tags.any(theme_tag))
                count_q = count_q.where(Title.theme_tags.any(theme_tag))

            total = (await db.execute(count_q)).scalar_one()

            offset = (page - 1) * page_size
            result = await db.execute(
                base.order_by(Title.title).offset(offset).limit(page_size)
            )
            titles = list(result.scalars().unique())

            return {
                "titles": [_serialize_title_summary(t) for t in titles],
                "total": total,
                "page": page,
                "page_size": page_size,
            }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def list_mood_tags(ctx: Context) -> dict:
    """List all distinct mood tags used across titles, with counts."""
    session_factory = _get_session_factory(ctx)
    try:
        async with session_factory() as db:
            result = await db.execute(
                select(
                    func.unnest(Title.mood_tags).label("tag"),
                    func.count().label("count"),
                )
                .where(Title.mood_tags.isnot(None))
                .group_by(text("tag"))
                .order_by(text("count DESC"))
            )
            tags = [{"tag": tag, "count": count} for tag, count in result.fetchall()]
            return {"mood_tags": tags}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def list_theme_tags(ctx: Context) -> dict:
    """List all distinct theme tags used across titles, with counts."""
    session_factory = _get_session_factory(ctx)
    try:
        async with session_factory() as db:
            result = await db.execute(
                select(
                    func.unnest(Title.theme_tags).label("tag"),
                    func.count().label("count"),
                )
                .where(Title.theme_tags.isnot(None))
                .group_by(text("tag"))
                .order_by(text("count DESC"))
            )
            tags = [{"tag": tag, "count": count} for tag, count in result.fetchall()]
            return {"theme_tags": tags}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# US7: Package & Entitlement Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_packages(ctx: Context) -> list[dict]:
    """List all content packages with full details (description, tier, pricing, stream limits)."""
    session_factory = _get_session_factory(ctx)
    try:
        async with session_factory() as db:
            result = await db.execute(
                select(ContentPackage).order_by(ContentPackage.price_cents)
            )
            packages = result.scalars().all()
            return [
                {
                    "id": str(p.id),
                    "name": p.name,
                    "description": p.description,
                    "tier": p.tier,
                    "max_streams": p.max_streams,
                    "price_cents": p.price_cents,
                    "currency": p.currency,
                }
                for p in packages
            ]
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_package_contents(package_id: str, ctx: Context) -> dict:
    """List all titles and channels included in a content package.

    Args:
        package_id: The UUID of the content package
    """
    session_factory = _get_session_factory(ctx)
    try:
        pid = uuid.UUID(package_id)
    except ValueError:
        return {"error": f"Invalid UUID: {package_id}"}

    try:
        async with session_factory() as db:
            # Package info
            pkg = (await db.execute(
                select(ContentPackage).where(ContentPackage.id == pid)
            )).scalar_one_or_none()
            if pkg is None:
                return {"error": f"Package not found: {package_id}"}

            # VOD titles in package
            vod_q = await db.execute(
                select(Title)
                .join(PackageContent, PackageContent.content_id == Title.id)
                .where(
                    PackageContent.package_id == pid,
                    PackageContent.content_type == "vod_title",
                )
                .options(selectinload(Title.genres).selectinload(TitleGenre.genre))
                .order_by(Title.title)
            )
            vod_titles = [_serialize_title_summary(t) for t in vod_q.scalars().unique()]

            # Channels in package
            ch_q = await db.execute(
                select(Channel)
                .join(PackageContent, PackageContent.content_id == Channel.id)
                .where(
                    PackageContent.package_id == pid,
                    PackageContent.content_type == "channel",
                )
                .order_by(Channel.channel_number)
            )
            channels = [
                {"id": str(ch.id), "name": ch.name, "channel_number": ch.channel_number}
                for ch in ch_q.scalars().all()
            ]

            return {
                "package": {"id": str(pkg.id), "name": pkg.name, "tier": pkg.tier},
                "vod_titles": vod_titles,
                "vod_title_count": len(vod_titles),
                "channels": channels,
                "channel_count": len(channels),
            }
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# US8: EPG Enhancements
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_catchup_available(
    ctx: Context,
    channel_id: str | None = None,
    limit: int = 50,
) -> dict:
    """List programs available on catch-up TV right now (aired recently, still within catchup window).

    Args:
        channel_id: Optional UUID to filter by a specific channel
        limit: Maximum results (default 50, max 200)
    """
    limit = min(max(1, limit), 200)
    session_factory = _get_session_factory(ctx)
    try:
        async with session_factory() as db:
            now = datetime.now(timezone.utc)
            stmt = (
                select(ScheduleEntry)
                .join(Channel, ScheduleEntry.channel_id == Channel.id)
                .where(
                    ScheduleEntry.catchup_eligible.is_(True),
                    Channel.catchup_enabled.is_(True),
                    ScheduleEntry.end_time <= now,
                    ScheduleEntry.end_time >= func.now() - text(
                        "make_interval(hours => channels.catchup_window_hours)"
                    ),
                )
                .order_by(ScheduleEntry.end_time.desc())
                .limit(limit)
            )
            if channel_id:
                try:
                    cid = uuid.UUID(channel_id)
                except ValueError:
                    return {"error": f"Invalid UUID: {channel_id}"}
                stmt = stmt.where(ScheduleEntry.channel_id == cid)

            result = await db.execute(stmt)
            entries = result.scalars().all()
            return {
                "programs": [_serialize_schedule_entry(e) for e in entries],
                "total": len(entries),
            }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def search_schedule(
    query: str,
    ctx: Context,
    date: str = "today",
    limit: int = 20,
) -> dict:
    """Search the EPG schedule by program title or series title across all channels.

    Args:
        query: Search keyword (matches program title and series_title)
        date: Date in YYYY-MM-DD format or "today" (default: "today")
        limit: Maximum results (default 20, max 100)
    """
    limit = min(max(1, limit), 100)
    session_factory = _get_session_factory(ctx)

    if date == "today":
        day = datetime.now(timezone.utc).date()
    else:
        try:
            day = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return {"error": f"Invalid date format: {date}. Use YYYY-MM-DD or 'today'."}

    try:
        async with session_factory() as db:
            day_start = datetime.combine(day, datetime.min.time()).replace(tzinfo=timezone.utc)
            day_end = datetime.combine(day, datetime.max.time()).replace(tzinfo=timezone.utc)
            pattern = f"%{query}%"

            stmt = (
                select(ScheduleEntry)
                .join(Channel, ScheduleEntry.channel_id == Channel.id)
                .where(
                    ScheduleEntry.start_time >= day_start,
                    ScheduleEntry.start_time <= day_end,
                    (ScheduleEntry.title.ilike(pattern) | ScheduleEntry.series_title.ilike(pattern)),
                )
                .order_by(ScheduleEntry.start_time)
                .limit(limit)
            )

            result = await db.execute(stmt)
            entries = result.scalars().all()

            programs = []
            for e in entries:
                entry = _serialize_schedule_entry(e)
                entry["series_title"] = e.series_title
                entry["season_number"] = e.season_number
                entry["episode_number"] = e.episode_number
                programs.append(entry)

            return {"programs": programs, "total": len(programs)}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# US9: Analytics & Engagement (read-only aggregates)
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_title_popularity(
    ctx: Context,
    title_type: str | None = None,
    days: int = 30,
    limit: int = 20,
) -> dict:
    """Get the most-watched titles by play count over a recent time period.

    Args:
        title_type: Optional filter — "movie" or "series"
        days: Look-back period in days (default 30)
        limit: Number of top titles to return (default 20, max 100)
    """
    limit = min(max(1, limit), 100)
    session_factory = _get_session_factory(ctx)
    try:
        async with session_factory() as db:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)

            stmt = (
                select(
                    Title.id,
                    Title.title,
                    Title.title_type,
                    func.count(AnalyticsEvent.id).label("play_count"),
                    func.avg(AnalyticsEvent.watch_percentage).label("avg_watch_pct"),
                )
                .join(AnalyticsEvent, AnalyticsEvent.title_id == Title.id)
                .where(
                    AnalyticsEvent.event_type == "play_start",
                    AnalyticsEvent.occurred_at >= cutoff,
                )
                .group_by(Title.id, Title.title, Title.title_type)
                .order_by(func.count(AnalyticsEvent.id).desc())
                .limit(limit)
            )
            if title_type:
                stmt = stmt.where(Title.title_type == title_type)

            result = await db.execute(stmt)
            titles = [
                {
                    "title_id": str(tid),
                    "title": name,
                    "title_type": ttype,
                    "play_count": count,
                    "avg_watch_percentage": round(float(avg_pct), 1) if avg_pct else None,
                }
                for tid, name, ttype, count, avg_pct in result.fetchall()
            ]
            return {"period_days": days, "titles": titles}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_service_type_stats(
    ctx: Context,
    days: int = 30,
) -> dict:
    """Get play count breakdown by service type (Linear, VoD, SVoD, TSTV, Catch_up, Cloud_PVR).

    Args:
        days: Look-back period in days (default 30)
    """
    session_factory = _get_session_factory(ctx)
    try:
        async with session_factory() as db:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)

            result = await db.execute(
                select(
                    AnalyticsEvent.service_type,
                    func.count().label("play_count"),
                    func.avg(AnalyticsEvent.duration_seconds).label("avg_duration_s"),
                )
                .where(
                    AnalyticsEvent.event_type == "play_start",
                    AnalyticsEvent.occurred_at >= cutoff,
                )
                .group_by(AnalyticsEvent.service_type)
                .order_by(func.count().desc())
            )
            breakdown = [
                {
                    "service_type": stype,
                    "play_count": count,
                    "avg_duration_seconds": round(float(avg_dur), 0) if avg_dur else None,
                }
                for stype, count, avg_dur in result.fetchall()
            ]
            return {"period_days": days, "breakdown": breakdown}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_title_ratings(title_id: str, ctx: Context) -> dict:
    """Get audience rating summary for a title (thumbs up/down counts).

    Args:
        title_id: The UUID of the title
    """
    session_factory = _get_session_factory(ctx)
    try:
        tid = uuid.UUID(title_id)
    except ValueError:
        return {"error": f"Invalid UUID: {title_id}"}

    try:
        async with session_factory() as db:
            result = await db.execute(
                select(
                    func.count().filter(Rating.rating == 1).label("thumbs_up"),
                    func.count().filter(Rating.rating == -1).label("thumbs_down"),
                    func.count().label("total_ratings"),
                )
                .where(Rating.title_id == tid)
            )
            row = result.one()
            thumbs_up = row.thumbs_up or 0
            thumbs_down = row.thumbs_down or 0
            total = row.total_ratings or 0
            return {
                "title_id": str(tid),
                "thumbs_up": thumbs_up,
                "thumbs_down": thumbs_down,
                "total_ratings": total,
                "approval_rate": round(thumbs_up / total * 100, 1) if total > 0 else None,
            }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_most_wishlisted(
    ctx: Context,
    limit: int = 20,
) -> dict:
    """Get titles with the most watchlist additions (demand signal).

    Args:
        limit: Number of top titles to return (default 20, max 100)
    """
    limit = min(max(1, limit), 100)
    session_factory = _get_session_factory(ctx)
    try:
        async with session_factory() as db:
            result = await db.execute(
                select(
                    Title.id,
                    Title.title,
                    Title.title_type,
                    func.count(WatchlistItem.profile_id).label("watchlist_count"),
                )
                .join(WatchlistItem, WatchlistItem.title_id == Title.id)
                .group_by(Title.id, Title.title, Title.title_type)
                .order_by(func.count(WatchlistItem.profile_id).desc())
                .limit(limit)
            )
            titles = [
                {
                    "title_id": str(tid),
                    "title": name,
                    "title_type": ttype,
                    "watchlist_count": count,
                }
                for tid, name, ttype, count in result.fetchall()
            ]
            return {"titles": titles}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# US10: Operational / Health Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_embedding_status(ctx: Context) -> dict:
    """Check content embedding coverage — how many titles have vector embeddings vs missing."""
    session_factory = _get_session_factory(ctx)
    try:
        async with session_factory() as db:
            total_q = await db.execute(select(func.count()).select_from(Title))
            total_titles = total_q.scalar_one()

            embedded_q = await db.execute(select(func.count()).select_from(ContentEmbedding))
            embedded = embedded_q.scalar_one()

            # Titles missing embeddings
            missing_q = await db.execute(
                select(Title.id, Title.title)
                .outerjoin(ContentEmbedding, ContentEmbedding.title_id == Title.id)
                .where(ContentEmbedding.title_id.is_(None))
                .order_by(Title.title)
                .limit(20)
            )
            missing_sample = [
                {"title_id": str(tid), "title": name}
                for tid, name in missing_q.fetchall()
            ]

            return {
                "total_titles": total_titles,
                "with_embeddings": embedded,
                "missing_embeddings": total_titles - embedded,
                "coverage_pct": round(embedded / total_titles * 100, 1) if total_titles > 0 else 0,
                "missing_sample": missing_sample,
            }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_tstv_stats(
    ctx: Context,
    days: int = 30,
) -> dict:
    """Get TSTV usage statistics — Start Over vs Catch-up sessions, completion rates.

    Args:
        days: Look-back period in days (default 30)
    """
    session_factory = _get_session_factory(ctx)
    try:
        async with session_factory() as db:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)

            result = await db.execute(
                select(
                    TSTVSession.session_type,
                    func.count().label("session_count"),
                    func.count().filter(TSTVSession.completed.is_(True)).label("completed"),
                    func.avg(TSTVSession.last_position_s).label("avg_position_s"),
                )
                .where(TSTVSession.started_at >= cutoff)
                .group_by(TSTVSession.session_type)
            )
            breakdown = []
            for stype, count, completed, avg_pos in result.fetchall():
                breakdown.append({
                    "session_type": stype,
                    "session_count": count,
                    "completed": completed,
                    "completion_rate": round(completed / count * 100, 1) if count > 0 else 0,
                    "avg_position_seconds": round(float(avg_pos), 0) if avg_pos else 0,
                })

            return {"period_days": days, "breakdown": breakdown}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def get_recording_stats(
    ctx: Context,
    days: int = 30,
) -> dict:
    """Get Cloud PVR recording statistics — counts by status.

    Args:
        days: Look-back period in days (default 30)
    """
    session_factory = _get_session_factory(ctx)
    try:
        async with session_factory() as db:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)

            result = await db.execute(
                select(
                    Recording.status,
                    func.count().label("count"),
                )
                .where(Recording.requested_at >= cutoff)
                .group_by(Recording.status)
                .order_by(func.count().desc())
            )
            statuses = {status: count for status, count in result.fetchall()}

            total = sum(statuses.values())
            return {
                "period_days": days,
                "total_recordings": total,
                "by_status": statuses,
            }
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    """Run the MCP server with stdio transport."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
