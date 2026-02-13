# Tasks: Profile Viewing Time Limits

**Input**: Design documents from `/specs/006-viewing-time-limits/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/
**Tests**: Not included — manual verification via quickstart.md per PoC constraints

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database migration and router registration

- [x] T001 Create Alembic migration `backend/alembic/versions/003_add_viewing_time_limits.py` — add `pin_hash` (VARCHAR 255 nullable), `pin_failed_attempts` (INTEGER default 0), `pin_lockout_until` (TIMESTAMPTZ nullable) to `users`; add `is_educational` (BOOLEAN default false) to `titles`; create tables `viewing_time_configs`, `viewing_time_balances`, `viewing_sessions`, `time_grants` with all constraints and indexes per data-model.md
- [x] T002 Register `parental_controls` and `viewing_time` routers in `backend/app/main.py` — add `app.include_router(parental_controls.router, prefix="/api/v1/parental-controls", tags=["Parental Controls"])` and `app.include_router(viewing_time.router, prefix="/api/v1/viewing-time", tags=["Viewing Time"])`; create stub router files at `backend/app/routers/parental_controls.py` and `backend/app/routers/viewing_time.py` with empty `APIRouter()` instances

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Models, schemas, and API client that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 [P] Extend User model with PIN fields in `backend/app/models/user.py` — add `pin_hash: Mapped[Optional[str]]` (String 255, nullable), `pin_failed_attempts: Mapped[int]` (Integer, default 0), `pin_lockout_until: Mapped[Optional[datetime]]` (DateTime timezone-aware, nullable)
- [x] T004 [P] Add `is_educational` boolean to Title model in `backend/app/models/catalog.py` — add `is_educational: Mapped[bool]` (Boolean, default False, server_default="false")
- [x] T005 [P] Create viewing time models in `backend/app/models/viewing_time.py` — implement `ViewingTimeConfig`, `ViewingTimeBalance`, `ViewingSession`, `TimeGrant` ORM classes with all fields, relationships, constraints (CHECK for 15-min increments, UNIQUE for profile_id on configs, UNIQUE for profile_id+reset_date on balances), and indexes (partial index on viewing_sessions for active sessions) per data-model.md; export from `backend/app/models/__init__.py`
- [x] T006 [P] Create parental controls Pydantic schemas in `backend/app/schemas/parental_controls.py` — `PinCreate` (new_pin, current_pin optional), `PinVerify` (pin), `PinReset` (password, new_pin), `PinError` (detail, remaining_attempts, locked_until), `ViewingTimeConfigResponse`, `ViewingTimeConfigUpdate` (weekday/weekend limits, reset_hour, educational_exempt, timezone), `GrantExtraTimeRequest` (minutes nullable enum [15,30,60,null], pin optional), `ViewingHistoryResponse` (days with sessions), `WeeklyReportResponse` per contracts/parental-controls-api.yaml
- [x] T007 [P] Create viewing time Pydantic schemas in `backend/app/schemas/viewing_time.py` — `ViewingTimeBalanceResponse` (profile_id, is_child_profile, has_limits, used_minutes, educational_minutes, limit_minutes, remaining_minutes, is_unlimited_override, next_reset_at, warning thresholds), `HeartbeatRequest` (profile_id, session_id optional, title_id, device_id, device_type, is_paused), `HeartbeatResponse` (session_id, enforcement enum [allowed/warning_15/warning_5/blocked], remaining_minutes, used_minutes, is_educational), `PlaybackEligibilityResponse`, `SessionEndResponse` per contracts/viewing-time-api.yaml
- [x] T008 [P] Create frontend API client in `frontend-client/src/services/viewingTimeApi.ts` — typed functions for all 11 endpoints: `createPin`, `verifyPin`, `resetPin`, `getViewingTimeConfig`, `updateViewingTimeConfig`, `grantExtraTime`, `getViewingHistory`, `getWeeklyReport`, `getBalance`, `sendHeartbeat`, `endSession`, `checkPlaybackEligibility`; use existing API client patterns from the codebase

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 — Parent Configures Daily Viewing Limits (Priority: P1) 🎯 MVP

**Goal**: Parents can set/update a 4-digit PIN, then configure weekday/weekend viewing time limits with reset hour for any child profile. New child profiles get sensible defaults (2h weekday, 3h weekend, 06:00 reset).

**Independent Test**: Create a child profile → navigate to Parental Controls → set PIN → configure limits → verify config persists via GET endpoint. Verify PIN lockout after 5 failed attempts. Verify PIN reset via account password. Use quickstart.md scenarios 1a–1c, 3a–3b, 4.

### Implementation for User Story 1

- [x] T009 [US1] Implement PIN service in `backend/app/services/pin_service.py` — `create_pin(user, new_pin, current_pin?)` creates bcrypt hash and stores in `user.pin_hash`; `verify_pin(user, pin)` checks bcrypt hash, increments `pin_failed_attempts` on failure, sets `pin_lockout_until = now + 30min` after 5 failures, resets attempts on success; `reset_pin(user, password, new_pin)` verifies account password then resets PIN and clears lockout; check lockout before any verification (return 403 with `locked_until` if locked)
- [x] T010 [US1] Add PIN verification dependency in `backend/app/dependencies.py` — `require_pin_verified` dependency that checks PIN was recently verified (via a short-lived claim or session flag); `require_account_owner` ensures the JWT user owns the requested profile
- [x] T011 [US1] Implement PIN endpoints in `backend/app/routers/parental_controls.py` — `POST /pin` (create/update), `POST /pin/verify` (verify with lockout), `POST /pin/reset` (reset via password) per contracts/parental-controls-api.yaml; all require JWT auth
- [x] T012 [US1] Implement viewing time config endpoints in `backend/app/routers/parental_controls.py` — `GET /profiles/{profile_id}/viewing-time` returns current config (create default config if none exists), `PUT /profiles/{profile_id}/viewing-time` validates 15-min increments, range 15–480 or null, reset_hour 0–23; require PIN verification; reject if profile is not `is_kids=true`; return 404 for adult profiles
- [x] T013 [US1] Implement default config creation in `backend/app/services/viewing_time_service.py` — `ensure_default_config(profile_id)` creates ViewingTimeConfig with weekday=120, weekend=180, reset_hour=6, educational_exempt=True, timezone="UTC" if no config exists; called on child profile creation and on first GET
- [x] T014 [P] [US1] Create ParentalControlsPage in `frontend-client/src/pages/ParentalControlsPage.tsx` — PIN entry gate (4-digit input with lockout countdown display, forgot PIN link to password reset flow); on PIN verified, show settings sections; include PIN setup flow for first-time users
- [x] T015 [P] [US1] Create viewing time settings components in `frontend-client/src/components/ParentalControls/ViewingTimeSettings.tsx` — list child profiles with current limits; per-profile editor: weekday/weekend dropdowns (15min to 8h in 15-min steps + Unlimited), reset hour dropdown (00:00–23:00), educational exemption toggle; save calls `updateViewingTimeConfig`; show adult profiles as "Unlimited (cannot be changed)"

**Checkpoint**: At this point, parents can manage PINs and configure viewing time limits for child profiles

---

## Phase 4: User Story 2 — Child Watches Content With Time Tracking (Priority: P1)

**Goal**: Server-side real-time viewing time tracking via 30-second heartbeats, cross-device balance sync (±1 min), single concurrent stream per child profile, pause detection (clock stops after 5 min idle), remaining time indicator with amber/red thresholds.

**Independent Test**: Start playback on child profile → verify balance decreases → pause >5 min → verify clock stopped → switch device → verify balance accurate. Use quickstart.md scenarios 2a–2c.

**Dependencies**: Can start in parallel with US1 (no overlap in backend files)

### Implementation for User Story 2

- [x] T016 [US2] Implement viewing time service core in `backend/app/services/viewing_time_service.py` — `get_viewing_day(now, reset_hour, timezone)` computes current viewing day per data-model.md; `get_balance(profile_id)` returns ViewingTimeBalance for current day (fresh if no row), computes remaining from config limits with weekday/weekend detection; `process_heartbeat(profile_id, title_id, device_id, device_type, session_id?, is_paused)` — on first heartbeat creates ViewingSession, on subsequent heartbeats increments `used_seconds` (30s) via UPSERT on `viewing_time_balances`, terminates any existing active session for same profile on different device (concurrent stream limit), skips incrementing if paused >5 min; returns enforcement status (allowed/warning_15/warning_5/blocked) based on remaining minutes
- [x] T017 [US2] Implement viewing time router endpoints in `backend/app/routers/viewing_time.py` — `GET /balance/{profile_id}` returns full balance response (returns unlimited for non-child profiles); `POST /heartbeat` processes heartbeat and returns enforcement + balance; `POST /session/{session_id}/end` marks session ended_at=now; `GET /playback-eligible/{profile_id}` pre-flight check (returns eligible=true for adults, checks balance for children; fail-closed: return eligible=false with reason if service error)
- [x] T018 [P] [US2] Create useViewingTime hook in `frontend-client/src/hooks/useViewingTime.ts` — `useViewingTime(profileId)` polls balance every 60s; `useHeartbeat(profileId, titleId, deviceId)` sends heartbeat every 30s during active playback, stops heartbeat on pause, tracks enforcement status from responses; exports `remainingMinutes`, `enforcement`, `isEducational`, `sessionId`; calls `checkPlaybackEligibility` before playback start
- [x] T019 [P] [US2] Create ViewingTimeIndicator in `frontend-client/src/components/ViewingTimeIndicator.tsx` — displays remaining time in profile menu (e.g., "1h 15m left today"); color changes: default → amber at ≤30 min → red at ≤15 min; shows "Unlimited" for adult profiles or unlimited-override days; hidden when no limits configured

**Checkpoint**: At this point, child viewing time is tracked in real-time across devices with balance indicator

---

## Phase 5: User Story 3 — Child Receives Warnings and Friendly Lock Screen (Priority: P1)

**Goal**: Non-intrusive toast warnings at 15 min and 5 min remaining during playback. Kid-friendly lock screen when time expires with cheerful message, offline activity suggestions, and parent override button. Child can browse but not start playback when locked.

**Independent Test**: Set 15-minute limit → watch content → verify 15m and 5m warnings appear → verify lock screen at 0 → verify browse works but playback is denied.

**Dependencies**: Depends on US2 (heartbeat enforcement signals drive warning/lock state)

### Implementation for User Story 3

- [x] T020 [P] [US3] Create ViewingTimeWarning component in `frontend-client/src/components/ViewingTimeWarning.tsx` — renders toast notification when `enforcement` changes to `warning_15` ("15 minutes of viewing time left today") or `warning_5` ("5 minutes left — ask a parent for more time"); dismissable; does not reappear for same threshold once dismissed; second warning is more prominent (larger, different color)
- [x] T021 [P] [US3] Create LockScreen component in `frontend-client/src/components/LockScreen.tsx` — full-screen overlay when `enforcement === "blocked"`; cheerful message ("Great watching today! Time for something else."); list of 3–4 suggested offline activities; "Need more time? Ask a parent" button (placeholder for US4 grant flow); displays next reset time ("Your time resets at 6:00 AM")
- [x] T022 [US3] Integrate warnings and lock screen into playback flow in `frontend-client/src/hooks/useViewingTime.ts` — expose `showWarning15`, `showWarning5`, `isLocked` state derived from heartbeat responses; trigger lock screen on `blocked` enforcement; block playback start when `isLocked` is true (redirect to lock screen); allow navigation/browsing when locked

**Checkpoint**: At this point, the full child viewing experience works: tracking → warnings → lock screen

---

## Phase 6: User Story 4 — Parent Grants Extra Time via PIN Override (Priority: P1)

**Goal**: Parent enters PIN on child's lock screen to grant +15/+30/+60 min or unlimited-for-today. Parent can also grant remotely from their own device without PIN re-entry. Child's device updates within 10s polling on lock screen. All grants are audited.

**Independent Test**: Let time expire → enter PIN on lock screen → grant +30 min → verify playback resumes. On separate device: grant time remotely → verify child's lock screen dismisses. Use quickstart.md scenario 5a–5b.

**Dependencies**: Depends on US1 (PIN service) and US3 (lock screen component)

### Implementation for User Story 4

- [x] T023 [US4] Implement grant extra time logic in `backend/app/services/viewing_time_service.py` — `grant_extra_time(profile_id, user_id, minutes, is_remote)` adds minutes to current balance (or sets `is_unlimited_override=true` for null/unlimited); creates `TimeGrant` audit record; if minutes is a number, add to remaining balance by reducing `used_seconds` or adding a grant offset; handle edge case where balance row doesn't exist yet
- [x] T024 [US4] Implement grant endpoint in `backend/app/routers/parental_controls.py` — `POST /profiles/{profile_id}/viewing-time/grant` accepts `{minutes: 15|30|60|null, pin?: string}`; if `pin` provided: verify PIN (on-device grant from lock screen); if no `pin`: require that current user is account owner (remote grant from parent's device); return updated remaining_minutes and granted_minutes
- [x] T025 [US4] Add PIN-based grant flow to LockScreen in `frontend-client/src/components/LockScreen.tsx` — "Need more time?" button opens PIN entry modal; on correct PIN, show quick-add presets: "+15 min", "+30 min", "+1 hour", "Unlimited for today"; on selection, call `grantExtraTime` API; on success, dismiss lock screen and resume playback; on PIN failure, show error with remaining attempts
- [x] T026 [US4] Add remote grant UI to parental controls in `frontend-client/src/components/ParentalControls/RemoteGrant.tsx` — under each child profile in the parental controls page, show "Grant Extra Time" button; same presets (+15/+30/+60/unlimited); no PIN needed (parent is already in their authenticated session); show confirmation with child's current balance after grant
- [x] T027 [US4] Implement accelerated polling on lock screen in `frontend-client/src/hooks/useViewingTime.ts` — when `isLocked` is true, increase balance poll frequency from 60s to 10s to catch remote grants faster; on balance update showing time available, auto-dismiss lock screen

**Checkpoint**: At this point, all P1 stories are complete — full enforcement loop with parent override

---

## Phase 7: User Story 5 — Educational Content Is Exempt From Limits (Priority: P2)

**Goal**: Educational content (tagged by provider) does not count toward daily limit. Tracked separately in balance. Per-profile toggle to disable exemption. "Educational" badge visible on content cards. Playback indicator confirms exemption.

**Independent Test**: Watch educational title → verify remaining time does NOT decrease → watch regular title → verify it DOES decrease → check balance shows educational_minutes separately. Use quickstart.md scenario 6.

**Dependencies**: Depends on US2 (heartbeat processing to modify)

### Implementation for User Story 5

- [x] T028 [US5] Add educational exemption logic to heartbeat processing in `backend/app/services/viewing_time_service.py` — in `process_heartbeat`: look up `title.is_educational`; if true AND profile config has `educational_exempt=true`, increment `educational_seconds` instead of `used_seconds` on the balance row; set `is_educational=true` on ViewingSession; return `is_educational: true` in heartbeat response so client can show indicator; if educational lookup fails (title not found), treat as regular per fail-closed policy
- [x] T029 [US5] Ensure educational toggle is exposed in config endpoints in `backend/app/routers/parental_controls.py` — verify `educational_exempt` field is included in GET/PUT for viewing time config (should already be in schema from T006/T012; add handling if missing)
- [x] T030 [P] [US5] Add "Educational" badge to content cards in `frontend-client/src/components/` — in browse/search result cards, show a small "Educational" badge when `title.is_educational === true`; visible in content detail screen as well
- [x] T031 [P] [US5] Add educational exemption indicator during playback in `frontend-client/src/components/ViewingTimeWarning.tsx` — when heartbeat response includes `is_educational: true`, show brief non-intrusive indicator "This doesn't count toward your daily limit" that auto-dismisses after 5 seconds; show only once per playback session

**Checkpoint**: At this point, educational content exemption is fully functional

---

## Phase 8: User Story 7 — Viewing History and Weekly Reports (Priority: P2)

**Goal**: Parents see chronological viewing history grouped by day with title, duration, device, and educational flag per session. Daily totals with educational breakdown. Weekly summary report with averages and most-watched. At least 30 days of history.

**Independent Test**: Have child watch content over several sessions → access history → verify entries, daily totals, and educational breakdown. Request weekly report → verify daily totals, averages, most-watched content. Use quickstart.md scenarios 7–8.

**Dependencies**: Depends on US2 (ViewingSession data exists from heartbeat processing)

> **Note**: US6 (Offline Enforcement) is **deferred** to post-PoC per research.md R6. The PoC frontend is web-only with no download capability.

### Implementation for User Story 7

- [x] T032 [US7] Implement viewing history query in `backend/app/services/viewing_time_service.py` — `get_viewing_history(profile_id, from_date, to_date)` queries ViewingSessions joined with Titles, groups by day, computes daily totals (counted vs educational minutes), returns sorted descending by date; default from_date = 30 days ago; filter by profile ownership
- [x] T033 [US7] Implement weekly report aggregation in `backend/app/services/viewing_time_service.py` — `get_weekly_report(user_id)` aggregates last 7 days of sessions across all child profiles; per profile: daily totals (counted + educational), average daily minutes, limit usage percentage, most-watched titles (top 3 by total minutes); returns structured report per WeeklyReport schema
- [x] T034 [US7] Implement history and report endpoints in `backend/app/routers/parental_controls.py` — `GET /profiles/{profile_id}/history?from_date&to_date` returns viewing history; `GET /weekly-report` returns weekly report for all child profiles; both require PIN verification
- [x] T035 [P] [US7] Create viewing history UI in `frontend-client/src/components/ParentalControls/ViewingHistory.tsx` — day-grouped list with expand/collapse; each day shows total ("Tuesday Feb 11 — 1h 45m total | 30m educational"); each session row: title, time range, duration, device icon, educational badge; date range filter; load within 2 seconds
- [x] T036 [P] [US7] Create weekly report UI in `frontend-client/src/components/ParentalControls/WeeklyReport.tsx` — per-child profile card with: bar chart of daily totals (counted vs educational), average daily viewing, limit usage %, top 3 most-watched titles; multi-child summary if multiple profiles

**Checkpoint**: At this point, parents have full visibility into viewing patterns and trends

---

## Phase 9: User Story 8 — Unified Parental Controls Experience (Priority: P2)

**Goal**: Viewing time settings, history, and reports are integrated into the existing Parental Controls screen alongside content ratings. Consistent visual design. Changes propagate within 5 seconds.

**Independent Test**: Access Parental Controls → verify sections for Content Ratings, Viewing Time Limits, and Profile Management are all visible → edit a child's viewing time → verify changes propagate to active sessions.

**Dependencies**: Depends on US1 (settings), US7 (history/reports integration)

### Implementation for User Story 8

- [x] T037 [US8] Integrate viewing time into existing parental controls layout in `frontend-client/src/pages/ParentalControlsPage.tsx` — add "Viewing Time Limits" section between Content Ratings and Profile Management; list each child profile with summary (weekday limit / weekend limit / reset time); link to full editor (ViewingTimeSettings from T015); link to history (ViewingHistory from T035); visually consistent with existing parental rating enforcement UI
- [x] T038 [US8] Add per-child profile summary cards in `frontend-client/src/components/ParentalControls/ProfileSummaryCard.tsx` — compact card per child: avatar, name, today's usage bar (used/limit), current status (watching/idle/locked), quick links to "Edit Limits", "View History", "Grant Time"; show "No limits set" for profiles without config

**Checkpoint**: All user stories are independently functional with a unified settings experience

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Seed data, demo validation, and integration refinements

- [x] T039 [P] Create seed data for demo scenarios in `backend/seed/seed_viewing_time.py` — create a sample child profile with pre-configured limits (weekday=120, weekend=180, reset=6); set `is_educational=true` on 5–10 titles (documentaries, kids learning content); create pre-populated viewing history (7 days of sessions with varied titles, devices, educational mix); create a TimeGrant record; set account PIN for demo user
- [x] T040 [P] Add frontend routing for ParentalControlsPage in `frontend-client/src/` — add route `/parental-controls` pointing to ParentalControlsPage; add navigation link in profile/settings menu; ensure route is protected (requires authenticated adult profile)
- [x] T041 Run quickstart.md verification scenarios end-to-end — execute all 8 scenarios from `specs/006-viewing-time-limits/quickstart.md` against running stack; verify expected responses match; fix any discrepancies
- [x] T042 Verify profile deletion cascade for viewing time data in `backend/app/models/viewing_time.py` — confirm all FK relationships to `profiles.id` use `CASCADE` on delete so that viewing_time_configs, viewing_time_balances, viewing_sessions, and time_grants are automatically purged when a child profile is deleted; verify with a test deletion in seed data; satisfies FR-023 (GDPR/COPPA data deletion)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - US1 and US2 can proceed **in parallel** (no overlapping files)
  - US3 depends on US2 (heartbeat enforcement signals)
  - US4 depends on US1 + US3 (PIN service + lock screen)
  - US5 depends on US2 (modifies heartbeat processing)
  - US7 depends on US2 (queries ViewingSession data)
  - US8 depends on US1 + US7 (integrates settings and history)
- **Polish (Phase 10)**: Depends on all desired user stories being complete

### User Story Dependencies

```
Foundational ──┬──→ US1 (Configure Limits) ──────────────────┐
               │                                              │
               ├──→ US2 (Time Tracking) ──┬──→ US3 (Warnings) ┤
               │                          │                    ├──→ US4 (Extra Time Grant)
               │                          ├──→ US5 (Educational)
               │                          │
               │                          └──→ US7 (History) ──┤
               │                                               │
               └───────────────────────────────────────────────┴──→ US8 (Unified Settings)
```

### Deferred

- **US6 (Offline Enforcement)**: Deferred to post-PoC per research.md R6 — web-only frontend has no download/offline capability

### Within Each User Story

- Models before services (already in Foundational)
- Services before endpoints
- Backend before frontend (data must exist before UI consumes it)
- Core implementation before integration refinements

### Parallel Opportunities

- All Foundational tasks (T003–T008) can run in parallel
- US1 and US2 can run fully in parallel after Foundational
- Frontend tasks within a story marked [P] can run in parallel with each other
- After US1+US2 complete: US3, US5, and US7 can start in parallel

---

## Parallel Example: After Foundational Complete

```
# Wave 1 — US1 and US2 in parallel:
Team A: T009 → T010 → T011 → T012 → T013 + T014∥T015   (US1: Configure Limits)
Team B: T016 → T017 + T018∥T019                          (US2: Time Tracking)

# Wave 2 — US3, US5, US7 can start in parallel:
Team A: T020∥T021 → T022                                  (US3: Warnings & Lock Screen)
Team B: T028 → T029 + T030∥T031                           (US5: Educational Exemption)
Team C: T032 → T033 → T034 + T035∥T036                   (US7: History & Reports)

# Wave 3 — US4 (needs US1+US3), US8 (needs US1+US7):
Team A: T023 → T024 → T025∥T026 → T027                   (US4: Extra Time Grant)
Team B: T037 → T038                                       (US8: Unified Settings)
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 (configure limits)
4. Complete Phase 4: User Story 2 (time tracking)
5. **STOP and VALIDATE**: Both stories independently testable via quickstart.md

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 + US2 → Core enforcement works → Demo: set limits, track time, see balance (MVP!)
3. US3 → Warnings + lock screen → Demo: full child experience
4. US4 → Parent override → Demo: complete enforcement loop with escape hatch
5. US5 → Educational exemption → Demo: educational content doesn't count
6. US7 → History + reports → Demo: parent visibility into viewing patterns
7. US8 → Unified settings → Demo: polished, integrated experience
8. Polish → Seed data + verification → Demo-ready

### Single Developer Strategy

Follow phases sequentially: Setup → Foundational → US1 → US2 → US3 → US4 → US5 → US7 → US8 → Polish

Each story adds value and is independently testable before proceeding to the next.

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- No test tasks included — verification via quickstart.md manual scenarios per PoC constraints
- US6 (Offline) deferred — document design only, no implementation tasks
- Commit after each story completion for clean git history
- Stop at any checkpoint to validate story independently
- All backend endpoints use `/api/v1/` prefix per existing router patterns in main.py
