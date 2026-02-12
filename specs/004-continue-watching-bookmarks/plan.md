# Implementation Plan: Continue Watching & Cross-Device Bookmarks

**Branch**: `004-continue-watching-bookmarks` | **Date**: 2026-02-12 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-continue-watching-bookmarks/spec.md`

## Summary

Enhance the existing bookmark system with cross-device sync reliability, a dedicated Continue Watching rail on the home screen with progress bars, AI-sorted resumption ordering using a scoring service, context-aware device/time signals, manual dismiss, and stale content auto-archival to a "Paused" section. Builds on the existing Bookmark model, viewing router, and recommendation service.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5+ (frontend)
**Primary Dependencies**: FastAPI 0.115+, SQLAlchemy 2.0+ async, React 18, TanStack Query, Shaka Player 4+, Tailwind CSS 3+
**Storage**: PostgreSQL 16 + pgvector, Redis 7 (optional for caching)
**Testing**: pytest (backend), Vitest (frontend)
**Target Platform**: Web browser (primary), Docker Compose local dev
**Project Type**: Web application (backend + frontend-client + frontend-admin)
**Performance Goals**: Continue Watching rail loads within 2 seconds; bookmark sync within 10 seconds
**Constraints**: Single FastAPI process, no cloud dependencies, Docker Compose as truth, PoC-first quality
**Scale/Scope**: 50-100 titles seed data, single-user demo focus

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. PoC-First Quality | PASS | No production hardening (rate limiting, horizontal scaling) included |
| II. Monolithic Simplicity | PASS | All new logic in existing FastAPI routers/services; no new microservices |
| III. AI-Native by Default | PASS | AI resumption scoring included (Stories 3 & 4); not deferred to later |
| IV. Docker Compose as Truth | PASS | No external services added; uses existing PostgreSQL + Redis |
| V. Seed Data as Demo | PASS | Seed script will create bookmarks across multiple profiles for demo |

No violations. No complexity tracking needed.

## Project Structure

### Documentation (this feature)

```text
specs/004-continue-watching-bookmarks/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── continue-watching-api.yaml
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── models/viewing.py          # Extend Bookmark model (add dismissed_at field)
│   ├── schemas/viewing.py         # Extend schemas (ContinueWatchingResponse, context params)
│   ├── routers/viewing.py         # Extend endpoints (dismiss, paused, enhanced continue-watching)
│   ├── services/
│   │   ├── bookmark_service.py    # NEW: Bookmark business logic (completion, series advance, archival)
│   │   └── recommendation_service.py  # Extend: resumption scoring with context signals
│   └── seed/seed_bookmarks.py     # NEW: Seed bookmarks for demo

frontend-client/
├── src/
│   ├── api/viewing.ts             # Extend: dismiss, paused, enhanced continue-watching
│   ├── components/
│   │   └── ContinueWatchingCard.tsx  # NEW: Card with progress bar + dismiss
│   ├── pages/
│   │   ├── HomePage.tsx           # Extend: dedicated Continue Watching rail
│   │   ├── PlayerPage.tsx         # Extend: 30s heartbeat, resume from bookmark
│   │   └── PausedPage.tsx         # NEW: Paused/archived bookmarks view
│   └── hooks/
│       └── useBookmarkSync.ts     # NEW: Heartbeat + local caching logic
```

**Structure Decision**: Web application (Option 2). Extends existing backend/ and frontend-client/ directories. Two new backend files (bookmark_service.py, seed_bookmarks.py), three new frontend files (ContinueWatchingCard.tsx, PausedPage.tsx, useBookmarkSync.ts). All other changes are extensions to existing files.
