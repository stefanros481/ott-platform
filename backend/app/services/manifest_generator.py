"""HLS manifest generator for TSTV start-over and catch-up playback.

Reads fMP4 segments from disk (written by SimLiveManager), filters by time
range, and builds HLS EVENT or VOD playlists with ClearKey DRM headers.
"""

import logging
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

# Segment filename pattern: {channel_key}-YYYYMMDDHHmmSS.m4s
_SEGMENT_RE = re.compile(r"^(.+)-(\d{14})\.m4s$")


def _parse_segment_time(filename: str) -> datetime | None:
    """Parse timestamp from segment filename like 'ch1-20260225143022.m4s'."""
    m = _SEGMENT_RE.match(filename)
    if not m:
        return None
    ts_str = m.group(2)
    try:
        return datetime.strptime(ts_str, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def list_segments(
    channel_key: str,
    start_dt: datetime,
    end_dt: datetime | None = None,
) -> list[tuple[str, datetime]]:
    """List segments for a channel within a time range.

    Returns a sorted list of (filename, segment_time) tuples.
    If end_dt is None, includes all segments from start_dt onward.
    """
    seg_dir = Path(settings.hls_segment_dir) / channel_key
    if not seg_dir.exists():
        return []

    segments = []
    for f in seg_dir.iterdir():
        if f.suffix != ".m4s":
            continue
        ts = _parse_segment_time(f.name)
        if ts is None:
            continue
        if ts < start_dt:
            continue
        if end_dt is not None and ts > end_dt:
            continue
        segments.append((f.name, ts))

    segments.sort(key=lambda x: x[1])
    return segments


def _build_ext_x_key(key_id_hex: str) -> str:
    """Build #EXT-X-KEY line for ClearKey DRM."""
    return (
        f'#EXT-X-KEY:METHOD=SAMPLE-AES-CTR,'
        f'URI="/api/v1/drm/license",'
        f'KEYFORMAT="urn:uuid:e2719d58-a985-b3c9-781a-b030af78d30e",'
        f'KEYID=0x{key_id_hex}'
    )


def build_event_manifest(
    channel_key: str,
    start_time: datetime,
    key_id_hex: str,
) -> str:
    """Build an HLS EVENT manifest for start-over playback.

    EVENT playlists grow in real-time: segments from program start to now
    are listed, and the playlist does NOT have #EXT-X-ENDLIST (allowing
    the player to poll for new segments as the live broadcast continues).
    """
    t0 = time.monotonic()
    segment_duration = settings.hls_segment_duration
    segments = list_segments(channel_key, start_time)

    cdn_base = settings.cdn_base_url.rstrip("/")

    lines = [
        "#EXTM3U",
        "#EXT-X-VERSION:7",
        f"#EXT-X-TARGETDURATION:{segment_duration}",
        "#EXT-X-PLAYLIST-TYPE:EVENT",
        f'#EXT-X-MAP:URI="{cdn_base}/hls/{channel_key}/init.mp4"',
        _build_ext_x_key(key_id_hex),
        "",
    ]

    for filename, seg_time in segments:
        lines.append(f"#EXT-X-PROGRAM-DATE-TIME:{seg_time.isoformat()}")
        lines.append(f"#EXTINF:{segment_duration}.000000,")
        lines.append(f"{cdn_base}/hls/{channel_key}/{filename}")

    # No #EXT-X-ENDLIST — EVENT playlist grows as broadcast continues

    build_ms = (time.monotonic() - t0) * 1000
    logger.info(
        "Built EVENT manifest for %s: %d segments from %s (%.1fms)",
        channel_key,
        len(segments),
        start_time.isoformat(),
        build_ms,
    )

    return "\n".join(lines) + "\n"


def build_vod_manifest(
    channel_key: str,
    start_time: datetime,
    end_time: datetime,
    key_id_hex: str,
) -> str:
    """Build an HLS VOD manifest for catch-up playback.

    VOD playlists are complete: all segments from program start to end are
    listed, terminated with #EXT-X-ENDLIST. The player gets the full scrub
    range immediately.

    Handles schedule overruns (e.g., live sports): includes segments up to
    end_time + 30 minutes if they exist, and logs a warning.
    """
    t0 = time.monotonic()
    segment_duration = settings.hls_segment_duration
    overrun_limit = end_time + timedelta(minutes=30)
    segments = list_segments(channel_key, start_time, overrun_limit)

    # Check for overrun
    overrun_segments = [s for s in segments if s[1] > end_time]
    if overrun_segments:
        logger.warning(
            "Schedule overrun for %s: %d segments past end_time %s (up to %s)",
            channel_key,
            len(overrun_segments),
            end_time.isoformat(),
            overrun_segments[-1][1].isoformat(),
        )

    cdn_base = settings.cdn_base_url.rstrip("/")

    lines = [
        "#EXTM3U",
        "#EXT-X-VERSION:7",
        f"#EXT-X-TARGETDURATION:{segment_duration}",
        "#EXT-X-PLAYLIST-TYPE:VOD",
        f'#EXT-X-MAP:URI="{cdn_base}/hls/{channel_key}/init.mp4"',
        _build_ext_x_key(key_id_hex),
        "",
    ]

    for filename, seg_time in segments:
        lines.append(f"#EXT-X-PROGRAM-DATE-TIME:{seg_time.isoformat()}")
        lines.append(f"#EXTINF:{segment_duration}.000000,")
        lines.append(f"{cdn_base}/hls/{channel_key}/{filename}")

    lines.append("#EXT-X-ENDLIST")

    build_ms = (time.monotonic() - t0) * 1000
    logger.info(
        "Built VOD manifest for %s: %d segments [%s -> %s] (%.1fms)",
        channel_key,
        len(segments),
        start_time.isoformat(),
        end_time.isoformat(),
        build_ms,
    )

    return "\n".join(lines) + "\n"
