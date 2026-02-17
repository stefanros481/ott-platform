# Quickstart: Backend Performance Optimization

**Feature Branch**: `009-backend-performance`
**Date**: 2026-02-13

## Prerequisites

- Feature 006 (Viewing Time Limits) must be complete and merged
- Docker Compose stack running (`docker compose up`)
- Backend running with existing seed data

## Implementation Order

Work through these phases sequentially. Each phase is independently testable.

### Phase 1: Unblock the Event Loop (C-01)

**File**: `backend/app/services/pin_service.py`

1. Create async wrappers for `_hash_pin()` and `_verify_pin_hash()` using `asyncio.to_thread()`
2. Update all callers (`create_pin`, `verify_pin`, `reset_pin`) to `await` the async variants
3. **Test**: Verify PIN create/verify/reset still work. Confirm heartbeats are not delayed during PIN operations.

### Phase 2: Optimize Heartbeat Hot Path (C-02, H-05)

**File**: `backend/app/services/viewing_time_service.py`

1. Combine profile + config + title lookups into a single joined query in `process_heartbeat()`
2. Update balance upsert to use `RETURNING` clause, eliminating the post-upsert re-read
3. Replace `func.date()` with `datetime.combine()` range comparisons in `get_viewing_history()` and `get_weekly_report()`
4. **Test**: Verify heartbeat still tracks time correctly. Verify balance values are accurate. Check viewing history returns same results.

### Phase 3: Add Composite Index (H-01)

**File**: New migration `backend/alembic/versions/004_add_performance_indexes.py`

1. Create Alembic migration to verify/create the composite index with `CONCURRENTLY` flag
2. Run migration: `docker compose exec backend alembic upgrade head`
3. **Test**: Verify index exists with `EXPLAIN ANALYZE` on a viewing session query.

### Phase 4: Config Cache (H-02)

**File**: `backend/app/services/viewing_time_service.py`

1. Create a `ConfigCache` class with TTL and bounded size
2. Replace `ensure_default_config()` calls in `process_heartbeat()` with cached version
3. Add cache invalidation call in `PUT /viewing-time` endpoint (`backend/app/routers/parental_controls.py`)
4. **Test**: Verify config changes are picked up within 60 seconds. Verify cache hit rate via logs.

### Phase 5: Batch Queries & Profile Pass-through (C-03, H-03, H-04)

**Files**: `backend/app/services/viewing_time_service.py`, `backend/app/routers/parental_controls.py`

1. Rewrite `get_weekly_report()` to use batch `IN(...)` queries instead of per-profile loops
2. Add optional `profile` parameter to `get_balance()` and `check_playback_eligible()` to skip redundant fetches
3. Change `selectinload(ViewingSession.title)` to `joinedload(...).load_only(Title.id, Title.title)` in history/report queries
4. **Test**: Verify weekly report data is identical. Verify history shows correct titles.

### Phase 6: System-Level Improvements (M-01, M-06, L-05)

**Files**: `backend/app/config.py`, `backend/app/database.py`, `backend/app/main.py`

1. Change `cors_origin_list` from `@property` to `@functools.cached_property`
2. Add `connect_args={"statement_cache_size": 100}` to engine creation
3. Add connection pre-warming in `lifespan()` startup
4. **Test**: Verify app starts without errors. Verify CORS still works.

### Phase 7: Observability (FR-015, FR-016)

**Files**: New `backend/app/services/metrics_service.py`, `backend/app/routers/admin.py`, `backend/app/services/viewing_time_service.py`

1. Create `PerformanceMetrics` class with counters
2. Instrument `process_heartbeat()` with timing and DB op counting
3. Add structured log lines for cache events and heartbeat durations
4. Add `GET /api/v1/admin/metrics` endpoint
5. **Test**: Verify metrics endpoint returns data after sending heartbeats.

## Verification Checklist

After all phases:

- [ ] All existing tests pass (no regressions)
- [ ] PIN create/verify/reset work correctly
- [ ] Heartbeats track viewing time accurately
- [ ] Balance enforcement (warning/blocked) still works
- [ ] Weekly reports show correct data
- [ ] Viewing history returns correct results
- [ ] Config updates take effect within 60 seconds
- [ ] Metrics endpoint shows reasonable values
- [ ] API response formats are unchanged (FR-013)

## Key Files Modified

| File | Changes |
|------|---------|
| `backend/app/services/pin_service.py` | asyncio.to_thread wrappers for bcrypt |
| `backend/app/services/viewing_time_service.py` | Joined queries, RETURNING, range comparisons, batch queries, load_only, config cache |
| `backend/app/routers/parental_controls.py` | Cache invalidation on config update |
| `backend/app/config.py` | cached_property for CORS |
| `backend/app/database.py` | statement_cache_size |
| `backend/app/main.py` | Connection pre-warming in lifespan |
| `backend/app/models/viewing_time.py` | Index model annotation update (if needed) |
| `backend/alembic/versions/004_*.py` | New migration for index verification |
| `backend/app/services/metrics_service.py` | New: performance counters |
| `backend/app/routers/admin.py` | New endpoint: GET /admin/metrics |
| `backend/app/schemas/admin.py` | New: PerformanceMetricsResponse schema |
