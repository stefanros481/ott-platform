from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

import redis.asyncio as aioredis
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import settings
from app.limiter import limiter


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    import sys

    secret = settings.jwt_secret.get_secret_value()
    if len(secret) < 32:
        print("FATAL: JWT_SECRET must be at least 32 characters", file=sys.stderr)
        sys.exit(1)

    # T021: Pre-warm one connection so first request avoids cold-start
    from sqlalchemy import text

    from app.database import async_session_factory, engine

    async with async_session_factory() as session:
        await session.execute(text("SELECT 1"))

    # Initialize Redis client for entitlement caching
    redis_client = aioredis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=5,
    )
    _app.state.redis = redis_client

    yield

    # Shutdown: close Redis, dispose engine
    await redis_client.aclose()
    await engine.dispose()


app = FastAPI(
    title="OTT Platform PoC",
    description="AI-Native OTT Streaming Platform - Proof of Concept",
    version="0.1.0",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# Import and mount routers
from app.routers import (
    admin,
    analytics,
    auth,
    catalog,
    content_analytics,
    epg,
    offers,
    parental_controls,
    recommendations,
    viewing,
    viewing_time,
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(catalog.router, prefix="/api/v1/catalog", tags=["Catalog"])
app.include_router(offers.router, prefix="/api/v1/catalog", tags=["Offers"])
app.include_router(epg.router, prefix="/api/v1/epg", tags=["EPG"])
app.include_router(recommendations.router, prefix="/api/v1/recommendations", tags=["Recommendations"])
app.include_router(viewing.router, prefix="/api/v1/viewing", tags=["Viewing"])
app.include_router(parental_controls.router, prefix="/api/v1/parental-controls", tags=["Parental Controls"])
app.include_router(viewing_time.router, prefix="/api/v1/viewing-time", tags=["Viewing Time"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
# Feature 001: Content Analytics Agent
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(content_analytics.router, prefix="/api/v1/content-analytics", tags=["Content Analytics"])


@app.get("/health/live")
async def health_live():
    return {"status": "ok"}


async def _check_readiness():
    import asyncio

    from fastapi.responses import JSONResponse
    from sqlalchemy import text

    from app.database import async_session_factory

    try:
        async with async_session_factory() as session:
            await asyncio.wait_for(session.execute(text("SELECT 1")), timeout=5.0)
        return JSONResponse({"status": "ok", "checks": {"database": "ok"}})
    except Exception:
        return JSONResponse(
            {"status": "degraded", "checks": {"database": "unreachable"}},
            status_code=503,
        )


@app.get("/health/ready")
async def health_ready():
    return await _check_readiness()


@app.get("/health")
async def health():
    return await _check_readiness()
