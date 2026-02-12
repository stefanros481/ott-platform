"""Viewing router -- bookmarks (continue-watching), ratings, watchlist."""

import uuid
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import and_, delete, select, text

from app.dependencies import DB, CurrentUser
from app.models.viewing import Bookmark, Rating, WatchlistItem
from app.schemas.viewing import (
    BookmarkResponse,
    BookmarkUpdate,
    ContinueWatchingItem,
    RatingRequest,
    RatingResponse,
    WatchlistItemResponse,
)
from app.services import bookmark_service
from app.services.recommendation_service import compute_resumption_scores

router = APIRouter()


# ---------------------------------------------------------------------------
# Continue Watching / Bookmarks
# ---------------------------------------------------------------------------


@router.get("/continue-watching", response_model=list[ContinueWatchingItem])
async def continue_watching(
    db: DB,
    user: CurrentUser,
    profile_id: uuid.UUID = Query(..., description="Active profile"),
    device_type: Literal["tv", "mobile", "tablet", "web"] = Query("web", description="Client device type"),
    hour_of_day: int | None = Query(None, ge=0, le=23, description="Client local hour (0-23)"),
    limit: int = Query(20, ge=1, le=20, description="Max items to return"),
):
    """Return the Continue Watching rail: active bookmarks with progress, title info, and next episode."""
    items = await bookmark_service.get_active_bookmarks(db, profile_id, limit=limit)

    # AI scoring (US3) — sort by resumption likelihood, fall back to recency
    scores = await compute_resumption_scores(
        db, items, device_type=device_type, hour_of_day=hour_of_day,
    )
    if scores:
        for item in items:
            item.resumption_score = scores.get(str(item.id))
        items.sort(key=lambda x: x.resumption_score or 0.0, reverse=True)

    return items


@router.get("/continue-watching/paused", response_model=list[ContinueWatchingItem])
async def paused_bookmarks(
    db: DB,
    user: CurrentUser,
    profile_id: uuid.UUID = Query(..., description="Active profile"),
):
    """Return dismissed + stale bookmarks for the Paused section."""
    return await bookmark_service.get_paused_bookmarks(db, profile_id)


@router.post("/bookmarks/{bookmark_id}/dismiss", response_model=BookmarkResponse)
async def dismiss_bookmark(
    bookmark_id: uuid.UUID,
    db: DB,
    user: CurrentUser,
    profile_id: uuid.UUID = Query(..., description="Active profile"),
):
    """Dismiss a bookmark from Continue Watching (moves to Paused)."""
    bookmark = await bookmark_service.dismiss_bookmark(db, bookmark_id, profile_id)
    if bookmark is None:
        raise HTTPException(status_code=404, detail="Bookmark not found or doesn't belong to profile")
    return BookmarkResponse(
        id=bookmark.id,
        content_type=bookmark.content_type,
        content_id=bookmark.content_id,
        position_seconds=bookmark.position_seconds,
        duration_seconds=bookmark.duration_seconds,
        completed=bookmark.completed,
        dismissed_at=bookmark.dismissed_at,
        updated_at=bookmark.updated_at,
        title_info=None,
    )


@router.post("/bookmarks/{bookmark_id}/restore", response_model=BookmarkResponse)
async def restore_bookmark(
    bookmark_id: uuid.UUID,
    db: DB,
    user: CurrentUser,
    profile_id: uuid.UUID = Query(..., description="Active profile"),
):
    """Restore a dismissed/paused bookmark back to Continue Watching."""
    bookmark = await bookmark_service.restore_bookmark(db, bookmark_id, profile_id)
    if bookmark is None:
        raise HTTPException(status_code=404, detail="Bookmark not found or doesn't belong to profile")
    return BookmarkResponse(
        id=bookmark.id,
        content_type=bookmark.content_type,
        content_id=bookmark.content_id,
        position_seconds=bookmark.position_seconds,
        duration_seconds=bookmark.duration_seconds,
        completed=bookmark.completed,
        dismissed_at=bookmark.dismissed_at,
        updated_at=bookmark.updated_at,
        title_info=None,
    )


@router.put("/bookmarks", response_model=BookmarkResponse)
async def update_bookmark(
    body: BookmarkUpdate,
    db: DB,
    user: CurrentUser,
    profile_id: uuid.UUID = Query(..., description="Active profile"),
):
    """Create or update a playback bookmark (heartbeat). Auto-completes at 95% or final 2 min."""
    bookmark = await bookmark_service.upsert_bookmark(
        db,
        profile_id=profile_id,
        content_type=body.content_type,
        content_id=body.content_id,
        position_seconds=body.position_seconds,
        duration_seconds=body.duration_seconds,
    )
    return BookmarkResponse(
        id=bookmark.id,
        content_type=bookmark.content_type,
        content_id=bookmark.content_id,
        position_seconds=bookmark.position_seconds,
        duration_seconds=bookmark.duration_seconds,
        completed=bookmark.completed,
        dismissed_at=bookmark.dismissed_at,
        updated_at=bookmark.updated_at,
        title_info=None,
    )


# ---------------------------------------------------------------------------
# Ratings
# ---------------------------------------------------------------------------


@router.get("/ratings/{title_id}", response_model=RatingResponse | None)
async def get_rating(
    title_id: uuid.UUID,
    db: DB,
    user: CurrentUser,
    profile_id: uuid.UUID = Query(..., description="Active profile"),
):
    """Get the user's rating for a specific title (or null if not rated)."""
    result = await db.execute(
        select(Rating).where(
            and_(
                Rating.profile_id == profile_id,
                Rating.title_id == title_id,
            )
        )
    )
    return result.scalar_one_or_none()


@router.post("/ratings", response_model=RatingResponse)
async def rate_title(
    body: RatingRequest,
    db: DB,
    user: CurrentUser,
    profile_id: uuid.UUID = Query(..., description="Active profile"),
):
    """Rate a title (thumbs up / thumbs down). Upserts if rating already exists."""
    result = await db.execute(
        select(Rating).where(
            and_(
                Rating.profile_id == profile_id,
                Rating.title_id == body.title_id,
            )
        )
    )
    rating = result.scalar_one_or_none()

    if rating is None:
        rating = Rating(
            profile_id=profile_id,
            title_id=body.title_id,
            rating=body.rating,
        )
        db.add(rating)
    else:
        rating.rating = body.rating

    await db.commit()
    await db.refresh(rating)
    return rating


# ---------------------------------------------------------------------------
# Watchlist
# ---------------------------------------------------------------------------


@router.get("/watchlist", response_model=list[WatchlistItemResponse])
async def get_watchlist(
    db: DB,
    user: CurrentUser,
    profile_id: uuid.UUID = Query(..., description="Active profile"),
):
    """Return the profile's watchlist with title metadata."""
    result = await db.execute(
        text(
            """
            SELECT w.title_id, w.added_at,
                   t.title AS title_name, t.poster_url, t.landscape_url,
                   t.title_type, t.release_year, t.age_rating
            FROM watchlist w
            LEFT JOIN titles t ON t.id = w.title_id
            WHERE w.profile_id = :pid
            ORDER BY w.added_at DESC
            """
        ).bindparams(pid=profile_id)
    )
    rows = result.fetchall()
    return [
        WatchlistItemResponse(
            title_id=r.title_id,
            added_at=r.added_at,
            title_info={
                "id": str(r.title_id),
                "title": r.title_name,
                "poster_url": r.poster_url,
                "landscape_url": r.landscape_url,
                "title_type": r.title_type,
                "release_year": r.release_year,
                "age_rating": r.age_rating,
            },
        )
        for r in rows
    ]


@router.post("/watchlist/{title_id}", status_code=201)
async def add_to_watchlist(
    title_id: uuid.UUID,
    db: DB,
    user: CurrentUser,
    profile_id: uuid.UUID = Query(..., description="Active profile"),
):
    """Add a title to the profile's watchlist (idempotent)."""
    existing = await db.execute(
        select(WatchlistItem).where(
            and_(
                WatchlistItem.profile_id == profile_id,
                WatchlistItem.title_id == title_id,
            )
        )
    )
    if existing.scalar_one_or_none() is not None:
        return {"detail": "Already in watchlist"}

    db.add(WatchlistItem(profile_id=profile_id, title_id=title_id))
    await db.commit()
    return {"detail": "Added to watchlist"}


@router.delete("/watchlist/{title_id}", status_code=204)
async def remove_from_watchlist(
    title_id: uuid.UUID,
    db: DB,
    user: CurrentUser,
    profile_id: uuid.UUID = Query(..., description="Active profile"),
):
    """Remove a title from the profile's watchlist."""
    await db.execute(
        delete(WatchlistItem).where(
            and_(
                WatchlistItem.profile_id == profile_id,
                WatchlistItem.title_id == title_id,
            )
        )
    )
    await db.commit()
