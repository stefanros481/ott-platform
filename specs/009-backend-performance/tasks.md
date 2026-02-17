# Tasks: Backend Performance Optimization

**Input**: Design documents from `/specs/009-backend-performance/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in the feature specification. Tests omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create new modules and schemas that multiple user stories depend on

- [X] T001 Create `PerformanceMetrics` counter class and `ConfigCache` class with TTL + bounded LRU eviction in backend/app/services/metrics_service.py — ConfigCache: 60s TTL, 10,000 max entries, `get(profile_id, db)`, `invalidate(profile_id)`, `clear()` methods. PerformanceMetrics: heartbeat counters (total, db_ops_total, duration_ms_sum, duration_ms_max), cache counters (hits, misses, invalidations), `record_heartbeat(db_ops, duration_ms)`, `snapshot()` methods. Module-level singletons: `config_cache` and `perf_metrics`.
- [X] T002 [P] Add `PerformanceMetricsResponse` Pydantic schema (with nested `HeartbeatMetrics` and `CacheMetrics` models) in backend/app/schemas/admin.py — match the contract in specs/009-backend-performance/contracts/metrics-api.yaml

---

## Phase 2: Foundational — Database Index (US5, Priority: P2)

**Purpose**: Ensure composite index exists on viewing_sessions for (profile_id, started_at DESC). This is foundational because the query optimizations in US2, US3, and US6 depend on this index being in place.

**Goal**: Viewing session queries by profile and date use index scans, not sequential scans.

**Independent Test**: Run `EXPLAIN ANALYZE` on a viewing session query filtered by profile_id and started_at range — should show Index Scan, not Seq Scan.

- [X] T003 [US5] Create Alembic migration in backend/alembic/versions/004_add_performance_indexes.py — drop existing `ix_vs_profile_started` index if it exists (ASC ordering), then create `ix_vs_profile_started` on viewing_sessions(profile_id, started_at DESC) using `CREATE INDEX CONCURRENTLY IF NOT EXISTS`. Add proper downgrade. Update revision chain to follow 003 migration.
- [X] T004 [US5] Verify index annotation in backend/app/models/viewing_time.py — ensure the ViewingSession model's `__table_args__` reflects the DESC ordering on the composite index so model and migration are aligned.

**Checkpoint**: Index migration complete. Run `alembic upgrade head` and verify with `EXPLAIN ANALYZE SELECT * FROM viewing_sessions WHERE profile_id = '...' AND started_at >= '...' AND started_at < '...' ORDER BY started_at DESC`.

---

## Phase 3: User Story 1 — Concurrent Viewing Without Stalls (Priority: P1) MVP

**Goal**: PIN verification and hashing operations no longer block the async event loop, allowing concurrent heartbeats to proceed unaffected.

**Independent Test**: Verify PIN create/verify/reset all still work. Send a heartbeat concurrently with a PIN verification — heartbeat should complete without delay.

- [X] T005 [US1] Refactor `_hash_pin()` and `_verify_pin_hash()` in backend/app/services/pin_service.py — rename originals to `_hash_pin_sync` / `_verify_pin_hash_sync`, create async versions `_hash_pin(pin)` and `_verify_pin_hash(pin, hashed)` that use `await asyncio.to_thread(...)` to delegate bcrypt to the thread pool. Import `asyncio` at module level.
- [X] T006 [US1] Update all callers in backend/app/services/pin_service.py — change `create_pin()`, `verify_pin()`, and `reset_pin()` to `await` the new async `_hash_pin()` and `_verify_pin_hash()`. Ensure the 200ms timing pad in `verify_pin()` still works correctly with the async call (measure elapsed time including the awaited thread operation).

**Checkpoint**: US1 complete. All PIN endpoints (POST /pin, POST /pin/verify, POST /pin/reset) return correct results. bcrypt no longer blocks the event loop.

---

## Phase 4: User Story 2 — Fast Heartbeat Processing at Scale (Priority: P1)

**Goal**: Heartbeat processing uses no more than 3 database operations (down from 4-6) by combining lookups into a joined query and using RETURNING on the balance upsert.

**Independent Test**: Send heartbeats and verify viewing time is tracked correctly. Balance values should match expectations. Count DB operations via structured logging (added in T010).

- [X] T007 [US2] Combine profile + config + title lookups into a single joined query in `process_heartbeat()` in backend/app/services/viewing_time_service.py — replace the separate `select(Profile)`, `ensure_default_config()`, and `select(Title)` calls (around L208-222) with a single `select(Profile, ViewingTimeConfig, Title).outerjoin(ViewingTimeConfig, ...).outerjoin(Title, ...)` query. Handle NULL config (create default if missing — only on first heartbeat for a new profile). Handle NULL title (raise 404 as before).
- [X] T008 [US2] Add RETURNING clause to balance upsert in `process_heartbeat()` in backend/app/services/viewing_time_service.py — modify the `insert(ViewingTimeBalance).on_conflict_do_update()` statement (around L304-338) to add `.returning(ViewingTimeBalance.used_seconds, ViewingTimeBalance.educational_seconds, ViewingTimeBalance.is_unlimited_override)`. Remove the separate balance re-read query (around L338-349). Use the returned values directly for enforcement status calculation.
- [X] T009 [US2] Add optional pre-loaded profile parameter to `check_playback_eligible()` and `get_balance()` in backend/app/services/viewing_time_service.py — add `profile: Profile | None = None` parameter. If profile is provided, skip the `select(Profile)` query. Update callers in backend/app/routers/viewing_time.py to pass the profile when already loaded by the AccountOwner dependency (pass profile_id for lookup, not the full profile object — the service can accept either).
- [X] T010 [US2] Add basic heartbeat operation logging in backend/app/services/viewing_time_service.py — at the end of `process_heartbeat()`, log a structured line: `logger.info("heartbeat_processed", extra={"profile_id": str(profile_id), "db_ops": db_op_count, "duration_ms": duration_ms})`. Track `db_op_count` by incrementing a local counter after each DB operation in the function.

**Checkpoint**: US2 complete. Heartbeats process with ≤3 DB operations. Balance tracking is accurate. Enforcement status (allowed/warning/blocked) unchanged.

---

## Phase 5: User Story 4 — Cached Configuration for Repeat Requests (Priority: P2)

**Goal**: Viewing time configuration is cached in-process with 60s TTL, reducing DB load by eliminating one query per heartbeat.

**Independent Test**: Send multiple heartbeats for the same profile within 60 seconds — only the first should trigger a config DB lookup. Update config via PUT /viewing-time and verify the next heartbeat uses updated values.

- [X] T011 [US4] Integrate ConfigCache into `process_heartbeat()` in backend/app/services/viewing_time_service.py — replace the `ensure_default_config(db, profile_id)` call with `config_cache.get(profile_id, db)` (import from metrics_service). When config is None from the joined query (T007), use the cache to fetch-or-create. The cache's `get()` method should call `ensure_default_config()` on miss and store the result (detached from session via `db.expunge(config)` + `make_transient(config)`).
- [X] T012 [US4] Add cache invalidation on config update in backend/app/routers/parental_controls.py — after the `db.commit()` in the `PUT /profiles/{profile_id}/viewing-time` endpoint (around L163), call `config_cache.invalidate(profile_id)`. Import `config_cache` from `app.services.metrics_service`.
- [X] T013 [US4] Add cache metrics logging in backend/app/services/metrics_service.py — in ConfigCache `get()` method, increment `perf_metrics.config_cache_hits` or `perf_metrics.config_cache_misses`. In `invalidate()`, increment `perf_metrics.config_cache_invalidations` and log: `logger.info("config_cache_invalidated", extra={"profile_id": str(profile_id)})`.

**Checkpoint**: US4 complete. Config is fetched from DB at most once per 60 seconds per profile. Cache invalidation works on config update.

---

## Phase 6: User Story 3 — Efficient History and Report Queries (Priority: P2)

**Goal**: Weekly reports use a fixed number of queries (not proportional to profile count). History queries use index-friendly date range comparisons.

**Independent Test**: Generate a weekly report for a parent with multiple children — verify data is identical to before. Query viewing history for a date range — verify results match and EXPLAIN shows index scan.

- [X] T014 [US3] Replace `func.date()` with datetime range comparisons in `get_viewing_history()` in backend/app/services/viewing_time_service.py — change the WHERE clause (around L564-568) from `func.date(ViewingSession.started_at) >= from_date` to `ViewingSession.started_at >= datetime.combine(from_date, time.min)` and `ViewingSession.started_at < datetime.combine(to_date + timedelta(days=1), time.min)`. Import `datetime, time as dt_time, timedelta` if not already present.
- [X] T015 [US3] Rewrite `get_weekly_report()` to use batch queries in backend/app/services/viewing_time_service.py — replace the per-profile loop (around L650-700) with: (1) collect all `profile_ids` from child profiles, (2) single `select(ViewingSession).where(ViewingSession.profile_id.in_(profile_ids))` with date range filter using datetime range (not func.date), (3) single `select(ViewingTimeConfig).where(ViewingTimeConfig.profile_id.in_(profile_ids))`, (4) group results by profile_id in Python using `defaultdict`. Preserve all existing response fields (daily_totals, top_titles, limit_usage_percent, etc.).
- [X] T016 [US3] Replace `func.date()` in `get_weekly_report()` date filtering in backend/app/services/viewing_time_service.py — ensure the batch sessions query from T015 uses `ViewingSession.started_at >= datetime.combine(week_start, time.min)` and `ViewingSession.started_at < datetime.combine(week_end + timedelta(days=1), time.min)` instead of `func.date()`.

**Checkpoint**: US3 complete. Weekly report returns identical data with 3 queries (instead of 2N+1). History queries use the composite index.

---

## Phase 7: User Story 6 — Lightweight Data Loading for History (Priority: P3)

**Goal**: History and report queries load only needed fields from Title records instead of full objects.

**Independent Test**: Request viewing history — verify title names appear correctly. Compare memory footprint or query data volume.

- [X] T017 [P] [US6] Change Title loading strategy in `get_viewing_history()` in backend/app/services/viewing_time_service.py — replace `.options(selectinload(ViewingSession.title))` (around L561-563) with `.options(joinedload(ViewingSession.title).load_only(Title.id, Title.title))`. Import `joinedload` from `sqlalchemy.orm` and `Title` from `app.models.catalog` if not already imported.
- [X] T018 [P] [US6] Change Title loading strategy in `get_weekly_report()` in backend/app/services/viewing_time_service.py — apply the same `joinedload(...).load_only(Title.id, Title.title)` to the batch sessions query from T015. Ensure the report's `top_titles` field still resolves correctly.

**Checkpoint**: US6 complete. History and report endpoints return correct title names. Only Title.id and Title.title are fetched from the database.

---

## Phase 8: User Story 7 — Connection and Configuration Efficiency (Priority: P3)

**Goal**: CORS origins are cached, prepared statement caching is enabled, and database connections are pre-warmed on startup.

**Independent Test**: Restart the application and immediately send a request — should not experience cold-start connection delay. Verify CORS headers work correctly.

- [X] T019 [P] [US7] Change `cors_origin_list` from `@property` to `@functools.cached_property` in backend/app/config.py — add `import functools` and change the decorator on `cors_origin_list` (around L35). This caches the parsed list after first access.
- [X] T020 [P] [US7] Add `statement_cache_size` to async engine configuration in backend/app/database.py — add `connect_args={"statement_cache_size": 100}` to the `create_async_engine()` call. This enables asyncpg's prepared statement cache for repeated queries.
- [X] T021 [US7] Add connection pre-warming in application startup in backend/app/main.py — in the `lifespan()` function, after the JWT_SECRET validation, add: `async with engine.begin() as conn: await conn.execute(text("SELECT 1"))`. This forces the connection pool to establish at least one connection before serving requests. Import `text` from `sqlalchemy` and `engine` from `app.database`.

**Checkpoint**: US7 complete. Application starts with pre-warmed connections. CORS still works. Statement cache is active.

---

## Phase 9: Polish & Cross-Cutting — Observability

**Purpose**: Wire up the metrics infrastructure to expose performance data via admin endpoint and structured logging

- [X] T022 Instrument `process_heartbeat()` with PerformanceMetrics in backend/app/services/viewing_time_service.py — wrap the function body with timing (`time.monotonic()` at start and end), call `perf_metrics.record_heartbeat(db_ops=db_op_count, duration_ms=duration_ms)` at the end. Import `perf_metrics` from `app.services.metrics_service` and `time`.
- [X] T023 Add `GET /api/v1/admin/metrics` endpoint in backend/app/routers/admin.py — add a new route returning `PerformanceMetricsResponse`. Import `perf_metrics` and `config_cache` from `app.services.metrics_service`, compute `uptime_seconds` from a module-level `_start_time = time.monotonic()`. Require `AdminUser` dependency. Return snapshot with heartbeat metrics, cache metrics (hit_rate, current_size, max_size), and uptime.
- [X] T024 Add structured log lines for cache events in backend/app/services/metrics_service.py — in ConfigCache, log `logger.debug("config_cache_hit", extra={"profile_id": ...})` on hit and `logger.debug("config_cache_miss", extra={"profile_id": ...})` on miss. Log `logger.info("config_cache_invalidated", ...)` on invalidation (if not already added in T013).
- [X] T025 Verify all existing API responses are unchanged (FR-013) — manually test or write a quick verification script: POST /heartbeat, GET /balance, GET /playback-eligible, GET /history, GET /weekly-report, POST /pin/verify, PUT /viewing-time. Confirm response shapes and values match pre-optimization behavior. Run `alembic upgrade head` to apply migration.

**Checkpoint**: Observability complete. `GET /admin/metrics` returns heartbeat and cache data. Structured logs visible in application output.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational / US5 (Phase 2)**: No dependency on Phase 1 — can run in parallel with Setup
- **US1 (Phase 3)**: No dependency on any other phase — can start immediately (different file: pin_service.py)
- **US2 (Phase 4)**: Depends on Phase 1 (metrics_service.py for logging) and benefits from Phase 2 (index)
- **US4 (Phase 5)**: Depends on Phase 1 (ConfigCache in metrics_service.py)
- **US3 (Phase 6)**: Benefits from Phase 2 (index) — functionally independent
- **US6 (Phase 7)**: Can run after US3 (same functions modified in T015)
- **US7 (Phase 8)**: No dependencies — can start immediately (different files: config.py, database.py, main.py)
- **Polish (Phase 9)**: Depends on Phase 1 (metrics_service.py), Phase 4 (heartbeat instrumentation), Phase 5 (cache metrics)

### User Story Dependencies

```
Phase 1 (Setup) ─────────┬──→ Phase 4 (US2) ──→ Phase 9 (Polish)
                          │
                          ├──→ Phase 5 (US4) ──→ Phase 9 (Polish)
                          │
Phase 2 (US5/Index) ─────┤
                          │
Phase 3 (US1) ───────────┘  (independent — can run in parallel with anything)

Phase 6 (US3) ──→ Phase 7 (US6)   (US6 modifies same functions as US3)

Phase 8 (US7) ────────────────── (fully independent — any time)
```

### Parallel Opportunities

- **T001 and T002**: Setup tasks can run in parallel (different files)
- **T003 and T004**: Foundational tasks can run in parallel (migration vs model)
- **Phase 3 (US1) and Phase 2 (US5)**: Different files entirely — fully parallel
- **Phase 8 (US7)**: All three tasks (T019, T020, T021) touch different files — fully parallel
- **T017 and T018**: Both [P] marked — different functions, same file but independent changes

---

## Parallel Example: Fast Start

```text
# These can all launch simultaneously:
Task: T001 — Create metrics_service.py (Setup)
Task: T003 — Create Alembic migration (US5)
Task: T005 — Async bcrypt wrappers (US1)
Task: T019 — cached_property for CORS (US7)
Task: T020 — statement_cache_size (US7)
```

---

## Implementation Strategy

### MVP First (US1 + US2 Only)

1. Complete Phase 1: Setup (T001–T002)
2. Complete Phase 2: Foundational index (T003–T004)
3. Complete Phase 3: US1 — async bcrypt (T005–T006)
4. Complete Phase 4: US2 — heartbeat optimization (T007–T010)
5. **STOP and VALIDATE**: Heartbeats process with ≤3 DB ops, PIN ops don't block event loop
6. Deploy/demo if ready — the two most critical performance issues are resolved

### Incremental Delivery

1. Setup + Foundational → Infrastructure ready
2. US1 (async bcrypt) → Event loop unblocked (P1 critical fix)
3. US2 (heartbeat hot path) → DB load cut by 50%+ (P1 critical fix)
4. US4 (config cache) → Additional DB query eliminated per heartbeat
5. US3 (batch reports) → Reports scale to any number of children
6. US6 + US7 (lightweight loading + system tweaks) → Refinements
7. Polish → Observability metrics for ongoing monitoring

Each increment is independently testable and delivers measurable improvement.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US1 and US7 are fully independent — can be done at any point after setup
- US2 and US4 share metrics_service.py — do setup first
- US3 and US6 share the same functions in viewing_time_service.py — do US3 before US6
- All changes must preserve existing API response formats (FR-013)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
