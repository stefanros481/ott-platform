"""PIN management service — create, verify, reset parental control PINs."""

from datetime import UTC, datetime, timedelta

import bcrypt
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.auth_service import verify_password

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30


def _hash_pin(pin: str) -> str:
    """Hash a 4-digit PIN using bcrypt."""
    return bcrypt.hashpw(pin.encode(), bcrypt.gensalt()).decode()


def _verify_pin_hash(pin: str, hashed: str) -> bool:
    """Check a plain PIN against its bcrypt hash."""
    return bcrypt.checkpw(pin.encode(), hashed.encode())


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
        if not _verify_pin_hash(current_pin, user.pin_hash):
            raise HTTPException(status_code=400, detail="Current PIN is incorrect")

    user.pin_hash = _hash_pin(new_pin)
    user.pin_failed_attempts = 0
    user.pin_lockout_until = None
    await db.commit()


async def verify_pin(db: AsyncSession, user: User, pin: str) -> bool:
    """Verify a PIN with lockout protection.

    Returns ``True`` on success, ``False`` on mismatch.
    Raises 403 if the account is currently locked out.
    Raises 400 if no PIN has been set.
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

    if _verify_pin_hash(pin, user.pin_hash):
        # Success — reset counters
        user.pin_failed_attempts = 0
        user.pin_lockout_until = None
        await db.commit()
        return True

    # Failure — increment counter, possibly lock
    user.pin_failed_attempts += 1
    if user.pin_failed_attempts >= MAX_FAILED_ATTEMPTS:
        user.pin_lockout_until = datetime.now(UTC) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
    await db.commit()
    return False


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

    user.pin_hash = _hash_pin(new_pin)
    user.pin_failed_attempts = 0
    user.pin_lockout_until = None
    await db.commit()
