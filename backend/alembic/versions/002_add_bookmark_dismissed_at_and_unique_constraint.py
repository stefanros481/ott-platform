"""add bookmark dismissed_at and unique constraint

Revision ID: 002
Revises: 001
Create Date: 2026-02-12
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add dismissed_at column
    op.add_column(
        "bookmarks",
        sa.Column("dismissed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Deduplicate existing rows before adding unique constraint:
    # keep the most recently updated bookmark per (profile_id, content_id)
    op.execute(
        """
        DELETE FROM bookmarks
        WHERE id NOT IN (
            SELECT DISTINCT ON (profile_id, content_id) id
            FROM bookmarks
            ORDER BY profile_id, content_id, updated_at DESC
        )
        """
    )

    # Add unique constraint
    op.create_unique_constraint(
        "uq_bookmark_profile_content",
        "bookmarks",
        ["profile_id", "content_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_bookmark_profile_content", "bookmarks", type_="unique")
    op.drop_column("bookmarks", "dismissed_at")
