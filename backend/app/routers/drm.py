"""DRM router — ClearKey key provisioning and license delivery."""

import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from sqlalchemy import and_, select

from app.dependencies import AdminUser, CurrentUser, DB
from app.models.tstv import DRMKey
from app.schemas.tstv import ClearKeyLicenseRequest, DRMKeyResponse
from app.services import drm_service

router = APIRouter()


@router.get("/keys/channel/{channel_key}", response_model=DRMKeyResponse)
async def get_channel_key(
    channel_key: str,
    db: DB,
    admin: AdminUser,
):
    """Fetch or generate the active AES-128 key for a channel (admin only)."""
    try:
        key = await drm_service.get_or_create_active_key(db, channel_key)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Channel key {channel_key!r} not found")
    await db.commit()
    return DRMKeyResponse(
        key_id=key.key_id,
        key_value_hex=key.key_value.hex(),
        channel_key=channel_key,
        active=key.active,
    )


@router.post("/license")
async def clearkey_license(
    body: ClearKeyLicenseRequest,
    db: DB,
    user: CurrentUser,
):
    """ClearKey license endpoint — returns AES-128 keys for requested KIDs.

    Validates the Bearer JWT (via CurrentUser dependency). For each requested
    key ID, looks up the key in the database and returns the W3C ClearKey
    JSON license response.
    """
    keys = []
    for kid_b64 in body.kids:
        try:
            kid_uuid = drm_service.b64url_to_uuid(kid_b64)
        except (ValueError, Exception):
            raise HTTPException(status_code=400, detail=f"Invalid key ID: {kid_b64}")

        key = await drm_service.resolve_key_by_kid(db, kid_uuid)
        if key is None:
            raise HTTPException(status_code=404, detail=f"Key ID not found: {kid_b64}")
        keys.append(key)

    return drm_service.build_clearkey_license_response(keys)


@router.get("/clearkeys/{channel_id}")
async def get_clearkeys(
    channel_id: uuid.UUID,
    db: DB,
    user: CurrentUser,
):
    """Return ClearKey hex pairs for a channel (for Shaka drm.clearKeys config).

    Returns a map of hex key-id → hex key-value for the active DRM key(s).
    """
    result = await db.execute(
        select(DRMKey).where(
            and_(DRMKey.channel_id == channel_id, DRMKey.active.is_(True))
        )
    )
    key = result.scalar_one_or_none()
    if key is None:
        return {"keys": {}}
    return {"keys": {key.key_id.hex: key.key_value.hex()}}


@router.get("/hls-key/{channel_key}")
async def get_hls_key(
    channel_key: str,
    db: DB,
):
    """Return raw 16-byte AES-128 key for HLS AES-128-CBC decryption.

    Used as the URI in #EXT-X-KEY:METHOD=AES-128. The player fetches this
    endpoint and receives the raw key bytes (not JSON).
    """
    try:
        key = await drm_service.get_or_create_active_key(db, channel_key)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Channel key {channel_key!r} not found")
    return Response(content=key.key_value, media_type="application/octet-stream")
