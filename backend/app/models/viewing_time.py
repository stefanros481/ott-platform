"""Viewing time models — config, balance, sessions, grants."""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ViewingTimeConfig(Base):
    __tablename__ = "viewing_time_configs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    weekday_limit_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True, default=120)
    weekend_limit_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True, default=180)
    reset_hour: Mapped[int] = mapped_column(Integer, nullable=False, default=6, server_default="6")
    educational_exempt: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="UTC", server_default="'UTC'")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("profile_id", name="uq_vtc_profile"),
        CheckConstraint(
            "weekday_limit_minutes IS NULL OR (weekday_limit_minutes >= 15 AND weekday_limit_minutes <= 480 AND weekday_limit_minutes % 15 = 0)",
            name="ck_vtc_weekday_range",
        ),
        CheckConstraint(
            "weekend_limit_minutes IS NULL OR (weekend_limit_minutes >= 15 AND weekend_limit_minutes <= 480 AND weekend_limit_minutes % 15 = 0)",
            name="ck_vtc_weekend_range",
        ),
        CheckConstraint(
            "reset_hour >= 0 AND reset_hour <= 23",
            name="ck_vtc_reset_hour",
        ),
    )


class ViewingTimeBalance(Base):
    __tablename__ = "viewing_time_balances"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    reset_date: Mapped[date] = mapped_column(Date, nullable=False)
    used_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    educational_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_unlimited_override: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("profile_id", "reset_date", name="uq_vtb_profile_date"),
    )


class ViewingSession(Base):
    __tablename__ = "viewing_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    title_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("titles.id", ondelete="CASCADE"), nullable=False
    )
    device_id: Mapped[str] = mapped_column(String(100), nullable=False)
    device_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_educational: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_heartbeat_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    title: Mapped["Title"] = relationship()

    __table_args__ = (
        Index("ix_vs_profile_active", "profile_id", postgresql_where=text("ended_at IS NULL")),
        # Migration 004 recreates this index with DESC on started_at for history queries
        Index("ix_vs_profile_started", "profile_id", "started_at"),
    )


class TimeGrant(Base):
    __tablename__ = "time_grants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    granted_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    granted_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_remote: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


# Resolve forward reference
from app.models.catalog import Title  # noqa: E402, F401
