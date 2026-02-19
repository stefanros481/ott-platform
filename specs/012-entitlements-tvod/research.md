# Research: Subscription Tiers, Entitlements & TVOD

**Branch**: `012-entitlements-tvod` | **Date**: 2026-02-17

---

## Finding 1: Rate Limiting (FR-024, FR-025)

**Decision**: `slowapi` library with Redis backend

**Rationale**: `slowapi` is a Starlette/FastAPI-native rate limiting library that integrates with Redis as a storage backend. It provides decorator-based per-endpoint limits and a global default. The key function must be synchronous — user_id is extracted from the JWT token synchronously using `python-jose` (already a project dependency).

**Integration pattern**:
```python
# In main.py
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

def get_user_or_ip(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        try:
            from jose import jwt
            payload = jwt.decode(auth[7:], settings.jwt_secret.get_secret_value(),
                                 algorithms=[settings.jwt_algorithm])
            if uid := payload.get("sub"):
                return f"user:{uid}"
        except Exception:
            pass
    from slowapi.util import get_remote_address
    return get_remote_address(request)

limiter = Limiter(
    key_func=get_user_or_ip,
    storage_uri=settings.redis_url,
    default_limits=["100/minute"],
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
app.add_middleware(SlowAPIMiddleware)
```

Per-endpoint override for TVOD transactions:
```python
@router.post("/titles/{title_id}/purchase")
@limiter.limit("10/hour")
async def purchase_title(request: Request, ...):
    ...
```

**Alternatives considered**:
- Custom Redis sliding window: more control but ~100 lines of boilerplate
- No rate limiting: rejected — violates FR-024 and reduces PoC credibility
- Per-IP only: rejected — doesn't protect against authenticated abuse

**Dependency**: `uv add slowapi` (no version pin needed; current stable is 0.1.9)

**Constitution note**: Constitution says "Skip: rate limiting" for PoC. This feature explicitly includes X-03 (rate limiting) in scope. Justified violation — slowapi adds < 30 LOC to `main.py`.

---

## Finding 2: Entitlement Check Caching (FR-021)

**Decision**: `redis.asyncio` with 5-minute TTL, fail-closed on exception

**Rationale**: `redis>=5.2` is already in `pyproject.toml`. The `redis.asyncio` module provides an async client that integrates cleanly with FastAPI's async dependency injection. Entitlement check results are cached per (user_id, title_id) pair with a 300-second TTL. Any Redis error (connection failure, timeout) is caught and treated as a cache miss → the live DB check is attempted. If both Redis AND the DB check fail, access is denied (fail-closed).

**Key pattern**:
```python
CACHE_KEY = "ent:{user_id}:{title_id}"
CACHE_TTL = 300  # 5 minutes

async def check_entitlement_cached(redis_client, user_id, title_id, db) -> bool:
    key = f"ent:{user_id}:{title_id}"
    try:
        cached = await redis_client.get(key)
        if cached is not None:
            return cached == "1"
    except Exception:
        pass  # Redis unavailable — fall through to DB check

    try:
        result = await _check_entitlement_db(user_id, title_id, db)
        try:
            await redis_client.set(key, "1" if result else "0", ex=CACHE_TTL)
        except Exception:
            pass  # Cache write failure is non-fatal
        return result
    except Exception:
        return False  # DB also unavailable — fail closed
```

**Cache invalidation**: Delete `ent:{user_id}:*` pattern on:
- User subscription tier change (admin endpoint)
- TVOD transaction creation (purchase/rental)

**Alternatives considered**:
- In-process dict cache: rejected — doesn't survive process restart, can't invalidate across workers
- No caching: simpler but fails the 5-minute in-progress session grace requirement from spec

---

## Finding 3: Viewing Session Cleanup (FR-019)

**Decision**: On-demand cleanup at session-start check time

**Rationale**: Rather than a background task (which requires task scheduling infrastructure), abandoned sessions are cleaned up lazily: when checking if a user can start a new session, the query first marks sessions as ended where `last_heartbeat_at < now() - 5 minutes`, then counts active sessions against the limit. This is a single transactional operation.

```sql
-- Atomically expire and count in one go
UPDATE viewing_sessions
  SET ended_at = now()
  WHERE user_id = :user_id
    AND ended_at IS NULL
    AND last_heartbeat_at < now() - INTERVAL '5 minutes';

SELECT COUNT(*) FROM viewing_sessions
  WHERE user_id = :user_id AND ended_at IS NULL;
```

**Alternatives considered**:
- Background task with APScheduler: more accurate but requires scheduler setup
- Database cron job: requires pg_cron extension or external scheduler
- Client-side only: rejected — can't trust client to close sessions reliably

---

## Finding 4: UserEntitlement Model Extension for TVOD

**Decision**: Make `package_id` nullable, add nullable `title_id`, enforce one-is-not-null via Python-level validation

**Rationale**: The current `UserEntitlement` uses `package_id` (non-nullable) for SVOD package membership. TVOD entitlements are per-title (not per-package). The cleanest extension is:
- `package_id` becomes nullable (`SVOD path`)
- New `title_id` nullable FK to `titles.id` (`TVOD path`)
- One and exactly one of {package_id, title_id} must be non-null (enforced in the service layer; a DB CHECK constraint is optional for PoC)

This keeps SVOD and TVOD entitlements in a single table queryable with a `source_type` discriminator.

**Alternatives considered**:
- Separate `TVODEntitlement` table: cleaner schema but requires JOIN across tables for access checks
- Virtual packages per TVOD purchase: avoids schema change but is a data model hack

---

## Finding 5: `redis.asyncio` Client Initialization

**Decision**: Initialize Redis client in `lifespan` context manager, store on `app.state`

```python
# In main.py lifespan
from redis.asyncio import from_url as redis_from_url

async with lifespan():
    redis_client = redis_from_url(settings.redis_url, decode_responses=True)
    app.state.redis = redis_client
    yield
    await redis_client.aclose()

# In dependencies.py
async def get_redis(request: Request) -> redis.asyncio.Redis:
    return request.app.state.redis

RedisClient = Annotated[redis.asyncio.Redis, Depends(get_redis)]
```

**Note**: `slowapi` uses its own sync Redis connection for rate limit counters. The async client on `app.state` is separate and used only for entitlement caching.
