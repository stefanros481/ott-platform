# Backend Performance Optimization Plan (009)

**Scope:** Python/FastAPI backend at `backend/app/`
**Stack:** Python 3.12, FastAPI 0.115+, SQLAlchemy 2.0+ async, PostgreSQL 16 + pgvector, bcrypt, python-jose

---

## CRITICAL (3)

### C-01: bcrypt blocks the async event loop

**Location:** `backend/app/services/pin_service.py:22,27,78`
**Impact:** bcrypt is CPU-bound (~200ms per call). `_verify_pin_hash()` and `_hash_pin()` run synchronously, stalling the entire asyncio event loop. A single PIN verification blocks all concurrent heartbeat processing.

**Fix:** Run bcrypt in a thread executor:

```python
import asyncio

async def _verify_pin_hash_async(pin: str, hashed: str) -> bool:
    return await asyncio.to_thread(bcrypt.checkpw, pin.encode(), hashed.encode())

async def _hash_pin_async(pin: str) -> str:
    return await asyncio.to_thread(
        lambda: bcrypt.hashpw(pin.encode(), bcrypt.gensalt()).decode()
    )
```

Update all callers (`verify_pin`, `create_pin`, `reset_pin`) to use the async variants. The M-04 constant-time padding already uses `asyncio.sleep` — now the bcrypt call itself also won't block.

---

### C-02: Heartbeat does 4-6 DB round-trips per call

**Location:** `backend/app/services/viewing_time_service.py:191-378`
**Impact:** `process_heartbeat()` is the hottest path — called every 30s per active viewer. Currently executes separate queries for:
1. Profile lookup (L208)
2. Config lookup (L214-217)
3. Title lookup (L220-222)
4. Session lookup or create (L230-253)
5. Balance upsert (L304-335)
6. Balance re-read (L338-349)

At 500K concurrent viewers, that's ~100K heartbeats/minute, each doing 4-6 queries.

**Fix — Phase A (combine lookups):**

```python
# Single joined query for profile + config + title
result = await db.execute(
    select(Profile, ViewingTimeConfig, Title)
    .outerjoin(ViewingTimeConfig, ViewingTimeConfig.profile_id == Profile.id)
    .outerjoin(Title, Title.id == title_id)
    .where(Profile.id == profile_id)
)
row = result.one_or_none()
profile, config, title = row if row else (None, None, None)
```

**Fix — Phase B (eliminate balance re-read):**

Use PostgreSQL `RETURNING` clause on the upsert:

```python
stmt = insert(ViewingTimeBalance).values(...).on_conflict_do_update(
    constraint="uq_vtb_profile_date",
    set_={...},
).returning(
    ViewingTimeBalance.used_seconds,
    ViewingTimeBalance.educational_seconds,
    ViewingTimeBalance.is_unlimited_override,
)
result = await db.execute(stmt)
row = result.one()
used_seconds, educational_secs, is_unlimited = row
```

**Target:** Reduce from 4-6 queries to 2-3 per heartbeat.

---

### C-03: N+1 queries in weekly report

**Location:** `backend/app/services/viewing_time_service.py:636-719`
**Impact:** For each child profile, a separate `select(ViewingSession)` and `ensure_default_config` are issued. With N kids, that's 2N+1 queries.

**Fix:** Fetch all sessions and configs for all child profiles in one query each:

```python
# 1. Fetch all child profiles (already done)
# 2. Fetch all sessions for all profiles in one query
profile_ids = [p.id for p in child_profiles]
sessions_result = await db.execute(
    select(ViewingSession)
    .options(selectinload(ViewingSession.title))
    .where(
        and_(
            ViewingSession.profile_id.in_(profile_ids),
            func.date(ViewingSession.started_at) >= week_start,
            func.date(ViewingSession.started_at) <= week_end,
        )
    )
)
# 3. Fetch all configs in one query
configs_result = await db.execute(
    select(ViewingTimeConfig).where(ViewingTimeConfig.profile_id.in_(profile_ids))
)
# 4. Group in Python
```

**Target:** Reduce from 2N+1 queries to 3 queries regardless of profile count.

---

## HIGH (5)

### H-01: Missing composite index on ViewingSession

**Location:** `backend/app/models/viewing_time.py` (ViewingSession model)
**Impact:** History and heartbeat queries filter on `(profile_id, started_at)` without a composite index, forcing sequential scans on large tables.

**Fix:** Add Alembic migration:

```sql
CREATE INDEX ix_viewing_session_profile_started
ON viewing_sessions (profile_id, started_at DESC);
```

---

### H-02: Config fetched on every heartbeat

**Location:** `backend/app/services/viewing_time_service.py:50-76`
**Impact:** `ensure_default_config()` does a SELECT (and possibly INSERT) on every heartbeat. Config rarely changes — at most once per parent settings update.

**Fix:** Add a simple in-process TTL cache:

```python
from functools import lru_cache
import time

_config_cache: dict[uuid.UUID, tuple[ViewingTimeConfig, float]] = {}
CONFIG_CACHE_TTL = 60  # seconds

async def get_cached_config(db: AsyncSession, profile_id: uuid.UUID) -> ViewingTimeConfig:
    cached = _config_cache.get(profile_id)
    if cached and time.monotonic() - cached[1] < CONFIG_CACHE_TTL:
        return cached[0]
    config = await ensure_default_config(db, profile_id)
    _config_cache[profile_id] = (config, time.monotonic())
    return config
```

Invalidate on config update in the router.

---

### H-03: Redundant profile fetch in playback eligibility

**Location:** `backend/app/services/viewing_time_service.py:429-454`
**Impact:** `check_playback_eligible` calls `get_balance`, which re-fetches the profile. When called from the router, the profile was already loaded by the `AccountOwner` dependency.

**Fix:** Pass the already-loaded profile to `get_balance` as an optional parameter to avoid the redundant query.

---

### H-04: Full Title objects loaded for history

**Location:** `backend/app/services/viewing_time_service.py:561-563`
**Impact:** `selectinload(ViewingSession.title)` loads the complete Title ORM object (with all columns) but only `title.title` is used.

**Fix:** Use `joinedload` with `load_only`:

```python
.options(
    joinedload(ViewingSession.title).load_only(Title.id, Title.title)
)
```

---

### H-05: `func.date()` prevents index usage on history queries

**Location:** `backend/app/services/viewing_time_service.py:564-568`
**Impact:** Wrapping `started_at` in `func.date()` prevents PostgreSQL from using the composite index. Forces a sequential scan.

**Fix:** Use range comparison:

```python
from datetime import datetime, time as dt_time

start_dt = datetime.combine(from_date, dt_time.min)
end_dt = datetime.combine(to_date + timedelta(days=1), dt_time.min)

.where(
    and_(
        ViewingSession.profile_id == profile_id,
        ViewingSession.started_at >= start_dt,
        ViewingSession.started_at < end_dt,
    )
)
```

---

## MEDIUM (8)

### M-01: CORS origins parsed on every request

**Location:** `backend/app/config.py:35-36`
**Fix:** Cache the split result with `@functools.cached_property`.

### M-02: ZoneInfo instantiation in `get_viewing_day`

**Location:** `backend/app/services/viewing_time_service.py:90`
**Note:** Python's `ZoneInfo` has its own internal cache. Low priority.

### M-03: Duplicate upsert SQL paths for educational vs counted

**Location:** `backend/app/services/viewing_time_service.py:304-335`
**Fix:** Unify into a single parameterized upsert with conditional `set_` values.

### M-04: `model_dump(exclude_unset=True)` allocation

**Location:** `backend/app/routers/parental_controls.py:144`
**Note:** Negligible for the config update path (low frequency).

### M-05: Session end uses SELECT + UPDATE pattern

**Location:** `backend/app/services/viewing_time_service.py:396-421`
**Fix:** Could use `UPDATE ... WHERE ... RETURNING` to combine into one query.

### M-06: No connection pool pre-warming

**Location:** `backend/app/config.py` (engine creation)
**Fix:** Add pool pre-ping and optionally pre-create connections on startup.

### M-07: Weekly report calls `ensure_default_config` per profile

**Location:** `backend/app/services/viewing_time_service.py:695`
**Fix:** Batch fetch all configs in one query (covered by C-03 fix).

### M-08: defaultdict allocation in history grouping

**Location:** `backend/app/services/viewing_time_service.py:577`
**Note:** Negligible overhead — `defaultdict` is fine here.

---

## LOW (6)

### L-01: Repeated `round()` calls in responses

**Location:** Multiple places in `viewing_time_service.py`
**Note:** Minimal CPU impact.

### L-02: Multiple `datetime.now(UTC)` calls per heartbeat

**Location:** `backend/app/services/viewing_time_service.py:205`
**Fix:** Capture `now` once at function entry (already done — but some code paths call it again).

### L-03: Import-inside-function pattern in routers

**Location:** `backend/app/routers/parental_controls.py:132,150,194,234,250`
**Note:** Prevents circular imports. Negligible perf impact after first import.

### L-04: `db_pool_recycle=3600` may be aggressive

**Location:** `backend/app/config.py:21`
**Note:** PostgreSQL handles long connections well. Consider 3600 → 7200.

### L-05: No `statement_cache_size` on async engine

**Location:** Engine creation (not in config.py)
**Fix:** Set `statement_cache_size=100` on the engine for prepared statement reuse.

### L-06: Full ViewingTimeBalance loaded when only counters needed

**Location:** `backend/app/services/viewing_time_service.py:338-349`
**Fix:** Covered by C-02 RETURNING fix.

---

## Implementation Order

| Phase | Findings | Impact | Effort |
|-------|----------|--------|--------|
| 1 | C-01 | Unblock event loop from bcrypt | Small — `asyncio.to_thread` wrapper |
| 2 | C-02, H-05 | Optimize heartbeat hot path | Medium — query rewrite |
| 3 | H-01 | Add composite index (migration) | Small — one migration |
| 4 | H-02 | Cache config lookups | Small — TTL cache dict |
| 5 | C-03, H-03, H-04 | Optimize weekly report + balance | Medium — query consolidation |
| 6 | M-01, M-06, L-05 | Config + connection improvements | Small — one-liners |
