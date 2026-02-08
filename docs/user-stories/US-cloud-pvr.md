# User Stories: Cloud PVR (PRD-003)

**Source PRD:** PRD-003-cloud-pvr.md
**Generated:** 2026-02-08
**Total Stories:** 30

---

## Epic 1: Recording Scheduling

### US-PVR-001: Schedule Single Program Recording from EPG

**As a** viewer
**I want to** schedule a recording of a specific program from the EPG or program detail screen
**So that** I can watch the program later at my convenience

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** PVR-FR-001

**Acceptance Criteria:**
- [ ] Given a viewer presses "Record" on an eligible EPG listing, when the scheduling completes, then confirmation appears within 2 seconds showing: title, channel, time, estimated storage usage
- [ ] Given the recording is scheduled, when the EPG listing is viewed, then a recording icon is displayed on the program
- [ ] Given the recording is scheduled, when it appears in "Scheduled Recordings," then it shows title, channel, date/time, and estimated duration
- [ ] Performance: Recording scheduled in < 2 seconds from user action to confirmation

**AI Component:** No

**Dependencies:** EPG Service (PRD-005) for program metadata, Recording Service, Rights Engine

**Technical Notes:**
- Recording captures from scheduled start to scheduled end per EPG metadata
- Padding is applied per PVR-FR-004 settings

---

### US-PVR-002: Schedule Series Recording (Series Link)

**As a** binge watcher
**I want to** set up a series link that automatically records all future episodes of a series
**So that** I never miss an episode of a series I follow

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** PVR-FR-002

**Acceptance Criteria:**
- [ ] Given a viewer selects "Record Series" on a program, when the series link dialog appears, then options include: "New episodes only," "All episodes (including repeats)," "New + repeats on this channel only"
- [ ] Given a series link is created, when new EPG data arrives (typically 7 days ahead), then future episodes matching the series ID are automatically scheduled within 5 minutes
- [ ] Given the series link, when viewing "Scheduled Recordings," then it shows the series name with upcoming episodes listed
- [ ] Given recordings from a series, when viewing the library, then episodes are grouped under the series name with correct episode ordering
- [ ] Performance: Series link creation completes in < 2 seconds

**AI Component:** No

**Dependencies:** EPG Service (series ID metadata), Recording Service

**Technical Notes:**
- Series matching based on series ID from EPG metadata
- Episode numbering and ordering from EPG season/episode fields

---

### US-PVR-003: Record from Live Viewing

**As a** sports fan
**I want to** start recording a live program I am currently watching
**So that** I can capture the rest (or the entire program from the beginning) when I need to leave

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** PVR-FR-003

**Acceptance Criteria:**
- [ ] Given a viewer presses "Record" during live viewing, when the recording options appear, then they include: "Record from now," "Record from beginning" (if start-over buffer available), and "Record series"
- [ ] Given "Record from now," when initiated, then recording starts capturing within 2 seconds from the current live position
- [ ] Given "Record from beginning," when initiated, then the recording includes content from program start (sourced from start-over buffer) plus the live remainder
- [ ] Given the live viewing bookmark, when the recording completes, then the bookmark transfers to the recording (e.g., "Continue from 45:00")
- [ ] Given recording is active, when the player overlay shows, then a recording indicator icon is visible

**AI Component:** No

**Dependencies:** Live TV Service (PRD-001), TSTV start-over buffer (PRD-002), Recording Service

**Technical Notes:**
- "Record from beginning" sources segments from EFS start-over buffer or S3 catch-up storage
- No playback interruption during recording initiation

---

### US-PVR-004: Recording Padding Configuration

**As a** viewer
**I want to** configure start-early and end-late padding for my recordings
**So that** I capture the complete program even when schedules run over

**Priority:** P0
**Phase:** 1
**Story Points:** S
**PRD Reference:** PVR-FR-004

**Acceptance Criteria:**
- [ ] Given recording padding options, when configuring, then available settings are: start 0/1/5 min early; end 0/5/15/30 min late
- [ ] Given padding is configured, when a recording captures, then the actual capture includes the padding time
- [ ] Given padding time, when quota is calculated, then padding time counts against the user's quota
- [ ] Given per-recording override, when set, then it takes precedence over the global default

**AI Component:** No

**Dependencies:** Recording Service, EPG Service

**Technical Notes:**
- Default: 0 min early, 5 min late
- Global default configurable in settings; per-recording override on scheduling dialog

---

### US-PVR-005: Cancel Scheduled Recording

**As a** viewer
**I want to** cancel a scheduled single recording or an entire series link
**So that** I can manage my recording schedule and free up quota for other programs

**Priority:** P0
**Phase:** 1
**Story Points:** S
**PRD Reference:** PVR-FR-005

**Acceptance Criteria:**
- [ ] Given a viewer cancels a single scheduled recording, when cancelled, then it is removed from the schedule immediately
- [ ] Given a viewer cancels a series link, when cancelled, then all future scheduled recordings for that series are removed; already-completed recordings remain in the library
- [ ] Given a recording was already captured, when the series link is cancelled, then existing recordings are not deleted

**AI Component:** No

**Dependencies:** Recording Service

**Technical Notes:**
- Cancellation is immediate; no async delay
- Series link cancellation preserves historical recordings

---

### US-PVR-006: Recording Eligibility Enforcement

**As an** operator
**I want to** ensure recording buttons only appear for PVR-enabled channels and programs
**So that** content rights agreements are respected

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** PVR-FR-007, PVR-FR-030, PVR-FR-031

**Acceptance Criteria:**
- [ ] Given a channel with `recording_enabled = false`, when displayed in EPG or program detail, then no "Record" button is shown
- [ ] Given a specific program with recording restrictions, when displayed, then "Recording not available for this program" message is shown instead of a Record button
- [ ] Given rights data, when checked, then eligibility is resolved in < 50ms (Redis cache)

**AI Component:** No

**Dependencies:** Rights Engine (Redis-cached), EPG Service

**Technical Notes:**
- Channel-level defaults with program-level overrides
- Fail-closed: if rights status is ambiguous, recording button is hidden

---

## Epic 2: Recording Storage and Management

### US-PVR-007: Storage Quota Display and Tracking

**As a** viewer
**I want to** see my current PVR storage usage and remaining capacity in real-time
**So that** I can manage my recordings and know when I need to free up space

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** PVR-FR-010

**Acceptance Criteria:**
- [ ] Given a viewer opens the PVR library, when the screen loads, then current usage is displayed as "X / Y hours used" (e.g., "62/100 hours")
- [ ] Given a viewer schedules a recording, when the confirmation dialog shows, then it includes quota impact (e.g., "Storage: ~2.5 hours. Current usage: 62/100 hours")
- [ ] Given quota tiers (50, 100, 200, unlimited), when the user's tier is displayed, then the correct tier is shown
- [ ] Performance: Quota accuracy within 1 minute of real-time; quota displayed on library screen, scheduling confirmation, and account settings

**AI Component:** No

**Dependencies:** Recording Service (quota tracking), Redis cache

**Technical Notes:**
- Quota tracked in hours (user-friendly) not bytes
- Redis cache key: `pvr:quota:{user_id}`, refreshed on schedule/delete events

---

### US-PVR-008: Quota Enforcement with Upgrade Prompt

**As a** viewer
**I want to** be warned when a recording would exceed my quota and offered options to free space or upgrade
**So that** I can take action before a recording fails

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** PVR-FR-011

**Acceptance Criteria:**
- [ ] Given a new recording would exceed the user's quota, when scheduling is attempted, then a warning is shown BEFORE the recording is scheduled
- [ ] Given the warning, when displayed, then it clearly shows: required space, available space, and the shortfall
- [ ] Given the warning, when options are presented, then the user can: "Delete recordings to free space" (opens AI Cleanup) or "Upgrade quota" (links to subscription management)
- [ ] Given the user frees sufficient space, when retrying, then the recording is scheduled successfully

**AI Component:** Yes -- AI suggests which recordings to delete (see US-PVR-018)

**Dependencies:** Recording Service, Subscription Service, US-PVR-018 (AI Cleanup)

**Technical Notes:**
- Quota check performed pre-scheduling to prevent failed recordings
- "Upgrade" CTA deep-links to subscription management

---

### US-PVR-009: Recording Library Browse and Management

**As a** viewer
**I want to** browse my recordings with sort, filter, and search capabilities
**So that** I can quickly find and manage recordings in a large library

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** PVR-FR-012

**Acceptance Criteria:**
- [ ] Given a viewer opens "My Recordings," when the library loads, then all recordings are displayed within 2 seconds (up to 500 recordings)
- [ ] Given sort options, when sorting, then available sorts are: date (newest/oldest), title (A-Z), size (largest/smallest), watch status (unwatched first), series grouping
- [ ] Given filter options, when filtering, then available filters are: unwatched, partially watched, fully watched, protected, series, movies
- [ ] Given search, when searching within recordings, then results match on title and series name
- [ ] Given series recordings, when grouped, then series show episode count and a "next unwatched" indicator
- [ ] Performance: Sort and filter operations complete in < 500ms

**AI Component:** No

**Dependencies:** Recording Service, BFF

**Technical Notes:**
- Library data pre-fetched and cached client-side for fast sort/filter
- Series grouping based on series ID from EPG metadata

---

### US-PVR-010: Delete Recordings (Single and Bulk)

**As a** viewer
**I want to** delete individual or multiple recordings at once to free up storage
**So that** I can manage my quota efficiently

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** PVR-FR-013

**Acceptance Criteria:**
- [ ] Given a viewer deletes a single recording, when confirmed, then deletion completes in < 2 seconds and quota updates immediately
- [ ] Given a viewer enters multi-select mode, when selecting up to 50 recordings for bulk delete, then all are deleted within 5 seconds
- [ ] Given a deletion, when completed, then an undo option is available for 10 seconds (soft delete, then hard delete)
- [ ] Given a bulk deletion summary, when displayed, then it shows: number of recordings, total space freed, and new available space

**AI Component:** No

**Dependencies:** Recording Service, quota cache

**Technical Notes:**
- Soft delete (10-second undo window) followed by hard delete
- Copy-on-write: only user recording pointer is deleted; master recording persists if other users reference it

---

### US-PVR-011: Protect Recording from Auto-Delete

**As a** viewer
**I want to** mark recordings as "protected" so they are never auto-deleted
**So that** my important recordings are preserved even when my quota is full

**Priority:** P0
**Phase:** 1
**Story Points:** S
**PRD Reference:** PVR-FR-014

**Acceptance Criteria:**
- [ ] Given a viewer toggles protection on a recording, when toggled, then a lock icon appears on the recording
- [ ] Given a protected recording, when auto-delete policies run, then protected recordings are never removed
- [ ] Given a protected recording, when AI Cleanup suggests deletions, then protected recordings are excluded from suggestions

**AI Component:** No

**Dependencies:** Recording Service

**Technical Notes:**
- Protection status stored as a flag on the user recording entry
- One-press toggle in recording detail or long-press context menu

---

### US-PVR-012: Auto-Delete Policy per Recording

**As a** viewer
**I want to** set a retention policy per recording: "Space needed" (auto-delete when full) or "I delete" (keep forever)
**So that** I can control which recordings are automatically cleaned up

**Priority:** P1
**Phase:** 1
**Story Points:** S
**PRD Reference:** PVR-FR-015

**Acceptance Criteria:**
- [ ] Given the default retention policy is "Space needed," when a user's quota is full and a new recording needs space, then the oldest "Space needed" recording is auto-deleted
- [ ] Given a recording set to "I delete," when auto-delete runs, then it is never removed
- [ ] Given auto-deletion occurs, when the user is notified, then a message shows: "Deleted: [title] to make room for [new recording]"

**AI Component:** No

**Dependencies:** Recording Service, Notification Service

**Technical Notes:**
- Auto-delete priority: oldest "Space needed" recordings first
- Protected recordings are a superset of "I delete" (protected implies no auto-delete)

---

## Epic 3: Recording Playback

### US-PVR-013: Recording Playback with Full Trick-Play

**As a** viewer
**I want to** play my recordings with full trick-play controls
**So that** I can watch recordings at my own pace with full navigation control

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** PVR-FR-020

**Acceptance Criteria:**
- [ ] Given a viewer selects a recording, when playback starts, then the recording begins playing within 2 seconds
- [ ] Given trick-play controls, when used, then pause, rewind (2x, 4x, 8x, 16x, 32x), fast-forward (2x, 4x, 8x, 16x, 32x), and skip (10s, 30s forward/backward) all respond in < 300ms
- [ ] Given scrubbing, when thumbnail previews are available, then I-frame thumbnails are displayed at 10-second intervals
- [ ] Performance: Rebuffer ratio < 0.2% for recording playback sessions

**AI Component:** No

**Dependencies:** S3 recording storage, CDN delivery, player per platform

**Technical Notes:**
- Recording playback uses same player components as VOD/catch-up
- Trick-play thumbnails generated from I-frames during recording capture

---

### US-PVR-014: Cross-Device Recording Playback with Resume

**As a** viewer
**I want to** play recordings on any device and resume from where I left off
**So that** I can switch between devices seamlessly

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** PVR-FR-021, PVR-FR-022

**Acceptance Criteria:**
- [ ] Given a viewer partially watches a recording on one device, when opening the app on another device, then the recording shows a "Continue from [time]" indicator
- [ ] Given resume, when playback starts, then it begins at the bookmarked position with a "Resuming from [time]" indicator shown for 3 seconds
- [ ] Given the recording detail screen, when displayed, then both "Resume" and "Play from beginning" options are available
- [ ] Performance: Bookmark sync latency < 5 seconds across devices; bookmark accuracy within 5 seconds

**AI Component:** No

**Dependencies:** Bookmark Service, Profile Service

**Technical Notes:**
- DRM license acquired per device per session (same content key, different license)
- Bookmark stored per user profile + master recording ID

---

### US-PVR-015: Multi-Audio and Subtitle Selection in Recordings

**As a** viewer
**I want to** select from all audio and subtitle tracks that were available in the original live broadcast
**So that** I can watch recordings in my preferred language

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** PVR-FR-023

**Acceptance Criteria:**
- [ ] Given a recording preserves all original broadcast audio tracks, when the audio menu is opened, then all tracks (original, dubbed, audio description) are available
- [ ] Given a recording preserves all subtitle tracks, when the subtitle menu is opened, then all original subtitle languages are available
- [ ] Given a track switch, when selected, then the change applies within 500ms without stream restart

**AI Component:** No

**Dependencies:** Recording capture pipeline (must preserve all tracks), player per platform

**Technical Notes:**
- CMAF packaging preserves all alternate renditions (audio, subtitle) from the live manifest
- Same audio/subtitle selection UX as live TV and VOD

---

### US-PVR-016: Playback of In-Progress Recording

**As a** viewer
**I want to** start watching a recording that is still being captured (the program is still airing)
**So that** I can begin watching from the start while the rest of the program is still recording

**Priority:** P2
**Phase:** 2
**Story Points:** L
**PRD Reference:** PVR-FR-025

**Acceptance Criteria:**
- [ ] Given a recording is in progress, when the viewer selects "Play," then playback starts from the beginning within 3 seconds
- [ ] Given playback of an in-progress recording, when trick-play is used, then full trick-play is available within the already-recorded portion
- [ ] Given playback reaches the recording edge, when at the edge, then a "Jump to Live" button is available to switch to the live broadcast
- [ ] Given the recording is in progress, when the UI displays, then an "In Progress" indicator is visible on the recording

**AI Component:** No

**Dependencies:** Recording Service (progressive manifest), Live TV Service (PRD-001)

**Technical Notes:**
- Progressive manifest grows as new segments are captured
- Similar to Start Over UX but sourced from PVR storage

---

## Epic 4: AI-Powered Recording Features

### US-PVR-017: AI Smart Recording Suggestions

**As a** viewer
**I want to** receive proactive recording suggestions based on my viewing habits
**So that** I do not miss programs I would enjoy and do not have to manually browse the EPG

**Priority:** P1
**Phase:** 1
**Story Points:** XL
**PRD Reference:** AI Section 5.1

**Acceptance Criteria:**
- [ ] Given the AI evaluates upcoming programs, when a match exceeds 75% confidence, then a suggestion is delivered at least 12 hours before broadcast
- [ ] Given a suggestion is displayed, when shown, then it includes: program details, channel, time, duration, storage impact, confidence reason, and one-tap "Record" and "Dismiss" buttons
- [ ] Given suggestion acceptance rate, when measured, then > 50% of suggestions above 75% confidence are accepted
- [ ] Given accepted suggestions, when measured, then > 60% are watched for more than 50% of their duration
- [ ] Given frequency capping, when enforced, then a maximum of 5 suggestions per user per week are delivered
- [ ] Given a user dismisses a suggestion, when noted, then the dismiss signal is used to calibrate future suggestions (e.g., dismissing domestic league sports reduces future domestic league confidence)
- [ ] Given a user disables suggestions, when configured in settings, then suggestions can be turned off entirely or per genre

**AI Component:** Yes -- XGBoost model trained on recording-outcome data (suggested -> accepted/rejected -> watched/not-watched); served via KServe (CPU, < 15ms inference); retrains daily

**Dependencies:** Recommendation Service (PRD-007), Feature Store, EPG Service, Notification Service

**Technical Notes:**
- Model inputs: recording history patterns, viewing history, content signals, temporal signals
- Suggestion delivery: in-app notification card, optional push notification, "Suggested for you" badge in EPG

---

### US-PVR-018: AI Smart Retention (Storage Cleanup)

**As a** viewer
**I want to** receive intelligent suggestions for which recordings to delete when my storage is running low
**So that** I can free up space without agonizing over what to keep

**Priority:** P1
**Phase:** 1
**Story Points:** L
**PRD Reference:** AI Section 5.2

**Acceptance Criteria:**
- [ ] Given a viewer opens "AI Cleanup" or hits a quota warning, when suggestions are generated, then a ranked list of recordings to delete appears within 1 second
- [ ] Given each suggestion, when displayed, then it includes: recording title, watch progress, age, size, availability elsewhere (catch-up/VOD), and a human-readable reason
- [ ] Given protected recordings, when generating suggestions, then they are NEVER included
- [ ] Given the deletability scoring, when applied, then factors are: watched % (+40 for fully watched), availability elsewhere (+15 each for catch-up/VOD), age (+1/day up to +15), user thumbs-up (-20)
- [ ] Given users who open AI Cleanup, when measured, then 80%+ accept at least one suggestion
- [ ] Given AI Cleanup access, when available, then it is accessible from: PVR library "Manage" button, quota warning dialog, and recording scheduling when quota is insufficient

**AI Component:** Yes -- Rule-based deletability scoring (not ML) with explainable composite score; intentionally deterministic for user trust

**Dependencies:** Recording Service, Catalog Service (catch-up/VOD availability check)

**Technical Notes:**
- Scoring formula: watched_score + availability_score + age_score + user_signal_score
- Cross-service check: Catalog Service for catch-up/VOD availability of same content

---

### US-PVR-019: AI Chapter Marks and Highlights

**As a** sports fan
**I want to** see AI-generated chapter marks and highlights in my sports recordings
**So that** I can jump to key moments or watch a condensed highlight summary

**Priority:** P2
**Phase:** 3
**Story Points:** XL
**PRD Reference:** AI Section 5.3

**Acceptance Criteria:**
- [ ] Given a recording completes, when AI processing finishes, then chapter marks are available within 60 minutes
- [ ] Given a sports recording, when highlights are generated, then 90%+ of goals are detected, 85%+ of penalties and red cards, with < 10% false positive rate
- [ ] Given a non-sports recording, when chapters are generated, then 5-15 chapter marks per hour are created, aligned with scene transitions
- [ ] Given the chapter navigation overlay, when accessed from the scrubber bar, then it loads in < 500ms
- [ ] Given a "Watch Highlights" option, when selected, then all chapter marks play sequentially with 15 seconds of pre-context per mark
- [ ] Given highlight summary duration, when calculated, then it is < 15% of total recording duration (e.g., < 12 min for a 90-min match)

**AI Component:** Yes -- Multimodal model: fine-tuned CLIP variant (video) + audio classifier (crowd intensity, commentator, whistles) served via SageMaker (GPU: A10G); 0.3x real-time processing

**Dependencies:** SageMaker batch processing, Recording Service metadata, KServe

**Technical Notes:**
- Sports: detects scoreboards, celebration scenes, referee actions, crowd spikes, commentator excitement
- Non-sports: shot boundary detection (cuts, fades, dissolves) + audio silence/music transitions
- Chapter marks stored in Recording Service metadata (PostgreSQL)

---

### US-PVR-020: Skip Intro and Skip Recap

**As a** binge watcher
**I want to** skip the intro sequence and "previously on" recap at the start of recorded episodes
**So that** I can get straight to new content when binge-watching

**Priority:** P2
**Phase:** 3
**Story Points:** L
**PRD Reference:** PVR-FR-024

**Acceptance Criteria:**
- [ ] Given a recorded episode has AI-detected intro markers, when the intro begins, then a "Skip Intro" button appears
- [ ] Given a recorded episode has AI-detected recap markers, when the recap begins, then a "Skip Recap" button appears
- [ ] Given the skip button, when not pressed, then it auto-dismisses after the intro/recap ends
- [ ] Given marker accuracy, when measured, then 90%+ are correct within 3 seconds of the actual boundary

**AI Component:** Yes -- Scene detection model analyzes audio patterns (theme music) and visual patterns (title cards) to identify intro and recap sequences

**Dependencies:** AI content enrichment pipeline, SageMaker

**Technical Notes:**
- Markers generated as part of the chapter mark batch processing pipeline
- Same model processes both chapter marks and intro/recap detection

---

### US-PVR-021: Auto-Record Based on Learned Preferences

**As a** sports fan
**I want to** have the platform automatically record programs it knows I would want based on 6+ months of behavior
**So that** I never miss important content even when I forget to schedule recordings

**Priority:** P2
**Phase:** 4
**Story Points:** XL
**PRD Reference:** AI Section 5.4

**Acceptance Criteria:**
- [ ] Given Auto-Record is opt-in, when enabled in Settings, then the user can configure: genres, channels, confidence threshold (default 90%), and weekly cap (default 10)
- [ ] Given Auto-Record is active, when new EPG data arrives, then programs above the confidence threshold are automatically scheduled
- [ ] Given auto-recordings are made, when the user is notified, then a review notification is sent within 1 hour listing all auto-recordings with a "Cancel" option per item
- [ ] Given 85%+ of auto-recorded items, when measured, then they are either watched or retained (not immediately cancelled/deleted)
- [ ] Given the user cancels 3+ items of the same content type, when the pattern is detected, then future confidence for that type is reduced
- [ ] Given quota constraints, when Auto-Record would exceed quota, then Smart Retention suggestions are offered alongside the auto-record notification
- [ ] Given Auto-Record is available, when checking eligibility, then only users with 6+ months of recording history can enable it

**AI Component:** Yes -- Extended XGBoost model from Smart Recording Suggestions with higher confidence threshold (90%); autonomous scheduling with mandatory review window

**Dependencies:** Recommendation Service (PRD-007), Feature Store, Recording Service, Notification Service

**Technical Notes:**
- 24-hour review window: user can cancel any auto-recording within 24 hours
- If cancellation rate exceeds 30%, auto-downgrade to suggestion-only mode for that user

---

## Epic 5: Catch-Up and PVR Overlap

### US-PVR-022: Catch-Up Overlap Detection and Information

**As a** viewer
**I want to** be informed when a program I want to record is also available on Catch-Up
**So that** I can make an informed decision about whether to use my PVR quota

**Priority:** P1
**Phase:** 1
**Story Points:** M
**PRD Reference:** Scenario 9

**Acceptance Criteria:**
- [ ] Given a viewer records a program that will also be available on Catch-Up, when the scheduling dialog appears, then an informational message says: "Also available on Catch-Up for [X] days after it airs"
- [ ] Given the message, when options are shown, then the viewer can choose: "Record (keep in my library)" or "Don't record (watch on Catch-Up instead)"
- [ ] Given a program NOT available on catch-up, when scheduling, then no overlap message is shown
- [ ] Given the overlap check, when performed, then it is accurate per the rights engine

**AI Component:** No

**Dependencies:** Rights Engine (catch-up availability), Recording Service

**Technical Notes:**
- Overlap check queries catch-up rights for the same program
- Message is informational, not blocking -- the user always has the choice to record

---

### US-PVR-023: Record from Catch-Up Browse

**As a** viewer
**I want to** record a catch-up program to my PVR to keep it beyond the catch-up window
**So that** I can preserve content that will expire from catch-up

**Priority:** P1
**Phase:** 1
**Story Points:** M
**PRD Reference:** TSTV integration (Section 7.4)

**Acceptance Criteria:**
- [ ] Given a catch-up program is displayed, when a "Record to PVR" button is available, then pressing it creates a PVR recording from the catch-up content
- [ ] Given the recording is created, when stored, then it appears in "My Recordings" with no expiry tied to the catch-up window
- [ ] Given the user has no PVR entitlement, when the button would appear, then it is hidden
- [ ] Given storage quota, when the recording is created, then quota is checked and enforced

**AI Component:** No

**Dependencies:** TSTV Service (PRD-002), Recording Service, Catalog Service

**Technical Notes:**
- Copy-on-write: the user recording pointer references the catch-up master recording
- Retention extends beyond catch-up window (catch-up segments are preserved for PVR users)

---

## Epic 6: Recording Rights and Business Rules

### US-PVR-024: Recording Expiry Based on Content Rights

**As an** operator
**I want to** enforce content rights-based expiry on recordings
**So that** contractual obligations are met when content licenses expire

**Priority:** P1
**Phase:** 2
**Story Points:** M
**PRD Reference:** PVR-FR-032

**Acceptance Criteria:**
- [ ] Given a recording has a rights-based expiry (e.g., 90-day retention), when the expiry date is set, then it is visible on the recording detail screen
- [ ] Given a recording is approaching expiry, when 7 days remain, then a notification is sent; another at 1 day remaining
- [ ] Given a recording expires, when the expiry time passes, then the recording is auto-deleted within 24 hours

**AI Component:** No

**Dependencies:** Rights Engine, Notification Service

**Technical Notes:**
- Rights-based expiry overrides user retention preference
- Notification: "Your recording of [title] expires in [X] days"

---

### US-PVR-025: Advertising Support in Recordings

**As an** operator
**I want to** preserve ad break markers in recordings for SSAI integration
**So that** targeted ads can be inserted when viewers play back recordings

**Priority:** P1
**Phase:** 2
**Story Points:** M
**PRD Reference:** PVR-FR-033

**Acceptance Criteria:**
- [ ] Given a recording manifest, when ad markers from the original live broadcast are present, then SCTE-35 markers are preserved
- [ ] Given the Ad Service, when SSAI is active, then ads are inserted at the marker positions during playback
- [ ] Given ad skip policy, when configured per channel/operator, then skip behavior is enforced client-side (no skip, skip after X seconds, free skip)

**AI Component:** No

**Dependencies:** Ad Service (separate PRD), recording capture pipeline (SCTE-35 preservation)

**Technical Notes:**
- SCTE-35 markers passed through from live packaging to recording segments
- Ad policy metadata associated with recording via channel/program rights

---

### US-PVR-026: Copy-on-Write Compliance Mode

**As an** operator
**I want to** support per-user individual copies in markets where regulations require them
**So that** Cloud PVR complies with local regulations in all territories

**Priority:** P1
**Phase:** 2
**Story Points:** L
**PRD Reference:** PVR-FR-034

**Acceptance Criteria:**
- [ ] Given a territory requires individual copies, when configured, then each user's recording is a physically separate copy on S3
- [ ] Given individual copy mode, when active, then storage ratio drops to 1:1 (no copy-on-write savings)
- [ ] Given the mode, when configured, then it is set per territory/operator in the Recording Service configuration
- [ ] Given the mode, when active, then functionality is identical from the user's perspective

**AI Component:** No

**Dependencies:** Recording Service configuration, Legal/compliance input per territory

**Technical Notes:**
- Per-territory configuration flag in Recording Service
- In individual copy mode, each user's recording is stored in a separate S3 path

---

## Epic 7: Non-Functional and Technical Enablers

### US-PVR-027: Recording Capture Reliability and Failover

**As a** developer
**I want to** ensure recording captures have high reliability with automatic failover
**So that** scheduled recordings are never missed due to infrastructure failures

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** NFR Section 6.2, Technical Section 7.2

**Acceptance Criteria:**
- [ ] Given recording capture success rate, when measured, then 99.5% of scheduled recordings are successfully captured
- [ ] Given a capture worker fails mid-recording, when the watchdog detects it (within 60 seconds), then capture is restarted from the last successful segment on another worker
- [ ] Given the Recording Scheduler, when monitoring capture health, then it reassigns captures where heartbeats are missing for 60+ seconds
- [ ] Performance: Recording starts within +/- 5 seconds of scheduled time; recording available for playback within 2 minutes of program end

**AI Component:** No

**Dependencies:** Kubernetes (worker pool), S3, Kafka (heartbeat monitoring)

**Technical Notes:**
- N+2 redundancy for capture workers
- Segments are immutable on S3 -- restart from last written segment, no corruption risk
- Master recording check: if another user already triggered a master recording, no duplicate capture

---

### US-PVR-028: PVR Telemetry and Observability

**As a** developer
**I want to** have comprehensive telemetry for recording scheduling, capture, playback, and AI features
**So that** we can monitor reliability, measure success metrics, and detect issues

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** NFR Section 6, Metrics Section 9

**Acceptance Criteria:**
- [ ] Given recording operations, when telemetry is captured, then the following are recorded: scheduling events, capture start/complete/failure, playback sessions, quota changes, AI suggestion delivery/acceptance/rejection
- [ ] Given Conviva integration, when reporting on recording playback, then QoE metrics are available per session
- [ ] Given server-side metrics, when reported, then capture success rate, capture worker utilization, S3 storage usage, copy-on-write ratio, and quota enforcement events are available in Grafana
- [ ] Given AI metrics, when tracked, then suggestion acceptance rate, watch-through rate, AI Cleanup adoption, and auto-record accuracy are tracked in dashboards

**AI Component:** No

**Dependencies:** Conviva SDK, Prometheus + Grafana, Kafka telemetry pipeline

**Technical Notes:**
- Key operational metrics: capture success rate, recording availability time, S3 storage growth, copy-on-write ratio
- Key AI metrics: suggestion acceptance, watch-through, cleanup adoption

---

### US-PVR-029: Copy-on-Write Garbage Collection

**As a** developer
**I want to** have automated garbage collection for master recordings that no user references
**So that** S3 storage does not grow indefinitely with orphaned content

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** Technical Section 7.1

**Acceptance Criteria:**
- [ ] Given the last user recording pointer to a master recording is deleted, when garbage collection runs, then the master recording and its physical segments are removed from S3 after a 7-day safety retention period
- [ ] Given the garbage collection job, when scheduled, then it runs daily during off-peak hours
- [ ] Given shared segments between catch-up and PVR, when a segment is referenced by either service, then it is not deleted

**AI Component:** No

**Dependencies:** Recording Service, S3, TSTV Service (shared segment references)

**Technical Notes:**
- Reference counting: master recordings track user recording count
- Safety retention period (7 days) prevents accidental data loss if a user re-creates a recording
- Shared segment reference check prevents deleting segments still needed by catch-up

---

### US-PVR-030: Catch-Up to PVR Storage Integration

**As a** developer
**I want to** share storage segments between TSTV catch-up and Cloud PVR
**So that** the same content is not duplicated across services, reducing storage costs

**Priority:** P1
**Phase:** 1
**Story Points:** L
**PRD Reference:** Technical Section 7.4

**Acceptance Criteria:**
- [ ] Given a channel is both catch-up-enabled and PVR-enabled, when both services need the same segments, then the same S3 segments are referenced by both (no duplication)
- [ ] Given catch-up content expires, when a PVR user still references the segments, then the segments are retained for the PVR user
- [ ] Given "Record from beginning" uses the start-over buffer, when the buffer content is available, then segments from EFS/S3 catch-up storage are reused for the PVR recording

**AI Component:** No

**Dependencies:** TSTV Service (PRD-002), Recording Service, S3 segment management

**Technical Notes:**
- Segment path conventions must align between catch-up and PVR storage
- Reference counting spans both services to prevent premature deletion

---

*End of User Stories for PRD-003: Cloud PVR*
*Total: 30 stories (14 core functional, 5 AI enhancement, 5 non-functional, 6 technical/integration)*
