# Tasks: TSTV — Start Over & Catch-Up TV

**Input**: Design documents from `/specs/016-tstv/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/tstv.yaml ✅, quickstart.md ✅

**Tests**: No test tasks generated — not requested in the spec.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on other in-progress tasks)
- **[Story]**: Which user story this task belongs to (US1–US6)
- All paths relative to repository root

---

## Phase 1: Setup (Docker + nginx + FFmpeg)

**Purpose**: Add the three new runtime components to the existing stack before any feature work begins.

- [x] T001 Add `cdn` service (nginx:alpine), `hls_data` named volume, and volume mounts to `docker-compose.yml` per quickstart.md Step 3
- [x] T002 [P] Create `nginx/cdn.conf` with `/hls/` location block, CORS header, MIME types for `.m3u8`/`.m4s`/`.mp4`
- [x] T003 [P] Add `RUN apt-get install -y ffmpeg` to `backend/Dockerfile`

**Checkpoint**: `docker compose up --build` succeeds; CDN container is healthy; `ffmpeg -version` works inside the backend container.

---

## Phase 2: Foundational (Schema + Models + DRM + Seed)

**Purpose**: Database schema, SQLAlchemy models, DRM service, and seed data — **must be complete before any user story can be implemented or tested**.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T004 Write Alembic migration `backend/alembic/versions/007_tstv_schema.py` covering all 7 changes from data-model.md (channel columns, schedule_entry columns, bookmark constraint swap, tstv_sessions, recordings, drm_keys, indexes)
- [x] T005 [P] Extend `Channel` model in `backend/app/models/epg.py`: add `cdn_channel_key`, `tstv_enabled`, `startover_enabled`, `catchup_enabled`, `catchup_window_hours`, `cutv_window_hours` mapped columns
- [x] T006 [P] Extend `ScheduleEntry` model in `backend/app/models/epg.py`: add `catchup_eligible`, `startover_eligible`, `series_id` mapped columns
- [x] T007 [P] Create `backend/app/models/tstv.py` with `TSTVSession` and `Recording` SQLAlchemy models (as specified in data-model.md)
- [x] T008 [P] Add `DRMKey` SQLAlchemy model to `backend/app/models/tstv.py`
- [x] T009 Modify `Bookmark` model in `backend/app/models/viewing.py`: drop `uq_bookmark_profile_content` unique constraint definition; add `uq_bookmark_profile_content_type` on `(profile_id, content_id, content_type)`; ensure `'tstv_catchup'` and `'tstv_startover'` are valid `content_type` values
- [x] T010 Create `backend/app/services/drm_service.py`: key generation (16-byte random AES key + UUID KID), `get_or_create_active_key(channel_key)`, `resolve_key_by_kid(kid)`, license validation helper (JWT entitlement check)
- [x] T011 Create `backend/app/routers/drm.py`: `GET /api/v1/drm/keys/channel/{channel_key}` (admin-scoped) and `POST /api/v1/drm/license` (ClearKey JSON response per W3C spec)
- [x] T012 Extend `backend/app/seed_data.py`: assign `cdn_channel_key` (`ch1`–`ch5`) to 5 seeded channels; set all TSTV flags to `True`; set `cutv_window_hours` per channel; generate schedule entries for ±7 days as repeating loops (10–12 min per channel); insert static test DRM keys per channel
- [x] T013 Register `tstv` and `drm` routers in `backend/app/main.py`; add lifespan startup hook that calls `SimLiveManager.restore_running_channels()` on app start (non-blocking, logs warning if no channels configured)

**Checkpoint**: `alembic upgrade head` succeeds; seed script populates all 5 channels with TSTV data; `GET /api/v1/drm/keys/channel/ch1` returns a key for admin JWT.

---

## Phase 3: User Story 1 — Start Over a Currently Airing Program (Priority: P1) 🎯 MVP

**Goal**: Viewer tunes in late to a live channel, sees a Start Over prompt, accepts, and watches from the program's first frame with full trick-play.

**Independent Test**: Start the backend, run seed + migration, start SimLive for ch1, tune to ch1 in the browser 4+ minutes after a program started → toast appears → accept → video plays from beginning → scrub bar shows position behind live edge.

- [x] T014 Create `backend/app/services/simlive_manager.py`: in-memory PID registry, `start_channel(channel_key)` (fetch DRM key from drm_service, spawn FFmpeg fmp4 + CENC subprocess writing to `HLS_SEGMENT_DIR/{channel_key}/`), `stop_channel(channel_key)`, `restart_channel(channel_key)`, `get_status(channel_key)`, `list_all_statuses()`
- [x] T015 Create `backend/app/services/manifest_generator.py`: `list_segments(channel_key, start_dt, end_dt)` (filesystem scan of `HLS_SEGMENT_DIR/{channel_key}/`, parse strftime filenames `{key}-YYYYMMDDHHmmSS.m4s`, return ordered list); `build_event_manifest(channel_key, schedule_entry)` (HLS EVENT playlist from `schedule_entry.start_time` to now, with `#EXT-X-KEY` pointing to `/api/v1/drm/license`)
- [x] T016 [P] [US1] Create `backend/app/routers/tstv.py` with `GET /api/v1/tstv/channels` (returns channels where `tstv_enabled=True` with TSTV fields)
- [x] T017 [US1] Add `GET /api/v1/tstv/startover/{channel_id}` to `backend/app/routers/tstv.py`: query current `ScheduleEntry` for channel; check `channel.startover_enabled AND entry.startover_eligible`; return availability + `elapsed_seconds`
- [x] T018 [US1] Add `GET /api/v1/tstv/startover/{channel_id}/manifest` to `backend/app/routers/tstv.py`: validate `schedule_entry_id` param; check start-over eligibility (403 if disabled); call `manifest_generator.build_event_manifest()`; return m3u8 response
- [x] T019 [P] [US1] Create `frontend/src/services/tstv.ts`: typed API client wrapping `fetchTSTVChannels()`, `getStartOverAvailability(channelId)`, `getStartOverManifest(channelId, scheduleEntryId)`
- [x] T020 [P] [US1] Create `frontend/src/components/StartOverToast.tsx`: displays program title + elapsed time; "Start from Beginning" and "Continue Live" buttons; auto-dismisses after 10 seconds; fires `onAccept` / `onDismiss` callbacks
- [x] T021 [US1] Integrate `StartOverToast` into `frontend/src/pages/PlayerPage.tsx`: on live channel load, call `getStartOverAvailability()`; if `startover_available && elapsed_seconds > 180`, show `StartOverToast`; track dismissed prompts in session state so the toast does not reappear for the same program during the same session (FR-003)
- [x] T022 [US1] Handle toast accept in `frontend/src/pages/PlayerPage.tsx`: call `getStartOverManifest()`, reload Shaka Player with EVENT manifest URL, set player to start-over mode
- [x] T023 [US1] Configure Shaka Player ClearKey DRM in `frontend/src/pages/PlayerPage.tsx`: set `drm.servers['org.w3.clearkey']` to `/api/v1/drm/license` for all TSTV manifests

**Checkpoint**: Full start-over flow works end-to-end. `GET /api/v1/tstv/startover/{id}/manifest` returns a valid m3u8. Shaka loads and plays the start-over stream from the first segment.

---

## Phase 4: User Story 2 — Return to Live from Start Over (Priority: P1)

**Goal**: Viewer in Start Over mode can jump back to the live broadcast edge in one tap.

**Independent Test**: Start Start Over on a channel → click "Jump to Live" button → player switches to live stream within 1 second → badge changes from "START OVER" to "LIVE".

**Depends on**: US1 (T014–T023)

- [x] T024 [US2] Add "Jump to Live" button to player controls in `frontend/src/components/` or `frontend/src/pages/PlayerPage.tsx`; visible only when `playerMode === 'startover'`; calls `onJumpToLive()`
- [x] T025 [US2] Implement `onJumpToLive()` in `frontend/src/pages/PlayerPage.tsx`: reload Shaka with the live HLS URL (from `channel.hls_live_url`); reset player mode to `'live'`
- [x] T026 [US2] Add player mode badge to `frontend/src/pages/PlayerPage.tsx` or player overlay component: render "START OVER" badge in start-over mode, "LIVE" badge in live mode with animated dot
- [x] T027 [US2] Implement live-edge fast-forward throttle in `frontend/src/pages/PlayerPage.tsx`: when scrubber reaches within 30 seconds of the current segment's broadcast time, disable further fast-forward and show "At live edge" indicator (per spec edge case)

**Checkpoint**: US2 complete — "Jump to Live" works; badge transitions correctly; scrubbing cannot go past the live edge.

---

## Phase 5: User Story 3 — Browse and Play Catch-Up Programs (Priority: P2)

**Goal**: Viewer browses the past-7-days catch-up catalog, picks a program, and watches it as a VOD with full trick-play.

**Independent Test**: Navigate to `/catchup`, select a channel, select a program from 3 days ago → playback starts within 2s with full trick-play. Expired program shows "no longer available". Program without `catchup_eligible` shows lock icon.

**Depends on**: Foundational (T004–T013) + US1 infrastructure (T014, T015)

- [x] T028 Extend `backend/app/services/manifest_generator.py` with `build_vod_manifest(channel_key, schedule_entry)`: list segments within `[schedule_entry.start_time, schedule_entry.end_time]`; build HLS VOD (#EXT-X-ENDLIST) playlist; include `#EXT-X-KEY` header
- [x] T029 [US3] Add `GET /api/v1/tstv/catchup/{channel_id}` to `backend/app/routers/tstv.py`: return eligible past `ScheduleEntry` records within `channel.cutv_window_hours`; include `expires_at` and `bookmark_position_seconds` (null until US4)
- [x] T030 [US3] Add `GET /api/v1/tstv/catchup/{channel_id}/manifest` to `backend/app/routers/tstv.py`: validate `schedule_entry_id`; enforce CUTV window (`NOW() < entry.end_time + cutv_window_hours`); check `catchup_eligible`; call `manifest_generator.build_vod_manifest()`
- [x] T060 [US3] Add `GET /api/v1/tstv/catchup` (no channel_id path param) to `backend/app/routers/tstv.py`: cross-channel date browsing per FR-012; query params `date` (defaults today), `channel_id` (optional filter), `genre` (optional filter), `limit`, `offset`; returns eligible past `ScheduleEntry` records across all TSTV-enabled channels for the given date
- [x] T031 [P] [US3] Extend `frontend/src/services/tstv.ts` with `listCatchUpPrograms(channelId, limit?, offset?)`, `listCatchUpByDate(date?, channelId?, genre?)`, and `getCatchUpManifest(channelId, scheduleEntryId)`
- [x] T032 [P] [US3] Create `frontend/src/pages/CatchUpPage.tsx`: two browse modes — "By Channel" (channel selector + program list) and "By Date" (date tabs today through 7 days ago, all channels, genre filter) showing title, channel name, air time, duration, expiry date, play/lock state
- [x] T033 [US3] Add `/catchup` route to `frontend/src/App.tsx` router; add "Catch-Up TV" navigation entry to main nav
- [x] T034 [US3] Add catch-up badge and lock icon to past programs in `frontend/src/pages/EpgPage.tsx`: eligible programs show a play/clock icon; ineligible show lock icon; clicking eligible program navigates to CatchUpPage with channel preselected
- [x] T035 [US3] Extend `frontend/src/pages/PlayerPage.tsx`: accept `?mode=catchup&scheduleEntryId=<uuid>` query params; load catch-up manifest on mount; set player to VOD mode (no live edge, full scrub range)

**Checkpoint**: Full catch-up browse and play works end-to-end. VOD manifests load and play. Expired content returns 403 and shows "no longer available" in UI.

---

## Phase 6: User Story 4 — Continue Watching Across Devices (Priority: P3)

**Goal**: Viewer resumes a partially-watched catch-up program from exactly where they left off, on any device.

**Independent Test**: Watch 8 minutes of a catch-up program → close tab → open app → "Continue Watching" rail shows the program with a progress bar → clicking resumes at 8:xx with a "Resuming from 8:00" toast.

**Depends on**: US3 (T028–T035)

- [x] T036 Implement bookmark persistence in `backend/app/services/viewing_service.py` (or `backend/app/routers/viewing.py`): replace stub implementation with actual `upsert_bookmark()` that writes to DB; for `tstv_catchup` / `tstv_startover` content types use `ON CONFLICT DO UPDATE SET position_seconds = GREATEST(EXCLUDED.position_seconds, bookmarks.position_seconds)`
- [x] T037 [US4] Implement `GET /api/v1/viewing/bookmarks/{content_type}/{content_id}` (or equivalent existing endpoint): return bookmark for current profile; used by player to determine resume position
- [x] T038 [US4] Add `POST /api/v1/tstv/sessions` and `PATCH /api/v1/tstv/sessions/{session_id}` to `backend/app/routers/tstv.py`: create/update `TSTVSession` records for analytics
- [x] T039 [US4] Extend `frontend/src/pages/PlayerPage.tsx` with bookmark heartbeat: call bookmark upsert every 30 seconds during TSTV playback and on pause/stop events; pass `content_type` = `'tstv_catchup'` or `'tstv_startover'` and `schedule_entry_id` as `content_id`
- [x] T040 [US4] Extend `GET /api/v1/tstv/catchup/{channel_id}` response (T029) to include `bookmark_position_seconds` by joining with bookmarks for the current profile
- [x] T061 [P] [US4] Create `frontend/src/components/ResumeToast.tsx`: dismissable toast showing "Resuming from {mm:ss}" with a "Start from beginning" link; auto-dismisses after 3 seconds; fires `onRestart` / `onDismiss` callbacks (FR-021)
- [x] T062 [US4] Integrate `ResumeToast` into `frontend/src/pages/PlayerPage.tsx`: when loading a catch-up manifest with a saved bookmark, show `ResumeToast` with the resume position; "Start from beginning" resets playback to 0
- [x] T041 [P] [US4] Create `frontend/src/components/CatchUpRail.tsx`: horizontal scroll rail of TSTV Continue Watching items; shows thumbnail, title, progress bar, remaining time, expiry date; items expiring within 24h show "Expires today" badge
- [x] T042 [US4] Add `CatchUpRail` to `frontend/src/pages/HomePage.tsx` below the hero banner; fetch from `/api/v1/tstv/catchup` filtered to items with `bookmark_position_seconds > 0` across all channels

**Checkpoint**: Auto-save works every 30s. Switching to a second browser tab and refreshing shows the program in Continue Watching at the correct position. Furthest-position-wins: two concurrent writes → only the higher position is stored.

---

## Phase 7: User Story 5 — Per-Channel TSTV Rules Management (Priority: P4)

**Goal**: Admin can start/stop/restart SimLive streams per channel and change TSTV rules (enabled flags + CUTV window) from the admin panel without touching the terminal or restarting services.

**Independent Test**: Open admin panel → Streaming page → change ch3 catch-up window from 168h to 48h → save → immediately call `GET /api/v1/tstv/catchup/{ch3_id}` → programs beyond 48h ago are no longer returned.

**Depends on**: Foundational (T004–T013), SimLiveManager (T014)

- [x] T043 Add SimLive admin endpoints to `backend/app/routers/admin.py`: `GET /api/v1/admin/simlive/status` (all channels); `POST /api/v1/admin/simlive/{channel_key}/start`; `POST /api/v1/admin/simlive/{channel_key}/stop`; `POST /api/v1/admin/simlive/{channel_key}/restart`; `POST /api/v1/admin/simlive/cleanup` — all delegate to `SimLiveManager`; require admin JWT scope
- [x] T044 Add TSTV rules admin endpoints to `backend/app/routers/admin.py`: `GET /api/v1/admin/tstv/rules` (all channels); `PUT /api/v1/admin/tstv/rules/{channel_id}` (partial update of TSTV flags + `cutv_window_hours`; validates `cutv_window_hours` ∈ `{2, 6, 12, 24, 48, 72, 168}`)
- [x] T045 [P] [US5] Create `frontend/src/admin/pages/StreamingPage.tsx`: two panels — SimLive Controls (top) and TSTV Rules (bottom); wraps `SimLivePanel` and `TSTVRulesPanel`
- [x] T046 [P] [US5] Create `frontend/src/admin/components/SimLivePanel.tsx`: table of channels with `running` status badge, segment count, disk usage, and Start/Stop/Restart action buttons; polls status every 10 seconds
- [x] T047 [P] [US5] Create `frontend/src/admin/components/TSTVRulesPanel.tsx`: table of channels with toggle checkboxes for `tstv_enabled`, `startover_enabled`, `catchup_enabled`, and a `cutv_window_hours` dropdown (options: 2h/6h/12h/24h/48h/72h/168h); Save button per row
- [x] T048 [US5] Add `/streaming` route to the admin frontend router (`frontend/src/admin/App.tsx` or equivalent); add "Streaming" navigation item to admin sidebar
- [x] T049 [US5] Wire `SimLivePanel` to admin API calls in `frontend/src/services/tstv.ts` or new `frontend/src/services/admin.ts`: `getSimLiveStatus()`, `startChannel(key)`, `stopChannel(key)`, `restartChannel(key)`, `runCleanup()`
- [x] T050 [US5] Wire `TSTVRulesPanel` save to `PUT /api/v1/admin/tstv/rules/{channel_id}` in frontend; show success/error toast after save; rules take effect on next viewer request without page reload

**Checkpoint**: Admin can start/stop ch1 from the UI and verify segment writing starts/stops. Can change ch2 CUTV window to 6h and immediately verify the catch-up listing shortens.

---

## Phase 8: User Story 6 — Catch-Up Expiry Notifications (Priority: P5)

**Goal**: Viewer with a partially-watched catch-up program receives a notification 24 hours before it expires.

**Independent Test**: Insert a bookmark for a program with `expires_at = NOW() + 23h`; run the notification job; verify an in-app notification is created; open the app; verify the notification appears. Also verify "Expires today" badge appears on all listing surfaces for that program.

**Depends on**: US4 (T036–T042)

- [x] T051 Create `backend/app/services/notification_service.py`: `check_expiring_catchup()` function that queries bookmarks with `content_type IN ('tstv_catchup', 'tstv_startover')` joined with schedule entries expiring within 24 hours; emits one in-app notification per bookmark; mark bookmarks as notified to avoid duplicates
- [x] T052 [US6] Schedule `check_expiring_catchup()` to run hourly using APScheduler (or `asyncio` background task started in `main.py` lifespan); log results; does not block app startup
- [x] T053 [P] [US6] Add `expires_at` display to `frontend/src/pages/CatchUpPage.tsx` program list items and `frontend/src/pages/EpgPage.tsx` past-program entries — show formatted expiry date on every item
- [x] T054 [P] [US6] Add "Expires today" urgency badge to `frontend/src/components/CatchUpRail.tsx` and any Continue Watching surface when `expires_at` is within 24 hours
- [x] T055 [US6] Implement in-app notification fetch + display in the frontend: `GET /api/v1/notifications` (extend existing endpoint or create new); render expiry notification with "Watch Now" deep-link and "Record" link (PVR upsell, links to recordings page placeholder)

**Checkpoint**: Hourly job runs without error. In-app notification appears in the notification bell for expiring content. "Expires today" badge shows on CatchUpRail items within 24h of expiry.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Error handling, segment cleanup, edge states, and operational readiness.

- [x] T063 Add catch-up expiry filtering to `backend/app/routers/tstv.py`: in `GET /api/v1/tstv/catchup/{channel_id}` and `GET /api/v1/tstv/catchup` queries, exclude programs where `end_time + cutv_window_hours < NOW()`; ensure expired programs are never returned in browse listings (FR-014)
- [x] T064 Add mid-window rights revocation handling to `backend/app/routers/tstv.py` and `backend/app/services/manifest_generator.py`: when `catchup_eligible` or `startover_eligible` is set to `False` on a schedule entry or channel, exclude from browse/search queries within the next request cycle; for active playback sessions, allow manifest requests to continue until the session's current segment range is exhausted (FR-033)
- [x] T056 Add segment cleanup cron to `backend/app/services/simlive_manager.py`: `cleanup_old_segments()` scans `HLS_SEGMENT_DIR`, deletes `.m4s` files older than `channel.catchup_window_hours`; scheduled hourly; also callable via `POST /api/v1/admin/simlive/cleanup`
- [x] T057 [P] Add TSTV-specific structured log lines to `backend/app/services/simlive_manager.py`, `manifest_generator.py`, and `drm_service.py`: FFmpeg PID lifecycle, manifest build time (ms), key lookup, CUTV window enforcement decisions
- [x] T058 [P] Add frontend empty/error states to `frontend/src/pages/CatchUpPage.tsx` and `frontend/src/components/CatchUpRail.tsx`: "No catch-up available for this channel" empty state; "Content no longer available" for 403/expired; loading skeleton while fetching
- [x] T059 Handle schedule overrun edge case in `backend/app/services/manifest_generator.py`: when building a VOD playlist, if segments continue past `schedule_entry.end_time` (live sports overrun), include segments up to `end_time + 30 minutes` and log a warning

---

## Dependencies

### User Story Completion Order

```
Phase 1 (Setup)
    │
    ▼
Phase 2 (Foundational — BLOCKS ALL STORIES)
    │
    ├──▶ Phase 3 (US1 Start Over) ──▶ Phase 4 (US2 Return to Live)
    │                                           │
    │                                           ▼
    ├──▶ Phase 5 (US3 Catch-Up Browse)  ◀─────────── (shares manifest_generator from US1)
    │        │
    │        ▼
    │    Phase 6 (US4 Continue Watching)
    │        │
    │        ▼
    ├──▶ Phase 7 (US5 Admin Rules)  ◀──── depends on SimLiveManager from US1
    │
    └──▶ Phase 8 (US6 Expiry Notifications)  ◀──── depends on US4 bookmarks
```

### Within Each Phase

- Models before services
- Services before routers
- Routers before frontend
- Frontend API client before UI components
- UI components before page integration

---

## Parallel Opportunities

### Phase 2 (Foundational) — Run Together

```text
T004 (migration) — must run first
Then in parallel:
  T005 (Channel model)
  T006 (ScheduleEntry model)
  T007 (TSTVSession + Recording models)
  T008 (DRMKey model)
Then sequentially:
  T009 (Bookmark constraint — depends on model files being stable)
  T010 (drm_service)
  T011 (drm router — depends on T010)
  T012 (seed data — depends on T005, T006, T007, T008)
  T013 (main.py registration — depends on T011)
```

### Phase 3 (US1) — Run Together

```text
T014 (SimLiveManager) and T015 (ManifestGenerator) — independent, run in parallel
T016 (tstv router GET /channels) — independent of T014/T015
T019 (frontend tstv.ts) — independent of backend tasks
T020 (StartOverToast component) — independent of backend
Then:
  T017, T018 (manifest endpoints — depend on T015)
  T021, T022, T023 (frontend integration — depend on T019, T020)
```

### Phase 5 (US3) — Run Together

```text
T031 (tstv.ts catch-up methods) and T032 (CatchUpPage) — run in parallel
T028 (VOD manifest) — independent of frontend tasks
Then:
  T029, T030 (catch-up endpoints — depend on T028)
  T033, T034, T035 (frontend integration — depend on T031, T032)
```

---

## Implementation Strategy

### MVP First (US1 + US2 Only)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational (T004–T013)
3. Complete Phase 3: US1 Start Over (T014–T023)
4. Complete Phase 4: US2 Return to Live (T024–T027)
5. **STOP and VALIDATE**: Full start-over → jump-to-live flow works in the browser
6. Demo to stakeholders — core TSTV value is visible

### Incremental Delivery

| Milestone | Stories | Viewer Experience |
|-----------|---------|-------------------|
| M1 (MVP) | US1 + US2 | Start over any live program; return to live |
| M2 | + US3 | Full 7-day catch-up browse and play |
| M3 | + US4 | Cross-device continue watching; bookmark sync |
| M4 | + US5 | Admin can control SimLive and TSTV rules via UI |
| M5 | + US6 | Expiry notifications; urgency badges |

### Parallel Team Strategy

With two developers after Phase 2:
- **Dev A**: US1 (T014–T023) → US2 (T024–T027) → US5 (T043–T050)
- **Dev B**: US3 (T028–T035, T060) → US4 (T036–T042, T061–T062) → US6 (T051–T055)

Phase 9 polish can be divided between both after M5.

---

## Task Summary

| Phase | Tasks | Parallelizable | User Story |
|-------|-------|----------------|------------|
| 1: Setup | T001–T003 | 2 of 3 | — |
| 2: Foundational | T004–T013 | 4 of 10 | — |
| 3: US1 Start Over | T014–T023 | 3 of 10 | US1 (P1) |
| 4: US2 Return to Live | T024–T027 | 0 of 4 | US2 (P1) |
| 5: US3 Catch-Up Browse | T028–T035, T060 | 2 of 9 | US3 (P2) |
| 6: US4 Continue Watching | T036–T042, T061–T062 | 3 of 9 | US4 (P3) |
| 7: US5 Admin Rules | T043–T050 | 3 of 8 | US5 (P4) |
| 8: US6 Expiry Notifications | T051–T055 | 2 of 5 | US6 (P5) |
| 9: Polish | T056–T059, T063–T064 | 2 of 6 | — |
| **Total** | **64 tasks** | **20 parallelizable** | — |
