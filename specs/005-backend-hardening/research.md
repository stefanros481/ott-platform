# Research: Backend Hardening for Production Readiness

**Date**: 2026-02-13
**Branch**: `005-backend-hardening`

## 1. JWT Secret Hardening

### Current State
- **File**: `backend/app/config.py:12` — `jwt_secret: str = "poc-secret-key-change-in-production"`
- **File**: `docker/docker-compose.yml` — `JWT_SECRET: poc-secret-key-change-in-production` hardcoded
- `SecretStr` is NOT imported; jwt_secret is a plain `str`
- `backend/app/dependencies.py:25` uses `settings.jwt_secret` to decode tokens

### Decision: Use Pydantic `SecretStr` + remove default + startup validation
- **Rationale**: `SecretStr` prevents accidental logging/serialization of the secret. Removing the default forces explicit configuration. Startup validation ensures minimum strength.
- **Alternatives considered**:
  - Keep `str` type + just remove default — rejected because `SecretStr` also prevents accidental exposure in logs/repr
  - Add validator on the Settings class — rejected because validation during lifespan gives a clearer error message at boot time

### Implementation
- `config.py`: Change `jwt_secret: str = "..."` to `jwt_secret: SecretStr` (no default)
- `dependencies.py`: Change `settings.jwt_secret` to `settings.jwt_secret.get_secret_value()`
- `main.py` lifespan: Add length check `>= 32` with `sys.exit(1)` on failure
- `docker/docker-compose.yml`: Change to `JWT_SECRET: ${JWT_SECRET:?Set JWT_SECRET env var}` or generate a random value
- `.env.example`: Add `JWT_SECRET=` with comment about minimum length

### Files Affected
| File | Change |
|------|--------|
| `backend/app/config.py` | Import SecretStr, change jwt_secret type, remove default |
| `backend/app/dependencies.py` | Use `.get_secret_value()` |
| `backend/app/main.py` | Add length validation in lifespan |
| `docker/docker-compose.yml` | Use env var substitution |

---

## 2. Profile Ownership (IDOR Fix)

### Current State
- **19 total endpoints** accept `profile_id` across 4 routers
- **14 endpoints are vulnerable** (required profile_id, zero ownership checks)
- **5 endpoints** use optional profile_id (catalog.py) — lower risk but should still validate when provided
- `auth.py:select_profile` (line 114-128) already validates correctly: `Profile.user_id == user.id`
- `Profile.user_id` FK exists in `models/user.py:31` (`nullable=False`, `ondelete="CASCADE"`)

### Vulnerable Endpoints

| Router | Endpoint | Required? |
|--------|----------|-----------|
| viewing.py | GET /continue-watching | Yes |
| viewing.py | GET /continue-watching/paused | Yes |
| viewing.py | POST /bookmarks/{id}/dismiss | Yes |
| viewing.py | POST /bookmarks/{id}/restore | Yes |
| viewing.py | GET /bookmarks/by-content/{id} | Yes |
| viewing.py | PUT /bookmarks | Yes |
| viewing.py | GET /ratings/{title_id} | Yes |
| viewing.py | POST /ratings | Yes |
| viewing.py | GET /watchlist | Yes |
| viewing.py | POST /watchlist/{title_id} | Yes |
| viewing.py | DELETE /watchlist/{title_id} | Yes |
| epg.py | POST /favorites/{channel_id} | Yes |
| epg.py | DELETE /favorites/{channel_id} | Yes |
| recommendations.py | GET /home | Yes |
| recommendations.py | GET /post-play/{title_id} | Yes |
| catalog.py | GET /titles | Optional |
| catalog.py | GET /titles/{title_id} | Optional |
| catalog.py | GET /featured | Optional |
| catalog.py | GET /search | Optional |
| catalog.py | GET /search/semantic | Optional |
| epg.py | GET /channels | Optional |
| recommendations.py | GET /similar/{title_id} | Optional |

### Decision: Create `VerifiedProfileId` and `OptionalVerifiedProfileId` dependencies
- **Rationale**: A FastAPI dependency that validates ownership is the idiomatic approach. Two variants cover required vs optional cases. Returns the validated `uuid.UUID` so router code stays clean.
- **Alternatives considered**:
  - Middleware-based check — rejected because not all endpoints have profile_id, and parameter extraction in middleware is fragile
  - Decorator pattern — rejected because FastAPI's dependency injection is the native pattern

### Implementation
- `dependencies.py`: Add `get_verified_profile_id()` that queries `Profile` with `user_id == user.id`, raises 403 if not found
- `dependencies.py`: Add `get_optional_verified_profile_id()` that returns `None` when not provided, validates when provided
- All routers: Replace `profile_id: uuid.UUID = Query(...)` with `profile_id: VerifiedProfileId`
- All routers: Replace `profile_id: uuid.UUID | None = Query(None, ...)` with `profile_id: OptionalVerifiedProfileId`

### Files Affected
| File | Change |
|------|--------|
| `backend/app/dependencies.py` | Add VerifiedProfileId + OptionalVerifiedProfileId |
| `backend/app/routers/viewing.py` | Replace 11 profile_id params |
| `backend/app/routers/epg.py` | Replace 3 profile_id params |
| `backend/app/routers/recommendations.py` | Replace 3 profile_id params |
| `backend/app/routers/catalog.py` | Replace 5 profile_id params |

---

## 3. SQL Injection Remediation

### Current State — f-string SQL interpolation (2 instances)

**recommendation_service.py:157** — `get_for_you_rail()`:
```python
exclusion_list = ", ".join(f"'{uid}'" for uid in interacted_ids)
# ... later used in:
WHERE ce.title_id NOT IN ({exclusion_list})
```

**recommendation_service.py:412** — `compute_resumption_scores()`:
```python
id_list = ", ".join(f"'{eid}'" for eid in episode_ids)
# ... later used in:
WHERE e_target.id IN ({id_list})
```

### Current State — Unescaped ILIKE patterns (11 instances)

| File | Line(s) | Fields |
|------|---------|--------|
| search_service.py | 27, 32, 36-38 | title, synopsis_short, synopsis_long, person_name |
| catalog_service.py | 51, 55, 59-61 | title, synopsis_short, synopsis_long, person_name |
| epg_service.py | 147 | title |
| admin.py (router) | 94-95 | title |

### Decision: Use `bindparam(expanding=True)` for IN clauses + escape helper for ILIKE
- **Rationale**: SQLAlchemy's `expanding=True` bind parameter is designed for dynamic IN clauses. A shared escape function ensures consistency across all ILIKE usages.
- **Alternatives considered**:
  - Use SQLAlchemy `in_()` ORM method — not feasible for raw `text()` queries that use pgvector operators
  - Use array `ANY()` — PostgreSQL-specific, less readable

### Implementation
- Create helper `escape_like(value: str) -> str` that escapes `\`, `%`, `_`
- recommendation_service.py: Replace f-string IN with `bindparam("excluded_ids", expanding=True)`
- All ILIKE usages: Apply `escape_like()` before building pattern

### Files Affected
| File | Change |
|------|--------|
| `backend/app/services/recommendation_service.py` | Replace 2 f-string IN clauses with bind params |
| `backend/app/services/search_service.py` | Escape ILIKE patterns (4 usages) |
| `backend/app/services/catalog_service.py` | Escape ILIKE patterns (4 usages) |
| `backend/app/services/epg_service.py` | Escape ILIKE pattern (1 usage) |
| `backend/app/routers/admin.py` | Escape ILIKE patterns (2 usages) |

---

## 4. CORS Restriction

### Current State
- `backend/app/main.py:31-32`: `allow_methods=["*"], allow_headers=["*"]`
- Origins are already configurable via `settings.cors_origin_list`

### Decision: Restrict to explicit method and header lists
- Methods: `["GET", "POST", "PUT", "DELETE", "OPTIONS"]`
- Headers: `["Authorization", "Content-Type", "Accept"]`
- **Rationale**: Only methods actually used by the API. Only headers required for JWT auth and JSON bodies.

### Files Affected
| File | Change |
|------|--------|
| `backend/app/main.py` | Replace `["*"]` with explicit lists |

---

## 5. Health Check Split (Liveness + Readiness)

### Current State
- `backend/app/main.py`: Single `GET /health` returning `{"status": "ok"}` with no dependency checks

### Decision: Split into `/health/live` and `/health/ready`
- **Liveness** (`GET /health/live`): Returns `{"status": "ok"}` — confirms process is running
- **Readiness** (`GET /health/ready`): Runs `SELECT 1` against DB, returns per-dependency status
- Keep legacy `GET /health` as alias for `/health/ready` for backward compatibility
- **Rationale**: Per clarification session, split prevents orchestrator restart loops during transient DB outages

### Implementation
- Readiness executes `SELECT 1` with a 5-second timeout
- Returns `{"status": "ok", "checks": {"database": "ok"}}` or `{"status": "degraded", "checks": {"database": "unreachable"}}`
- Returns 200 for healthy, 503 for unhealthy

### Files Affected
| File | Change |
|------|--------|
| `backend/app/main.py` | Replace single `/health` with `/health/live` + `/health/ready` |

---

## 6. Duplicate Entry Point Removal

### Current State
- `backend/main.py`: Contains only `print("Hello from backend!")` — not used by the application

### Decision: Delete the file
- **Rationale**: No code depends on it. It creates confusion about the real entry point.

### Files Affected
| File | Change |
|------|--------|
| `backend/main.py` | Delete |

---

## 7. Database Connection Pool Configuration

### Current State
- `backend/app/database.py`: `create_async_engine(settings.database_url, echo=False)` — SQLAlchemy defaults (pool_size=5, no overflow, no pre-ping, no recycle)

### Decision: Add configurable pool parameters
- `pool_size=20` (configurable via `DB_POOL_SIZE`)
- `max_overflow=10` (configurable via `DB_MAX_OVERFLOW`)
- `pool_pre_ping=True` (always enabled — detects stale connections)
- `pool_recycle=3600` (configurable via `DB_POOL_RECYCLE`)
- **Rationale**: Default pool of 5 is insufficient for 30-second bookmark heartbeats from concurrent clients. Pre-ping prevents errors from stale connections.

### Files Affected
| File | Change |
|------|--------|
| `backend/app/config.py` | Add pool_size, max_overflow, pool_recycle settings |
| `backend/app/database.py` | Pass pool params to create_async_engine |
| `docker/docker-compose.yml` | Add pool env vars (optional, defaults are sensible) |

---

## 8. Admin Authorization Dependency

### Current State
- `backend/app/routers/admin.py`: `_require_admin(user)` called manually in 15 endpoints
- Helper function at line 40-46 raises 403 if `not user.is_admin`

### Decision: Create `AdminUser` annotated dependency
- **Rationale**: FastAPI `Depends()` ensures the check runs automatically. Impossible to forget on new endpoints.
- **Alternatives considered**:
  - Router-level middleware — rejected because FastAPI doesn't support per-router middleware natively
  - APIRouter `dependencies` parameter — viable but less explicit in function signatures

### Implementation
- `dependencies.py`: Add `get_admin_user()` that calls `get_current_user()` + checks `is_admin`
- `dependencies.py`: Add `AdminUser = Annotated[User, Depends(get_admin_user)]`
- `admin.py`: Replace `user: CurrentUser` + `_require_admin(user)` with `user: AdminUser`
- Remove `_require_admin()` helper function

### Files Affected
| File | Change |
|------|--------|
| `backend/app/dependencies.py` | Add AdminUser dependency |
| `backend/app/routers/admin.py` | Replace CurrentUser + manual check with AdminUser (15 endpoints), delete helper |
