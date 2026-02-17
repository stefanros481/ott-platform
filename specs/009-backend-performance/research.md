# Research: Backend Performance Optimization

**Feature Branch**: `009-backend-performance`
**Date**: 2026-02-13

## R-01: Offloading CPU-bound bcrypt to thread executor

**Decision**: Use `asyncio.to_thread()` to run bcrypt operations off the async event loop.

**Rationale**: `bcrypt.hashpw()` and `bcrypt.checkpw()` are CPU-bound (~200ms per call). Running them synchronously on the asyncio event loop blocks all concurrent coroutines. `asyncio.to_thread()` (Python 3.9+) delegates to the default thread pool executor, freeing the event loop immediately.

**Alternatives considered**:
- **`loop.run_in_executor(None, ...)`**: Equivalent but more verbose; `asyncio.to_thread` is the modern wrapper.
- **ProcessPoolExecutor**: Overkill — bcrypt releases the GIL during its C-level computation, so threads suffice.
- **Async bcrypt library (e.g., `aiohttp`-based)**: Adds a dependency; `asyncio.to_thread` with stdlib bcrypt is simpler and equally effective.

**Current code** ([pin_service.py:21-28](backend/app/services/pin_service.py#L21-L28)):
- `_hash_pin()` calls `bcrypt.hashpw()` synchronously.
- `_verify_pin_hash()` calls `bcrypt.checkpw()` synchronously.
- Callers: `create_pin`, `verify_pin`, `reset_pin`.

**Impact**: Unblocks concurrent heartbeat processing during PIN operations.

---

## R-02: Reducing heartbeat DB round-trips with joined queries

**Decision**: Combine the profile + config + title lookups into a single joined query. Use PostgreSQL `INSERT ... ON CONFLICT ... RETURNING` to eliminate the post-upsert re-read.

**Rationale**: `process_heartbeat()` currently executes 4-6 sequential queries per call. At 30-second intervals with thousands of concurrent viewers, this is the dominant source of database load.

**Current query pattern** ([viewing_time_service.py:191-378](backend/app/services/viewing_time_service.py#L191-L378)):
1. Profile lookup (separate query)
2. Config lookup via `ensure_default_config` (SELECT + possible INSERT)
3. Title lookup (separate query)
4. Session lookup or create (SELECT/INSERT)
5. Balance upsert (INSERT ON CONFLICT UPDATE)
6. Balance re-read (SELECT to get updated values)

**Optimized pattern**:
1. **Joined lookup**: `SELECT Profile, ViewingTimeConfig, Title` in one query using `outerjoin` (1 query).
2. Session lookup or create (1 query — unchanged, conditional logic required).
3. Balance upsert with `RETURNING` clause (1 query — replaces upsert + re-read).

**Target**: 2-3 queries per heartbeat (down from 4-6).

**Alternatives considered**:
- **Materialized view for profile+config**: Overly complex for this PoC; joined query is simpler.
- **Caching profile+title in application**: Would reduce to 1-2 queries but adds invalidation complexity. Config caching (R-04) handles the most valuable part.

---

## R-03: Fixing N+1 in weekly report with batch queries

**Decision**: Replace per-profile loops with batch `IN(...)` queries for sessions and configs.

**Rationale**: `get_weekly_report()` iterates over each child profile and issues 2 queries per profile (sessions + config). For N children, that's 2N+1 queries.

**Current pattern** ([viewing_time_service.py:636-719](backend/app/services/viewing_time_service.py#L636-L719)):
```
1. SELECT child profiles WHERE user_id = X AND is_kids = True  (1 query)
2. FOR each profile:
   a. SELECT sessions WHERE profile_id = profile.id AND date range  (N queries)
   b. ensure_default_config(profile.id)                              (N queries)
```

**Optimized pattern**:
```
1. SELECT child profiles (1 query)
2. SELECT sessions WHERE profile_id IN (...all profile IDs...) (1 query)
3. SELECT configs WHERE profile_id IN (...all profile IDs...) (1 query)
4. Group sessions and configs by profile_id in Python
```

**Target**: 3 queries regardless of profile count (down from 2N+1).

---

## R-04: In-process TTL cache for ViewingTimeConfig

**Decision**: Use a simple dictionary-based TTL cache with bounded size and LRU eviction.

**Rationale**: `ensure_default_config()` is called on every heartbeat but config rarely changes (only when parents update settings). A 60-second TTL cache eliminates one DB query per heartbeat with minimal staleness risk.

**Design choices**:
- **TTL**: 60 seconds (configurable). Max 60 seconds of stale data if invalidation fails.
- **Invalidation**: Explicit cache eviction when `PUT /viewing-time` config endpoint is called.
- **Max size**: 10,000 entries (well above realistic concurrent profile count for a PoC).
- **Eviction**: LRU when max size reached.
- **Thread safety**: Not required — single asyncio event loop, no concurrent dict mutations.

**Alternatives considered**:
- **`functools.lru_cache`**: No TTL support; entries never expire.
- **`cachetools.TTLCache`**: Perfect fit but adds a dependency. A simple dict + `time.monotonic()` is equivalent and dependency-free.
- **Redis**: Overkill for single-instance PoC (constitution principle: no external dependencies beyond docker-compose stack).

---

## R-05: Composite index on ViewingSession

**Decision**: Add composite index `(profile_id, started_at DESC)` via Alembic migration.

**Rationale**: History and heartbeat queries filter on `(profile_id, started_at)`. The existing partial index `ix_vs_profile_active` only covers active sessions (WHERE ended_at IS NULL). The existing `ix_vs_profile_started` index exists but H-05's `func.date()` wrapper prevents its use.

**Current indexes** ([viewing_time.py:75-99](backend/app/models/viewing_time.py#L75-L99)):
- `ix_vs_profile_active`: `(profile_id) WHERE ended_at IS NULL` — for active session lookup.
- `ix_vs_profile_started`: `(profile_id, started_at)` — exists but unused due to `func.date()` wrapping.

**Fix**: The index already exists. The real fix is R-06 (replacing `func.date()` with range comparisons so PostgreSQL can use the existing index).

**Migration approach**: Use `CREATE INDEX CONCURRENTLY` to avoid table locks during creation if adding new indexes in the future. The current migration for the existing index is sufficient.

---

## R-06: Replacing func.date() with range comparisons

**Decision**: Replace `func.date(ViewingSession.started_at) >= from_date` with `ViewingSession.started_at >= datetime.combine(from_date, time.min)`.

**Rationale**: Wrapping a column in a function (e.g., `func.date()`) prevents PostgreSQL from using B-tree indexes on that column. Range comparisons preserve index eligibility.

**Current pattern** ([viewing_time_service.py:564-568](backend/app/services/viewing_time_service.py#L564-L568)):
```python
func.date(ViewingSession.started_at) >= from_date
func.date(ViewingSession.started_at) <= to_date
```

**Optimized pattern**:
```python
ViewingSession.started_at >= datetime.combine(from_date, time.min)
ViewingSession.started_at < datetime.combine(to_date + timedelta(days=1), time.min)
```

**Applies to**: `get_viewing_history()` and `get_weekly_report()`.

---

## R-07: Lightweight Title loading with load_only

**Decision**: Use `joinedload(...).load_only(Title.id, Title.title)` instead of full `selectinload`.

**Rationale**: History and report queries load full Title objects but only use `title.title` (display name). Loading only needed columns reduces memory and I/O.

**Current pattern** ([viewing_time_service.py:561-563](backend/app/services/viewing_time_service.py#L561-L563)):
```python
.options(selectinload(ViewingSession.title))
```

**Optimized pattern**:
```python
.options(joinedload(ViewingSession.title).load_only(Title.id, Title.title))
```

---

## R-08: Passing pre-loaded profile to avoid redundant fetch

**Decision**: Add optional `profile` parameter to `get_balance()` and `check_playback_eligible()`.

**Rationale**: When called from routers, the profile has already been loaded by the `AccountOwner` dependency. Passing it through avoids a redundant SELECT.

**Current flow** ([viewing_time_service.py:429-454](backend/app/services/viewing_time_service.py#L429-L454)):
```
Router: AccountOwner dependency loads user (includes profile ownership check)
→ Service: check_playback_eligible calls get_balance
→ Service: get_balance re-fetches profile from DB
```

**Optimized flow**:
```
Router: AccountOwner dependency loads user
→ Router: passes profile_id (already verified)
→ Service: accepts optional pre-loaded profile, skips DB fetch if provided
```

---

## R-09: CORS origin caching

**Decision**: Use `@functools.cached_property` for `cors_origin_list` on the Settings class.

**Rationale**: `cors_origin_list` parses a comma-separated string on every access. Since Settings is a singleton and CORS origins don't change at runtime, caching the result is safe and eliminates per-request string splitting.

**Current code** ([config.py:35-36](backend/app/config.py#L35-L36)):
```python
@property
def cors_origin_list(self) -> list[str]:
    return [o.strip() for o in self.cors_origins.split(",")]
```

**Fix**: Change `@property` to `@functools.cached_property`.

---

## R-10: Connection pool pre-warming and statement cache

**Decision**: Add `pool_pre_ping=True` (already set), and set `statement_cache_size=100` on the async engine. Optionally pre-create connections on startup.

**Rationale**:
- `pool_pre_ping` is already configured ([database.py:13](backend/app/database.py#L13)). No change needed.
- `statement_cache_size` enables asyncpg's prepared statement cache, reducing query parse overhead for repeated queries.
- Pre-warming connections on startup eliminates the cold-start latency for the first requests.

**Current engine config** ([database.py:8-15](backend/app/database.py#L8-L15)):
```python
engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,
    pool_recycle=settings.db_pool_recycle,
)
```

**Additions**:
- `connect_args={"statement_cache_size": 100}` on engine creation.
- Startup hook in `lifespan()` to execute a simple query, forcing pool initialization.

---

## R-11: Observability metrics approach

**Decision**: Use Python stdlib `logging` with structured log fields for metrics, plus a simple in-process metrics counter for key indicators.

**Rationale**: The PoC doesn't need a full metrics stack (Prometheus, etc.). Structured logging with key metrics (heartbeat_db_ops, heartbeat_duration_ms, cache_hit_rate) provides observability that can be upgraded to proper metrics later.

**Metrics to expose**:
1. **Heartbeat DB operation count**: Log per-heartbeat with actual query count.
2. **Heartbeat response latency**: Log duration in milliseconds.
3. **Config cache hit/miss**: Track hit rate via counter; log on cache invalidation.
4. **Weekly report query count**: Log actual query count per report generation.

**Implementation**:
- Add a lightweight `PerformanceMetrics` helper class with counters.
- Expose via `GET /api/v1/admin/metrics` endpoint (behind AdminUser auth).
- Structured log lines for each heartbeat and cache event.

**Alternatives considered**:
- **Prometheus client**: Adds dependency; overkill for PoC.
- **StatsD/Datadog**: External dependency; violates constitution (no cloud services).
- **FastAPI middleware timing**: Only measures total request time, not per-component.
