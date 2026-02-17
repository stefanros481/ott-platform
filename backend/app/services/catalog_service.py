"""Catalog service — title browsing, search, and detail retrieval."""

import uuid

from sqlalchemy import exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.catalog import Episode, Genre, Season, Title, TitleCast, TitleGenre
from app.services.search_service import escape_like


async def get_titles(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 20,
    genre_slug: str | None = None,
    title_type: str | None = None,
    search_query: str | None = None,
    allowed_ratings: list[str] | None = None,
) -> tuple[list[Title], int]:
    """Return a paginated, optionally filtered list of titles.

    Supports filtering by genre slug, title type (movie/series), and free-text
    search across title and synopsis_short using ILIKE.
    """
    base = select(Title).options(
        selectinload(Title.genres).selectinload(TitleGenre.genre),
    )

    # Count query shares the same filters but no pagination / eager loads.
    count_q = select(func.count()).select_from(Title)

    if allowed_ratings is not None:
        base = base.where(Title.age_rating.in_(allowed_ratings))
        count_q = count_q.where(Title.age_rating.in_(allowed_ratings))

    if genre_slug:
        base = base.join(Title.genres).join(TitleGenre.genre).where(Genre.slug == genre_slug)
        count_q = (
            count_q.join(TitleGenre, TitleGenre.title_id == Title.id)
            .join(Genre, Genre.id == TitleGenre.genre_id)
            .where(Genre.slug == genre_slug)
        )

    if title_type:
        base = base.where(Title.title_type == title_type)
        count_q = count_q.where(Title.title_type == title_type)

    if search_query:
        pattern = f"%{escape_like(search_query)}%"
        cast_match = exists(
            select(TitleCast.id).where(
                TitleCast.title_id == Title.id,
                TitleCast.person_name.ilike(pattern),
            )
        )
        search_filter = or_(
            Title.title.ilike(pattern),
            Title.synopsis_short.ilike(pattern),
            Title.synopsis_long.ilike(pattern),
            cast_match,
        )
        base = base.where(search_filter)
        count_q = count_q.where(search_filter)

    # Total count
    total = (await db.execute(count_q)).scalar_one()

    # Paginated results
    offset = (page - 1) * page_size
    query = base.order_by(Title.title).offset(offset).limit(page_size)
    result = await db.execute(query)
    titles = list(result.scalars().unique())

    return titles, total


async def get_title_detail(db: AsyncSession, title_id: uuid.UUID) -> Title | None:
    """Load a single title with all relationships eagerly loaded."""
    query = (
        select(Title)
        .where(Title.id == title_id)
        .options(
            selectinload(Title.genres).selectinload(TitleGenre.genre),
            selectinload(Title.cast_members),
            selectinload(Title.seasons).selectinload(Season.episodes),
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_genres(db: AsyncSession) -> list[Genre]:
    """Return all genres ordered alphabetically."""
    result = await db.execute(select(Genre).order_by(Genre.name))
    return list(result.scalars().all())


async def get_featured_titles(
    db: AsyncSession,
    *,
    allowed_ratings: list[str] | None = None,
    profile_id: uuid.UUID | None = None,
) -> list[Title]:
    """Return titles flagged as featured (for the hero banner).

    When *profile_id* is provided, titles are sorted by cosine similarity to the
    profile's viewing preferences.  Falls back to ``created_at DESC`` for new profiles.
    """
    query = (
        select(Title)
        .where(Title.is_featured.is_(True))
        .options(
            selectinload(Title.genres).selectinload(TitleGenre.genre),
        )
        .order_by(Title.created_at.desc())
    )
    if allowed_ratings is not None:
        query = query.where(Title.age_rating.in_(allowed_ratings))
    result = await db.execute(query)
    titles = list(result.scalars().unique())

    # Apply personalized sorting when a profile is provided.
    if profile_id is not None and titles:
        from app.services.recommendation_service import get_personalized_featured_titles

        sorted_ids = await get_personalized_featured_titles(
            db, profile_id, allowed_ratings=allowed_ratings
        )
        if sorted_ids is not None:
            id_order = {tid: i for i, tid in enumerate(sorted_ids)}
            titles.sort(key=lambda t: id_order.get(t.id, len(sorted_ids)))

    return titles
