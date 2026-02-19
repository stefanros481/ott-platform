"""StreamSession model — user-scoped concurrent stream tracking for entitlement enforcement.

NOTE: This is distinct from the profile-scoped ViewingSession in viewing_time.py,
which tracks per-profile watch time for parental controls. StreamSession tracks
concurrent streams per user for subscription stream-limit enforcement.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class StreamSession(Base):
    __tablename__ = "stream_sessions"

    __table_args__ = (
        Index("ix_stream_sessions_user_ended", "user_id", "ended_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("titles.id", ondelete="SET NULL"), nullable=True
    )
    content_type: Mapped[str] = mapped_column(String(20), nullable=False, default="vod_title")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_heartbeat_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    title: Mapped["Title"] = relationship()


# Resolve forward reference
from app.models.catalog import Title  # noqa: E402, F401
