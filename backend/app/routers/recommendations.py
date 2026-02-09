"""Recommendations router -- home rails, similar titles, post-play."""

import uuid

from fastapi import APIRouter, Query

from app.dependencies import DB
from app.schemas.recommendation import ContentRail, ContentRailItem, HomeResponse
from app.services import recommendation_service

router = APIRouter()


@router.get("/home", response_model=HomeResponse)
async def home_rails(
    db: DB,
    profile_id: uuid.UUID = Query(..., description="Active profile"),
):
    """Return assembled home-screen rails for a profile.

    Rails include: Continue Watching, For You, New Releases, Trending,
    and a top-genre rail (when viewing history exists).
    """
    raw_rails = await recommendation_service.get_home_rails(db, profile_id)
    rails = [
        ContentRail(
            name=r["name"],
            rail_type=r["rail_type"],
            items=[ContentRailItem(**item) for item in r["items"]],
        )
        for r in raw_rails
    ]
    return HomeResponse(rails=rails)


@router.get("/similar/{title_id}", response_model=list[ContentRailItem])
async def similar_titles(
    title_id: uuid.UUID,
    db: DB,
    limit: int = Query(12, ge=1, le=50),
):
    """Return titles similar to the given title using embedding similarity."""
    items = await recommendation_service.get_similar_titles(db, title_id, limit=limit)
    return [ContentRailItem(**item) for item in items]


@router.get("/post-play/{title_id}", response_model=list[ContentRailItem])
async def post_play(
    title_id: uuid.UUID,
    db: DB,
    profile_id: uuid.UUID | None = Query(None, description="Active profile (reserved for future personalisation)"),
    limit: int = Query(8, ge=1, le=20),
):
    """Post-play suggestions after finishing a title."""
    items = await recommendation_service.get_post_play(db, title_id, limit=limit)
    return [ContentRailItem(**item) for item in items]
