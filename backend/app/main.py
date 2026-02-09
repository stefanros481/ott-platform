from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # Startup: nothing needed for now (DB pool is lazy)
    yield
    # Shutdown: dispose engine
    from app.database import engine

    await engine.dispose()


app = FastAPI(
    title="OTT Platform PoC",
    description="AI-Native OTT Streaming Platform - Proof of Concept",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and mount routers
from app.routers import admin, auth, catalog, epg, recommendations, viewing

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(catalog.router, prefix="/api/v1/catalog", tags=["Catalog"])
app.include_router(epg.router, prefix="/api/v1/epg", tags=["EPG"])
app.include_router(recommendations.router, prefix="/api/v1/recommendations", tags=["Recommendations"])
app.include_router(viewing.router, prefix="/api/v1/viewing", tags=["Viewing"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])


@app.get("/health")
async def health():
    return {"status": "ok"}
