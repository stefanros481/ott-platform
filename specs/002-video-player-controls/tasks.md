# Tasks: Video Player Controls

**Input**: Design documents from `/specs/002-video-player-controls/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, quickstart.md

**Tests**: No test framework configured (PoC — manual browser testing only). Test tasks are omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend-client/src/` (React + TypeScript + Tailwind CSS)
- Two files modified: `components/VideoPlayer.tsx` (primary), `pages/PlayerPage.tsx` (secondary)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add the `isLive` prop foundation that multiple user stories depend on

- [x] T001 Add `isLive?: boolean` to `VideoPlayerProps` interface and destructure with default `false` in `frontend-client/src/components/VideoPlayer.tsx`
- [x] T002 [P] Pass `isLive={type === 'live'}` prop to `<VideoPlayer>` invocation in `frontend-client/src/pages/PlayerPage.tsx`

---

## Phase 2: User Story 1 — Play On-Demand Content from Beginning (Priority: P1) MVP

**Goal**: VOD content (movies and episodes) starts playback from 0:00; live content starts at the live edge

**Independent Test**: Navigate to any title with a valid playback URL, press Play, confirm video starts at 0:00

### Implementation for User Story 1

- [x] T003 [US1] Guard `startPosition` application to skip when `isLive` is true in `frontend-client/src/components/VideoPlayer.tsx` — covers FR-001 (VOD starts at 0:00 by Shaka default) and FR-002 (live starts at live edge)

**Checkpoint**: VOD content starts from the beginning; live content (when routes are added) will start at the live edge

---

## Phase 3: User Story 2 — Transport Controls (Priority: P1)

**Goal**: Control bar displays Rewind 10s, Play/Pause, Forward 10s, and Start Over buttons with correct behavior

**Independent Test**: Play any content, hover to reveal control bar, click each button and verify expected behavior

### Implementation for User Story 2

- [x] T004 [US2] Add `rewind10()` function: `video.currentTime = Math.max(0, video.currentTime - 10)` in `frontend-client/src/components/VideoPlayer.tsx`
- [x] T005 [US2] Add `forward10()` function: `video.currentTime = Math.min(duration, video.currentTime + 10)` in `frontend-client/src/components/VideoPlayer.tsx`
- [x] T006 [US2] Add `startOver()` function: VOD sets `currentTime = 0` and auto-plays if paused in `frontend-client/src/components/VideoPlayer.tsx`
- [x] T007 [US2] Rework bottom control bar to 3-group layout (transport left, time center, utility right) in `frontend-client/src/components/VideoPlayer.tsx`
- [x] T008 [US2] Add inline SVG icons for Rewind 10s (counterclockwise arrow + "10"), Forward 10s (clockwise arrow + "10"), and Start Over (refresh arrow) in `frontend-client/src/components/VideoPlayer.tsx`

**Checkpoint**: All four transport controls visible and functional for VOD content

---

## Phase 4: User Story 3 — Control Bar Visibility on Hover (Priority: P1)

**Goal**: Control bar appears on mouse hover and auto-hides after 5 seconds of inactivity during playback

**Independent Test**: Play content, move mouse to show controls, stop moving and time the 5-second hide delay; verify controls stay visible while paused

### Implementation for User Story 3

- [x] T009 [US3] Update `hideControlsDelayed` timeout from `3000` to `5000` in `frontend-client/src/components/VideoPlayer.tsx`

**Checkpoint**: Controls auto-hide after 5 seconds during playback; remain visible while paused

---

## Phase 5: User Story 4 — Live Content Playback (Priority: P2)

**Goal**: Live streams show a LIVE badge, hide the seek bar, and Start Over jumps to the beginning of the live buffer

**Independent Test**: Navigate to a live content URL (when live routes are added) and confirm LIVE badge, hidden seek bar, and Start Over seeks to buffer start

### Implementation for User Story 4

- [x] T010 [US4] Conditionally hide seek bar when `isLive` is true in `frontend-client/src/components/VideoPlayer.tsx`
- [x] T011 [US4] Show LIVE badge with pulsing red dot instead of elapsed/total time display when `isLive` in `frontend-client/src/components/VideoPlayer.tsx`
- [x] T012 [US4] Update `startOver()` to seek to `player.seekRange().start` when `isLive` in `frontend-client/src/components/VideoPlayer.tsx`

**Checkpoint**: Live content plays from live edge, shows LIVE badge, hides seek bar, Start Over seeks to buffer start

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verify existing functionality is preserved and run full validation

- [x] T013 Verify existing player features (volume, fullscreen, seek bar, bookmark reporting) still work in `frontend-client/src/components/VideoPlayer.tsx`
- [x] T014 Run quickstart.md validation steps end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **User Story 1 (Phase 2)**: Depends on T001 (isLive prop exists)
- **User Story 2 (Phase 3)**: Depends on Phase 1 completion (prop + layout changes build on base)
- **User Story 3 (Phase 4)**: No dependency on other stories — only modifies timer constant
- **User Story 4 (Phase 5)**: Depends on T001 (isLive prop), T006 (startOver exists for live variant)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Depends on Setup only — independently testable
- **US2 (P1)**: Depends on Setup only — independently testable
- **US3 (P1)**: Depends on Setup only — independently testable (single constant change)
- **US4 (P2)**: Depends on Setup + US2 (startOver function must exist before adding live variant)

### Within Each User Story

- All tasks within a story are sequential (same file: `VideoPlayer.tsx`)
- T001 and T002 are parallel (different files)

### Parallel Opportunities

- T001 and T002 can run in parallel (different files)
- US1, US2, and US3 are independent of each other (though all modify the same file, they touch different sections)
- US4 depends on US2's `startOver()` function

---

## Parallel Example: Setup Phase

```bash
# These two tasks modify different files and can run in parallel:
Task: "T001 — Add isLive prop in VideoPlayer.tsx"
Task: "T002 — Pass isLive prop in PlayerPage.tsx"
```

---

## Implementation Strategy

### MVP First (User Stories 1-3)

1. Complete Phase 1: Setup (T001, T002)
2. Complete Phase 2: User Story 1 — VOD starts from beginning (T003)
3. Complete Phase 3: User Story 2 — Transport controls (T004-T008)
4. Complete Phase 4: User Story 3 — Auto-hide at 5 seconds (T009)
5. **STOP and VALIDATE**: All P1 stories complete — run quickstart verification

### Incremental Delivery

1. Setup + US1 → VOD playback works correctly (MVP!)
2. Add US2 → Transport controls functional → Demo
3. Add US3 → Auto-hide timing correct → Demo
4. Add US4 → Live content ready → Demo
5. Polish → Full validation → Feature complete

### Single Developer Strategy

Since all primary changes are in `VideoPlayer.tsx`, the recommended approach is sequential by phase:
1. Setup (both files) → US1 → US2 → US3 → US4 → Polish
2. Commit after each phase checkpoint

---

## Notes

- All primary changes are in a single file (`VideoPlayer.tsx`), so [P] parallelism is limited to Setup phase
- No test framework configured — all validation is manual via quickstart.md
- SVG icons must be inline (project convention: no icon library)
- Existing controls (volume, fullscreen, seek bar) must remain functional
- `PlayerPage.tsx` change is minimal (one prop addition) and future-proofing for live routes
