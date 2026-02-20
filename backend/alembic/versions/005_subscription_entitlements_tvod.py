"""subscription entitlements and tvod

Revision ID: 005
Revises: 004
Create Date: 2026-02-18

Adds:
  - title_offers table (TVOD rent/buy/free offers per title)
  - stream_sessions table (concurrent stream limit enforcement, user-scoped)
    NOTE: the existing viewing_sessions table (migration 003) is profile-scoped
    for viewing time limits; this is a distinct concept.
  - user_entitlements.package_id becomes nullable (supports TVOD entitlements)
  - user_entitlements.title_id added (for TVOD entitlements)
  - content_packages.tier and max_streams columns added
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. CREATE TABLE title_offers
    op.create_table(
        "title_offers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title_id", UUID(as_uuid=True), sa.ForeignKey("titles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("offer_type", sa.String(10), nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("rental_window_hours", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("offer_type IN ('rent', 'buy', 'free')", name="ck_title_offers_type"),
    )
    # Partial unique index: one active offer per type per title
    op.execute(
        "CREATE UNIQUE INDEX uix_title_offers_active_type "
        "ON title_offers (title_id, offer_type) WHERE is_active = TRUE"
    )
    op.create_index("ix_title_offers_title_active", "title_offers", ["title_id", "is_active"])

    # 2. CREATE TABLE stream_sessions (user-scoped, for concurrent stream limits)
    op.create_table(
        "stream_sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title_id", UUID(as_uuid=True), sa.ForeignKey("titles.id", ondelete="SET NULL"), nullable=True),
        sa.Column("content_type", sa.String(20), nullable=False, server_default="vod_title"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_stream_sessions_user_ended", "stream_sessions", ["user_id", "ended_at"])

    # 3. Make user_entitlements.package_id nullable (supports TVOD where package_id is NULL)
    op.alter_column("user_entitlements", "package_id", nullable=True)

    # 4. Add user_entitlements.title_id for TVOD entitlements
    op.add_column(
        "user_entitlements",
        sa.Column("title_id", UUID(as_uuid=True), sa.ForeignKey("titles.id", ondelete="CASCADE"), nullable=True),
    )
    op.execute(
        "CREATE INDEX ix_ue_user_title_expires "
        "ON user_entitlements (user_id, title_id, expires_at) WHERE title_id IS NOT NULL"
    )

    # 5. Add content_packages.tier, max_streams, price_cents, currency
    op.add_column("content_packages", sa.Column("tier", sa.String(20), nullable=True))
    op.add_column(
        "content_packages",
        sa.Column("max_streams", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "content_packages",
        sa.Column("price_cents", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "content_packages",
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
    )


def downgrade() -> None:
    op.drop_column("content_packages", "currency")
    op.drop_column("content_packages", "price_cents")
    op.drop_column("content_packages", "max_streams")
    op.drop_column("content_packages", "tier")

    op.execute("DROP INDEX IF EXISTS ix_ue_user_title_expires")
    op.drop_column("user_entitlements", "title_id")

    op.alter_column("user_entitlements", "package_id", nullable=False)

    op.drop_index("ix_stream_sessions_user_ended", table_name="stream_sessions")
    op.drop_table("stream_sessions")

    op.drop_index("ix_title_offers_title_active", table_name="title_offers")
    op.execute("DROP INDEX IF EXISTS uix_title_offers_active_type")
    op.drop_table("title_offers")
