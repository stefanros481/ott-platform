# Implementation Plan: TSTV — Start Over & Catch-Up TV

**Branch**: `016-tstv` | **Date**: 2026-02-24 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/016-tstv/spec.md`

---

## Summary

Implement Time-Shifted TV (TSTV) on the existing OTT platform. FFmpeg subprocesses
running inside the backend container write encrypted fMP4 segments to a shared
Docker volume with strftime-based filenames. FastAPI assembles HLS EVENT (start-over)
and VOD (catch-up) manifests on demand by reading the filesystem. A ClearKey KMS
(two backend endpoints + one new DB table) provides per-channel AES-128 encryption.
The existing Bookmark service is extended with two new content types. The admin panel
gains a Streaming page for SimLive controls and TSTV rule management. The client
frontend gains a CatchUpPage and start-over entry points on the EPG and player pages.

---

## Technical Context

**Language/Version**: Python 3.12, TypeScript 5.x
**Primary Dependencies**: FastAPI 0.115, SQLAlchemy 2.0, Alembic, React 18, Shaka Player 4.12, FFmpeg (system), nginx:alpine
**Storage**: PostgreSQL 16 (schema changes via Alembic migration `007_tstv_schema.py`), `hls_data` Docker volume (fMP4 segments)
**Testing**: pytest (backend unit + integration), Vitest + Testing Library (frontend)
**Target Platform**: Linux server (Docker Compose), browser (Web client)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: Start-over manifest < 300ms p95; catch-up manifest < 300ms p95; segment delivery via nginx (no FastAPI overhead)
**Constraints**: No cloud dependencies; Docker Compose as ground truth; uv for Python deps; Shaka Player 4.12 (no swap)
**Scale/Scope**: 5 channels, PoC segment volume (~100K files per channel at 7-day retention)

---

## Constitution Check

*Evaluated against `.specify/memory/constitution.md`*

| Gate | Status | Notes |
|------|--------|-------|
| PoC-first (no over-engineering) | ✅ PASS | Single migration, subprocess-based FFmpeg, no Redis/sidecar |
| Monolithic FastAPI (no new services) | ✅ PASS | All endpoints added to existing backend; nginx is a CDN sidecar (config-only) |
| Docker Compose as truth | ✅ PASS | Two volume mounts + cdn service added to docker-compose.yml |
| No cloud dependencies | ✅ PASS | ClearKey KMS is fully self-hosted; no AWS/GCP required |
| uv for Python deps | ✅ PASS | No change needed; ffmpeg is a system binary via Dockerfile apt-get |
| Shaka Player 4.12 | ✅ PASS | Shaka supports ClearKey natively; no player changes needed |
| AI-Native by Default (§III) | ⚠️ ACCEPTED DEVIATION | All AI variants deferred to Phase 2 — TSTV is infrastructure-first; no viewing-history corpus exists until TSTV is live. See spec.md §Constitution Deviation for full rationale. |

---

## Project Structure

### Documentation (this feature)

```text
specs/016-tstv/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: 9 architectural decisions
├── data-model.md        # Phase 1: DB schema changes + new tables
├── quickstart.md        # Phase 1: How to run TSTV from scratch
├── contracts/
│   └── tstv.yaml        # Phase 1: OpenAPI 3.1 contract (15 endpoints)
└── checklists/
    └── requirements.md  # Spec quality checklist (all pass)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── models/
│   │   ├── epg.py               # EXTEND: add 6 columns to Channel, 3 to ScheduleEntry
│   │   ├── viewing.py           # MODIFY: change bookmarks unique constraint
│   │   └── tstv.py              # NEW: TSTVSession, Recording models
│   ├── routers/
│   │   ├── tstv.py              # NEW: viewer endpoints (channels, manifests, sessions)
│   │   ├── admin.py             # EXTEND: SimLive + TSTV rules endpoints
│   │   └── drm.py               # NEW: ClearKey KMS endpoints
│   ├── services/
│   │   ├── simlive_manager.py   # NEW: FFmpeg subprocess lifecycle management
│   │   ├── manifest_generator.py # NEW: HLS EVENT/VOD playlist assembly
│   │   └── drm_service.py       # NEW: key generation, license validation
│   ├── seed_data.py             # EXTEND: cdn_channel_key, TSTV flags, schedule entries, DRM keys
│   └── main.py                  # EXTEND: register tstv + drm routers; startup SimLive init
├── alembic/versions/
│   └── 007_tstv_schema.py       # NEW: single migration for all schema changes
├── hls_sources/                  # NEW: source .mp4 files (not committed, volume-mounted)
└── Dockerfile                   # EXTEND: apt-get install ffmpeg

nginx/
└── cdn.conf                     # NEW: nginx config for HLS segment serving

frontend/
├── src/
│   ├── pages/
│   │   ├── CatchUpPage.tsx      # NEW: catch-up browse by channel + date
│   │   └── EpgPage.tsx          # EXTEND: catch-up badge on past programs
│   ├── components/
│   │   ├── StartOverToast.tsx   # NEW: Start Over prompt (program title + elapsed time + accept/dismiss)
│   │   └── CatchUpRail.tsx      # NEW: catch-up rail on HomePage
│   └── services/
│       └── tstv.ts              # NEW: API client for TSTV endpoints
│   ├── admin/
│       ├── pages/
│       │   └── StreamingPage.tsx # NEW: SimLive controls + TSTV rules
│       └── components/
│           ├── SimLivePanel.tsx   # NEW: per-channel start/stop/restart/status
│           └── TSTVRulesPanel.tsx # NEW: CUTV window dropdown + toggles

docker-compose.yml               # EXTEND: cdn service, hls_data volume mounts
```

---

## Complexity Tracking

One accepted deviation (§III AI-Native by Default) — see Constitution Check table. No unresolved violations.

---

## Artifact Index

| File | Status | Description |
|------|--------|-------------|
| [spec.md](spec.md) | ✅ Complete | Feature spec with 5 clarifications applied |
| [research.md](research.md) | ✅ Complete | 9 decisions (segment format, FFmpeg arch, DRM, bookmarks, etc.) |
| [data-model.md](data-model.md) | ✅ Complete | 4 table changes + 3 new tables + Alembic migration outline |
| [contracts/tstv.yaml](contracts/tstv.yaml) | ✅ Complete | OpenAPI 3.1 spec for all 15 endpoints |
| [quickstart.md](quickstart.md) | ✅ Complete | 8-step setup guide with troubleshooting |
| tasks.md | ✅ Complete | 64 tasks across 9 phases, generated by `/speckit.tasks` |
