"""ClearKey DRM service — key generation, lookup, and license helpers."""

import base64
import logging
import os
import uuid

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from app.models.epg import Channel
from app.models.tstv import DRMKey


def _b64url_encode(data: bytes) -> str:
    """Base64url-encode without padding (per W3C ClearKey spec)."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    """Base64url-decode with padding restoration."""
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def uuid_to_b64url(kid: uuid.UUID) -> str:
    """Convert a UUID key ID to base64url (16 bytes, no padding)."""
    return _b64url_encode(kid.bytes)


def b64url_to_uuid(kid_b64: str) -> uuid.UUID:
    """Convert a base64url key ID back to UUID."""
    return uuid.UUID(bytes=_b64url_decode(kid_b64))


async def get_or_create_active_key(
    db: AsyncSession, channel_key: str
) -> DRMKey:
    """Return the active DRM key for a channel, creating one if none exists.

    Looks up the channel by ``cdn_channel_key``, then checks for an active key.
    If no active key is found, generates a new 16-byte AES-128 key with a
    random UUID KID and persists it.
    """
    # Resolve channel by cdn_channel_key
    result = await db.execute(
        select(Channel).where(Channel.cdn_channel_key == channel_key)
    )
    channel = result.scalar_one_or_none()
    if channel is None:
        raise ValueError(f"No channel with cdn_channel_key={channel_key!r}")

    # Look for existing active key
    result = await db.execute(
        select(DRMKey).where(
            and_(DRMKey.channel_id == channel.id, DRMKey.active.is_(True))
        )
    )
    key = result.scalar_one_or_none()
    if key is not None:
        logger.debug("DRM key lookup hit: channel=%s kid=%s", channel_key, key.key_id.hex)
        return key

    # Generate new key
    key = DRMKey(
        key_id=uuid.uuid4(),
        key_value=os.urandom(16),
        channel_id=channel.id,
        active=True,
    )
    db.add(key)
    await db.flush()
    logger.info("Generated new DRM key: channel=%s kid=%s", channel_key, key.key_id.hex)
    return key


async def resolve_key_by_kid(
    db: AsyncSession, kid: uuid.UUID
) -> DRMKey | None:
    """Look up a DRM key by its key ID (KID). Returns None if not found."""
    result = await db.execute(select(DRMKey).where(DRMKey.key_id == kid))
    key = result.scalar_one_or_none()
    if key is None:
        logger.warning("DRM key lookup miss: kid=%s", kid.hex)
    return key


def build_clearkey_license_response(keys: list[DRMKey]) -> dict:
    """Build a W3C ClearKey JSON license response from a list of DRM keys.

    Format:
    {
      "keys": [
        {"kty": "oct", "kid": "<base64url>", "k": "<base64url>"}
      ]
    }
    """
    return {
        "keys": [
            {
                "kty": "oct",
                "kid": uuid_to_b64url(key.key_id),
                "k": _b64url_encode(key.key_value),
            }
            for key in keys
        ]
    }
