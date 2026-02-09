"""Service for generating and managing content embeddings via sentence-transformers."""

import logging

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.catalog import Title, TitleGenre
from app.models.embedding import ContentEmbedding

logger = logging.getLogger(__name__)

# Module-level model cache -- avoids reloading the heavy model on every call.
_model = None


def get_model():
    """Lazily load and cache the SentenceTransformer model."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        logger.info("Loading embedding model: %s", settings.embedding_model)
        _model = SentenceTransformer(settings.embedding_model)
    return _model


def generate_embedding(text_input: str) -> list[float]:
    """Generate a 384-dim embedding vector for the given text."""
    model = get_model()
    vector = model.encode(text_input, normalize_embeddings=True)
    return vector.tolist()


def _build_embedding_text(title: Title, genre_names: list[str], cast_names: list[str] | None = None) -> str:
    """Build a single text blob from a Title's metadata for embedding."""
    parts: list[str] = [title.title]
    if title.synopsis_short:
        parts.append(title.synopsis_short)
    if title.synopsis_long:
        parts.append(title.synopsis_long)
    if genre_names:
        parts.append("Genres: " + ", ".join(genre_names))
    if cast_names:
        parts.append("Cast: " + ", ".join(cast_names))
    if title.mood_tags:
        parts.append("Mood: " + ", ".join(title.mood_tags))
    if title.theme_tags:
        parts.append("Themes: " + ", ".join(title.theme_tags))
    if title.ai_description:
        parts.append(title.ai_description)
    return " ".join(parts)


async def generate_all_embeddings(db: AsyncSession, *, regenerate: bool = False) -> int:
    """Generate embeddings for every Title that does not yet have one.

    If *regenerate* is True, delete all existing embeddings first so every
    title gets a fresh embedding (useful after changing the text composition).

    Returns the count of newly created embeddings.
    """
    if regenerate:
        await db.execute(delete(ContentEmbedding))
        await db.flush()

    # Find titles without embeddings.
    existing_ids_q = select(ContentEmbedding.title_id)
    result = await db.execute(
        select(Title).where(Title.id.notin_(existing_ids_q))
    )
    titles_without_embeddings = result.scalars().all()

    if not titles_without_embeddings:
        return 0

    created = 0
    for title in titles_without_embeddings:
        # Fetch genre names for this title.
        genre_q = await db.execute(
            text(
                "SELECT g.name FROM genres g "
                "JOIN title_genres tg ON tg.genre_id = g.id "
                "WHERE tg.title_id = :tid"
            ).bindparams(tid=title.id)
        )
        genre_names = [row[0] for row in genre_q.fetchall()]

        # Fetch cast names for this title.
        cast_q = await db.execute(
            text(
                "SELECT person_name FROM title_cast "
                "WHERE title_id = :tid ORDER BY sort_order"
            ).bindparams(tid=title.id)
        )
        cast_names = [row[0] for row in cast_q.fetchall()]

        embedding_text = _build_embedding_text(title, genre_names, cast_names)
        vector = generate_embedding(embedding_text)

        embedding_row = ContentEmbedding(
            title_id=title.id,
            embedding=vector,
            model_version=settings.embedding_model,
        )
        db.add(embedding_row)
        created += 1

    await db.commit()
    logger.info("Generated %d new embeddings", created)
    return created
