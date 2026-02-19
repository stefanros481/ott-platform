"""Pydantic schemas for the content catalog endpoints."""

import uuid
from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# ── Nested / shared schemas ─────────────────────────────────────────────────


class GenreResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str

    model_config = {"from_attributes": True}


class CastMember(BaseModel):
    person_name: str
    role: str
    character_name: str | None = None

    model_config = {"from_attributes": True}


class EpisodeResponse(BaseModel):
    id: uuid.UUID
    episode_number: int
    title: str
    synopsis: str | None = None
    duration_minutes: int | None = None
    hls_manifest_url: str | None = None

    model_config = {"from_attributes": True}


class SeasonResponse(BaseModel):
    id: uuid.UUID
    season_number: int
    name: str | None = None
    synopsis: str | None = None
    episodes: list[EpisodeResponse] = []

    model_config = {"from_attributes": True}


# ── Title schemas ────────────────────────────────────────────────────────────


class TitleListItem(BaseModel):
    """Compact title representation for list / browse views."""

    id: uuid.UUID
    title: str
    title_type: str
    synopsis_short: str | None = None
    release_year: int | None = None
    duration_minutes: int | None = None
    age_rating: str | None = None
    poster_url: str | None = None
    landscape_url: str | None = None
    is_featured: bool = False
    mood_tags: list[str] | None = None
    genres: list[str] = []
    access_options: list["AccessOption"] = []
    user_access: "UserAccess | None" = None

    model_config = {"from_attributes": True}


class TitleDetail(BaseModel):
    """Full title detail including cast, seasons, and AI metadata."""

    id: uuid.UUID
    title: str
    title_type: str
    synopsis_short: str | None = None
    synopsis_long: str | None = None
    release_year: int | None = None
    duration_minutes: int | None = None
    age_rating: str | None = None
    country_of_origin: str | None = None
    language: str | None = None
    poster_url: str | None = None
    landscape_url: str | None = None
    logo_url: str | None = None
    hls_manifest_url: str | None = None
    is_featured: bool = False
    mood_tags: list[str] | None = None
    theme_tags: list[str] | None = None
    ai_description: str | None = None
    genres: list[str] = []
    cast: list[CastMember] = []
    seasons: list[SeasonResponse] = []
    access_options: list["AccessOption"] = []
    user_access: "UserAccess | None" = None

    model_config = {"from_attributes": True}


# ── Pagination wrapper ───────────────────────────────────────────────────────


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)


# ── Semantic search schemas ──────────────────────────────────────────────────


class SearchResultItem(BaseModel):
    """A content title enriched with search match metadata."""

    id: uuid.UUID
    title: str
    title_type: str
    synopsis_short: str | None = None
    release_year: int | None = None
    duration_minutes: int | None = None
    age_rating: str | None = None
    poster_url: str | None = None
    landscape_url: str | None = None
    is_featured: bool = False
    mood_tags: list[str] | None = None
    genres: list[str] = []
    match_reason: str
    match_type: str
    similarity_score: float | None = None


class SemanticSearchResponse(BaseModel):
    """Response wrapper for the semantic search endpoint."""

    items: list[SearchResultItem]
    total: int
    query: str
    mode: str


# ── Entitlement / access schemas (Feature 012) ───────────────────────────────


class AccessOption(BaseModel):
    type: str
    label: str
    price_cents: int | None = None
    currency: str | None = None
    rental_window_hours: int | None = None


class UserAccess(BaseModel):
    has_access: bool
    access_type: str | None = None
    expires_at: datetime | None = None
    required_tier: str | None = None  # lowest SVOD tier that grants access


# Rebuild models that reference AccessOption/UserAccess as forward refs
TitleListItem.model_rebuild()
TitleDetail.model_rebuild()
