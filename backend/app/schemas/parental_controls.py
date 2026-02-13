"""Pydantic schemas for parental controls endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# -- PIN schemas --

class PinCreate(BaseModel):
    new_pin: str = Field(min_length=4, max_length=4, pattern=r"^\d{4}$")
    current_pin: str | None = Field(None, min_length=4, max_length=4, pattern=r"^\d{4}$")


class PinVerify(BaseModel):
    pin: str = Field(min_length=4, max_length=4, pattern=r"^\d{4}$")


class PinReset(BaseModel):
    password: str = Field(min_length=1)
    new_pin: str = Field(min_length=4, max_length=4, pattern=r"^\d{4}$")


class PinResponse(BaseModel):
    detail: str


class PinError(BaseModel):
    detail: str
    remaining_attempts: int | None = None
    locked_until: datetime | None = None


class PinVerifyResponse(BaseModel):
    verified: bool
    pin_token: str | None = None


class PinStatusResponse(BaseModel):
    has_pin: bool
    locked_until: datetime | None = None


# -- Viewing Time Config schemas --

class ViewingTimeConfigResponse(BaseModel):
    profile_id: uuid.UUID
    weekday_limit_minutes: int | None
    weekend_limit_minutes: int | None
    reset_hour: int
    educational_exempt: bool
    timezone: str
    updated_at: datetime

    model_config = {"from_attributes": True}


class ViewingTimeConfigUpdate(BaseModel):
    weekday_limit_minutes: int | None = Field(None, ge=15, le=480)
    weekend_limit_minutes: int | None = Field(None, ge=15, le=480)
    reset_hour: int | None = Field(None, ge=0, le=23)
    educational_exempt: bool | None = None
    timezone: str | None = Field(None, max_length=50)


# -- Grant Extra Time schemas --

class GrantExtraTimeRequest(BaseModel):
    minutes: int | None = Field(None, ge=15, le=120,
                                description="15, 30, or 60 minutes. null = Unlimited for today.")
    pin: str | None = Field(None, min_length=4, max_length=4, pattern=r"^\d{4}$",
                            description="Inline PIN verification for on-device grant")
    pin_token: str | None = Field(None,
                                  description="Short-lived token from /pin/verify (alternative to pin)")


class GrantExtraTimeResponse(BaseModel):
    granted_minutes: int | None
    remaining_minutes: float | None
    is_unlimited_override: bool


# -- Viewing History schemas --

class ViewingHistorySession(BaseModel):
    session_id: uuid.UUID
    title_id: uuid.UUID
    title_name: str
    device_type: str | None
    is_educational: bool
    started_at: datetime
    ended_at: datetime | None
    duration_minutes: float


class ViewingHistoryDay(BaseModel):
    date: str
    total_minutes: float
    educational_minutes: float
    counted_minutes: float
    sessions: list[ViewingHistorySession]


class ViewingHistoryResponse(BaseModel):
    profile_id: uuid.UUID
    days: list[ViewingHistoryDay]


# -- Weekly Report schemas --

class TopTitle(BaseModel):
    title_id: uuid.UUID
    title_name: str
    total_minutes: float


class ProfileWeeklyStats(BaseModel):
    profile_id: uuid.UUID
    profile_name: str
    daily_totals: list[dict]
    average_daily_minutes: float
    total_minutes: float
    educational_minutes: float
    limit_usage_percent: float | None
    top_titles: list[TopTitle]


class WeeklyReportResponse(BaseModel):
    week_start: str
    week_end: str
    profiles: list[ProfileWeeklyStats]
