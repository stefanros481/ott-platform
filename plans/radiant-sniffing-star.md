# Backend Improvement Plan

## Context

The backend is a well-structured FastAPI + SQLAlchemy 2.0 async POC (~5,000 lines, 30+ files) for an AI-native OTT streaming platform. It has clean architecture (thin routers → services → async ORM), JWT auth with refresh rotation, pgvector-backed AI features (hybrid search, resumption scoring, recommendations), and comprehensive seed data.

This plan identifies **20 improvements** graded by impact and importance, organized into 4 tiers. The goal is to harden security, improve reliability, and bring the codebase toward production readiness.

---

## Tier 1: Production Blockers (Must fix before any deployment)

### 1.1 Hardcoded JWT Secret
| Impact: **Critical** | Importance: **Must-have** | Effort: **S** |
|---|---|---|

`config.py:12` has `jwt_secret: str = "poc-secret-key-change-in-production"`. Anyone who reads the source can forge tokens.

**Fix:** Remove the default value so startup fails without env var. Use `SecretStr` type. Add length validation (>= 32 chars) in the lifespan handler.

**Files:** [config.py](backend/app/config.py), [main.py](backend/app/main.py), [docker-compose.yml](docker/docker-compose.yml)

---

### 1.2 Profile Ownership Not Validated (IDOR Vulnerability)
| Impact: **Critical** | Importance: **Must-have** | Effort: **M** |
|---|---|---|

Every router accepts `profile_id` as a query param but **never verifies it belongs to the authenticated user**. An attacker with a valid JWT can read/modify any user's bookmarks, watchlist, ratings, and viewing history.

**Fix:** Create a `VerifiedProfileId` dependency in [dependencies.py](backend/app/dependencies.py) that checks `Profile.user_id == user.id`. Replace all `profile_id: UUID = Query(...)` params across all routers.

**Files:** [dependencies.py](backend/app/dependencies.py), all files in [routers/](backend/app/routers/)

---

### 1.3 SQL Injection via String Interpolation
| Impact: **Critical** | Importance: **Must-have** | Effort: **M** |
|---|---|---|

[recommendation_service.py:157](backend/app/services/recommendation_service.py#L157) and [line 412](backend/app/services/recommendation_service.py#L412) build SQL `IN` clauses via f-string interpolation (`", ".join(f"'{uid}'" ...)`). While inputs come from DB queries, this is a SQL injection vector.

**Fix:** Replace with SQLAlchemy `bindparam(..., expanding=True)` for all `IN` clauses. Also escape `%` and `_` in ILIKE patterns in [catalog_service.py](backend/app/services/catalog_service.py), [search_service.py](backend/app/services/search_service.py), [epg_service.py](backend/app/services/epg_service.py).

---

### 1.4 Overly Permissive CORS
| Impact: **High** | Importance: **Must-have** | Effort: **S** |
|---|---|---|

[main.py:31-32](backend/app/main.py#L31) uses `allow_methods=["*"], allow_headers=["*"]`.

**Fix:** Restrict to `["GET", "POST", "PUT", "DELETE", "OPTIONS"]` and `["Authorization", "Content-Type", "Accept"]`.

---

### 1.5 Shallow Health Check
| Impact: **High** | Importance: **Must-have** | Effort: **S** |
|---|---|---|

`/health` always returns 200, even if the database is unreachable.

**Fix:** Add `SELECT 1` DB check. Return 503 if unreachable. Optionally split into `/health/live` (shallow) and `/health/ready` (deep).

**Files:** [main.py](backend/app/main.py)

---

### 1.6 Remove Duplicate `backend/main.py`
| Impact: **Medium** | Importance: **Must-have** | Effort: **S** |
|---|---|---|

[backend/main.py](backend/main.py) contains only `print("Hello from backend!")` alongside the real [backend/app/main.py](backend/app/main.py). Confusing, could cause import issues.

**Fix:** Delete [backend/main.py](backend/main.py).

---

### 1.7 Database Connection Pool Configuration
| Impact: **High** | Importance: **Must-have** | Effort: **S** |
|---|---|---|

[database.py](backend/app/database.py) uses SQLAlchemy defaults (pool_size=5). With 30-second bookmark heartbeats from multiple clients, this exhausts quickly.

**Fix:** Add `pool_size=20, max_overflow=10, pool_pre_ping=True, pool_recycle=3600` with configurable settings in [config.py](backend/app/config.py).

---

## Tier 2: High-Value Improvements (Significant quality/reliability gains)

### 2.1 Test Suite Foundation
| Impact: **Critical** | Importance: **Should-have** | Effort: **L** |
|---|---|---|

Zero test files exist. 22+ endpoints, complex raw SQL queries, and AI scoring logic are all unverified.

**Fix:** Create `tests/` with `conftest.py` (fixtures, test DB, auth helpers). Priority tests:
1. Auth & security (registration, login, token refresh, IDOR protection)
2. Bookmark service (upsert, auto-completion thresholds, dismiss/restore, next episode)
3. Resumption scoring (4-factor model edge cases)
4. Search (keyword, semantic fallback, hybrid RRF)
5. Full continue-watching flow (E2E)

**Dependencies:** Implement 1.2 first so tests verify correct security behavior.

---

### 2.2 Structured Logging with Request Context
| Impact: **High** | Importance: **Should-have** | Effort: **M** |
|---|---|---|

Basic `logging.getLogger()` with no correlation IDs, no request context, no structured output.

**Fix:** Add `structlog`. Create logging middleware that generates `request_id` per request, binds user_id/profile_id/method/path, logs request timing. JSON output in production, human-readable in dev.

**Files:** New `middleware/logging.py`, [main.py](backend/app/main.py), service files

---

### 2.3 Error Handling Middleware
| Impact: **High** | Importance: **Should-have** | Effort: **M** |
|---|---|---|

Raw HTTPExceptions, no consistent error envelope, unhandled exceptions may leak stack traces.

**Fix:** Global exception handler returning `{detail, request_id}` envelope. Log full tracebacks server-side. This matches the frontend's existing error parsing (`body.detail`).

**Dependencies:** 2.2 for request_id propagation.

---

### 2.4 Admin Authorization as Dependency
| Impact: **Medium** | Importance: **Should-have** | Effort: **S** |
|---|---|---|

[admin.py](backend/app/routers/admin.py) calls `_require_admin(user)` manually in every endpoint (15 times). Easy to forget on new endpoints.

**Fix:** Create `AdminUser = Annotated[User, Depends(get_admin_user)]` in [dependencies.py](backend/app/dependencies.py). Replace all manual checks.

---

### 2.5 Async Embedding Generation
| Impact: **High** | Importance: **Should-have** | Effort: **M** |
|---|---|---|

[embedding_service.py](backend/app/services/embedding_service.py) `generate_all_embeddings` blocks the event loop during CPU-intensive model inference, making the entire backend unresponsive.

**Fix:** Use `FastAPI.BackgroundTasks` for the admin endpoint. Return `{"status": "started"}` immediately. Add a `/admin/embeddings/status` endpoint for progress.

---

### 2.6 N+1 Query Fixes
| Impact: **High** | Importance: **Should-have** | Effort: **M** |
|---|---|---|

Multiple services execute queries inside loops:
- [bookmark_service.py:130](backend/app/services/bookmark_service.py#L130) — `resolve_next_episode()` per bookmark (20 queries for 20 bookmarks)
- [search_service.py:66](backend/app/services/search_service.py#L66) — cast check per search hit (30 queries)
- [epg_service.py:116](backend/app/services/epg_service.py#L116) — next program per channel (20 queries)
- [embedding_service.py:81](backend/app/services/embedding_service.py#L81) — genres + cast per title (80+ queries)

**Fix:** Batch queries using LATERAL JOINs, window functions (`LEAD()`), or pre-fetching with lookup dicts.

---

### 2.7 Rate Limiting
| Impact: **High** | Importance: **Should-have** | Effort: **M** |
|---|---|---|

No rate limiting anywhere. Auth endpoints vulnerable to brute-force, embedding endpoint to CPU exhaustion.

**Fix:** Add `slowapi`. Limits: auth `5/min/IP`, bookmarks `10/min/user`, search `30/min/user`, embedding gen `1/min/user`, general `60/min/user`.

---

### 2.8 Redis Caching Layer
| Impact: **High** | Importance: **Should-have** | Effort: **L** |
|---|---|---|

Redis is deployed and configured but never used. Home rails execute 5+ DB queries per request; genres/featured rarely change.

**Fix:** Create `cache.py` with `redis.asyncio`. Cache: genres (TTL 3600), featured (TTL 300), home rails per profile (TTL 120), EPG schedule per channel+date (TTL 300), now-playing (TTL 30). Add Redis to health check.

---

## Tier 3: Professional Polish (Production-grade refinements)

| # | Improvement | Impact | Effort | Description |
|---|---|---|---|---|
| 3.1 | Request/Response Logging | Medium | S | Log method, path, timing, status for all requests. Skip health checks. Warn on >500ms. |
| 3.2 | API Docs Enhancement | Medium | S | Add OpenAPI tags, endpoint summaries, schema examples. |
| 3.3 | Consistent Pagination | Medium | S | Add `{items, total}` wrapper to endpoints returning bare lists (watchlist, continue-watching, channels). |
| 3.4 | Refresh Token Cleanup | Medium | S | Add cleanup function for expired/revoked tokens. Expose via admin endpoint. |
| 3.5 | Entitlement Enforcement | High | M | Check `UserEntitlement` + `PackageContent` on playback. Add `entitled: bool` to catalog responses. |
| 3.6 | Input Validation Hardening | Medium | S | Use `Literal` types for enums, add cross-field validators (e.g., `end_time > start_time`). |
| 3.7 | Remove Unused `passlib` Dep | Low | S | `passlib[bcrypt]` is installed but unused — code imports `bcrypt` directly. Remove from pyproject.toml. |

---

## Tier 4: Advanced Features (Future enhancements)

| # | Improvement | Impact | Effort | Description |
|---|---|---|---|---|
| 4.1 | Prometheus Metrics | High | M | `prometheus-fastapi-instrumentator` with custom business metrics (bookmarks/min, search mode split, cache hits). |
| 4.2 | OpenTelemetry Tracing | Medium | L | Auto-instrument FastAPI + SQLAlchemy. Propagate trace IDs. Export to Jaeger/OTLP. |
| 4.3 | Background Task Scheduler | Medium | M | `arq` (async Redis queue) for token cleanup, embedding refresh, cache warming. |
| 4.4 | SSE for Real-Time Updates | Medium | L | Server-Sent Events for cross-device bookmark sync, new content notifications. |

---

## Implementation Sequence

```
Week 1 — Security & Stability (Tier 1):
  1.1 JWT secret          1.2 IDOR fix           1.3 SQL injection
  1.4 CORS                1.5 Health check        1.6 Remove dup main.py
  1.7 DB pool config

Week 2 — Reliability & Testing (Tier 2, part 1):
  2.1 Test suite          2.4 Admin auth dep      2.5 Async embeddings
  2.6 N+1 query fixes

Week 3 — Observability & Caching (Tier 2, part 2):
  2.2 Structured logging  2.3 Error middleware     2.7 Rate limiting
  2.8 Redis caching

Week 4 — Polish (Tier 3):
  3.1–3.7 as prioritized above

Ongoing — Advanced (Tier 4):
  4.1–4.4 as capacity allows
```

---

## Verification

After implementing each tier:
- **Tier 1:** Manually test: startup fails without JWT_SECRET env var, passing another user's profile_id returns 403, raw SQL queries use bind params (check via `echo=True`), health check returns 503 when DB is stopped
- **Tier 2:** Run `pytest` with >80% coverage on services. Verify embedding generation returns immediately. Check structured JSON logs in Docker logs. Verify rate limit 429 responses.
- **Tier 3:** Check OpenAPI docs at `/docs`. Verify pagination wrappers. Test entitlement blocking on restricted content.
- **Tier 4:** Check `/metrics` endpoint. Verify traces in Jaeger UI.
