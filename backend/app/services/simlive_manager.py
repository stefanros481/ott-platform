"""SimLive Manager — FFmpeg subprocess management for TSTV segment generation.

Manages one FFmpeg process per channel, writing fMP4/CENC encrypted segments
to the shared HLS_SEGMENT_DIR volume using strftime-based filenames.
"""

import asyncio
import logging
import os
import signal
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ChannelProcess:
    channel_key: str
    pid: int
    process: subprocess.Popen
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error: str | None = None


class SimLiveManager:
    """In-memory registry of FFmpeg processes, one per channel."""

    _processes: dict[str, ChannelProcess] = {}

    @classmethod
    def _segment_dir(cls, channel_key: str) -> Path:
        return Path(settings.hls_segment_dir) / channel_key

    @classmethod
    def _source_file(cls, channel_key: str) -> Path:
        return Path(settings.hls_sources_dir) / f"{channel_key}.mp4"

    @classmethod
    async def start_channel(
        cls,
        channel_key: str,
        key_id_hex: str,
        key_hex: str,
    ) -> ChannelProcess:
        """Start FFmpeg for a channel, writing encrypted fMP4 segments.

        Args:
            channel_key: CDN channel key (e.g., 'ch1')
            key_id_hex: DRM key ID as hex string (32 chars)
            key_hex: AES-128 key as hex string (32 chars)

        Raises:
            RuntimeError: If the channel is already running.
            FileNotFoundError: If the source file doesn't exist.
        """
        if channel_key in cls._processes:
            proc = cls._processes[channel_key]
            if proc.process.poll() is None:
                raise RuntimeError(f"Channel {channel_key} is already running (PID {proc.pid})")
            # Process has exited — clean up and allow restart
            del cls._processes[channel_key]

        seg_dir = cls._segment_dir(channel_key)
        seg_dir.mkdir(parents=True, exist_ok=True)

        source = cls._source_file(channel_key)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")

        segment_duration = settings.hls_segment_duration

        # Build FFmpeg command for fMP4/CENC output with strftime filenames
        cmd = [
            "ffmpeg",
            "-re",  # Read at native framerate (realtime simulation)
            "-stream_loop", "-1",  # Loop input indefinitely
            "-i", str(source),
            "-c:v", "copy",  # No re-encoding
            "-c:a", "copy",
            "-f", "hls",
            "-hls_time", str(segment_duration),
            "-hls_segment_type", "fmp4",
            "-hls_flags", "independent_segments+program_date_time+delete_segments",
            "-hls_segment_filename", str(seg_dir / f"{channel_key}-%Y%m%d%H%M%S.m4s"),
            "-strftime", "1",
            "-encryption_scheme", "cenc-aes-ctr",
            "-encryption_key", key_hex,
            "-encryption_kid", key_id_hex,
            "-hls_playlist_type", "event",
            str(seg_dir / "live.m3u8"),
        ]

        logger.info("Starting SimLive for %s: %s", channel_key, " ".join(cmd))

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )

        cp = ChannelProcess(
            channel_key=channel_key,
            pid=process.pid,
            process=process,
        )
        cls._processes[channel_key] = cp
        logger.info("SimLive started for %s (PID %d)", channel_key, process.pid)
        return cp

    @classmethod
    async def stop_channel(cls, channel_key: str) -> None:
        """Stop FFmpeg for a channel. No-op if not running."""
        proc = cls._processes.pop(channel_key, None)
        if proc is None:
            return

        if proc.process.poll() is None:
            logger.info("Stopping SimLive for %s (PID %d)", channel_key, proc.pid)
            proc.process.send_signal(signal.SIGTERM)
            try:
                proc.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning("SimLive %s did not stop gracefully, killing", channel_key)
                proc.process.kill()
                proc.process.wait()

    @classmethod
    async def restart_channel(
        cls,
        channel_key: str,
        key_id_hex: str,
        key_hex: str,
    ) -> ChannelProcess:
        """Stop and restart FFmpeg for a channel."""
        await cls.stop_channel(channel_key)
        return await cls.start_channel(channel_key, key_id_hex, key_hex)

    @classmethod
    def get_status(cls, channel_key: str) -> dict:
        """Get the status of a single channel."""
        proc = cls._processes.get(channel_key)
        seg_dir = cls._segment_dir(channel_key)

        segment_count = 0
        disk_bytes = 0
        if seg_dir.exists():
            for f in seg_dir.iterdir():
                if f.suffix == ".m4s":
                    segment_count += 1
                    disk_bytes += f.stat().st_size

        if proc is None:
            return {
                "channel_key": channel_key,
                "running": False,
                "pid": None,
                "segment_count": segment_count,
                "disk_bytes": disk_bytes,
                "error": None,
            }

        running = proc.process.poll() is None
        error = None
        if not running and proc.process.returncode != 0:
            stderr = proc.process.stderr
            if stderr:
                error = stderr.read().decode("utf-8", errors="replace")[-500:]

        return {
            "channel_key": channel_key,
            "running": running,
            "pid": proc.pid if running else None,
            "segment_count": segment_count,
            "disk_bytes": disk_bytes,
            "error": error,
        }

    @classmethod
    def list_all_statuses(cls, channel_keys: list[str] | None = None) -> list[dict]:
        """Get status for all known channels (or specified list)."""
        if channel_keys is None:
            # Return status for all channels with processes + any with segment dirs
            keys = set(cls._processes.keys())
            seg_root = Path(settings.hls_segment_dir)
            if seg_root.exists():
                for d in seg_root.iterdir():
                    if d.is_dir():
                        keys.add(d.name)
            channel_keys = sorted(keys)

        return [cls.get_status(k) for k in channel_keys]

    @classmethod
    async def restore_running_channels(cls) -> None:
        """Restore channels on startup. Called from lifespan hook.

        In a real system, this would re-read persisted state and restart
        FFmpeg processes. For the PoC, we just log that no channels are
        auto-started (admin must start them manually via the API).
        """
        logger.info("[SimLive] Restore check: no auto-start configured. Use admin API to start channels.")

    @classmethod
    def cleanup_old_segments(cls, channel_key: str, max_age_hours: int) -> tuple[int, int]:
        """Delete segments older than max_age_hours for a channel.

        Returns (segments_deleted, bytes_freed).
        """
        seg_dir = cls._segment_dir(channel_key)
        if not seg_dir.exists():
            return 0, 0

        now = datetime.now(timezone.utc)
        deleted = 0
        freed = 0

        for f in seg_dir.iterdir():
            if f.suffix != ".m4s":
                continue
            mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
            age_hours = (now - mtime).total_seconds() / 3600
            if age_hours > max_age_hours:
                size = f.stat().st_size
                f.unlink()
                deleted += 1
                freed += size

        if deleted:
            logger.info(
                "Cleaned up %d segments (%.1f MB) for %s",
                deleted,
                freed / (1024 * 1024),
                channel_key,
            )

        return deleted, freed

    @classmethod
    def cleanup_all(cls, max_age_hours: int = 168) -> dict:
        """Run cleanup_old_segments for every known channel directory.

        Returns a CleanupResult-compatible dict.
        """
        seg_root = Path(settings.hls_segment_dir)
        if not seg_root.exists():
            return {"channels_processed": 0, "total_segments_deleted": 0, "total_bytes_freed": 0}

        channels_processed = 0
        total_deleted = 0
        total_freed = 0

        for d in seg_root.iterdir():
            if d.is_dir():
                deleted, freed = cls.cleanup_old_segments(d.name, max_age_hours)
                channels_processed += 1
                total_deleted += deleted
                total_freed += freed

        return {
            "channels_processed": channels_processed,
            "total_segments_deleted": total_deleted,
            "total_bytes_freed": total_freed,
        }
