"""Parental controls router — PIN management, viewing time config, history, weekly report, grant."""

import uuid
from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.dependencies import DB, AccountOwner, CurrentUser
from app.schemas.parental_controls import (
    GrantExtraTimeRequest,
    GrantExtraTimeResponse,
    PinCreate,
    PinReset,
    PinResponse,
    PinStatusResponse,
    PinVerify,
    PinVerifyResponse,
    ViewingHistoryResponse,
    ViewingTimeConfigResponse,
    ViewingTimeConfigUpdate,
    WeeklyReportResponse,
)
from app.services import pin_service

router = APIRouter()


# ---------------------------------------------------------------------------
# PIN management
# ---------------------------------------------------------------------------


@router.get("/pin/status", response_model=PinStatusResponse)
async def pin_status(user: CurrentUser):
    """H-5: Lightweight check — has a PIN been set? Is it currently locked?"""
    return PinStatusResponse(
        has_pin=user.pin_hash is not None,
        locked_until=user.pin_lockout_until,
    )


@router.post("/pin", response_model=PinResponse)
async def create_or_update_pin(
    body: PinCreate,
    db: DB,
    user: CurrentUser,
):
    """Create or update the account-level parental control PIN."""
    await pin_service.create_pin(
        db, user, new_pin=body.new_pin, current_pin=body.current_pin,
    )
    return PinResponse(detail="PIN set successfully")


@router.post("/pin/verify", response_model=PinVerifyResponse)
async def verify_pin(
    body: PinVerify,
    db: DB,
    user: CurrentUser,
):
    """Verify the parental control PIN.

    Returns ``verified: true`` on success.  On failure, returns
    ``verified: false`` with remaining attempts.  Locks the PIN after
    5 consecutive failures for 30 minutes.
    """
    try:
        ok = await pin_service.verify_pin(db, user, body.pin)
    except HTTPException:
        raise  # re-raise lockout / no-PIN errors

    if not ok:
        # M-09: Don't leak remaining attempt count — generic message only
        raise HTTPException(
            status_code=403,
            detail="Incorrect PIN",
        )

    token = pin_service.generate_pin_token(user.id)
    return PinVerifyResponse(verified=True, pin_token=token)


@router.post("/pin/reset", response_model=PinResponse)
async def reset_pin(
    body: PinReset,
    db: DB,
    user: CurrentUser,
):
    """Reset the parental control PIN by verifying the account password."""
    await pin_service.reset_pin(db, user, password=body.password, new_pin=body.new_pin)
    return PinResponse(detail="PIN reset successfully")


# ---------------------------------------------------------------------------
# Viewing Time Config
# ---------------------------------------------------------------------------


@router.get(
    "/profiles/{profile_id}/viewing-time",
    response_model=ViewingTimeConfigResponse,
)
async def get_viewing_time_config(
    profile_id: uuid.UUID,
    user: AccountOwner,
    db: DB,
):
    """Return the viewing time configuration for a profile.

    Creates a default config if none exists.
    """
    from app.services.viewing_time_service import ensure_default_config

    config = await ensure_default_config(db, profile_id)
    return ViewingTimeConfigResponse.model_validate(config)


@router.put(
    "/profiles/{profile_id}/viewing-time",
    response_model=ViewingTimeConfigResponse,
)
async def update_viewing_time_config(
    profile_id: uuid.UUID,
    body: ViewingTimeConfigUpdate,
    user: AccountOwner,
    db: DB,
):
    """Update viewing time limits for a profile.

    Limits must be in 15-minute increments between 15 and 480.
    """
    from app.services.viewing_time_service import ensure_default_config

    # Validate 15-minute increments
    for field_name in ("weekday_limit_minutes", "weekend_limit_minutes"):
        val = getattr(body, field_name, None)
        if val is not None and val % 15 != 0:
            raise HTTPException(
                status_code=422,
                detail=f"{field_name} must be a multiple of 15 minutes",
            )

    # M-03: Require PIN token when changing sensitive fields
    update_data = body.model_dump(exclude_unset=True)
    update_data.pop("pin_token", None)  # never persist pin_token itself
    changed_sensitive = set(update_data.keys()) & ViewingTimeConfigUpdate.SENSITIVE_FIELDS
    if changed_sensitive:
        if not body.pin_token or not pin_service.verify_pin_token(body.pin_token, user.id):
            raise HTTPException(
                status_code=403,
                detail=f"Valid PIN token required to change: {', '.join(sorted(changed_sensitive))}",
            )

    config = await ensure_default_config(db, profile_id)

    # Apply updates (explicit allowlist — only known config fields)
    ALLOWED_CONFIG_FIELDS = {
        "weekday_limit_minutes", "weekend_limit_minutes",
        "reset_hour", "educational_exempt", "timezone",
    }
    for key, value in update_data.items():
        if key in ALLOWED_CONFIG_FIELDS:
            setattr(config, key, value)

    from datetime import UTC, datetime

    config.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(config)

    # T012: Invalidate config cache so next heartbeat picks up new values
    from app.services.metrics_service import config_cache
    config_cache.invalidate(profile_id)

    return ViewingTimeConfigResponse.model_validate(config)


# ---------------------------------------------------------------------------
# Grant Extra Time
# ---------------------------------------------------------------------------


@router.post(
    "/profiles/{profile_id}/viewing-time/grant",
    response_model=GrantExtraTimeResponse,
)
async def grant_extra_time(
    profile_id: uuid.UUID,
    body: GrantExtraTimeRequest,
    user: AccountOwner,
    db: DB,
):
    """Grant additional viewing time for today.

    On-device grant: supply ``pin`` or ``pin_token`` (from prior verify).
    Remote grant: no ``pin`` needed, just JWT auth + profile ownership.
    """
    has_pin = body.pin is not None
    has_pin_token = body.pin_token is not None
    is_remote = not has_pin and not has_pin_token

    if has_pin:
        ok = await pin_service.verify_pin(db, user, body.pin)
        if not ok:
            # M-09: Don't leak remaining attempt count
            raise HTTPException(
                status_code=403,
                detail="Incorrect PIN",
            )
    elif has_pin_token:
        if not pin_service.verify_pin_token(body.pin_token, user.id):
            raise HTTPException(status_code=403, detail="Invalid or expired PIN token")

    from app.services.viewing_time_service import grant_extra_time as _grant

    remaining_minutes, is_unlimited = await _grant(
        db,
        profile_id=profile_id,
        user_id=user.id,
        minutes=body.minutes,
        is_remote=is_remote,
    )

    return GrantExtraTimeResponse(
        granted_minutes=body.minutes,
        remaining_minutes=remaining_minutes,
        is_unlimited_override=is_unlimited,
    )


# ---------------------------------------------------------------------------
# Viewing History
# ---------------------------------------------------------------------------


@router.get(
    "/profiles/{profile_id}/history",
    response_model=ViewingHistoryResponse,
)
async def get_viewing_history(
    profile_id: uuid.UUID,
    user: AccountOwner,
    db: DB,
    from_date: date = Query(..., description="Start date (inclusive) YYYY-MM-DD"),
    to_date: date = Query(..., description="End date (inclusive) YYYY-MM-DD"),
):
    """Return viewing session history for a profile within a date range."""
    # H-3: Cap date range to 90 days to prevent expensive queries
    if (to_date - from_date).days > 90:
        raise HTTPException(status_code=422, detail="Date range must not exceed 90 days")
    if from_date > to_date:
        raise HTTPException(status_code=422, detail="from_date must not be after to_date")

    from app.services.viewing_time_service import get_viewing_history as _history

    return await _history(db, profile_id, from_date, to_date)


# ---------------------------------------------------------------------------
# Weekly Report
# ---------------------------------------------------------------------------


@router.get("/weekly-report", response_model=WeeklyReportResponse)
async def weekly_report(
    db: DB,
    user: CurrentUser,
):
    """Return a weekly viewing report for all child profiles owned by this user."""
    from app.services.viewing_time_service import get_weekly_report as _report

    return await _report(db, user.id)
