"""TSTV: start-over and catch-up TV schema

Revision ID: 007
Revises: 006
Create Date: 2026-02-25

Adds:
  - 6 columns to channels (cdn_channel_key, tstv flags, window hours)
  - 3 columns to schedule_entries (catchup/startover eligible, series_id)
  - Bookmark constraint swap (profile_id, content_id) -> (profile_id, content_id, content_type)
  - tstv_sessions table
  - recordings table (PVR stub)
  - drm_keys table
  - Supporting indexes
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add TSTV columns to channels
    op.add_column("channels", sa.Column("cdn_channel_key", sa.String(20), nullable=True))
    op.add_column("channels", sa.Column("tstv_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.add_column("channels", sa.Column("startover_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.add_column("channels", sa.Column("catchup_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.add_column("channels", sa.Column("catchup_window_hours", sa.Integer(), nullable=False, server_default=sa.text("168")))
    op.add_column("channels", sa.Column("cutv_window_hours", sa.Integer(), nullable=False, server_default=sa.text("168")))
    op.create_index("idx_channels_cdn_channel_key", "channels", ["cdn_channel_key"], unique=True, postgresql_where=sa.text("cdn_channel_key IS NOT NULL"))

    # 2. Add TSTV columns to schedule_entries
    op.add_column("schedule_entries", sa.Column("catchup_eligible", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.add_column("schedule_entries", sa.Column("startover_eligible", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.add_column("schedule_entries", sa.Column("series_id", sa.String(100), nullable=True))

    # 3. Bookmark constraint swap
    op.drop_constraint("uq_bookmark_profile_content", "bookmarks", type_="unique")
    op.create_unique_constraint(
        "uq_bookmark_profile_content_type",
        "bookmarks",
        ["profile_id", "content_id", "content_type"],
    )

    # 4. Create tstv_sessions table
    op.create_table(
        "tstv_sessions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("profile_id", UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True),
        sa.Column("channel_id", sa.String(20), nullable=False),
        sa.Column("schedule_entry_id", UUID(as_uuid=True), sa.ForeignKey("schedule_entries.id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_type", sa.String(20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("last_position_s", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.CheckConstraint("session_type IN ('startover', 'catchup')", name="ck_tstv_sessions_type"),
    )
    op.create_index("idx_tstv_sessions_user_started", "tstv_sessions", ["user_id", sa.text("started_at DESC")])
    op.create_index("idx_tstv_sessions_schedule_entry", "tstv_sessions", ["schedule_entry_id"])

    # 5. Create recordings table (PVR stub)
    op.create_table(
        "recordings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("schedule_entry_id", UUID(as_uuid=True), sa.ForeignKey("schedule_entries.id", ondelete="CASCADE"), nullable=False),
        sa.Column("channel_id", sa.String(20), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'completed'")),
        sa.CheckConstraint("status IN ('pending', 'recording', 'completed', 'failed')", name="ck_recordings_status"),
    )

    # 6. Create drm_keys table
    op.create_table(
        "drm_keys",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("key_id", UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("key_value", sa.LargeBinary(), nullable=False),
        sa.Column("channel_id", UUID(as_uuid=True), sa.ForeignKey("channels.id", ondelete="CASCADE"), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("rotated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_drm_keys_channel_active", "drm_keys", ["channel_id", "active"])


def downgrade() -> None:
    op.drop_table("drm_keys")
    op.drop_table("recordings")
    op.drop_table("tstv_sessions")

    # Restore bookmark constraint
    op.drop_constraint("uq_bookmark_profile_content_type", "bookmarks", type_="unique")
    op.create_unique_constraint("uq_bookmark_profile_content", "bookmarks", ["profile_id", "content_id"])

    # Remove schedule_entries columns
    op.drop_column("schedule_entries", "series_id")
    op.drop_column("schedule_entries", "startover_eligible")
    op.drop_column("schedule_entries", "catchup_eligible")

    # Remove channels columns
    op.drop_index("idx_channels_cdn_channel_key", table_name="channels")
    op.drop_column("channels", "cutv_window_hours")
    op.drop_column("channels", "catchup_window_hours")
    op.drop_column("channels", "catchup_enabled")
    op.drop_column("channels", "startover_enabled")
    op.drop_column("channels", "tstv_enabled")
    op.drop_column("channels", "cdn_channel_key")
