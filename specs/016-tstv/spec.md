# Feature Specification: Time-Shifted TV (TSTV) — Start Over & Catch-Up

**Feature Branch**: `016-tstv`
**Created**: 2026-02-24
**Status**: Draft
**PRD Reference**: PRD-002-tstv.md
**User Stories Reference**: docs/user-stories/US-tstv.md (33 stories across 7 epics)

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Start Over a Currently Airing Program (Priority: P1)

A viewer tunes into a channel and finds a program that started 20+ minutes ago. The platform detects the late tune-in and displays a prompt: "This program started 23 minutes ago — Start from the beginning?" The viewer accepts and the program restarts immediately from the first frame, with full playback controls available. A visible indicator shows the viewer's position relative to the live broadcast edge.

**Why this priority**: This is the primary differentiating TSTV capability. It directly addresses the #1 frustration with live TV ("I missed the beginning") and has the clearest, most measurable success condition. Without Start Over, there is no TSTV feature to demonstrate.

**Independent Test**: Can be fully tested by tuning to a channel mid-program, observing the Start Over prompt, accepting it, and confirming playback begins at the program's start — all without any other TSTV features in place.

**Acceptance Scenarios**:

1. **Given** a viewer tunes to a live channel where the current program started more than 3 minutes ago, **When** the channel loads, **Then** a Start Over prompt appears within 2 seconds showing the program title and time elapsed
2. **Given** the Start Over prompt is displayed, **When** the viewer selects "Start from Beginning," **Then** playback transitions to the program's start within 3 seconds with no interruption or re-authentication
3. **Given** a program without start-over rights, **When** a viewer tunes in late, **Then** no Start Over prompt is shown
4. **Given** the Start Over prompt, **When** 10 seconds pass without action, **Then** the prompt auto-dismisses and the live stream continues uninterrupted
5. **Given** Start Over is active, **When** the viewer uses playback controls, **Then** full trick-play (pause, fast-forward up to the live edge, rewind to program start, scrubbing) works correctly *(thumbnail previews deferred to Phase 2)*

---

### User Story 2 — Return to Live from Start Over (Priority: P1)

While watching in Start Over mode, a viewer wants to jump back to the current live broadcast — for example, after catching up through the first half of a match, they want to rejoin the live broadcast for the second half in real-time.

**Why this priority**: Completing the live → start-over → live journey is essential to make Start Over feel seamless rather than a dead-end detour. It is part of the same core session as Story 1 and significantly reduces viewer anxiety about "missing live."

**Independent Test**: Can be tested by starting a Start Over session and pressing "Jump to Live," confirming playback immediately switches to the live edge.

**Acceptance Scenarios**:

1. **Given** the viewer is watching in Start Over mode, **When** "Jump to Live" is pressed, **Then** playback returns to the current live broadcast position within 1 second
2. **Given** the "Jump to Live" button, **When** rendered in Start Over mode, **Then** it is prominently visible in the player controls (not hidden in a menu)
3. **Given** the viewer returns to live, **When** the player badge updates, **Then** the "START OVER" badge transitions to "LIVE" with no visual glitch

---

### User Story 3 — Browse and Play Catch-Up Programs (Priority: P2)

A viewer missed a documentary that aired on Tuesday evening. On Saturday they open the catch-up section, browse to Channel 12, find Tuesday's schedule, and start watching the program. They get full playback controls — just like watching a recorded video.

**Why this priority**: Catch-Up TV is the second core TSTV capability. Together with Start Over, it delivers the complete "break free from the schedule" value proposition. Without catch-up, the feature only covers the narrow window of being late to a currently airing program.

**Independent Test**: Can be fully tested by navigating to the catch-up section, selecting a channel and date, choosing a program, and confirming playback starts with full trick-play — independently of Start Over.

**Acceptance Scenarios**:

1. **Given** a viewer navigates to the catch-up section and selects a channel, **When** the listing loads, **Then** all available catch-up programs from the past 7 days are displayed organized by date (most recent first), each showing title, air time, duration, expiry date, and a play button
2. **Given** a catch-up program listing, **When** the viewer selects play, **Then** the program starts within 2 seconds with full trick-play capability (pause, fast-forward, rewind, scrubbing) *(thumbnail previews deferred to Phase 2)*
3. **Given** a program without catch-up rights, **When** displayed in the schedule, **Then** it shows a lock icon and "Not available on Catch-Up" — no play button
4. **Given** a program whose catch-up window has expired, **When** a viewer attempts to access it directly, **Then** a clear "no longer available" message is shown with a link to the VOD version if one exists

---

### User Story 4 — Continue Watching Across Devices (Priority: P3)

A viewer starts a catch-up program on their TV, watches 30 minutes, then pauses. The next day they open the app on their phone and see the program in "Continue Watching" with a progress indicator. They resume exactly where they left off.

**Why this priority**: Cross-device resume is table-stakes for a modern streaming service. It significantly increases the perceived quality of the catch-up experience and reduces re-watch frustration. It builds on Stories 1–3 and requires a functional bookmarking system.

**Independent Test**: Can be tested by watching a catch-up program on one device, stopping, switching to a different device, and confirming the resume position appears in the Continue Watching rail within 5 seconds.

**Acceptance Scenarios**:

1. **Given** a viewer pauses a catch-up program, **When** they switch to another device and open the app, **Then** the program appears in "Continue Watching" with the correct resume position synced within 5 seconds
2. **Given** a catch-up item in the "Continue Watching" rail, **When** displayed, **Then** it shows a thumbnail, title, channel name, progress bar, time remaining, and catch-up expiry date
3. **Given** an item expiring within 24 hours, **When** shown in Continue Watching, **Then** it is visually highlighted with an expiry urgency indicator (e.g., "Expires today" badge)

---

### User Story 5 — Per-Channel TSTV Rules Management (Priority: P4)

An operator needs to configure which channels offer Start Over and Catch-Up, and how long the catch-up window is. A sports channel may only allow 2-hour catch-up; an entertainment channel offers 7 days. These settings must be changeable from the admin panel without a deployment.

**Why this priority**: Rights configurations are required before any TSTV content can be served correctly. However, since a default configuration can be pre-set for PoC channels, this can be built slightly after core playback flows are validated.

**Independent Test**: Can be tested by opening the admin panel, changing a channel's TSTV settings, and confirming the channel's catch-up and start-over behavior changes immediately on the next viewer request.

**Acceptance Scenarios**:

1. **Given** the admin panel, **When** the TSTV Rules section is opened, **Then** a table shows all channels with editable columns: TSTV enabled, start-over enabled, catch-up enabled, and catch-up window duration
2. **Given** a channel is configured with catch-up disabled, **When** a viewer browses catch-up, **Then** no catch-up programs are available for that channel
3. **Given** the catch-up window is changed, **When** the change is saved, **Then** it takes effect on the next viewer request without restarting any services
4. **Given** the window duration dropdown, **When** setting options are shown, **Then** available choices are: 2h, 6h, 12h, 24h, 48h, 72h, 168h

---

### User Story 6 — Catch-Up Expiry Notifications (Priority: P5)

A viewer started watching a drama series episode on catch-up and left it at 40% through. The episode expires in 22 hours. They receive a notification: "Episode 1 of The Bridge expires tomorrow — continue watching or record to keep it."

**Why this priority**: Expiry notifications protect against viewer disappointment and create a natural PVR upsell moment, but they depend on the notification infrastructure and bookmarking system being in place first.

**Independent Test**: Can be tested by creating a bookmark on a catch-up program, setting the expiry to 24 hours from now, and confirming a notification is triggered with the correct expiry message.

**Acceptance Scenarios**:

1. **Given** a viewer has started a catch-up program, **When** the program is within 24 hours of expiry, **Then** a notification is sent with the expiry time and options to watch now or record to PVR
2. **Given** catch-up content in any listing view, **When** displayed, **Then** the expiry date is visible on every program item

---

### Edge Cases

- What happens when a program overruns its scheduled end time (e.g., a live sports event runs 20 minutes over)? Segment capture must handle schedule drift — the start-over and catch-up archive captures actual broadcast content, not just the scheduled window.
- What happens when a channel's streaming process crashes mid-program? Segments written before the crash are still available for catch-up up to the last recorded point; the player must play what is available rather than showing an error for the whole program.
- What happens when a viewer fast-forwards within 30 seconds of the live edge during Start Over? Fast-forward slows and stops at the live edge; the player transitions to live mode automatically.
- What happens when two devices send concurrent bookmark updates for the same program? The furthest (highest) position is stored; an earlier position from a second device never overwrites a further position already recorded.
- What happens when catch-up rights are revoked while a viewer is actively watching the program? The current session is allowed to complete; new play requests after revocation are denied.
- What happens when no catch-up programs are eligible for a given channel on a given day? An empty state is shown with a clear "No catch-up available" message — not an error.
- What happens when a viewer searches for catch-up content using a term that matches both catch-up and VOD titles? Results are shown in a combined list with clear labels distinguishing catch-up (with expiry) from VOD. *(Deferred — catch-up search is out of scope for Phase 1; see Out of Scope.)*

---

## Requirements *(mandatory)*

### Functional Requirements

**Start Over TV**

- **FR-001**: When a viewer tunes to a live channel where the current program started more than 3 minutes ago, the platform MUST display a Start Over prompt within 2 seconds of channel load
- **FR-002**: The Start Over prompt MUST display the program title, elapsed time since start, and two actions: "Start from Beginning" and "Continue Live"
- **FR-003**: The prompt MUST auto-dismiss after 10 seconds without user action and MUST NOT reappear for the same program during the same session
- **FR-004**: When the viewer selects "Start from Beginning," playback MUST begin at the program's first frame within 3 seconds, without re-authentication or session interruption
- **FR-005**: During Start Over playback, the viewer MUST have full trick-play: pause, rewind (multiple speeds), fast-forward up to but not past the live edge (multiple speeds), and scrubbing. *(Thumbnail previews during scrubbing are deferred to Phase 2 — requires I-frame playlist or BIF sprite generation in the FFmpeg pipeline.)*
- **FR-006**: A "Jump to Live" button MUST be prominently displayed throughout Start Over; pressing it MUST return playback to the current live position within 1 second
- **FR-007**: The player MUST indicate Start Over mode with a visible badge and show the viewer's position relative to the live edge via a scrubber bar
- **FR-008**: Start Over MUST only be offered for programs that have start-over rights enabled; programs without rights MUST silently omit the prompt

**Catch-Up TV**

- **FR-010**: Previously aired programs on catch-up-enabled channels MUST become available in the catch-up catalog within 5 minutes of actual broadcast end (accounting for schedule overrun, not just the scheduled end time)
- **FR-011**: The catch-up catalog MUST support browsing by channel: programs sorted by date (most recent first), each showing title, air time, duration, expiry date, and play/resume action
- **FR-012**: The catch-up catalog MUST support browsing by date: all available programs across channels for a selected day (up to 7 days back), filterable by genre and channel. Served by `GET /api/v1/tstv/catchup?date=YYYY-MM-DD&genre=&channel_id=`
- **FR-013**: Catch-up playback MUST start within 2 seconds and provide full trick-play identical to VOD (pause, rewind, fast-forward, scrubbing). *(Thumbnail previews during scrubbing are deferred to Phase 2 — same dependency as FR-005.)*
- **FR-014**: Programs MUST be automatically removed from the catch-up catalog within 5 minutes of their window expiring; expired programs show a "no longer available" state

**Bookmarking & Continue Watching**

- **FR-020**: The platform MUST automatically save viewing position during Start Over and catch-up playback at least every 30 seconds and on stop/pause events
- **FR-021**: When a viewer returns to a partially watched catch-up program, playback MUST auto-resume from the saved position immediately; a brief dismissable toast ("Resuming from 30:12") MUST appear for 3 seconds with a "Start from beginning" link for viewers who want to restart
- **FR-022**: Bookmarks MUST sync across all of a viewer's devices within 5 seconds; resume position accuracy MUST be within 5 seconds of the actual stop point; when concurrent updates arrive for the same profile + program, the furthest (highest) position MUST be kept
- **FR-023**: Partially watched catch-up programs MUST appear in the "Continue Watching" rail on the home screen, showing progress bar, remaining time, and expiry date; items expiring within 24 hours MUST be visually highlighted

**Content Rights**

- **FR-030**: Each channel MUST support configurable TSTV settings: start-over enabled flag, catch-up enabled flag, and catch-up window duration (options: 2h, 6h, 12h, 24h, 48h, 72h, 168h)
- **FR-031**: Individual programs MUST be able to override the channel-level catch-up and start-over eligibility
- **FR-032**: Rights MUST be enforced at both the catalog display level (lock icon for ineligible content) and the playback level (access denied for unauthorized requests)
- **FR-033**: If a program's catch-up rights are revoked mid-window, it MUST be removed from browse and search within 15 minutes; active playback sessions MUST be allowed to complete

**Expiry Notifications**

- **FR-040**: Viewers who have started a catch-up program MUST receive a notification 24 hours before it expires, including options to watch now or record to PVR
- **FR-041**: Catch-up expiry dates MUST be visible on all program listings across all browse, search, and Continue Watching surfaces

**Admin Controls**

- **FR-050**: Operators MUST be able to start, stop, and restart simulated live channel processes per channel from the admin panel without terminal access
- **FR-051**: The admin panel MUST display per-channel streaming status (running/stopped), disk usage, and segment count
- **FR-052**: Operators MUST be able to update per-channel TSTV rules (enabled flags and window duration) from the admin panel; changes MUST take effect immediately without service restarts

### Key Entities

- **Channel**: A live broadcast source with TSTV configuration — start-over enabled, catch-up enabled, viewer-facing catch-up window duration (`cutv_window_hours` — controls what viewers can access), and infrastructure retention window (`catchup_window_hours` — controls how long segments are kept on disk; always ≥ `cutv_window_hours`)
- **Schedule Entry (Program)**: A specific broadcast on a channel at a defined time — carries per-program start-over and catch-up eligibility flags that override channel defaults; carries series link for episode grouping
- **Catch-Up Asset**: A stored, playable version of a previously aired program — tied to its schedule entry, available for the configured window, auto-expires
- **TSTV Session**: A record of a viewer watching in start-over or catch-up mode — tracks session type (start-over/catch-up), viewing position, and completion status
- **Bookmark**: A saved viewing position for a specific viewer profile on a specific program instance — synced across devices, expires with the associated content
- **Viewer Profile**: The profile-level identity used for bookmarks, entitlements, and personalization — distinct from the account/user entity

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Start Over transition completes in under 3 seconds for 95% of viewers (from "Start from Beginning" tap to first frame playing)
- **SC-002**: Catch-up programs become playable within 5 minutes of broadcast end for 95% of programs
- **SC-003**: Expired programs are removed from the catch-up catalog within 5 minutes of expiry time
- **SC-004**: At least 30% of viewers who tune in more than 3 minutes late to an eligible program choose Start Over
- **SC-005**: Cross-device resume position is accurate to within 5 seconds and the bookmark syncs to the second device within 5 seconds for 90% of resume events
- **SC-006**: Catch-up browsing (by channel or by date) loads within 2 seconds
- **SC-008**: Per-channel TSTV rule changes in the admin panel take effect within one page reload with no service restart
- **SC-009**: Zero unauthorized playback events — content without TSTV rights must not be playable via Start Over or Catch-Up under any circumstances
- **SC-010**: Catch-up viewing accounts for at least 20% of total live+TSTV viewing hours within 30 days of launch

---

## Clarifications

### Session 2026-02-24

- Q: How are schedule entries (program start/end times) created and maintained in the PoC environment? → A: Static schedule entries manually seeded in the DB — programs repeat on a fixed loop aligned to FFmpeg's video loop duration
- Q: What is the actual current implementation state of the bookmark/watch-position service? → A: Stub only — endpoints exist and return 200 but nothing is persisted or returned from the DB
- Q: When a viewer selects a partially-watched catch-up program, what is the exact resume interaction? → A: Auto-resume — playback starts immediately from the saved position; a brief dismissable toast shows "Resuming from 30:12" with a "Start from beginning" link
- Q: Should catch-up content search (FR-015) be included in this feature or deferred? → A: Defer — catch-up search is a separate follow-on feature (must be implemented after the catch-up catalog is built)
- Q: When two devices write conflicting bookmark positions for the same viewer profile + program, which wins? → A: Furthest position wins — the higher playback position is always kept, regardless of write order

---

## Assumptions

- The PoC environment already has channels streaming via simulated live (FFmpeg writing HLS segments to a shared volume); TSTV builds on top of the existing segment archive — no new ingest infrastructure required
- Schedule entries are statically seeded in the database with program start/end times aligned to the FFmpeg video loop duration for each channel; programs repeat on a fixed loop and schedule entries repeat accordingly. No external EPG integration is required for the PoC.
- A default TSTV configuration is seeded per PoC channel; the admin panel allows runtime adjustments but the initial state is set via database seed data
- The Bookmark Service has stub endpoints that return 200 but do not persist to or read from the DB. This feature must implement the full bookmark persistence logic (DB writes, reads, cross-device sync) as part of the P3 story — it is not a pure integration task.
- The viewer-facing catch-up window (entitlement) and the infrastructure retention window (storage) are configured independently; infrastructure always retains segments for the maximum possible window
- Rights are managed at the channel level for the PoC; per-program overrides are supported in the data model but only a subset of channels will use them at launch
- Push notifications for expiry alerts require a notification service to be in place; in-app notifications are the minimum viable delivery mechanism if push is not yet available
- DRM/encryption for segments is already handled by the existing SimLive setup; TSTV manifests reuse the same encryption — no additional DRM work required for the PoC
- Search for catch-up content is explicitly deferred to a follow-on feature; no search infrastructure dependency exists for this feature

---

## Constitution Deviation: AI-Native by Default (§III)

Constitution §III mandates "Every feature should include its AI-enhanced variant, even in the PoC." This feature intentionally defers all AI variants to Phase 2 for the following reasons:

1. **Infrastructure-first**: TSTV is a streaming infrastructure feature (FFmpeg, HLS manifests, DRM, segment storage). The AI variants (personalized catch-up recommendations, smart notifications, AI summaries) are presentation-layer enhancements that require a functioning catch-up catalog to operate on.
2. **No corpus yet**: AI recommendations need a catch-up viewing history corpus that doesn't exist until TSTV is live. Building AI features before the data pipeline exists would produce dummy results with no demo value.
3. **Clear Phase 2 path**: All 6 AI variants are documented in Out of Scope with explicit phase assignments. They will be implemented as a follow-on feature once TSTV generates real viewing data.

**Accepted deviation**: No AI component in Phase 1. Revisit after TSTV launch when viewing data exists.

---

## Out of Scope

- AI-powered personalized catch-up recommendations ("Your Catch-Up" rail) — Phase 2
- "You Missed This" smart notifications — Phase 2
- AI-generated program summaries — Phase 2
- Predictive CDN cache warming — Phase 2
- Viewing pattern prediction model — Phase 2
- AI auto-bookmarking at chapter breaks — Phase 3
- Cloud PVR recording pipeline — PRD-003 (separate feature)
- Advertising marker insertion in catch-up manifests — Phase 2
- Catch-Up for FAST channels — separate scope
- Extended catch-up windows beyond 7 days
- Downloading catch-up content for offline playback — Phase 3+
- Territory-based rights enforcement — single territory for PoC; territory logic is in the data model but not enforced at runtime in Phase 1
- **Catch-up content search** — deferred to a follow-on feature; must be built after the catch-up catalog is complete so there is a corpus to search. Implement after this feature ships.
- **Thumbnail previews during scrubbing** — requires I-frame playlist (`#EXT-X-I-FRAMES-ONLY`) or BIF sprite sheet generation in the FFmpeg pipeline. Deferred to Phase 2; scrubbing works without thumbnails (time-based position only).
