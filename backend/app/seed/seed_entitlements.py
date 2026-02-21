"""Seed data for Feature 012 — Subscription Tiers, Entitlements & TVOD.

Idempotent: checks before inserting/updating. Safe to re-run.

This seed MUST run AFTER seed_users (packages must already exist).

What it does:
  1. Updates the existing Basic/Standard/Premium packages with tier + max_streams
     + Nordic pricing (NOK).
  2. Adds/updates TitleOffers on a subset of catalog titles:
       - First 5 titles:       free (no auth required)
       - Last 40% of titles:   rent (49 NOK / 48h) + buy (129 NOK)
  3. Creates four quickstart test users (idempotent — skipped if email exists):
       - admin@test.com   (is_admin, Premium plan)
       - basic@test.com   (Basic plan, 1 stream)
       - premium@test.com (Premium plan, 4 streams)
       - noplan@test.com  (no subscription — uses rent/buy or free titles)
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import Title
from app.models.entitlement import ContentPackage, TitleOffer, UserEntitlement
from app.models.user import Profile, User
from app.services.auth_service import hash_password

# ---------------------------------------------------------------------------
# Package tier / stream-limit metadata
# ---------------------------------------------------------------------------

PACKAGE_ATTRS = {
    "Basic":    {"tier": "basic",    "max_streams": 1},
    "Standard": {"tier": "standard", "max_streams": 2},
    "Premium":  {"tier": "premium",  "max_streams": 4},
}

# ---------------------------------------------------------------------------
# Test users created by this seed
# ---------------------------------------------------------------------------

TEST_USERS = [
    {
        "email":    "admin@test.com",
        "password": "admin1234",
        "subscription": "Premium",
        "is_admin": True,
    },
    {
        "email":    "basic@test.com",
        "password": "test1234",
        "subscription": "Basic",
        "is_admin": False,
    },
    {
        "email":    "premium@test.com",
        "password": "test1234",
        "subscription": "Premium",
        "is_admin": False,
    },
    {
        "email":    "noplan@test.com",
        "password": "test1234",
        "subscription": None,  # no subscription — relies on TVOD / free
        "is_admin": False,
    },
]

# ---------------------------------------------------------------------------
# Nordic pricing (NOK as primary market currency)
# ---------------------------------------------------------------------------

RENT_PRICE_CENTS  = 4900   # 49 NOK
BUY_PRICE_CENTS   = 12900  # 129 NOK
RENT_WINDOW_HOURS = 48
CURRENCY          = "NOK"

# Subscription package pricing (NOK)
PACKAGE_PRICING = {
    "Basic":    9900,   # 99 NOK/mo
    "Standard": 14900,  # 149 NOK/mo
    "Premium":  24900,  # 249 NOK/mo
}


async def seed_entitlements(session: AsyncSession) -> dict[str, int]:
    """Run all Feature-012 seed steps. Returns counts of created records."""

    counts: dict[str, int] = {
        "packages_updated": 0,
        "title_offers": 0,
        "users": 0,
        "entitlements": 0,
    }

    # ------------------------------------------------------------------
    # 1. Update packages with tier + max_streams
    # ------------------------------------------------------------------
    pkg_result = await session.execute(select(ContentPackage))
    packages = {pkg.name: pkg for pkg in pkg_result.scalars().all()}

    for pkg_name, attrs in PACKAGE_ATTRS.items():
        pkg = packages.get(pkg_name)
        if pkg is None:
            continue
        changed = False
        if pkg.tier != attrs["tier"]:
            pkg.tier = attrs["tier"]
            changed = True
        if pkg.max_streams != attrs["max_streams"]:
            pkg.max_streams = attrs["max_streams"]
            changed = True
        if pkg.price_cents != PACKAGE_PRICING.get(pkg_name, 0):
            pkg.price_cents = PACKAGE_PRICING.get(pkg_name, 0)
            changed = True
        if pkg.currency != CURRENCY:
            pkg.currency = CURRENCY
            changed = True
        if changed:
            counts["packages_updated"] += 1

    await session.flush()
    print(f"  [seed_entitlements] Updated {counts['packages_updated']} package(s) with NOK pricing.")

    # ------------------------------------------------------------------
    # 2. Add TitleOffers
    # ------------------------------------------------------------------
    title_result = await session.execute(
        select(Title.id).order_by(Title.created_at)
    )
    all_title_ids: list[uuid.UUID] = list(title_result.scalars().all())

    if not all_title_ids:
        print("  [seed_entitlements] No titles found — skipping TitleOffers.")
    else:
        # Free offers: first 5 titles
        free_ids = all_title_ids[:5]

        # Rent + buy offers: all titles NOT in the Basic package (~last 40%)
        # Basic gets 60% of titles per seed_users.py PACKAGES definition.
        # Without TVOD offers, Basic users would see these titles as locked
        # with no purchase path — so we add rent + buy on all of them.
        basic_cutoff = int(len(all_title_ids) * 0.60)
        tvod_ids = all_title_ids[basic_cutoff:]

        nordic = {"NOK", "DKK", "SEK"}

        # Helper: insert offer if missing, update currency/price if non-Nordic
        async def _upsert_offer(title_id: uuid.UUID, offer_type: str, price_cents: int, currency: str, **kwargs) -> str:
            result = await session.execute(
                select(TitleOffer).where(
                    and_(
                        TitleOffer.title_id == title_id,
                        TitleOffer.offer_type == offer_type,
                    )
                )
            )
            existing = result.scalar_one_or_none()
            if existing is None:
                session.add(TitleOffer(
                    title_id=title_id,
                    offer_type=offer_type,
                    price_cents=price_cents,
                    currency=currency,
                    **kwargs,
                ))
                return "created"
            elif existing.currency not in nordic:
                existing.currency = currency
                existing.price_cents = price_cents
                return "updated"
            return "skipped"

        offers_created = 0
        offers_updated = 0

        for tid in free_ids:
            action = await _upsert_offer(tid, "free", 0, CURRENCY)
            if action == "created":
                offers_created += 1
            elif action == "updated":
                offers_updated += 1

        for tid in tvod_ids:
            action = await _upsert_offer(tid, "rent", RENT_PRICE_CENTS, CURRENCY, rental_window_hours=RENT_WINDOW_HOURS)
            if action == "created":
                offers_created += 1
            elif action == "updated":
                offers_updated += 1

            action = await _upsert_offer(tid, "buy", BUY_PRICE_CENTS, CURRENCY)
            if action == "created":
                offers_created += 1
            elif action == "updated":
                offers_updated += 1

        counts["title_offers"] = offers_created

        await session.flush()
        print(f"  [seed_entitlements] Created {offers_created} title offer(s), updated {offers_updated} to NOK currency.")

    # ------------------------------------------------------------------
    # 3. Create test users + entitlements (idempotent)
    # ------------------------------------------------------------------
    # Refresh package map after flush
    pkg_result2 = await session.execute(select(ContentPackage))
    packages = {pkg.name: pkg for pkg in pkg_result2.scalars().all()}

    for u in TEST_USERS:
        # Check if user already exists
        existing = await session.execute(
            select(User).where(User.email == u["email"])
        )
        if existing.scalar_one_or_none() is not None:
            continue

        user_id = uuid.uuid4()
        subscription_tier = None
        if u["subscription"]:
            pkg = packages.get(u["subscription"])
            if pkg:
                subscription_tier = pkg.tier

        session.add(User(
            id=user_id,
            email=u["email"],
            password_hash=hash_password(u["password"]),
            subscription_tier=subscription_tier,
            is_admin=u.get("is_admin", False),
            is_active=True,
        ))

        # Default profile
        session.add(Profile(
            user_id=user_id,
            name=u["email"].split("@")[0].replace(".", " ").title(),
            avatar_url=f"https://api.dicebear.com/7.x/avataaars/svg?seed={u['email']}",
            parental_rating="TV-MA",
            is_kids=False,
        ))
        counts["users"] += 1

        # Subscription entitlement
        if u["subscription"] and u["subscription"] in packages:
            pkg = packages[u["subscription"]]
            session.add(UserEntitlement(
                user_id=user_id,
                package_id=pkg.id,
                source_type="subscription",
            ))
            counts["entitlements"] += 1

    await session.flush()
    print(
        f"  [seed_entitlements] Created {counts['users']} test user(s), "
        f"{counts['entitlements']} entitlement(s)."
    )

    await session.commit()
    return counts
