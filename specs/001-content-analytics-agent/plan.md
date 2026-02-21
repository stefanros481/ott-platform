# Implementation Plan: Natural Language Content Analytics Agent

**Branch**: `001-content-analytics-agent` | **Date**: 2026-02-21 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-content-analytics-agent/spec.md`

## Summary

Build a natural language query agent that lets admin users ask plain-English questions about OTT content performance and receive structured answers with ranked data and plain-English summaries. The feature includes: (1) a lightweight analytics event capture layer in the backend and client, (2) a query engine that maps natural language to SQL via embedding similarity using the existing sentence-transformers + pgvector stack, (3) async job processing for complex queries, and (4) synthetic seed data so the agent is queryable from first startup.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5+ / React 18 (frontend-client)
**Primary Dependencies**: FastAPI 0.115+, SQLAlchemy 2.0+ async, sentence-transformers (all-MiniLM-L6-v2), pgvector 0.7+, Alembic 1.14+
**Storage**: PostgreSQL 16 + pgvector — two new tables (`analytics_events`, `query_jobs`) via Alembic migration 006; `query_templates` seeded as application data
**Testing**: pytest (backend unit + integration), vitest (frontend)
**Target Platform**: Linux (Docker Compose), local development
**Project Type**: Web application — backend-only feature (no new UI; queries via API / admin tooling per spec assumption)
**Performance Goals**: Simple queries synchronous <2s; complex queries return job ID <500ms, result available via polling <30s
**Constraints**: No cloud dependencies, no external queue (Docker Compose only), PoC-first quality, `uv` for Python deps
**Scale/Scope**: PoC — single admin user, ~500–1000 synthetic analytics events seeded

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. PoC-First Quality | ✓ PASS | No rate limiting, no Redis caching layer, no horizontal scaling. FastAPI BackgroundTasks for async (no Celery/RQ). |
| II. Monolithic Simplicity | ✓ PASS | Two new routers added to existing FastAPI monolith (`analytics.py`, `content_analytics.py`). No new services or containers. |
| III. AI-Native by Default | ✓ PASS | NLP query engine uses existing `all-MiniLM-L6-v2` + pgvector HNSW — AI is the query resolution mechanism, not a bolt-on. |
| IV. Docker Compose as Truth | ✓ PASS | No new Docker services. All new functionality runs inside existing `backend` container. |
| V. Seed Data as Demo | ✓ PASS | `seed_analytics.py` generates realistic synthetic events across titles, service types, and regions. Agent is queryable from first `docker compose up`. |

**Post-Design Re-check**: No violations. Complexity table not required.

## Project Structure

### Documentation (this feature)

```text
specs/001-content-analytics-agent/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── analytics-events.yaml    # POST /api/v1/analytics/events
│   └── content-analytics.yaml  # POST /api/v1/content-analytics/query
│                                # GET  /api/v1/content-analytics/jobs/{job_id}
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── models/
│   │   └── analytics.py              # AnalyticsEvent, QueryJob SQLAlchemy models
│   ├── routers/
│   │   ├── analytics.py              # POST /api/v1/analytics/events
│   │   └── content_analytics.py     # POST /api/v1/content-analytics/query
│   │                                 # GET  /api/v1/content-analytics/jobs/{job_id}
│   └── services/
│       ├── analytics_service.py      # Event ingestion + query aggregation logic
│       └── query_engine.py           # NLP → template match → SQL → QueryResult
├── alembic/versions/
│   └── 006_analytics_events_and_query_jobs.py
└── seed/
    └── seed_analytics.py             # Synthetic analytics event generator

frontend-client/
└── src/
    ├── api/
    │   └── analytics.ts              # fire-and-forget event emitter (apiFetch wrapper)
    └── hooks/
        └── useAnalytics.ts           # Hook exposing trackPlay, trackPause, etc.
```

**Structure Decision**: Web application (Option 2 from template) — backend adds new routers/services to the existing monolith; frontend-client adds a thin analytics emission layer that is non-blocking and fails silently.
