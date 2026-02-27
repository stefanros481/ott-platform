"""Bookmark business logic for Continue Watching & Cross-Device Bookmarks."""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.viewing import Bookmark
from app.schemas.viewing import (
    BookmarkResponse,
    ContinueWatchingItem,
    NextEpisodeInfo,
    TitleInfo,
)

STALE_DAYS = 30
COMPLETION_PERCENT = 0.95
COMPLETION_REMAINING_SECONDS = 120  # 2 minutes


async def upsert_bookmark(
    db: AsyncSession,
    profile_id: uuid.UUID,
    content_type: str,
    content_id: uuid.UUID,
    position_seconds: int,
    duration_seconds: int,
) -> Bookmark:
    """Create or update a bookmark. Auto-marks completed at 95% or final 2 minutes."""
    result = await db.execute(
        select(Bookmark).where(
            and_(
                Bookmark.profile_id == profile_id,
                Bookmark.content_id == content_id,
            )
        )
    )
    bookmark = result.scalar_one_or_none()

    completed = (
        position_seconds >= duration_seconds * COMPLETION_PERCENT
        or (duration_seconds - position_seconds) <= COMPLETION_REMAINING_SECONDS
    )

    # TSTV content types use furthest-position-wins to handle concurrent writes
    tstv_types = ("tstv_catchup", "tstv_startover")
    use_furthest_position = content_type in tstv_types

    if bookmark is None:
        bookmark = Bookmark(
            profile_id=profile_id,
            content_type=content_type,
            content_id=content_id,
            position_seconds=position_seconds,
            duration_seconds=duration_seconds,
            completed=completed,
        )
        db.add(bookmark)
    else:
        if use_furthest_position:
            bookmark.position_seconds = max(bookmark.position_seconds, position_seconds)
        else:
            bookmark.position_seconds = position_seconds
        bookmark.duration_seconds = duration_seconds
        bookmark.completed = completed
        # Clear dismissed_at if user actively resumes
        if bookmark.dismissed_at is not None:
            bookmark.dismissed_at = None

    await db.commit()
    await db.refresh(bookmark)
    return bookmark


async def get_active_bookmarks(
    db: AsyncSession,
    profile_id: uuid.UUID,
    limit: int = 20,
) -> list[ContinueWatchingItem]:
    """Return active (not completed, not dismissed, not stale) bookmarks with title info."""
    stale_cutoff = datetime.now(timezone.utc) - timedelta(days=STALE_DAYS)

    result = await db.execute(
        text(
            """
            SELECT b.id, b.content_type, b.content_id, b.position_seconds,
                   b.duration_seconds, b.completed, b.dismissed_at, b.updated_at,
                   CASE
                     WHEN b.content_type = 'movie' THEN t.title
                     WHEN b.content_type = 'episode' THEN t.title
                   END AS title_name,
                   t.poster_url, t.landscape_url, t.title_type, t.age_rating,
                   e.title AS episode_title,
                   s.season_number, e.episode_number
            FROM bookmarks b
            LEFT JOIN titles t ON (
                CASE
                    WHEN b.content_type = 'movie' THEN t.id = b.content_id
                    WHEN b.content_type = 'episode' THEN t.id = (
                        SELECT s2.title_id FROM episodes e2
                        JOIN seasons s2 ON s2.id = e2.season_id
                        WHERE e2.id = b.content_id
                    )
                END
            )
            LEFT JOIN episodes e ON b.content_type = 'episode' AND e.id = b.content_id
            LEFT JOIN seasons s ON e.season_id = s.id
            WHERE b.profile_id = :pid
              AND b.completed = false
              AND b.dismissed_at IS NULL
              AND b.updated_at >= :stale_cutoff
              AND t.id IS NOT NULL
            ORDER BY b.updated_at DESC
            LIMIT :lim
            """
        ).bindparams(pid=profile_id, stale_cutoff=stale_cutoff, lim=limit),
    )
    rows = result.fetchall()

    items = []
    for r in rows:
        progress = (r.position_seconds / r.duration_seconds * 100) if r.duration_seconds > 0 else 0.0

        title_info = TitleInfo(
            title=r.title_name or "Unknown",
            poster_url=r.poster_url,
            landscape_url=r.landscape_url,
            title_type=r.title_type or ("movie" if r.content_type == "movie" else "series"),
            age_rating=r.age_rating,
            episode_title=r.episode_title,
            season_number=r.season_number,
            episode_number=r.episode_number,
        )

        next_ep = None
        if r.content_type == "episode":
            next_ep = await resolve_next_episode(db, profile_id, r.content_id)

        items.append(
            ContinueWatchingItem(
                id=r.id,
                content_type=r.content_type,
                content_id=r.content_id,
                position_seconds=r.position_seconds,
                duration_seconds=r.duration_seconds,
                progress_percent=round(progress, 1),
                completed=r.completed,
                dismissed_at=r.dismissed_at,
                updated_at=r.updated_at,
                title_info=title_info,
                next_episode=next_ep,
            )
        )

    return items


async def get_paused_bookmarks(
    db: AsyncSession,
    profile_id: uuid.UUID,
) -> list[ContinueWatchingItem]:
    """Return dismissed + stale bookmarks for the Paused section."""
    stale_cutoff = datetime.now(timezone.utc) - timedelta(days=STALE_DAYS)

    result = await db.execute(
        text(
            """
            SELECT b.id, b.content_type, b.content_id, b.position_seconds,
                   b.duration_seconds, b.completed, b.dismissed_at, b.updated_at,
                   CASE
                     WHEN b.content_type = 'movie' THEN t.title
                     WHEN b.content_type = 'episode' THEN t.title
                   END AS title_name,
                   t.poster_url, t.landscape_url, t.title_type, t.age_rating,
                   e.title AS episode_title,
                   s.season_number, e.episode_number
            FROM bookmarks b
            LEFT JOIN titles t ON (
                CASE
                    WHEN b.content_type = 'movie' THEN t.id = b.content_id
                    WHEN b.content_type = 'episode' THEN t.id = (
                        SELECT s2.title_id FROM episodes e2
                        JOIN seasons s2 ON s2.id = e2.season_id
                        WHERE e2.id = b.content_id
                    )
                END
            )
            LEFT JOIN episodes e ON b.content_type = 'episode' AND e.id = b.content_id
            LEFT JOIN seasons s ON e.season_id = s.id
            WHERE b.profile_id = :pid
              AND b.completed = false
              AND t.id IS NOT NULL
              AND (
                  b.dismissed_at IS NOT NULL
                  OR (b.dismissed_at IS NULL AND b.updated_at < :stale_cutoff)
              )
            ORDER BY COALESCE(b.dismissed_at, b.updated_at) DESC
            """
        ).bindparams(pid=profile_id, stale_cutoff=stale_cutoff),
    )
    rows = result.fetchall()

    items = []
    for r in rows:
        progress = (r.position_seconds / r.duration_seconds * 100) if r.duration_seconds > 0 else 0.0

        title_info = TitleInfo(
            title=r.title_name or "Unknown",
            poster_url=r.poster_url,
            landscape_url=r.landscape_url,
            title_type=r.title_type or ("movie" if r.content_type == "movie" else "series"),
            age_rating=r.age_rating,
            episode_title=r.episode_title,
            season_number=r.season_number,
            episode_number=r.episode_number,
        )

        items.append(
            ContinueWatchingItem(
                id=r.id,
                content_type=r.content_type,
                content_id=r.content_id,
                position_seconds=r.position_seconds,
                duration_seconds=r.duration_seconds,
                progress_percent=round(progress, 1),
                completed=r.completed,
                dismissed_at=r.dismissed_at,
                updated_at=r.updated_at,
                title_info=title_info,
                next_episode=None,
            )
        )

    return items


async def dismiss_bookmark(
    db: AsyncSession,
    bookmark_id: uuid.UUID,
    profile_id: uuid.UUID,
) -> Bookmark | None:
    """Set dismissed_at to now. Returns None if bookmark not found or wrong profile."""
    result = await db.execute(
        select(Bookmark).where(
            and_(Bookmark.id == bookmark_id, Bookmark.profile_id == profile_id)
        )
    )
    bookmark = result.scalar_one_or_none()
    if bookmark is None:
        return None

    bookmark.dismissed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(bookmark)
    return bookmark


async def restore_bookmark(
    db: AsyncSession,
    bookmark_id: uuid.UUID,
    profile_id: uuid.UUID,
) -> Bookmark | None:
    """Clear dismissed_at, set updated_at to now. Returns None if not found."""
    result = await db.execute(
        select(Bookmark).where(
            and_(Bookmark.id == bookmark_id, Bookmark.profile_id == profile_id)
        )
    )
    bookmark = result.scalar_one_or_none()
    if bookmark is None:
        return None

    bookmark.dismissed_at = None
    # Force updated_at refresh by touching a value (onupdate=func.now() handles it)
    bookmark.position_seconds = bookmark.position_seconds
    await db.commit()
    await db.refresh(bookmark)
    return bookmark


async def get_bookmark_by_content(
    db: AsyncSession,
    profile_id: uuid.UUID,
    content_id: uuid.UUID,
) -> Bookmark | None:
    """Return a single bookmark by profile + content_id, or None if not found."""
    result = await db.execute(
        select(Bookmark).where(
            and_(
                Bookmark.profile_id == profile_id,
                Bookmark.content_id == content_id,
            )
        )
    )
    return result.scalar_one_or_none()


async def resolve_next_episode(
    db: AsyncSession,
    profile_id: uuid.UUID,
    current_episode_id: uuid.UUID,
) -> NextEpisodeInfo | None:
    """Find the next unwatched episode in the same series."""
    result = await db.execute(
        text(
            """
            WITH current AS (
                SELECT e.id, e.episode_number, s.season_number, s.title_id
                FROM episodes e
                JOIN seasons s ON s.id = e.season_id
                WHERE e.id = :episode_id
            )
            SELECT e.id AS episode_id, e.title AS episode_title,
                   s.season_number, e.episode_number
            FROM episodes e
            JOIN seasons s ON s.id = e.season_id
            JOIN current c ON s.title_id = c.title_id
            WHERE (s.season_number, e.episode_number) > (c.season_number, c.episode_number)
              AND NOT EXISTS (
                  SELECT 1 FROM bookmarks b
                  WHERE b.profile_id = :pid
                    AND b.content_id = e.id
                    AND b.completed = true
              )
            ORDER BY s.season_number, e.episode_number
            LIMIT 1
            """
        ).bindparams(episode_id=current_episode_id, pid=profile_id),
    )
    row = result.fetchone()
    if row is None:
        return None

    return NextEpisodeInfo(
        episode_id=row.episode_id,
        season_number=row.season_number,
        episode_number=row.episode_number,
        episode_title=row.episode_title,
    )
