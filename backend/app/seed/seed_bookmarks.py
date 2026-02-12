"""Seed bookmark data for Continue Watching & Paused section demo.

Creates 7 bookmarks across profiles to demonstrate:
- Active bookmarks (recent, varying progress)
- Stale bookmark (35 days old → appears in Paused)
- Dismissed bookmark (manually archived → appears in Paused)
- Completed bookmark (excluded from both rails)
- Kids profile bookmark (parental filtering)
"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import Episode, Season, Title
from app.models.user import Profile, User
from app.models.viewing import Bookmark


async def seed_bookmarks(session: AsyncSession) -> dict[str, int]:
    """Create demo bookmarks. Returns count of created records."""
    # Check if bookmarks already exist
    count = await session.scalar(select(func.count()).select_from(Bookmark))
    if count and count > 0:
        return {"bookmarks": 0}

    # Look up demo user's adult profile
    demo_user = (
        await session.execute(
            select(User).where(User.email == "demo@ott.test")
        )
    ).scalar_one_or_none()
    if demo_user is None:
        print("  WARNING: demo@ott.test not found — skipping bookmark seed")
        return {"bookmarks": 0}

    profiles = (
        await session.execute(
            select(Profile).where(Profile.user_id == demo_user.id)
        )
    ).scalars().all()

    adult_profile = next((p for p in profiles if not p.is_kids), None)
    kids_profile = next((p for p in profiles if p.is_kids), None)

    if adult_profile is None:
        print("  WARNING: No adult profile found for demo user — skipping bookmark seed")
        return {"bookmarks": 0}

    # Fetch movies and series episodes for bookmark targets
    movies = (
        await session.execute(
            select(Title)
            .where(Title.title_type == "movie")
            .order_by(Title.title)
            .limit(10)
        )
    ).scalars().all()

    episodes = (
        await session.execute(
            select(Episode)
            .join(Season)
            .order_by(Season.season_number, Episode.episode_number)
            .limit(10)
        )
    ).scalars().all()

    # Fetch a kids-appropriate title
    kids_titles = (
        await session.execute(
            select(Title)
            .where(Title.title_type == "movie", Title.age_rating.in_(["TV-Y", "TV-G", "G", "PG"]))
            .limit(5)
        )
    ).scalars().all()

    now = datetime.now(timezone.utc)
    bookmarks_created = 0

    # --- Bookmark 1: Active movie, recent, 37% progress ---
    if len(movies) >= 1:
        session.add(Bookmark(
            profile_id=adult_profile.id,
            content_type="movie",
            content_id=movies[0].id,
            position_seconds=2700,  # 45 min
            duration_seconds=7200,  # 120 min → 37.5%
            completed=False,
        ))
        bookmarks_created += 1

    # --- Bookmark 2: Active series episode, near completion (next-ep demo) ---
    if len(episodes) >= 1:
        ep = episodes[0]
        duration = (ep.duration_minutes or 22) * 60
        session.add(Bookmark(
            profile_id=adult_profile.id,
            content_type="episode",
            content_id=ep.id,
            position_seconds=int(duration * 0.82),  # 82% → not completed but close
            duration_seconds=duration,
            completed=False,
        ))
        bookmarks_created += 1

    # --- Bookmark 3: Active movie, 2 days old, mid-progress ---
    if len(movies) >= 2:
        b = Bookmark(
            profile_id=adult_profile.id,
            content_type="movie",
            content_id=movies[1].id,
            position_seconds=1800,  # 30 min
            duration_seconds=5400,  # 90 min → 33%
            completed=False,
        )
        session.add(b)
        bookmarks_created += 1
        # We'll update updated_at after commit via raw SQL

    # --- Bookmark 4: Stale movie (35 days old → Paused section) ---
    if len(movies) >= 3:
        b = Bookmark(
            profile_id=adult_profile.id,
            content_type="movie",
            content_id=movies[2].id,
            position_seconds=600,   # 10 min
            duration_seconds=3600,  # 60 min → 16.7%
            completed=False,
        )
        session.add(b)
        bookmarks_created += 1

    # --- Bookmark 5: Dismissed movie → Paused section ---
    if len(movies) >= 4:
        session.add(Bookmark(
            profile_id=adult_profile.id,
            content_type="movie",
            content_id=movies[3].id,
            position_seconds=300,   # 5 min
            duration_seconds=6000,  # 100 min → 5%
            completed=False,
            dismissed_at=now - timedelta(days=2),
        ))
        bookmarks_created += 1

    # --- Bookmark 6: Completed movie → excluded from both rails ---
    if len(movies) >= 5:
        session.add(Bookmark(
            profile_id=adult_profile.id,
            content_type="movie",
            content_id=movies[4].id,
            position_seconds=5700,  # 95 min
            duration_seconds=6000,  # 100 min → 95% completed
            completed=True,
        ))
        bookmarks_created += 1

    # --- Bookmark 7: Kids profile active bookmark ---
    if kids_profile and len(kids_titles) >= 1:
        session.add(Bookmark(
            profile_id=kids_profile.id,
            content_type="movie",
            content_id=kids_titles[0].id,
            position_seconds=1200,  # 20 min
            duration_seconds=4500,  # 75 min → 26.7%
            completed=False,
        ))
        bookmarks_created += 1
    elif len(movies) >= 6:
        # Fallback: use adult profile if no kids profile
        session.add(Bookmark(
            profile_id=adult_profile.id,
            content_type="movie",
            content_id=movies[5].id,
            position_seconds=1200,
            duration_seconds=4500,
            completed=False,
        ))
        bookmarks_created += 1

    await session.commit()

    # Post-commit: backdate specific bookmarks for stale/age demo
    from sqlalchemy import text

    if len(movies) >= 2:
        # Bookmark 3: Set updated_at to 2 days ago
        await session.execute(
            text("""
                UPDATE bookmarks SET updated_at = :ts
                WHERE profile_id = :pid AND content_id = :cid
            """).bindparams(
                ts=now - timedelta(days=2),
                pid=adult_profile.id,
                cid=movies[1].id,
            )
        )

    if len(movies) >= 3:
        # Bookmark 4: Set updated_at to 35 days ago (stale)
        await session.execute(
            text("""
                UPDATE bookmarks SET updated_at = :ts
                WHERE profile_id = :pid AND content_id = :cid
            """).bindparams(
                ts=now - timedelta(days=35),
                pid=adult_profile.id,
                cid=movies[2].id,
            )
        )

    await session.commit()

    return {"bookmarks": bookmarks_created}
