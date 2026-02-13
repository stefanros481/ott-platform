"""Viewing time router — heartbeat, balance, session management, playback eligibility."""

import logging
import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import and_, select

from app.dependencies import DB, AccountOwner, CurrentUser
from app.models.user import Profile
from app.schemas.viewing_time import (
    EnforcementStatus,
    HeartbeatRequest,
    HeartbeatResponse,
    PlaybackEligibilityResponse,
    SessionEndResponse,
    ViewingTimeBalanceResponse,
)
from app.services import viewing_time_service

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Balance
# ---------------------------------------------------------------------------


@router.get("/balance/{profile_id}", response_model=ViewingTimeBalanceResponse)
async def get_balance(
    profile_id: uuid.UUID,
    db: DB,
    user: AccountOwner,
):
    """Return the current viewing time balance for a profile."""
    return await viewing_time_service.get_balance(db, profile_id)


# ---------------------------------------------------------------------------
# Heartbeat
# ---------------------------------------------------------------------------


@router.post("/heartbeat", response_model=HeartbeatResponse)
async def heartbeat(
    body: HeartbeatRequest,
    db: DB,
    user: CurrentUser,
):
    """Process a 30-second player heartbeat.

    Fail-closed: if an unexpected error occurs, returns ``blocked`` status
    so the client stops playback rather than allowing untracked viewing.
    """
    # H-1: Verify profile belongs to authenticated user (IDOR prevention)
    result = await db.execute(
        select(Profile.id).where(
            and_(Profile.id == body.profile_id, Profile.user_id == user.id)
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=403, detail="Profile not found or access denied")

    try:
        return await viewing_time_service.process_heartbeat(
            db,
            profile_id=body.profile_id,
            title_id=body.title_id,
            device_id=body.device_id,
            device_type=body.device_type.value,
            session_id=body.session_id,
            is_paused=body.is_paused,
        )
    except HTTPException:
        raise  # pass through known HTTP errors (404, etc.)
    except Exception:
        logger.exception("Heartbeat processing failed — returning blocked (fail-closed)")
        return HeartbeatResponse(
            session_id=body.session_id or uuid.uuid4(),
            enforcement=EnforcementStatus.blocked,
            remaining_minutes=0,
            used_minutes=0,
            is_educational=False,
        )


# ---------------------------------------------------------------------------
# Session End
# ---------------------------------------------------------------------------


@router.post("/session/{session_id}/end", response_model=SessionEndResponse)
async def end_session(
    session_id: uuid.UUID,
    db: DB,
    user: CurrentUser,
):
    """End a viewing session (H-2: ownership verified in service layer)."""
    return await viewing_time_service.end_session(db, session_id, user.id)


# ---------------------------------------------------------------------------
# Playback Eligibility
# ---------------------------------------------------------------------------


@router.get(
    "/playback-eligible/{profile_id}",
    response_model=PlaybackEligibilityResponse,
)
async def playback_eligible(
    profile_id: uuid.UUID,
    db: DB,
    user: AccountOwner,
):
    """Pre-flight check: is this profile allowed to start playback?"""
    return await viewing_time_service.check_playback_eligible(db, profile_id)
