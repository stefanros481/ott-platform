import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ContentPackage(Base):
    __tablename__ = "content_packages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)


class UserEntitlement(Base):
    __tablename__ = "user_entitlements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    package_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("content_packages.id"), nullable=False)
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
