"""Pydantic schemas for viewing time tracking endpoints."""

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class EnforcementStatus(str, Enum):
    allowed = "allowed"
    warning_15 = "warning_15"
    warning_5 = "warning_5"
    blocked = "blocked"


class DeviceType(str, Enum):
    tv = "tv"
    mobile = "mobile"
    tablet = "tablet"
    web = "web"


# -- Balance --

class ViewingTimeBalanceResponse(BaseModel):
    profile_id: uuid.UUID
    is_child_profile: bool
    has_limits: bool
    used_minutes: float
    educational_minutes: float
    limit_minutes: int | None
    remaining_minutes: float | None
    is_unlimited_override: bool
    next_reset_at: datetime | None
    warning_threshold_minutes: list[int] = Field(default_factory=lambda: [15, 5])


# -- Heartbeat --

class HeartbeatRequest(BaseModel):
    profile_id: uuid.UUID
    session_id: uuid.UUID | None = None
    title_id: uuid.UUID
    device_id: str = Field(max_length=100)
    device_type: DeviceType = DeviceType.web
    is_paused: bool = False


class HeartbeatResponse(BaseModel):
    session_id: uuid.UUID
    enforcement: EnforcementStatus
    remaining_minutes: float | None
    used_minutes: float
    is_educational: bool


# -- Session End --

class SessionEndResponse(BaseModel):
    session_id: uuid.UUID
    total_seconds: int
    ended_at: datetime


# -- Playback Eligibility --

class PlaybackEligibilityResponse(BaseModel):
    eligible: bool
    remaining_minutes: float | None = None
    reason: str | None = None
    next_reset_at: datetime | None = None
