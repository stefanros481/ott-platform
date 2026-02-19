# Tasks: Subscription Tiers, Entitlements & TVOD

**Input**: Design documents from `/specs/012-entitlements-tvod/`
**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ contracts/ ✅ quickstart.md ✅

**Organization**: Tasks grouped by user story. Each story is independently implementable and testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no shared state dependencies)
- **[Story]**: Which user story this implements (US1–US6)
- All paths relative to repo root

---

## Phase 1: Setup

**Purpose**: Install new dependency before any implementation begins.

- [X] T001 Add `slowapi` to `backend/pyproject.toml` via `uv add slowapi`

**Checkpoint**: `backend/pyproject.toml` contains `slowapi`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Database schema, models, schemas, service layer, and infrastructure wiring that ALL user stories depend on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 Write migration `backend/alembic/versions/005_subscription_entitlements_tvod.py` — CREATE TABLE `title_offers` (id, title_id FK CASCADE, offer_type CHECK IN ('rent','buy','free'), price_cents, currency, rental_window_hours nullable, is_active, created_at) with partial unique index `(title_id, offer_type) WHERE is_active`; CREATE TABLE `viewing_sessions` (id, user_id FK CASCADE, title_id FK SET NULL nullable, content_type, started_at, last_heartbeat_at, ended_at nullable) with index `(user_id, ended_at)`; ALTER TABLE `user_entitlements` DROP NOT NULL on `package_id`, ADD COLUMN `title_id UUID REFERENCES titles(id) ON DELETE CASCADE`, CREATE INDEX `(user_id, title_id, expires_at) WHERE title_id IS NOT NULL`; ALTER TABLE `content_packages` ADD COLUMN `tier VARCHAR(20)`, ADD COLUMN `max_streams INTEGER NOT NULL DEFAULT 0`
- [X] T003 [P] Update `backend/app/models/entitlement.py` — add `TitleOffer` SQLAlchemy model mapped to `title_offers`; make `UserEntitlement.package_id` Optional (nullable); add `title_id: Optional[UUID]` FK to `UserEntitlement`; add `tier: Optional[str]` and `max_streams: int` fields to `ContentPackage`
- [X] T004 [P] Add `ViewingSession` SQLAlchemy model to `backend/app/models/viewing.py` — fields: id (UUID PK), user_id (FK users.id CASCADE), title_id (FK titles.id SET NULL, nullable), content_type (str, default 'vod_title'), started_at (timestamptz server default), last_heartbeat_at (timestamptz server default), ended_at (timestamptz nullable)
- [X] T005 [P] Create `backend/app/schemas/entitlement.py` — Pydantic v2 models: `PackageCreate` (name, description, tier), `PackageUpdate` (all optional), `PackageResponse` (+ id, title_count); `OfferCreate` (offer_type, price_cents, currency, rental_window_hours), `OfferUpdate` (all optional), `OfferResponse` (+ id, is_active, created_at); `TVODPurchaseRequest` (offer_type), `TVODPurchaseResponse` (entitlement_id, title_id, offer_type, expires_at, price_cents, currency); `SessionStartRequest` (title_id, content_type), `SessionResponse` (session_id, started_at), `SessionListResponse` (session_id, title_id, title_name, started_at, last_heartbeat_at); `UserSubscriptionUpdate` (package_id nullable, expires_at nullable)
- [X] T006 [P] Extend `backend/app/schemas/catalog.py` — add `AccessOption` (type: str, label: str, price_cents: int | None, currency: str | None, rental_window_hours: int | None); add `UserAccess` (has_access: bool, access_type: str | None, expires_at: datetime | None); add `access_options: list[AccessOption] = []` and `user_access: UserAccess | None = None` to `TitleResponse`
- [X] T007 Add slowapi + Redis initialization to `backend/app/main.py` — implement sync `get_user_or_ip(request)` key function (decode JWT via python-jose, fall back to remote address); instantiate `Limiter(key_func=get_user_or_ip, storage_uri=settings.redis_url, default_limits=["100/minute"])`; add `app.state.limiter = limiter`; register `RateLimitExceeded` exception handler returning 429 JSON with `retry_after`; add `SlowAPIMiddleware`; initialize `redis.asyncio.from_url(settings.redis_url, decode_responses=True)` in lifespan context manager stored as `app.state.redis`, closed on shutdown
- [X] T008 [P] Add `get_redis()` async dependency function and `RedisClient = Annotated[redis.asyncio.Redis, Depends(get_redis)]` type alias to `backend/app/dependencies.py`
- [X] T009 Create `backend/app/services/entitlement_service.py` with all six functions: (1) `check_access(user_id, title_id, db, redis) -> bool` — union check: SVOD package membership OR TVOD rental (not expired) OR TVOD purchase OR free offer (direct `TitleOffer` lookup — no `UserEntitlement` row required for free access); free offer access is checked via `TitleOffer(offer_type='free', is_active=True)` and `create_tvod_entitlement` must reject `offer_type='free'` with a 422 (free titles are accessed directly, not purchased); (2) `check_access_cached(user_id, title_id, db, redis) -> bool` — wrap check_access with Redis key `ent:{user_id}:{title_id}`, **TTL = `min(300, seconds_until_expires_at)` for TVOD rental entitlements** (to satisfy SC-003: expired rentals become inaccessible within 60s), TTL 300s for SVOD and TVOD purchase (no expiry), fail-closed on both Redis and DB errors; (3) `get_access_options(title_id, user_id_or_none, db, redis) -> tuple[list[AccessOption], UserAccess | None]` — fetch active TitleOffers for title (one DB query); if authenticated, fetch user's active UserEntitlements covering this title via direct DB query (uses migration 005 indexes: `(user_id, title_id, expires_at)` for TVOD, package membership join for SVOD); **does not use Redis cache** — returns richer data (access_type, expires_at) than check_access_cached's bool, and two indexed DB queries per title satisfies SC-008 at PoC scale; return structured options; (4) `create_tvod_entitlement(user_id, title_id, offer_type, db, redis) -> UserEntitlement` — validate active offer exists, check no duplicate active entitlement of same type, create `UserEntitlement(source_type='tvod', title_id=title_id, expires_at=now()+rental_window if rent else None)`, call invalidate_entitlement_cache; (5) `check_stream_limit(user_id, db) -> tuple[bool, list[ViewingSession]]` — atomically expire abandoned sessions (last_heartbeat_at < now()-5min), count active sessions, compare against user's package max_streams; (6) `invalidate_entitlement_cache(user_id, redis)` — delete all keys matching `ent:{user_id}:*`

**Checkpoint**: Migration written, models updated, schemas created, service layer complete. User story implementation can now begin.

---

## Phase 3: User Story 1 — Subscription Content Access Enforcement (Priority: P1) 🎯 MVP

**Goal**: Subscribers can play titles in their package; non-subscribers are denied with upgrade options.

**Independent Test**: `POST /api/v1/viewing/sessions` as `basic@test.com` with a Basic-package title → 201. Same endpoint with a Premium-only title → 403 with `access_options`.

- [X] T010 [US1] Add `POST /viewing/sessions` endpoint to `backend/app/routers/viewing.py` — require auth (existing `CurrentUser` dep), require `RedisClient` dep; call `check_access_cached(user.id, title_id, db, redis)` → if False return 403 JSON `{detail, access_options}` using `get_access_options`; if True create `ViewingSession` record (set started_at, last_heartbeat_at to now(), ended_at=None); return 201 `SessionResponse(session_id, started_at)`; on any exception during access check deny access and log the error (fail-closed per FR-021)

**Checkpoint**: User Story 1 complete — subscription access is enforced at playback start. **Note**: concurrent stream limit enforcement is added in Phase 8 (T020). When testing US1 in isolation, a single user may open unlimited concurrent sessions — this is expected and by design for MVP delivery.

---

## Phase 4: User Story 2 — View Access Options in Catalog (Priority: P2)

**Goal**: Every catalog response includes structured access options; guest users see pricing; authenticated users see their entitlement status.

**Independent Test**: GET `/api/v1/catalog/titles` with no auth → titles include `access_options`, no `user_access`. Same endpoint as `basic@test.com` → `user_access.has_access=true` for Basic-package titles.

- [X] T011 [US2] Modify `GET /catalog/titles` in `backend/app/routers/catalog.py` — change auth to optional (`HTTPBearer(auto_error=False)`); for each title call `get_access_options(title_id, user_id_or_none, db, redis)`; attach `access_options` and `user_access` (None if unauthenticated) to each item; exclude titles where both `access_options` is empty and no package assignment exists (FR-007 / US2 scenario 4) from unauthenticated responses
- [X] T012 [US2] Modify `GET /catalog/titles/{title_id}` in `backend/app/routers/catalog.py` — same optional auth pattern; add `access_options` and `user_access` to single-title response; return 404 if title has no offers and no package assignment (for unauthenticated requests)

**Checkpoint**: User Story 2 complete — catalog surfaces access options for all titles.

---

## Phase 5: User Story 3 — Rent a Title (TVOD) (Priority: P3)

**Goal**: A user can rent a title, creating a time-limited entitlement; playback is immediately available.

**Independent Test**: POST `/api/v1/catalog/titles/{id}/purchase` with `{"offer_type": "rent"}` as `noplan@test.com` → 201 with `expires_at` ~48h from now. Subsequent `POST /viewing/sessions` for same title → 201.

- [X] T013 [US3] Create `backend/app/routers/offers.py` — implement `POST /catalog/titles/{title_id}/purchase` endpoint: require auth; apply `@limiter.limit("10/hour")`; accept `TVODPurchaseRequest(offer_type: Literal['rent', 'buy'])` (reject 'free' with 422 — free titles are accessed directly, not purchased); validate active offer of requested type exists (404 if not); call `create_tvod_entitlement(user_id, title_id, offer_type, db, redis)`; return 201 `TVODPurchaseResponse`; return 409 if user already has active entitlement of same type; return 429 on rate limit exceeded; **device-independence is inherent** — entitlements are scoped to `user_id`, not device_id; any authenticated request from any device passes the entitlement check (FR-016)
- [X] T014 [US3] Register offers router in `backend/app/main.py` — `app.include_router(offers_router, prefix="/api/v1/catalog")`

**Checkpoint**: User Story 3 complete — rental transactions create time-limited entitlements.

---

## Phase 6: User Story 4 — Buy a Title (TVOD) (Priority: P4)

**Goal**: A user can permanently purchase a title; access persists indefinitely regardless of subscription status.

**Independent Test**: POST purchase with `{"offer_type": "buy"}` → 201 with `expires_at: null`. Cancel subscription (remove entitlement). GET catalog title → `user_access.access_type = "tvod_buy"`, `has_access = true`.

- [X] T015 [US4] Extend `get_access_options` in `backend/app/services/entitlement_service.py` — when user has an active TVOD buy entitlement: set `user_access.access_type = "tvod_buy"` and `expires_at = null`; suppress `rent` option in access_options (FR-015: don't offer rent when title already owned); when user has an active rental: set `access_type = "tvod_rent"`, include `expires_at`; suppress duplicate rent offer if rental already active

**Checkpoint**: User Story 4 complete — buy creates permanent entitlements, catalog shows owned/rented status correctly.

---

## Phase 7: User Story 5 — Admin Manages Subscription Packages (Priority: P5)

**Goal**: Admins can create packages, assign titles, manage offers, and update user subscriptions via the admin API.

**Independent Test**: Admin creates a package, assigns 3 titles, PATCHes `basic@test.com` to that package. `basic@test.com` can now play those titles.

- [X] T016 [US5] Add package CRUD to `backend/app/routers/admin.py` — `GET /admin/packages` (list all with title_count), `POST /admin/packages` (create, 201), `PUT /admin/packages/{package_id}` (update name/description/tier, 404 if not found), `DELETE /admin/packages/{package_id}` (409 if active user entitlements exist, else 204); all behind existing `AdminUser` dependency
- [X] T017 [US5] Add title-assignment endpoints to `backend/app/routers/admin.py` — `POST /admin/packages/{package_id}/titles` (body: `{title_id}`, create PackageContent, 409 if already assigned), `DELETE /admin/packages/{package_id}/titles/{title_id}` (404 if not found, 204)
- [X] T018 [US5] Add offer CRUD to `backend/app/routers/admin.py` — `GET /admin/titles/{title_id}/offers` (list all including inactive), `POST /admin/titles/{title_id}/offers` (create TitleOffer, 409 if active offer of same type already exists, 201), `PATCH /admin/titles/{title_id}/offers/{offer_id}` (partial update price/is_active, 200)
- [X] T019 [US5] Add user subscription update to `backend/app/routers/admin.py` — `PATCH /admin/users/{user_id}/subscription` (body: `UserSubscriptionUpdate`); deactivate existing SVOD UserEntitlement for user; if package_id non-null, create new UserEntitlement(source_type='subscription', package_id, expires_at); call `invalidate_entitlement_cache(user_id, redis)`; update `User.subscription_tier` to match package tier; return 200 with updated subscription summary; **Note on invalidation**: `invalidate_entitlement_cache` uses Redis `SCAN + DELETE` — there is a ~100ms consistency window between cursor advances where a concurrent check could read a stale key; for PoC this is acceptable (SC-002 requires 10s, not 100ms); at production scale replace with a Lua script for atomic scan-and-delete

**Checkpoint**: User Story 5 complete — admins can fully manage packages, offers, and user tiers.

---

## Phase 8: User Story 6 — Concurrent Stream Limit Enforcement (Priority: P6)

**Goal**: Users cannot exceed their plan's stream limit; abandoned sessions auto-expire after 5 minutes.

**Independent Test**: `basic@test.com` (max_streams=1) starts Session A → 201. Starts Session B → 429 with `active_sessions`. DELETE Session A → 204. Start Session B → 201.

- [X] T020 [US6] Extend `POST /viewing/sessions` in `backend/app/routers/viewing.py` — after entitlement check (T010), call `check_stream_limit(user_id, db)`; if over limit return 429 JSON `{detail: "Concurrent stream limit reached", limit: N, active_sessions: [...]}` with session summaries (session_id, title_name, started_at); only create ViewingSession if both checks pass (first-write-wins: wrap count + insert in a single DB transaction to prevent race condition)
- [X] T021 [US6] Add `PUT /viewing/sessions/{session_id}/heartbeat` to `backend/app/routers/viewing.py` — require auth; verify session belongs to current user and ended_at IS NULL; update `last_heartbeat_at = now()`; return 200 `{last_heartbeat_at}`; return 404 if session not found or already ended
- [X] T022 [US6] Add `DELETE /viewing/sessions/{session_id}` to `backend/app/routers/viewing.py` — require auth; verify session belongs to current user; set `ended_at = now()`; return 204; return 404 if not found
- [X] T023 [US6] Add `GET /viewing/sessions` to `backend/app/routers/viewing.py` — require auth; return all sessions for current user where ended_at IS NULL; join title name; return 200 `list[SessionListResponse]`

**Checkpoint**: User Story 6 complete — stream limits enforced, heartbeat/stop/list endpoints operational.

---

## Phase 9: Polish & Cross-Cutting Concerns

- [X] T024 [P] Create `backend/app/seed/seed_entitlements.py` — idempotent seed function: create ContentPackage "Basic" (tier='basic', max_streams=1) and "Premium" (tier='premium', max_streams=3); assign first 30 titles to Basic, first 80 to Premium (superset); add TitleOffer rent ($3.99/48h) + buy ($9.99) on 20 titles; add TitleOffer free (price=0) on 5 titles; create UserEntitlement (SVOD) for `basic@test.com` → Basic, `premium@test.com` → Premium; `noplan@test.com` gets no SVOD entitlement; skip if packages already exist
- [X] T025 Update `backend/app/seed/run_seeds.py` to import and call `seed_entitlements.run()`
- [X] T026 [P] Run quickstart.md manual test flows end-to-end: apply migration 005, run seeds, execute all 5 curl test scenarios (SVOD enforcement, TVOD rental, stream limits, guest catalog, admin package management), verify rate limit 429 on 101st request — validates SC-001 (100% enforcement), SC-002 (10s update propagation), SC-003 (rental expiry), SC-004 (accurate access options), SC-005 (stream limits), and SC-007 (TVOD transaction < 5s)

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)         → no dependencies
Phase 2 (Foundational)  → depends on Phase 1 (T001 must complete before T007)
Phase 3 (US1)           → depends on Phase 2
Phase 4 (US2)           → depends on Phase 2
Phase 5 (US3)           → depends on Phase 2
Phase 6 (US4)           → depends on Phase 5 (extends create_tvod_entitlement)
Phase 7 (US5)           → depends on Phase 2
Phase 8 (US6)           → depends on Phase 3 (extends POST /viewing/sessions)
Phase 9 (Polish)        → depends on Phases 3–8 all complete
```

### User Story Dependencies

- **US1 (P1)**: Start after Foundational — no dependency on other stories
- **US2 (P2)**: Start after Foundational — independent of US1
- **US3 (P3)**: Start after Foundational — independent of US1/US2
- **US4 (P4)**: Start after US3 (extends service logic from T009 and router from T013)
- **US5 (P5)**: Start after Foundational — independent of US1–US4
- **US6 (P6)**: Start after US1 (extends the POST /viewing/sessions endpoint from T010)

### Within Phase 2 (Parallel Opportunities)

```
T001                    # Install dep first
  └─ T002 [start]       # migration (parallel with T003-T008)
  └─ T003 [P]           # models/entitlement.py
  └─ T004 [P]           # models/viewing.py
  └─ T005 [P]           # schemas/entitlement.py
  └─ T006 [P]           # schemas/catalog.py
  └─ T007               # main.py (depends on T001)
  └─ T008 [P]           # dependencies.py
       └─ T009          # service (depends on T003, T004, T005, T006 completing first)
```

---

## Parallel Execution Example: Phase 2

```bash
# After T001 completes, launch in parallel:
Task: "Write migration 005 in backend/alembic/versions/005_subscription_entitlements_tvod.py"
Task: "Update backend/app/models/entitlement.py - add TitleOffer, extend UserEntitlement, extend ContentPackage"
Task: "Add ViewingSession model to backend/app/models/viewing.py"
Task: "Create backend/app/schemas/entitlement.py with all request/response schemas"
Task: "Extend backend/app/schemas/catalog.py with AccessOption and UserAccess"
Task: "Add slowapi + Redis init to backend/app/main.py"
Task: "Add get_redis() to backend/app/dependencies.py"

# After all above complete:
Task: "Create backend/app/services/entitlement_service.py with all 6 functions"
```

## Parallel Execution Example: User Stories (after Phase 2)

```bash
# US1, US2, US3, US5 can all start simultaneously after Phase 2:
Task: "T010 - POST /viewing/sessions with entitlement check [US1]"
Task: "T011 - Modify GET /catalog/titles with access options [US2]"
Task: "T013 - Create offers.py with purchase endpoint [US3]"
Task: "T016 - Add package CRUD to admin.py [US5]"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002–T009) — CRITICAL
3. Complete Phase 3: US1 (T010)
4. **STOP and VALIDATE**: Run quickstart.md SVOD enforcement flow
5. Database has migration applied, seed data runs, entitlement check works

### Incremental Delivery

| Step | Tasks | Validates |
|------|-------|-----------|
| Foundation | T001–T009 | Migration applies, service layer tests pass |
| +US1 | T010 | Subscription enforcement works end-to-end |
| +US2 | T011–T012 | Catalog shows access options with correct entitlement status |
| +US3 | T013–T014 | TVOD rental creates time-limited entitlements |
| +US4 | T015 | Buy flow creates permanent entitlements, owned status shown |
| +US5 | T016–T019 | Admin can manage packages, offers, and user tiers |
| +US6 | T020–T023 | Stream limits enforced, heartbeat/stop/list operational |
| Polish | T024–T026 | Seed data ready, all quickstart flows pass |

---

## Summary

| Metric | Count |
|--------|-------|
| Total tasks | 26 |
| Phase 1 (Setup) | 1 |
| Phase 2 (Foundational) | 8 |
| US1 tasks | 1 |
| US2 tasks | 2 |
| US3 tasks | 2 |
| US4 tasks | 1 |
| US5 tasks | 4 |
| US6 tasks | 4 |
| Polish tasks | 3 |
| Parallelizable [P] tasks | 8 |

**MVP scope**: T001–T010 (9 tasks) — complete subscription enforcement with full foundation.
