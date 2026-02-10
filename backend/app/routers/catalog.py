"""Catalog router — title browsing, search, detail, genres, featured."""

import uuid

from fastapi import APIRouter, HTTPException, Query, status

from app.dependencies import DB, CurrentUser
from app.schemas.catalog import (
    CastMember,
    GenreResponse,
    PaginatedResponse,
    SeasonResponse,
    SemanticSearchResponse,
    TitleDetail,
    TitleListItem,
)
from app.services import catalog_service, search_service
from app.services.rating_utils import resolve_profile_rating

router = APIRouter()


# ── Helpers ──────────────────────────────────────────────────────────────────


def _title_to_list_item(title) -> TitleListItem:
    """Convert an ORM Title (with genres loaded) to a TitleListItem schema."""
    return TitleListItem(
        id=title.id,
        title=title.title,
        title_type=title.title_type,
        synopsis_short=title.synopsis_short,
        release_year=title.release_year,
        duration_minutes=title.duration_minutes,
        age_rating=title.age_rating,
        poster_url=title.poster_url,
        landscape_url=title.landscape_url,
        is_featured=title.is_featured,
        mood_tags=title.mood_tags,
        genres=[tg.genre.name for tg in title.genres],
    )


def _title_to_detail(title) -> TitleDetail:
    """Convert an ORM Title (fully loaded) to a TitleDetail schema."""
    return TitleDetail(
        id=title.id,
        title=title.title,
        title_type=title.title_type,
        synopsis_short=title.synopsis_short,
        synopsis_long=title.synopsis_long,
        release_year=title.release_year,
        duration_minutes=title.duration_minutes,
        age_rating=title.age_rating,
        country_of_origin=title.country_of_origin,
        language=title.language,
        poster_url=title.poster_url,
        landscape_url=title.landscape_url,
        logo_url=title.logo_url,
        hls_manifest_url=title.hls_manifest_url,
        is_featured=title.is_featured,
        mood_tags=title.mood_tags,
        theme_tags=title.theme_tags,
        ai_description=title.ai_description,
        genres=[tg.genre.name for tg in title.genres],
        cast=[
            CastMember(
                person_name=cm.person_name,
                role=cm.role,
                character_name=cm.character_name,
            )
            for cm in sorted(title.cast_members, key=lambda c: c.sort_order)
        ],
        seasons=[
            SeasonResponse.model_validate(s)
            for s in sorted(title.seasons, key=lambda s: s.season_number)
        ],
    )


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/titles", response_model=PaginatedResponse[TitleListItem])
async def list_titles(
    user: CurrentUser,
    db: DB,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    genre: str | None = Query(None, description="Filter by genre slug"),
    type: str | None = Query(None, description="Filter by title type (movie/series)"),
    q: str | None = Query(None, description="Free-text search"),
    profile_id: uuid.UUID | None = Query(None, description="Active profile for parental filtering"),
) -> PaginatedResponse[TitleListItem]:
    """Browse the content catalog with optional filtering and search."""
    allowed_ratings = None
    if profile_id is not None:
        allowed_ratings = await resolve_profile_rating(db, profile_id)
    titles, total = await catalog_service.get_titles(
        db,
        page=page,
        page_size=page_size,
        genre_slug=genre,
        title_type=type,
        search_query=q,
        allowed_ratings=allowed_ratings,
    )
    return PaginatedResponse(
        items=[_title_to_list_item(t) for t in titles],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/titles/{title_id}", response_model=TitleDetail)
async def get_title(
    title_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    profile_id: uuid.UUID | None = Query(None, description="Active profile for parental filtering"),
) -> TitleDetail:
    """Retrieve full detail for a single title."""
    title = await catalog_service.get_title_detail(db, title_id)
    if not title:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Title not found",
        )
    if profile_id is not None:
        allowed_ratings = await resolve_profile_rating(db, profile_id)
        if allowed_ratings is not None and title.age_rating not in allowed_ratings:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Content not available for this profile",
            )
    return _title_to_detail(title)


@router.get("/genres", response_model=list[GenreResponse])
async def list_genres(user: CurrentUser, db: DB) -> list[GenreResponse]:
    """List all available genres."""
    genres = await catalog_service.get_genres(db)
    return [GenreResponse.model_validate(g) for g in genres]


@router.get("/featured", response_model=list[TitleListItem])
async def featured_titles(
    user: CurrentUser,
    db: DB,
    profile_id: uuid.UUID | None = Query(None, description="Active profile for parental filtering"),
) -> list[TitleListItem]:
    """Return featured titles for the hero banner carousel."""
    allowed_ratings = None
    if profile_id is not None:
        allowed_ratings = await resolve_profile_rating(db, profile_id)
    titles = await catalog_service.get_featured_titles(db, allowed_ratings=allowed_ratings)
    return [_title_to_list_item(t) for t in titles]


@router.get("/search", response_model=PaginatedResponse[TitleListItem])
async def search_titles(
    user: CurrentUser,
    db: DB,
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    profile_id: uuid.UUID | None = Query(None, description="Active profile for parental filtering"),
) -> PaginatedResponse[TitleListItem]:
    """Search titles by keyword (alias for /titles?q=)."""
    allowed_ratings = None
    if profile_id is not None:
        allowed_ratings = await resolve_profile_rating(db, profile_id)
    titles, total = await catalog_service.get_titles(
        db,
        page=page,
        page_size=page_size,
        search_query=q,
        allowed_ratings=allowed_ratings,
    )
    return PaginatedResponse(
        items=[_title_to_list_item(t) for t in titles],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/search/semantic", response_model=SemanticSearchResponse)
async def semantic_search(
    user: CurrentUser,
    db: DB,
    q: str = Query(..., min_length=1, description="Search query (natural language supported)"),
    mode: str = Query("hybrid", pattern="^(keyword|semantic|hybrid)$", description="Search mode"),
    page_size: int = Query(20, ge=1, le=100, description="Max results"),
    profile_id: uuid.UUID | None = Query(None, description="Active profile for parental filtering"),
) -> SemanticSearchResponse:
    """Hybrid semantic + keyword search with match explanations."""
    allowed_ratings = None
    if profile_id is not None:
        allowed_ratings = await resolve_profile_rating(db, profile_id)
    results = await search_service.hybrid_search(
        db,
        query_text=q,
        mode=mode,
        allowed_ratings=allowed_ratings,
        limit=page_size,
    )
    return SemanticSearchResponse(
        items=results,
        total=len(results),
        query=q,
        mode=mode,
    )
