FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Pre-download the embedding model during build
RUN uv run python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')" || true

# Copy application code
COPY . .

# Run migrations, seed data, then start uvicorn
CMD ["sh", "-c", "uv run alembic upgrade head && uv run python -m app.seed.run_seeds && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]
