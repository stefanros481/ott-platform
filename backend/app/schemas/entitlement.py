"""Pydantic schemas for entitlement, TVOD, and stream session endpoints."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ── Content Package schemas ───────────────────────────────────────────────────


class PackageCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    tier: str | None = None
    max_streams: int = Field(1, ge=1)
    price_cents: int = Field(0, ge=0)
    currency: str = Field("USD", min_length=3, max_length=3)


class PackageUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    tier: str | None = None
    max_streams: int | None = Field(None, ge=1)
    price_cents: int | None = Field(None, ge=0)
    currency: str | None = Field(None, min_length=3, max_length=3)


class PackageResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    tier: str | None = None
    max_streams: int = 0
    price_cents: int = 0
    currency: str = "USD"
    title_count: int = 0

    model_config = {"from_attributes": True}


# ── Title Offer schemas ───────────────────────────────────────────────────────


class OfferCreate(BaseModel):
    offer_type: Literal["rent", "buy", "free"]
    price_cents: int = Field(0, ge=0)
    currency: str = Field("USD", min_length=3, max_length=3)
    rental_window_hours: int | None = Field(None, gt=0)


class OfferUpdate(BaseModel):
    price_cents: int | None = Field(None, ge=0)
    currency: str | None = Field(None, min_length=3, max_length=3)
    rental_window_hours: int | None = None
    is_active: bool | None = None


class OfferResponse(BaseModel):
    id: uuid.UUID
    offer_type: str
    price_cents: int
    currency: str
    rental_window_hours: int | None = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── TVOD purchase schemas ─────────────────────────────────────────────────────


class TVODPurchaseRequest(BaseModel):
    offer_type: Literal["rent", "buy"]


class TVODPurchaseResponse(BaseModel):
    entitlement_id: uuid.UUID
    title_id: uuid.UUID
    offer_type: str
    expires_at: datetime | None
    price_cents: int
    currency: str


# ── Viewing / Stream Session schemas ─────────────────────────────────────────


class SessionStartRequest(BaseModel):
    title_id: uuid.UUID
    content_type: str = "vod_title"


class SessionResponse(BaseModel):
    session_id: uuid.UUID
    started_at: datetime


class SessionListResponse(BaseModel):
    session_id: uuid.UUID
    title_id: uuid.UUID | None
    title_name: str | None
    started_at: datetime
    last_heartbeat_at: datetime


# ── Admin subscription update ─────────────────────────────────────────────────


class UserSubscriptionUpdate(BaseModel):
    package_id: uuid.UUID | None = None
    expires_at: datetime | None = None


# ── Admin entitlement query ────────────────────────────────────────────────────


class UserEntitlementResponse(BaseModel):
    """A single entitlement record for a user, as returned by the admin API."""

    id: uuid.UUID
    source_type: str                    # "subscription" | "tvod_rent" | "tvod_buy"
    package_id: uuid.UUID | None        # set for SVOD subscriptions
    package_name: str | None            # denormalised for convenience
    package_tier: str | None
    title_id: uuid.UUID | None          # set for TVOD purchases
    title_name: str | None              # denormalised for convenience
    granted_at: datetime
    expires_at: datetime | None
    is_active: bool                     # True if not yet expired
