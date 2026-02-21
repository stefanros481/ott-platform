"""Analytics router — client-side event ingestion."""

from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

from app.dependencies import CurrentUser, DB
from app.schemas.analytics import AnalyticsEventCreate
from app.services import analytics_service

router = APIRouter()


@router.post("/events", status_code=status.HTTP_201_CREATED)
async def ingest_analytics_event(
    body: AnalyticsEventCreate,
    user: CurrentUser,
    db: DB,
) -> dict:
    """Record an analytics event emitted by the client.

    Any authenticated user can emit events. Failure is returned as HTTP 500
    so the client can handle it silently (FR-011).
    """
    try:
        event = await analytics_service.ingest_event(db, user.id, body)
        return {"id": str(event.id)}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record analytics event",
        ) from exc
