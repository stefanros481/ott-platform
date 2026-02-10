"""Pydantic schemas for EPG (Electronic Program Guide) endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# -- Response schemas ---------------------------------------------------------


class ChannelResponse(BaseModel):
    """A single TV channel."""

    id: uuid.UUID
    name: str
    channel_number: int
    logo_url: str | None = None
    genre: str | None = None
    is_hd: bool = True
    is_favorite: bool = False
    hls_live_url: str | None = None

    model_config = {"from_attributes": True}


class ScheduleEntryResponse(BaseModel):
    """A single programme in the schedule grid."""

    id: uuid.UUID
    channel_id: uuid.UUID
    title: str
    synopsis: str | None = None
    genre: str | None = None
    start_time: datetime
    end_time: datetime
    age_rating: str | None = None
    is_new: bool = False
    is_repeat: bool = False
    series_title: str | None = None
    season_number: int | None = None
    episode_number: int | None = None

    model_config = {"from_attributes": True}


class NowPlayingResponse(BaseModel):
    """What is currently airing on a channel, plus the next programme."""

    channel: ChannelResponse
    current_program: ScheduleEntryResponse
    next_program: ScheduleEntryResponse | None = None


# -- Request schemas ----------------------------------------------------------


class ChannelCreateRequest(BaseModel):
    """Create a new channel (admin)."""

    name: str = Field(min_length=1, max_length=200)
    channel_number: int = Field(ge=1)
    logo_url: str | None = None
    genre: str | None = None
    is_hd: bool = True
    hls_live_url: str | None = None


class ChannelUpdateRequest(BaseModel):
    """Update an existing channel (admin)."""

    name: str | None = None
    channel_number: int | None = None
    logo_url: str | None = None
    genre: str | None = None
    is_hd: bool | None = None
    hls_live_url: str | None = None


class ScheduleEntryCreateRequest(BaseModel):
    """Create a schedule entry (admin)."""

    channel_id: uuid.UUID
    title: str = Field(min_length=1, max_length=500)
    synopsis: str | None = None
    genre: str | None = None
    start_time: datetime
    end_time: datetime
    age_rating: str | None = None
    is_new: bool = False
    is_repeat: bool = False
    series_title: str | None = None
    season_number: int | None = None
    episode_number: int | None = None


class ScheduleEntryUpdateRequest(BaseModel):
    """Update a schedule entry (admin)."""

    title: str | None = None
    synopsis: str | None = None
    genre: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    age_rating: str | None = None
    is_new: bool | None = None
    is_repeat: bool | None = None
    series_title: str | None = None
    season_number: int | None = None
    episode_number: int | None = None
