"""PIN management service — create, verify, reset parental control PINs."""

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
from fastapi import HTTPException
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User
from app.services.auth_service import verify_password

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30
PIN_TOKEN_EXPIRY_MINUTES = 5


def _hash_pin_sync(pin: str) -> str:
    """Hash a 4-digit PIN using bcrypt (CPU-bound, synchronous)."""
    return bcrypt.hashpw(pin.encode(), bcrypt.gensalt()).decode()


def _verify_pin_hash_sync(pin: str, hashed: str) -> bool:
    """Check a plain PIN against its bcrypt hash (CPU-bound, synchronous)."""
    return bcrypt.checkpw(pin.encode(), hashed.encode())


async def _hash_pin(pin: str) -> str:
    """Hash a PIN off the event loop via thread pool."""
    return await asyncio.to_thread(_hash_pin_sync, pin)


async def _verify_pin_hash(pin: str, hashed: str) -> bool:
    """Verify a PIN hash off the event loop via thread pool."""
    return await asyncio.to_thread(_verify_pin_hash_sync, pin, hashed)


async def create_pin(
    db: AsyncSession,
    user: User,
    new_pin: str,
    current_pin: str | None = None,
) -> None:
    """Create or update the account PIN.

    If the user already has a PIN set, ``current_pin`` must be provided and
    verified before the new PIN is accepted.
    """
    if user.pin_hash is not None:
        if current_pin is None:
            raise HTTPException(
                status_code=400,
                detail="Current PIN required to change existing PIN",
            )
        if not await _verify_pin_hash(current_pin, user.pin_hash):
            raise HTTPException(status_code=400, detail="Current PIN is incorrect")

    user.pin_hash = await _hash_pin(new_pin)
    user.pin_failed_attempts = 0
    user.pin_lockout_until = None
    await db.commit()


async def verify_pin(db: AsyncSession, user: User, pin: str) -> bool:
    """Verify a PIN with lockout protection.

    Returns ``True`` on success, ``False`` on mismatch.
    Raises 403 if the account is currently locked out.
    Raises 400 if no PIN has been set.

    M-04: Uses a constant-time delay to prevent timing oracle attacks.
    """
    # Check lockout
    if user.pin_lockout_until is not None and user.pin_lockout_until > datetime.now(UTC):
        raise HTTPException(
            status_code=403,
            detail="PIN locked due to too many failed attempts",
            headers={"X-Locked-Until": user.pin_lockout_until.isoformat()},
        )

    if user.pin_hash is None:
        raise HTTPException(status_code=400, detail="No PIN set")

    # M-04: Normalize response time so success and failure are indistinguishable
    start = asyncio.get_event_loop().time()
    matched = await _verify_pin_hash(pin, user.pin_hash)

    if matched:
        user.pin_failed_attempts = 0
        user.pin_lockout_until = None
        await db.commit()
    else:
        user.pin_failed_attempts += 1
        if user.pin_failed_attempts >= MAX_FAILED_ATTEMPTS:
            user.pin_lockout_until = datetime.now(UTC) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
        await db.commit()

    # Pad to a minimum of 200ms to mask bcrypt timing differences
    elapsed = asyncio.get_event_loop().time() - start
    pad = max(0, 0.2 - elapsed)
    if pad > 0:
        await asyncio.sleep(pad)

    return matched


async def reset_pin(
    db: AsyncSession,
    user: User,
    password: str,
    new_pin: str,
) -> None:
    """Reset the PIN by verifying the account password.

    This bypasses PIN lockout so the user can regain access.
    """
    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect account password")

    user.pin_hash = await _hash_pin(new_pin)
    user.pin_failed_attempts = 0
    user.pin_lockout_until = None
    await db.commit()


# ---------------------------------------------------------------------------
# PIN token (C-02 security fix) — short-lived proof of PIN verification
# ---------------------------------------------------------------------------


def generate_pin_token(user_id: uuid.UUID) -> str:
    """Create a short-lived JWT proving the parental PIN was recently verified."""
    payload = {
        "sub": str(user_id),
        "purpose": "pin_verified",
        "jti": str(uuid.uuid4()),
        "exp": datetime.now(UTC) + timedelta(minutes=PIN_TOKEN_EXPIRY_MINUTES),
    }
    return jwt.encode(payload, settings.jwt_secret.get_secret_value(), algorithm=settings.jwt_algorithm)


def verify_pin_token(token: str, user_id: uuid.UUID) -> bool:
    """Validate a pin_token and confirm it belongs to *user_id*."""
    try:
        payload = jwt.decode(token, settings.jwt_secret.get_secret_value(), algorithms=[settings.jwt_algorithm])
        return (
            payload.get("purpose") == "pin_verified"
            and payload.get("sub") == str(user_id)
        )
    except JWTError:
        return False
