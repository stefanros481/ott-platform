"""analytics events and query jobs

Revision ID: 006
Revises: 005
Create Date: 2026-02-21

Adds:
  - analytics_events table (client interaction events)
  - query_jobs table (async NL query processing)
  - Indexes supporting the 10 query patterns and job polling
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. CREATE TABLE analytics_events
    op.create_table(
        "analytics_events",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("event_type", sa.String(20), nullable=False),
        sa.Column(
            "title_id",
            UUID(as_uuid=True),
            sa.ForeignKey("titles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("service_type", sa.String(20), nullable=False),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "profile_id",
            UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("region", sa.String(10), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("session_id", UUID(as_uuid=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("watch_percentage", sa.SmallInteger(), nullable=True),
        sa.Column("extra_data", JSONB(), nullable=True),
        # CHECK constraints
        sa.CheckConstraint(
            "event_type IN ('play_start', 'play_pause', 'play_complete', 'browse', 'search')",
            name="ck_analytics_events_event_type",
        ),
        sa.CheckConstraint(
            "service_type IN ('Linear', 'VoD', 'SVoD', 'TSTV', 'Catch_up', 'Cloud_PVR')",
            name="ck_analytics_events_service_type",
        ),
        sa.CheckConstraint(
            "watch_percentage IS NULL OR (watch_percentage >= 0 AND watch_percentage <= 100)",
            name="ck_analytics_events_watch_percentage",
        ),
        sa.CheckConstraint(
            "duration_seconds IS NULL OR duration_seconds >= 0",
            name="ck_analytics_events_duration_seconds",
        ),
    )

    # Indexes for the 10 query patterns
    op.create_index(
        "idx_analytics_events_user_time",
        "analytics_events",
        ["user_id", sa.text("occurred_at DESC")],
    )
    op.create_index(
        "idx_analytics_events_service_time",
        "analytics_events",
        ["service_type", sa.text("occurred_at DESC")],
    )
    op.create_index(
        "idx_analytics_events_region_time",
        "analytics_events",
        ["region", sa.text("occurred_at DESC")],
    )
    op.create_index(
        "idx_analytics_events_title",
        "analytics_events",
        ["title_id"],
        postgresql_where=sa.text("title_id IS NOT NULL"),
    )
    op.create_index(
        "idx_analytics_events_type_time",
        "analytics_events",
        ["event_type", sa.text("occurred_at DESC")],
    )

    # 2. CREATE TABLE query_jobs
    op.create_table(
        "query_jobs",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("status", sa.String(10), nullable=False, server_default="pending"),
        sa.Column(
            "submitted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result", JSONB(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'complete', 'failed')",
            name="ck_query_jobs_status",
        ),
    )

    op.create_index(
        "idx_query_jobs_user_submitted",
        "query_jobs",
        ["user_id", sa.text("submitted_at DESC")],
    )


def downgrade() -> None:
    op.drop_table("query_jobs")
    op.drop_table("analytics_events")
