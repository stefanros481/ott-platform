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

    # Feature 016: Attempt to restore SimLive channels on startup (non-blocking)
    try:
        from app.services.simlive_manager import SimLiveManager

        await SimLiveManager.restore_running_channels()
    except ImportError:
        print("  [TSTV] SimLiveManager not yet implemented, skipping restore.")
    except Exception as e:
        print(f"  [TSTV] Warning: SimLive restore failed: {e}")

    # Feature 016 T052: Hourly catch-up expiry notification checker
    import asyncio
    import logging

    _notification_logger = logging.getLogger("app.notifications")

    async def _expiry_check_loop() -> None:
        """Run check_expiring_catchup() every hour."""
        while True:
            try:
                await asyncio.sleep(3600)  # 1 hour
                from app.services.notification_service import check_expiring_catchup

                async with async_session_factory() as session:
                    count = await check_expiring_catchup(session)
                    _notification_logger.info("Expiry check: %d notifications created", count)
            except asyncio.CancelledError:
                break
            except Exception:
                _notification_logger.exception("Expiry check failed")

    expiry_task = asyncio.create_task(_expiry_check_loop())

    # Feature 016 T056: Hourly segment cleanup
    _cleanup_logger = logging.getLogger("app.simlive.cleanup")

    async def _segment_cleanup_loop() -> None:
        """Run cleanup_old_segments for all channels every hour."""
        while True:
            try:
                await asyncio.sleep(3600)
                from app.services.simlive_manager import SimLiveManager

                result = SimLiveManager.cleanup_all()
                _cleanup_logger.info(
                    "Segment cleanup: %d channels, %d segments deleted, %d bytes freed",
                    result["channels_processed"],
                    result["total_segments_deleted"],
                    result["total_bytes_freed"],
                )
            except asyncio.CancelledError:
                break
            except Exception:
                _cleanup_logger.exception("Segment cleanup failed")

    cleanup_task = asyncio.create_task(_segment_cleanup_loop())

    yield

    # Shutdown: cancel background tasks, close Redis, dispose engine
    for task in (expiry_task, cleanup_task):
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
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
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# Import and mount routers
from app.routers import (
    admin,
    analytics,
    auth,
    catalog,
    content_analytics,
    drm,
    epg,
    offers,
    parental_controls,
    recommendations,
    tstv,
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
# Feature 016: TSTV — DRM ClearKey KMS + Time-Shifted TV
app.include_router(drm.router, prefix="/api/v1/drm", tags=["DRM"])
app.include_router(tstv.router, prefix="/api/v1/tstv", tags=["TSTV"])
# Feature 016: In-app notifications (catch-up expiry alerts)
from app.routers import notifications
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])


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
