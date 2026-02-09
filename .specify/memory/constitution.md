# AI-Native OTT Streaming Platform — PoC Constitution

## Core Principles

### I. PoC-First Quality
This is a proof-of-concept validating technical feasibility. Optimize for functional correctness and demonstrability over production hardening. Skip: rate limiting, advanced caching, horizontal scaling, multi-region.

### II. Monolithic Simplicity
Collapse the production microservices architecture into a single FastAPI application with router-based module separation. Each router maps to a future production microservice boundary, making the path to decomposition clear.

### III. AI-Native by Default
Every feature should include its AI-enhanced variant, even in the PoC. Content-based recommendations (pgvector), personalized EPG ordering, and AI-enriched metadata are core — not bolt-on features.

### IV. Docker Compose as Truth
The entire stack runs with `docker compose up`. No external services, no cloud dependencies. PostgreSQL, Redis, backend, and frontends all containerized.

### V. Seed Data as Demo
Rich, realistic seed data (50-100 titles, 20-30 channels, 7-day EPG schedule) is essential for demonstrating the platform. Invest in quality seed data with diverse genres, moods, and metadata.

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Backend | Python + FastAPI | 3.12 / 0.115+ |
| Python deps | uv | latest |
| Database | PostgreSQL + pgvector | 16 / 0.7+ |
| Cache | Redis | 7 |
| Frontend client | React + TypeScript + Tailwind CSS | 18 / 5+ / 3+ |
| Frontend admin | React + TypeScript + Tailwind CSS | 18 / 5+ / 3+ |
| Build tool | Vite | 6+ |
| Video player | Shaka Player | 4+ |
| AI embeddings | sentence-transformers (all-MiniLM-L6-v2) | 3+ |
| Vector search | pgvector (HNSW index) | 0.7+ |
| Auth | JWT (HS256) | - |
| ORM | SQLAlchemy (async) | 2.0+ |
| Migrations | Alembic | 1.14+ |
| Deployment | Docker Compose | - |

## Constraints

- No `version` key at the top of docker-compose files
- Use `uv` for all Python dependency management
- Mock HLS content via public test streams (no encoding pipeline)
- Single FastAPI process (not microservices)
- No cloud provider dependencies (everything runs locally)
- Frontend uses Vite dev server in development (not production builds)

## Development Workflow

1. Backend changes: Edit Python → uvicorn auto-reloads
2. Frontend changes: Edit TSX → Vite HMR reloads
3. Database changes: Create Alembic migration → run `alembic upgrade head`
4. Seed data: Run seed scripts after migration

## Reference Documentation

All product requirements and architecture decisions are documented in `docs/`:
- `docs/01-project-vision-and-design.md` — Platform vision and strategy
- `docs/02-platform-architecture.md` — Full production architecture (PoC simplifies from this)
- `docs/prd/PRD-004-vod-svod.md` — VOD/SVOD requirements
- `docs/prd/PRD-005-epg.md` — EPG requirements
- `docs/prd/PRD-007-ai-user-experience.md` — AI recommendation requirements
- `docs/cross-cutting/authentication-entitlements.md` — Auth and entitlement model

**Version**: 1.0.0 | **Ratified**: 2026-02-09 | **Last Amended**: 2026-02-09
