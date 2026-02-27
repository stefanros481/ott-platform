"""Seed TSTV data: assign cdn_channel_key to channels, enable TSTV flags, insert DRM keys."""

import os
import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.epg import Channel
from app.models.tstv import DRMKey

# CDN base URL for SimLive HLS playlists (served by the cdn-nginx container)
CDN_BASE_URL = os.environ.get("CDN_BASE_URL", "http://localhost:8081")

# Map first 5 channels (by channel_number) to CDN keys
TSTV_CHANNEL_CONFIG = [
    {"channel_number": 1, "cdn_key": "ch1", "cutv_window_hours": 168},
    {"channel_number": 2, "cdn_key": "ch2", "cutv_window_hours": 168},
    {"channel_number": 3, "cdn_key": "ch3", "cutv_window_hours": 168},
    {"channel_number": 9, "cdn_key": "ch4", "cutv_window_hours": 48},  # sports — shorter window
    {"channel_number": 13, "cdn_key": "ch5", "cutv_window_hours": 168},
]

# Static test DRM keys (deterministic for dev/test reproducibility)
_STATIC_TEST_KEYS = {
    "ch1": (uuid.UUID("00000000-0000-0000-0000-000000000001"), bytes.fromhex("00112233445566778899aabbccddeeff")),
    "ch2": (uuid.UUID("00000000-0000-0000-0000-000000000002"), bytes.fromhex("112233445566778899aabbccddeeff00")),
    "ch3": (uuid.UUID("00000000-0000-0000-0000-000000000003"), bytes.fromhex("2233445566778899aabbccddeeff0011")),
    "ch4": (uuid.UUID("00000000-0000-0000-0000-000000000004"), bytes.fromhex("33445566778899aabbccddeeff001122")),
    "ch5": (uuid.UUID("00000000-0000-0000-0000-000000000005"), bytes.fromhex("445566778899aabbccddeeff00112233")),
}


async def seed_tstv(session: AsyncSession) -> dict[str, int]:
    """Assign TSTV config to channels and insert static DRM keys.

    Idempotent: skips if cdn_channel_key is already set on any channel.
    """
    # Check if already seeded
    result = await session.execute(
        select(Channel).where(Channel.cdn_channel_key.isnot(None)).limit(1)
    )
    if result.scalar_one_or_none() is not None:
        print("  [seed_tstv] TSTV data already seeded, skipping.")
        return {"tstv_channels": 0, "drm_keys": 0}

    channels_updated = 0
    keys_created = 0

    for cfg in TSTV_CHANNEL_CONFIG:
        # Find channel by channel_number
        result = await session.execute(
            select(Channel).where(Channel.channel_number == cfg["channel_number"])
        )
        channel = result.scalar_one_or_none()
        if channel is None:
            print(f"  [seed_tstv] Warning: channel_number={cfg['channel_number']} not found, skipping.")
            continue

        # Update TSTV fields
        await session.execute(
            update(Channel)
            .where(Channel.id == channel.id)
            .values(
                cdn_channel_key=cfg["cdn_key"],
                tstv_enabled=True,
                startover_enabled=True,
                catchup_enabled=True,
                cutv_window_hours=cfg["cutv_window_hours"],
                catchup_window_hours=168,
                hls_live_url=f"{CDN_BASE_URL}/hls/{cfg['cdn_key']}/live.m3u8",
            )
        )
        channels_updated += 1

        # Insert static DRM key
        kid, key_value = _STATIC_TEST_KEYS[cfg["cdn_key"]]
        result = await session.execute(
            select(DRMKey).where(DRMKey.key_id == kid)
        )
        if result.scalar_one_or_none() is None:
            session.add(DRMKey(
                key_id=kid,
                key_value=key_value,
                channel_id=channel.id,
                active=True,
            ))
            keys_created += 1

    await session.flush()
    await session.commit()

    print(f"  [seed_tstv] Updated {channels_updated} channels with TSTV config.")
    print(f"  [seed_tstv] Created {keys_created} static DRM keys.")

    return {"tstv_channels": channels_updated, "drm_keys": keys_created}
