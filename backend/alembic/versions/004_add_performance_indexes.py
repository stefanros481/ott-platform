"""add performance indexes for viewing sessions

Revision ID: 004
Revises: 003
Create Date: 2026-02-13
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the existing ASC index and recreate with DESC ordering on started_at
    # so that ORDER BY started_at DESC queries (history, newest-first) use it.
    op.drop_index("ix_vs_profile_started", table_name="viewing_sessions", if_exists=True)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vs_profile_started "
        "ON viewing_sessions (profile_id, started_at DESC)"
    )


def downgrade() -> None:
    op.drop_index("ix_vs_profile_started", table_name="viewing_sessions", if_exists=True)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vs_profile_started "
        "ON viewing_sessions (profile_id, started_at)"
    )
