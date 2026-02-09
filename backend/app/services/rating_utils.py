"""Rating hierarchy utilities for parental content filtering."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import Profile

# US TV Parental Guidelines in ascending restrictiveness.
RATING_HIERARCHY: list[str] = ["TV-Y", "TV-G", "TV-PG", "TV-14", "TV-MA"]


def get_allowed_ratings(parental_rating: str) -> list[str] | None:
    """Return the list of age ratings a profile is allowed to see.

    Returns None for TV-MA (no filtering needed), or a list of allowed
    rating strings for any other level.
    """
    if parental_rating == "TV-MA":
        return None
    try:
        idx = RATING_HIERARCHY.index(parental_rating)
    except ValueError:
        # Unknown rating — treat as unrestricted.
        return None
    return RATING_HIERARCHY[: idx + 1]


async def resolve_profile_rating(
    db: AsyncSession, profile_id: uuid.UUID
) -> list[str] | None:
    """Fetch the profile's parental_rating and return allowed ratings.

    Returns None when the profile has TV-MA or is not found (fail-open for PoC).
    """
    result = await db.execute(
        select(Profile.parental_rating).where(Profile.id == profile_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        return None
    return get_allowed_ratings(row)
