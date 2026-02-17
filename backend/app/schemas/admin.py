"""Pydantic schemas for admin endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class PlatformStatsResponse(BaseModel):
    """High-level platform statistics."""

    title_count: int
    channel_count: int
    user_count: int
    embedding_count: int


class TitleCreateRequest(BaseModel):
    """Create a new VOD title."""

    title: str = Field(min_length=1, max_length=500)
    title_type: str = Field(pattern=r"^(movie|series)$")
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
    genre_ids: list[uuid.UUID] | None = None


class TitleUpdateRequest(BaseModel):
    """Update an existing VOD title (all fields optional)."""

    title: str | None = None
    title_type: str | None = None
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
    is_featured: bool | None = None
    mood_tags: list[str] | None = None
    theme_tags: list[str] | None = None
    ai_description: str | None = None
    genre_ids: list[uuid.UUID] | None = None


class TitleAdminResponse(BaseModel):
    """Title information for admin table views."""

    id: uuid.UUID
    title: str
    title_type: str
    release_year: int | None = None
    age_rating: str | None = None
    poster_url: str | None = None
    is_featured: bool
    has_embedding: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class TitlePaginatedResponse(BaseModel):
    """Paginated list of titles for admin table."""

    items: list[TitleAdminResponse]
    total: int
    page: int
    page_size: int


class EmbeddingGenerationResponse(BaseModel):
    """Result of a bulk embedding generation run."""

    new_embeddings_created: int


# ---------------------------------------------------------------------------
# Performance Metrics (009-backend-performance)
# ---------------------------------------------------------------------------


class HeartbeatMetrics(BaseModel):
    total_processed: int
    avg_db_ops_per_heartbeat: float
    avg_duration_ms: float
    max_duration_ms: float
    p95_duration_ms: float = 0.0


class CacheMetrics(BaseModel):
    hit_rate: float = Field(ge=0, le=1)
    total_hits: int
    total_misses: int
    total_invalidations: int
    current_size: int
    max_size: int


class PerformanceMetricsResponse(BaseModel):
    """Response for GET /api/v1/admin/metrics."""

    uptime_seconds: float
    heartbeat: HeartbeatMetrics
    config_cache: CacheMetrics
