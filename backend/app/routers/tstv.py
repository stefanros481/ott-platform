"""TSTV router — Start Over, Catch-Up, and session tracking endpoints."""

import uuid
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from app.dependencies import CurrentUser, DB, OptionalVerifiedProfileId
from app.models.epg import Channel, ScheduleEntry
from app.models.viewing import Bookmark
from app.schemas.tstv import (
    CatchUpByDateResponse,
    CatchUpListResponse,
    CatchUpProgram,
    ScheduleEntrySummary,
    StartOverAvailability,
    TSTVChannelResponse,
    TSTVSessionCreate,
    TSTVSessionResponse,
    TSTVSessionUpdate,
)
from app.services import manifest_generator

from sqlalchemy import and_, select
from sqlalchemy.sql import func as sa_func

router = APIRouter()


# ---------------------------------------------------------------------------
# T016 — GET /channels
# ---------------------------------------------------------------------------

@router.get("/channels", response_model=list[TSTVChannelResponse])
async def list_tstv_channels(
    db: DB,
    user: CurrentUser,
):
    """List all channels with TSTV enabled."""
    result = await db.execute(
        select(Channel).where(Channel.tstv_enabled.is_(True)).order_by(Channel.channel_number)
    )
    channels = result.scalars().all()
    return [TSTVChannelResponse.model_validate(ch) for ch in channels]


# ---------------------------------------------------------------------------
# T017 — GET /startover/{channel_id}
# ---------------------------------------------------------------------------

async def _get_current_entry(db, channel_id: uuid.UUID) -> tuple[Channel, ScheduleEntry]:
    """Fetch channel and currently-airing schedule entry."""
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one_or_none()
    if channel is None:
        raise HTTPException(status_code=404, detail="Channel not found")

    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(ScheduleEntry).where(
            and_(
                ScheduleEntry.channel_id == channel_id,
                ScheduleEntry.start_time <= now,
                ScheduleEntry.end_time > now,
            )
        )
    )
    entry = result.scalar_one_or_none()
    if entry is None:
        raise HTTPException(status_code=404, detail="No program currently airing on this channel")

    return channel, entry


@router.get("/startover/{channel_id}", response_model=StartOverAvailability)
async def get_startover_availability(
    channel_id: uuid.UUID,
    db: DB,
    user: CurrentUser,
):
    """Check if start-over is available for the current program on a channel."""
    channel, entry = await _get_current_entry(db, channel_id)

    now = datetime.now(timezone.utc)
    elapsed = int((now - entry.start_time).total_seconds())

    startover_available = (
        channel.tstv_enabled
        and channel.startover_enabled
        and entry.startover_eligible
    )

    return StartOverAvailability(
        channel_id=channel.id,
        schedule_entry=ScheduleEntrySummary.model_validate(entry),
        startover_available=startover_available,
        elapsed_seconds=elapsed,
    )


# ---------------------------------------------------------------------------
# T018 — GET /startover/{channel_id}/manifest
# ---------------------------------------------------------------------------

@router.api_route("/startover/{channel_id}/manifest", methods=["GET", "HEAD"])
async def get_startover_manifest(
    channel_id: uuid.UUID,
    db: DB,
    user: CurrentUser,
    schedule_entry_id: uuid.UUID = Query(..., description="Schedule entry UUID"),
):
    """Generate HLS EVENT manifest for start-over playback."""
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one_or_none()
    if channel is None:
        raise HTTPException(status_code=404, detail="Channel not found")

    if not channel.tstv_enabled or not channel.startover_enabled:
        raise HTTPException(status_code=403, detail="Start-over not enabled for this channel")

    if not channel.cdn_channel_key:
        raise HTTPException(status_code=403, detail="Channel not configured for TSTV")

    result = await db.execute(
        select(ScheduleEntry).where(
            and_(
                ScheduleEntry.id == schedule_entry_id,
                ScheduleEntry.channel_id == channel_id,
            )
        )
    )
    entry = result.scalar_one_or_none()
    if entry is None:
        raise HTTPException(status_code=404, detail="Schedule entry not found")

    if not entry.startover_eligible:
        raise HTTPException(status_code=403, detail="Program not eligible for start-over")

    m3u8 = manifest_generator.build_event_manifest(
        channel_key=channel.cdn_channel_key,
        start_time=entry.start_time,
    )

    return Response(content=m3u8, media_type="application/vnd.apple.mpegurl")


# ---------------------------------------------------------------------------
# T029 — GET /catchup/{channel_id}
# ---------------------------------------------------------------------------

@router.get("/catchup/{channel_id}", response_model=CatchUpListResponse)
async def list_catchup_programs(
    channel_id: uuid.UUID,
    db: DB,
    user: CurrentUser,
    profile_id: OptionalVerifiedProfileId = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
):
    """List catch-up programs for a channel within the CUTV window."""
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one_or_none()
    if channel is None:
        raise HTTPException(status_code=404, detail="Channel not found")

    now = datetime.now(timezone.utc)
    cutv_cutoff = now - timedelta(hours=channel.cutv_window_hours)

    # Count total
    count_q = (
        select(sa_func.count())
        .select_from(ScheduleEntry)
        .where(
            and_(
                ScheduleEntry.channel_id == channel_id,
                ScheduleEntry.end_time <= now,
                ScheduleEntry.end_time > cutv_cutoff,
                ScheduleEntry.catchup_eligible.is_(True),
            )
        )
    )
    total = (await db.execute(count_q)).scalar() or 0

    # Fetch page
    q = (
        select(ScheduleEntry)
        .where(
            and_(
                ScheduleEntry.channel_id == channel_id,
                ScheduleEntry.end_time <= now,
                ScheduleEntry.end_time > cutv_cutoff,
                ScheduleEntry.catchup_eligible.is_(True),
            )
        )
        .order_by(ScheduleEntry.start_time.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(q)
    entries = result.scalars().all()

    # Build bookmark lookup for the current profile
    bookmark_map: dict[uuid.UUID, int] = {}
    if profile_id:
        entry_ids = [e.id for e in entries]
        if entry_ids:
            bk_q = select(Bookmark.content_id, Bookmark.position_seconds).where(
                and_(
                    Bookmark.profile_id == profile_id,
                    Bookmark.content_type == "tstv_catchup",
                    Bookmark.content_id.in_(entry_ids),
                    Bookmark.completed.is_(False),
                )
            )
            bk_result = await db.execute(bk_q)
            for row in bk_result:
                bookmark_map[row.content_id] = row.position_seconds

    programs = [
        CatchUpProgram(
            schedule_entry=ScheduleEntrySummary.model_validate(e),
            expires_at=e.end_time + timedelta(hours=channel.cutv_window_hours),
            bookmark_position_seconds=bookmark_map.get(e.id),
        )
        for e in entries
    ]

    return CatchUpListResponse(programs=programs, total=total)


# ---------------------------------------------------------------------------
# T030 — GET /catchup/{channel_id}/manifest
# ---------------------------------------------------------------------------

@router.api_route("/catchup/{channel_id}/manifest", methods=["GET", "HEAD"])
async def get_catchup_manifest(
    channel_id: uuid.UUID,
    db: DB,
    user: CurrentUser,
    schedule_entry_id: uuid.UUID = Query(..., description="Schedule entry UUID"),
):
    """Generate HLS VOD manifest for catch-up playback."""
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one_or_none()
    if channel is None:
        raise HTTPException(status_code=404, detail="Channel not found")

    if not channel.tstv_enabled or not channel.catchup_enabled:
        raise HTTPException(status_code=403, detail="Catch-up not enabled for this channel")

    if not channel.cdn_channel_key:
        raise HTTPException(status_code=403, detail="Channel not configured for TSTV")

    result = await db.execute(
        select(ScheduleEntry).where(
            and_(
                ScheduleEntry.id == schedule_entry_id,
                ScheduleEntry.channel_id == channel_id,
            )
        )
    )
    entry = result.scalar_one_or_none()
    if entry is None:
        raise HTTPException(status_code=404, detail="Schedule entry not found")

    if not entry.catchup_eligible:
        raise HTTPException(status_code=403, detail="program_not_eligible")

    # Enforce CUTV window
    now = datetime.now(timezone.utc)
    expires_at = entry.end_time + timedelta(hours=channel.cutv_window_hours)
    if now > expires_at:
        raise HTTPException(
            status_code=403,
            detail="catch_up_window_expired",
            headers={"X-Expires-At": expires_at.isoformat()},
        )

    m3u8 = manifest_generator.build_vod_manifest(
        channel_key=channel.cdn_channel_key,
        start_time=entry.start_time,
        end_time=entry.end_time,
    )

    return Response(content=m3u8, media_type="application/vnd.apple.mpegurl")


# ---------------------------------------------------------------------------
# T060 — GET /catchup (cross-channel date browsing)
# ---------------------------------------------------------------------------

@router.get("/catchup", response_model=CatchUpByDateResponse)
async def list_catchup_by_date(
    db: DB,
    user: CurrentUser,
    profile_id: OptionalVerifiedProfileId = None,
    browse_date: date | None = Query(default=None, alias="date", description="YYYY-MM-DD"),
    channel_id: uuid.UUID | None = Query(default=None),
    genre: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
):
    """List catch-up programs across all TSTV-enabled channels for a given date."""
    now = datetime.now(timezone.utc)
    if browse_date is None:
        browse_date = now.date()

    day_start = datetime.combine(browse_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)

    # Build filters
    filters = [
        ScheduleEntry.end_time <= now,
        ScheduleEntry.start_time >= day_start,
        ScheduleEntry.start_time < day_end,
        ScheduleEntry.catchup_eligible.is_(True),
        Channel.tstv_enabled.is_(True),
        Channel.catchup_enabled.is_(True),
    ]

    if channel_id is not None:
        filters.append(ScheduleEntry.channel_id == channel_id)
    if genre is not None:
        filters.append(ScheduleEntry.genre == genre)

    # Count
    count_q = (
        select(sa_func.count())
        .select_from(ScheduleEntry)
        .join(Channel, ScheduleEntry.channel_id == Channel.id)
        .where(and_(*filters))
    )
    total = (await db.execute(count_q)).scalar() or 0

    # Fetch
    q = (
        select(ScheduleEntry, Channel.cutv_window_hours)
        .join(Channel, ScheduleEntry.channel_id == Channel.id)
        .where(and_(*filters))
        .order_by(ScheduleEntry.start_time.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(q)
    rows = result.all()

    # Build bookmark lookup
    valid_entries = [(e, h) for e, h in rows if now <= e.end_time + timedelta(hours=h)]
    bookmark_map: dict[uuid.UUID, int] = {}
    if profile_id and valid_entries:
        entry_ids = [e.id for e, _ in valid_entries]
        bk_q = select(Bookmark.content_id, Bookmark.position_seconds).where(
            and_(
                Bookmark.profile_id == profile_id,
                Bookmark.content_type == "tstv_catchup",
                Bookmark.content_id.in_(entry_ids),
                Bookmark.completed.is_(False),
            )
        )
        bk_result = await db.execute(bk_q)
        for row in bk_result:
            bookmark_map[row.content_id] = row.position_seconds

    programs = [
        CatchUpProgram(
            schedule_entry=ScheduleEntrySummary.model_validate(entry),
            expires_at=entry.end_time + timedelta(hours=cutv_hours),
            bookmark_position_seconds=bookmark_map.get(entry.id),
        )
        for entry, cutv_hours in valid_entries
    ]

    return CatchUpByDateResponse(
        programs=programs,
        total=total,
        date=browse_date.isoformat(),
    )


# ---------------------------------------------------------------------------
# T038 — POST /sessions and PATCH /sessions/{session_id}
# ---------------------------------------------------------------------------

from app.models.tstv import TSTVSession


@router.post("/sessions", response_model=TSTVSessionResponse, status_code=201)
async def create_session(
    body: TSTVSessionCreate,
    db: DB,
    user: CurrentUser,
):
    """Record a new TSTV viewing session."""
    session = TSTVSession(
        user_id=user.id,
        profile_id=body.profile_id,
        channel_id=body.channel_id,
        schedule_entry_id=body.schedule_entry_id,
        session_type=body.session_type,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return TSTVSessionResponse.model_validate(session)


@router.patch("/sessions/{session_id}", response_model=TSTVSessionResponse)
async def update_session(
    session_id: int,
    body: TSTVSessionUpdate,
    db: DB,
    user: CurrentUser,
):
    """Update playback position and/or completion status for a TSTV session."""
    result = await db.execute(
        select(TSTVSession).where(
            and_(TSTVSession.id == session_id, TSTVSession.user_id == user.id)
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    if body.last_position_s is not None:
        session.last_position_s = body.last_position_s
    if body.completed is not None:
        session.completed = body.completed

    await db.commit()
    await db.refresh(session)
    return TSTVSessionResponse.model_validate(session)
