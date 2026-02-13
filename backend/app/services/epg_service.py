"""Service layer for EPG (channels, schedule, favourites)."""

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.epg import Channel, ChannelFavorite, ScheduleEntry
from app.services.search_service import escape_like


async def get_channels(
    db: AsyncSession,
    profile_id: uuid.UUID | None = None,
) -> list[dict]:
    """Return all channels.

    When *profile_id* is supplied the result includes an ``is_favorite`` flag
    and favourites are sorted to the top, followed by channel number.
    """
    result = await db.execute(select(Channel).order_by(Channel.channel_number))
    channels = result.scalars().all()

    if profile_id is None:
        return [
            {**_channel_dict(ch), "is_favorite": False}
            for ch in channels
        ]

    # Fetch favourite channel IDs for this profile.
    fav_result = await db.execute(
        select(ChannelFavorite.channel_id).where(
            ChannelFavorite.profile_id == profile_id
        )
    )
    fav_ids: set[uuid.UUID] = {row[0] for row in fav_result.fetchall()}

    channel_dicts = [
        {**_channel_dict(ch), "is_favorite": ch.id in fav_ids}
        for ch in channels
    ]
    # AI ordering: favourites first, then by channel number.
    channel_dicts.sort(key=lambda c: (not c["is_favorite"], c["channel_number"]))
    return channel_dicts


def _channel_dict(ch: Channel) -> dict:
    return {
        "id": ch.id,
        "name": ch.name,
        "channel_number": ch.channel_number,
        "logo_url": ch.logo_url,
        "genre": ch.genre,
        "is_hd": ch.is_hd,
    }


async def get_schedule(
    db: AsyncSession,
    channel_id: uuid.UUID,
    day: date,
) -> list[ScheduleEntry]:
    """Return schedule entries for *channel_id* on *day*, ordered by start_time."""
    day_start = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
    day_end = datetime(day.year, day.month, day.day, 23, 59, 59, tzinfo=timezone.utc)

    result = await db.execute(
        select(ScheduleEntry)
        .where(
            and_(
                ScheduleEntry.channel_id == channel_id,
                ScheduleEntry.start_time >= day_start,
                ScheduleEntry.start_time <= day_end,
            )
        )
        .order_by(ScheduleEntry.start_time)
    )
    return list(result.scalars().all())


async def get_now_playing(db: AsyncSession) -> list[dict]:
    """Return the currently airing programme (and next) for every channel."""
    now = datetime.now(timezone.utc)

    # Current programmes.
    current_q = await db.execute(
        select(ScheduleEntry)
        .where(
            and_(
                ScheduleEntry.start_time <= now,
                ScheduleEntry.end_time > now,
            )
        )
        .order_by(ScheduleEntry.channel_id)
    )
    current_entries = current_q.scalars().all()

    # Build a lookup of channel_id -> current entry.
    channel_ids = [e.channel_id for e in current_entries]
    if not channel_ids:
        return []

    # Fetch channels for those entries.
    ch_result = await db.execute(
        select(Channel).where(Channel.id.in_(channel_ids))
    )
    channels_by_id = {ch.id: ch for ch in ch_result.scalars().all()}

    results: list[dict] = []
    for entry in current_entries:
        channel = channels_by_id.get(entry.channel_id)
        if channel is None:
            continue

        # Find the next programme on the same channel.
        next_q = await db.execute(
            select(ScheduleEntry)
            .where(
                and_(
                    ScheduleEntry.channel_id == entry.channel_id,
                    ScheduleEntry.start_time >= entry.end_time,
                )
            )
            .order_by(ScheduleEntry.start_time)
            .limit(1)
        )
        next_entry = next_q.scalar_one_or_none()

        results.append(
            {
                "channel": {**_channel_dict(channel), "is_favorite": False},
                "current_program": entry,
                "next_program": next_entry,
            }
        )

    return results


async def search_schedule(
    db: AsyncSession,
    query: str,
) -> list[ScheduleEntry]:
    """Search schedule entries by title (case-insensitive LIKE)."""
    result = await db.execute(
        select(ScheduleEntry)
        .where(ScheduleEntry.title.ilike(f"%{escape_like(query)}%"))
        .order_by(ScheduleEntry.start_time)
        .limit(50)
    )
    return list(result.scalars().all())


async def add_favorite(
    db: AsyncSession,
    profile_id: uuid.UUID,
    channel_id: uuid.UUID,
) -> None:
    """Mark a channel as favourite for a profile (idempotent)."""
    existing = await db.execute(
        select(ChannelFavorite).where(
            and_(
                ChannelFavorite.profile_id == profile_id,
                ChannelFavorite.channel_id == channel_id,
            )
        )
    )
    if existing.scalar_one_or_none() is not None:
        return  # Already a favourite.

    db.add(ChannelFavorite(profile_id=profile_id, channel_id=channel_id))
    await db.commit()


async def remove_favorite(
    db: AsyncSession,
    profile_id: uuid.UUID,
    channel_id: uuid.UUID,
) -> None:
    """Remove a channel favourite for a profile (idempotent)."""
    await db.execute(
        delete(ChannelFavorite).where(
            and_(
                ChannelFavorite.profile_id == profile_id,
                ChannelFavorite.channel_id == channel_id,
            )
        )
    )
    await db.commit()
