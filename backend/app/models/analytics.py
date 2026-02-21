"""SQLAlchemy models for analytics events and query jobs."""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AnalyticsEvent(Base):
    """Records a single user interaction with content."""

    __tablename__ = "analytics_events"
    __table_args__ = (
        CheckConstraint(
            "event_type IN ('play_start', 'play_pause', 'play_complete', 'browse', 'search')",
            name="ck_analytics_events_event_type",
        ),
        CheckConstraint(
            "service_type IN ('Linear', 'VoD', 'SVoD', 'TSTV', 'Catch_up', 'Cloud_PVR')",
            name="ck_analytics_events_service_type",
        ),
        CheckConstraint(
            "watch_percentage IS NULL OR (watch_percentage >= 0 AND watch_percentage <= 100)",
            name="ck_analytics_events_watch_percentage",
        ),
        CheckConstraint(
            "duration_seconds IS NULL OR duration_seconds >= 0",
            name="ck_analytics_events_duration_seconds",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_type: Mapped[str] = mapped_column(String(20), nullable=False)
    title_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("titles.id", ondelete="SET NULL"),
        nullable=True,
    )
    service_type: Mapped[str] = mapped_column(String(20), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    profile_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
    region: Mapped[str] = mapped_column(String(10), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    watch_percentage: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    extra_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class QueryJob(Base):
    """Tracks async query processing for complex natural language queries."""

    __tablename__ = "query_jobs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'complete', 'failed')",
            name="ck_query_jobs_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="pending")
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
