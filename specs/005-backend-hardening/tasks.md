# Tasks: Backend Hardening for Production Readiness

**Input**: Design documents from `/specs/005-backend-hardening/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Not included — test suite creation is a separate feature (out of scope per spec).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: No project setup needed — this is a hardening feature on an existing codebase.

*All infrastructure, dependencies, and project structure already exist. Proceed directly to user stories.*

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No blocking foundational work required. Each user story is self-contained. Shared files (config.py, dependencies.py, main.py) are edited by multiple stories in non-overlapping sections, coordinated via execution order.

**Checkpoint**: Proceed to user stories immediately.

---

## Phase 3: User Story 1 - Secure Authentication Credentials (Priority: P1)

**Goal**: Remove the hardcoded JWT secret default, use SecretStr to prevent accidental exposure, and validate minimum secret length at startup.

**Independent Test**: Start the application without JWT_SECRET env var — it must fail. Start with a short secret — it must fail. Start with a valid 32+ char secret — it must succeed. The secret must never appear in logs or repr.

### Implementation for User Story 1

- [x] T001 [US1] Change `jwt_secret` from `str` with default to `SecretStr` without default, import SecretStr from pydantic in `backend/app/config.py`
- [x] T002 [US1] Update `decode_token()` to use `settings.jwt_secret.get_secret_value()` instead of `settings.jwt_secret` in `backend/app/dependencies.py`
- [x] T003 [US1] Add JWT secret length validation (>= 32 chars) in the lifespan handler, exit with clear error message if invalid, in `backend/app/main.py`
- [x] T004 [US1] Replace hardcoded `JWT_SECRET` value with env var substitution `${JWT_SECRET:?Set JWT_SECRET env var with at least 32 characters}` in `docker/docker-compose.yml`

**Checkpoint**: Application refuses to start without JWT_SECRET or with a secret under 32 characters. Authentication works normally with a valid secret. Secret is never visible in logs.

---

## Phase 4: User Story 2 - Profile Ownership Enforcement (Priority: P1)

**Goal**: Create VerifiedProfileId and OptionalVerifiedProfileId dependencies that validate Profile.user_id == authenticated User.id, then apply to all 22 profile-scoped endpoints.

**Independent Test**: Log in as User A, request User B's bookmarks/watchlist/ratings — should get 403. Request with own profile — should succeed. Request with non-existent profile — should get 403 (not 404).

### Implementation for User Story 2

- [x] T005 [US2] Create `get_verified_profile_id()` and `get_optional_verified_profile_id()` dependency functions and their `VerifiedProfileId` / `OptionalVerifiedProfileId` type aliases in `backend/app/dependencies.py`. Query Profile where `id == profile_id AND user_id == user.id`, raise 403 if not found. Optional variant returns None when profile_id not provided, validates when provided.
- [x] T006 [US2] Replace all 11 `profile_id: uuid.UUID = Query(...)` params with `profile_id: VerifiedProfileId` in `backend/app/routers/viewing.py` (continue-watching, paused, dismiss, restore, bookmark-by-content, update-bookmark, get-rating, rate-title, watchlist, add-watchlist, remove-watchlist)
- [x] T007 [P] [US2] Replace 2 required `profile_id` params with `VerifiedProfileId` and 1 optional with `OptionalVerifiedProfileId` in `backend/app/routers/epg.py` (add_favorite, remove_favorite use required; list_channels uses optional)
- [x] T008 [P] [US2] Replace 2 required and 1 optional `profile_id` params in `backend/app/routers/recommendations.py` (home and post-play use required VerifiedProfileId; similar uses optional OptionalVerifiedProfileId)
- [x] T009 [P] [US2] Replace all 5 optional `profile_id` params with `OptionalVerifiedProfileId` in `backend/app/routers/catalog.py` (list_titles, get_title, featured_titles, search_titles, semantic_search)

**Checkpoint**: All 22 profile-scoped endpoints enforce ownership. Cross-user access returns 403. Own-profile access works normally. Non-existent profile returns 403.

---

## Phase 5: User Story 3 - Elimination of SQL Injection Vectors (Priority: P1)

**Goal**: Replace 2 f-string SQL interpolation instances with bind parameters, and escape ILIKE wildcard characters in all 11 search pattern constructions across 5 files.

**Independent Test**: Search with `'; DROP TABLE titles; --` — query runs safely. Search with `%` — treated as literal character, not wildcard. Code review confirms zero f-string SQL interpolation remains.

### Implementation for User Story 3

- [x] T010 [US3] Create an `escape_like(value: str) -> str` helper function that escapes `\`, `%`, and `_` characters for safe use in ILIKE patterns. Place in `backend/app/services/search_service.py` (or a shared location if preferred) since it's the primary search service.
- [x] T011 [US3] Replace f-string SQL IN clause in `get_for_you_rail()` (line ~157) with `bindparam("excluded_ids", expanding=True)` and add excluded_ids to bind_kw dict in `backend/app/services/recommendation_service.py`
- [x] T012 [US3] Replace f-string SQL IN clause in `compute_resumption_scores()` (line ~412) with `bindparam("episode_ids", expanding=True)` in `backend/app/services/recommendation_service.py`
- [x] T013 [P] [US3] Apply `escape_like()` to the search pattern in `keyword_search()` (line ~27) before all 4 ilike usages (title, synopsis_short, synopsis_long, person_name) in `backend/app/services/search_service.py`
- [x] T014 [P] [US3] Apply `escape_like()` to the search pattern in `get_titles()` (line ~51) before all 4 ilike usages (title, synopsis_short, synopsis_long, person_name) in `backend/app/services/catalog_service.py`
- [x] T015 [P] [US3] Apply `escape_like()` to the search pattern in `search_schedule()` (line ~147) before the ilike usage (title) in `backend/app/services/epg_service.py`
- [x] T016 [P] [US3] Apply `escape_like()` to the search pattern in `list_titles()` (lines ~94-95) before both ilike usages (title) in `backend/app/routers/admin.py`

**Checkpoint**: Zero f-string SQL interpolation in codebase. All ILIKE patterns escape wildcards. Searches with SQL metacharacters return safely. Searches with `%` or `_` treat them as literal text.

---

## Phase 6: User Story 4 - Restricted Cross-Origin Access (Priority: P2)

**Goal**: Replace wildcard CORS method and header configuration with explicit allowlists.

**Independent Test**: Send OPTIONS preflight with PATCH method — not allowed. Send OPTIONS with GET — allowed. Send with non-standard header — not in allowed headers.

### Implementation for User Story 4

- [x] T017 [US4] Replace `allow_methods=["*"]` with `allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]` and `allow_headers=["*"]` with `allow_headers=["Authorization", "Content-Type", "Accept"]` in the CORSMiddleware configuration in `backend/app/main.py`

**Checkpoint**: CORS preflight responses include only explicitly allowed methods and headers.

---

## Phase 7: User Story 5 - Reliable Health Monitoring (Priority: P2)

**Goal**: Replace single shallow `/health` endpoint with split `/health/live` (liveness, no deps) and `/health/ready` (readiness, checks DB). Keep `/health` as backward-compatible alias for readiness.

**Independent Test**: Stop the database. `/health/live` returns 200. `/health/ready` returns 503 with `{"status": "degraded", "checks": {"database": "unreachable"}}`. Start the database. `/health/ready` returns 200 with `{"status": "ok", "checks": {"database": "ok"}}`.

### Implementation for User Story 5

- [x] T018 [US5] Replace the existing `GET /health` endpoint with three endpoints in `backend/app/main.py`: (1) `GET /health/live` returning `{"status": "ok"}`, (2) `GET /health/ready` that executes `SELECT 1` against the DB (using `async_session_factory`) with a 5-second timeout, returns 200 with `{"status": "ok", "checks": {"database": "ok"}}` on success or 503 with `{"status": "degraded", "checks": {"database": "unreachable"}}` on failure, (3) `GET /health` as alias calling the same readiness logic for backward compatibility.

**Checkpoint**: Liveness returns 200 regardless of DB state. Readiness returns 503 when DB is down, 200 when DB is up. Readiness completes within 5 seconds.

---

## Phase 8: User Story 7 - Database Connection Pool Resilience (Priority: P2)

**Goal**: Add configurable pool_size, max_overflow, pool_pre_ping, and pool_recycle parameters to the database engine.

**Independent Test**: With pool_size=20 and max_overflow=10, simulate 25+ concurrent requests — no pool exhaustion errors. Stale connections are detected and replaced automatically.

### Implementation for User Story 7

- [x] T019 [P] [US7] Add `db_pool_size: int = 20`, `db_max_overflow: int = 10`, and `db_pool_recycle: int = 3600` settings fields to the Settings class in `backend/app/config.py`
- [x] T020 [US7] Pass `pool_size=settings.db_pool_size`, `max_overflow=settings.db_max_overflow`, `pool_pre_ping=True`, `pool_recycle=settings.db_pool_recycle` to `create_async_engine()` in `backend/app/database.py`

**Checkpoint**: Engine is created with configurable pool parameters. Pool handles concurrent load without exhaustion. Stale connections are detected via pre-ping.

---

## Phase 9: User Story 6 - Removal of Confusing Duplicate Entry Point (Priority: P3)

**Goal**: Delete the unused duplicate entry point file that causes developer confusion.

**Independent Test**: File `backend/main.py` no longer exists. Application starts correctly from `backend/app/main.py`.

### Implementation for User Story 6

- [x] T021 [US6] Delete the duplicate entry point file `backend/main.py` (contains only `print("Hello from backend!")`)

**Checkpoint**: Only one entry point exists. Application starts correctly.

---

## Phase 10: User Story 8 - Admin Authorization Consistency (Priority: P3)

**Goal**: Replace 15 manual `_require_admin(user)` calls with a centralized `AdminUser` dependency. Remove the `_require_admin()` helper.

**Independent Test**: Non-admin user calling any admin endpoint gets 403 before the handler runs. Admin user proceeds normally. New endpoints using `AdminUser` type get automatic enforcement.

### Implementation for User Story 8

- [x] T022 [US8] Create `get_admin_user()` async function (depends on `get_current_user`, checks `user.is_admin`, raises 403 if not) and `AdminUser = Annotated[User, Depends(get_admin_user)]` type alias in `backend/app/dependencies.py`
- [x] T023 [US8] In `backend/app/routers/admin.py`: (1) replace all 15 `user: CurrentUser` params with `user: AdminUser`, (2) remove all 15 `_require_admin(user)` calls from endpoint bodies, (3) delete the `_require_admin()` helper function, (4) update imports (add AdminUser, remove CurrentUser if no longer used)

**Checkpoint**: All 15 admin endpoints use AdminUser dependency. Zero manual authorization checks remain. Non-admin users get 403 automatically.

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Final verification and cleanup across all stories

- [x] T024 Run the full quickstart.md verification checklist from `specs/005-backend-hardening/quickstart.md` to validate all 8 user stories
- [x] T025 Verify zero f-string SQL interpolation remains using grep: search for patterns like `f".*SELECT`, `f".*WHERE`, `f".*IN \(` across `backend/app/`
- [x] T026 Verify all 22 profile-scoped endpoints use VerifiedProfileId or OptionalVerifiedProfileId by checking for any remaining `profile_id: uuid.UUID` params in `backend/app/routers/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Skipped — existing project
- **Foundational (Phase 2)**: Skipped — no shared prerequisites
- **US1 JWT (Phase 3)**: No dependencies — start immediately
- **US2 IDOR (Phase 4)**: Independent, but shares `dependencies.py` with US1 (different sections). Can start after T002 if working sequentially.
- **US3 SQL Injection (Phase 5)**: Fully independent — different files from US1/US2
- **US4 CORS (Phase 6)**: Shares `main.py` with US1/US5 (different sections)
- **US5 Health (Phase 7)**: Shares `main.py` with US1/US4 (different sections)
- **US7 DB Pool (Phase 8)**: Shares `config.py` with US1 (different sections)
- **US6 Delete Dup (Phase 9)**: Fully independent — no shared files
- **US8 Admin Auth (Phase 10)**: Shares `dependencies.py` with US2 and `admin.py` with US3 (different sections)
- **Polish (Phase 11)**: After all user stories complete

### User Story Dependencies

| Story | Can Start After | Shared Files | Independent? |
|-------|----------------|--------------|-------------|
| US1 (JWT) | Immediately | config.py, dependencies.py, main.py | Yes |
| US2 (IDOR) | US1 T002 (dependencies.py) | dependencies.py, routers | Yes |
| US3 (SQL Injection) | Immediately | services, admin.py | Yes |
| US4 (CORS) | US1 T003, US5 T018 (main.py) | main.py | Yes |
| US5 (Health) | US1 T003 (main.py) | main.py | Yes |
| US6 (Delete Dup) | Immediately | None | Yes |
| US7 (DB Pool) | US1 T001 (config.py) | config.py, database.py | Yes |
| US8 (Admin Auth) | US2 T005 (dependencies.py) | dependencies.py, admin.py | Yes |

### Parallel Opportunities

**Maximum parallelism (3 parallel streams)**:
```
Stream 1: US1 → US2 → US8      (dependencies.py chain)
Stream 2: US3 → US4             (independent, then main.py)
Stream 3: US6 → US5 → US7      (independent, then main.py + config.py)
```

**Sequential execution (recommended for single developer)**:
```
US1 → US7 → US5 → US4 → US2 → US8 → US3 → US6 → Polish
```
This order minimizes file conflicts by grouping edits to the same file together.

---

## Parallel Example: P1 Stories

```bash
# US1, US3, and US6 have no file overlaps — can all start simultaneously:
Task: "[US1] T001-T004 — JWT Secret hardening"
Task: "[US3] T010-T016 — SQL Injection remediation"
Task: "[US6] T021 — Delete duplicate entry point"
```

---

## Implementation Strategy

### MVP First (P1 Stories Only — US1 + US2 + US3)

1. Complete US1: JWT Secret (T001-T004)
2. Complete US2: IDOR Fix (T005-T009)
3. Complete US3: SQL Injection (T010-T016)
4. **STOP and VALIDATE**: All 3 critical security vulnerabilities are fixed
5. The application is now safe to deploy even without P2/P3 items

### Incremental Delivery

1. P1 Security (US1+US2+US3) → Critical vulnerabilities eliminated
2. P2 Reliability (US4+US5+US7) → Production-grade CORS, health checks, pool config
3. P3 Cleanup (US6+US8) → Developer experience improvements
4. Polish (verification) → Full confidence in all changes

### Single Developer Sequential (Fastest Path)

Total: **26 tasks** across 8 user stories + 3 polish tasks

Estimated effort per story:
- US1 (JWT): 4 tasks, ~15 min
- US2 (IDOR): 5 tasks, ~30 min
- US3 (SQL Injection): 7 tasks, ~30 min
- US4 (CORS): 1 task, ~5 min
- US5 (Health): 1 task, ~15 min
- US6 (Delete Dup): 1 task, ~1 min
- US7 (DB Pool): 2 tasks, ~10 min
- US8 (Admin Auth): 2 tasks, ~15 min
- Polish: 3 tasks, ~15 min

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks in the same phase
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- No new Python dependencies are needed
- No database migrations are needed
- Commit after each user story for clean git history
- The recommended sequential order minimizes file conflicts: US1 → US7 → US5 → US4 → US2 → US8 → US3 → US6
