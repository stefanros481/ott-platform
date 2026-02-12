"""Service layer for content recommendations backed by pgvector similarity search."""

import logging
import math
import uuid
from datetime import datetime, timezone

import numpy as np
from sqlalchemy import bindparam, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import Genre, Title, TitleGenre
from app.models.embedding import ContentEmbedding
from app.models.viewing import Bookmark, Rating
from app.schemas.viewing import ContinueWatchingItem

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _title_to_rail_item(row, similarity: float | None = None) -> dict:
    """Convert a Title row (or Row result) into a ContentRailItem-compatible dict."""
    return {
        "id": row.id,
        "title": row.title,
        "title_type": row.title_type,
        "poster_url": row.poster_url,
        "landscape_url": row.landscape_url,
        "synopsis_short": row.synopsis_short,
        "release_year": row.release_year,
        "age_rating": row.age_rating,
        "similarity_score": similarity,
    }


# ---------------------------------------------------------------------------
# Core recommendation functions
# ---------------------------------------------------------------------------

async def get_similar_titles(
    db: AsyncSession,
    title_id: uuid.UUID,
    limit: int = 12,
    *,
    allowed_ratings: list[str] | None = None,
) -> list[dict]:
    """Return titles most similar to *title_id* using pgvector cosine distance.

    Algorithm:
      1. Fetch the embedding for the source title.
      2. Run a nearest-neighbour query with ``<=>`` (cosine distance).
      3. Convert distance to similarity score (1 - distance).
    """
    # 1. Get source embedding.
    src = await db.execute(
        select(ContentEmbedding.embedding).where(
            ContentEmbedding.title_id == title_id
        )
    )
    src_row = src.first()
    if src_row is None:
        return []

    source_vector = src_row[0]

    # 2. Nearest-neighbour query.
    # Convert numpy floats to plain Python floats for pgvector compatibility.
    vec_str = "[" + ",".join(str(float(v)) for v in source_vector) + "]"
    age_filter = ""
    bind_kw: dict = dict(query_vec=vec_str, source_id=title_id, lim=limit)
    extra_params = []
    if allowed_ratings is not None:
        age_filter = "AND t.age_rating IN :allowed"
        bind_kw["allowed"] = list(allowed_ratings)
        extra_params.append(bindparam("allowed", expanding=True))
    stmt = text(
        f"""
        SELECT t.id, t.title, t.title_type, t.poster_url, t.landscape_url,
               t.synopsis_short, t.release_year, t.age_rating,
               1 - (ce.embedding <=> CAST(:query_vec AS vector)) AS similarity
        FROM content_embeddings ce
        JOIN titles t ON t.id = ce.title_id
        WHERE ce.title_id != :source_id {age_filter}
        ORDER BY ce.embedding <=> CAST(:query_vec AS vector)
        LIMIT :lim
        """
    )
    if extra_params:
        stmt = stmt.bindparams(*extra_params)
    result = await db.execute(stmt.params(**bind_kw))

    return [
        {
            "id": r.id,
            "title": r.title,
            "title_type": r.title_type,
            "poster_url": r.poster_url,
            "landscape_url": r.landscape_url,
            "synopsis_short": r.synopsis_short,
            "release_year": r.release_year,
            "age_rating": r.age_rating,
            "similarity_score": float(r.similarity) if r.similarity is not None else None,
        }
        for r in result.fetchall()
    ]


async def get_for_you_rail(
    db: AsyncSession,
    profile_id: uuid.UUID,
    limit: int = 20,
    *,
    allowed_ratings: list[str] | None = None,
) -> list[dict]:
    """Build a 'For You' rail by averaging the profile's interaction embeddings.

    Steps:
      1. Gather title IDs the profile has bookmarked or positively rated.
      2. Fetch those embeddings and compute the centroid vector.
      3. Run a similarity search against the centroid, excluding already-watched.
    """
    # 1. Collect interacted title IDs.
    bookmark_q = await db.execute(
        select(Bookmark.content_id).where(Bookmark.profile_id == profile_id)
    )
    bookmarked_ids = {row[0] for row in bookmark_q.fetchall()}

    rating_q = await db.execute(
        select(Rating.title_id).where(
            Rating.profile_id == profile_id,
            Rating.rating == 1,
        )
    )
    rated_ids = {row[0] for row in rating_q.fetchall()}

    interacted_ids = bookmarked_ids | rated_ids
    if not interacted_ids:
        return []

    # 2. Fetch embeddings for interacted titles.
    emb_q = await db.execute(
        select(ContentEmbedding.embedding).where(
            ContentEmbedding.title_id.in_(interacted_ids)
        )
    )
    vectors = [row[0] for row in emb_q.fetchall()]
    if not vectors:
        return []

    centroid = np.mean(vectors, axis=0).tolist()

    # 3. Similarity search excluding already-interacted titles.
    # Build exclusion list as a comma-separated string of quoted UUIDs for the SQL.
    exclusion_list = ", ".join(f"'{uid}'" for uid in interacted_ids)

    # Convert to plain float string for pgvector compatibility.
    vec_str = "[" + ",".join(str(float(v)) for v in centroid) + "]"

    age_filter = ""
    bind_kw: dict = dict(query_vec=vec_str, lim=limit)
    extra_params = []
    if allowed_ratings is not None:
        age_filter = "AND t.age_rating IN :allowed"
        bind_kw["allowed"] = list(allowed_ratings)
        extra_params.append(bindparam("allowed", expanding=True))

    stmt = text(
        f"""
        SELECT t.id, t.title, t.title_type, t.poster_url, t.landscape_url,
               t.synopsis_short, t.release_year, t.age_rating,
               1 - (ce.embedding <=> CAST(:query_vec AS vector)) AS similarity
        FROM content_embeddings ce
        JOIN titles t ON t.id = ce.title_id
        WHERE ce.title_id NOT IN ({exclusion_list}) {age_filter}
        ORDER BY ce.embedding <=> CAST(:query_vec AS vector)
        LIMIT :lim
        """
    )
    if extra_params:
        stmt = stmt.bindparams(*extra_params)
    result = await db.execute(stmt.params(**bind_kw))

    return [
        {
            "id": r.id,
            "title": r.title,
            "title_type": r.title_type,
            "poster_url": r.poster_url,
            "landscape_url": r.landscape_url,
            "synopsis_short": r.synopsis_short,
            "release_year": r.release_year,
            "age_rating": r.age_rating,
            "similarity_score": float(r.similarity) if r.similarity is not None else None,
        }
        for r in result.fetchall()
    ]


async def _continue_watching_rail(
    db: AsyncSession,
    profile_id: uuid.UUID,
    limit: int = 20,
    *,
    allowed_ratings: list[str] | None = None,
) -> list[dict]:
    """Fetch bookmarks that are not completed, most recent first."""
    age_filter = ""
    bind_kw: dict = dict(pid=profile_id, lim=limit)
    extra_params = []
    if allowed_ratings is not None:
        age_filter = "AND t.age_rating IN :allowed"
        bind_kw["allowed"] = list(allowed_ratings)
        extra_params.append(bindparam("allowed", expanding=True))
    stmt = text(
        f"""
        SELECT b.content_id AS id, t.title, t.title_type, t.poster_url,
               t.landscape_url, t.synopsis_short, t.release_year, t.age_rating,
               b.position_seconds, b.duration_seconds
        FROM bookmarks b
        JOIN titles t ON t.id = b.content_id
        WHERE b.profile_id = :pid AND b.completed = false {age_filter}
        ORDER BY b.updated_at DESC
        LIMIT :lim
        """
    )
    if extra_params:
        stmt = stmt.bindparams(*extra_params)
    result = await db.execute(stmt.params(**bind_kw))
    return [
        {
            "id": r.id,
            "title": r.title,
            "title_type": r.title_type,
            "poster_url": r.poster_url,
            "landscape_url": r.landscape_url,
            "synopsis_short": r.synopsis_short,
            "release_year": r.release_year,
            "age_rating": r.age_rating,
            "similarity_score": None,
        }
        for r in result.fetchall()
    ]


async def _new_releases_rail(
    db: AsyncSession, limit: int = 20, *, allowed_ratings: list[str] | None = None
) -> list[dict]:
    query = select(Title).order_by(Title.created_at.desc()).limit(limit)
    if allowed_ratings is not None:
        query = query.where(Title.age_rating.in_(allowed_ratings))
    result = await db.execute(query)
    return [_title_to_rail_item(t) for t in result.scalars().all()]


async def _trending_rail(
    db: AsyncSession, limit: int = 20, *, allowed_ratings: list[str] | None = None
) -> list[dict]:
    """Titles with the most bookmarks (proxy for popularity)."""
    age_filter = ""
    bind_kw: dict = dict(lim=limit)
    extra_params = []
    if allowed_ratings is not None:
        age_filter = "WHERE t.age_rating IN :allowed"
        bind_kw["allowed"] = list(allowed_ratings)
        extra_params.append(bindparam("allowed", expanding=True))
    stmt = text(
        f"""
        SELECT t.id, t.title, t.title_type, t.poster_url, t.landscape_url,
               t.synopsis_short, t.release_year, t.age_rating,
               COUNT(b.id) AS bm_count
        FROM titles t
        LEFT JOIN bookmarks b ON b.content_id = t.id
        {age_filter}
        GROUP BY t.id
        ORDER BY bm_count DESC
        LIMIT :lim
        """
    )
    if extra_params:
        stmt = stmt.bindparams(*extra_params)
    result = await db.execute(stmt.params(**bind_kw)
    )
    return [
        {
            "id": r.id,
            "title": r.title,
            "title_type": r.title_type,
            "poster_url": r.poster_url,
            "landscape_url": r.landscape_url,
            "synopsis_short": r.synopsis_short,
            "release_year": r.release_year,
            "age_rating": r.age_rating,
            "similarity_score": None,
        }
        for r in result.fetchall()
    ]


async def _top_genre_rail(
    db: AsyncSession,
    profile_id: uuid.UUID,
    limit: int = 20,
    *,
    allowed_ratings: list[str] | None = None,
) -> dict | None:
    """Build a rail for the profile's most-watched genre.

    Returns None if there is no viewing history.
    """
    # Find most-watched genre via bookmarks -> title -> title_genres -> genre.
    result = await db.execute(
        text(
            """
            SELECT g.name, g.id, COUNT(*) AS cnt
            FROM bookmarks b
            JOIN title_genres tg ON tg.title_id = b.content_id
            JOIN genres g ON g.id = tg.genre_id
            WHERE b.profile_id = :pid
            GROUP BY g.id, g.name
            ORDER BY cnt DESC
            LIMIT 1
            """
        ).bindparams(pid=profile_id)
    )
    row = result.first()
    if row is None:
        return None

    genre_name: str = row.name
    genre_id: uuid.UUID = row.id

    # Fetch titles in that genre.
    age_filter = ""
    bind_kw: dict = dict(gid=genre_id, lim=limit)
    extra_params = []
    if allowed_ratings is not None:
        age_filter = "AND t.age_rating IN :allowed"
        bind_kw["allowed"] = list(allowed_ratings)
        extra_params.append(bindparam("allowed", expanding=True))
    stmt = text(
        f"""
        SELECT t.id, t.title, t.title_type, t.poster_url, t.landscape_url,
               t.synopsis_short, t.release_year, t.age_rating
        FROM titles t
        JOIN title_genres tg ON tg.title_id = t.id
        WHERE tg.genre_id = :gid {age_filter}
        ORDER BY t.created_at DESC
        LIMIT :lim
        """
    )
    if extra_params:
        stmt = stmt.bindparams(*extra_params)
    titles_q = await db.execute(stmt.params(**bind_kw))
    items = [
        {
            "id": r.id,
            "title": r.title,
            "title_type": r.title_type,
            "poster_url": r.poster_url,
            "landscape_url": r.landscape_url,
            "synopsis_short": r.synopsis_short,
            "release_year": r.release_year,
            "age_rating": r.age_rating,
            "similarity_score": None,
        }
        for r in titles_q.fetchall()
    ]
    if not items:
        return None

    return {
        "name": f"Top in {genre_name}",
        "rail_type": "genre",
        "items": items,
    }


# ---------------------------------------------------------------------------
# Resumption scoring (US3 / US4)
# ---------------------------------------------------------------------------


async def compute_resumption_scores(
    db: AsyncSession,
    bookmarks: list[ContinueWatchingItem],
    device_type: str = "web",
    hour_of_day: int | None = None,
) -> dict[str, float]:
    """Score bookmarks by predicted resumption likelihood.

    Returns a mapping of ``str(bookmark.id)`` to a score between 0.0 and 1.0.
    An empty dict signals the caller should fall back to recency ordering.
    """
    if not bookmarks:
        return {}

    try:
        now = datetime.now(timezone.utc)
        scores: dict[str, float] = {}

        # Pre-compute series momentum: for each title that the bookmark's
        # episode belongs to, count recently completed bookmarks in the same
        # series.  Join path: episodes -> seasons -> titles.
        episode_ids = [
            str(b.content_id) for b in bookmarks if b.content_type == "episode"
        ]
        series_completed_counts: dict[str, int] = {}
        if episode_ids:
            id_list = ", ".join(f"'{eid}'" for eid in episode_ids)
            result = await db.execute(
                text(
                    f"""
                    SELECT e_target.id AS episode_id,
                           COUNT(b2.id) AS completed_count
                    FROM episodes e_target
                    JOIN seasons s ON s.id = e_target.season_id
                    LEFT JOIN episodes e_same ON e_same.season_id IN (
                        SELECT s2.id FROM seasons s2 WHERE s2.title_id = s.title_id
                    )
                    LEFT JOIN bookmarks b2 ON b2.content_id = e_same.id
                        AND b2.completed = true
                        AND b2.updated_at > NOW() - INTERVAL '30 days'
                    WHERE e_target.id IN ({id_list})
                    GROUP BY e_target.id
                    """
                )
            )
            for row in result.fetchall():
                series_completed_counts[str(row.episode_id)] = int(row.completed_count)

        for b in bookmarks:
            # Recency score: exponential decay with ~5-day half-life
            days_since = (now - b.updated_at).total_seconds() / 86400.0
            recency_score = math.exp(-days_since / 7.0)

            # Completion score: peak at 20-80% progress
            progress = b.progress_percent
            completion_score = max(0.0, min(1.0, 1.0 - abs(progress - 50.0) / 50.0))

            # Series momentum score
            if b.content_type == "episode":
                cc = series_completed_counts.get(str(b.content_id), 0)
                # Cap at 5 for normalisation
                series_momentum_score = min(cc, 5) / 5.0
            else:
                series_momentum_score = 0.5

            # Time affinity score (US4) — context-aware when device_type
            # and hour_of_day are provided
            use_time_affinity = device_type is not None and hour_of_day is not None
            if use_time_affinity:
                remaining_seconds = max(0, b.duration_seconds - b.position_seconds)
                remaining_minutes = remaining_seconds / 60.0

                if device_type == "mobile" and 6 <= hour_of_day <= 10:
                    # Morning mobile: boost short remaining content (< 30 min)
                    time_affinity_score = 1.0 - min(remaining_minutes, 60.0) / 60.0
                elif device_type == "tv" and 19 <= hour_of_day <= 23:
                    # Evening TV: boost long remaining content (> 60 min)
                    time_affinity_score = min(remaining_minutes, 120.0) / 120.0
                else:
                    time_affinity_score = 0.5

                # 4-weight model
                w_recency = 0.3
                w_completion = 0.2
                w_momentum = 0.25
                w_time = 0.25

                score = (
                    w_recency * recency_score
                    + w_completion * completion_score
                    + w_momentum * series_momentum_score
                    + w_time * time_affinity_score
                )
            else:
                # 3-weight model (no time affinity)
                w_recency = 0.4
                w_completion = 0.25
                w_momentum = 0.35

                score = (
                    w_recency * recency_score
                    + w_completion * completion_score
                    + w_momentum * series_momentum_score
                )

            scores[str(b.id)] = round(min(1.0, max(0.0, score)), 4)

        return scores
    except Exception:
        logger.exception("Failed to compute resumption scores")
        return {}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def get_home_rails(
    db: AsyncSession,
    profile_id: uuid.UUID,
    *,
    allowed_ratings: list[str] | None = None,
) -> list[dict]:
    """Assemble the full set of home-screen rails for a profile."""
    rails: list[dict] = []

    # 1. Continue Watching
    cw_items = await _continue_watching_rail(db, profile_id, allowed_ratings=allowed_ratings)
    if cw_items:
        rails.append({"name": "Continue Watching", "rail_type": "continue_watching", "items": cw_items})

    # 2. For You (only if there is viewing history)
    fy_items = await get_for_you_rail(db, profile_id, allowed_ratings=allowed_ratings)
    if fy_items:
        rails.append({"name": "For You", "rail_type": "for_you", "items": fy_items})

    # 3. New Releases
    nr_items = await _new_releases_rail(db, allowed_ratings=allowed_ratings)
    if nr_items:
        rails.append({"name": "New Releases", "rail_type": "new_releases", "items": nr_items})

    # 4. Trending
    tr_items = await _trending_rail(db, allowed_ratings=allowed_ratings)
    if tr_items:
        rails.append({"name": "Trending", "rail_type": "trending", "items": tr_items})

    # 5. Top genre rail
    genre_rail = await _top_genre_rail(db, profile_id, allowed_ratings=allowed_ratings)
    if genre_rail:
        rails.append(genre_rail)

    return rails


async def get_post_play(
    db: AsyncSession,
    title_id: uuid.UUID,
    limit: int = 8,
    *,
    allowed_ratings: list[str] | None = None,
) -> list[dict]:
    """Post-play suggestions -- reuses the similarity engine."""
    return await get_similar_titles(db, title_id, limit=limit, allowed_ratings=allowed_ratings)
