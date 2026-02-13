"""Pydantic schemas for viewing-related endpoints (bookmarks, ratings, watchlist)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


# -- Request schemas ----------------------------------------------------------


class BookmarkUpdate(BaseModel):
    """Create or update a playback bookmark."""

    content_type: str = Field(pattern=r"^(movie|episode)$", description="'movie' or 'episode'")
    content_id: uuid.UUID
    position_seconds: int = Field(ge=0)
    duration_seconds: int = Field(ge=1)

    @field_validator("position_seconds", "duration_seconds", mode="before")
    @classmethod
    def truncate_floats(cls, v: object) -> object:
        """Accept float values from clients and truncate to int."""
        if isinstance(v, float):
            return int(v)
        return v


class RatingRequest(BaseModel):
    """Rate a title (thumbs up / thumbs down)."""

    title_id: uuid.UUID
    rating: int = Field(description="Must be -1 (thumbs down) or 1 (thumbs up)")

    def model_post_init(self, __context: object) -> None:
        if self.rating not in (-1, 1):
            raise ValueError("rating must be -1 or 1")


# -- Response schemas ---------------------------------------------------------


class BookmarkResponse(BaseModel):
    """A single bookmark (continue-watching entry)."""

    id: uuid.UUID
    content_type: str
    content_id: uuid.UUID
    position_seconds: int
    duration_seconds: int
    completed: bool
    dismissed_at: datetime | None = None
    updated_at: datetime
    title_info: dict | None = None

    model_config = {"from_attributes": True}


class TitleInfo(BaseModel):
    """Title metadata attached to a Continue Watching item."""

    title: str
    poster_url: str | None = None
    landscape_url: str | None = None
    title_type: str  # 'movie' or 'series'
    age_rating: str | None = None
    episode_title: str | None = None
    season_number: int | None = None
    episode_number: int | None = None


class NextEpisodeInfo(BaseModel):
    """Metadata about the next unwatched episode in a series."""

    episode_id: uuid.UUID
    season_number: int
    episode_number: int
    episode_title: str


class ContinueWatchingItem(BaseModel):
    """A single item in the Continue Watching rail."""

    id: uuid.UUID
    content_type: str
    content_id: uuid.UUID
    position_seconds: int
    duration_seconds: int
    progress_percent: float
    completed: bool = False
    dismissed_at: datetime | None = None
    updated_at: datetime
    resumption_score: float | None = None
    title_info: TitleInfo
    next_episode: NextEpisodeInfo | None = None


class RatingResponse(BaseModel):
    """A user's rating for a title."""

    title_id: uuid.UUID
    rating: int
    created_at: datetime

    model_config = {"from_attributes": True}


class WatchlistItemResponse(BaseModel):
    """A single watchlist entry."""

    title_id: uuid.UUID
    added_at: datetime
    title_info: dict | None = None  # {"title": ..., "poster_url": ...}

    model_config = {"from_attributes": True}
