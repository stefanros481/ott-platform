"""Performance metrics and config cache — in-process observability for 009-backend-performance."""

import logging
import time
import uuid

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# ConfigCache — TTL-based in-process cache for ViewingTimeConfig
# ---------------------------------------------------------------------------

_CACHE_TTL_SECONDS = 60
_CACHE_MAX_SIZE = 10_000


class ConfigCache:
    """In-process TTL cache for ViewingTimeConfig objects.

    - **TTL**: 60 seconds (configurable).
    - **Max size**: 10,000 entries with LRU eviction.
    - **Thread safety**: Not required — single asyncio event loop.
    """

    def __init__(self, ttl: float = _CACHE_TTL_SECONDS, max_size: int = _CACHE_MAX_SIZE):
        self.ttl = ttl
        self.max_size = max_size
        self._store: dict[uuid.UUID, tuple[object, float]] = {}  # {profile_id: (config, cached_at)}

    def get_cached(self, profile_id: uuid.UUID) -> object | None:
        """Return cached config if present and not expired, else None."""
        entry = self._store.get(profile_id)
        if entry is None:
            logger.debug("config_cache_miss", extra={"profile_id": str(profile_id)})
            return None
        config, cached_at = entry
        if time.monotonic() - cached_at > self.ttl:
            del self._store[profile_id]
            logger.debug("config_cache_expired", extra={"profile_id": str(profile_id)})
            return None
        # Move to end for LRU ordering (dict preserves insertion order in 3.7+)
        self._store.move_to_end(profile_id) if hasattr(self._store, "move_to_end") else None
        logger.debug("config_cache_hit", extra={"profile_id": str(profile_id)})
        return config

    def put(self, profile_id: uuid.UUID, config: object) -> None:
        """Store a config entry, evicting LRU if at capacity."""
        if profile_id in self._store:
            del self._store[profile_id]
        elif len(self._store) >= self.max_size:
            # Evict oldest (first) entry
            oldest_key = next(iter(self._store))
            del self._store[oldest_key]
        self._store[profile_id] = (config, time.monotonic())

    def invalidate(self, profile_id: uuid.UUID) -> None:
        """Remove a specific profile's cached config."""
        self._store.pop(profile_id, None)
        perf_metrics.config_cache_invalidations += 1
        logger.info("config_cache_invalidated", extra={"profile_id": str(profile_id)})

    def clear(self) -> None:
        """Remove all cached entries."""
        self._store.clear()

    @property
    def current_size(self) -> int:
        return len(self._store)


# ---------------------------------------------------------------------------
# PerformanceMetrics — lightweight in-process counters
# ---------------------------------------------------------------------------


class PerformanceMetrics:
    """In-process performance counters, reset on application restart."""

    def __init__(self):
        self.heartbeat_total: int = 0
        self.heartbeat_db_ops_total: int = 0
        self.heartbeat_duration_ms_sum: float = 0.0
        self.heartbeat_duration_ms_max: float = 0.0
        self._heartbeat_durations: list[float] = []  # for p95 calculation
        self.config_cache_hits: int = 0
        self.config_cache_misses: int = 0
        self.config_cache_invalidations: int = 0

    def record_heartbeat(self, db_ops: int, duration_ms: float) -> None:
        """Record metrics for a single heartbeat processing call."""
        self.heartbeat_total += 1
        self.heartbeat_db_ops_total += db_ops
        self.heartbeat_duration_ms_sum += duration_ms
        if duration_ms > self.heartbeat_duration_ms_max:
            self.heartbeat_duration_ms_max = duration_ms
        self._heartbeat_durations.append(duration_ms)
        # Keep only last 1000 durations for p95 calculation
        if len(self._heartbeat_durations) > 1000:
            self._heartbeat_durations = self._heartbeat_durations[-1000:]

    def snapshot(self) -> dict:
        """Return a point-in-time snapshot of all metrics."""
        total = self.heartbeat_total or 1  # avoid division by zero
        cache_total = self.config_cache_hits + self.config_cache_misses

        # Compute p95 from recent durations
        p95 = 0.0
        if self._heartbeat_durations:
            sorted_d = sorted(self._heartbeat_durations)
            idx = int(len(sorted_d) * 0.95)
            p95 = sorted_d[min(idx, len(sorted_d) - 1)]

        return {
            "heartbeat": {
                "total_processed": self.heartbeat_total,
                "avg_db_ops_per_heartbeat": round(self.heartbeat_db_ops_total / total, 2),
                "avg_duration_ms": round(self.heartbeat_duration_ms_sum / total, 2),
                "max_duration_ms": round(self.heartbeat_duration_ms_max, 2),
                "p95_duration_ms": round(p95, 2),
            },
            "config_cache": {
                "hit_rate": round(self.config_cache_hits / cache_total, 4) if cache_total > 0 else 0.0,
                "total_hits": self.config_cache_hits,
                "total_misses": self.config_cache_misses,
                "total_invalidations": self.config_cache_invalidations,
            },
        }


# Module-level singletons
config_cache = ConfigCache()
perf_metrics = PerformanceMetrics()
