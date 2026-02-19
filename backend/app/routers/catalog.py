"""Catalog router — title browsing, search, detail, genres, featured.

Auth is optional for catalog endpoints (US2: guests see prices, subscribers see entitlement status).
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.dependencies import DB, RedisClient
from app.models.user import User
from app.schemas.catalog import (
    AccessOption,
    CastMember,
    GenreResponse,
    PaginatedResponse,
    SeasonResponse,
    SemanticSearchResponse,
    TitleDetail,
    TitleListItem,
    UserAccess,
)
from app.services import catalog_service, recommendation_service, search_service
from app.services.rating_utils import resolve_profile_rating

router = APIRouter()

_optional_bearer = HTTPBearer(auto_error=False)


async def _get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_optional_bearer)],
    db: DB,
) -> User | None:
    """Resolve a user from Bearer token, or None for unauthenticated requests."""
    if credentials is None:
        return None
    try:
        from app.config import settings
        from app.dependencies import decode_token
        from sqlalchemy import select

        payload = decode_token(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            return None
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        return user if user and user.is_active else None
    except Exception:
        return None


OptionalCurrentUser = Annotated[User | None, Depends(_get_optional_user)]


# ── Helpers ──────────────────────────────────────────────────────────────────


def _title_to_list_item(
    title,
    access_options: list[AccessOption] | None = None,
    user_access: UserAccess | None = None,
) -> TitleListItem:
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
        access_options=access_options or [],
        user_access=user_access,
    )


def _title_to_detail(
    title,
    access_options: list[AccessOption] | None = None,
    user_access: UserAccess | None = None,
) -> TitleDetail:
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
        access_options=access_options or [],
        user_access=user_access,
    )


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/titles", response_model=PaginatedResponse[TitleListItem])
async def list_titles(
    user: OptionalCurrentUser,
    db: DB,
    redis: RedisClient,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    genre: str | None = Query(None, description="Filter by genre slug"),
    type: str | None = Query(None, description="Filter by title type (movie/series)"),
    q: str | None = Query(None, description="Free-text search"),
) -> PaginatedResponse[TitleListItem]:
    """Browse the content catalog. Auth optional — guests see pricing, subscribers see entitlement status."""
    from app.services import entitlement_service

    titles, total = await catalog_service.get_titles(
        db,
        page=page,
        page_size=page_size,
        genre_slug=genre,
        title_type=type,
        search_query=q,
    )

    items = []
    for t in titles:
        access_options, user_access = await entitlement_service.get_access_options(
            t.id, user.id if user else None, db, redis
        )
        items.append(_title_to_list_item(t, access_options, user_access))

    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/titles/{title_id}", response_model=TitleDetail)
async def get_title(
    title_id: uuid.UUID,
    user: OptionalCurrentUser,
    db: DB,
    redis: RedisClient,
) -> TitleDetail:
    """Retrieve full detail for a single title. Auth optional."""
    from app.services import entitlement_service

    title = await catalog_service.get_title_detail(db, title_id)
    if not title:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Title not found")

    access_options, user_access = await entitlement_service.get_access_options(
        title_id, user.id if user else None, db, redis
    )
    return _title_to_detail(title, access_options, user_access)


@router.get("/genres", response_model=list[GenreResponse])
async def list_genres(db: DB) -> list[GenreResponse]:
    """List all available genres."""
    genres = await catalog_service.get_genres(db)
    return [GenreResponse.model_validate(g) for g in genres]


@router.get("/featured", response_model=list[TitleListItem])
async def featured_titles(
    user: OptionalCurrentUser,
    db: DB,
    redis: RedisClient,
) -> list[TitleListItem]:
    """Return featured titles for the hero banner carousel."""
    from app.services import entitlement_service

    titles = await catalog_service.get_featured_titles(db)
    items = []
    for t in titles:
        access_options, user_access = await entitlement_service.get_access_options(
            t.id, user.id if user else None, db, redis
        )
        items.append(_title_to_list_item(t, access_options, user_access))
    return items


@router.get("/search", response_model=PaginatedResponse[TitleListItem])
async def search_titles(
    user: OptionalCurrentUser,
    db: DB,
    redis: RedisClient,
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[TitleListItem]:
    """Search titles by keyword."""
    from app.services import entitlement_service

    titles, total = await catalog_service.get_titles(
        db, page=page, page_size=page_size, search_query=q,
    )
    items = []
    for t in titles:
        access_options, user_access = await entitlement_service.get_access_options(
            t.id, user.id if user else None, db, redis
        )
        items.append(_title_to_list_item(t, access_options, user_access))
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/search/semantic", response_model=SemanticSearchResponse)
async def semantic_search(
    user: OptionalCurrentUser,
    db: DB,
    q: str = Query(..., min_length=1, description="Search query (natural language supported)"),
    mode: str = Query("hybrid", pattern="^(keyword|semantic|hybrid)$", description="Search mode"),
    page_size: int = Query(20, ge=1, le=100, description="Max results"),
) -> SemanticSearchResponse:
    """Hybrid semantic + keyword search with match explanations."""
    results = await search_service.hybrid_search(db, query_text=q, mode=mode, limit=page_size)
    return SemanticSearchResponse(items=results, total=len(results), query=q, mode=mode)
