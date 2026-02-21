import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ContentPackage(Base):
    __tablename__ = "content_packages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    tier: Mapped[str | None] = mapped_column(String(20), nullable=True)
    max_streams: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="NOK", server_default="NOK")


class TitleOffer(Base):
    __tablename__ = "title_offers"

    __table_args__ = (
        CheckConstraint("offer_type IN ('rent', 'buy', 'free')", name="ck_title_offers_type"),
        Index("ix_title_offers_title_active", "title_id", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("titles.id", ondelete="CASCADE"), nullable=False)
    offer_type: Mapped[str] = mapped_column(String(10), nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="NOK", server_default="NOK")
    rental_window_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class UserEntitlement(Base):
    __tablename__ = "user_entitlements"

    __table_args__ = (
        Index(
            "ix_ue_user_title_expires",
            "user_id", "title_id", "expires_at",
            postgresql_where=text("title_id IS NOT NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    package_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("content_packages.id"), nullable=True)
    title_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("titles.id", ondelete="CASCADE"), nullable=True
    )
    source_type: Mapped[str] = mapped_column(String(20), nullable=False, default="subscription")
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="entitlements")
    package: Mapped["ContentPackage"] = relationship()


class PackageContent(Base):
    __tablename__ = "package_contents"

    package_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("content_packages.id"), primary_key=True)
    content_type: Mapped[str] = mapped_column(String(20), primary_key=True)  # 'vod_title', 'channel'
    content_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)


from app.models.user import User  # noqa: E402, F401
