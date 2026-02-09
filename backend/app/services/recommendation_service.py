"""Service layer for content recommendations backed by pgvector similarity search."""

import logging
import uuid

import numpy as np
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import Genre, Title, TitleGenre
from app.models.embedding import ContentEmbedding
from app.models.viewing import Bookmark, Rating

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
    result = await db.execute(
        text(
            """
            SELECT t.id, t.title, t.title_type, t.poster_url, t.landscape_url,
                   t.synopsis_short, t.release_year, t.age_rating,
                   1 - (ce.embedding <=> CAST(:query_vec AS vector)) AS similarity
            FROM content_embeddings ce
            JOIN titles t ON t.id = ce.title_id
            WHERE ce.title_id != :source_id
            ORDER BY ce.embedding <=> CAST(:query_vec AS vector)
            LIMIT :lim
            """
        ).bindparams(
            query_vec=vec_str,
            source_id=title_id,
            lim=limit,
        )
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
            "similarity_score": float(r.similarity) if r.similarity is not None else None,
        }
        for r in result.fetchall()
    ]


async def get_for_you_rail(
    db: AsyncSession,
    profile_id: uuid.UUID,
    limit: int = 20,
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

    result = await db.execute(
        text(
            f"""
            SELECT t.id, t.title, t.title_type, t.poster_url, t.landscape_url,
                   t.synopsis_short, t.release_year, t.age_rating,
                   1 - (ce.embedding <=> CAST(:query_vec AS vector)) AS similarity
            FROM content_embeddings ce
            JOIN titles t ON t.id = ce.title_id
            WHERE ce.title_id NOT IN ({exclusion_list})
            ORDER BY ce.embedding <=> CAST(:query_vec AS vector)
            LIMIT :lim
            """
        ).bindparams(
            query_vec=vec_str,
            lim=limit,
        )
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
            "similarity_score": float(r.similarity) if r.similarity is not None else None,
        }
        for r in result.fetchall()
    ]


async def _continue_watching_rail(
    db: AsyncSession,
    profile_id: uuid.UUID,
    limit: int = 20,
) -> list[dict]:
    """Fetch bookmarks that are not completed, most recent first."""
    result = await db.execute(
        text(
            """
            SELECT b.content_id AS id, t.title, t.title_type, t.poster_url,
                   t.landscape_url, t.synopsis_short, t.release_year, t.age_rating,
                   b.position_seconds, b.duration_seconds
            FROM bookmarks b
            JOIN titles t ON t.id = b.content_id
            WHERE b.profile_id = :pid AND b.completed = false
            ORDER BY b.updated_at DESC
            LIMIT :lim
            """
        ).bindparams(pid=profile_id, lim=limit)
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


async def _new_releases_rail(db: AsyncSession, limit: int = 20) -> list[dict]:
    result = await db.execute(
        select(Title).order_by(Title.created_at.desc()).limit(limit)
    )
    return [_title_to_rail_item(t) for t in result.scalars().all()]


async def _trending_rail(db: AsyncSession, limit: int = 20) -> list[dict]:
    """Titles with the most bookmarks (proxy for popularity)."""
    result = await db.execute(
        text(
            """
            SELECT t.id, t.title, t.title_type, t.poster_url, t.landscape_url,
                   t.synopsis_short, t.release_year, t.age_rating,
                   COUNT(b.id) AS bm_count
            FROM titles t
            LEFT JOIN bookmarks b ON b.content_id = t.id
            GROUP BY t.id
            ORDER BY bm_count DESC
            LIMIT :lim
            """
        ).bindparams(lim=limit)
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
    titles_q = await db.execute(
        text(
            """
            SELECT t.id, t.title, t.title_type, t.poster_url, t.landscape_url,
                   t.synopsis_short, t.release_year, t.age_rating
            FROM titles t
            JOIN title_genres tg ON tg.title_id = t.id
            WHERE tg.genre_id = :gid
            ORDER BY t.created_at DESC
            LIMIT :lim
            """
        ).bindparams(gid=genre_id, lim=limit)
    )
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
# Public API
# ---------------------------------------------------------------------------

async def get_home_rails(
    db: AsyncSession,
    profile_id: uuid.UUID,
) -> list[dict]:
    """Assemble the full set of home-screen rails for a profile."""
    rails: list[dict] = []

    # 1. Continue Watching
    cw_items = await _continue_watching_rail(db, profile_id)
    if cw_items:
        rails.append({"name": "Continue Watching", "rail_type": "continue_watching", "items": cw_items})

    # 2. For You (only if there is viewing history)
    fy_items = await get_for_you_rail(db, profile_id)
    if fy_items:
        rails.append({"name": "For You", "rail_type": "for_you", "items": fy_items})

    # 3. New Releases
    nr_items = await _new_releases_rail(db)
    if nr_items:
        rails.append({"name": "New Releases", "rail_type": "new_releases", "items": nr_items})

    # 4. Trending
    tr_items = await _trending_rail(db)
    if tr_items:
        rails.append({"name": "Trending", "rail_type": "trending", "items": tr_items})

    # 5. Top genre rail
    genre_rail = await _top_genre_rail(db, profile_id)
    if genre_rail:
        rails.append(genre_rail)

    return rails


async def get_post_play(
    db: AsyncSession,
    title_id: uuid.UUID,
    limit: int = 8,
) -> list[dict]:
    """Post-play suggestions -- reuses the similarity engine."""
    return await get_similar_titles(db, title_id, limit=limit)
