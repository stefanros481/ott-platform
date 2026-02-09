"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-02-09
"""

from typing import Sequence, Union

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure pgvector extension exists
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── Users & Auth ─────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("subscription_tier", sa.String(20), nullable=False, server_default="basic"),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "profiles",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("avatar_url", sa.String(500)),
        sa.Column("parental_rating", sa.String(10), server_default="TV-MA"),
        sa.Column("is_kids", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── Entitlements ─────────────────────────────────────────────────────
    op.create_table(
        "content_packages",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text()),
    )

    op.create_table(
        "user_entitlements",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("package_id", sa.UUID(), sa.ForeignKey("content_packages.id"), nullable=False),
        sa.Column("source_type", sa.String(20), nullable=False, server_default="subscription"),
        sa.Column("granted_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "package_contents",
        sa.Column("package_id", sa.UUID(), sa.ForeignKey("content_packages.id"), primary_key=True),
        sa.Column("content_type", sa.String(20), primary_key=True),
        sa.Column("content_id", sa.UUID(), primary_key=True),
    )

    # ── Catalog ──────────────────────────────────────────────────────────
    op.create_table(
        "genres",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(50), unique=True, nullable=False),
        sa.Column("slug", sa.String(50), unique=True, nullable=False),
    )

    op.create_table(
        "titles",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("title_type", sa.String(20), nullable=False),
        sa.Column("synopsis_short", sa.Text()),
        sa.Column("synopsis_long", sa.Text()),
        sa.Column("release_year", sa.Integer()),
        sa.Column("duration_minutes", sa.Integer()),
        sa.Column("age_rating", sa.String(10)),
        sa.Column("country_of_origin", sa.String(5)),
        sa.Column("language", sa.String(10)),
        sa.Column("poster_url", sa.String(500)),
        sa.Column("landscape_url", sa.String(500)),
        sa.Column("logo_url", sa.String(500)),
        sa.Column("hls_manifest_url", sa.String(500)),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("mood_tags", sa.ARRAY(sa.Text())),
        sa.Column("theme_tags", sa.ARRAY(sa.Text())),
        sa.Column("ai_description", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "title_genres",
        sa.Column("title_id", sa.UUID(), sa.ForeignKey("titles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("genre_id", sa.UUID(), sa.ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    op.create_table(
        "title_cast",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title_id", sa.UUID(), sa.ForeignKey("titles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("person_name", sa.String(200), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("character_name", sa.String(200)),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )

    op.create_table(
        "seasons",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title_id", sa.UUID(), sa.ForeignKey("titles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("season_number", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200)),
        sa.Column("synopsis", sa.Text()),
        sa.UniqueConstraint("title_id", "season_number"),
    )

    op.create_table(
        "episodes",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("season_id", sa.UUID(), sa.ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("episode_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("synopsis", sa.Text()),
        sa.Column("duration_minutes", sa.Integer()),
        sa.Column("hls_manifest_url", sa.String(500)),
        sa.UniqueConstraint("season_id", "episode_number"),
    )

    # ── EPG ──────────────────────────────────────────────────────────────
    op.create_table(
        "channels",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("channel_number", sa.Integer(), unique=True, nullable=False),
        sa.Column("logo_url", sa.String(500)),
        sa.Column("genre", sa.String(50)),
        sa.Column("is_hd", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("hls_live_url", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "schedule_entries",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("channel_id", sa.UUID(), sa.ForeignKey("channels.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("synopsis", sa.Text()),
        sa.Column("genre", sa.String(50)),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("age_rating", sa.String(10)),
        sa.Column("is_new", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_repeat", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("series_title", sa.String(200)),
        sa.Column("season_number", sa.Integer()),
        sa.Column("episode_number", sa.Integer()),
        sa.UniqueConstraint("channel_id", "start_time"),
    )
    op.create_index("idx_schedule_channel_time", "schedule_entries", ["channel_id", "start_time", "end_time"])
    op.create_index("idx_schedule_time_range", "schedule_entries", ["start_time", "end_time"])

    op.create_table(
        "channel_favorites",
        sa.Column("profile_id", sa.UUID(), sa.ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("channel_id", sa.UUID(), sa.ForeignKey("channels.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("position", sa.Integer()),
    )

    # ── Viewing State ────────────────────────────────────────────────────
    op.create_table(
        "bookmarks",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("profile_id", sa.UUID(), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content_type", sa.String(20), nullable=False),
        sa.Column("content_id", sa.UUID(), nullable=False),
        sa.Column("position_seconds", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "ratings",
        sa.Column("profile_id", sa.UUID(), sa.ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("title_id", sa.UUID(), sa.ForeignKey("titles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("rating", sa.SmallInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "watchlist",
        sa.Column("profile_id", sa.UUID(), sa.ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("title_id", sa.UUID(), sa.ForeignKey("titles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── Content Embeddings (AI) ──────────────────────────────────────────
    op.create_table(
        "content_embeddings",
        sa.Column("title_id", sa.UUID(), sa.ForeignKey("titles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("embedding", Vector(384), nullable=False),
        sa.Column("model_version", sa.String(50), nullable=False, server_default="all-MiniLM-L6-v2"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # HNSW index for approximate nearest neighbor search
    op.execute(
        "CREATE INDEX idx_content_embedding_hnsw ON content_embeddings "
        "USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )


def downgrade() -> None:
    op.drop_table("content_embeddings")
    op.drop_table("watchlist")
    op.drop_table("ratings")
    op.drop_table("bookmarks")
    op.drop_table("channel_favorites")
    op.drop_index("idx_schedule_time_range")
    op.drop_index("idx_schedule_channel_time")
    op.drop_table("schedule_entries")
    op.drop_table("channels")
    op.drop_table("episodes")
    op.drop_table("seasons")
    op.drop_table("title_cast")
    op.drop_table("title_genres")
    op.drop_table("titles")
    op.drop_table("genres")
    op.drop_table("package_contents")
    op.drop_table("user_entitlements")
    op.drop_table("content_packages")
    op.drop_table("refresh_tokens")
    op.drop_table("profiles")
    op.drop_table("users")
