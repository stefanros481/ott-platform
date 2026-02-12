# Tasks: Continue Watching & Cross-Device Bookmarks

**Input**: Design documents from `/specs/004-continue-watching-bookmarks/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/continue-watching-api.yaml, quickstart.md

**Tests**: Not explicitly requested — test tasks omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Database migration, model extension, and shared service creation

- [x] T001 Extend Bookmark model with `dismissed_at` nullable DateTime field and `uq_bookmark_profile_content` unique constraint on `(profile_id, content_id)` in `backend/app/models/viewing.py`; create Alembic migration `add_bookmark_dismissed_at_and_unique_constraint` that deduplicates any existing rows before adding the constraint
- [x] T002 Extend Pydantic schemas: add `ContinueWatchingItem`, `ContinueWatchingResponse`, `TitleInfo`, `NextEpisodeInfo` response schemas and update `BookmarkResponse` with `dismissed_at` field in `backend/app/schemas/viewing.py`
- [x] T003 Create `BookmarkService` with core business logic: `upsert_bookmark` (with 95%/2-min completion detection), `get_active_bookmarks`, `get_paused_bookmarks`, `dismiss_bookmark`, `restore_bookmark`, and `resolve_next_episode` in `backend/app/services/bookmark_service.py`
- [x] T004 Create seed bookmark data script with 7 bookmarks across profiles covering active, stale, dismissed, and completed states per data-model.md in `backend/app/seed/seed_bookmarks.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Enhanced backend endpoints that all frontend stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Enhance `GET /viewing/continue-watching` endpoint: accept `device_type`, `hour_of_day`, `limit` query params; use `BookmarkService.get_active_bookmarks`; return `ContinueWatchingItem[]` with `progress_percent`, `title_info`, and `next_episode`; filter out completed/dismissed/stale; limit to 20 items in `backend/app/routers/viewing.py`
- [x] T006 Add `GET /viewing/continue-watching/paused` endpoint: return dismissed + stale bookmarks ordered by most recently dismissed/stale first using `BookmarkService.get_paused_bookmarks` in `backend/app/routers/viewing.py`
- [x] T007 [P] Add `POST /viewing/bookmarks/{bookmark_id}/dismiss` endpoint: set `dismissed_at` to now, validate bookmark belongs to profile, return updated bookmark in `backend/app/routers/viewing.py`
- [x] T008 [P] Add `POST /viewing/bookmarks/{bookmark_id}/restore` endpoint: clear `dismissed_at`, set `updated_at` to now, return updated bookmark in `backend/app/routers/viewing.py`
- [x] T009 Update `PUT /viewing/bookmarks` endpoint to use `BookmarkService.upsert_bookmark` with auto-completion logic (95% or final 2 minutes) and series next-episode advancement in `backend/app/routers/viewing.py`
- [x] T010 Extend frontend API client: add `getContinueWatching(profileId, deviceType?, hourOfDay?)`, `getPausedBookmarks(profileId)`, `dismissBookmark(bookmarkId, profileId)`, `restoreBookmark(bookmarkId, profileId)` in `frontend-client/src/api/viewing.ts`
- [x] T011 Run seed script and verify all 5 endpoints return expected data via quickstart.md curl commands

**Checkpoint**: All backend endpoints operational, frontend API client ready — user story implementation can begin

---

## Phase 3: User Story 1 — Cross-Device Bookmark Sync (Priority: P1) 🎯 MVP

**Goal**: Player sends 30-second heartbeats, bookmarks persist server-side, resume from bookmark position on any device. Auto-complete at 95%/2 min. Series advance to next episode.

**Independent Test**: Play content in one browser tab, pause at a known position, open a second tab and verify Continue Watching shows the correct position. Tap to resume and confirm playback starts from that position.

### Implementation for User Story 1

- [x] T012 [P] [US1] Create `useBookmarkSync` hook: 30-second heartbeat interval during playback, `localStorage` caching of pending bookmarks when offline, sync-on-reconnect logic, save on pause/stop/unmount in `frontend-client/src/hooks/useBookmarkSync.ts`
- [x] T014 [P] [US1] Update `VideoPlayer.tsx` `onPositionUpdate` interval from 10 seconds to 30 seconds to match the heartbeat spec in `frontend-client/src/components/VideoPlayer.tsx`
- [x] T013 [US1] Update `PlayerPage.tsx` to use `useBookmarkSync` hook instead of direct `saveBookmark` calls: pass content metadata, wire hook to VideoPlayer's `onPositionUpdate` callback, ensure resume-from-bookmark passes `startPosition` to VideoPlayer (depends on T012 + T014) in `frontend-client/src/pages/PlayerPage.tsx`

**Checkpoint**: Bookmarks sync across tabs at 30s intervals, resume from position works, auto-completion triggers at 95%, series advance works

---

## Phase 4: User Story 2 — Continue Watching Rail Display (Priority: P1)

**Goal**: Dedicated Continue Watching rail on home screen with progress bars, episode info, max 20 items, hidden when empty. Tapping resumes playback.

**Independent Test**: Log in as a profile with seed bookmarks. Verify the Continue Watching rail shows on the home screen with progress bars. Tap an item and verify playback resumes from the bookmarked position. Verify the rail is hidden when no active bookmarks exist.

### Implementation for User Story 2

- [x] T015 [P] [US2] Create `ContinueWatchingCard` component: poster/landscape image, progress bar overlay (computed from `progress_percent`), title + episode info (S_E_ format), dismiss button (X or swipe), "Up Next" badge for series with `next_episode` in `frontend-client/src/components/ContinueWatchingCard.tsx`
- [x] T016 [US2] Update `HomePage.tsx` to fetch Continue Watching from the dedicated `GET /viewing/continue-watching` endpoint (separate from recommendations), render as first rail using `ContinueWatchingCard` components inside a horizontal scroll, hide rail entirely when response is empty, add "Paused" link/button below the rail in `frontend-client/src/pages/HomePage.tsx`

**Checkpoint**: Home screen shows Continue Watching rail with progress bars, cards are tappable to resume, empty state hides rail, dismiss button renders but is wired in US5

---

## Phase 5: User Story 3 — AI-Sorted by Resumption Likelihood (Priority: P2)

**Goal**: Continue Watching rail sorted by AI-predicted resumption score using weighted heuristic (recency 0.4, completion 0.25, series_momentum 0.35). Context-aware time_affinity_score deferred to US4. Fallback to recency when scoring fails.

**Independent Test**: With 5+ bookmarks at varied ages and completion levels, verify the rail is not purely recency-sorted. Verify series with recent consecutive completions rank higher. Verify fallback to recency if scoring returns null.

**Depends on**: US1 + US2 (needs bookmark data and working rail)

### Implementation for User Story 3

- [x] T017 [US3] Add `compute_resumption_scores` method to `recommendation_service.py`: weighted heuristic combining `recency_score` (exponential decay, weight 0.4), `completion_score` (peak at 20-80%, weight 0.25), `series_momentum_score` (bonus for series with recent completed episodes in same title via completed bookmarks joined through episodes→seasons→titles, weight 0.35); accept `device_type` and `hour_of_day` as optional inputs (ignored until US4); return dict of `bookmark_id → score` in `backend/app/services/recommendation_service.py`
- [x] T018 [US3] Integrate scoring into `GET /viewing/continue-watching` endpoint: call `compute_resumption_scores` with context params, sort results by score descending, fall back to `updated_at` descending if scoring raises an exception or returns empty, attach `resumption_score` to each response item in `backend/app/routers/viewing.py`

**Checkpoint**: Rail ordering visibly differs from pure recency, responds to context params, graceful fallback works

---

## Phase 6: User Story 4 — Context-Aware Ordering (Priority: P2)

**Goal**: Frontend passes device type and local hour to the API. Short content promoted on mobile/morning, long content on TV/evening.

**Independent Test**: Call Continue Watching API with `device_type=mobile&hour_of_day=8` and verify short-remaining-time content ranks higher. Call with `device_type=tv&hour_of_day=21` and verify long content ranks higher.

**Depends on**: US3 (scoring function must exist)

### Implementation for User Story 4

- [x] T019 [US4] Update Continue Watching fetch call in `HomePage.tsx` to pass `device_type` (detect from user agent or default to `web`) and `hour_of_day` (from `new Date().getHours()`) as query parameters to the API in `frontend-client/src/pages/HomePage.tsx`
- [x] T020 [US4] Add `time_affinity_score` component to `compute_resumption_scores` (weight 0.25, redistributing from recency 0.4→0.3, completion 0.25→0.2, momentum 0.35→0.25): for `device_type=mobile` + morning hours (6-10), boost items with remaining duration < 30 min; for `device_type=tv` + evening hours (19-23), boost items with remaining duration > 60 min; neutral weighting for other combinations in `backend/app/services/recommendation_service.py`

**Checkpoint**: Same profile shows different rail ordering when queried with mobile/morning vs TV/evening context

---

## Phase 7: User Story 5 — Stale Content Auto-Archival & Paused Section (Priority: P3)

**Goal**: Bookmarks inactive for 30+ days automatically excluded from Continue Watching and shown in a Paused section. Includes manual dismiss and restore. One-tap access to Paused from Continue Watching.

**Independent Test**: Verify a bookmark with `updated_at` older than 30 days does not appear in the active rail. Navigate to the Paused page and verify it shows stale + dismissed items. Restore an item and verify it reappears in the active rail.

**Depends on**: US2 (needs Continue Watching rail with Paused link)

### Implementation for User Story 5

- [x] T021 [P] [US5] Create `PausedPage.tsx`: fetch from `GET /viewing/continue-watching/paused`, display bookmarks using `ContinueWatchingCard` with a "Restore" button instead of dismiss, handle restore via `POST /viewing/bookmarks/{id}/restore`, show empty state message when no paused items in `frontend-client/src/pages/PausedPage.tsx`
- [x] T022 [P] [US5] Add route for Paused page in the app router (e.g., `/paused`) and wire the "Paused" link from the Continue Watching rail on HomePage to navigate there in `frontend-client/src/App.tsx` (or router config)
- [x] T023 [US5] Wire dismiss action on `ContinueWatchingCard`: on dismiss click, call `POST /viewing/bookmarks/{id}/dismiss`, optimistically remove card from rail, show brief undo toast or confirmation in `frontend-client/src/components/ContinueWatchingCard.tsx`

**Checkpoint**: Stale bookmarks appear only in Paused, manual dismiss moves items to Paused, restore returns items to active rail, one-tap navigation works

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Seed data, edge cases, and validation

- [x] T024 Integrate `seed_bookmarks.py` into the main seed script so bookmarks are created during `docker compose up` initialization in `backend/app/seed/` (main seed entry point)
- [x] T025 Handle catalog removal edge case: in `BookmarkService.get_active_bookmarks`, LEFT JOIN with titles/episodes and exclude bookmarks where content no longer exists in `backend/app/services/bookmark_service.py`
- [x] T026 Run full quickstart.md validation: verify all curl commands and frontend scenarios pass per `specs/004-continue-watching-bookmarks/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (model + schemas + service must exist before endpoints)
- **User Stories (Phase 3+)**: All depend on Phase 2 (backend endpoints + frontend API client)
  - US1 and US2 can proceed in parallel after Phase 2
  - US3 depends on US1 + US2 (needs bookmarks and rail to sort)
  - US4 depends on US3 (extends the scoring function)
  - US5 can proceed after US2 (needs the rail with Paused link, independent of AI sorting)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

```
Phase 1 (Setup) → Phase 2 (Foundational)
                        ↓
            ┌───────────┼───────────┐
            ↓           ↓           ↓
        US1 (P1)    US2 (P1)    US5 (P3)
            ↓           ↓           ↑
            └─────┬─────┘           │
                  ↓                 │
              US3 (P2) ────────────*│
                  ↓                 │
              US4 (P2)              │
                  ↓                 │
              Phase 8 (Polish) ←────┘
```

*US5 depends on US2 only (not on US3/US4)

### Within Each User Story

- Backend changes before frontend changes
- Services before routes/endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- T007 and T008 can run in parallel (dismiss + restore are independent endpoints)
- T012 and T014 can run in parallel (different files), then T013 integrates both
- T015 can run in parallel with T012-T014 (different files, no dependencies)
- T021 and T022 can run in parallel (PausedPage + route registration)
- US1 and US2 can run in parallel after Phase 2
- US5 can run in parallel with US3/US4 (independent dependency chain from US2)

---

## Parallel Example: User Stories 1 & 2 (after Phase 2)

```bash
# Stream A: User Story 1 (bookmark sync)
Task: "T012 [P] [US1] Create useBookmarkSync hook" &  # parallel with T014
Task: "T014 [P] [US1] Update VideoPlayer.tsx interval to 30s"  # parallel with T012
# then sequentially:
Task: "T013 [US1] Update PlayerPage.tsx to use useBookmarkSync (depends on T012 + T014)"

# Stream B: User Story 2 (rail display) — can run simultaneously with Stream A
Task: "T015 [US2] Create ContinueWatchingCard in frontend-client/src/components/ContinueWatchingCard.tsx"
Task: "T016 [US2] Update HomePage.tsx with dedicated Continue Watching rail"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup (model, schemas, service, seed)
2. Complete Phase 2: Foundational (all endpoints + API client)
3. Complete Phase 3: US1 — Bookmark sync with 30s heartbeat
4. Complete Phase 4: US2 — Continue Watching rail with progress bars
5. **STOP and VALIDATE**: Test cross-device sync + rail display independently
6. Deploy/demo if ready — this delivers core value

### Incremental Delivery

1. Setup + Foundational → Backend ready
2. US1 + US2 (parallel) → Core experience (MVP!) 🎯
3. US3 → AI-sorted rail (visible differentiator)
4. US4 → Context-aware ordering (polished intelligence)
5. US5 → Paused section + auto-archival (housekeeping)
6. Polish → Seed integration, edge cases, full validation

### Parallel Team Strategy

With two developers after Phase 2:

- **Developer A**: US1 (bookmark sync) → US3 (AI scoring) → US4 (context signals)
- **Developer B**: US2 (rail display) → US5 (paused section) → Polish

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently testable at its checkpoint
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- The 30-day stale threshold in US5 uses the existing `updated_at` field — no cron job needed, computed at query time
