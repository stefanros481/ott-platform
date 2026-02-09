# AI-Native OTT Streaming Platform — PoC

Proof-of-concept for an AI-native OTT streaming platform with VOD/SVOD catalog, EPG grid, and content-based AI recommendations.

## Quick Start

```bash
cd docker
docker compose up --build
```

First build takes ~5 min (Python deps + Node deps + sentence-transformers model download). Subsequent starts use cached layers.

## URLs

| Service | URL |
|---------|-----|
| Client App | http://localhost:5173 |
| Admin Dashboard | http://localhost:5174 |
| Backend API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |

## Test Users

| Email | Password | Tier | Admin | Profiles |
|-------|----------|------|-------|----------|
| admin@ott.test | admin123 | Premium | Yes | Admin, Kids |
| basic@ott.test | test123 | Basic | No | Basic User |
| standard@ott.test | test123 | Standard | No | Standard User, Family |
| premium@ott.test | test123 | Premium | No | Premium User, Partner, Kids |
| demo@ott.test | demo123 | Premium | No | Demo User |

### Entitlement Tiers

- **Basic** — 60% of titles, 15 channels
- **Standard** — 85% of titles, 25 channels
- **Premium** — 100% of titles, all channels

## Seed Data

| Data | Count |
|------|-------|
| Titles (movies + series) | 70 |
| Genres | 12 |
| Channels | 25 |
| Schedule entries (7-day) | ~4,800 |
| Content embeddings | 70 |
| Users | 5 |
| Profiles | 10 |

Data is seeded automatically on first backend startup. To re-seed, delete the `postgres_data` volume and restart.

## Tech Stack

- **Backend:** Python / FastAPI, SQLAlchemy 2.0 (async), Alembic
- **Database:** PostgreSQL 16 + pgvector (HNSW index for similarity search)
- **Cache:** Redis 7
- **AI:** sentence-transformers (`all-MiniLM-L6-v2`, 384-dim embeddings)
- **Frontend Client:** React 18, TypeScript, Vite, Tailwind CSS, TanStack Query, Shaka Player
- **Frontend Admin:** React 18, TypeScript, Vite, Tailwind CSS, TanStack Query
- **Auth:** JWT (HS256)
- **Infra:** Docker Compose

## Architecture

```
frontend-client (5173)  frontend-admin (5174)
         \                     /
          \                   /
           +--> backend (8000) <--+
                |          |
           PostgreSQL    Redis
           + pgvector
```

Single FastAPI monolith with router-based module separation:

| Module | Endpoints |
|--------|-----------|
| Auth | `/auth/login`, `/register`, `/refresh`, `/profiles` |
| Catalog | `/catalog/titles`, `/search`, `/genres`, `/featured` |
| EPG | `/epg/channels`, `/schedule/{channel_id}`, `/favorites` |
| Viewing | `/viewing/continue-watching`, `/bookmarks`, `/ratings`, `/watchlist` |
| Recommendations | `/recommendations/home`, `/similar/{id}` |
| Admin | `/admin/titles`, `/channels`, `/schedule`, `/embeddings/generate` |

## AI Recommendations

Embeddings are generated from title metadata (title, synopsis, genres, cast, mood/theme tags) using `all-MiniLM-L6-v2`. Similarity search uses pgvector cosine distance with HNSW index.

**Surfaces:**
- **"More Like This"** — cosine similarity from a source title's embedding
- **"For You"** — centroid of user's watched/rated titles → similarity search
- **Home rails** — Continue Watching, For You, New Releases, Trending, genre rails

**Regenerate embeddings** (e.g. after changing seed data):
```bash
# Via admin dashboard: click "Generate Embeddings" button
# Via API (as admin user):
curl -X POST "http://localhost:8000/api/v1/admin/embeddings/generate?regenerate=true" \
  -H "Authorization: Bearer <admin-jwt>"
```

## Project Structure

```
ott-platform-docs/
├── docs/                    # Design docs, PRDs, user stories (23 files)
├── backend/                 # FastAPI app (Python/uv)
│   └── app/
│       ├── models/          # SQLAlchemy ORM models
│       ├── schemas/         # Pydantic request/response schemas
│       ├── routers/         # FastAPI route handlers
│       ├── services/        # Business logic
│       └── seed/            # Data seeding scripts
├── frontend-client/         # Viewer-facing React app
│   └── src/
│       ├── api/             # Typed API client
│       ├── pages/           # Route pages
│       ├── components/      # Reusable UI components
│       └── context/         # Auth context
├── frontend-admin/          # Admin dashboard React app
└── docker/                  # Docker Compose + init scripts
```
