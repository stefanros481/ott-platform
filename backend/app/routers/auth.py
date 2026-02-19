"""Auth router — registration, login, token refresh, profiles."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.dependencies import DB, CurrentUser, RedisClient
from app.models.entitlement import ContentPackage, UserEntitlement
from app.models.user import Profile
from sqlalchemy import and_
from app.schemas.auth import (
    LoginRequest,
    ProfileCreateRequest,
    ProfileResponse,
    RefreshRequest,
    RegisterRequest,
    SubscriptionUpgradeRequest,
    TokenResponse,
    UserResponse,
)
from app.services import auth_service

router = APIRouter()


# ── Public endpoints ─────────────────────────────────────────────────────────


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: DB) -> TokenResponse:
    """Create a new user account and return JWT tokens."""
    try:
        user = await auth_service.register_user(db, body.email, body.password)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    access_token = auth_service.create_access_token(user.id, user.is_admin)
    raw_refresh, token_hash = auth_service.create_refresh_token(user.id)
    await auth_service.store_refresh_token(db, user.id, token_hash)

    return TokenResponse(access_token=access_token, refresh_token=raw_refresh)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: DB) -> TokenResponse:
    """Authenticate with email/password and receive JWT tokens."""
    user = await auth_service.authenticate_user(db, body.email, body.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = auth_service.create_access_token(user.id, user.is_admin)
    raw_refresh, token_hash = auth_service.create_refresh_token(user.id)
    await auth_service.store_refresh_token(db, user.id, token_hash)

    return TokenResponse(access_token=access_token, refresh_token=raw_refresh)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: DB) -> TokenResponse:
    """Exchange a valid refresh token for a new token pair (rotation)."""
    try:
        access_token, new_refresh = await auth_service.refresh_access_token(
            db, body.refresh_token
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    return TokenResponse(access_token=access_token, refresh_token=new_refresh)


# ── Authenticated endpoints ──────────────────────────────────────────────────


@router.get("/me", response_model=UserResponse)
async def me(user: CurrentUser) -> UserResponse:
    """Return the currently authenticated user."""
    return UserResponse.model_validate(user)


@router.get("/profiles", response_model=list[ProfileResponse])
async def list_profiles(user: CurrentUser, db: DB) -> list[ProfileResponse]:
    """List all profiles belonging to the current user."""
    result = await db.execute(
        select(Profile).where(Profile.user_id == user.id).order_by(Profile.created_at)
    )
    profiles = result.scalars().all()
    return [ProfileResponse.model_validate(p) for p in profiles]


@router.post("/profiles", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    body: ProfileCreateRequest, user: CurrentUser, db: DB
) -> ProfileResponse:
    """Create a new profile for the current user."""
    profile = Profile(
        user_id=user.id,
        name=body.name,
        avatar_url=body.avatar_url,
        parental_rating=body.parental_rating,
        is_kids=body.is_kids,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return ProfileResponse.model_validate(profile)


@router.put("/profiles/{profile_id}/select", response_model=ProfileResponse)
async def select_profile(
    profile_id: str, user: CurrentUser, db: DB
) -> ProfileResponse:
    """Select (activate) a profile. Returns the profile for the client to store."""
    result = await db.execute(
        select(Profile).where(Profile.id == profile_id, Profile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )
    return ProfileResponse.model_validate(profile)


# ── Subscription upgrade ─────────────────────────────────────────────────────


@router.patch("/subscription", response_model=UserResponse)
async def upgrade_subscription(
    body: SubscriptionUpgradeRequest,
    user: CurrentUser,
    db: DB,
    redis: RedisClient,
) -> UserResponse:
    """Upgrade the current user's subscription to the requested tier.

    Finds the package matching the requested tier, expires any existing SVOD
    entitlement, creates a new one, and updates the user's subscription_tier.
    Invalidates the entitlement cache so the change takes effect immediately.
    """
    from datetime import datetime, timezone
    from app.services import entitlement_service

    pkg = (
        await db.execute(
            select(ContentPackage).where(ContentPackage.tier == body.tier)
        )
    ).scalar_one_or_none()

    if pkg is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No package found for tier '{body.tier}'",
        )

    now = datetime.now(timezone.utc)

    # Expire existing SVOD entitlements
    existing = await db.execute(
        select(UserEntitlement).where(
            and_(
                UserEntitlement.user_id == user.id,
                UserEntitlement.source_type == "subscription",
            )
        )
    )
    for ent in existing.scalars().all():
        ent.expires_at = now
    await db.flush()

    # Create new entitlement
    db.add(UserEntitlement(user_id=user.id, package_id=pkg.id, source_type="subscription"))

    # Update display tier
    user.subscription_tier = pkg.tier
    await db.commit()
    await db.refresh(user)

    await entitlement_service.invalidate_entitlement_cache(user.id, redis)

    return UserResponse.model_validate(user)
