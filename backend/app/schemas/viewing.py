"""Pydantic schemas for viewing-related endpoints (bookmarks, ratings, watchlist)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# -- Request schemas ----------------------------------------------------------


class BookmarkUpdate(BaseModel):
    """Create or update a playback bookmark."""

    content_type: str = Field(pattern=r"^(movie|episode)$", description="'movie' or 'episode'")
    content_id: uuid.UUID
    position_seconds: int = Field(ge=0)
    duration_seconds: int = Field(ge=1)


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
    updated_at: datetime
    title_info: dict | None = None  # {"title": ..., "poster_url": ...}

    model_config = {"from_attributes": True}


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
