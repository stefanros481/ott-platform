"""Authentication service — password hashing, JWT management, user operations."""

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.user import Profile, RefreshToken, User


# ── Password helpers ─────────────────────────────────────────────────────────


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against its bcrypt hash."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ── JWT helpers ──────────────────────────────────────────────────────────────


def create_access_token(user_id: uuid.UUID, is_admin: bool) -> str:
    """Create a short-lived JWT access token."""
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "is_admin": is_admin,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expiry_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _hash_token(raw_token: str) -> str:
    """SHA-256 hash a raw refresh token for safe DB storage."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


def create_refresh_token(user_id: uuid.UUID) -> tuple[str, str]:
    """Generate a random refresh token.

    Returns:
        (raw_token, token_hash) -- send raw_token to the client, store token_hash in DB.
    """
    raw_token = secrets.token_urlsafe(48)
    token_hash = _hash_token(raw_token)
    return raw_token, token_hash


def verify_refresh_token(raw_token: str, stored_hash: str) -> bool:
    """Verify a client-provided refresh token against the stored hash."""
    return _hash_token(raw_token) == stored_hash


# ── User operations ──────────────────────────────────────────────────────────


async def register_user(db: AsyncSession, email: str, password: str) -> User:
    """Create a new user with a default profile.

    Raises:
        ValueError: If the email is already registered.
    """
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise ValueError("Email already registered")

    user = User(
        email=email,
        password_hash=hash_password(password),
    )
    db.add(user)
    await db.flush()  # populate user.id before creating profile

    profile = Profile(
        user_id=user.id,
        name="Default",
    )
    db.add(profile)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    """Validate credentials and return the user, or None if invalid."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        return None
    if not user.is_active:
        return None
    return user


async def refresh_access_token(
    db: AsyncSession,
    refresh_token_str: str,
) -> tuple[str, str]:
    """Rotate a refresh token and return a new (access_token, refresh_token) pair.

    Raises:
        ValueError: If the refresh token is invalid or expired.
    """
    token_hash = _hash_token(refresh_token_str)
    result = await db.execute(
        select(RefreshToken)
        .options(selectinload(RefreshToken.user))
        .where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > datetime.now(UTC),
        )
    )
    stored = result.scalar_one_or_none()
    if not stored:
        raise ValueError("Invalid or expired refresh token")

    user = stored.user

    # Revoke old token
    stored.revoked_at = datetime.now(UTC)

    # Issue new refresh token
    new_raw, new_hash = create_refresh_token(user.id)
    new_rt = RefreshToken(
        user_id=user.id,
        token_hash=new_hash,
        expires_at=datetime.now(UTC) + timedelta(days=settings.jwt_refresh_expiry_days),
    )
    db.add(new_rt)
    await db.commit()

    access_token = create_access_token(user.id, user.is_admin)
    return access_token, new_raw


async def store_refresh_token(db: AsyncSession, user_id: uuid.UUID, token_hash: str) -> None:
    """Persist a hashed refresh token in the database."""
    rt = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=datetime.now(UTC) + timedelta(days=settings.jwt_refresh_expiry_days),
    )
    db.add(rt)
    await db.commit()
