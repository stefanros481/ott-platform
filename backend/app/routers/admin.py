"""Admin router -- platform stats, CRUD for titles / channels / schedule, embedding generation."""

import uuid
from datetime import date

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import DB, AdminUser
from app.services.search_service import escape_like
from app.models.catalog import Title, TitleGenre
from app.models.embedding import ContentEmbedding
from app.models.epg import Channel, ScheduleEntry
from app.models.user import Profile, User
from app.schemas.admin import (
    EmbeddingGenerationResponse,
    PlatformStatsResponse,
    TitleAdminResponse,
    TitleCreateRequest,
    TitlePaginatedResponse,
    TitleUpdateRequest,
)
from app.schemas.epg import (
    ChannelCreateRequest,
    ChannelResponse,
    ChannelUpdateRequest,
    ScheduleEntryCreateRequest,
    ScheduleEntryResponse,
    ScheduleEntryUpdateRequest,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Platform Stats
# ---------------------------------------------------------------------------


@router.get("/stats", response_model=PlatformStatsResponse)
async def stats(db: DB, user: AdminUser):
    """Return high-level platform statistics."""


    title_count = (await db.execute(select(func.count(Title.id)))).scalar_one()
    channel_count = (await db.execute(select(func.count(Channel.id)))).scalar_one()
    user_count = (await db.execute(select(func.count(User.id)))).scalar_one()
    embedding_count = (await db.execute(select(func.count(ContentEmbedding.title_id)))).scalar_one()

    return PlatformStatsResponse(
        title_count=title_count,
        channel_count=channel_count,
        user_count=user_count,
        embedding_count=embedding_count,
    )


# ---------------------------------------------------------------------------
# Titles CRUD
# ---------------------------------------------------------------------------


@router.get("/titles", response_model=TitlePaginatedResponse)
async def list_titles(
    db: DB,
    user: AdminUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    q: str | None = Query(None, description="Search by title"),
):
    """Paginated list of titles for the admin table."""


    # Base query
    query = select(Title)
    count_query = select(func.count()).select_from(Title)

    # Search filter
    if q:
        pattern = f"%{escape_like(q)}%"
        query = query.where(Title.title.ilike(pattern))
        count_query = count_query.where(Title.title.ilike(pattern))

    # Total count
    total = (await db.execute(count_query)).scalar() or 0

    # Paginated results
    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Title.created_at.desc()).offset(offset).limit(page_size)
    )
    titles = result.scalars().all()

    # Sub-query: which title IDs have embeddings?
    emb_result = await db.execute(select(ContentEmbedding.title_id))
    embedding_ids = {row[0] for row in emb_result.fetchall()}

    items = [
        TitleAdminResponse(
            id=t.id,
            title=t.title,
            title_type=t.title_type,
            release_year=t.release_year,
            age_rating=t.age_rating,
            poster_url=t.poster_url,
            is_featured=t.is_featured,
            has_embedding=t.id in embedding_ids,
            created_at=t.created_at,
        )
        for t in titles
    ]

    return TitlePaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("/titles", response_model=TitleAdminResponse, status_code=201)
async def create_title(body: TitleCreateRequest, db: DB, user: AdminUser):
    """Create a new VOD title."""


    title = Title(
        title=body.title,
        title_type=body.title_type,
        synopsis_short=body.synopsis_short,
        synopsis_long=body.synopsis_long,
        release_year=body.release_year,
        duration_minutes=body.duration_minutes,
        age_rating=body.age_rating,
        country_of_origin=body.country_of_origin,
        language=body.language,
        poster_url=body.poster_url,
        landscape_url=body.landscape_url,
        logo_url=body.logo_url,
        hls_manifest_url=body.hls_manifest_url,
        is_featured=body.is_featured,
        mood_tags=body.mood_tags,
        theme_tags=body.theme_tags,
        ai_description=body.ai_description,
    )
    db.add(title)
    await db.flush()  # get the generated id

    # Attach genre links if provided.
    if body.genre_ids:
        for gid in body.genre_ids:
            db.add(TitleGenre(title_id=title.id, genre_id=gid))

    await db.commit()
    await db.refresh(title)

    return TitleAdminResponse(
        id=title.id,
        title=title.title,
        title_type=title.title_type,
        release_year=title.release_year,
        age_rating=title.age_rating,
        poster_url=title.poster_url,
        is_featured=title.is_featured,
        has_embedding=False,
        created_at=title.created_at,
    )


@router.get("/titles/{title_id}")
async def get_title(title_id: uuid.UUID, db: DB, user: AdminUser):
    """Get a single title with all fields for the edit form."""


    result = await db.execute(select(Title).where(Title.id == title_id))
    title = result.scalar_one_or_none()
    if not title:
        raise HTTPException(status_code=404, detail="Title not found")

    # Get genre IDs for this title
    genre_result = await db.execute(
        select(TitleGenre.genre_id).where(TitleGenre.title_id == title_id)
    )
    genre_ids = [str(row[0]) for row in genre_result.all()]

    return {
        "id": str(title.id),
        "title": title.title,
        "title_type": title.title_type,
        "synopsis_short": title.synopsis_short,
        "synopsis_long": title.synopsis_long,
        "release_year": title.release_year,
        "duration_minutes": title.duration_minutes,
        "age_rating": title.age_rating,
        "country_of_origin": title.country_of_origin,
        "language": title.language,
        "poster_url": title.poster_url,
        "landscape_url": title.landscape_url,
        "logo_url": title.logo_url,
        "hls_manifest_url": title.hls_manifest_url,
        "is_featured": title.is_featured,
        "mood_tags": title.mood_tags or [],
        "theme_tags": title.theme_tags or [],
        "genre_ids": genre_ids,
        "created_at": title.created_at.isoformat() + "Z" if title.created_at else None,
    }


@router.put("/titles/{title_id}", response_model=TitleAdminResponse)
async def update_title(title_id: uuid.UUID, body: TitleUpdateRequest, db: DB, user: AdminUser):
    """Update an existing VOD title."""


    result = await db.execute(select(Title).where(Title.id == title_id))
    title = result.scalar_one_or_none()
    if title is None:
        raise HTTPException(status_code=404, detail="Title not found")

    update_data = body.model_dump(exclude_unset=True)
    genre_ids = update_data.pop("genre_ids", None)

    for field, value in update_data.items():
        setattr(title, field, value)

    # Replace genre links when provided.
    if genre_ids is not None:
        await db.execute(delete(TitleGenre).where(TitleGenre.title_id == title_id))
        for gid in genre_ids:
            db.add(TitleGenre(title_id=title_id, genre_id=gid))

    await db.commit()
    await db.refresh(title)

    # Check embedding existence.
    emb = await db.execute(
        select(ContentEmbedding.title_id).where(ContentEmbedding.title_id == title_id)
    )
    has_emb = emb.scalar_one_or_none() is not None

    return TitleAdminResponse(
        id=title.id,
        title=title.title,
        title_type=title.title_type,
        release_year=title.release_year,
        age_rating=title.age_rating,
        poster_url=title.poster_url,
        is_featured=title.is_featured,
        has_embedding=has_emb,
        created_at=title.created_at,
    )


@router.delete("/titles/{title_id}", status_code=204)
async def delete_title(title_id: uuid.UUID, db: DB, user: AdminUser):
    """Delete a title and its related data (cascade)."""


    result = await db.execute(select(Title).where(Title.id == title_id))
    title = result.scalar_one_or_none()
    if title is None:
        raise HTTPException(status_code=404, detail="Title not found")

    await db.delete(title)
    await db.commit()


# ---------------------------------------------------------------------------
# Users (read-only)
# ---------------------------------------------------------------------------


@router.get("/users")
async def list_users(db: DB, user: AdminUser):
    """List all users with profile counts."""


    result = await db.execute(
        select(
            User.id,
            User.email,
            User.subscription_tier,
            User.is_admin,
            User.created_at,
            func.count(Profile.id).label("profiles_count"),
        )
        .outerjoin(Profile, Profile.user_id == User.id)
        .group_by(User.id)
        .order_by(User.created_at)
    )
    rows = result.all()
    return [
        {
            "id": str(r.id),
            "email": r.email,
            "subscription_tier": r.subscription_tier,
            "is_admin": r.is_admin,
            "created_at": r.created_at.isoformat() + "Z" if r.created_at else None,
            "profiles_count": r.profiles_count,
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Channels CRUD
# ---------------------------------------------------------------------------


@router.get("/channels", response_model=list[ChannelResponse])
async def list_channels(db: DB, user: AdminUser):
    """List all channels (admin view)."""


    result = await db.execute(select(Channel).order_by(Channel.channel_number))
    channels = result.scalars().all()
    return [
        ChannelResponse(
            id=ch.id,
            name=ch.name,
            channel_number=ch.channel_number,
            logo_url=ch.logo_url,
            genre=ch.genre,
            is_hd=ch.is_hd,
            is_favorite=False,
            hls_live_url=ch.hls_live_url,
        )
        for ch in channels
    ]


@router.post("/channels", response_model=ChannelResponse, status_code=201)
async def create_channel(body: ChannelCreateRequest, db: DB, user: AdminUser):
    """Create a new channel."""


    channel = Channel(
        name=body.name,
        channel_number=body.channel_number,
        logo_url=body.logo_url,
        genre=body.genre,
        is_hd=body.is_hd,
        hls_live_url=body.hls_live_url,
    )
    db.add(channel)
    await db.commit()
    await db.refresh(channel)

    return ChannelResponse(
        id=channel.id,
        name=channel.name,
        channel_number=channel.channel_number,
        logo_url=channel.logo_url,
        genre=channel.genre,
        is_hd=channel.is_hd,
        is_favorite=False,
        hls_live_url=channel.hls_live_url,
    )


@router.put("/channels/{channel_id}", response_model=ChannelResponse)
async def update_channel(channel_id: uuid.UUID, body: ChannelUpdateRequest, db: DB, user: AdminUser):
    """Update an existing channel."""


    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one_or_none()
    if channel is None:
        raise HTTPException(status_code=404, detail="Channel not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(channel, field, value)

    await db.commit()
    await db.refresh(channel)

    return ChannelResponse(
        id=channel.id,
        name=channel.name,
        channel_number=channel.channel_number,
        logo_url=channel.logo_url,
        genre=channel.genre,
        is_hd=channel.is_hd,
        is_favorite=False,
        hls_live_url=channel.hls_live_url,
    )


# ---------------------------------------------------------------------------
# Schedule CRUD
# ---------------------------------------------------------------------------


@router.get("/schedule", response_model=list[ScheduleEntryResponse])
async def list_schedule(
    db: DB,
    user: AdminUser,
    channel_id: uuid.UUID = Query(..., description="Channel to fetch schedule for"),
    day: date = Query(default=None, alias="date", description="Date in YYYY-MM-DD format"),
):
    """List schedule entries for a channel on a given date."""


    if day is None:
        from datetime import datetime, timezone
        day = datetime.now(timezone.utc).date()

    from datetime import datetime, time, timezone
    start = datetime.combine(day, time.min, tzinfo=timezone.utc)
    end = datetime.combine(day, time.max, tzinfo=timezone.utc)

    result = await db.execute(
        select(ScheduleEntry)
        .where(
            ScheduleEntry.channel_id == channel_id,
            ScheduleEntry.start_time >= start,
            ScheduleEntry.start_time <= end,
        )
        .order_by(ScheduleEntry.start_time)
    )
    return result.scalars().all()


@router.post("/schedule", response_model=ScheduleEntryResponse, status_code=201)
async def create_schedule_entry(body: ScheduleEntryCreateRequest, db: DB, user: AdminUser):
    """Create a new schedule entry."""


    entry = ScheduleEntry(
        channel_id=body.channel_id,
        title=body.title,
        synopsis=body.synopsis,
        genre=body.genre,
        start_time=body.start_time,
        end_time=body.end_time,
        age_rating=body.age_rating,
        is_new=body.is_new,
        is_repeat=body.is_repeat,
        series_title=body.series_title,
        season_number=body.season_number,
        episode_number=body.episode_number,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


@router.put("/schedule/{entry_id}", response_model=ScheduleEntryResponse)
async def update_schedule_entry(entry_id: uuid.UUID, body: ScheduleEntryUpdateRequest, db: DB, user: AdminUser):
    """Update a schedule entry."""


    result = await db.execute(select(ScheduleEntry).where(ScheduleEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if entry is None:
        raise HTTPException(status_code=404, detail="Schedule entry not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)

    await db.commit()
    await db.refresh(entry)
    return entry


@router.delete("/schedule/{entry_id}", status_code=204)
async def delete_schedule_entry(entry_id: uuid.UUID, db: DB, user: AdminUser):
    """Delete a schedule entry."""


    result = await db.execute(select(ScheduleEntry).where(ScheduleEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if entry is None:
        raise HTTPException(status_code=404, detail="Schedule entry not found")

    await db.delete(entry)
    await db.commit()


# ---------------------------------------------------------------------------
# Embedding Generation
# ---------------------------------------------------------------------------


@router.post("/embeddings/generate", response_model=EmbeddingGenerationResponse)
async def generate_embeddings(
    db: DB,
    user: AdminUser,
    regenerate: bool = Query(False, description="Delete all existing embeddings and regenerate from scratch"),
):
    """Trigger embedding generation for all titles that do not yet have one.

    Pass ``?regenerate=true`` to rebuild every embedding (e.g. after changing
    the text composition).
    """


    from app.services.embedding_service import generate_all_embeddings

    count = await generate_all_embeddings(db, regenerate=regenerate)
    return EmbeddingGenerationResponse(new_embeddings_created=count)
