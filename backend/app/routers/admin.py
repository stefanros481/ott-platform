"""Admin router -- platform stats, CRUD for titles / channels / schedule, embedding generation,
packages, offers, and user subscription management (Feature 012)."""

import uuid
from datetime import date

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import and_, delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import DB, AdminUser, RedisClient
from app.services.search_service import escape_like
from app.models.catalog import Title, TitleGenre
from app.models.embedding import ContentEmbedding
from app.models.entitlement import ContentPackage, PackageContent, TitleOffer, UserEntitlement
from app.models.epg import Channel, ScheduleEntry
from app.models.user import Profile, User
from app.schemas.admin import (
    EmbeddingGenerationResponse,
    PerformanceMetricsResponse,
    PlatformStatsResponse,
    TitleAdminResponse,
    TitleCreateRequest,
    TitlePaginatedResponse,
    TitleUpdateRequest,
)
from app.schemas.entitlement import (
    OfferCreate,
    OfferResponse,
    OfferUpdate,
    PackageCreate,
    PackageResponse,
    PackageUpdate,
    UserEntitlementResponse,
    UserSubscriptionUpdate,
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


# ---------------------------------------------------------------------------
# Performance Metrics (009-backend-performance)
# ---------------------------------------------------------------------------


@router.get("/metrics", response_model=PerformanceMetricsResponse)
async def get_performance_metrics(_user: AdminUser):
    """Return in-process performance metrics (heartbeat stats, config cache)."""
    import time

    from app.services.metrics_service import config_cache, perf_metrics

    snapshot = perf_metrics.snapshot()
    return PerformanceMetricsResponse(
        uptime_seconds=round(time.monotonic(), 2),
        heartbeat=snapshot["heartbeat"],
        config_cache={
            **snapshot["config_cache"],
            "current_size": config_cache.current_size,
            "max_size": config_cache.max_size,
        },
    )


# ---------------------------------------------------------------------------
# T016 — Package CRUD (Feature 012)
# ---------------------------------------------------------------------------


async def _package_response(pkg: ContentPackage, db: AsyncSession) -> PackageResponse:
    """Build a PackageResponse with the denormalized title_count."""
    count_result = await db.execute(
        select(func.count()).select_from(PackageContent).where(
            and_(PackageContent.package_id == pkg.id, PackageContent.content_type == "vod_title")
        )
    )
    title_count = count_result.scalar_one()
    return PackageResponse(
        id=pkg.id,
        name=pkg.name,
        description=pkg.description,
        tier=pkg.tier,
        max_streams=pkg.max_streams,
        price_cents=pkg.price_cents,
        currency=pkg.currency,
        title_count=title_count,
    )


@router.get("/packages", response_model=list[PackageResponse])
async def list_packages(db: DB, user: AdminUser) -> list[PackageResponse]:
    """List all subscription packages."""
    result = await db.execute(select(ContentPackage).order_by(ContentPackage.name))
    packages = result.scalars().all()
    return [await _package_response(pkg, db) for pkg in packages]


@router.post("/packages", response_model=PackageResponse, status_code=201)
async def create_package(body: PackageCreate, db: DB, user: AdminUser) -> PackageResponse:
    """Create a new subscription package."""
    pkg = ContentPackage(
        name=body.name,
        description=body.description,
        tier=body.tier,
        max_streams=body.max_streams,
        price_cents=body.price_cents,
        currency=body.currency,
    )
    db.add(pkg)
    await db.commit()
    await db.refresh(pkg)
    return await _package_response(pkg, db)


@router.put("/packages/{package_id}", response_model=PackageResponse)
async def update_package(
    package_id: uuid.UUID, body: PackageUpdate, db: DB, user: AdminUser
) -> PackageResponse:
    """Update a package's name, description, or tier."""
    result = await db.execute(select(ContentPackage).where(ContentPackage.id == package_id))
    pkg = result.scalar_one_or_none()
    if pkg is None:
        raise HTTPException(status_code=404, detail="Package not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(pkg, field, value)
    await db.commit()
    await db.refresh(pkg)
    return await _package_response(pkg, db)


@router.delete("/packages/{package_id}", status_code=204)
async def delete_package(package_id: uuid.UUID, db: DB, user: AdminUser) -> None:
    """Delete a package. Fails with 409 if active user entitlements exist."""
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    active_ent = await db.execute(
        select(UserEntitlement).where(
            and_(
                UserEntitlement.package_id == package_id,
                (UserEntitlement.expires_at.is_(None)) | (UserEntitlement.expires_at > now),
            )
        )
    )
    if active_ent.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete package with active user entitlements",
        )

    result = await db.execute(select(ContentPackage).where(ContentPackage.id == package_id))
    pkg = result.scalar_one_or_none()
    if pkg is None:
        raise HTTPException(status_code=404, detail="Package not found")

    await db.delete(pkg)
    await db.commit()


# ---------------------------------------------------------------------------
# T017 — Package Title Assignment (Feature 012)
# ---------------------------------------------------------------------------


@router.get("/packages/{package_id}/titles")
async def list_package_titles(
    package_id: uuid.UUID,
    db: DB,
    user: AdminUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """List all titles assigned to a package (paginated)."""
    pkg = (await db.execute(select(ContentPackage).where(ContentPackage.id == package_id))).scalar_one_or_none()
    if pkg is None:
        raise HTTPException(status_code=404, detail="Package not found")

    total = (
        await db.execute(
            select(func.count()).select_from(PackageContent).where(
                and_(
                    PackageContent.package_id == package_id,
                    PackageContent.content_type == "vod_title",
                )
            )
        )
    ).scalar() or 0

    offset = (page - 1) * page_size
    rows = (
        await db.execute(
            select(Title)
            .join(PackageContent, and_(
                PackageContent.content_id == Title.id,
                PackageContent.package_id == package_id,
                PackageContent.content_type == "vod_title",
            ))
            .order_by(Title.title)
            .offset(offset)
            .limit(page_size)
        )
    ).scalars().all()

    items = [
        TitleAdminResponse(
            id=t.id,
            title=t.title,
            title_type=t.title_type,
            release_year=t.release_year,
            age_rating=t.age_rating,
            poster_url=t.poster_url,
            is_featured=t.is_featured,
            has_embedding=False,
            created_at=t.created_at,
        )
        for t in rows
    ]
    return TitlePaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("/packages/{package_id}/titles", status_code=201)
async def assign_title_to_package(
    package_id: uuid.UUID,
    body: dict,
    db: DB,
    user: AdminUser,
):
    """Assign a title to a package."""
    title_id = body.get("title_id")
    if not title_id:
        raise HTTPException(status_code=422, detail="title_id is required")
    title_id = uuid.UUID(str(title_id))

    # Verify package and title exist
    pkg = (await db.execute(select(ContentPackage).where(ContentPackage.id == package_id))).scalar_one_or_none()
    if pkg is None:
        raise HTTPException(status_code=404, detail="Package not found")

    title = (await db.execute(select(Title).where(Title.id == title_id))).scalar_one_or_none()
    if title is None:
        raise HTTPException(status_code=404, detail="Title not found")

    # Check for duplicate
    existing = await db.execute(
        select(PackageContent).where(
            and_(
                PackageContent.package_id == package_id,
                PackageContent.content_type == "vod_title",
                PackageContent.content_id == title_id,
            )
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Title already assigned to this package")

    db.add(PackageContent(package_id=package_id, content_type="vod_title", content_id=title_id))
    await db.commit()
    return {"package_id": str(package_id), "title_id": str(title_id), "content_type": "vod_title"}


@router.delete("/packages/{package_id}/titles/{title_id}", status_code=204)
async def remove_title_from_package(
    package_id: uuid.UUID,
    title_id: uuid.UUID,
    db: DB,
    user: AdminUser,
) -> None:
    """Remove a title from a package."""
    result = await db.execute(
        select(PackageContent).where(
            and_(
                PackageContent.package_id == package_id,
                PackageContent.content_type == "vod_title",
                PackageContent.content_id == title_id,
            )
        )
    )
    assignment = result.scalar_one_or_none()
    if assignment is None:
        raise HTTPException(status_code=404, detail="Title assignment not found")

    await db.delete(assignment)
    await db.commit()


# ---------------------------------------------------------------------------
# T018 — Offer CRUD (Feature 012)
# ---------------------------------------------------------------------------


@router.get("/titles/{title_id}/offers", response_model=list[OfferResponse])
async def list_title_offers(title_id: uuid.UUID, db: DB, user: AdminUser) -> list[OfferResponse]:
    """List all offers (including inactive) for a title."""
    result = await db.execute(
        select(TitleOffer)
        .where(TitleOffer.title_id == title_id)
        .order_by(TitleOffer.created_at)
    )
    return result.scalars().all()


@router.post("/titles/{title_id}/offers", response_model=OfferResponse, status_code=201)
async def create_title_offer(
    title_id: uuid.UUID, body: OfferCreate, db: DB, user: AdminUser
) -> OfferResponse:
    """Create an offer for a title. Fails if an active offer of the same type already exists."""
    # Validate title exists
    title = (await db.execute(select(Title).where(Title.id == title_id))).scalar_one_or_none()
    if title is None:
        raise HTTPException(status_code=404, detail="Title not found")

    # Validate rental_window_hours required for rent
    if body.offer_type == "rent" and body.rental_window_hours is None:
        raise HTTPException(
            status_code=422,
            detail="rental_window_hours is required when offer_type is 'rent'",
        )

    # Check for duplicate active offer of same type
    existing = await db.execute(
        select(TitleOffer).where(
            and_(
                TitleOffer.title_id == title_id,
                TitleOffer.offer_type == body.offer_type,
                TitleOffer.is_active.is_(True),
            )
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409,
            detail=f"An active {body.offer_type} offer already exists for this title",
        )

    offer = TitleOffer(
        title_id=title_id,
        offer_type=body.offer_type,
        price_cents=body.price_cents,
        currency=body.currency,
        rental_window_hours=body.rental_window_hours,
    )
    db.add(offer)
    await db.commit()
    await db.refresh(offer)
    return offer


@router.patch("/titles/{title_id}/offers/{offer_id}", response_model=OfferResponse)
async def update_title_offer(
    title_id: uuid.UUID,
    offer_id: uuid.UUID,
    body: OfferUpdate,
    db: DB,
    user: AdminUser,
) -> OfferResponse:
    """Update an offer (e.g., change price, deactivate)."""
    result = await db.execute(
        select(TitleOffer).where(
            and_(TitleOffer.id == offer_id, TitleOffer.title_id == title_id)
        )
    )
    offer = result.scalar_one_or_none()
    if offer is None:
        raise HTTPException(status_code=404, detail="Offer not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(offer, field, value)

    await db.commit()
    await db.refresh(offer)
    return offer


# ---------------------------------------------------------------------------
# T019 — User Subscription Management (Feature 012)
# ---------------------------------------------------------------------------


@router.patch("/users/{user_id}/subscription")
async def update_user_subscription(
    user_id: uuid.UUID,
    body: UserSubscriptionUpdate,
    db: DB,
    user: AdminUser,
    redis: RedisClient,
):
    """Update a user's subscription. Creates or replaces SVOD entitlement.

    Set package_id to null to cancel the subscription.
    Invalidates the entitlement cache for the affected user.
    """
    from app.services import entitlement_service
    from datetime import datetime, timezone

    # Verify target user exists
    target_user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if target_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    now = datetime.now(timezone.utc)

    # Expire all existing SVOD entitlements for this user
    existing_svod = await db.execute(
        select(UserEntitlement).where(
            and_(
                UserEntitlement.user_id == user_id,
                UserEntitlement.source_type == "subscription",
            )
        )
    )
    for ent in existing_svod.scalars().all():
        ent.expires_at = now
    await db.flush()

    subscription_tier = None
    package_id = body.package_id

    if package_id is not None:
        # Verify package exists and get tier
        pkg = (await db.execute(select(ContentPackage).where(ContentPackage.id == package_id))).scalar_one_or_none()
        if pkg is None:
            raise HTTPException(status_code=404, detail="Package not found")
        subscription_tier = pkg.tier

        # Create new subscription entitlement
        new_ent = UserEntitlement(
            user_id=user_id,
            package_id=package_id,
            source_type="subscription",
            expires_at=body.expires_at,
        )
        db.add(new_ent)

    # Update User.subscription_tier for display
    target_user.subscription_tier = subscription_tier
    await db.commit()

    # Invalidate the entitlement cache for this user
    await entitlement_service.invalidate_entitlement_cache(user_id, redis)

    return {
        "user_id": str(user_id),
        "package_id": str(package_id) if package_id else None,
        "subscription_tier": subscription_tier,
        "expires_at": body.expires_at.isoformat() if body.expires_at else None,
    }


@router.get("/users/{user_id}/entitlements", response_model=list[UserEntitlementResponse])
async def list_user_entitlements(
    user_id: uuid.UUID,
    db: DB,
    user: AdminUser,
    include_expired: bool = Query(False, description="Include expired entitlements"),
) -> list[UserEntitlementResponse]:
    """List all entitlements for a user (SVOD subscriptions + TVOD purchases).

    By default only active (non-expired) entitlements are returned.
    Pass ?include_expired=true to see the full history.
    """
    from datetime import datetime, timezone

    target = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")

    query = select(UserEntitlement).where(UserEntitlement.user_id == user_id)
    if not include_expired:
        now = datetime.now(timezone.utc)
        query = query.where(
            (UserEntitlement.expires_at.is_(None)) | (UserEntitlement.expires_at > now)
        )
    query = query.order_by(UserEntitlement.granted_at.desc())

    entitlements = (await db.execute(query)).scalars().all()

    # Bulk-fetch referenced packages and titles for denormalisation
    pkg_ids = {e.package_id for e in entitlements if e.package_id}
    title_ids = {e.title_id for e in entitlements if e.title_id}

    packages: dict[uuid.UUID, ContentPackage] = {}
    if pkg_ids:
        rows = (await db.execute(select(ContentPackage).where(ContentPackage.id.in_(pkg_ids)))).scalars().all()
        packages = {p.id: p for p in rows}

    titles: dict[uuid.UUID, Title] = {}
    if title_ids:
        rows = (await db.execute(select(Title).where(Title.id.in_(title_ids)))).scalars().all()
        titles = {t.id: t for t in rows}

    now = datetime.now(timezone.utc)
    result = []
    for e in entitlements:
        pkg = packages.get(e.package_id) if e.package_id else None
        title = titles.get(e.title_id) if e.title_id else None
        result.append(UserEntitlementResponse(
            id=e.id,
            source_type=e.source_type,
            package_id=e.package_id,
            package_name=pkg.name if pkg else None,
            package_tier=pkg.tier if pkg else None,
            title_id=e.title_id,
            title_name=title.title if title else None,
            granted_at=e.granted_at,
            expires_at=e.expires_at,
            is_active=e.expires_at is None or e.expires_at > now,
        ))
    return result


@router.delete("/users/{user_id}/entitlements/{entitlement_id}", status_code=204)
async def revoke_user_entitlement(
    user_id: uuid.UUID,
    entitlement_id: uuid.UUID,
    db: DB,
    user: AdminUser,
    redis: RedisClient,
) -> None:
    """Revoke a specific entitlement immediately by setting expires_at = now.

    Works for both SVOD subscriptions and TVOD purchases.
    Invalidates the entitlement cache for the affected user.
    """
    from datetime import datetime, timezone
    from app.services import entitlement_service

    ent = (
        await db.execute(
            select(UserEntitlement).where(
                and_(UserEntitlement.id == entitlement_id, UserEntitlement.user_id == user_id)
            )
        )
    ).scalar_one_or_none()

    if ent is None:
        raise HTTPException(status_code=404, detail="Entitlement not found")

    ent.expires_at = datetime.now(timezone.utc)

    # If this was the active SVOD subscription, clear the user's tier
    if ent.source_type == "subscription":
        target_user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if target_user:
            target_user.subscription_tier = None

    await db.commit()
    await entitlement_service.invalidate_entitlement_cache(user_id, redis)


# ---------------------------------------------------------------------------
# T043 — SimLive Admin Endpoints (Feature 016)
# ---------------------------------------------------------------------------

from app.schemas.tstv import (
    CleanupResult,
    SimLiveChannelStatus,
    TSTVRulesResponse,
    TSTVRulesUpdate,
)


@router.get("/simlive/status", response_model=list[SimLiveChannelStatus])
async def simlive_status(db: DB, user: AdminUser):
    """Get status of all SimLive channels."""
    from app.services.simlive_manager import SimLiveManager

    # Query channels with cdn_channel_key so they always appear in the panel
    result = await db.execute(
        select(Channel.cdn_channel_key)
        .where(Channel.cdn_channel_key.isnot(None))
        .where(Channel.cdn_channel_key != "")
        .order_by(Channel.cdn_channel_key)
    )
    db_keys = [row[0] for row in result.all()]

    return SimLiveManager.list_all_statuses(channel_keys=db_keys if db_keys else None)


@router.post("/simlive/{channel_key}/start")
async def simlive_start(channel_key: str, db: DB, user: AdminUser):
    """Start SimLive for a channel."""
    from app.services.simlive_manager import SimLiveManager
    from app.services import drm_service

    drm_key = await drm_service.get_or_create_active_key(db, channel_key)
    await SimLiveManager.start_channel(
        channel_key,
        key_id_hex=drm_key.key_id.hex,
        key_hex=drm_key.key_value.hex(),
    )
    return {"status": "started", "channel_key": channel_key}


@router.post("/simlive/{channel_key}/stop")
async def simlive_stop(channel_key: str, user: AdminUser):
    """Stop SimLive for a channel."""
    from app.services.simlive_manager import SimLiveManager

    await SimLiveManager.stop_channel(channel_key)
    return {"status": "stopped", "channel_key": channel_key}


@router.post("/simlive/{channel_key}/restart")
async def simlive_restart(channel_key: str, db: DB, user: AdminUser):
    """Restart SimLive for a channel."""
    from app.services.simlive_manager import SimLiveManager
    from app.services import drm_service

    drm_key = await drm_service.get_or_create_active_key(db, channel_key)
    await SimLiveManager.restart_channel(
        channel_key,
        key_id_hex=drm_key.key_id.hex,
        key_hex=drm_key.key_value.hex(),
    )
    return {"status": "restarted", "channel_key": channel_key}


@router.post("/simlive/cleanup", response_model=CleanupResult)
async def simlive_cleanup(user: AdminUser):
    """Clean up old segments across all channels."""
    from app.services.simlive_manager import SimLiveManager

    result = SimLiveManager.cleanup_all()
    return result


# ---------------------------------------------------------------------------
# T044 — TSTV Rules Admin Endpoints (Feature 016)
# ---------------------------------------------------------------------------


@router.get("/tstv/rules", response_model=list[TSTVRulesResponse])
async def list_tstv_rules(db: DB, user: AdminUser):
    """List TSTV rules for all channels."""
    result = await db.execute(select(Channel).order_by(Channel.channel_number))
    channels = result.scalars().all()
    return [
        TSTVRulesResponse(
            channel_id=ch.id,
            channel_name=ch.name,
            tstv_enabled=ch.tstv_enabled,
            startover_enabled=ch.startover_enabled,
            catchup_enabled=ch.catchup_enabled,
            cutv_window_hours=ch.cutv_window_hours,
            catchup_window_hours=getattr(ch, "catchup_window_hours", ch.cutv_window_hours),
        )
        for ch in channels
    ]


VALID_CUTV_HOURS = {2, 6, 12, 24, 48, 72, 168}


@router.put("/tstv/rules/{channel_id}", response_model=TSTVRulesResponse)
async def update_tstv_rules(
    channel_id: uuid.UUID,
    body: TSTVRulesUpdate,
    db: DB,
    user: AdminUser,
):
    """Update TSTV rules for a channel."""
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one_or_none()
    if channel is None:
        raise HTTPException(status_code=404, detail="Channel not found")

    if body.cutv_window_hours is not None and body.cutv_window_hours not in VALID_CUTV_HOURS:
        raise HTTPException(
            status_code=422,
            detail=f"cutv_window_hours must be one of {sorted(VALID_CUTV_HOURS)}",
        )

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(channel, field, value)

    await db.commit()
    await db.refresh(channel)

    return TSTVRulesResponse(
        channel_id=channel.id,
        channel_name=channel.name,
        tstv_enabled=channel.tstv_enabled,
        startover_enabled=channel.startover_enabled,
        catchup_enabled=channel.catchup_enabled,
        cutv_window_hours=channel.cutv_window_hours,
        catchup_window_hours=getattr(channel, "catchup_window_hours", channel.cutv_window_hours),
    )
