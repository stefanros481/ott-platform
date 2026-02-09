"""Seed embeddings for all titles using sentence-transformers.

This module depends on app.services.embedding_service which may be created by
another agent. It generates a text representation for each title and stores the
resulting vector in the content_embeddings table.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import Title, TitleGenre, Genre
from app.models.embedding import ContentEmbedding


async def seed_embeddings(session: AsyncSession) -> dict[str, int]:
    """Generate and store embeddings for all titles that do not yet have one.

    Uses sentence-transformers (all-MiniLM-L6-v2) via the embedding service.
    Idempotent: skips titles that already have embeddings.
    Returns a count of newly created embeddings.
    """
    # Late import — the embedding service may not exist yet during early dev.
    try:
        from app.services.embedding_service import generate_embedding
    except ImportError:
        print(
            "  [seed_embeddings] app.services.embedding_service not found. "
            "Falling back to inline sentence-transformers."
        )
        generate_embedding = None

    # If the dedicated service is unavailable, create a local fallback.
    if generate_embedding is None:
        try:
            from sentence_transformers import SentenceTransformer

            _model = SentenceTransformer("all-MiniLM-L6-v2")

            def generate_embedding(text: str) -> list[float]:  # type: ignore[misc]
                """Generate a 384-dim embedding using sentence-transformers."""
                return _model.encode(text, normalize_embeddings=True).tolist()

        except ImportError:
            print(
                "  [seed_embeddings] sentence-transformers not installed. "
                "Skipping embedding generation."
            )
            return {"embeddings": 0}

    # ------------------------------------------------------------------
    # Fetch all titles with their genres
    # ------------------------------------------------------------------
    result = await session.execute(
        select(Title)
    )
    titles = result.scalars().all()

    if not titles:
        print("  [seed_embeddings] No titles found. Run seed_catalog first.")
        return {"embeddings": 0}

    # Fetch existing embeddings to skip
    existing_result = await session.execute(
        select(ContentEmbedding.title_id)
    )
    existing_ids = set(existing_result.scalars().all())

    # Fetch genre names mapped by genre_id for building text representations
    genre_result = await session.execute(select(Genre))
    genre_map = {g.id: g.name for g in genre_result.scalars().all()}

    # Fetch title-genre associations
    tg_result = await session.execute(select(TitleGenre))
    title_genre_map: dict[str, list[str]] = {}
    for tg in tg_result.scalars().all():
        genre_name = genre_map.get(tg.genre_id, "")
        title_genre_map.setdefault(str(tg.title_id), []).append(genre_name)

    created = 0
    total = len(titles)

    for i, title in enumerate(titles):
        if title.id in existing_ids:
            continue

        # Build text representation for embedding
        genres_str = ", ".join(title_genre_map.get(str(title.id), []))
        moods_str = ", ".join(title.mood_tags) if title.mood_tags else ""
        themes_str = ", ".join(title.theme_tags) if title.theme_tags else ""

        text = (
            f"{title.title}. "
            f"{title.synopsis_short or ''} "
            f"Genres: {genres_str}. "
            f"Mood: {moods_str}. "
            f"Themes: {themes_str}."
        )

        embedding = generate_embedding(text)

        session.add(ContentEmbedding(
            title_id=title.id,
            embedding=embedding,
            model_version="all-MiniLM-L6-v2",
        ))
        created += 1

        # Progress feedback every 10 titles
        if created % 10 == 0:
            print(f"  [seed_embeddings] Generated {created}/{total} embeddings...")

    if created > 0:
        await session.flush()
        await session.commit()

    print(f"  [seed_embeddings] Created {created} embeddings (skipped {total - created} existing).")

    return {"embeddings": created}
