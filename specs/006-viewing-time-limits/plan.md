# Implementation Plan: Profile Viewing Time Limits

**Branch**: `006-viewing-time-limits` | **Date**: 2026-02-13 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/006-viewing-time-limits/spec.md`

## Summary

Add per-profile daily viewing time limits for child profiles, with configurable weekday/weekend schedules, configurable reset times, educational content exemption, cross-device server-side enforcement via direct DB writes per heartbeat, parent PIN override (local + remote), a kid-friendly lock screen, viewing history, and on-demand weekly reports. Extends the existing Profile and Parental Controls system within the monolithic FastAPI backend. 5 new database tables, 2 new routers, 2 new services, 1 Alembic migration, and frontend components for settings, lock screen, and time indicator.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: FastAPI 0.115+, SQLAlchemy 2.0+ (async), Pydantic Settings, python-jose (JWT), bcrypt (PIN hashing)
**Storage**: PostgreSQL 16 + pgvector 0.7+ (5 new tables, 1 migration)
**Testing**: Manual verification + seed data scenarios (automated test suite is out of scope per PoC constraints)
**Target Platform**: Linux server (Docker container) + React 18 frontend
**Project Type**: Web application (backend + frontend-client changes)
**Performance Goals**: Balance query < 100ms p95, heartbeat ingestion handles 500+ concurrent child sessions in PoC, settings propagation < 5s
**Constraints**: Single FastAPI process (constitution: monolithic simplicity), `uv` for deps, `docker compose up` as entry point, no cloud dependencies, no new external services
**Scale/Scope**: 5 new tables, ~12 new/modified backend files, ~8 new/modified frontend files, 1 Alembic migration

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. PoC-First Quality | PASS | Feature is a core parental controls capability needed for demo. Skipping: horizontal scaling, multi-region, advanced caching. Using in-process tracking (not Redis) per PoC constraints. |
| II. Monolithic Simplicity | PASS | All logic within single FastAPI app. New routers (`parental_controls.py`, `viewing_time.py`) follow existing router-based module separation. No new services or containers. |
| III. AI-Native by Default | N/A | Parental controls feature — not adding AI capabilities. Future enhancement: AI-suggested limits based on viewing patterns (Phase 2+). |
| IV. Docker Compose as Truth | PASS | No new containers or external services. Stack still runs with `docker compose up`. |
| V. Seed Data as Demo | PASS | Seed data will include: sample child profile with pre-configured limits, educational content tags on 5-10 titles, pre-populated viewing history for demo. |
| Constraints: uv for deps | PASS | No new Python dependencies needed — bcrypt already present for password hashing. |
| Constraints: No cloud deps | PASS | All enforcement in-process. No additional Redis usage for this feature — direct DB writes per heartbeat (UPSERT pattern). |
| Constraints: No version in docker-compose | PASS | No docker-compose changes needed. |

## Project Structure

### Documentation (this feature)

```text
specs/006-viewing-time-limits/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: design decisions
├── data-model.md        # Phase 1: entity documentation
├── quickstart.md        # Phase 1: verification guide
├── contracts/           # Phase 1: API contracts
│   ├── parental-controls-api.yaml
│   └── viewing-time-api.yaml
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (files affected)

```text
backend/
├── app/
│   ├── models/
│   │   ├── user.py              # EXTEND: add Account PIN fields to User
│   │   └── viewing_time.py      # NEW: ViewingTimeConfig, ViewingTimeBalance, ViewingSession, TimeGrant
│   ├── routers/
│   │   ├── parental_controls.py # NEW: PIN mgmt, viewing time config, history, weekly report
│   │   └── viewing_time.py      # NEW: heartbeat, balance, override, session mgmt
│   ├── schemas/
│   │   ├── parental_controls.py # NEW: request/response schemas for parental controls
│   │   └── viewing_time.py      # NEW: heartbeat, balance, override schemas
│   ├── services/
│   │   ├── pin_service.py       # NEW: PIN create/verify/reset with bcrypt + lockout
│   │   └── viewing_time_service.py # NEW: tracking, enforcement, balance, reset, reporting
│   ├── dependencies.py          # EXTEND: add PIN verification dependency
│   └── main.py                  # EXTEND: register new routers
├── alembic/versions/
│   └── 003_add_viewing_time_limits.py  # NEW: migration for 5 new tables + User.pin_hash
└── seed/
    └── seed_viewing_time.py     # NEW: seed data for demo

frontend-client/
├── src/
│   ├── components/
│   │   ├── ParentalControls/    # NEW: settings UI for viewing time limits
│   │   ├── ViewingTimeIndicator.tsx  # NEW: remaining time badge in profile menu
│   │   ├── ViewingTimeWarning.tsx    # NEW: playback warning overlays (15m, 5m)
│   │   └── LockScreen.tsx       # NEW: kid-friendly time-expired screen
│   ├── hooks/
│   │   └── useViewingTime.ts    # NEW: hook for balance polling + heartbeat sending
│   ├── services/
│   │   └── viewingTimeApi.ts    # NEW: API client for viewing time endpoints
│   └── pages/
│       └── ParentalControlsPage.tsx  # NEW: PIN-protected settings page
```

**Structure Decision**: Extends the existing web application structure (backend/ + frontend-client/) with new modules following established patterns. New routers map to future microservice boundaries (Viewing Time Service, Parental Controls Service) per Constitution II.

## Post-Phase 1 Constitution Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. PoC-First Quality | PASS | Design uses direct DB writes (no Redis), on-demand computation (no scheduler), polling (no WebSocket). All appropriate for PoC scale. |
| II. Monolithic Simplicity | PASS | Two new routers + two new services within single FastAPI app. No new containers or external services. |
| III. AI-Native by Default | N/A | Parental controls — no AI capabilities added. Future: AI-suggested limits based on viewing patterns. |
| IV. Docker Compose as Truth | PASS | No changes to docker-compose. No new containers. Stack still runs with `docker compose up`. |
| V. Seed Data as Demo | PASS | Seed script includes child profile with limits, educational titles, pre-populated viewing history. |
| Constraints: uv for deps | PASS | No new Python dependencies — bcrypt already present. |
| Constraints: No cloud deps | PASS | All enforcement in-process with PostgreSQL. |

No constitution violations introduced during Phase 1 design.

## Complexity Tracking

No constitution violations to justify. All design fits within monolithic simplicity.
