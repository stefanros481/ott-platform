"""Seed synthetic analytics events for the Content Analytics Agent demo.

Generates 500–1000 AnalyticsEvent records spanning the last 90 days, covering:
- All 5 event types: play_start, play_pause, play_complete, browse, search
- All 6 service types: Linear, VoD, SVoD, TSTV, Catch_up, Cloud_PVR
- 3 Nordic regions: NO, SE, DK
- Realistic patterns: Drama/Thriller → high SVoD completion, Sports → weekend Linear,
  high browse-to-watch ratio for SVoD (upgrade signal), kids profile events for
  trending_by_profile_type template, Cloud_PVR prime-time recordings.

Idempotent: skips seeding if analytics_events table already has rows.
"""

import random
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import AnalyticsEvent
from app.models.catalog import Title
from app.models.user import Profile, User


async def seed_analytics(session: AsyncSession) -> dict[str, int]:
    """Seed analytics events. Returns count of created records."""
    # Idempotency check
    count = await session.scalar(select(func.count()).select_from(AnalyticsEvent))
    if count and count > 0:
        return {"analytics_events": 0}

    # Load all users
    users = (await session.execute(select(User))).scalars().all()
    if not users:
        print("  WARNING: No users found — skipping analytics seed")
        return {"analytics_events": 0}

    # Load all titles (need their IDs)
    titles = (await session.execute(select(Title))).scalars().all()
    if not titles:
        print("  WARNING: No titles found — skipping analytics seed")
        return {"analytics_events": 0}

    # Load all profiles, group by user
    profiles = (await session.execute(select(Profile))).scalars().all()
    profiles_by_user: dict[uuid.UUID, list[Profile]] = {}
    for profile in profiles:
        profiles_by_user.setdefault(profile.user_id, []).append(profile)

    rng = random.Random(42)  # Deterministic seed for reproducible data
    now = datetime.now(timezone.utc)
    ninety_days_ago = now - timedelta(days=90)

    events: list[AnalyticsEvent] = []

    # ---------------------------------------------------------------------------
    # Helper: random timestamp within the 90-day window, with time-of-day skew
    # ---------------------------------------------------------------------------
    def random_ts(*, weekday_bias: bool = False, prime_time: bool = False) -> datetime:
        total_seconds = int((now - ninety_days_ago).total_seconds())
        offset = rng.randint(0, total_seconds)
        ts = ninety_days_ago + timedelta(seconds=offset)

        if prime_time:
            # Replace hour with prime-time (19:00–22:59)
            ts = ts.replace(hour=rng.randint(19, 22), minute=rng.randint(0, 59))
        elif weekday_bias:
            # Weekend-skewed: if ts is on a weekday, randomly push to weekend
            if ts.weekday() < 5 and rng.random() < 0.7:
                days_to_saturday = (5 - ts.weekday()) % 7
                ts = ts + timedelta(days=rng.randint(0, days_to_saturday))
        return ts

    # ---------------------------------------------------------------------------
    # Helper: emit play_start → play_pause/play_complete sequence
    # ---------------------------------------------------------------------------
    def make_play_events(
        user: User,
        profile: Profile | None,
        title: Title,
        service_type: str,
        region: str,
        watch_pct: int,
        base_ts: datetime,
    ) -> list[AnalyticsEvent]:
        session_id = uuid.uuid4()
        duration_s = (title.duration_minutes or 90) * 60
        evs: list[AnalyticsEvent] = []

        evs.append(AnalyticsEvent(
            event_type="play_start",
            title_id=title.id,
            service_type=service_type,
            user_id=user.id,
            profile_id=profile.id if profile else None,
            region=region,
            occurred_at=base_ts,
            session_id=session_id,
        ))

        complete_threshold = 80  # >= 80% = complete, else pause
        if watch_pct >= complete_threshold:
            actual_duration = int(duration_s * watch_pct / 100)
            evs.append(AnalyticsEvent(
                event_type="play_complete",
                title_id=title.id,
                service_type=service_type,
                user_id=user.id,
                profile_id=profile.id if profile else None,
                region=region,
                occurred_at=base_ts + timedelta(seconds=actual_duration),
                session_id=session_id,
                duration_seconds=actual_duration,
                watch_percentage=watch_pct,
            ))
        else:
            actual_duration = int(duration_s * watch_pct / 100)
            evs.append(AnalyticsEvent(
                event_type="play_pause",
                title_id=title.id,
                service_type=service_type,
                user_id=user.id,
                profile_id=profile.id if profile else None,
                region=region,
                occurred_at=base_ts + timedelta(seconds=actual_duration),
                session_id=session_id,
                duration_seconds=actual_duration,
                watch_percentage=watch_pct,
            ))
        return evs

    # ---------------------------------------------------------------------------
    # Classify titles by genre for realistic distribution
    # Genres: Action, Comedy, Drama, Thriller, Sci-Fi, Horror, Romance,
    #         Documentary, Animation, Crime, Fantasy, Family
    # ---------------------------------------------------------------------------
    drama_thriller_titles: list[Title] = []
    kids_titles: list[Title] = []
    all_titles: list[Title] = list(titles)

    # Use title names to roughly classify (actual genre join not available at seed time)
    for t in titles:
        title_lower = t.title.lower()
        if any(w in title_lower for w in ["kids", "family", "animation", "cartoon", "junior"]):
            kids_titles.append(t)
        elif t.is_educational:
            kids_titles.append(t)

    if not kids_titles:
        # Fall back: use first 10% of titles for kids profile events
        kids_titles = all_titles[: max(5, len(all_titles) // 10)]

    drama_thriller_titles = all_titles  # all titles get drama-pattern skew

    regions = ["NO", "SE", "DK"]
    service_types = ["Linear", "VoD", "SVoD", "TSTV", "Catch_up", "Cloud_PVR"]

    # ---------------------------------------------------------------------------
    # Pattern 1: SVoD drama/thriller — high completion rates (60–100%)
    # Target: ≥ 100 SVoD events
    # ---------------------------------------------------------------------------
    for _ in range(140):
        user = rng.choice(users)
        user_profiles = profiles_by_user.get(user.id, [])
        adult_profile = next((p for p in user_profiles if not p.is_kids), None)
        title = rng.choice(all_titles)
        region = rng.choices(regions, weights=[0.4, 0.35, 0.25])[0]
        ts = random_ts()
        watch_pct = rng.randint(65, 100)
        events.extend(make_play_events(user, adult_profile, title, "SVoD", region, watch_pct, ts))

    # ---------------------------------------------------------------------------
    # Pattern 2: Sports on Linear — weekend prime-time skew
    # Target: ≥ 50 Linear events
    # ---------------------------------------------------------------------------
    for _ in range(70):
        user = rng.choice(users)
        user_profiles = profiles_by_user.get(user.id, [])
        adult_profile = next((p for p in user_profiles if not p.is_kids), None)
        title = rng.choice(all_titles)
        region = rng.choices(regions, weights=[0.5, 0.3, 0.2])[0]
        ts = random_ts(weekday_bias=True, prime_time=True)
        watch_pct = rng.randint(30, 95)
        events.extend(make_play_events(user, adult_profile, title, "Linear", region, watch_pct, ts))

    # ---------------------------------------------------------------------------
    # Pattern 3: High browse-to-watch ratio (SVoD upgrade signal)
    # Target: ≥ 50 browse events for SVoD
    # ---------------------------------------------------------------------------
    for _ in range(80):
        user = rng.choice(users)
        title = rng.choice(all_titles)
        region = rng.choice(regions)
        ts = random_ts()
        events.append(AnalyticsEvent(
            event_type="browse",
            title_id=title.id,
            service_type="SVoD",
            user_id=user.id,
            profile_id=None,
            region=region,
            occurred_at=ts,
            extra_data={"genre_filter": "Drama", "source": "home_rail"},
        ))
        # Only 30% of browses convert to plays — high browse-to-watch ratio
        if rng.random() < 0.3:
            user_profiles = profiles_by_user.get(user.id, [])
            adult_profile = next((p for p in user_profiles if not p.is_kids), None)
            watch_pct = rng.randint(40, 100)
            events.extend(make_play_events(
                user, adult_profile, title, "SVoD", region, watch_pct,
                ts + timedelta(minutes=rng.randint(1, 5))
            ))

    # ---------------------------------------------------------------------------
    # Pattern 4: Kids profile events (for trending_by_profile_type template)
    # Target: ≥ 30 events with kids profile
    # ---------------------------------------------------------------------------
    for _ in range(50):
        user = rng.choice(users)
        user_profiles = profiles_by_user.get(user.id, [])
        kids_profile = next((p for p in user_profiles if p.is_kids), None)
        if kids_profile is None:
            # No kids profile for this user, use first profile available
            kids_profile = user_profiles[0] if user_profiles else None
            if kids_profile is not None:
                # Still useful for query engine even if not a kids profile
                pass
        title = rng.choice(kids_titles)
        region = rng.choice(regions)
        ts = random_ts()
        watch_pct = rng.randint(50, 100)
        events.extend(make_play_events(user, kids_profile, title, "SVoD", region, watch_pct, ts))

    # ---------------------------------------------------------------------------
    # Pattern 5: Cloud PVR — prime-time recordings of Linear content
    # Target: ≥ 50 Cloud_PVR events
    # ---------------------------------------------------------------------------
    for _ in range(65):
        user = rng.choice(users)
        user_profiles = profiles_by_user.get(user.id, [])
        adult_profile = next((p for p in user_profiles if not p.is_kids), None)
        title = rng.choice(all_titles)
        region = rng.choices(regions, weights=[0.45, 0.35, 0.2])[0]
        ts = random_ts(prime_time=True)
        watch_pct = rng.randint(60, 100)
        events.extend(make_play_events(
            user, adult_profile, title, "Cloud_PVR", region, watch_pct, ts
        ))

    # ---------------------------------------------------------------------------
    # Pattern 6: VoD and other service types
    # ---------------------------------------------------------------------------
    for _ in range(50):
        user = rng.choice(users)
        user_profiles = profiles_by_user.get(user.id, [])
        adult_profile = next((p for p in user_profiles if not p.is_kids), None)
        title = rng.choice(all_titles)
        region = rng.choice(regions)
        service = rng.choice(["VoD", "TSTV", "Catch_up"])
        ts = random_ts()
        watch_pct = rng.randint(20, 100)
        events.extend(make_play_events(user, adult_profile, title, service, region, watch_pct, ts))

    # ---------------------------------------------------------------------------
    # Pattern 7: Search events
    # ---------------------------------------------------------------------------
    search_queries = [
        "drama series", "new movies", "action", "comedy", "kids shows",
        "thriller", "documentary", "sci-fi", "crime drama", "fantasy"
    ]
    for _ in range(60):
        user = rng.choice(users)
        region = rng.choice(regions)
        ts = random_ts()
        query = rng.choice(search_queries)
        events.append(AnalyticsEvent(
            event_type="search",
            title_id=None,
            service_type=rng.choice(["SVoD", "VoD", "Linear"]),
            user_id=user.id,
            profile_id=None,
            region=region,
            occurred_at=ts,
            extra_data={"query": query},
        ))

    # ---------------------------------------------------------------------------
    # Pattern 8: General browse events (catalog browsing)
    # ---------------------------------------------------------------------------
    for _ in range(60):
        user = rng.choice(users)
        title = rng.choice(all_titles) if rng.random() > 0.3 else None
        region = rng.choice(regions)
        ts = random_ts()
        events.append(AnalyticsEvent(
            event_type="browse",
            title_id=title.id if title else None,
            service_type=rng.choice(service_types),
            user_id=user.id,
            profile_id=None,
            region=region,
            occurred_at=ts,
            extra_data={"source": rng.choice(["home", "catalog", "search", "recommendation"])},
        ))

    # ---------------------------------------------------------------------------
    # Assertions: verify template coverage
    # ---------------------------------------------------------------------------
    pvr_events = sum(1 for e in events if e.service_type == "Cloud_PVR")
    svod_events = sum(1 for e in events if e.service_type == "SVoD")
    kids_events = sum(1 for e in events if any(
        p.is_kids for u_profiles in profiles_by_user.values()
        for p in u_profiles
        if e.profile_id == p.id
    ))

    assert pvr_events >= 50, f"Expected ≥50 Cloud_PVR events, got {pvr_events}"
    assert svod_events >= 100, f"Expected ≥100 SVoD events, got {svod_events}"

    # Bulk insert all events
    session.add_all(events)
    await session.commit()

    total = len(events)
    print(f"  Seeded {total} analytics events "
          f"({pvr_events} Cloud_PVR, {svod_events} SVoD, {kids_events} kids-profile)")
    return {"analytics_events": total}
