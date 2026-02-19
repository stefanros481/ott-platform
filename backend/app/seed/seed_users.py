"""Seed data for users, profiles, content packages, entitlements, and package contents."""

import uuid

import bcrypt
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import Title
from app.models.entitlement import ContentPackage, PackageContent, UserEntitlement
from app.models.epg import Channel
from app.models.user import Profile, User
from app.services.auth_service import hash_password

# Default PIN assigned to every seeded user.
# Users can change it on the Parental Controls page.
DEFAULT_PIN = "1234"


def _hash_default_pin() -> str:
    return bcrypt.hashpw(DEFAULT_PIN.encode(), bcrypt.gensalt()).decode()

# ---------------------------------------------------------------------------
# User definitions
# ---------------------------------------------------------------------------
# (email, password, subscription_tier, is_admin, profiles)
# Each profile: (name, avatar_seed, parental_rating, is_kids)
# ---------------------------------------------------------------------------

USERS = [
    {
        "email": "admin@ott.test",
        "password": "admin123",
        "subscription_tier": "premium",
        "is_admin": True,
        "profiles": [
            {"name": "Admin", "avatar_seed": "admin", "parental_rating": "TV-MA", "is_kids": False},
            {"name": "Kids", "avatar_seed": "admin-kids", "parental_rating": "TV-Y", "is_kids": True},
        ],
    },
    {
        "email": "basic@ott.test",
        "password": "test123",
        "subscription_tier": "basic",
        "is_admin": False,
        "profiles": [
            {"name": "Basic User", "avatar_seed": "basic", "parental_rating": "TV-MA", "is_kids": False},
        ],
    },
    {
        "email": "standard@ott.test",
        "password": "test123",
        "subscription_tier": "standard",
        "is_admin": False,
        "profiles": [
            {"name": "Standard User", "avatar_seed": "standard", "parental_rating": "TV-MA", "is_kids": False},
            {"name": "Family", "avatar_seed": "standard-family", "parental_rating": "TV-PG", "is_kids": False},
        ],
    },
    {
        "email": "premium@ott.test",
        "password": "test123",
        "subscription_tier": "premium",
        "is_admin": False,
        "profiles": [
            {"name": "Premium User", "avatar_seed": "premium", "parental_rating": "TV-MA", "is_kids": False},
            {"name": "Partner", "avatar_seed": "premium-partner", "parental_rating": "TV-MA", "is_kids": False},
            {"name": "Kids", "avatar_seed": "premium-kids", "parental_rating": "TV-Y", "is_kids": True},
        ],
    },
    {
        "email": "demo@ott.test",
        "password": "demo123",
        "subscription_tier": "premium",
        "is_admin": False,
        "profiles": [
            {"name": "Demo User", "avatar_seed": "demo", "parental_rating": "TV-MA", "is_kids": False},
        ],
    },
]

# ---------------------------------------------------------------------------
# Package definitions
# ---------------------------------------------------------------------------
PACKAGES = [
    {
        "name": "Basic",
        "description": "Access to essential channels and a curated selection of on-demand titles. Perfect for casual viewers.",
        "title_pct": 0.60,   # 60% of titles
        "channel_count": 15,  # first 15 channels
    },
    {
        "name": "Standard",
        "description": "Expanded channel lineup and most of the on-demand catalog. Great for families and regular viewers.",
        "title_pct": 0.85,   # 85% of titles
        "channel_count": 25,  # first 25 channels
    },
    {
        "name": "Premium",
        "description": "Full access to every channel and the complete on-demand library including exclusive premieres and 4K content.",
        "title_pct": 1.00,   # 100% of titles
        "channel_count": 25,  # all channels
    },
]

# Map subscription tier to package name
_TIER_TO_PACKAGE = {
    "basic": "Basic",
    "standard": "Standard",
    "premium": "Premium",
}


async def seed_users(session: AsyncSession) -> dict[str, int]:
    """Seed content packages, users, profiles, entitlements, and package content links.

    Must run AFTER seed_catalog and seed_epg so that title and channel IDs exist.
    Idempotent: skips if users already exist.
    Returns counts of created entities.
    """
    result = await session.execute(select(User).limit(1))
    if result.scalar_one_or_none() is not None:
        print("  [seed_users] Users already seeded, skipping.")
        return {
            "packages": 0, "users": 0, "profiles": 0,
            "entitlements": 0, "package_contents": 0,
        }

    # ------------------------------------------------------------------
    # 1. Fetch all title IDs and channel IDs (ordered by creation)
    # ------------------------------------------------------------------
    title_result = await session.execute(
        select(Title.id).order_by(Title.created_at)
    )
    all_title_ids: list[uuid.UUID] = list(title_result.scalars().all())

    channel_result = await session.execute(
        select(Channel.id).order_by(Channel.channel_number)
    )
    all_channel_ids: list[uuid.UUID] = list(channel_result.scalars().all())

    if not all_title_ids or not all_channel_ids:
        print("  [seed_users] No titles or channels found. Run seed_catalog and seed_epg first.")
        return {
            "packages": 0, "users": 0, "profiles": 0,
            "entitlements": 0, "package_contents": 0,
        }

    total_titles = len(all_title_ids)
    total_channels = len(all_channel_ids)

    # ------------------------------------------------------------------
    # 2. Create content packages
    # ------------------------------------------------------------------
    package_map: dict[str, uuid.UUID] = {}
    for pkg in PACKAGES:
        pkg_id = uuid.uuid4()
        package_map[pkg["name"]] = pkg_id
        session.add(ContentPackage(
            id=pkg_id,
            name=pkg["name"],
            description=pkg["description"],
        ))
    await session.flush()
    print(f"  [seed_users] Created {len(PACKAGES)} content packages.")

    # ------------------------------------------------------------------
    # 3. Create PackageContent entries
    # ------------------------------------------------------------------
    package_content_count = 0
    for pkg in PACKAGES:
        pkg_id = package_map[pkg["name"]]

        # Titles: take first N% of titles
        n_titles = int(total_titles * pkg["title_pct"])
        for tid in all_title_ids[:n_titles]:
            session.add(PackageContent(
                package_id=pkg_id,
                content_type="vod_title",
                content_id=tid,
            ))
            package_content_count += 1

        # Channels: take first N channels
        n_channels = min(pkg["channel_count"], total_channels)
        for cid in all_channel_ids[:n_channels]:
            session.add(PackageContent(
                package_id=pkg_id,
                content_type="channel",
                content_id=cid,
            ))
            package_content_count += 1

    await session.flush()
    print(f"  [seed_users] Created {package_content_count} package content entries.")

    # ------------------------------------------------------------------
    # 4. Create users with profiles and entitlements
    # ------------------------------------------------------------------
    user_count = 0
    profile_count = 0
    entitlement_count = 0

    for u in USERS:
        user_id = uuid.uuid4()
        session.add(User(
            id=user_id,
            email=u["email"],
            password_hash=hash_password(u["password"]),
            subscription_tier=u["subscription_tier"],
            is_admin=u["is_admin"],
            is_active=True,
            pin_hash=_hash_default_pin(),
        ))
        user_count += 1

        # Profiles
        for p in u["profiles"]:
            session.add(Profile(
                user_id=user_id,
                name=p["name"],
                avatar_url=f"https://api.dicebear.com/7.x/avataaars/svg?seed={p['avatar_seed']}",
                parental_rating=p["parental_rating"],
                is_kids=p["is_kids"],
            ))
            profile_count += 1

        # Entitlement — link user to their package
        pkg_name = _TIER_TO_PACKAGE[u["subscription_tier"]]
        pkg_id = package_map[pkg_name]
        session.add(UserEntitlement(
            user_id=user_id,
            package_id=pkg_id,
            source_type="subscription",
        ))
        entitlement_count += 1

    await session.flush()
    print(
        f"  [seed_users] Created {user_count} users, "
        f"{profile_count} profiles, {entitlement_count} entitlements."
    )

    await session.commit()

    return {
        "packages": len(PACKAGES),
        "users": user_count,
        "profiles": profile_count,
        "entitlements": entitlement_count,
        "package_contents": package_content_count,
    }
