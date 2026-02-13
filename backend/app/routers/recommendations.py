"""Recommendations router -- home rails, similar titles, post-play."""

import uuid

from fastapi import APIRouter, Query

from app.dependencies import DB, OptionalVerifiedProfileId, VerifiedProfileId
from app.schemas.recommendation import ContentRail, ContentRailItem, HomeResponse
from app.services import recommendation_service
from app.services.rating_utils import resolve_profile_rating

router = APIRouter()


@router.get("/home", response_model=HomeResponse)
async def home_rails(
    db: DB,
    profile_id: VerifiedProfileId,
):
    """Return assembled home-screen rails for a profile.

    Rails include: Continue Watching, For You, New Releases, Trending,
    and a top-genre rail (when viewing history exists).
    """
    allowed_ratings = await resolve_profile_rating(db, profile_id)
    raw_rails = await recommendation_service.get_home_rails(db, profile_id, allowed_ratings=allowed_ratings)
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
    profile_id: OptionalVerifiedProfileId = None,
):
    """Return titles similar to the given title using embedding similarity."""
    allowed_ratings = None
    if profile_id is not None:
        allowed_ratings = await resolve_profile_rating(db, profile_id)
    items = await recommendation_service.get_similar_titles(db, title_id, limit=limit, allowed_ratings=allowed_ratings)
    return [ContentRailItem(**item) for item in items]


@router.get("/post-play/{title_id}", response_model=list[ContentRailItem])
async def post_play(
    title_id: uuid.UUID,
    db: DB,
    profile_id: VerifiedProfileId,
    limit: int = Query(8, ge=1, le=20),
):
    """Post-play suggestions after finishing a title."""
    allowed_ratings = await resolve_profile_rating(db, profile_id)
    items = await recommendation_service.get_post_play(db, title_id, limit=limit, allowed_ratings=allowed_ratings)
    return [ContentRailItem(**item) for item in items]
