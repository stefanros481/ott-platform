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
        remaining = pin_service.MAX_FAILED_ATTEMPTS - user.pin_failed_attempts
        raise HTTPException(
            status_code=403,
            detail=f"Incorrect PIN. {remaining} attempt(s) remaining.",
        )

    return PinVerifyResponse(verified=True, pin_token=None)


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

    config = await ensure_default_config(db, profile_id)

    # Apply updates for all fields that were provided
    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)

    from datetime import UTC, datetime

    config.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(config)
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

    On-device grant: supply ``pin`` (verified against account PIN).
    Remote grant: no ``pin`` needed, just JWT auth + profile ownership.
    """
    is_remote = body.pin is None

    if body.pin is not None:
        ok = await pin_service.verify_pin(db, user, body.pin)
        if not ok:
            remaining = pin_service.MAX_FAILED_ATTEMPTS - user.pin_failed_attempts
            raise HTTPException(
                status_code=403,
                detail=f"Incorrect PIN. {remaining} attempt(s) remaining.",
            )

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
