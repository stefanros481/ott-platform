# Implementation Plan: Parental Rating Enforcement

**Branch**: `001-parental-rating-enforcement` | **Date**: 2026-02-09 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-parental-rating-enforcement/spec.md`

## Summary

Enforce the profile's `parental_rating` across all content surfaces (catalog browse, search, featured, home rails, similar titles, title detail) by introducing a rating hierarchy check in the backend services and passing `profile_id` from the frontend on all catalog/recommendation API calls. Profiles with `TV-MA` (default) skip filtering entirely for zero performance impact.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5+ (frontend)
**Primary Dependencies**: FastAPI 0.115+, SQLAlchemy 2.0+ async, React 18, TanStack Query
**Storage**: PostgreSQL 16 + pgvector
**Testing**: Manual PoC testing (no automated test suite)
**Target Platform**: Docker Compose (local)
**Project Type**: Web application (FastAPI backend + 2 React frontends)
**Performance Goals**: No perceptible latency increase; TV-MA profiles skip filtering entirely
**Constraints**: PoC scope — no PIN overrides, no admin filtering, single FastAPI process
**Scale/Scope**: 70 seed titles, 5 users, ~10 profiles

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. PoC-First Quality | PASS | Simple filtering logic, no production hardening |
| II. Monolithic Simplicity | PASS | Changes are in existing services/routers, no new services |
| III. AI-Native by Default | PASS | Recommendations respect parental ratings too |
| IV. Docker Compose as Truth | PASS | No new containers or external services |
| V. Seed Data as Demo | PASS | Existing seed data has varied age_ratings (TV-Y through TV-MA) |

All gates pass. No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/001-parental-rating-enforcement/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── services/
│   │   ├── catalog_service.py         # Add allowed_ratings filter to get_titles, get_featured_titles
│   │   ├── recommendation_service.py  # Add allowed_ratings filter to all rail + similar functions
│   │   └── rating_utils.py            # NEW: Rating hierarchy helper
│   └── routers/
│       ├── catalog.py                 # Add profile_id param, resolve parental_rating, pass to service
│       └── recommendations.py         # Add profile_id to similar/post-play, pass allowed_ratings

frontend-client/
├── src/
│   ├── api/
│   │   ├── catalog.ts                 # Add profile_id param to getTitles, getFeatured, getTitleById
│   │   └── recommendations.ts         # Add profile_id param to getSimilarTitles
│   └── pages/
│       ├── BrowsePage.tsx             # Pass profile_id to catalog calls
│       ├── HomePage.tsx               # Pass profile_id to featured call
│       ├── SearchPage.tsx             # Pass profile_id to search call
│       └── TitleDetailPage.tsx        # Pass profile_id to detail + similar calls, handle 403
```

**Structure Decision**: All changes are within existing files. One new utility module (`rating_utils.py`) for the rating hierarchy helper to keep the comparison logic DRY across catalog_service and recommendation_service.
