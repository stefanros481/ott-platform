import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    channel_number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(500))
    genre: Mapped[str | None] = mapped_column(String(50))
    is_hd: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    hls_live_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    schedule_entries: Mapped[list["ScheduleEntry"]] = relationship(back_populates="channel")


class ScheduleEntry(Base):
    __tablename__ = "schedule_entries"
    __table_args__ = (
        UniqueConstraint("channel_id", "start_time"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    channel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    synopsis: Mapped[str | None] = mapped_column(Text)
    genre: Mapped[str | None] = mapped_column(String(50))
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    age_rating: Mapped[str | None] = mapped_column(String(10))
    is_new: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_repeat: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    series_title: Mapped[str | None] = mapped_column(String(200))
    season_number: Mapped[int | None] = mapped_column(Integer)
    episode_number: Mapped[int | None] = mapped_column(Integer)

    channel: Mapped["Channel"] = relationship(back_populates="schedule_entries")


class ChannelFavorite(Base):
    __tablename__ = "channel_favorites"

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True)
    channel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE"), primary_key=True)
    position: Mapped[int | None] = mapped_column(Integer)
