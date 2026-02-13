"""Seed data package for the OTT platform PoC."""

from app.seed.seed_catalog import seed_catalog
from app.seed.seed_embeddings import seed_embeddings
from app.seed.seed_epg import seed_epg
from app.seed.seed_users import seed_users
from app.seed.seed_viewing_time import seed_viewing_time

__all__ = [
    "seed_catalog",
    "seed_epg",
    "seed_users",
    "seed_embeddings",
    "seed_viewing_time",
]


async def run_all_seeds(session, *, include_embeddings: bool = False) -> dict[str, int]:
    """Run all seed functions in dependency order.

    Returns a summary dict with counts of created entities.
    """
    summary: dict[str, int] = {}

    catalog_counts = await seed_catalog(session)
    summary.update(catalog_counts)

    epg_counts = await seed_epg(session)
    summary.update(epg_counts)

    user_counts = await seed_users(session)
    summary.update(user_counts)

    if include_embeddings:
        embed_counts = await seed_embeddings(session)
        summary.update(embed_counts)

    # Viewing time seed must run after users + catalog
    viewing_time_counts = await seed_viewing_time(session)
    summary.update(viewing_time_counts)

    return summary
