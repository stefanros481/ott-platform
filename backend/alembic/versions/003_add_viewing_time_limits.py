"""add viewing time limits tables and columns

Revision ID: 003
Revises: 002
Create Date: 2026-02-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -- Extend users table with PIN fields --
    op.add_column(
        "users",
        sa.Column("pin_hash", sa.String(255), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("pin_failed_attempts", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "users",
        sa.Column("pin_lockout_until", sa.DateTime(timezone=True), nullable=True),
    )

    # -- Extend titles table with is_educational --
    op.add_column(
        "titles",
        sa.Column("is_educational", sa.Boolean(), nullable=False, server_default="false"),
    )

    # -- Create viewing_time_configs --
    op.create_table(
        "viewing_time_configs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("profile_id", UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("weekday_limit_minutes", sa.Integer(), nullable=True),
        sa.Column("weekend_limit_minutes", sa.Integer(), nullable=True),
        sa.Column("reset_hour", sa.Integer(), nullable=False, server_default="6"),
        sa.Column("educational_exempt", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("timezone", sa.String(50), nullable=False, server_default="'UTC'"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("profile_id", name="uq_vtc_profile"),
        sa.CheckConstraint(
            "weekday_limit_minutes IS NULL OR (weekday_limit_minutes >= 15 AND weekday_limit_minutes <= 480 AND weekday_limit_minutes % 15 = 0)",
            name="ck_vtc_weekday_range",
        ),
        sa.CheckConstraint(
            "weekend_limit_minutes IS NULL OR (weekend_limit_minutes >= 15 AND weekend_limit_minutes <= 480 AND weekend_limit_minutes % 15 = 0)",
            name="ck_vtc_weekend_range",
        ),
        sa.CheckConstraint(
            "reset_hour >= 0 AND reset_hour <= 23",
            name="ck_vtc_reset_hour",
        ),
    )

    # -- Create viewing_time_balances --
    op.create_table(
        "viewing_time_balances",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("profile_id", UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reset_date", sa.Date(), nullable=False),
        sa.Column("used_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("educational_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_unlimited_override", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("profile_id", "reset_date", name="uq_vtb_profile_date"),
    )

    # -- Create viewing_sessions --
    op.create_table(
        "viewing_sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("profile_id", UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title_id", UUID(as_uuid=True), sa.ForeignKey("titles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("device_id", sa.String(100), nullable=False),
        sa.Column("device_type", sa.String(20), nullable=True),
        sa.Column("is_educational", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("paused_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Partial index for active sessions (concurrent stream check)
    op.create_index(
        "ix_vs_profile_active",
        "viewing_sessions",
        ["profile_id"],
        postgresql_where=sa.text("ended_at IS NULL"),
    )
    # Composite index for viewing history queries
    op.create_index(
        "ix_vs_profile_started",
        "viewing_sessions",
        ["profile_id", sa.text("started_at DESC")],
    )

    # -- Create time_grants --
    op.create_table(
        "time_grants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("profile_id", UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("granted_by_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("granted_minutes", sa.Integer(), nullable=True),
        sa.Column("is_remote", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("granted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("time_grants")
    op.drop_index("ix_vs_profile_started", table_name="viewing_sessions")
    op.drop_index("ix_vs_profile_active", table_name="viewing_sessions")
    op.drop_table("viewing_sessions")
    op.drop_table("viewing_time_balances")
    op.drop_table("viewing_time_configs")
    op.drop_column("titles", "is_educational")
    op.drop_column("users", "pin_lockout_until")
    op.drop_column("users", "pin_failed_attempts")
    op.drop_column("users", "pin_hash")
