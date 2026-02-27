import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, LargeBinary, String, ForeignKey, CheckConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TSTVSession(Base):
    __tablename__ = "tstv_sessions"
    __table_args__ = (
        CheckConstraint("session_type IN ('startover', 'catchup')", name="ck_tstv_sessions_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    profile_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True
    )
    channel_id: Mapped[str] = mapped_column(String(20), nullable=False)
    schedule_entry_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("schedule_entries.id", ondelete="CASCADE"), nullable=False
    )
    session_type: Mapped[str] = mapped_column(String(20), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_position_s: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0")
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")


class Recording(Base):
    __tablename__ = "recordings"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'recording', 'completed', 'failed')",
            name="ck_recordings_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    schedule_entry_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("schedule_entries.id", ondelete="CASCADE"), nullable=False
    )
    channel_id: Mapped[str] = mapped_column(String(20), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="completed", server_default="completed"
    )


class DRMKey(Base):
    __tablename__ = "drm_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, unique=True)
    key_value: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    channel_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("channels.id", ondelete="CASCADE"), nullable=False
    )
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    rotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
