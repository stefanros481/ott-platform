"""Pydantic schemas for recommendation and home-screen endpoints."""

import uuid

from pydantic import BaseModel


class ContentRailItem(BaseModel):
    """A single content item inside a rail."""

    id: uuid.UUID
    title: str
    title_type: str
    poster_url: str | None = None
    landscape_url: str | None = None
    synopsis_short: str | None = None
    release_year: int | None = None
    age_rating: str | None = None
    similarity_score: float | None = None

    model_config = {"from_attributes": True}


class ContentRail(BaseModel):
    """A named horizontal rail of content items (e.g. 'Continue Watching')."""

    name: str
    rail_type: str  # e.g. "continue_watching", "for_you", "new_releases", "trending", "genre"
    items: list[ContentRailItem]


class HomeResponse(BaseModel):
    """Full home-screen payload, composed of multiple rails."""

    rails: list[ContentRail]
