"""Notification service for catch-up/start-over expiry alerts."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.epg import Channel, ScheduleEntry
from app.models.notification import Notification
from app.models.viewing import Bookmark

logger = logging.getLogger(__name__)


async def check_expiring_catchup(db: AsyncSession) -> int:
    """Find TSTV bookmarks whose catch-up window expires within 24 hours.

    Creates one in-app notification per bookmark. Skips bookmarks that
    already have a notification (idempotent).

    Returns the number of notifications created.
    """
    now = datetime.now(timezone.utc)
    expiry_horizon = now + timedelta(hours=24)

    # Find incomplete TSTV bookmarks
    bk_q = (
        select(Bookmark, ScheduleEntry, Channel)
        .join(ScheduleEntry, ScheduleEntry.id == Bookmark.content_id)
        .join(Channel, Channel.id == ScheduleEntry.channel_id)
        .where(
            and_(
                Bookmark.content_type.in_(["tstv_catchup", "tstv_startover"]),
                Bookmark.completed.is_(False),
                Bookmark.dismissed_at.is_(None),
            )
        )
    )
    result = await db.execute(bk_q)
    rows = result.all()

    created = 0

    for bookmark, entry, channel in rows:
        # Compute expiry from end_time + channel CUTV window
        cutv_hours = getattr(channel, "cutv_window_hours", 168)
        expires_at = entry.end_time + timedelta(hours=cutv_hours)

        # Only notify if expiring within 24h and not already expired
        if expires_at > now and expires_at <= expiry_horizon:
            # Check if notification already exists for this bookmark
            existing = await db.execute(
                select(Notification.id).where(
                    and_(
                        Notification.profile_id == bookmark.profile_id,
                        Notification.notification_type == "catchup_expiry",
                        Notification.deep_link.contains(str(entry.id)),
                    )
                )
            )
            if existing.scalar_one_or_none() is not None:
                continue

            hours_left = max(1, int((expires_at - now).total_seconds() / 3600))
            notification = Notification(
                profile_id=bookmark.profile_id,
                notification_type="catchup_expiry",
                title=f'"{entry.title}" expires soon',
                body=f"Your catch-up recording on {channel.name} expires in {hours_left}h. Watch it before it's gone!",
                deep_link=f"/play/live/{channel.id}?catchup={entry.id}",
            )
            db.add(notification)
            created += 1

    if created:
        await db.commit()
        logger.info("Created %d catch-up expiry notifications", created)
    else:
        logger.debug("No new expiry notifications needed")

    return created
