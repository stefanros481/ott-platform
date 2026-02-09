"""Viewing router -- bookmarks (continue-watching), ratings, watchlist."""

import uuid

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import and_, delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import DB, CurrentUser
from app.models.viewing import Bookmark, Rating, WatchlistItem
from app.schemas.viewing import (
    BookmarkResponse,
    BookmarkUpdate,
    RatingRequest,
    RatingResponse,
    WatchlistItemResponse,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Continue Watching / Bookmarks
# ---------------------------------------------------------------------------


@router.get("/continue-watching", response_model=list[BookmarkResponse])
async def continue_watching(
    db: DB,
    user: CurrentUser,
    profile_id: uuid.UUID = Query(..., description="Active profile"),
):
    """Return the continue-watching list for a profile (incomplete bookmarks, most recent first)."""
    result = await db.execute(
        text(
            """
            SELECT b.id, b.content_type, b.content_id, b.position_seconds,
                   b.duration_seconds, b.completed, b.updated_at,
                   t.title AS title_name, t.poster_url
            FROM bookmarks b
            LEFT JOIN titles t ON t.id = b.content_id
            WHERE b.profile_id = :pid AND b.completed = false
            ORDER BY b.updated_at DESC
            """
        ).bindparams(pid=profile_id)
    )
    rows = result.fetchall()
    return [
        BookmarkResponse(
            id=r.id,
            content_type=r.content_type,
            content_id=r.content_id,
            position_seconds=r.position_seconds,
            duration_seconds=r.duration_seconds,
            completed=r.completed,
            updated_at=r.updated_at,
            title_info={"title": r.title_name, "poster_url": r.poster_url},
        )
        for r in rows
    ]


@router.put("/bookmarks", response_model=BookmarkResponse)
async def update_bookmark(
    body: BookmarkUpdate,
    db: DB,
    user: CurrentUser,
    profile_id: uuid.UUID = Query(..., description="Active profile"),
):
    """Create or update a playback bookmark (upsert by profile + content_id)."""
    result = await db.execute(
        select(Bookmark).where(
            and_(
                Bookmark.profile_id == profile_id,
                Bookmark.content_id == body.content_id,
            )
        )
    )
    bookmark = result.scalar_one_or_none()

    # Mark completed when position reaches 95 % of duration.
    completed = body.position_seconds >= (body.duration_seconds * 0.95)

    if bookmark is None:
        bookmark = Bookmark(
            profile_id=profile_id,
            content_type=body.content_type,
            content_id=body.content_id,
            position_seconds=body.position_seconds,
            duration_seconds=body.duration_seconds,
            completed=completed,
        )
        db.add(bookmark)
    else:
        bookmark.position_seconds = body.position_seconds
        bookmark.duration_seconds = body.duration_seconds
        bookmark.completed = completed

    await db.commit()
    await db.refresh(bookmark)

    return BookmarkResponse(
        id=bookmark.id,
        content_type=bookmark.content_type,
        content_id=bookmark.content_id,
        position_seconds=bookmark.position_seconds,
        duration_seconds=bookmark.duration_seconds,
        completed=bookmark.completed,
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
