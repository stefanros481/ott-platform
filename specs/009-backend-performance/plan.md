# Implementation Plan: Backend Performance Optimization

**Branch**: `009-backend-performance` | **Date**: 2026-02-13 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/009-backend-performance/spec.md`

## Summary

Optimize the backend viewing time system for concurrent usage at scale. The three critical fixes are: (1) offload CPU-bound bcrypt PIN operations to a thread executor so they don't block the async event loop, (2) reduce heartbeat database round-trips from 4-6 to 2-3 via joined queries and RETURNING clauses, and (3) eliminate N+1 query patterns in weekly reports via batch queries. Supporting optimizations include an in-process config cache with TTL, index-friendly date range queries, lightweight Title loading, CORS caching, connection pre-warming, and production observability metrics.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: FastAPI 0.115+, SQLAlchemy 2.0+ (async), bcrypt, python-jose (JWT), Pydantic Settings
**Storage**: PostgreSQL 16 + pgvector 0.7+ (asyncpg driver)
**Testing**: pytest + httpx (AsyncClient)
**Target Platform**: Linux container (Docker Compose)
**Project Type**: Web application (backend-only changes for this feature)
**Performance Goals**: Heartbeat p95 < 200ms, heartbeat DB ops <= 3, weekly report < 2s for 10 profiles
**Constraints**: Single FastAPI process, in-process caching only, no external metrics services
**Scale/Scope**: 1,000 concurrent viewers target, 30s heartbeat interval (~33 heartbeats/sec)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. PoC-First Quality | PASS | Optimizations target functional correctness under concurrency; no production hardening beyond what's needed |
| II. Monolithic Simplicity | PASS | All changes within single FastAPI app; no new services or processes |
| III. AI-Native by Default | N/A | Performance feature, no AI components |
| IV. Docker Compose as Truth | PASS | No new containers or external dependencies; in-process caching only |
| V. Seed Data as Demo | PASS | Existing seed data unchanged; optimizations are transparent |

**Gate result**: PASS — no violations.

### Post-Design Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. PoC-First Quality | PASS | Config cache and metrics are simple in-process structures, not production infrastructure |
| II. Monolithic Simplicity | PASS | New metrics_service.py is a module within the existing app, not a separate service |
| IV. Docker Compose as Truth | PASS | No new containers; statement_cache_size is asyncpg config, not an external dependency |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/009-backend-performance/
├── plan.md                          # This file
├── spec.md                          # Feature specification
├── research.md                      # Phase 0: research decisions
├── data-model.md                    # Phase 1: data model changes
├── quickstart.md                    # Phase 1: implementation guide
├── contracts/
│   └── metrics-api.yaml             # Phase 1: new metrics endpoint contract
├── checklists/
│   └── requirements.md              # Specification quality checklist
└── tasks.md                         # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── config.py                    # MODIFIED: cached_property for CORS
│   ├── database.py                  # MODIFIED: statement_cache_size
│   ├── main.py                      # MODIFIED: connection pre-warming in lifespan
│   ├── models/
│   │   └── viewing_time.py          # MODIFIED: index annotation update (if needed)
│   ├── routers/
│   │   ├── admin.py                 # MODIFIED: add GET /admin/metrics endpoint
│   │   ├── parental_controls.py     # MODIFIED: cache invalidation on config update
│   │   └── viewing_time.py          # UNCHANGED (router logic stays the same)
│   ├── schemas/
│   │   └── admin.py                 # MODIFIED: add PerformanceMetricsResponse
│   ├── services/
│   │   ├── metrics_service.py       # NEW: performance counters and cache
│   │   ├── pin_service.py           # MODIFIED: asyncio.to_thread for bcrypt
│   │   └── viewing_time_service.py  # MODIFIED: joined queries, RETURNING, batch, load_only, cache
│   └── seed/                        # UNCHANGED
├── alembic/
│   └── versions/
│       └── 004_add_performance_indexes.py  # NEW: index migration
└── tests/                           # Tests for all changes
```

**Structure Decision**: Backend-only changes within the existing monolithic FastAPI application. No frontend changes. One new service module (`metrics_service.py`), one new migration, and modifications to 7 existing files.

## Complexity Tracking

No constitution violations to justify.

## Implementation Phases

### Phase 1: Unblock Event Loop (C-01) — FR-001

**Priority**: P1 (Critical — blocks concurrent operation)

**Changes**:
- `pin_service.py`: Create `_hash_pin_async()` and `_verify_pin_hash_async()` using `asyncio.to_thread()`
- Update `create_pin()`, `verify_pin()`, `reset_pin()` to await async variants

**Verification**: SC-001 — PIN operations don't block concurrent heartbeats.

### Phase 2: Optimize Heartbeat Hot Path (C-02, H-03) — FR-002, FR-003, FR-014

**Priority**: P1 (Critical — highest impact on DB load)

**Changes**:
- `viewing_time_service.py:process_heartbeat()`: Replace 3 separate lookups with single `outerjoin` query
- `viewing_time_service.py:process_heartbeat()`: Add `RETURNING` clause to balance upsert
- `viewing_time_service.py:check_playback_eligible()`: Accept optional pre-loaded profile parameter

**Verification**: SC-002 (≤3 DB ops), SC-003 (p95 < 200ms), SC-005 (index scans).

### Phase 3: Database Index (H-01) — FR-006

**Priority**: P2 (Foundational — enables other query optimizations)

**Changes**:
- New migration `004_add_performance_indexes.py`: Verify/create composite index with `CONCURRENTLY`
- `viewing_time.py`: Update model `__table_args__` if index annotation needs alignment

**Verification**: SC-005 — EXPLAIN ANALYZE shows index scan, not sequential scan.

### Phase 4: Config Cache (H-02) — FR-004, FR-005, FR-012

**Priority**: P2 (High impact, low risk)

**Changes**:
- `metrics_service.py` (new): `ConfigCache` class with TTL, bounded size, LRU eviction
- `viewing_time_service.py`: Replace `ensure_default_config()` calls with `config_cache.get()`
- `parental_controls.py:PUT /viewing-time`: Add `config_cache.invalidate(profile_id)` after config update

**Verification**: SC-006 — Config fetched from DB at most once per 60 seconds per profile.

### Phase 5: Batch Queries, Range Comparisons & Lightweight Loading (C-03, H-04, H-05) — FR-007, FR-008, FR-009

**Priority**: P2 (Report and history optimization)

**Changes**:
- `viewing_time_service.py:get_viewing_history()`: Replace `func.date()` with `datetime.combine()` range comparisons
- `viewing_time_service.py:get_weekly_report()`: Batch sessions and configs with `IN(...)` queries, using range comparisons (not `func.date()`)
- `viewing_time_service.py:get_viewing_history()`: Change `selectinload` to `joinedload(...).load_only(Title.id, Title.title)`
- `viewing_time_service.py:get_weekly_report()`: Same load_only treatment for report queries

**Verification**: SC-004 — Weekly report < 2s, fixed query count regardless of profile count.

### Phase 6: System-Level Improvements (M-01, M-06, L-05) — FR-010, FR-011

**Priority**: P3 (Low effort, marginal gains)

**Changes**:
- `config.py`: Change `@property` to `@functools.cached_property` on `cors_origin_list`
- `database.py`: Add `connect_args={"statement_cache_size": 100}`
- `main.py:lifespan()`: Add startup connection pre-warming (execute `SELECT 1`)

**Verification**: SC-008 — No cold-start connection delay.

### Phase 7: Observability (FR-015, FR-016) — SC-009

**Priority**: P2 (Required for production verification)

**Changes**:
- `metrics_service.py`: Add `PerformanceMetrics` counter class
- `viewing_time_service.py:process_heartbeat()`: Instrument with timing and DB op counting
- `viewing_time_service.py`: Add structured log lines for cache events
- `admin.py`: Add `GET /api/v1/admin/metrics` endpoint
- `schemas/admin.py`: Add `PerformanceMetricsResponse` Pydantic model

**Verification**: SC-009 — Metrics visible via admin endpoint after deployment.

## Risk Mitigation

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Joined query changes heartbeat behavior subtly | Medium | Comprehensive test suite comparing before/after responses |
| RETURNING clause syntax differs across SQLAlchemy versions | Low | Research confirmed SQLAlchemy 2.0+ supports it natively |
| Config cache staleness causes enforcement issues | Low | 60s TTL + explicit invalidation on update; max 60s stale data |
| Index migration locks table under load | Low | Use CONCURRENTLY flag; test on staging first |
| asyncio.to_thread thread pool exhaustion under PIN load | Very Low | Default thread pool is 40+ threads; PIN ops are infrequent |
