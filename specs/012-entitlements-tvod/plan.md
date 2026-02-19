# Implementation Plan: Subscription Tiers, Entitlements & TVOD

**Branch**: `012-entitlements-tvod` | **Date**: 2026-02-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/012-entitlements-tvod/spec.md`

---

## Summary

Activate the platform's monetization model by enforcing subscription-based content access (SVOD), introducing per-title transactional rent/buy (TVOD), surfacing access options in catalog responses, and adding concurrent stream limit enforcement. The data models for entitlements and packages already exist — this feature wires them up, extends the schema with one new table (`title_offers`) and a new model (`ViewingSession`), and adds rate limiting via `slowapi`.

---

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5+ / React 18 (frontend-admin)
**Primary Dependencies**: FastAPI 0.115+, SQLAlchemy 2.0+ async, Alembic 1.14+, slowapi (new), redis.asyncio 5.2+ (existing)
**Storage**: PostgreSQL 16 (primary), Redis 7 (rate limiting state + entitlement cache)
**Testing**: pytest + pytest-asyncio (existing pattern in codebase)
**Target Platform**: Linux container (Docker Compose), accessed via browser/admin panel
**Project Type**: Web application — backend API + admin React frontend
**Performance Goals**: 500 concurrent entitlement checks, TVOD transaction < 5s, catalog response unchanged
**Constraints**: Fail-closed on entitlement service failure (5-min cache for in-progress sessions), first-write-wins on concurrent stream slot race
**Scale/Scope**: PoC — ~100 test users, no horizontal scaling required

---

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. PoC-First Quality | ⚠️ Partial | Two justified violations — see below |
| II. Monolithic Simplicity | ✅ Pass | All new code in single FastAPI app; new routers extend existing pattern |
| III. AI-Native by Default | ⚠️ Partial | Justified exception — see below |
| IV. Docker Compose as Truth | ✅ Pass | Redis already in compose; no new services |
| V. Seed Data as Demo | ✅ Pass | New seed_entitlements.py with 2 packages, 110+ title assignments, sample offers |

**Constitution violations (all justified)**:
1. **Rate limiting (`slowapi`)** — excluded from PoC by constitution ("skip rate limiting"). Justified: `slowapi` adds < 30 LOC to `main.py` and is required by FR-024/FR-025 (TVOD transaction abuse prevention, X-03 in roadmap).
2. **Entitlement result caching (Redis)** — excluded from PoC by constitution ("skip advanced caching"). Justified: required by FR-021 (fail-closed safety — deny new sessions when entitlement service is unavailable) and SC-008 (platform must handle 500 concurrent entitlement checks). Redis is already in the Docker Compose stack; this adds only a `redis.asyncio` key-value read/write, not a new caching layer.
3. **Principle III (AI-Native by Default)** — constitution requires every feature to include its AI-enhanced variant. Entitlements enforcement is pure infrastructure — there is no meaningful AI variant that would not constitute a separate feature (e.g., ML-based fraud detection, personalised paywall messaging). This feature enables downstream AI (SVOD-filtered recommendation rails exclude unentitled titles for non-subscribers) but does not incorporate AI itself. Justified exception: the entitlement data model created here is the prerequisite for AI-aware content access in the recommendations and EPG features.

---

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| Rate limiting (constitution says skip) | FR-024/025 explicitly required; X-03 in roadmap | No simpler mechanism protects TVOD endpoints from abuse; no-op limiter would require reverting in next sprint |
| Redis entitlement caching (constitution says skip advanced caching) | FR-021 requires fail-closed safety with grace period for in-progress sessions; SC-008 requires 500 concurrent checks | In-process dict cache doesn't survive process restart and can't be invalidated across workers; no caching fails SC-008 and violates the 5-min in-progress session grace requirement |

---

## Project Structure

### Documentation (this feature)

```text
specs/012-entitlements-tvod/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 — slowapi, Redis caching, session cleanup patterns
├── data-model.md        # Phase 1 — schema changes and new tables
├── quickstart.md        # Phase 1 — manual test flows
├── contracts/
│   └── api-contracts.md # Phase 1 — all endpoint contracts
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── alembic/versions/
│   └── 005_subscription_entitlements_tvod.py   [NEW]
├── app/
│   ├── models/
│   │   ├── entitlement.py   [MODIFIED — add TitleOffer, extend UserEntitlement + ContentPackage]
│   │   └── viewing.py       [MODIFIED — add ViewingSession model]
│   ├── routers/
│   │   ├── admin.py         [MODIFIED — add package CRUD, offer CRUD, user tier PATCH]
│   │   ├── catalog.py       [MODIFIED — add access_options to responses, optional auth]
│   │   ├── offers.py        [NEW — TVOD purchase endpoint]
│   │   └── viewing.py       [MODIFIED — add session start/heartbeat/stop/list endpoints]
│   ├── schemas/
│   │   ├── entitlement.py   [NEW — package, offer, entitlement, session schemas]
│   │   └── catalog.py       [MODIFIED — add AccessOption, UserAccess to title responses]
│   ├── services/
│   │   └── entitlement_service.py  [NEW — access check, TVOD, stream limits, cache]
│   ├── seed/
│   │   ├── seed_entitlements.py    [NEW]
│   │   └── run_seeds.py            [MODIFIED — call seed_entitlements]
│   └── main.py              [MODIFIED — add offers router, slowapi middleware + Redis init]
└── pyproject.toml           [MODIFIED — add slowapi]
```

---

## Implementation Phases

### Phase A — Foundation (no dependencies between tasks)

**A1: Database Migration**
File: `backend/alembic/versions/005_subscription_entitlements_tvod.py`

```python
# Upgrade operations:
# 1. CREATE TABLE title_offers (id, title_id FK, offer_type, price_cents, currency,
#    rental_window_hours, is_active, created_at)
#    + partial unique index: (title_id, offer_type) WHERE is_active = TRUE
#    + index: (title_id, is_active)
# 2. CREATE TABLE viewing_sessions (id, user_id FK, title_id FK nullable,
#    content_type, started_at, last_heartbeat_at, ended_at nullable)
#    + index: (user_id, ended_at)
# 3. ALTER TABLE user_entitlements ALTER COLUMN package_id DROP NOT NULL
# 4. ALTER TABLE user_entitlements ADD COLUMN title_id UUID REFERENCES titles(id)
#    + index: (user_id, title_id, expires_at) WHERE title_id IS NOT NULL
# 5. ALTER TABLE content_packages ADD COLUMN tier VARCHAR(20)
```

**A2: Model Updates**
File: `backend/app/models/entitlement.py`
- Add `TitleOffer` SQLAlchemy model (mapped to `title_offers` table)
- Modify `UserEntitlement`: make `package_id` Optional, add `title_id` Optional
- Modify `ContentPackage`: add `tier` Optional[str]

File: `backend/app/models/viewing.py`
- Add `ViewingSession` SQLAlchemy model (mapped to `viewing_sessions` table)

**A3: New Schemas**
File: `backend/app/schemas/entitlement.py` (new file)
- `PackageCreate`, `PackageUpdate`, `PackageResponse`
- `OfferCreate`, `OfferUpdate`, `OfferResponse`
- `TVODPurchaseRequest`, `TVODPurchaseResponse`
- `SessionStartRequest`, `SessionResponse`, `SessionListResponse`
- `UserSubscriptionUpdate`

File: `backend/app/schemas/catalog.py` (modify)
- Add `AccessOption` (type, price_cents, currency, rental_window_hours)
- Add `UserAccess` (has_access, access_type, expires_at)
- Add `access_options: list[AccessOption]` and `user_access: UserAccess | None` to `TitleResponse`

**A4: Add slowapi + Redis to main.py**
File: `backend/app/main.py`
- Add `get_user_or_ip()` key function (sync JWT decode using existing `python-jose`)
- Initialize `Limiter` with `storage_uri=settings.redis_url`, `default_limits=["100/minute"]`
- Register `RateLimitExceeded` exception handler (returns 429 with `Retry-After` header)
- Add `SlowAPIMiddleware`
- Initialize `redis.asyncio` client in `lifespan`, store on `app.state.redis`
- Register `offers` router at `/api/v1/catalog`

File: `backend/pyproject.toml`
- Add `slowapi` dependency

File: `backend/app/dependencies.py`
- Add `get_redis()` dependency function
- Add `RedisClient` annotated type

---

### Phase B — Core Service (depends on A1, A2)

**B1: Entitlement Service**
File: `backend/app/services/entitlement_service.py` (new file)

Functions:
- `check_access(user_id, title_id, db, redis) -> bool` — union check across SVOD + TVOD + free offers
- `check_access_cached(user_id, title_id, db, redis) -> bool` — wraps check_access with Redis caching (300s TTL, fail-closed)
- `get_access_options(title_id, user_id_or_none, db, redis) -> list[AccessOption]` — for catalog responses
- `create_tvod_entitlement(user_id, title_id, offer_type, db, redis) -> UserEntitlement` — validates no duplicate, creates entitlement, invalidates cache
- `check_stream_limit(user_id, db) -> tuple[bool, list[Session]]` — cleans abandoned sessions then checks count vs tier limit
- `invalidate_entitlement_cache(user_id, redis)` — delete `ent:{user_id}:*` keys

**B2: Admin Package + Offer CRUD**
File: `backend/app/routers/admin.py` (extend)

New endpoints (all behind `AdminUser` dependency):
- `GET /admin/packages` — list all packages
- `POST /admin/packages` — create package
- `PUT /admin/packages/{package_id}` — update package
- `DELETE /admin/packages/{package_id}` — delete package (check for active entitlements first)
- `POST /admin/packages/{package_id}/titles` — assign title
- `DELETE /admin/packages/{package_id}/titles/{title_id}` — remove title
- `GET /admin/titles/{title_id}/offers` — list offers
- `POST /admin/titles/{title_id}/offers` — create offer (enforce one-active-per-type)
- `PATCH /admin/titles/{title_id}/offers/{offer_id}` — update/deactivate offer
- `PATCH /admin/users/{user_id}/subscription` — update user tier + entitlement, invalidate cache

---

### Phase C — User-Facing (depends on B1)

**C1: Catalog Access Options**
File: `backend/app/routers/catalog.py` (modify)

Changes:
- Make auth optional (use `HTTPBearer(auto_error=False)`)
- In title list + detail responses, call `entitlement_service.get_access_options(title_id, user_id_or_none, db, redis)`
- Titles with no offers and no package assignment are filtered from public catalog (FR-007 + Story 2 scenario 4)
- For authenticated users, include `user_access` field

**C2: TVOD Purchase Endpoint**
File: `backend/app/routers/offers.py` (new file)

- `POST /catalog/titles/{title_id}/purchase` — requires auth, stricter rate limit (`@limiter.limit("10/hour")`)
- Validates offer exists and is active
- Calls `entitlement_service.create_tvod_entitlement()`
- Returns entitlement with `expires_at`

**C3: Viewing Session Endpoints**
File: `backend/app/routers/viewing.py` (extend existing file)

New endpoints:
- `POST /viewing/sessions` — checks entitlement (cached), checks stream limit, creates session; returns 403 if no entitlement, 429 with active sessions if over limit
- `PUT /viewing/sessions/{session_id}/heartbeat` — updates `last_heartbeat_at`
- `DELETE /viewing/sessions/{session_id}` — sets `ended_at`, invalidates stream slot
- `GET /viewing/sessions` — returns active sessions for current user

---

### Phase D — Seed Data (depends on A1, A2)

**D1: Entitlement Seed Script**
File: `backend/app/seed/seed_entitlements.py` (new file)

Creates:
- Package "Basic" (tier=basic) with 30 titles
- Package "Premium" (tier=premium) with 80 titles (superset of Basic)
- Rental offer ($3.99/48h) on 20 titles
- Buy offer ($9.99) on same 20 titles
- 1 free offer on 5 titles (open access demo)
- UserEntitlement for `basic@test.com` → Basic package
- UserEntitlement for `premium@test.com` → Premium package
- `noplan@test.com` gets no subscription entitlement
- Stream limit config: Basic = 1 stream, Premium = 3 streams (stored in ContentPackage or config)

File: `backend/app/seed/run_seeds.py` (modify)
- Import and call `seed_entitlements.run()`

---

## Stream Limit Configuration

Stream limits per subscription tier are stored in the `ContentPackage` model via a `max_streams` integer field. This field is added in migration 005 as well.

| Package Tier | `max_streams` |
|---|---|
| free / no subscription | 0 (no streaming without entitlement) |
| basic | 1 |
| premium | 3 |

The entitlement service derives the user's stream limit from the most permissive active package entitlement.

---

## Constitution Check — Post-Design

| Principle | Post-Design Status |
|-----------|-------------------|
| I. PoC-First Quality | Two justified violations documented — `slowapi` (rate limiting) + Redis entitlement caching |
| II. Monolithic Simplicity | ✅ All within single FastAPI app; 1 new router file |
| III. AI-Native | ⚠️ Justified exception — pure infrastructure feature; enables downstream AI; see violations section |
| IV. Docker Compose | ✅ No new containers |
| V. Seed Data | ✅ Comprehensive seed: 2 packages, 110+ assignments, offers, test users |

## Admin Frontend Scope

**Decision**: Backend API only. No new admin React frontend components are required for this feature.

**Rationale**: The existing admin panel has a generic API client that surfaces all backend endpoints via the OpenAPI spec (`/docs`). Admins can perform all package management, offer management, and user subscription updates through the Swagger UI during the PoC phase. This satisfies SC-006 ("admin can complete operations in under 3 minutes") without new frontend code — navigating Swagger UI for package creation, title assignment, and user tier update takes well under 3 minutes for a PoC demonstration.

**Frontend work deferred to**: A future "Admin Package Management UI" feature that wraps these endpoints in a purpose-built React interface with forms and data tables.

---

## Key Dependencies Between Tasks

```
A1 (migration) ──────────┬──► B1 (service)
A2 (models)   ───────────┘
A3 (schemas)  ───────────────► B2 (admin CRUD)
A4 (main.py)  ───────────┐
                          ├──► C1 (catalog access options)
B1 (service)  ───────────┤──► C2 (TVOD purchase)
                          └──► C3 (session endpoints)
A1 + A2       ───────────────► D1 (seed data)
```

A1–A4 can all be worked in parallel. B1 and B2 can start once A1+A2 are done. C1–C3 require B1. D1 requires A1+A2 but is independent of B and C.

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| `slowapi` sync key function can't call async DB | Extract user_id from JWT token synchronously (python-jose is sync); no DB call needed in key function |
| Race condition on "last available stream slot" | First-write-wins: use atomic UPDATE + SELECT COUNT within a single DB transaction |
| Redis unavailable at startup | Graceful: `redis.asyncio.from_url()` with `socket_connect_timeout`; fail-closed logic catches connection errors |
| Migration 005 breaks existing UserEntitlement FK | Make `package_id` nullable with `ALTER COLUMN ... DROP NOT NULL` — existing rows unaffected |
| Admin `DELETE /packages` with active user entitlements | Service checks for active entitlements and returns 409 before deleting |
