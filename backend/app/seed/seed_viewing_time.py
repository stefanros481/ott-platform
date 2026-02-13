"""Seed data for viewing time — child profile config, sessions, balance, grants, educational titles, PIN.

Creates:
- Account PIN for the premium@ott.test demo user
- Marks 5-10 titles as is_educational=True
- ViewingTimeConfig for a child profile
- Pre-populated ViewingSession history (7 days)
- ViewingTimeBalance rows for recent days
- A TimeGrant audit record

Must run AFTER seed_users and seed_catalog.
Idempotent: skips if ViewingTimeConfig rows already exist.
"""

from datetime import datetime, timedelta, timezone

import bcrypt
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import Title
from app.models.user import Profile, User
from app.models.viewing_time import (
    TimeGrant,
    ViewingSession,
    ViewingTimeBalance,
    ViewingTimeConfig,
)


async def seed_viewing_time(session: AsyncSession) -> dict[str, int]:
    """Seed viewing time demo data. Returns counts of created entities."""
    # Idempotency check
    existing = await session.execute(select(ViewingTimeConfig).limit(1))
    if existing.scalar_one_or_none() is not None:
        print("  [seed_viewing_time] Viewing time data already seeded, skipping.")
        return {"viewing_time_configs": 0}

    now = datetime.now(timezone.utc)

    # ---------------------------------------------------------------
    # 1. Find the premium user with a kids profile
    # ---------------------------------------------------------------
    user_result = await session.execute(
        select(User).where(User.email == "premium@ott.test")
    )
    user = user_result.scalar_one_or_none()
    if user is None:
        print("  [seed_viewing_time] premium@ott.test not found — skipping.")
        return {"viewing_time_configs": 0}

    profiles_result = await session.execute(
        select(Profile).where(Profile.user_id == user.id)
    )
    profiles = profiles_result.scalars().all()
    kids_profile = next((p for p in profiles if p.is_kids), None)
    if kids_profile is None:
        print("  [seed_viewing_time] No kids profile found for premium user — skipping.")
        return {"viewing_time_configs": 0}

    # ---------------------------------------------------------------
    # 2. Set account PIN (1234)
    # ---------------------------------------------------------------
    pin_hash = bcrypt.hashpw(b"1234", bcrypt.gensalt()).decode()
    user.pin_hash = pin_hash
    user.pin_failed_attempts = 0
    user.pin_lockout_until = None
    print(f"  [seed_viewing_time] Set PIN for {user.email}")

    # ---------------------------------------------------------------
    # 3. Mark some titles as educational
    # ---------------------------------------------------------------
    titles_result = await session.execute(
        select(Title).order_by(Title.title).limit(50)
    )
    all_titles = titles_result.scalars().all()

    # Pick every 5th title (up to 10) as educational
    educational_titles = all_titles[::5][:10]
    educational_ids = [t.id for t in educational_titles]

    if educational_ids:
        await session.execute(
            update(Title)
            .where(Title.id.in_(educational_ids))
            .values(is_educational=True)
        )
        print(f"  [seed_viewing_time] Marked {len(educational_ids)} titles as educational.")

    # ---------------------------------------------------------------
    # 4. Create ViewingTimeConfig for kids profile
    # ---------------------------------------------------------------
    config = ViewingTimeConfig(
        profile_id=kids_profile.id,
        weekday_limit_minutes=120,   # 2 hours on weekdays
        weekend_limit_minutes=180,   # 3 hours on weekends
        reset_hour=6,
        educational_exempt=True,
        timezone="UTC",
    )
    session.add(config)
    print(f"  [seed_viewing_time] Created viewing time config for '{kids_profile.name}'.")

    # ---------------------------------------------------------------
    # 5. Create 7 days of viewing history
    # ---------------------------------------------------------------
    sessions_created = 0
    balances_created = 0

    # Pick content titles for sessions (some educational, some not)
    regular_titles = [t for t in all_titles if t.id not in educational_ids][:5]
    edu_titles_for_sessions = educational_titles[:3]

    for days_ago in range(7):
        day = (now - timedelta(days=days_ago)).date()
        day_start = datetime(day.year, day.month, day.day, 9, 0, 0, tzinfo=timezone.utc)

        used_seconds = 0
        educational_seconds = 0

        # 2-3 sessions per day
        session_count = 2 if days_ago % 2 == 0 else 3

        for s_idx in range(session_count):
            # Alternate between regular and educational titles
            if s_idx == 0 and edu_titles_for_sessions:
                title = edu_titles_for_sessions[days_ago % len(edu_titles_for_sessions)]
                is_edu = True
            elif regular_titles:
                title = regular_titles[(days_ago + s_idx) % len(regular_titles)]
                is_edu = False
            else:
                continue

            session_start = day_start + timedelta(hours=s_idx * 2)
            duration = 20 + (s_idx * 10) + (days_ago * 3)  # 20-50 min range
            duration_seconds = duration * 60

            vs = ViewingSession(
                profile_id=kids_profile.id,
                title_id=title.id,
                device_id="seed-device-tv",
                device_type="tv",
                is_educational=is_edu,
                started_at=session_start,
                last_heartbeat_at=session_start + timedelta(seconds=duration_seconds),
                ended_at=session_start + timedelta(seconds=duration_seconds),
                total_seconds=duration_seconds,
            )
            session.add(vs)
            sessions_created += 1

            if is_edu:
                educational_seconds += duration_seconds
            else:
                used_seconds += duration_seconds

        # Create balance row for each day
        balance = ViewingTimeBalance(
            profile_id=kids_profile.id,
            reset_date=day,
            used_seconds=used_seconds,
            educational_seconds=educational_seconds,
            is_unlimited_override=False,
        )
        session.add(balance)
        balances_created += 1

    print(f"  [seed_viewing_time] Created {sessions_created} viewing sessions.")
    print(f"  [seed_viewing_time] Created {balances_created} balance records.")

    # ---------------------------------------------------------------
    # 6. Create a TimeGrant record (parent granted 30 min yesterday)
    # ---------------------------------------------------------------
    grant = TimeGrant(
        profile_id=kids_profile.id,
        granted_by_user_id=user.id,
        granted_minutes=30,
        is_remote=False,
        granted_at=now - timedelta(days=1, hours=3),
    )
    session.add(grant)
    print("  [seed_viewing_time] Created 1 time grant record.")

    await session.commit()

    return {
        "viewing_time_configs": 1,
        "viewing_sessions": sessions_created,
        "viewing_time_balances": balances_created,
        "time_grants": 1,
        "educational_titles": len(educational_ids),
        "pin_set": 1,
    }
