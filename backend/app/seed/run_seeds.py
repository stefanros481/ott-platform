"""Main entry point for seeding the OTT platform database.

Usage:
    uv run python -m app.seed.run_seeds                # seed catalog, EPG, users
    uv run python -m app.seed.run_seeds --embeddings   # also generate embeddings
"""

import argparse
import asyncio
import sys
import time

from sqlalchemy import text

from app.database import async_session_factory, engine

# Ensure all models are imported so SQLAlchemy discovers them
import app.models  # noqa: F401


async def _check_db_connection() -> bool:
    """Verify the database is reachable."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"  Database connection failed: {e}")
        return False


async def _ensure_tables() -> None:
    """Create all tables if they do not exist.

    This is a safety fallback. In production, Alembic migrations should be
    used instead. We import Base here after models have been loaded.
    """
    from app.database import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def main(include_embeddings: bool = False) -> None:
    """Run all seed functions in order and print a summary."""
    print("=" * 60)
    print("  OTT Platform — Database Seeder")
    print("=" * 60)

    # 1. Check connectivity
    print("\n[1/5] Checking database connection...")
    if not await _check_db_connection():
        print("ERROR: Cannot connect to the database. Check DATABASE_URL.")
        sys.exit(1)
    print("  Connected.")

    # 2. Ensure tables exist
    print("\n[2/5] Ensuring tables exist...")
    await _ensure_tables()
    print("  Tables ready.")

    # 3. Seed catalog
    print("\n[3/5] Seeding catalog (genres, titles, cast, seasons, episodes)...")
    start = time.monotonic()
    from app.seed.seed_catalog import seed_catalog

    async with async_session_factory() as session:
        catalog_counts = await seed_catalog(session)
    elapsed = time.monotonic() - start
    print(f"  Done in {elapsed:.1f}s.")

    # 4. Seed EPG
    print("\n[4/5] Seeding EPG (channels, schedule entries)...")
    start = time.monotonic()
    from app.seed.seed_epg import seed_epg

    async with async_session_factory() as session:
        epg_counts = await seed_epg(session)
    elapsed = time.monotonic() - start
    print(f"  Done in {elapsed:.1f}s.")

    # 5. Seed users (depends on catalog + EPG)
    print("\n[5/5] Seeding users (packages, users, profiles, entitlements)...")
    start = time.monotonic()
    from app.seed.seed_users import seed_users

    async with async_session_factory() as session:
        user_counts = await seed_users(session)
    elapsed = time.monotonic() - start
    print(f"  Done in {elapsed:.1f}s.")

    # Optional: Embeddings
    embed_counts: dict[str, int] = {}
    if include_embeddings:
        print("\n[+] Generating content embeddings (this may take a minute)...")
        start = time.monotonic()
        from app.seed.seed_embeddings import seed_embeddings

        async with async_session_factory() as session:
            embed_counts = await seed_embeddings(session)
        elapsed = time.monotonic() - start
        print(f"  Done in {elapsed:.1f}s.")

    # Summary
    all_counts = {**catalog_counts, **epg_counts, **user_counts, **embed_counts}
    print("\n" + "=" * 60)
    print("  SEED SUMMARY")
    print("=" * 60)
    for key, value in all_counts.items():
        label = key.replace("_", " ").title()
        print(f"  {label:<25} {value:>6}")
    print("=" * 60)

    total = sum(all_counts.values())
    if total == 0:
        print("  Database was already seeded. No new records created.")
    else:
        print(f"  Total records created: {total}")
    print()

    # Dispose engine to close all connections
    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the OTT platform database.")
    parser.add_argument(
        "--embeddings",
        action="store_true",
        help="Also generate content embeddings using sentence-transformers.",
    )
    args = parser.parse_args()

    asyncio.run(main(include_embeddings=args.embeddings))
