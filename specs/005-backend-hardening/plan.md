# Implementation Plan: Backend Hardening for Production Readiness

**Branch**: `005-backend-hardening` | **Date**: 2026-02-13 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-backend-hardening/spec.md`

## Summary

Harden the FastAPI backend for production readiness by fixing 3 critical security vulnerabilities (hardcoded JWT secret, IDOR on all profile-scoped endpoints, SQL injection via f-string interpolation), restricting CORS, adding split health checks (liveness + readiness), configuring the database connection pool, removing a duplicate entry point file, and centralizing admin authorization. No new database tables — all changes are to application-level configuration, dependencies, and query construction. 13 files modified, 1 deleted.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: FastAPI 0.115+, SQLAlchemy 2.0+ (async), Pydantic Settings, python-jose, bcrypt
**Storage**: PostgreSQL 16 + pgvector 0.7+ (existing — no schema changes)
**Testing**: Manual verification (test suite is a separate feature, out of scope)
**Target Platform**: Linux server (Docker container)
**Project Type**: Web application (backend only — this feature does not touch frontend)
**Performance Goals**: Health check readiness < 5s timeout, connection pool handles 50+ concurrent requests
**Constraints**: No new Python dependencies, all configuration via environment variables
**Scale/Scope**: 13 files modified, 1 file deleted, 0 new files (besides the escape_like helper added to an existing service file or a shared utils module)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. PoC-First Quality | PASS | Security fixes (JWT, IDOR, SQLi) are about correctness, not production over-engineering. Constitution says to skip rate limiting/caching — we do. Pool config (pool_size=20) is also a correctness fix: the default of 5 causes failures in basic multi-user demo scenarios with concurrent bookmark heartbeats, breaking PoC demonstrability. |
| II. Monolithic Simplicity | PASS | All changes within single FastAPI app. No new services or modules introduced. |
| III. AI-Native by Default | N/A | Hardening feature — not adding AI capabilities. |
| IV. Docker Compose as Truth | PASS | docker-compose.yml updated for JWT_SECRET env var. Stack still runs with `docker compose up`. |
| V. Seed Data as Demo | N/A | No data changes. |
| Constraints: uv for deps | PASS | No new dependencies added. |
| Constraints: No cloud deps | PASS | No external services. |

**Post-Phase 1 Re-check**: All gates still pass. No new services, no new dependencies, no architectural changes.

## Project Structure

### Documentation (this feature)

```text
specs/005-backend-hardening/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: vulnerability audit + fix decisions
├── data-model.md        # Phase 1: entity documentation (no schema changes)
├── quickstart.md        # Phase 1: verification guide
├── contracts/           # Phase 1: API contracts
│   ├── health-check.yaml
│   ├── error-responses.yaml
│   └── cors-policy.yaml
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (files affected)

```text
backend/
├── main.py                          # DELETE (duplicate entry point)
└── app/
    ├── config.py                    # MODIFY: SecretStr, pool settings
    ├── database.py                  # MODIFY: pool configuration
    ├── dependencies.py              # MODIFY: VerifiedProfileId, AdminUser
    ├── main.py                      # MODIFY: CORS, health checks, JWT validation
    ├── routers/
    │   ├── admin.py                 # MODIFY: AdminUser dep, ILIKE escape
    │   ├── catalog.py               # MODIFY: OptionalVerifiedProfileId
    │   ├── epg.py                   # MODIFY: VerifiedProfileId + Optional
    │   ├── recommendations.py       # MODIFY: VerifiedProfileId + Optional
    │   └── viewing.py               # MODIFY: VerifiedProfileId
    └── services/
        ├── catalog_service.py       # MODIFY: ILIKE escape
        ├── epg_service.py           # MODIFY: ILIKE escape
        ├── recommendation_service.py # MODIFY: bind params for IN clauses
        └── search_service.py        # MODIFY: ILIKE escape

docker/
└── docker-compose.yml               # MODIFY: JWT_SECRET env var
```

**Structure Decision**: Existing web application structure. All changes are modifications to existing files within `backend/app/`. One file deleted (`backend/main.py`). One Docker config updated.

## Complexity Tracking

No constitution violations — this section is not applicable.

## Change Summary by Work Stream

### Stream A: Security (P1 — must complete first)

| Item | Files | Effort | Dependencies |
|------|-------|--------|--------------|
| 1.1 JWT Secret | config.py, dependencies.py, main.py, docker-compose.yml | S | None |
| 1.2 IDOR Fix | dependencies.py, viewing.py, catalog.py, epg.py, recommendations.py | M | None |
| 1.3 SQL Injection | recommendation_service.py, search_service.py, catalog_service.py, epg_service.py, admin.py | M | None |

### Stream B: Reliability (P2 — can parallelize with Stream A)

| Item | Files | Effort | Dependencies |
|------|-------|--------|--------------|
| 1.4 CORS | main.py | S | None |
| 1.5 Health Checks | main.py | S | None |
| 1.7 DB Pool | config.py, database.py | S | 1.1 (config.py shared) |

### Stream C: Cleanup (P3 — quick wins, no dependencies)

| Item | Files | Effort | Dependencies |
|------|-------|--------|--------------|
| 1.6 Delete duplicate | backend/main.py | S | None |
| 2.4 Admin auth dep | dependencies.py, admin.py | S | 1.2 (dependencies.py shared) |
