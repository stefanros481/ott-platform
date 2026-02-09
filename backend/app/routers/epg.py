"""EPG router -- channels, schedule, now-playing, favourites."""

import uuid
from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.dependencies import DB, CurrentUser
from app.schemas.epg import (
    ChannelResponse,
    NowPlayingResponse,
    ScheduleEntryResponse,
)
from app.services import epg_service

router = APIRouter()


@router.get("/channels", response_model=list[ChannelResponse])
async def list_channels(
    db: DB,
    profile_id: uuid.UUID | None = Query(None, description="Active profile for AI ordering"),
):
    """List all channels.

    When *profile_id* is provided, favourites are flagged and sorted to the top
    (basic AI channel ordering).
    """
    channels = await epg_service.get_channels(db, profile_id=profile_id)
    return channels


@router.get("/schedule/{channel_id}", response_model=list[ScheduleEntryResponse])
async def get_schedule(
    channel_id: uuid.UUID,
    db: DB,
    day: date = Query(default=None, alias="date", description="Date in YYYY-MM-DD format"),
):
    """Get the schedule for a channel on a given date (defaults to today UTC)."""
    if day is None:
        from datetime import datetime, timezone

        day = datetime.now(timezone.utc).date()
    entries = await epg_service.get_schedule(db, channel_id, day)
    return entries


@router.get("/now", response_model=list[NowPlayingResponse])
async def now_playing(db: DB):
    """Return what is currently airing on every channel, plus the next programme."""
    results = await epg_service.get_now_playing(db)
    return results


@router.get("/search", response_model=list[ScheduleEntryResponse])
async def search_epg(
    db: DB,
    q: str = Query(min_length=1, description="Search term"),
):
    """Search EPG schedule entries by title (case-insensitive)."""
    entries = await epg_service.search_schedule(db, q)
    return entries


@router.post("/favorites/{channel_id}", status_code=204)
async def add_favorite(
    channel_id: uuid.UUID,
    db: DB,
    user: CurrentUser,
    profile_id: uuid.UUID = Query(..., description="Active profile"),
):
    """Add a channel to the profile's favourites."""
    await epg_service.add_favorite(db, profile_id, channel_id)


@router.delete("/favorites/{channel_id}", status_code=204)
async def remove_favorite(
    channel_id: uuid.UUID,
    db: DB,
    user: CurrentUser,
    profile_id: uuid.UUID = Query(..., description="Active profile"),
):
    """Remove a channel from the profile's favourites."""
    await epg_service.remove_favorite(db, profile_id, channel_id)
