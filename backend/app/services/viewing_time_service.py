"""Viewing time service — balance tracking, heartbeat processing, grants, history, reports."""

import uuid
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.catalog import Title
from app.models.user import Profile
from app.models.viewing_time import (
    TimeGrant,
    ViewingSession,
    ViewingTimeBalance,
    ViewingTimeConfig,
)
from app.schemas.parental_controls import (
    ProfileWeeklyStats,
    TopTitle,
    ViewingHistoryDay,
    ViewingHistoryResponse,
    ViewingHistorySession,
    WeeklyReportResponse,
)
from app.schemas.viewing_time import (
    EnforcementStatus,
    HeartbeatResponse,
    PlaybackEligibilityResponse,
    SessionEndResponse,
    ViewingTimeBalanceResponse,
)

# Heartbeat interval in seconds — each heartbeat increments usage by this amount
HEARTBEAT_INTERVAL_SECONDS = 30

# If paused for more than this, we stop counting time
PAUSE_GRACE_SECONDS = 300  # 5 minutes


# ---------------------------------------------------------------------------
# T013 — Default config creation
# ---------------------------------------------------------------------------


async def ensure_default_config(
    db: AsyncSession,
    profile_id: uuid.UUID,
) -> ViewingTimeConfig:
    """Return the :class:`ViewingTimeConfig` for *profile_id*, creating
    sensible defaults if none exists yet.
    """
    result = await db.execute(
        select(ViewingTimeConfig).where(ViewingTimeConfig.profile_id == profile_id)
    )
    config = result.scalar_one_or_none()

    if config is not None:
        return config

    config = ViewingTimeConfig(
        profile_id=profile_id,
        weekday_limit_minutes=120,
        weekend_limit_minutes=180,
        reset_hour=6,
        educational_exempt=True,
        timezone="UTC",
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return config


# ---------------------------------------------------------------------------
# T016 — Core helpers
# ---------------------------------------------------------------------------


def get_viewing_day(now: datetime, reset_hour: int, timezone: str) -> date:
    """Compute the logical viewing day for *now*.

    If the local hour is before *reset_hour*, the viewing day is considered
    to be **yesterday** (the child is still on "yesterday's" allowance).
    """
    tz = ZoneInfo(timezone)
    local_now = now.astimezone(tz)
    if local_now.hour < reset_hour:
        return (local_now - timedelta(days=1)).date()
    return local_now.date()


def _is_weekend(d: date) -> bool:
    """Return ``True`` if *d* falls on Saturday (5) or Sunday (6)."""
    return d.weekday() >= 5


def _compute_next_reset(viewing_day: date, reset_hour: int, timezone: str) -> datetime:
    """Return the next reset moment as a UTC-aware datetime."""
    tz = ZoneInfo(timezone)
    next_day = viewing_day + timedelta(days=1)
    local_reset = datetime(next_day.year, next_day.month, next_day.day, reset_hour, tzinfo=tz)
    return local_reset.astimezone(ZoneInfo("UTC"))


# ---------------------------------------------------------------------------
# T016 — get_balance
# ---------------------------------------------------------------------------


async def get_balance(
    db: AsyncSession,
    profile_id: uuid.UUID,
) -> ViewingTimeBalanceResponse:
    """Return current viewing time balance for *profile_id*."""
    # Fetch profile to check is_kids
    result = await db.execute(select(Profile).where(Profile.id == profile_id))
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    if not profile.is_kids:
        return ViewingTimeBalanceResponse(
            profile_id=profile_id,
            is_child_profile=False,
            has_limits=False,
            used_minutes=0,
            educational_minutes=0,
            limit_minutes=None,
            remaining_minutes=None,
            is_unlimited_override=False,
            next_reset_at=None,
        )

    config = await ensure_default_config(db, profile_id)
    now = datetime.now(UTC)
    viewing_day = get_viewing_day(now, config.reset_hour, config.timezone)

    # Look up balance for today's viewing day
    bal_result = await db.execute(
        select(ViewingTimeBalance).where(
            and_(
                ViewingTimeBalance.profile_id == profile_id,
                ViewingTimeBalance.reset_date == viewing_day,
            )
        )
    )
    balance = bal_result.scalar_one_or_none()

    used_seconds = balance.used_seconds if balance else 0
    educational_seconds = balance.educational_seconds if balance else 0
    is_unlimited = balance.is_unlimited_override if balance else False

    # Determine limit for today
    limit_minutes: int | None
    if _is_weekend(viewing_day):
        limit_minutes = config.weekend_limit_minutes
    else:
        limit_minutes = config.weekday_limit_minutes

    if limit_minutes is None or is_unlimited:
        remaining_minutes = None
    else:
        remaining = (limit_minutes * 60 - used_seconds) / 60.0
        remaining_minutes = max(0.0, remaining)

    next_reset_at = _compute_next_reset(viewing_day, config.reset_hour, config.timezone)

    return ViewingTimeBalanceResponse(
        profile_id=profile_id,
        is_child_profile=True,
        has_limits=limit_minutes is not None and not is_unlimited,
        used_minutes=round(used_seconds / 60.0, 2),
        educational_minutes=round(educational_seconds / 60.0, 2),
        limit_minutes=limit_minutes,
        remaining_minutes=round(remaining_minutes, 2) if remaining_minutes is not None else None,
        is_unlimited_override=is_unlimited,
        next_reset_at=next_reset_at,
    )


# ---------------------------------------------------------------------------
# T016 — process_heartbeat
# ---------------------------------------------------------------------------


async def process_heartbeat(
    db: AsyncSession,
    profile_id: uuid.UUID,
    title_id: uuid.UUID,
    device_id: str,
    device_type: str,
    session_id: uuid.UUID | None,
    is_paused: bool,
) -> HeartbeatResponse:
    """Process a 30-second player heartbeat.

    Creates or updates a :class:`ViewingSession` and increments the daily
    usage balance unless the content is educational-exempt.
    """
    now = datetime.now(UTC)

    # Fetch profile
    result = await db.execute(select(Profile).where(Profile.id == profile_id))
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Fetch config (may be None for non-kids profiles)
    config_result = await db.execute(
        select(ViewingTimeConfig).where(ViewingTimeConfig.profile_id == profile_id)
    )
    config = config_result.scalar_one_or_none()

    # Fetch title to check educational flag
    title_result = await db.execute(select(Title).where(Title.id == title_id))
    title = title_result.scalar_one_or_none()
    if title is None:
        raise HTTPException(status_code=404, detail="Title not found")

    is_educational = title.is_educational

    # ---- Session management ----
    session: ViewingSession

    if session_id is None:
        # New session: terminate any existing active session for this profile
        active_result = await db.execute(
            select(ViewingSession).where(
                and_(
                    ViewingSession.profile_id == profile_id,
                    ViewingSession.ended_at.is_(None),
                )
            )
        )
        for old_session in active_result.scalars().all():
            old_session.ended_at = now

        session = ViewingSession(
            profile_id=profile_id,
            title_id=title_id,
            device_id=device_id,
            device_type=device_type,
            is_educational=is_educational,
            started_at=now,
            last_heartbeat_at=now,
        )
        db.add(session)
        await db.flush()  # populate session.id
    else:
        # Existing session — update heartbeat timestamp
        sess_result = await db.execute(
            select(ViewingSession).where(ViewingSession.id == session_id)
        )
        session = sess_result.scalar_one_or_none()
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        # M-02: Verify session belongs to the requesting profile
        if session.profile_id != profile_id:
            raise HTTPException(status_code=403, detail="Session does not belong to this profile")
        session.last_heartbeat_at = now

    # ---- Pause handling ----
    should_increment = True

    if is_paused:
        if session.paused_at is None:
            session.paused_at = now
        # If paused for longer than grace period, don't count
        elif (now - session.paused_at).total_seconds() > PAUSE_GRACE_SECONDS:
            should_increment = False
    else:
        # Resuming — if was paused more than grace, don't count this beat
        if session.paused_at is not None:
            if (now - session.paused_at).total_seconds() > PAUSE_GRACE_SECONDS:
                should_increment = False
            session.paused_at = None

    # ---- Determine if time counting applies ----
    has_limits = profile.is_kids and config is not None
    educational_exempt = config.educational_exempt if config else True

    # Always increment session total_seconds regardless of limits
    if should_increment:
        session.total_seconds += HEARTBEAT_INTERVAL_SECONDS

    # ---- Balance update (only for kids profiles with config) ----
    viewing_day: date | None = None
    used_seconds = 0
    educational_secs = 0
    limit_minutes: int | None = None
    is_unlimited = False

    if has_limits and config is not None:
        viewing_day = get_viewing_day(now, config.reset_hour, config.timezone)
        limit_minutes = (
            config.weekend_limit_minutes if _is_weekend(viewing_day) else config.weekday_limit_minutes
        )

        if should_increment:
            if is_educational and educational_exempt:
                # Increment educational_seconds only
                stmt = insert(ViewingTimeBalance).values(
                    profile_id=profile_id,
                    reset_date=viewing_day,
                    used_seconds=0,
                    educational_seconds=HEARTBEAT_INTERVAL_SECONDS,
                    is_unlimited_override=False,
                    updated_at=now,
                ).on_conflict_do_update(
                    constraint="uq_vtb_profile_date",
                    set_={
                        "educational_seconds": ViewingTimeBalance.educational_seconds + HEARTBEAT_INTERVAL_SECONDS,
                        "updated_at": now,
                    },
                )
                await db.execute(stmt)
            else:
                # Increment used_seconds (counts against limit)
                stmt = insert(ViewingTimeBalance).values(
                    profile_id=profile_id,
                    reset_date=viewing_day,
                    used_seconds=HEARTBEAT_INTERVAL_SECONDS,
                    educational_seconds=0,
                    is_unlimited_override=False,
                    updated_at=now,
                ).on_conflict_do_update(
                    constraint="uq_vtb_profile_date",
                    set_={
                        "used_seconds": ViewingTimeBalance.used_seconds + HEARTBEAT_INTERVAL_SECONDS,
                        "updated_at": now,
                    },
                )
                await db.execute(stmt)

        # Re-read balance for response
        bal_result = await db.execute(
            select(ViewingTimeBalance).where(
                and_(
                    ViewingTimeBalance.profile_id == profile_id,
                    ViewingTimeBalance.reset_date == viewing_day,
                )
            )
        )
        balance = bal_result.scalar_one_or_none()
        used_seconds = balance.used_seconds if balance else 0
        educational_secs = balance.educational_seconds if balance else 0
        is_unlimited = balance.is_unlimited_override if balance else False

    await db.commit()

    # ---- Compute enforcement status ----
    enforcement = EnforcementStatus.allowed

    if has_limits and limit_minutes is not None and not is_unlimited:
        limit_secs = limit_minutes * 60
        remaining_secs = limit_secs - used_seconds

        if remaining_secs <= 0:
            enforcement = EnforcementStatus.blocked
        elif remaining_secs <= 5 * 60:
            enforcement = EnforcementStatus.warning_5
        elif remaining_secs <= 15 * 60:
            enforcement = EnforcementStatus.warning_15

    # Compute remaining_minutes for response
    remaining_minutes: float | None = None
    if has_limits and limit_minutes is not None and not is_unlimited:
        remaining_minutes = max(0.0, round((limit_minutes * 60 - used_seconds) / 60.0, 2))

    return HeartbeatResponse(
        session_id=session.id,
        enforcement=enforcement,
        remaining_minutes=remaining_minutes,
        used_minutes=round(used_seconds / 60.0, 2),
        is_educational=is_educational,
    )


# ---------------------------------------------------------------------------
# Session end
# ---------------------------------------------------------------------------


async def end_session(
    db: AsyncSession,
    session_id: uuid.UUID,
    user_id: uuid.UUID | None = None,
) -> SessionEndResponse:
    """Mark a viewing session as ended.

    When *user_id* is provided (H-2 security fix), verifies the session
    belongs to a profile owned by that user before ending it.
    """
    result = await db.execute(
        select(ViewingSession).where(ViewingSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # H-2: Verify ownership — session's profile must belong to the caller
    if user_id is not None:
        profile_result = await db.execute(
            select(Profile.id).where(
                and_(Profile.id == session.profile_id, Profile.user_id == user_id)
            )
        )
        if profile_result.scalar_one_or_none() is None:
            raise HTTPException(status_code=403, detail="Session access denied")

    now = datetime.now(UTC)
    session.ended_at = now
    await db.commit()

    return SessionEndResponse(
        session_id=session.id,
        total_seconds=session.total_seconds,
        ended_at=now,
    )


# ---------------------------------------------------------------------------
# Playback eligibility
# ---------------------------------------------------------------------------


async def check_playback_eligible(
    db: AsyncSession,
    profile_id: uuid.UUID,
) -> PlaybackEligibilityResponse:
    """Pre-flight check: can this profile start playback right now?"""
    balance = await get_balance(db, profile_id)

    if not balance.is_child_profile or not balance.has_limits:
        return PlaybackEligibilityResponse(eligible=True)

    if balance.is_unlimited_override:
        return PlaybackEligibilityResponse(eligible=True)

    if balance.remaining_minutes is not None and balance.remaining_minutes <= 0:
        return PlaybackEligibilityResponse(
            eligible=False,
            remaining_minutes=0,
            reason="Daily viewing time limit reached",
            next_reset_at=balance.next_reset_at,
        )

    return PlaybackEligibilityResponse(
        eligible=True,
        remaining_minutes=balance.remaining_minutes,
        next_reset_at=balance.next_reset_at,
    )


# ---------------------------------------------------------------------------
# T023 — Grant extra time
# ---------------------------------------------------------------------------


async def grant_extra_time(
    db: AsyncSession,
    profile_id: uuid.UUID,
    user_id: uuid.UUID,
    minutes: int | None,
    is_remote: bool,
) -> tuple[float | None, bool]:
    """Grant additional viewing time for today.

    Args:
        minutes: Number of minutes to grant.  ``None`` means unlimited for today.
        is_remote: Whether the grant was issued remotely (vs on-device via PIN).

    Returns:
        (remaining_minutes, is_unlimited_override)
    """
    # Fetch config to determine viewing day
    config = await ensure_default_config(db, profile_id)
    now = datetime.now(UTC)
    viewing_day = get_viewing_day(now, config.reset_hour, config.timezone)

    # Ensure a balance row exists for today
    stmt = insert(ViewingTimeBalance).values(
        profile_id=profile_id,
        reset_date=viewing_day,
        used_seconds=0,
        educational_seconds=0,
        is_unlimited_override=False,
        updated_at=now,
    ).on_conflict_do_update(
        constraint="uq_vtb_profile_date",
        set_={"updated_at": now},  # no-op update just to get the row
    )
    await db.execute(stmt)

    # Fetch the balance row
    bal_result = await db.execute(
        select(ViewingTimeBalance).where(
            and_(
                ViewingTimeBalance.profile_id == profile_id,
                ViewingTimeBalance.reset_date == viewing_day,
            )
        )
    )
    balance = bal_result.scalar_one()

    if minutes is None:
        # Unlimited override for today
        balance.is_unlimited_override = True
    else:
        # Reduce used_seconds by minutes*60, floor at 0
        balance.used_seconds = max(0, balance.used_seconds - minutes * 60)

    balance.updated_at = now

    # Create audit record
    grant = TimeGrant(
        profile_id=profile_id,
        granted_by_user_id=user_id,
        granted_minutes=minutes,
        is_remote=is_remote,
        granted_at=now,
    )
    db.add(grant)
    await db.commit()

    # Compute remaining
    is_unlimited = balance.is_unlimited_override
    if is_unlimited:
        return None, True

    limit_minutes = (
        config.weekend_limit_minutes if _is_weekend(viewing_day) else config.weekday_limit_minutes
    )
    if limit_minutes is None:
        return None, False

    remaining = max(0.0, (limit_minutes * 60 - balance.used_seconds) / 60.0)
    return round(remaining, 2), False


# ---------------------------------------------------------------------------
# T032 — Viewing history
# ---------------------------------------------------------------------------


MAX_HISTORY_SESSIONS = 500


async def get_viewing_history(
    db: AsyncSession,
    profile_id: uuid.UUID,
    from_date: date,
    to_date: date,
) -> ViewingHistoryResponse:
    """Return viewing session history grouped by date.

    M-05: Results capped at MAX_HISTORY_SESSIONS to prevent unbounded queries.
    """
    result = await db.execute(
        select(ViewingSession)
        .options(selectinload(ViewingSession.title))
        .where(
            and_(
                ViewingSession.profile_id == profile_id,
                func.date(ViewingSession.started_at) >= from_date,
                func.date(ViewingSession.started_at) <= to_date,
            )
        )
        .order_by(ViewingSession.started_at.desc())
        .limit(MAX_HISTORY_SESSIONS)
    )
    sessions = result.scalars().all()

    # Group by date
    days_map: dict[str, list[ViewingSession]] = defaultdict(list)
    for s in sessions:
        day_str = s.started_at.date().isoformat()
        days_map[day_str].append(s)

    days: list[ViewingHistoryDay] = []
    for day_str in sorted(days_map.keys(), reverse=True):
        day_sessions = days_map[day_str]
        total_minutes = 0.0
        educational_minutes = 0.0
        session_items: list[ViewingHistorySession] = []

        for s in day_sessions:
            duration_min = s.total_seconds / 60.0
            total_minutes += duration_min
            if s.is_educational:
                educational_minutes += duration_min

            session_items.append(ViewingHistorySession(
                session_id=s.id,
                title_id=s.title_id,
                title_name=s.title.title if s.title else "Unknown",
                device_type=s.device_type,
                is_educational=s.is_educational,
                started_at=s.started_at,
                ended_at=s.ended_at,
                duration_minutes=round(duration_min, 2),
            ))

        counted_minutes = total_minutes - educational_minutes

        days.append(ViewingHistoryDay(
            date=day_str,
            total_minutes=round(total_minutes, 2),
            educational_minutes=round(educational_minutes, 2),
            counted_minutes=round(counted_minutes, 2),
            sessions=session_items,
        ))

    return ViewingHistoryResponse(profile_id=profile_id, days=days)


# ---------------------------------------------------------------------------
# T033 — Weekly report
# ---------------------------------------------------------------------------


async def get_weekly_report(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> WeeklyReportResponse:
    """Generate a weekly viewing report for all child profiles owned by *user_id*."""
    now = datetime.now(UTC)
    week_end = now.date()
    week_start = week_end - timedelta(days=6)

    # Fetch all child profiles for user
    result = await db.execute(
        select(Profile).where(
            and_(Profile.user_id == user_id, Profile.is_kids.is_(True))
        )
    )
    child_profiles = result.scalars().all()

    profiles_stats: list[ProfileWeeklyStats] = []

    for profile in child_profiles:
        # Fetch sessions for the week
        sessions_result = await db.execute(
            select(ViewingSession)
            .options(selectinload(ViewingSession.title))
            .where(
                and_(
                    ViewingSession.profile_id == profile.id,
                    func.date(ViewingSession.started_at) >= week_start,
                    func.date(ViewingSession.started_at) <= week_end,
                )
            )
        )
        sessions = sessions_result.scalars().all()

        # Daily totals
        daily_map: dict[str, float] = {}
        title_totals: dict[uuid.UUID, tuple[str, float]] = {}
        total_minutes = 0.0
        educational_minutes = 0.0

        for s in sessions:
            duration_min = s.total_seconds / 60.0
            day_str = s.started_at.date().isoformat()
            daily_map[day_str] = daily_map.get(day_str, 0.0) + duration_min
            total_minutes += duration_min

            if s.is_educational:
                educational_minutes += duration_min

            # Accumulate per-title totals
            t_name = s.title.title if s.title else "Unknown"
            existing = title_totals.get(s.title_id, (t_name, 0.0))
            title_totals[s.title_id] = (t_name, existing[1] + duration_min)

        # Build daily_totals list for every day of the week
        daily_totals: list[dict] = []
        for i in range(7):
            d = week_start + timedelta(days=i)
            d_str = d.isoformat()
            daily_totals.append({
                "date": d_str,
                "minutes": round(daily_map.get(d_str, 0.0), 2),
            })

        average_daily = round(total_minutes / 7, 2)

        # Top 3 titles
        sorted_titles = sorted(title_totals.items(), key=lambda x: x[1][1], reverse=True)[:3]
        top_titles = [
            TopTitle(
                title_id=tid,
                title_name=t_data[0],
                total_minutes=round(t_data[1], 2),
            )
            for tid, t_data in sorted_titles
        ]

        # Compute limit usage percent
        config = await ensure_default_config(db, profile.id)
        total_limit_minutes = 0
        for i in range(7):
            d = week_start + timedelta(days=i)
            if _is_weekend(d):
                total_limit_minutes += config.weekend_limit_minutes or 0
            else:
                total_limit_minutes += config.weekday_limit_minutes or 0

        limit_usage_pct = (
            round(total_minutes / total_limit_minutes * 100, 1)
            if total_limit_minutes > 0
            else None
        )

        profiles_stats.append(ProfileWeeklyStats(
            profile_id=profile.id,
            profile_name=profile.name,
            daily_totals=daily_totals,
            average_daily_minutes=average_daily,
            total_minutes=round(total_minutes, 2),
            educational_minutes=round(educational_minutes, 2),
            limit_usage_percent=limit_usage_pct,
            top_titles=top_titles,
        ))

    return WeeklyReportResponse(
        week_start=week_start.isoformat(),
        week_end=week_end.isoformat(),
        profiles=profiles_stats,
    )
