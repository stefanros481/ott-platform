# Tasks: Recommendations Quality, Watchlist Rail & Live TV Playback

**Input**: Design documents from `/specs/011-recs-watchlist-livetv/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/home-rails.yaml, quickstart.md
**Tests**: Not requested — no test tasks generated.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. No new database tables or migrations needed — all changes are to existing services and components.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Verify branch state and confirm existing service structure

- [x] T001 Verify branch `011-recs-watchlist-livetv` is checked out and read existing source files: `backend/app/services/recommendation_service.py`, `backend/app/services/search_service.py`, `backend/app/services/catalog_service.py`, `backend/app/routers/recommendations.py`, `backend/app/routers/catalog.py`, `frontend-client/src/pages/EpgPage.tsx`, `frontend-client/src/pages/PlayerPage.tsx`

**Note**: No Phase 2 (Foundational) needed — all database tables, models, migrations, and infrastructure already exist. User story implementation can begin immediately.

---

## Phase 3: User Story 1 - Accurate Personalized Recommendations (Priority: P1) 🎯 MVP

**Goal**: Exclude thumbs-down titles from "For You" rail and weight thumbs-up titles 2x in recommendation centroid (R-01, R-02)

**Independent Test**: Create a profile with bookmarks across 3 genres, thumbs-up 3 titles in Genre A, thumbs-down 2 titles in Genre B. Verify "For You" rail excludes thumbs-downed titles and Genre A titles dominate top positions.

### Implementation for User Story 1

- [x] T002 [US1] Add thumbs-down exclusion to `get_for_you_rail()`: query `Rating.rating == -1` title IDs, subtract from `interacted_ids` before centroid computation, and add to `excluded_ids` in the similarity query in `backend/app/services/recommendation_service.py`
- [x] T003 [US1] Add thumbs-up 2x weighting to `get_for_you_rail()`: duplicate embedding vectors for thumbs-up rated titles in the vector list before computing `np.mean()` centroid in `backend/app/services/recommendation_service.py`

**Checkpoint**: "For You" rail now excludes thumbs-downed titles and prioritizes thumbs-up preferences

---

## Phase 4: User Story 2 - My List Rail on Home Screen (Priority: P1)

**Goal**: Surface watchlist as a "My List" rail after Continue Watching and before For You on the home screen (R-03)

**Independent Test**: Add 5 titles to a profile's watchlist. Verify "My List" rail appears with those 5 titles in reverse chronological order.

### Implementation for User Story 2

- [x] T004 [US2] Add `_watchlist_rail()` helper function: query `WatchlistItem` joined to `Title` filtered by `profile_id` and `allowed_ratings`, ordered by `added_at DESC`, limit 20 in `backend/app/services/recommendation_service.py`
- [x] T005 [US2] Insert "My List" rail (rail_type: `"watchlist"`) into `get_home_rails()` after Continue Watching and before For You; omit when watchlist is empty in `backend/app/services/recommendation_service.py`

**Checkpoint**: Home screen shows "My List" rail with watchlist titles; rail hidden when watchlist is empty

---

## Phase 5: User Story 3 - Post-Play Next Episode (Priority: P1)

**Goal**: Prepend next sequential episode as first post-play suggestion when current content is a series episode (R-04)

**Independent Test**: Request post-play for Episode 3 of a series. Verify Episode 4 appears as the first suggestion.

### Implementation for User Story 3

- [x] T006 [US3] Add next-episode lookup to `get_post_play()`: check if `title_id` is an episode, find next episode by querying `WHERE episode_number > current ORDER BY episode_number ASC LIMIT 1` in same season (handles gaps), or first episode of next season by `season_number > current ORDER BY season_number ASC LIMIT 1`, prepend to similar titles list in `backend/app/services/recommendation_service.py`

**Checkpoint**: Post-play suggestions show next episode first for series content; movies unchanged

---

## Phase 6: User Story 6 - Trending Content Reflects Recent Popularity (Priority: P2)

**Goal**: Replace static count-based trending with time-decayed scoring using 7-day exponential decay (R-06)

**Note**: This phase is ordered before US4 because the cold-start "Popular Now" rail (US4) reuses the time-decayed trending logic.

**Independent Test**: Simulate 50 bookmarks on Title A in the last 2 days and 100 bookmarks on Title B over 90 days. Verify Title A ranks higher.

### Implementation for User Story 6

- [x] T007 [US6] Replace `COUNT(b.id)` trending query with `SUM(EXP(-EXTRACT(EPOCH FROM (NOW() - b.updated_at)) / (7 * 86400)))` time-decayed scoring in `_trending_rail()` in `backend/app/services/recommendation_service.py`

**Checkpoint**: Trending rail reflects recent activity; titles popular this week rank above titles with older engagement

---

## Phase 7: User Story 4 - New Profile Welcome Experience (Priority: P2)

**Goal**: Show "Popular Now" rail for profiles with no viewing history as a cold-start fallback (R-05)

**Depends on**: US6 (Phase 6) — uses the time-decayed `_trending_rail()` function

**Independent Test**: Create a new profile with zero history. Verify "Popular Now" rail appears in place of "For You".

### Implementation for User Story 4

- [x] T008 [US4] Add cold-start fallback to `get_home_rails()`: when `get_for_you_rail()` returns empty, call `_trending_rail()` and return as "Popular Now" (rail_type: `"popular_now"`) in the For You position in `backend/app/services/recommendation_service.py`

**Checkpoint**: New profiles see "Popular Now" rail; profiles with history see "For You" rail

---

## Phase 8: User Story 5 - Live TV Playback from EPG (Priority: P2)

**Goal**: Wire EPG program click to existing player page for live TV playback with EPG program info and Start Over (L-01)

**Independent Test**: Navigate to EPG, click a currently-airing program, verify existing player page opens with live stream and program info.

### Implementation for User Story 5

- [x] T009 [P] [US5] Implement `handleProgramClick` in `frontend-client/src/pages/EpgPage.tsx`: navigate to `/play/live/{channelId}` with `{ state: { channel, currentProgram } }` for currently-airing programs; show program details for future/past programs
- [x] T010 [US5] Add live TV type handler in `playbackInfo` useMemo: when `type === 'live'`, read channel/program from React Router state, set `manifestUrl` to `channel.hls_live_url`, set display title to program title and time slot; handle missing or broken `hls_live_url` by showing error state ("Channel temporarily unavailable") instead of attempting playback in `frontend-client/src/pages/PlayerPage.tsx`
- [x] T011 [US5] Add live TV Start Over offset calculation: when Start Over is pressed during live playback, compute `(now - program.start_time)` in seconds and seek backward from live edge by that amount in `frontend-client/src/pages/PlayerPage.tsx`
- [x] T012 [US5] Add program transition timer: use `useEffect` to schedule a timer at `program.end_time`, fetch the next program for the channel when timer fires, and update the displayed program info in `frontend-client/src/pages/PlayerPage.tsx`

**Checkpoint**: EPG click plays live TV in existing player; program info displayed; Start Over seeks to program start; program info updates on transition

---

## Phase 9: User Story 7 - Personalized Featured Content (Priority: P3)

**Goal**: Rank featured titles by cosine similarity to profile viewing preferences (R-11)

**Independent Test**: Mark 5 titles as featured. Create profile with Action affinity. Verify Action featured titles rank first.

### Implementation for User Story 7

- [x] T013 [US7] Add `get_personalized_featured_titles()` function: compute profile centroid (reuse centroid logic from `get_for_you_rail`), fetch featured title embeddings, sort by cosine similarity DESC, fall back to `created_at DESC` for new profiles in `backend/app/services/recommendation_service.py`
- [x] T014 [P] [US7] Add optional `profile_id` query parameter to `GET /catalog/featured` endpoint in `backend/app/routers/catalog.py`
- [x] T015 [US7] Update `get_featured_titles()` to call `get_personalized_featured_titles()` when `profile_id` is provided, preserving default sort for anonymous/new profiles in `backend/app/services/catalog_service.py`

**Checkpoint**: Featured titles sorted by personal relevance for established profiles; default order for new profiles

---

## Phase 10: User Story 8 - Faster Content Discovery (Priority: P3)

**Goal**: Fix semantic search N+1 query bug by batching genre lookups (S-01)

**Independent Test**: Perform a semantic search, verify backend logs show 2 queries (search + genre batch) instead of N+1.

### Implementation for User Story 8

- [x] T016 [P] [US8] Replace per-result genre query loop (lines 144-151) with single batch query `SELECT tg.title_id, g.name FROM title_genres tg JOIN genres g ON g.id = tg.genre_id WHERE tg.title_id IN :ids`, then map genres to results by title_id in `backend/app/services/search_service.py`

**Checkpoint**: Semantic search returns results with genres in 2 queries total instead of N+1

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end verification across all user stories

- [x] T017 Run all 9 quickstart.md verification scenarios (thumbs-down exclusion, thumbs-up weighting, My List rail, post-play next episode, cold-start Popular Now, time-decayed trending, personalized featured, search N+1 fix, live TV playback)
- [x] T018 Verify parental controls enforced on all new/modified rails: My List, Popular Now, Trending, Featured, post-play next episode

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — verify branch and read source
- **US1 (Phase 3)**: Can start after Setup — no dependencies on other stories
- **US2 (Phase 4)**: Can start after US1 — same file (`recommendation_service.py`), different function
- **US3 (Phase 5)**: Can start after US2 — same file, different function
- **US6 (Phase 6)**: Can start after US3 — same file, different function. **Must complete before US4**
- **US4 (Phase 7)**: **Depends on US6** — reuses time-decayed `_trending_rail()` for Popular Now
- **US5 (Phase 8)**: **Independent** (frontend only) — can run in parallel with any backend phase
- **US7 (Phase 9)**: Can start after US4 — touches `recommendation_service.py` + 2 other files
- **US8 (Phase 10)**: **Independent** — touches `search_service.py` only, can parallel with any phase
- **Polish (Phase 11)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: No dependencies — modifies `get_for_you_rail()` only
- **US2 (P1)**: No dependencies — adds new function `_watchlist_rail()` + modifies `get_home_rails()`
- **US3 (P1)**: No dependencies — modifies `get_post_play()` only
- **US6 (P2)**: No dependencies — modifies `_trending_rail()` only
- **US4 (P2)**: **Depends on US6** — calls the updated `_trending_rail()` from `get_home_rails()`
- **US5 (P2)**: No dependencies — frontend only (EpgPage.tsx + PlayerPage.tsx)
- **US7 (P3)**: No dependencies — new function in recommendation_service.py + changes to catalog router/service
- **US8 (P3)**: No dependencies — modifies `search_service.py` only

### Within Each User Story

- Service functions before router changes
- Backend before frontend (where applicable)
- Core logic before edge cases

### Parallel Opportunities

**Cross-phase parallelism** (different files, no conflicts):

1. **US5 (frontend)** can run in parallel with any backend story (US1–US4, US6–US8)
2. **US8 (search_service.py)** can run in parallel with any recommendation_service.py story
3. Within US5: T009 (EpgPage.tsx) can run in parallel with T010 (PlayerPage.tsx)
4. Within US7: T014 (catalog.py router) can run in parallel with T013 (recommendation_service.py)

**Sequential constraints** (same file):
- US1 → US2 → US3 → US6 → US4 → US7 all touch `recommendation_service.py` — must be sequential
- US5 T010 → T011 → T012 all touch `PlayerPage.tsx` — must be sequential

---

## Parallel Example: Maximum Throughput

```bash
# Developer A (backend - recommendation_service.py): Sequential
T002 → T003 → T004 → T005 → T006 → T007 → T008 → T013

# Developer B (frontend - EpgPage.tsx + PlayerPage.tsx): In parallel with Developer A
T009 → T010 → T011 → T012

# Developer C (backend - search + catalog): In parallel with Developer A
T016 (search N+1 fix)
Then: T014 + T015 (after T013 is complete)
```

---

## Implementation Strategy

### MVP First (P1 Stories Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 3: US1 — Accurate Recommendations (T002–T003)
3. Complete Phase 4: US2 — My List Rail (T004–T005)
4. Complete Phase 5: US3 — Post-Play Next Episode (T006)
5. **STOP and VALIDATE**: Test all 3 P1 stories independently
6. Deploy/demo if ready — home screen is already significantly better

### Incremental Delivery

1. **P1 Stories** (US1 + US2 + US3) → Core recommendation quality + watchlist + binge flow
2. **Add US6** → Trending rail becomes time-aware
3. **Add US4** → New profiles get a welcome experience
4. **Add US5** → Live TV playback works from EPG
5. **Add US7** → Featured titles personalized
6. **Add US8** → Search performance improved
7. Each increment adds value without breaking previous stories

### Parallel Team Strategy

With 2 developers:

1. Both read setup (T001)
2. **Developer A** (backend): US1 → US2 → US3 → US6 → US4 → US7 (recommendation_service.py chain)
3. **Developer B** (frontend + search): US5 (EpgPage + PlayerPage) → US8 (search N+1) → US7 T014-T015 (catalog router/service)
4. Polish together (T017–T018)

---

## Notes

- All 16 implementation tasks modify existing files — no new source files created
- No new database tables or migrations — all models already exist
- [P] tasks = different files, no dependencies on incomplete tasks in same phase
- [Story] label maps task to specific user story for traceability
- US4 MUST follow US6 (cold-start reuses time-decayed trending)
- Most backend tasks touch `recommendation_service.py` — serialize these
- Frontend tasks (US5) and search tasks (US8) are independent — parallelize freely
- Commit after each completed user story for clean incremental delivery
