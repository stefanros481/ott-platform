"""Pydantic schemas for TSTV and DRM endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# DRM
# ---------------------------------------------------------------------------

class DRMKeyResponse(BaseModel):
    key_id: uuid.UUID
    key_value_hex: str
    channel_key: str
    active: bool


class ClearKeyLicenseRequest(BaseModel):
    kids: list[str]
    type: str = "temporary"


class ClearKeyLicenseResponse(BaseModel):
    keys: list[dict]


# ---------------------------------------------------------------------------
# TSTV Channels
# ---------------------------------------------------------------------------

class TSTVChannelResponse(BaseModel):
    id: uuid.UUID
    name: str
    cdn_channel_key: str
    tstv_enabled: bool
    startover_enabled: bool
    catchup_enabled: bool
    cutv_window_hours: int

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Start Over
# ---------------------------------------------------------------------------

class ScheduleEntrySummary(BaseModel):
    id: uuid.UUID
    channel_id: uuid.UUID
    title: str
    synopsis: str | None = None
    genre: str | None = None
    start_time: datetime
    end_time: datetime
    catchup_eligible: bool
    startover_eligible: bool

    model_config = {"from_attributes": True}


class StartOverAvailability(BaseModel):
    channel_id: uuid.UUID
    schedule_entry: ScheduleEntrySummary
    startover_available: bool
    elapsed_seconds: int


# ---------------------------------------------------------------------------
# Catch-Up
# ---------------------------------------------------------------------------

class CatchUpProgram(BaseModel):
    schedule_entry: ScheduleEntrySummary
    expires_at: datetime
    bookmark_position_seconds: int | None = None


class CatchUpListResponse(BaseModel):
    programs: list[CatchUpProgram]
    total: int


class CatchUpByDateResponse(BaseModel):
    programs: list[CatchUpProgram]
    total: int
    date: str


# ---------------------------------------------------------------------------
# TSTV Sessions
# ---------------------------------------------------------------------------

class TSTVSessionCreate(BaseModel):
    channel_id: str
    schedule_entry_id: uuid.UUID
    session_type: str = Field(pattern=r"^(startover|catchup)$")
    profile_id: uuid.UUID | None = None


class TSTVSessionUpdate(BaseModel):
    last_position_s: float | None = Field(default=None, ge=0)
    completed: bool | None = None


class TSTVSessionResponse(BaseModel):
    id: int
    channel_id: str
    schedule_entry_id: uuid.UUID
    session_type: str
    started_at: datetime
    last_position_s: float
    completed: bool

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Admin — TSTV Rules
# ---------------------------------------------------------------------------

class TSTVRulesResponse(BaseModel):
    channel_id: uuid.UUID
    channel_name: str
    tstv_enabled: bool
    startover_enabled: bool
    catchup_enabled: bool
    cutv_window_hours: int
    catchup_window_hours: int


class TSTVRulesUpdate(BaseModel):
    tstv_enabled: bool | None = None
    startover_enabled: bool | None = None
    catchup_enabled: bool | None = None
    cutv_window_hours: int | None = Field(default=None)


# ---------------------------------------------------------------------------
# Admin — SimLive
# ---------------------------------------------------------------------------

class SimLiveChannelStatus(BaseModel):
    channel_key: str
    running: bool
    pid: int | None = None
    segment_count: int = 0
    disk_bytes: int = 0
    error: str | None = None


class CleanupResult(BaseModel):
    channels_processed: int
    total_segments_deleted: int
    total_bytes_freed: int
