# PoC Implementation Plan: AI-Native OTT Streaming Platform

## Context

We have 23 comprehensive documentation files (~1.1 MB) covering vision, architecture, 8 PRDs, 234 user stories, 4 cross-cutting docs, and a glossary for a full AI-native OTT streaming platform. The goal now is to build a **proof-of-concept** that validates the tech stack end-to-end, scoped to **VOD/SVOD + EPG + basic AI recommendations**, running entirely in Docker Compose.

## Confirmed Decisions

| Decision | Choice |
|----------|--------|
| PoC Scope | VOD/SVOD catalog + EPG grid + content-based AI recommendations |
| Backend | Python/FastAPI (monolithic, not microservices) |
| Python deps | uv |
| Frontend client | React + Tailwind CSS (viewer-facing) |
| Frontend admin | React + Tailwind CSS (content management dashboard) |
| Database | PostgreSQL 16 + pgvector extension |
| Cache | Redis 7 |
| Auth | JWT (HS256) |
| Video content | Mock HLS streams (public test streams) |
| AI approach | Content-based filtering via sentence-transformers embeddings + pgvector cosine similarity |
| Deployment | Docker Compose (no version key) |
| Repo structure | Monorepo — code alongside existing /docs |
| Spec Kit | Initialize on existing repo, reference existing PRDs |

---

## 1. Spec Kit Integration

### Init
```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
specify init --here --ai claude --force
```

### Constitution
Write a PoC-scoped constitution referencing:
- Tech stack (FastAPI, React/Tailwind, PostgreSQL+pgvector, Redis, Docker Compose, uv)
- Constraints (single FastAPI process, mock HLS content, PoC quality)

### Spec
Create a single spec (`specs/poc-vod-epg-recommendations.md`) that distills relevant requirements from existing PRDs:
- **VOD** — from [PRD-004-vod-svod.md](docs/prd/PRD-004-vod-svod.md) (catalog, browse, search, playback, entitlements)
- **EPG** — from [PRD-005-epg.md](docs/prd/PRD-005-epg.md) (grid, schedule, channel personalization)
- **AI Recs** — from [PRD-007-ai-user-experience.md](docs/prd/PRD-007-ai-user-experience.md) (content-based filtering, "For You", "More Like This")
- **Auth** — from [authentication-entitlements.md](docs/cross-cutting/authentication-entitlements.md) (JWT, entitlement checks)

---

## 2. Monorepo Structure

```
ott-platform-docs/
├── CLAUDE.md                         # Existing (keep as-is)
├── constitution.md                   # NEW — Spec Kit
├── specs/                            # NEW — Spec Kit spec
│   └── poc-vod-epg-recommendations.md
├── docs/                             # Existing — all 23 doc files (untouched)
├── backend/                          # NEW — FastAPI app
│   ├── pyproject.toml                # uv project
│   ├── uv.lock
│   ├── alembic.ini
│   ├── alembic/versions/
│   ├── Dockerfile
│   └── app/
│       ├── main.py                   # FastAPI app entry, CORS, router mounts
│       ├── config.py                 # Pydantic Settings (env vars)
│       ├── database.py               # SQLAlchemy async engine + session
│       ├── dependencies.py           # get_db, get_current_user
│       ├── models/                   # SQLAlchemy ORM
│       │   ├── user.py               # User, Profile, RefreshToken
│       │   ├── catalog.py            # Title, Season, Episode, Genre, TitleCast
│       │   ├── entitlement.py        # Package, UserEntitlement, PackageContent
│       │   ├── epg.py                # Channel, ScheduleEntry, ChannelFavorite
│       │   ├── viewing.py            # Bookmark, Rating, WatchlistItem
│       │   └── embedding.py          # ContentEmbedding (vector(384))
│       ├── schemas/                  # Pydantic request/response
│       │   ├── auth.py
│       │   ├── catalog.py
│       │   ├── epg.py
│       │   ├── recommendation.py
│       │   └── viewing.py
│       ├── routers/                  # FastAPI APIRouters
│       │   ├── auth.py               # /auth/login, /register, /refresh, /profiles
│       │   ├── catalog.py            # /catalog/titles, /search, /genres, /featured
│       │   ├── epg.py                # /epg/channels, /schedule, /now, /favorites
│       │   ├── recommendations.py    # /recommendations/home, /similar/{id}
│       │   ├── viewing.py            # /viewing/bookmarks, /ratings, /watchlist
│       │   └── admin.py              # /admin/titles, /channels, /schedule CRUD
│       ├── services/                 # Business logic
│       │   ├── auth_service.py       # JWT, password hashing
│       │   ├── catalog_service.py    # Catalog queries, search
│       │   ├── epg_service.py        # Schedule queries, AI channel ordering
│       │   ├── recommendation_service.py  # pgvector similarity, rail composition
│       │   ├── entitlement_service.py     # Package-based access checks
│       │   └── embedding_service.py  # sentence-transformers embedding gen
│       └── seed/                     # Data seeding scripts
│           ├── seed_catalog.py       # 50-100 mock titles
│           ├── seed_epg.py           # 20-30 channels, 7-day schedule
│           ├── seed_users.py         # Test users (basic/standard/premium)
│           └── seed_embeddings.py    # Generate embeddings for all titles
├── frontend-client/                  # NEW — Viewer web app
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── Dockerfile
│   └── src/
│       ├── api/                      # Fetch wrapper + typed API calls
│       ├── context/AuthContext.tsx
│       ├── hooks/
│       ├── pages/                    # Home, Browse, TitleDetail, Player, EPG, Search, Login
│       ├── components/               # ContentRail, TitleCard, HeroBanner, EpgGrid, VideoPlayer
│       └── styles/globals.css
├── frontend-admin/                   # NEW — Admin dashboard
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── Dockerfile
│   └── src/
│       ├── api/
│       ├── pages/                    # Dashboard, CatalogList/Edit, Channels, Schedule, Users
│       └── components/               # DataTable, FormField, Sidebar
└── docker/                           # NEW — Docker Compose
    ├── docker-compose.yml            # postgres, redis, backend, frontend-client, frontend-admin
    ├── postgres/init.sql             # CREATE EXTENSION vector
    └── sample-content/manifest.json  # Index of mock HLS stream URLs
```

---

## 3. Backend Architecture

### Microservices → Monolith Mapping

The production architecture defines 20+ Go/Python microservices. For the PoC, these collapse into a single FastAPI app with router-based separation:

| Production Service (Go/Python) | PoC Module |
|---|---|
| Auth Service, User Service, Profile Service | `routers/auth.py` + `services/auth_service.py` |
| Catalog Service, Search Service | `routers/catalog.py` + `services/catalog_service.py` |
| EPG Service | `routers/epg.py` + `services/epg_service.py` |
| Recommendation Service, Metadata Service | `routers/recommendations.py` + `services/recommendation_service.py` |
| Entitlement Service | `services/entitlement_service.py` (internal, no router) |
| Bookmark Service | `routers/viewing.py` |
| AI Model Serving (KServe) | `services/embedding_service.py` (direct inference) |
| Content Ingest | Replaced by seed scripts + admin CRUD |
| Playback Session, CDN Routing, CAT Token | **Not implemented** (PoC uses direct HLS URLs) |

### Database Schema (PostgreSQL + pgvector)

Single database, all tables in one schema. Key tables:

- **Auth**: `users`, `profiles`, `refresh_tokens`
- **Entitlements**: `content_packages`, `user_entitlements`, `package_contents`
- **Catalog**: `genres`, `titles` (with `mood_tags TEXT[]`, `theme_tags TEXT[]`), `title_genres`, `title_cast`, `seasons`, `episodes`
- **EPG**: `channels`, `schedule_entries` (indexed on channel+time), `channel_favorites`
- **Viewing**: `bookmarks`, `ratings` (thumbs up/down), `watchlist`
- **AI**: `content_embeddings` (title_id + `vector(384)` with HNSW index)

### AI Recommendations Implementation

**Embedding model**: `sentence-transformers/all-MiniLM-L6-v2` (384-dim, ~80MB)
- For each title: concatenate `title + synopsis + genres + mood_tags + theme_tags`
- Store in `content_embeddings` table with HNSW index for fast similarity

**Recommendation surfaces**:
1. **"More Like This"** — pgvector cosine distance from source title's embedding → top 12
2. **"For You" rail** — average embedding of user's watched+rated titles → similarity search → top 20
3. **Home screen rails** — composite: Continue Watching (bookmarks), For You (embeddings), New Releases (recent), Trending (most bookmarked), Genre rails
4. **Post-play** — blend of similar + user preference

**EPG AI channel ordering** (simplified from ML model):
- Score each channel based on: genre affinity (40%), time-of-day viewing pattern (30%), recency (20%), HD bonus (10%)
- Pinned favorites override AI ordering

**Fallback**: When AI unavailable, fall back to popularity-based ordering

### Key Python Dependencies

`fastapi`, `uvicorn[standard]`, `sqlalchemy>=2.0`, `alembic`, `asyncpg`, `pgvector`, `pydantic`, `pydantic-settings`, `python-jose[cryptography]`, `passlib[bcrypt]`, `redis`, `sentence-transformers`, `httpx`

---

## 4. Frontend Architecture

### Client App (port 5173)

**Stack**: React 18 + TypeScript + Vite + Tailwind CSS + React Router v6 + TanStack Query + Shaka Player

**Pages**:
| Route | Component | Description |
|---|---|---|
| `/` | HomePage | Personalized rails (For You, Continue Watching, New, Trending) |
| `/browse/:genre?` | BrowsePage | Genre/category browse with filtering |
| `/title/:id` | TitleDetailPage | Metadata, cast, More Like This, play/watchlist/rate |
| `/play/:type/:id` | PlayerPage | Shaka Player with HLS, bookmark reporting, auto-play next |
| `/epg` | EpgPage | Channel × time grid, AI-ordered channels, "Recommended" badges |
| `/search` | SearchPage | Text search with results |
| `/watchlist` | WatchlistPage | My List |
| `/login` | LoginPage | Email + password |
| `/profiles` | ProfilePage | Profile selection |

**Key components**: `ContentRail` (horizontal scroll), `TitleCard` (poster + metadata), `HeroBanner` (featured), `EpgGrid` (virtualized via react-window), `VideoPlayer` (Shaka Player wrapper)

### Admin Dashboard (port 5174)

**Stack**: Same as client app (minus Shaka Player)

**Pages**: Dashboard (stats), Catalog list/edit (CRUD), Channels (CRUD), Schedule (CRUD), Users (view), "Generate Embeddings" button

---

## 5. Docker Compose

```yaml
services:
  postgres:       # pgvector/pgvector:pg16, port 5432
  redis:          # redis:7-alpine, port 6379
  backend:        # Python 3.12-slim + uv, port 8000, depends on postgres+redis
  frontend-client: # Node 20-slim + vite dev, port 5173
  frontend-admin:  # Node 20-slim + vite dev, port 5174
```

Backend Dockerfile uses `uv sync --frozen` for deps, runs Alembic migrations on startup, then uvicorn with `--reload` for dev.

Mock HLS content: public test streams (Tears of Steel, Big Buck Bunny, etc.) — URLs stored directly in `titles.hls_manifest_url`. No local content serving needed.

---

## 6. Implementation Phases

### Phase 0: Project Scaffolding
- Run `specify init --here --ai claude --force`
- Write constitution + PoC spec
- Create directory structure
- Init `uv` project (`backend/`), Vite projects (`frontend-client/`, `frontend-admin/`)
- Create `docker-compose.yml` with PostgreSQL (pgvector) + Redis
- Init Alembic
- **Verify**: `docker compose up postgres redis` starts cleanly

### Phase 1: Backend — Auth + Catalog
- SQLAlchemy models: users, profiles, genres, titles, seasons, episodes, title_cast
- Auth service: register, login, JWT, refresh
- Catalog service: browse, detail, search (ILIKE)
- Seed data: 50-100 titles, test users
- **Verify**: Register → login → browse catalog → search → view detail via Swagger UI

### Phase 2: Backend — EPG + Viewing + Entitlements
- Models: channels, schedule_entries, bookmarks, ratings, watchlist, packages
- EPG service: channel list, schedule query, favorites
- Entitlement service: package-based access filtering
- Viewing service: bookmarks, ratings, watchlist CRUD
- Seed data: 20-30 channels, 7-day schedule, entitlement packages
- **Verify**: Browse EPG → view schedule → save bookmark → rate title → manage watchlist

### Phase 3: Backend — AI (Embeddings + Recommendations)
- ContentEmbedding model with vector(384) + HNSW index
- Embedding service: load sentence-transformers, generate + store embeddings
- Recommendation service: similar titles, "For You" rail, home rails composition
- EPG channel personalization (scoring function)
- Admin endpoint: trigger embedding generation
- **Verify**: "More Like This" returns semantically similar titles. Home "For You" rail reflects viewing history

### Phase 4: Frontend Client
- Project setup: Vite + React + Tailwind + React Router + TanStack Query
- API client with JWT interceptor
- Auth flow: Login → AuthContext → ProtectedRoute
- Home page with personalized rails
- Title detail with More Like This
- Video player (Shaka Player) with bookmark reporting
- EPG grid (virtualized) with AI-ordered channels
- Browse, search, watchlist pages
- **Verify**: Full user flow: login → browse → play → see recommendations → EPG

### Phase 5: Frontend Admin
- Dashboard, catalog CRUD, channel CRUD, schedule management
- "Generate Embeddings" button
- **Verify**: Create title in admin → generate embeddings → title appears in client recommendations

### Phase 6: Integration + Polish
- End-to-end test of all user journeys
- Entitlement enforcement verification
- Error/loading/empty states
- README with setup instructions and demo walkthrough

---

## 7. Verification Plan

After all phases complete, verify with `docker compose up`:

1. **Auth**: Register user → login → get JWT → access protected endpoints
2. **Catalog**: Browse titles → filter by genre → search → view detail with cast/seasons
3. **EPG**: View channel grid → navigate time → filter channels → see personalized order
4. **Playback**: Click play → Shaka Player loads HLS stream → bookmark saves on pause
5. **Recommendations**: "More Like This" shows semantically similar titles (not just same genre)
6. **Personalization**: After watching several titles, "For You" rail reflects preferences
7. **Entitlements**: Basic user cannot access premium-only content
8. **Admin**: Create new title → generate embeddings → verify it appears in client recommendations
9. **Continue Watching**: Start watching → close → reopen → resume from saved position

---

## Key Risk Areas

1. **sentence-transformers model download** (~80MB) — first Docker build is slow. Pre-download in Dockerfile build step or volume-mount HuggingFace cache
2. **pgvector on small data** — 50-100 titles is fine for demo, but recommendation quality depends on rich metadata in seed data
3. **Shaka Player HLS** — test with public Mux streams early; some streams may have CORS issues
4. **EPG grid rendering** — start with 20-30 channels; use react-window for virtualization
5. **Docker build time** — first build ~5-10 min (Python deps + Node deps + model download). Subsequent builds use cache

---

## Critical Files (existing docs to reference during implementation)

- [02-platform-architecture.md](docs/02-platform-architecture.md) — service catalog, data models, tech stack
- [PRD-004-vod-svod.md](docs/prd/PRD-004-vod-svod.md) — VOD functional requirements (VOD-FR-*)
- [PRD-005-epg.md](docs/prd/PRD-005-epg.md) — EPG requirements (EPG-FR-*, EPG-AI-*)
- [PRD-007-ai-user-experience.md](docs/prd/PRD-007-ai-user-experience.md) — recommendation architecture
- [authentication-entitlements.md](docs/cross-cutting/authentication-entitlements.md) — auth/entitlement model
