"""Notification endpoints for in-app alerts (catch-up expiry, etc.)."""

import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import and_, select, update
from datetime import datetime

from app.dependencies import DB, VerifiedProfileId
from app.models.notification import Notification

router = APIRouter()


class NotificationResponse(BaseModel):
    id: uuid.UUID
    notification_type: str
    title: str
    body: str
    deep_link: str | None
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/", response_model=list[NotificationResponse])
async def list_notifications(
    profile_id: VerifiedProfileId,
    db: DB,
    unread_only: bool = False,
    limit: int = 50,
):
    """Get notifications for the current profile."""
    q = select(Notification).where(Notification.profile_id == profile_id)
    if unread_only:
        q = q.where(Notification.is_read.is_(False))
    q = q.order_by(Notification.created_at.desc()).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/{notification_id}/read")
async def mark_read(
    notification_id: uuid.UUID,
    profile_id: VerifiedProfileId,
    db: DB,
):
    """Mark a notification as read."""
    result = await db.execute(
        update(Notification)
        .where(
            and_(
                Notification.id == notification_id,
                Notification.profile_id == profile_id,
            )
        )
        .values(is_read=True)
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    await db.commit()
    return {"status": "ok"}


@router.post("/read-all")
async def mark_all_read(
    profile_id: VerifiedProfileId,
    db: DB,
):
    """Mark all notifications as read for the current profile."""
    await db.execute(
        update(Notification)
        .where(
            and_(
                Notification.profile_id == profile_id,
                Notification.is_read.is_(False),
            )
        )
        .values(is_read=True)
    )
    await db.commit()
    return {"status": "ok"}
