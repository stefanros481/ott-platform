"""Entitlement service — access checking, TVOD purchases, stream limit enforcement.

Design decisions (see specs/012-entitlements-tvod/plan.md for full rationale):
- check_access_cached: fail-closed on Redis/DB errors (deny access rather than grant)
- Rental TTL = min(300, seconds_until_expiry) to satisfy SC-003 (60s expiry propagation)
- get_access_options: direct DB queries (no Redis cache) — returns rich data that the
  bool cache can't provide; two indexed queries are fast enough at PoC scale
- free offer access: direct TitleOffer lookup — no UserEntitlement row is created
- invalidate_entitlement_cache: SCAN+DELETE has ~100ms consistency window (acceptable
  for PoC); production would use Lua script for atomic scan-and-delete
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone

import redis.asyncio
from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entitlement import ContentPackage, PackageContent, TitleOffer, UserEntitlement
from app.models.stream_sessions import StreamSession
from app.schemas.catalog import AccessOption, UserAccess

logger = logging.getLogger(__name__)

_CACHE_KEY = "ent:{user_id}:{title_id}"
_CACHE_TTL_DEFAULT = 300  # seconds


# ── Internal helpers ──────────────────────────────────────────────────────────


def _cache_key(user_id: uuid.UUID, title_id: uuid.UUID) -> str:
    return f"ent:{user_id}:{title_id}"


def _user_glob(user_id: uuid.UUID) -> str:
    return f"ent:{user_id}:*"


async def _raw_check_access(
    user_id: uuid.UUID,
    title_id: uuid.UUID,
    db: AsyncSession,
) -> tuple[bool, str | None, datetime | None]:
    """Check access and return (has_access, access_type, expires_at).

    Access paths (in priority order):
    1. SVOD: active subscription entitlement whose package contains the title
    2. TVOD buy: permanent purchase entitlement for this title
    3. TVOD rent: time-limited rental for this title (not expired)
    4. Free offer: active free TitleOffer (no UserEntitlement row required)
    """
    now = datetime.now(timezone.utc)

    # 1. SVOD — subscription package membership
    svod_result = await db.execute(
        select(UserEntitlement).where(
            and_(
                UserEntitlement.user_id == user_id,
                UserEntitlement.source_type == "subscription",
                UserEntitlement.package_id.is_not(None),
                (UserEntitlement.expires_at.is_(None)) | (UserEntitlement.expires_at > now),
            )
        )
    )
    svod_entitlements = svod_result.scalars().all()

    for ent in svod_entitlements:
        pkg_check = await db.execute(
            select(PackageContent).where(
                and_(
                    PackageContent.package_id == ent.package_id,
                    PackageContent.content_type == "vod_title",
                    PackageContent.content_id == title_id,
                )
            )
        )
        if pkg_check.scalar_one_or_none() is not None:
            return True, "svod", None

    # 2. TVOD buy (permanent — no expiry)
    buy_result = await db.execute(
        select(UserEntitlement).where(
            and_(
                UserEntitlement.user_id == user_id,
                UserEntitlement.source_type == "tvod",
                UserEntitlement.title_id == title_id,
                UserEntitlement.expires_at.is_(None),
            )
        )
    )
    if buy_result.scalar_one_or_none() is not None:
        return True, "tvod_buy", None

    # 3. TVOD rent (time-limited)
    rent_result = await db.execute(
        select(UserEntitlement).where(
            and_(
                UserEntitlement.user_id == user_id,
                UserEntitlement.source_type == "tvod",
                UserEntitlement.title_id == title_id,
                UserEntitlement.expires_at.is_not(None),
                UserEntitlement.expires_at > now,
            )
        )
    )
    rental = rent_result.scalar_one_or_none()
    if rental is not None:
        return True, "tvod_rent", rental.expires_at

    # 4. Free offer
    free_offer = await db.execute(
        select(TitleOffer).where(
            and_(
                TitleOffer.title_id == title_id,
                TitleOffer.offer_type == "free",
                TitleOffer.is_active.is_(True),
            )
        )
    )
    if free_offer.scalar_one_or_none() is not None:
        return True, "free", None

    return False, None, None


# ── Public API ────────────────────────────────────────────────────────────────


async def check_access(
    user_id: uuid.UUID,
    title_id: uuid.UUID,
    db: AsyncSession,
    redis: redis.asyncio.Redis,
) -> bool:
    """Check if user has any active entitlement for the given title (uncached)."""
    has_access, _, _ = await _raw_check_access(user_id, title_id, db)
    return has_access


async def check_access_cached(
    user_id: uuid.UUID,
    title_id: uuid.UUID,
    db: AsyncSession,
    redis: redis.asyncio.Redis,
) -> bool:
    """Check access with Redis caching. Fail-closed on any error (deny access).

    TTL strategy:
    - SVOD / TVOD buy: 300 seconds (no natural expiry, invalidated on subscription change)
    - TVOD rental: min(300, seconds_until_rental_expiry) — ensures cached access
      expires within 60 seconds of rental expiry (satisfies SC-003)
    - No access: cached as '0' for 30 seconds to reduce DB load on repeated denials
    """
    key = _cache_key(user_id, title_id)

    try:
        cached = await redis.get(key)
        if cached is not None:
            return cached == "1"
    except Exception as exc:
        logger.warning("Redis read failed for key %s, falling back to DB: %s", key, exc)

    try:
        has_access, access_type, expires_at = await _raw_check_access(user_id, title_id, db)
    except Exception as exc:
        logger.error("DB entitlement check failed for user=%s title=%s: %s", user_id, title_id, exc)
        return False  # fail-closed

    # Determine TTL
    if has_access and access_type == "tvod_rent" and expires_at is not None:
        now = datetime.now(timezone.utc)
        secs_until_expiry = max(0, int((expires_at - now).total_seconds()))
        ttl = min(_CACHE_TTL_DEFAULT, secs_until_expiry)
        if ttl == 0:
            # Rental just expired — cache as denied
            has_access = False
    elif has_access:
        ttl = _CACHE_TTL_DEFAULT
    else:
        ttl = 30  # short negative-cache TTL

    try:
        await redis.setex(key, ttl, "1" if has_access else "0")
    except Exception as exc:
        logger.warning("Redis write failed for key %s: %s", key, exc)

    return has_access


async def get_access_options(
    title_id: uuid.UUID,
    user_id: uuid.UUID | None,
    db: AsyncSession,
    redis: redis.asyncio.Redis,
) -> tuple[list[AccessOption], UserAccess | None]:
    """Return structured access options and current user entitlement status.

    Queries DB directly (no Redis cache) — returns richer data than check_access_cached.
    Two indexed queries: TitleOffers (ix_title_offers_title_active) +
    UserEntitlements (ix_ue_user_title_expires) at PoC scale.
    """
    # Fetch all active offers for this title
    offers_result = await db.execute(
        select(TitleOffer).where(
            and_(
                TitleOffer.title_id == title_id,
                TitleOffer.is_active.is_(True),
            )
        )
    )
    active_offers = offers_result.scalars().all()

    options: list[AccessOption] = []
    for offer in active_offers:
        if offer.offer_type == "free":
            options.append(AccessOption(type="free", label="Free"))
        elif offer.offer_type == "rent":
            options.append(AccessOption(
                type="rent",
                label=f"Rent for ${offer.price_cents / 100:.2f}",
                price_cents=offer.price_cents,
                currency=offer.currency,
                rental_window_hours=offer.rental_window_hours,
            ))
        elif offer.offer_type == "buy":
            options.append(AccessOption(
                type="buy",
                label=f"Buy for ${offer.price_cents / 100:.2f}",
                price_cents=offer.price_cents,
                currency=offer.currency,
            ))

    # Check SVOD package membership
    svod_access = False
    if user_id is not None:
        svod_check = await db.execute(
            select(PackageContent).where(
                and_(
                    PackageContent.content_type == "vod_title",
                    PackageContent.content_id == title_id,
                )
            )
        )
        pkg_ids_with_title = {row.package_id for row in svod_check.scalars().all()}

        if pkg_ids_with_title:
            now = datetime.now(timezone.utc)
            svod_ent_result = await db.execute(
                select(UserEntitlement).where(
                    and_(
                        UserEntitlement.user_id == user_id,
                        UserEntitlement.source_type == "subscription",
                        UserEntitlement.package_id.in_(pkg_ids_with_title),
                        (UserEntitlement.expires_at.is_(None)) | (UserEntitlement.expires_at > now),
                    )
                )
            )
            if svod_ent_result.scalar_one_or_none() is not None:
                svod_access = True

    # If user has SVOD access, show that
    if user_id is not None and svod_access:
        return options, UserAccess(
            has_access=True,
            access_type="svod",
            expires_at=None,
        )

    # Check TVOD entitlements if authenticated
    if user_id is not None:
        now = datetime.now(timezone.utc)

        # Check buy (permanent)
        buy_result = await db.execute(
            select(UserEntitlement).where(
                and_(
                    UserEntitlement.user_id == user_id,
                    UserEntitlement.source_type == "tvod",
                    UserEntitlement.title_id == title_id,
                    UserEntitlement.expires_at.is_(None),
                )
            )
        )
        if buy_result.scalar_one_or_none() is not None:
            # User owns it — suppress rent option (FR-015)
            options = [o for o in options if o.type != "rent"]
            return options, UserAccess(has_access=True, access_type="tvod_buy", expires_at=None)

        # Check rent (time-limited)
        rent_result = await db.execute(
            select(UserEntitlement).where(
                and_(
                    UserEntitlement.user_id == user_id,
                    UserEntitlement.source_type == "tvod",
                    UserEntitlement.title_id == title_id,
                    UserEntitlement.expires_at.is_not(None),
                    UserEntitlement.expires_at > now,
                )
            )
        )
        rental = rent_result.scalar_one_or_none()
        if rental is not None:
            # Active rental — suppress duplicate rent option
            options = [o for o in options if o.type != "rent"]
            return options, UserAccess(
                has_access=True,
                access_type="tvod_rent",
                expires_at=rental.expires_at,
            )

    # Check free offer — free content is accessible without login
    free_offer_exists = any(o.offer_type == "free" for o in active_offers)
    if free_offer_exists:
        return options, UserAccess(has_access=True, access_type="free", expires_at=None)

    # Find the lowest SVOD tier that grants access to this title so the
    # frontend can show "Upgrade to Standard" / "Subscribe with Basic" etc.
    _tier_order = {"basic": 0, "standard": 1, "premium": 2}
    required_tier: str | None = None
    tier_result = await db.execute(
        select(ContentPackage.tier).join(
            PackageContent,
            and_(
                PackageContent.package_id == ContentPackage.id,
                PackageContent.content_type == "vod_title",
                PackageContent.content_id == title_id,
            ),
        )
    )
    pkg_tiers = [t for t in tier_result.scalars().all() if t]
    if pkg_tiers:
        required_tier = min(pkg_tiers, key=lambda t: _tier_order.get(t, 99))

    # No access — return a UserAccess object even for unauthenticated users so
    # the frontend can distinguish "locked with no purchase path" from "unknown".
    return options, UserAccess(
        has_access=False,
        access_type=None,
        expires_at=None,
        required_tier=required_tier,
    )


async def create_tvod_entitlement(
    user_id: uuid.UUID,
    title_id: uuid.UUID,
    offer_type: str,
    db: AsyncSession,
    redis: redis.asyncio.Redis,
) -> UserEntitlement:
    """Create a TVOD (rent or buy) entitlement for a user.

    Raises:
        ValueError: if offer_type is 'free' (free titles don't get UserEntitlement rows)
        LookupError: if no active offer of this type exists for the title
        RuntimeError: if user already has an active entitlement of this type
    """
    if offer_type == "free":
        raise ValueError("Free titles are accessed directly — no entitlement purchase required")

    now = datetime.now(timezone.utc)

    # Validate offer exists
    offer_result = await db.execute(
        select(TitleOffer).where(
            and_(
                TitleOffer.title_id == title_id,
                TitleOffer.offer_type == offer_type,
                TitleOffer.is_active.is_(True),
            )
        )
    )
    offer = offer_result.scalar_one_or_none()
    if offer is None:
        raise LookupError(f"No active {offer_type} offer for title {title_id}")

    # Check for duplicate active entitlement
    if offer_type == "rent":
        dup_result = await db.execute(
            select(UserEntitlement).where(
                and_(
                    UserEntitlement.user_id == user_id,
                    UserEntitlement.source_type == "tvod",
                    UserEntitlement.title_id == title_id,
                    UserEntitlement.expires_at.is_not(None),
                    UserEntitlement.expires_at > now,
                )
            )
        )
    else:  # buy
        dup_result = await db.execute(
            select(UserEntitlement).where(
                and_(
                    UserEntitlement.user_id == user_id,
                    UserEntitlement.source_type == "tvod",
                    UserEntitlement.title_id == title_id,
                    UserEntitlement.expires_at.is_(None),
                )
            )
        )
    if dup_result.scalar_one_or_none() is not None:
        raise RuntimeError(f"User already has an active {offer_type} entitlement for this title")

    # Calculate expiry for rental
    expires_at = None
    if offer_type == "rent" and offer.rental_window_hours:
        expires_at = now + timedelta(hours=offer.rental_window_hours)

    entitlement = UserEntitlement(
        user_id=user_id,
        title_id=title_id,
        source_type="tvod",
        expires_at=expires_at,
    )
    db.add(entitlement)
    await db.commit()
    await db.refresh(entitlement)

    # Invalidate cache so playback check picks up new entitlement immediately
    await invalidate_entitlement_cache(user_id, redis)

    return entitlement


async def check_stream_limit(
    user_id: uuid.UUID,
    db: AsyncSession,
) -> tuple[bool, list[StreamSession]]:
    """Check if user can start a new stream.

    First expires abandoned sessions (no heartbeat for 5+ minutes),
    then compares active session count against user's package max_streams.

    Returns (can_start, active_sessions).
    """
    now = datetime.now(timezone.utc)
    abandoned_cutoff = now - timedelta(minutes=2)

    # Expire abandoned sessions atomically (update ended_at)
    await db.execute(
        update(StreamSession)
        .where(
            and_(
                StreamSession.user_id == user_id,
                StreamSession.ended_at.is_(None),
                StreamSession.last_heartbeat_at < abandoned_cutoff,
            )
        )
        .values(ended_at=now)
    )
    await db.flush()

    # Count remaining active sessions
    active_result = await db.execute(
        select(StreamSession).where(
            and_(
                StreamSession.user_id == user_id,
                StreamSession.ended_at.is_(None),
            )
        )
    )
    active_sessions = active_result.scalars().all()
    active_count = len(active_sessions)

    # Get user's stream limit from their active subscription package
    from app.models.user import User
    ent_result = await db.execute(
        select(UserEntitlement, ContentPackage).join(
            ContentPackage, ContentPackage.id == UserEntitlement.package_id
        ).where(
            and_(
                UserEntitlement.user_id == user_id,
                UserEntitlement.source_type == "subscription",
                UserEntitlement.package_id.is_not(None),
                (UserEntitlement.expires_at.is_(None)) | (UserEntitlement.expires_at > now),
            )
        ).order_by(ContentPackage.max_streams.desc())
    )
    rows = ent_result.all()

    max_streams = 0
    if rows:
        # Use the most permissive (highest max_streams) active subscription
        max_streams = rows[0][1].max_streams

    can_start = active_count < max_streams
    return can_start, list(active_sessions)


async def invalidate_entitlement_cache(
    user_id: uuid.UUID,
    redis: redis.asyncio.Redis,
) -> None:
    """Delete all cached entitlement keys for a user.

    Uses SCAN + DELETE. There is a ~100ms consistency window between cursor
    advances where a concurrent check could read a stale key. Acceptable for
    PoC (SC-002 requires 10s propagation, not 100ms atomicity).
    """
    pattern = _user_glob(user_id)
    try:
        cursor = 0
        while True:
            cursor, keys = await redis.scan(cursor, match=pattern, count=100)
            if keys:
                await redis.delete(*keys)
            if cursor == 0:
                break
    except Exception as exc:
        logger.warning("Cache invalidation failed for user %s: %s", user_id, exc)
