"""Hybrid search service — keyword, semantic (pgvector), and RRF-merged search."""

import logging

from sqlalchemy import bindparam, exists, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.catalog import Genre, Title, TitleCast, TitleGenre
from app.services import embedding_service

logger = logging.getLogger(__name__)


def escape_like(value: str) -> str:
    """Escape special characters for safe use in ILIKE patterns."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


# ---------------------------------------------------------------------------
# T002 — Keyword search with field-level match detection
# ---------------------------------------------------------------------------


async def keyword_search(
    db: AsyncSession,
    query: str,
    allowed_ratings: list[str] | None = None,
    limit: int = 30,
) -> list[dict]:
    """Run ILIKE keyword search and track which fields matched."""
    pattern = f"%{escape_like(query)}%"

    cast_match = exists(
        select(TitleCast.id).where(
            TitleCast.title_id == Title.id,
            TitleCast.person_name.ilike(pattern),
        )
    )
    search_filter = or_(
        Title.title.ilike(pattern),
        Title.synopsis_short.ilike(pattern),
        Title.synopsis_long.ilike(pattern),
        cast_match,
    )

    stmt = (
        select(Title)
        .where(search_filter)
        .options(selectinload(Title.genres).selectinload(TitleGenre.genre))
        .order_by(Title.title)
        .limit(limit)
    )
    if allowed_ratings is not None:
        stmt = stmt.where(Title.age_rating.in_(allowed_ratings))

    result = await db.execute(stmt)
    titles = list(result.scalars().unique())

    hits: list[dict] = []
    query_lower = query.lower()
    for t in titles:
        match_fields: list[str] = []
        if t.title and query_lower in t.title.lower():
            match_fields.append("title")
        if t.synopsis_short and query_lower in t.synopsis_short.lower():
            match_fields.append("synopsis_short")
        if t.synopsis_long and query_lower in t.synopsis_long.lower():
            match_fields.append("synopsis_long")
        # Check cast
        cast_q = await db.execute(
            select(TitleCast.person_name).where(
                TitleCast.title_id == t.id,
                TitleCast.person_name.ilike(pattern),
            )
        )
        if cast_q.first() is not None:
            match_fields.append("cast")
        if not match_fields:
            match_fields.append("keyword")

        hits.append({
            "id": t.id,
            "title": t.title,
            "title_type": t.title_type,
            "synopsis_short": t.synopsis_short,
            "release_year": t.release_year,
            "duration_minutes": t.duration_minutes,
            "age_rating": t.age_rating,
            "poster_url": t.poster_url,
            "landscape_url": t.landscape_url,
            "is_featured": t.is_featured,
            "mood_tags": t.mood_tags,
            "genres": [tg.genre.name for tg in t.genres],
            "match_fields": match_fields,
        })
    return hits


# ---------------------------------------------------------------------------
# T003 — Semantic search via pgvector cosine similarity
# ---------------------------------------------------------------------------


async def semantic_search(
    db: AsyncSession,
    query_text: str,
    allowed_ratings: list[str] | None = None,
    limit: int = 30,
) -> list[dict]:
    """Embed the query and find similar titles via pgvector cosine distance."""
    query_vector = embedding_service.generate_embedding(query_text)
    vec_str = "[" + ",".join(str(float(v)) for v in query_vector) + "]"

    age_filter = ""
    bind_kw: dict = dict(query_vec=vec_str, lim=limit, min_sim=0.2)
    extra_params = []
    if allowed_ratings is not None:
        age_filter = "AND t.age_rating IN :allowed"
        bind_kw["allowed"] = list(allowed_ratings)
        extra_params.append(bindparam("allowed", expanding=True))

    stmt = text(
        f"""
        SELECT t.id, t.title, t.title_type, t.synopsis_short, t.release_year,
               t.duration_minutes, t.age_rating, t.poster_url, t.landscape_url,
               t.is_featured, t.mood_tags,
               1 - (ce.embedding <=> CAST(:query_vec AS vector)) AS similarity
        FROM content_embeddings ce
        JOIN titles t ON t.id = ce.title_id
        WHERE 1 - (ce.embedding <=> CAST(:query_vec AS vector)) >= :min_sim
              {age_filter}
        ORDER BY ce.embedding <=> CAST(:query_vec AS vector)
        LIMIT :lim
        """
    )
    if extra_params:
        stmt = stmt.bindparams(*extra_params)
    result = await db.execute(stmt.params(**bind_kw))

    hits: list[dict] = []
    for r in result.fetchall():
        # Fetch genres for this title
        genre_q = await db.execute(
            text(
                "SELECT g.name FROM genres g "
                "JOIN title_genres tg ON tg.genre_id = g.id "
                "WHERE tg.title_id = :tid"
            ).bindparams(tid=r.id)
        )
        genre_names = [row[0] for row in genre_q.fetchall()]

        hits.append({
            "id": r.id,
            "title": r.title,
            "title_type": r.title_type,
            "synopsis_short": r.synopsis_short,
            "release_year": r.release_year,
            "duration_minutes": r.duration_minutes,
            "age_rating": r.age_rating,
            "poster_url": r.poster_url,
            "landscape_url": r.landscape_url,
            "is_featured": r.is_featured,
            "mood_tags": list(r.mood_tags) if r.mood_tags else None,
            "genres": genre_names,
            "similarity_score": float(r.similarity),
        })
    return hits


# ---------------------------------------------------------------------------
# T004 — Reciprocal Rank Fusion
# ---------------------------------------------------------------------------


def _reciprocal_rank_fusion(
    keyword_hits: list[dict],
    semantic_hits: list[dict],
    k: int = 60,
) -> list[str]:
    """Merge two ranked lists using RRF. Returns title IDs sorted by RRF score."""
    scores: dict[str, float] = {}
    for rank, hit in enumerate(keyword_hits, start=1):
        tid = str(hit["id"])
        scores[tid] = scores.get(tid, 0.0) + 1.0 / (k + rank)
    for rank, hit in enumerate(semantic_hits, start=1):
        tid = str(hit["id"])
        scores[tid] = scores.get(tid, 0.0) + 1.0 / (k + rank)
    return sorted(scores, key=lambda tid: scores[tid], reverse=True)


# ---------------------------------------------------------------------------
# T005 — Match reason builder
# ---------------------------------------------------------------------------


def _build_match_reason(
    keyword_hit: dict | None,
    semantic_hit: dict | None,
) -> tuple[str, str]:
    """Return (match_reason, match_type) for a merged result."""
    reasons: list[str] = []

    if keyword_hit:
        field_labels = {
            "title": "Title match",
            "synopsis_short": "Description match",
            "synopsis_long": "Description match",
            "cast": "Cast match",
        }
        seen_labels: set[str] = set()
        for field in keyword_hit.get("match_fields", []):
            label = field_labels.get(field, "Keyword match")
            if label not in seen_labels:
                reasons.append(label)
                seen_labels.add(label)

    if semantic_hit:
        score = semantic_hit.get("similarity_score", 0)
        if score > 0.6:
            reasons.append("Strongly related themes")
        elif score > 0.4:
            reasons.append("Similar themes")
        elif score > 0.2:
            reasons.append("Related content")

    if keyword_hit and semantic_hit:
        match_type = "both"
    elif keyword_hit:
        match_type = "keyword"
    else:
        match_type = "semantic"

    return " · ".join(reasons) if reasons else "Match", match_type


# ---------------------------------------------------------------------------
# T006 — Hybrid search orchestrator
# ---------------------------------------------------------------------------


async def hybrid_search(
    db: AsyncSession,
    query_text: str,
    mode: str = "hybrid",
    allowed_ratings: list[str] | None = None,
    limit: int = 30,
) -> list[dict]:
    """Run keyword, semantic, or hybrid search depending on mode.

    For hybrid mode, merges results via Reciprocal Rank Fusion and generates
    match reasons per result. Auto-downgrades to keyword for short queries.
    Wraps semantic search in try/except for graceful fallback.
    """
    # Auto-downgrade short queries to keyword-only
    if len(query_text.strip()) < 3:
        mode = "keyword"

    keyword_hits: list[dict] = []
    semantic_hits: list[dict] = []

    if mode in ("keyword", "hybrid"):
        keyword_hits = await keyword_search(db, query_text, allowed_ratings, limit)

    if mode in ("semantic", "hybrid"):
        try:
            semantic_hits = await semantic_search(db, query_text, allowed_ratings, limit)
        except Exception:
            logger.warning("Semantic search failed, falling back to keyword-only", exc_info=True)
            await db.rollback()
            if not keyword_hits:
                keyword_hits = await keyword_search(db, query_text, allowed_ratings, limit)

    # Build lookup dicts keyed by title ID string
    kw_by_id = {str(h["id"]): h for h in keyword_hits}
    sem_by_id = {str(h["id"]): h for h in semantic_hits}

    # Determine ordering
    if keyword_hits and semantic_hits:
        ordered_ids = _reciprocal_rank_fusion(keyword_hits, semantic_hits)
    elif keyword_hits:
        ordered_ids = [str(h["id"]) for h in keyword_hits]
    else:
        ordered_ids = [str(h["id"]) for h in semantic_hits]

    # Build final results
    results: list[dict] = []
    for tid in ordered_ids[:limit]:
        kw_hit = kw_by_id.get(tid)
        sem_hit = sem_by_id.get(tid)
        base = kw_hit or sem_hit
        if base is None:
            continue

        match_reason, match_type = _build_match_reason(kw_hit, sem_hit)

        results.append({
            "id": base["id"],
            "title": base["title"],
            "title_type": base["title_type"],
            "synopsis_short": base.get("synopsis_short"),
            "release_year": base.get("release_year"),
            "duration_minutes": base.get("duration_minutes"),
            "age_rating": base.get("age_rating"),
            "poster_url": base.get("poster_url"),
            "landscape_url": base.get("landscape_url"),
            "is_featured": base.get("is_featured", False),
            "mood_tags": base.get("mood_tags"),
            "genres": base.get("genres", []),
            "match_reason": match_reason,
            "match_type": match_type,
            "similarity_score": sem_hit["similarity_score"] if sem_hit else None,
        })

    return results
