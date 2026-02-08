# PRD-003: Cloud PVR (Network PVR)
## AI-Native OTT Streaming Platform

**Document ID:** PRD-003
**Version:** 1.0
**Date:** 2026-02-08
**Status:** Draft
**Author:** PRD Writer A
**References:** VIS-001 (Project Vision & Design), ARCH-001 (Platform Architecture), PRD-001 (Live TV), PRD-002 (TSTV)
**Stakeholders:** Product Management, Engineering (Platform, Client, AI/ML), Content Rights, Legal, SRE

---

## Table of Contents

1. [Overview](#1-overview)
2. [Goals & Non-Goals](#2-goals--non-goals)
3. [User Scenarios](#3-user-scenarios)
4. [Functional Requirements](#4-functional-requirements)
5. [AI-Specific Features](#5-ai-specific-features)
6. [Non-Functional Requirements](#6-non-functional-requirements)
7. [Technical Considerations](#7-technical-considerations)
8. [Dependencies](#8-dependencies)
9. [Success Metrics](#9-success-metrics)
10. [Open Questions & Risks](#10-open-questions--risks)

---

## 1. Overview

### Service Description

Cloud PVR (also known as Network PVR or nPVR) is a cloud-based personal video recording service that allows subscribers to record live TV programs to platform-managed cloud storage and play them back on any device at any time. Unlike traditional set-top box PVR, Cloud PVR has no tuner conflicts (any number of simultaneous recordings), no local storage limitations (cloud-based quota), and full cross-device accessibility (watch a recording started on the living room TV from a phone on the train).

The service operates on a **copy-on-write** architecture: a single master recording is created per program per channel, and individual users receive entitlement pointers to that master recording. This achieves a storage efficiency ratio of 10:1 or better (10 users recording the same program consume the same physical storage as 1 user). From a user perspective, the recording appears as a personal asset in their library, with individual bookmarks, watch status, and deletion capability.

What makes this Cloud PVR AI-native is the intelligence layer: rather than relying on users to manually schedule recordings (the traditional approach that results in missed programs and cluttered libraries), the platform proactively suggests recordings based on learned preferences, manages storage quota intelligently, and generates navigable chapter marks and highlights for recorded content.

### Business Context

Cloud PVR is a proven monetization lever in the pay-TV industry. It serves three business purposes:

1. **Premium upsell**: Cloud PVR is typically offered as a paid add-on or included in higher subscription tiers. Base tier: 50 hours, premium: 200 hours, unlimited: enterprise pricing. Storage upgrades generate recurring revenue.
2. **Retention**: PVR users have 25-40% lower churn than non-PVR users across industry benchmarks, because accumulated recordings create switching cost and the recording habit creates platform dependency.
3. **Engagement**: PVR users watch 30-45% more content than non-PVR users. Recordings extend the value of live TV channels beyond the broadcast moment.

Cloud PVR complements TSTV (PRD-002) rather than replacing it. TSTV provides ephemeral access (7-day rolling window, operator-controlled). Cloud PVR provides persistent personal storage (user-controlled, survives beyond the catch-up window). A viewer who wants to watch a program next week records it to PVR; a viewer who wants to watch last night's episode uses catch-up.

### Scope

**In Scope:**
- Manual recording: single program recording, series recording (series link)
- Recording management: list, sort, filter, delete, protect individual recordings
- Storage quota management: per-user quotas, usage tracking, upgrade prompts
- Copy-on-write storage architecture for efficiency
- Full trick-play playback of recordings (pause, rewind, fast-forward, skip, scrub)
- Cross-device playback and bookmark sync for recordings
- AI-powered recording suggestions ("You might want to record...")
- AI-powered smart retention (storage cleanup suggestions)
- AI-generated chapter marks and highlights (Phase 3)
- Auto-record based on learned preferences (Phase 4)
- Integration with Live TV (PRD-001) for record-from-live
- Integration with EPG (PRD-005) for schedule-based recording
- Content rights management for recording eligibility

**Out of Scope:**
- Downloading recordings for offline playback (Phase 3+ mobile consideration)
- Sharing recordings between users/households (rights complexity)
- Recording VOD or catch-up content (only live broadcast is recordable)
- Recording FAST channels (separate future scope)
- Ad-free playback of recordings (ad policy in recordings is a monetization decision handled by the Ad Service)
- Physical PVR migration from legacy set-top boxes (operator-specific migration project)

---

## 2. Goals & Non-Goals

### Goals

1. **Deliver a conflict-free recording experience**: any number of programs can be recorded simultaneously with zero tuner conflicts, eliminating the primary frustration of traditional PVR.
2. **Achieve recording accuracy of +/- 5 seconds**: recordings start and end within 5 seconds of the scheduled program boundary, capturing the complete program.
3. **Make recordings playable within 2 minutes of program end**: a recording is available for playback shortly after the program finishes broadcasting, without waiting for post-processing.
4. **Implement copy-on-write architecture** achieving a physical-to-logical storage ratio of 10:1 or better, enabling cost-effective storage at scale.
5. **AI-suggest recordings** to increase recording adoption by 45%, reducing the number of missed programs that viewers would have wanted to keep.
6. **AI-manage storage** so that when quota approaches capacity, users receive intelligent recommendations for which recordings to delete or archive, based on watched status, availability elsewhere (catch-up/VOD), age, and user preferences.
7. **Support per-user quotas** with configurable tiers (50, 100, 200, unlimited hours) and real-time quota tracking visible to the user.
8. **Enable cross-device playback** with bookmark sync within 5 seconds, so viewers can start a recording on one device and continue on another.

### Non-Goals

1. **Replacing TSTV catch-up**: Cloud PVR is a premium, user-controlled service. Catch-up is an operator-provided service with different economics. They coexist.
2. **Live recording (real-time viewing of in-progress recording)**: While technically possible, this PRD does not require live-tail playback of a recording that is still in progress (Phase 2 consideration). The recording is available after broadcast ends.
3. **Social/shared PVR**: Sharing recordings between accounts or households raises content rights issues and is out of scope.
4. **Recording quality selection**: Recordings are stored at the same quality as the live broadcast. Users cannot choose to record at lower quality to save quota.
5. **Unlimited storage for all tiers**: Storage quotas exist as a monetization lever. "Unlimited" is a specific paid tier, not the default.

---

## 3. User Scenarios

### Scenario 1: Single Program Recording from EPG

**Persona:** David (Okafor Family)
**Context:** David browses the EPG on Tuesday evening and sees a Champions League match scheduled for Wednesday at 20:00 on Channel 5. He will be at a dinner and cannot watch live.

**Flow:**
1. David navigates to the EPG (PRD-005) and finds the Champions League match on Wednesday at 20:00, Channel 5.
2. He presses the "Record" button on the EPG listing.
3. A recording confirmation dialog appears: "Record: Champions League Semi-Final. Wed 20:00-22:15 on Channel 5. Storage: ~2.5 hours. Current usage: 62/100 hours." He confirms.
4. A recording icon appears on the EPG listing. The recording is added to David's "Scheduled Recordings" list.
5. On Wednesday at 20:00, the Recording Service automatically starts capturing the live feed. No user device needs to be powered on.
6. At 22:15, the recording completes. Within 2 minutes, the recording appears in David's "My Recordings" library, playable from any device.
7. On Thursday, David opens the app on his phone and sees the recording in "My Recordings." He plays it with full trick-play.

**Success Criteria:** Recording scheduled in < 2 seconds. Recording starts within 5 seconds of scheduled time. Recording available for playback within 2 minutes of program end. Storage usage update is immediate and accurate.

---

### Scenario 2: Series Recording (Series Link)

**Persona:** Priya (Binge Watcher)
**Context:** Priya discovers a new series "Midnight Sun" on the EPG. She wants to record every episode automatically.

**Flow:**
1. Priya finds "Midnight Sun - Episode 1" in the EPG, airing Thursday at 21:00 on Channel 22.
2. She selects "Record Series" (not just "Record" for the single episode).
3. A series recording options dialog appears:
   - Record: "New episodes only" / "All episodes (including repeats)" / "New + repeats on this channel only"
   - Keep until: "Space needed" (auto-delete oldest when quota full) / "I delete" (protected, never auto-delete)
   - Start: "On time" / "1 min early" / "5 min early"
   - End: "On time" / "5 min late" / "15 min late" / "30 min late" (for overruns)
4. Priya selects "New episodes only," "I delete," "On time" start, "5 min late" end.
5. The series link is created. Every future episode of "Midnight Sun" (identified by series ID from EPG metadata) is automatically scheduled for recording when the EPG data becomes available (typically 7 days in advance).
6. Priya sees "Midnight Sun (Series)" in her "Scheduled Recordings" with upcoming episodes listed.
7. Each week, the new episode is recorded automatically and appears in her library, grouped under the series name.

**Success Criteria:** Series link creation completes in < 2 seconds. New episodes are automatically detected and scheduled within 5 minutes of EPG data availability. Series grouping is accurate (correct series ID matching). Episode numbering is correct and sorted chronologically.

---

### Scenario 3: Record from Live Viewing

**Persona:** Erik (Sports Fan)
**Context:** Erik is watching a live football match and realizes he needs to leave. He wants to record the rest so he can finish watching later.

**Flow:**
1. Erik is watching Channel 5 live. 45 minutes into a 2-hour match.
2. He presses the "Record" button on the player overlay (per PRD-001 Scenario 7).
3. Options: "Record from now" (45 min remaining), "Record from beginning" (if start-over content is available, records the entire program including the 45 minutes he already watched), "Record series."
4. Erik selects "Record from beginning" to capture the entire match.
5. The Recording Service creates a recording of the full program. The portion that already aired is sourced from the start-over buffer (EFS, per PRD-002 architecture). The remainder continues recording from the live feed.
6. A recording indicator appears on the player overlay. Erik can leave knowing the entire match is being captured.
7. Later, Erik plays the recording from his library. His live viewing position (45 minutes) is preserved as a bookmark -- the recording interface offers "Continue from 45:00" or "Play from start."

**Success Criteria:** Recording initiation from live completes in < 2 seconds. "Record from beginning" captures content back to program start (sourced from start-over buffer). Live viewing bookmark transfers to the recording seamlessly.

---

### Scenario 4: AI Recording Suggestion

**Persona:** Erik (Sports Fan)
**Context:** A Champions League quarter-final is scheduled for tomorrow evening. Erik records Champions League matches 90% of the time. The platform proactively suggests recording.

**Flow:**
1. Erik opens the app on Tuesday evening. A notification card appears on the home screen: "Champions League Quarter-Final: Barcelona vs Inter Milan, Wed 20:00, Channel 5. Based on your viewing history, you usually record Champions League matches. Record it?" with "Record" and "Dismiss" buttons.
2. The suggestion includes: match details, channel, duration (2.5 hours estimated), storage impact ("You have 38 hours remaining").
3. Erik taps "Record." The recording is scheduled instantly. A confirmation toast appears.
4. If Erik dismisses, the suggestion does not reappear for this specific match. The AI notes the dismiss signal for future calibration.
5. Over time, if Erik consistently accepts Champions League suggestions but dismisses domestic league suggestions, the AI refines its model: Champions League confidence rises, domestic league confidence falls.

**Success Criteria:** AI suggestion delivered at least 12 hours before broadcast. Suggestion confidence threshold: only suggest when model confidence > 75%. Suggestion acceptance rate: > 50% for suggestions above threshold. One-tap recording from suggestion completes in < 1 second. Maximum 5 AI recording suggestions per user per week (frequency cap).

---

### Scenario 5: Storage Quota Management with AI Smart Retention

**Persona:** The Okafor Family (David)
**Context:** David's PVR quota is 100 hours. Current usage is 92 hours. A new recording is scheduled for tomorrow (2.5 hours). The platform needs to help David free up space.

**Flow:**
1. David sees a notification: "Your PVR is almost full (92/100 hours). A Champions League match (2.5 hrs) is scheduled for tomorrow. Free up space?"
2. He navigates to his recordings library. An "AI Cleanup" button is available.
3. Pressing "AI Cleanup" shows a list of suggested recordings to delete, ranked by AI confidence:
   - "Planet Earth: Oceans" (watched 100%, 1 hour) -- "Fully watched, also available on Catch-Up for 3 more days"
   - "News Special: Election Coverage" (watched 20%, 2 hours, 14 days old) -- "Watched only 20%, 2 weeks old"
   - "Bake Off S3 E2" (watched 0%, 1 hour, 21 days old) -- "Unwatched, 3 weeks old, all episodes available on VOD"
   - "MasterChef S8 E1" (protected, watched 100%) -- AI does NOT suggest deleting protected recordings
4. Each suggestion shows: recording title, watch progress (%), recording age, size, and the AI's reason for suggesting deletion. Availability elsewhere (catch-up, VOD) is highlighted.
5. David selects "Planet Earth" and "News Special" for deletion. 3 hours freed. A confirmation dialog shows: "Delete 2 recordings? This frees 3 hours. You'll have 11 hours available."
6. David confirms. Recordings are deleted. Quota updates immediately.

**Success Criteria:** AI cleanup suggestions generated in < 1 second. Suggestions never include protected recordings. Suggestions are ranked by a composite score: watched % (higher = more deletable), age (older = more deletable), availability elsewhere (available = more deletable), user-rated (lower rating or no rating = more deletable). 80%+ of users who use AI Cleanup accept at least one suggestion.

---

### Scenario 6: Recording Playback with Trick-Play

**Persona:** Maria (Busy Professional)
**Context:** Maria recorded a 2-hour documentary film. She wants to watch it over two evenings, skipping the opening credits.

**Flow:**
1. Maria opens "My Recordings" and selects the documentary.
2. A detail screen shows: title, recorded date, channel, duration, watch status (unwatched), and storage size.
3. She presses "Play." The recording starts from the beginning.
4. Maria fast-forwards through the opening credits (8x speed). Trick-play thumbnails (every 10 seconds) help her see when the actual content begins.
5. She presses play at the 4:30 mark. Watches for 1 hour (until 1:04:30), then pauses and goes to bed.
6. The next evening, Maria opens the app on a different device (Apple TV). "My Recordings" shows the documentary with a progress bar: "Continue from 1:04:30."
7. She resumes. During playback, she uses skip-forward (30-second jumps) to skip through a slow section.

**Success Criteria:** Recording playback starts in < 2 seconds. Trick-play speeds available: 2x, 4x, 8x, 16x, 32x forward, 2x, 4x, 8x, 16x, 32x reverse. Skip forward/backward in 10-second and 30-second increments. Bookmark accuracy: within 5 seconds. Cross-device resume within 5 seconds.

---

### Scenario 7: AI-Generated Chapter Marks and Highlights (Phase 3)

**Persona:** Erik (Sports Fan)
**Context:** Erik recorded a 2-hour football match. He does not have time to watch the full match but wants to see the key moments.

**Flow:**
1. Erik opens the recorded match in "My Recordings."
2. Below the standard playback controls, a "Highlights" section is visible: "5 key moments detected."
3. The highlights are AI-generated chapter marks: "Goal (23:15)", "Red Card (37:40)", "Goal (56:02)", "Penalty Saved (71:20)", "Goal (89:55)."
4. Erik can play highlights sequentially (8-minute summary) or jump to individual moments.
5. Each chapter mark includes a 15-second pre-context (starts 15 seconds before the key moment) so Erik sees the build-up.
6. For non-sports content (films, documentaries), chapter marks identify scene breaks, act breaks, and topic transitions rather than highlights.

**Success Criteria:** Chapter marks generated within 30 minutes of recording completion. Sports highlight accuracy: 90%+ of goals, penalties, red cards, and key plays detected. Chapter navigation overlay loads in < 500ms. Highlight summary (all chapters played sequentially) available as a one-click option. Non-sports content: 5-15 chapter marks per hour, aligned with natural scene transitions.

---

### Scenario 8: Auto-Record Based on Learned Preferences (Phase 4)

**Persona:** Erik (Sports Fan)
**Context:** Erik has been using Cloud PVR for 6+ months. The AI has learned that he records all Champions League matches, most Formula 1 qualifying sessions, and tennis Grand Slam finals. He has opted in to "Auto-Record" mode.

**Flow:**
1. Auto-Record is opt-in. Erik enabled it in Settings > PVR > Auto-Record. A toggle and a preferences screen allow him to tune: genres to auto-record, minimum confidence threshold, and maximum auto-recordings per week.
2. The AI detects that the Champions League round-of-16 draw is coming up. New matches will be scheduled. As soon as EPG data for these matches is available, the AI automatically schedules recordings.
3. Erik receives a notification: "Auto-recorded 4 Champions League matches next week (8 hours). Review?" The notification links to a review screen.
4. In the review screen, Erik can cancel individual auto-recordings or approve the batch.
5. If Erik's quota is insufficient, the AI applies Smart Retention rules to suggest deletions before the auto-recordings are confirmed.
6. Auto-Record learns from Erik's behavior: if he cancels Formula 1 practice sessions (but keeps qualifying and races), the AI stops auto-recording practice after 3 cancellations.

**Success Criteria:** Auto-Record suggestions generated within 1 hour of EPG data availability. Suggestion accuracy: 80%+ of auto-recorded items are either watched or retained (not immediately deleted). User can review and cancel auto-recordings before they take effect. Maximum auto-recordings per week: configurable (default 10). Auto-Record respects storage quota -- never over-records.

---

### Scenario 9: Recording Conflict with Catch-Up Overlap

**Persona:** Thomas (Casual Viewer)
**Context:** Thomas attempts to record a program that is also available on Catch-Up. The platform should help him understand his options.

**Flow:**
1. Thomas navigates to the EPG and selects "Record" for a documentary airing tomorrow.
2. The platform detects that this program will also be available on Catch-Up for 7 days after broadcast.
3. An informational message appears: "This program will also be available on Catch-Up for 7 days after it airs. Recording will use 1 hour of your PVR quota (23 hours remaining). Record anyway?"
4. Options: "Record (keep in my library)" or "Don't record (watch on Catch-Up instead)."
5. Thomas chooses to record because he wants to keep it longer than 7 days.
6. For programs NOT available on catch-up, no such message appears -- the recording proceeds without the informational prompt.

**Success Criteria:** Catch-up overlap detection is accurate (checked against rights engine). Message is informational, not blocking -- user always has the choice to record. Storage quota impact is clearly displayed.

---

### Scenario 10: Bulk Recording Management

**Persona:** Priya (Binge Watcher)
**Context:** Priya has 80 recordings accumulated over 3 months. She wants to clean up her library efficiently.

**Flow:**
1. Priya opens "My Recordings" and selects "Manage" (or long-presses to enter management mode).
2. She can sort recordings by: Date (newest/oldest), Title (A-Z), Size (largest/smallest), Watch status (unwatched first), Series grouping.
3. She can filter by: Unwatched, Partially watched, Fully watched, Protected, Series, Movies.
4. She enters multi-select mode and checks 15 fully-watched recordings for deletion.
5. A summary shows: "Delete 15 recordings? This frees 22 hours (30 hours → 52 hours available)."
6. She confirms. Recordings are deleted, and quota is updated immediately.
7. The AI learns from the bulk deletion pattern: Priya deletes fully-watched recordings but keeps partially-watched ones. This informs future Smart Retention suggestions.

**Success Criteria:** Multi-select mode supports selecting 50+ recordings. Bulk delete processes all selected recordings within 5 seconds. Quota update is real-time. Sort and filter operations complete in < 500ms.

---

## 4. Functional Requirements

### 4.1 Recording Scheduling

| Req ID | Description | Priority | Phase | AI Enhancement | Acceptance Criteria |
|--------|-------------|----------|-------|---------------|-------------------|
| PVR-FR-001 | Schedule a single program recording from the EPG, search results, or program detail screen. Recording captures the program from scheduled start to end per EPG metadata. | P0 | 1 | -- | Recording scheduled in < 2 seconds. User receives immediate confirmation with recording details (title, channel, time, estimated storage). Recording icon visible on the program in EPG. |
| PVR-FR-002 | Schedule a series recording (series link): automatically record all future episodes of a series based on series ID from EPG metadata. Options: new only, all, new + repeats. | P0 | 1 | -- | Series link created in < 2 seconds. Future episodes auto-scheduled as EPG data becomes available. Series grouping in library is accurate. Options (new only, etc.) correctly filter recordings. |
| PVR-FR-003 | Record from live: initiate a recording of the currently airing program while watching live (per PRD-001 Scenario 7). Options: "from now," "from beginning" (if start-over buffer available). | P0 | 1 | -- | Recording initiation from live: < 2 seconds. "From beginning" sources content from start-over buffer (PRD-002). Recording continues from live feed for remaining duration. Seamless -- no playback interruption. |
| PVR-FR-004 | Recording padding: configurable start-early and end-late padding per recording or globally. Default: 0 min early, 5 min late. Options: 0/1/5 min early, 0/5/15/30 min late. | P0 | 1 | -- | Padding applied to actual recording capture (not just metadata). Padding time counted against user quota. Per-recording override of global default is supported. |
| PVR-FR-005 | Cancel a scheduled recording: user can cancel a single scheduled recording or an entire series link at any time before the recording starts. | P0 | 1 | -- | Cancellation is immediate. Cancelled recordings are removed from the schedule. Cancelling a series link cancels all future recordings (already-completed recordings remain in library). |
| PVR-FR-006 | Modify a scheduled recording: change padding, keep-until setting, or series link options for an already-scheduled recording. | P1 | 1 | -- | Modifications applied in < 2 seconds. Changes to series link options apply to future episodes only (do not retroactively modify existing recordings). |
| PVR-FR-007 | Recording eligibility: only programs on PVR-enabled channels can be recorded. The "Record" button is not displayed for non-eligible channels/programs. | P0 | 1 | -- | Eligibility checked against rights engine in < 50ms (Redis cache). Non-eligible programs show no "Record" affordance in EPG or program detail. |

### 4.2 Recording Storage and Management

| Req ID | Description | Priority | Phase | AI Enhancement | Acceptance Criteria |
|--------|-------------|----------|-------|---------------|-------------------|
| PVR-FR-010 | Per-user storage quota with real-time tracking. Quota displayed as hours used / hours available. Quota tiers: 50, 100, 200, unlimited (configurable per subscription tier). | P0 | 1 | -- | Quota accuracy: within 1 minute of real-time. Quota visible on: PVR library screen, recording scheduling confirmation, account settings. Quota measured in hours (not GB) for user friendliness. |
| PVR-FR-011 | Quota enforcement: when a new recording would exceed the user's quota, display a warning and options: "Delete recordings to free space" or "Upgrade quota." Recording is blocked until space is available. | P0 | 1 | AI suggests which recordings to delete (see PVR-FR-020) | Warning shown before recording is scheduled (not after). Clear display of: required space, available space, shortfall. "Upgrade" CTA links to subscription management. |
| PVR-FR-012 | Recording library: list all recordings with sort (date, title, size, watch status, series), filter (unwatched, partially watched, fully watched, protected, series/movie), and search. | P0 | 1 | -- | Library loads in < 2 seconds. Supports 500+ recordings per user. Sort and filter: < 500ms. Series grouped with episode count and next-unwatched indicator. |
| PVR-FR-013 | Delete recordings: individual or bulk deletion. Immediate quota reclaim. Confirmation dialog for single delete, summary for bulk delete. | P0 | 1 | -- | Deletion completes in < 2 seconds (single), < 5 seconds (bulk up to 50). Quota updates immediately after deletion. Undo available for 10 seconds after delete (soft delete, then hard delete). |
| PVR-FR-014 | Protect recording: mark a recording as "protected" to prevent auto-deletion and AI cleanup suggestions. Protected recordings require explicit user action to delete. | P0 | 1 | -- | Protection toggle: one press. Protected recordings display a lock icon. Auto-delete policies (when quota-based retention is "Space needed") never remove protected recordings. |
| PVR-FR-015 | Auto-delete policy per recording: "Space needed" (auto-delete oldest unwatched when quota is full) or "I delete" (keep until user manually deletes). Default: "Space needed." | P1 | 1 | -- | Auto-delete removes the oldest "Space needed" recording when the quota is full and a new recording needs space. Auto-delete never removes protected or "I delete" recordings. User notified of auto-deletions: "Deleted: [title] to make room for [new recording]." |
| PVR-FR-016 | Recording detail screen: title, recorded date/time, channel, duration, file size (hours), watch progress, protection status, series info (if applicable), and actions (play, delete, protect, share link). | P1 | 1 | -- | All metadata fields populated from EPG + Recording Service data. Play button positioned prominently. Resume indicator if partially watched. |

### 4.3 Recording Playback

| Req ID | Description | Priority | Phase | AI Enhancement | Acceptance Criteria |
|--------|-------------|----------|-------|---------------|-------------------|
| PVR-FR-020 | Playback of completed recordings with full trick-play: pause, rewind, fast-forward (2x, 4x, 8x, 16x, 32x), scrub with thumbnail preview, skip forward/backward (10s, 30s). | P0 | 1 | -- | Playback starts in < 2 seconds. All trick-play commands respond in < 300ms. Trick-play thumbnails generated from I-frames at 10-second intervals. Skip forward/backward is configurable (10s/30s/60s). |
| PVR-FR-021 | Resume from bookmark: when a user returns to a partially watched recording, playback resumes from the last position with a "Resuming from [time]" indicator. | P0 | 1 | -- | Bookmark accuracy: within 5 seconds. Resume indicator shown for 3 seconds. "Play from beginning" option also available on the detail screen. |
| PVR-FR-022 | Cross-device playback: recordings can be played from any device associated with the user's account. Bookmark syncs across devices within 5 seconds. | P0 | 1 | -- | Recording visible in library on all devices. Bookmark sync latency: < 5 seconds. DRM license acquired per device (same content key, different license). |
| PVR-FR-023 | Multi-audio and subtitle selection during recording playback: same audio/subtitle tracks available as the original live broadcast. | P0 | 1 | -- | All audio and subtitle tracks from the original broadcast are preserved in the recording. Track selection during playback: < 500ms switch time. |
| PVR-FR-024 | Skip intro and skip recap: AI-detected intro and recap markers enable one-press skip at the beginning of episodes. | P2 | 3 | Scene detection model identifies intro/recap sequences by analyzing audio patterns (theme music) and visual patterns (title cards) | Skip intro button appears at the start of the intro sequence. Skip recap button appears at the start of the recap. Both dismiss after the sequence ends if not pressed. Marker accuracy: 90%+ correct within 3 seconds of actual boundary. |
| PVR-FR-025 | Playback of in-progress recordings (Phase 2): start watching a recording that is still being captured (the program is still airing live). Viewer can watch from the beginning while the end is still being recorded. | P2 | 2 | -- | In-progress recording playback starts in < 3 seconds. Viewer has full trick-play within the already-recorded portion. "Jump to Live" is available to skip to the live edge. In-progress status is clearly indicated in the UI. |

### 4.4 Rights and Business Rules

| Req ID | Description | Priority | Phase | AI Enhancement | Acceptance Criteria |
|--------|-------------|----------|-------|---------------|-------------------|
| PVR-FR-030 | Per-channel recording eligibility: each channel has a recording-enabled flag. Recording buttons are only shown for eligible channels. | P0 | 1 | -- | Eligibility data sourced from rights engine (Redis-cached, < 50ms). Non-eligible channels: no "Record" button displayed anywhere. |
| PVR-FR-031 | Per-program recording restrictions: specific programs may be excluded from recording (e.g., pay-per-view events, rights-restricted content). | P1 | 1 | -- | Program-level restrictions override channel-level defaults. Restricted programs display: "Recording not available for this program." |
| PVR-FR-032 | Recording expiry: recordings may expire based on content rights (e.g., 90-day maximum retention for certain content). Expiry date displayed on recording. User notified 7 days before expiry. | P1 | 2 | -- | Expiry date visible on recording detail. Notification sent 7 days and 1 day before expiry. Expired recordings auto-deleted within 24 hours of expiry. |
| PVR-FR-033 | Advertising in recordings: recording manifests include SCTE-35 ad break markers for SSAI. Ad skip policy configurable per channel/operator (no skip, skip after X seconds, free skip). | P1 | 2 | -- | Ad markers preserved from live broadcast in recording. SSAI integration point available for Ad Service. Ad skip policy enforced client-side per operator configuration. |
| PVR-FR-034 | Copy-on-write compliance: in markets where regulations require per-user individual copies (not shared master recordings), the architecture supports per-user recording mode. Configurable per territory. | P1 | 2 | -- | Per-user recording mode: each user's recording is a physically separate copy. Storage ratio drops to 1:1. Mode configurable per territory/operator. Functionality identical from user perspective. |

---

## 5. AI-Specific Features

### 5.1 Smart Recording Suggestions

**Description:** The AI proactively suggests programs for the viewer to record, based on viewing history, genre preferences, recording history, and content signals (trending, new seasons, sports schedules for followed teams). Suggestions are delivered as in-app notification cards and optionally as push notifications.

**Architecture:**
- The Recommendation Service generates recording suggestions per user profile using a model that combines:
  - **Recording history patterns**: genres, channels, and series that the user has previously recorded. Weighted by recency (recent recordings matter more than old ones).
  - **Viewing history (non-recorded)**: programs watched live or on catch-up that the user did NOT record -- a signal of content the user enjoys but may miss in the future.
  - **Content signals**: new seasons of previously recorded series, matches involving followed sports teams (inferred from recording and viewing patterns), high-rating programs in preferred genres.
  - **Temporal signals**: the user's typical recording activity (some users record Sunday night dramas, some record Saturday morning kids content).
- Model: gradient-boosted trees (XGBoost) trained on recording-outcome data (suggested → accepted/rejected → watched/not-watched). Served via KServe (CPU, < 15ms inference).
- Suggestion cadence: evaluated every 12 hours per user, or triggered by new EPG data (7-day forward schedule arrives).
- Suggestions are filtered by: confidence threshold (> 75%), not already scheduled, recording-eligible, user has sufficient quota.
- Delivery: in-app notification card (home screen), optional push notification (mobile, user must opt in), and highlighted programs in EPG with "Suggested for you" badge.

**Acceptance Criteria:**
- [ ] Suggestions delivered at least 12 hours before broadcast when possible
- [ ] Suggestion acceptance rate: > 50% for items above 75% confidence threshold
- [ ] Watch-through rate for accepted suggestions: > 60% (suggestions lead to actual viewing)
- [ ] Maximum 5 suggestions per user per week (frequency cap)
- [ ] Suggestions respect storage quota: never suggest more recordings than the user has space for (unless AI Cleanup is offered simultaneously)
- [ ] One-tap record from suggestion card: < 1 second to schedule
- [ ] Users can disable suggestions entirely or per-genre in settings
- [ ] Suggestion model retrains daily on latest recording-outcome data

### 5.2 AI Smart Retention (Storage Cleanup)

**Description:** When a user's PVR quota approaches capacity (> 80% full) or when a new recording cannot fit, the AI generates a prioritized list of recordings to delete, ranked by how "safe" the deletion is. The AI considers watched status, availability elsewhere, age, user rating, and protection status.

**Architecture:**
- A retention scoring model assigns a "deletability score" (0-100) to each recording per user:
  - **Watched %**: fully watched = +40 points, > 75% watched = +25, > 50% = +10, unwatched = 0
  - **Availability elsewhere**: available on Catch-Up = +15, available on VOD = +15 (stacks: both = +30)
  - **Age**: +1 point per day since recording (max +15)
  - **User signals**: user rated the recording (thumbs up) = -20, user protected it = excluded entirely
  - **Content type**: news/daily content = +10 (typically not re-watched), movies/series = 0
- The scoring model is not ML-based -- it is a configurable rule-based scoring system. This is intentional: storage cleanup decisions must be explainable and predictable. Users should understand WHY a recording is suggested for deletion.
- The scoring is computed on-demand when the user opens the "AI Cleanup" screen or when quota enforcement triggers.
- Each suggestion includes the score components as an explanation: "Fully watched (40pts), available on Catch-Up for 3 more days (15pts), 12 days old (12pts) = 67/100."

**Acceptance Criteria:**
- [ ] AI Cleanup suggestions generated in < 1 second
- [ ] Protected recordings are NEVER suggested for deletion
- [ ] Suggestions are sorted by deletability score (highest first)
- [ ] Each suggestion includes a human-readable explanation
- [ ] 80%+ of users who open AI Cleanup accept at least one suggestion
- [ ] After cleanup, quota is immediately updated
- [ ] AI Cleanup is accessible from: PVR library ("Manage" button), quota warning dialog, and recording scheduling when quota is insufficient

### 5.3 AI Chapter Marks and Highlights (Phase 3)

**Description:** The AI analyzes recorded content to generate navigable chapter marks that allow viewers to skip to specific moments. For sports, this includes goals, penalties, key plays, and other highlights. For non-sports content, this includes scene breaks, act boundaries, and topic transitions.

**Architecture:**
- Chapter mark generation runs as a batch job after recording completion. Processing runs on SageMaker (GPU instances: A10G).
- **Sports highlight detection**: a multimodal model analyzes video frames (detecting scoreboards, celebration scenes, referee actions) and audio (detecting crowd intensity spikes, commentator excitement levels, whistle sounds). Model: fine-tuned CLIP variant + audio classifier, combined via an ensemble.
- **Non-sports chapter detection**: scene detection using visual shot boundary detection (detecting cuts, fades, dissolves) combined with audio silence/music transitions. Groups sequential shots into "chapters" based on narrative flow.
- Processing time: approximately 0.3x real-time (a 2-hour recording processes in ~36 minutes).
- Output: a list of chapter marks per recording, stored in the Recording Service metadata (PostgreSQL). Each mark includes: timestamp, label (e.g., "Goal - 23:15"), type (highlight, chapter, scene), and optional thumbnail.
- Client integration: a chapter navigation overlay accessible from the player scrubber bar. Tapping a chapter mark jumps playback to that position.

**Acceptance Criteria:**
- [ ] Chapter marks generated within 60 minutes of recording completion
- [ ] Sports highlight detection accuracy: 90%+ recall for goals, 85%+ for penalties and red cards
- [ ] Sports false positive rate: < 10% (marks that are not actual key moments)
- [ ] Non-sports chapter detection: 5-15 marks per hour of content, aligned with scene transitions
- [ ] Chapter navigation overlay loads in < 500ms
- [ ] "Watch Highlights" mode plays all chapter marks sequentially with 15-second pre-context per mark
- [ ] Highlight summary duration: < 15% of total recording duration (e.g., 12 minutes for a 90-minute match)

### 5.4 Auto-Record (Phase 4)

**Description:** An advanced opt-in feature where the AI autonomously schedules recordings based on learned user preferences, without requiring the user to browse the EPG or respond to suggestions. The system learns what the user would record and does it automatically, with a review mechanism.

**Architecture:**
- Auto-Record extends the Smart Recording Suggestions model (Section 5.1) with a higher confidence threshold (> 90%) and autonomous action.
- The model learns from 6+ months of recording behavior: which suggestions were accepted, which recordings were watched vs deleted, explicit preferences (genres, channels, series follow).
- Auto-Record runs when new EPG data is available. For each program above the confidence threshold, the system:
  1. Checks quota availability (accounting for all scheduled recordings)
  2. If quota sufficient: schedules the recording automatically
  3. If quota insufficient: applies Smart Retention logic to identify deletable recordings. If sufficient space can be freed: suggests the cleanup + auto-record in a single review notification. If not: queues the suggestion for manual review.
- User controls:
  - Master toggle: Auto-Record on/off
  - Genre filter: include/exclude specific genres
  - Channel filter: include/exclude specific channels
  - Confidence threshold: adjustable (default 90%, range 75-99%)
  - Weekly cap: maximum auto-recordings per week (default 10)
  - Review notification: always sent after auto-recording (user can cancel within 24 hours)

**Acceptance Criteria:**
- [ ] Auto-Record only available to users with 6+ months of recording history
- [ ] Confidence threshold for autonomous action: default 90%
- [ ] Auto-recorded items reviewed by user within 24 hours: user can cancel with one tap
- [ ] 85%+ of auto-recorded items are either watched or retained (not immediately cancelled/deleted)
- [ ] Auto-Record respects storage quota absolutely -- never over-records
- [ ] Weekly cap enforced: default 10, user-configurable (1-20)
- [ ] Cancellation feedback (3+ cancellations for a content type) reduces future confidence for that type
- [ ] Users can see full auto-record history and confidence reasoning in settings

---

## 6. Non-Functional Requirements

### 6.1 Latency

| Requirement | Target | Measurement | Priority |
|-------------|--------|-------------|----------|
| Recording scheduling (user action to confirmation) | < 2 seconds | Client-side telemetry | P0 |
| Recording availability after program end | < 2 minutes | Time from broadcast end to first successful playback of recording | P0 |
| Recording playback start | < 2 seconds (p95) | Client-side telemetry | P0 |
| Trick-play response | < 300ms | Client-side telemetry | P0 |
| Library load (up to 500 recordings) | < 2 seconds | BFF API response + client render | P0 |
| Quota check (on schedule, on delete) | < 500ms | Recording Service API response | P0 |
| AI Cleanup suggestion generation | < 1 second | API response time | P1 |
| AI Recording suggestion delivery | Within 12 hours of EPG data availability | Batch job completion time | P1 |

### 6.2 Availability

| Requirement | Target | Measurement |
|-------------|--------|-------------|
| Recording capture service | 99.95% | Synthetic: scheduled recordings successfully captured |
| Recording playback service | 99.95% | Synthetic: recording playback initiation success rate |
| Scheduled recording accuracy | 99.9% of scheduled recordings captured successfully | Recording success rate metric |
| Recording start accuracy | Within +/- 5 seconds of scheduled time | Measured against EPG schedule time |

### 6.3 Scale

| Requirement | Phase 1 Target | Phase 4 Target | Measurement |
|-------------|---------------|----------------|-------------|
| Concurrent recording captures (platform-wide) | 500 simultaneous recordings | 5,000 | Active recording capture count |
| Concurrent recording playback sessions | 15,000 | 150,000 | Active recording playback sessions |
| Recordings per user (maximum) | 500 | 1,000 | Recording database count per user |
| Total recordings (platform-wide) | 5 million | 50 million | Total recording metadata entries |
| Physical storage (copy-on-write) | 100 TB | 500 TB | S3 storage metrics |
| Logical storage (user-perceived) | 1 PB | 5 PB | Sum of all user quotas used |
| Copy-on-write ratio | 10:1 | 15:1 | Logical / physical storage |

### 6.4 Quality

| Requirement | Target | Measurement |
|-------------|--------|-------------|
| Recording video quality | Same as original broadcast (VMAF > 93 for 1080p HEVC) | VMAF comparison: recording vs live |
| Recording audio quality | Lossless preservation of all audio tracks | Automated audio comparison |
| Rebuffer ratio (recording playback) | < 0.2% | Client-side telemetry (Conviva) |
| Trick-play thumbnail quality | Minimum 360p, 10-second intervals | Thumbnail audit |
| Bookmark accuracy | Within 5 seconds | Bookmark position vs actual stop position |

---

## 7. Technical Considerations

### 7.1 Copy-on-Write Architecture

The core design principle of Cloud PVR is copy-on-write: a single physical recording serves all users who have "recorded" the same program.

**Recording Capture Flow:**
1. When the first user schedules a recording for a specific program (identified by: channel ID + program ID + air date), the Recording Service creates a "master recording" entry in PostgreSQL.
2. At the scheduled time, the Recording Capture Worker (a Go service running on Kubernetes) begins consuming live segments from the packaging engine (USP) for the target channel.
3. Segments are written to S3 under: `s3://pvr/{channel_id}/{date}/{program_id}/`
4. At program end (+ padding), the capture worker stops. A complete manifest is generated and the master recording status is set to "complete."
5. The master recording is a single set of segments on S3, no different from catch-up content (in fact, the same segments can be reused if catch-up is already storing them).

**Per-User Entitlement:**
1. When user A schedules a recording, the Recording Service creates a "user recording" entry: `(user_id, profile_id, master_recording_id, bookmark_position, watch_status, protection, auto_delete_policy)`.
2. If user B also records the same program, a second "user recording" entry is created, pointing to the same `master_recording_id`. No new physical content is stored.
3. When user A plays the recording, the Playback Session Service resolves the user recording → master recording → S3 segments. DRM licenses are issued per user per session.
4. When user A deletes the recording, only the user recording entry is removed. The master recording and its physical segments remain (as long as at least one user recording references them).
5. When the last user recording referencing a master recording is deleted, a garbage collection job removes the physical segments from S3 (after a safety retention period of 7 days).

**Storage Efficiency:**
- If 10,000 users record the same Champions League match (2.5 hours), the physical storage is 2.5 hours (same as 1 user). The 10,000 user recording entries are lightweight metadata rows in PostgreSQL.
- Expected copy-on-write ratio: 10:1 at Phase 1 (popular programs recorded by many users), improving to 15:1 at Phase 4 as the user base grows.
- For programs recorded by only 1 user: ratio is 1:1 (no savings). These are typically niche content with low recording overlap.

### 7.2 Recording Capture Architecture

```
EPG Service (schedule) → Recording Scheduler (K8s CronJob)
                              │
                              ▼
                    Recording Capture Worker (Go)
                              │
                    ┌─────────┴─────────┐
                    │                   │
            Live Segments          S3 Storage
            (from USP/EFS)        (pvr bucket)
                                       │
                                       ▼
                              Master Recording
                              (manifest + segments)
```

**Recording Scheduler:**
- A Kubernetes CronJob that runs every 5 minutes, scanning the recording schedule for recordings that need to start within the next 10 minutes.
- For each pending recording, the scheduler:
  1. Checks if a master recording already exists (another user already scheduled this program). If yes: only creates the user recording pointer.
  2. If no master recording exists: creates one and dispatches a capture job to the Recording Capture Worker pool.

**Recording Capture Worker:**
- A stateless Go service running N replicas (scaled by number of concurrent captures).
- Each worker handles one recording capture at a time.
- Worker consumes live segments from the USP/packaging layer via HTTP (same segments as live/TSTV delivery).
- Segments are written to S3 with the recording's segment naming convention.
- Heartbeats are published to Kafka every 30 seconds for capture monitoring.
- On completion: worker generates the recording manifest, updates the master recording status, publishes `recording.completed` event to Kafka.

**Failover:**
- Each capture worker has a watchdog. If a worker fails mid-capture, the watchdog restarts the capture from the last successfully written segment (segments are immutable on S3, so no corruption risk).
- The Recording Scheduler monitors capture health. If a worker does not heartbeat for 60 seconds, the scheduler reassigns the capture to another worker.

### 7.3 Quota Management

Quota is tracked at the user level in the Recording Service (PostgreSQL + Redis cache):

```
user_quota_hours = SUM(duration_hours) for all user_recordings WHERE user_id = X AND deleted = false
```

- Quota is measured in hours (user-friendly) rather than bytes (varies by quality).
- Hours are calculated from the recording's actual duration (not scheduled duration), which is known after capture completes.
- For scheduled (not yet captured) recordings, the estimated duration from EPG metadata is used for quota projection.
- Quota check is performed:
  - On schedule: before scheduling a new recording
  - On delete: after deleting a recording (to confirm space freed)
  - On UI load: to display current usage
- Redis cache (key: `pvr:quota:{user_id}`) is updated on every recording schedule/delete event. TTL: 5 minutes (refreshed from PostgreSQL periodically).

### 7.4 Integration with TSTV

Cloud PVR and TSTV (PRD-002) share significant infrastructure:

- **Shared segments**: if a channel is both catch-up-enabled and PVR-enabled, the same segments stored for catch-up can be referenced by PVR master recordings. No duplication.
- **"Record from beginning" via start-over buffer**: when a user records a live program "from the beginning" (having already watched part of it live), the segments for the already-aired portion come from the EFS start-over buffer (if still available) or from the S3 catch-up storage (if the ingest-to-catch-up pipeline has already processed them).
- **Cross-service handoff**: the "Record to PVR" button in catch-up browse (PRD-002) creates a user recording pointer to the catch-up master recording, extending its retention beyond the 7-day catch-up window.

### 7.5 DRM for Recordings

- Recordings use the same CBCS encryption as live content. Content keys are per-channel per-day (rotated daily for live).
- For recordings that span a key rotation boundary (e.g., a program recorded across midnight), the manifest includes key period metadata so the player can acquire both keys.
- DRM licenses for recording playback are standard license requests to the DRM backend. No special recording-specific DRM workflow.
- Offline playback of recordings (Phase 3): would require an offline license with extended expiry (48 hours), issued at download time.

---

## 8. Dependencies

### 8.1 Service Dependencies

| Dependency | Service | PRD Reference | Dependency Type | Impact if Unavailable |
|------------|---------|---------------|-----------------|----------------------|
| Program schedule | EPG Service | PRD-005 | Hard | Cannot schedule recordings (no program data). Cannot determine recording boundaries. Service is non-functional for scheduling. |
| Live feed segments | Live TV packaging (USP) | PRD-001 | Hard | Cannot capture recordings. Playback of existing recordings is unaffected. |
| Start-over buffer (for "record from beginning") | TSTV Service | PRD-002 | Soft | "Record from beginning" falls back to "record from now." Standard recording unaffected. |
| Content rights | Rights Engine / Entitlement Service | ARCH-001 | Hard | Cannot verify recording eligibility. Fail-closed: recording buttons hidden. Playback of existing recordings unaffected. |
| User profile and auth | Auth/Profile Service | ARCH-001 | Hard | Cannot identify user or manage per-user recordings. |
| Bookmark sync | Bookmark Service | ARCH-001 | Soft | Bookmarks not saved/synced. Playback still works but no cross-device resume. |
| AI recommendations | Recommendation Service | PRD-007 | Soft | AI recording suggestions suspended. Smart Retention works (rule-based, not ML-dependent). |
| CDN delivery | Multi-CDN + CAT | ARCH-001 | Hard | Cannot deliver recording segments. Playback unavailable. |
| Storage (S3) | AWS S3 | ARCH-001 | Hard | Cannot write recordings or serve segments. Total PVR outage. |
| AI/ML inference | KServe | ARCH-001 | Soft | AI suggestions and chapter marks unavailable. Core recording/playback unaffected. |

### 8.2 Infrastructure Dependencies

| Dependency | Component | Impact if Unavailable |
|------------|-----------|----------------------|
| PostgreSQL (Recording DB) | RDS | Cannot schedule or query recordings. Total PVR outage. |
| Redis (quota cache, metadata cache) | ElastiCache | Slower quota checks and library loads. Falls back to PostgreSQL reads. Functional but degraded. |
| Kafka | Event bus | Recording events not published. AI features degrade. Capture monitoring delayed. Core recording capture unaffected (workers operate independently). |
| GPU (SageMaker) | Compute | Chapter marks and highlights not generated. Core recording unaffected. |

---

## 9. Success Metrics

| # | Metric | Baseline (Industry) | Phase 1 Target | Phase 2 Target | Phase 4 Target | Measurement Method |
|---|--------|--------------------|--------------|--------------|--------------|--------------------|
| 1 | PVR adoption (% of subscribers with at least 1 recording) | 30-40% | 35% | 50% | 65% | Users with active recordings / total subscribers |
| 2 | Recordings per active PVR user per month | 8-12 | 10 | 15 | 25 | Average recording count (includes AI-suggested and auto-recorded) |
| 3 | AI suggestion acceptance rate | N/A | 50% | 55% | 65% | Accepted suggestions / total suggestions delivered |
| 4 | AI suggestion watch-through rate | N/A | 60% | 65% | 75% | Accepted suggestions watched > 50% / total accepted |
| 5 | Recording capture success rate | 98-99% | 99.5% | 99.8% | 99.9% | Successfully captured recordings / total scheduled |
| 6 | Recording availability time (after program end) | 5-15 minutes | < 2 minutes | < 1 minute | < 30 seconds | Time from broadcast end to first playback |
| 7 | Copy-on-write storage ratio | 5:1 (industry) | 10:1 | 12:1 | 15:1 | Logical user storage / physical S3 storage |
| 8 | AI Cleanup adoption (% of quota-constrained users who use it) | N/A | 40% | 55% | 70% | Users who opened AI Cleanup and deleted ≥ 1 suggestion / users who hit quota warning |
| 9 | PVR user churn delta | -25% (industry: PVR users churn 25% less) | -25% | -30% | -35% | Churn rate of PVR users vs non-PVR users |
| 10 | Chapter mark usage (Phase 3) | N/A | N/A | 20% of sports recording plays use chapter navigation | 35% | Plays with chapter mark interactions / total plays of recordings with chapter marks |

---

## 10. Open Questions & Risks

### Open Questions

| # | Question | Owner | Impact | Target Resolution |
|---|----------|-------|--------|-------------------|
| 1 | What is the regulatory requirement for individual copies vs copy-on-write in the target market? Some jurisdictions (e.g., parts of Europe) require per-user individual copies for Cloud PVR, significantly increasing storage costs. | Legal | Storage cost (1:1 vs 10:1), architecture | Pre-launch legal review. Build the architecture to support both modes from Phase 1, configured per territory. |
| 2 | Should recordings be playable while still in progress (live-tail)? This would allow a user to start watching a recording 30 minutes after it started, while the rest is still being captured. | Product Manager | UX, engineering complexity | Phase 2 feature planning. Technically feasible (progressive manifest), adds complexity to the playback session. |
| 3 | What happens when a user with 100 recordings downgrades their subscription to a tier with fewer hours? Are recordings deleted, locked (view but cannot add), or grandfathered? | Product / Business | UX, business rules | Phase 1 business rules. Recommendation: lock (cannot add new recordings, existing recordings accessible until user deletes them). |
| 4 | Should AI auto-record suggestions count toward the weekly suggestion cap of the Smart Recording Suggestions feature, or have a separate cap? | Product Manager | UX, notification fatigue | Phase 2 planning. Recommendation: separate caps (5 suggestions + 10 auto-records per week maximum). |
| 5 | What is the maximum recording retention? Should recordings persist indefinitely (as long as the user's subscription is active) or expire after a set period (e.g., 12 months)? | Business / Legal | Storage cost, content rights | Pre-launch rights negotiation. Content rights may impose maximum retention. Default: indefinite (user-managed). Per-content expiry as override. |
| 6 | How should Cloud PVR storage be priced? Per-hour-per-month? Tiered bundles? Pay-per-use? | Business | Revenue model | Business case development. Recommendation: tiered bundles (50h included in base, 100h/200h/unlimited as add-ons) for simplicity. |

### Risks

| # | Risk | Severity | Likelihood | Mitigation |
|---|------|----------|------------|------------|
| 1 | **Storage cost escalation**: even with copy-on-write, storage grows linearly with content catalog and user base. At 500K users with 100-hour quotas, logical storage is 50M hours. | High | High | Copy-on-write targets 10-15:1 ratio, meaning 3.3-5M physical hours. Use S3 Intelligent-Tiering. Implement per-title encoding optimization (Phase 2) to reduce per-hour storage. Archive older segments to S3 Glacier after 90 days (infrequently accessed). Target: < $0.005 per user per hour per month. |
| 2 | **Recording capture failures during high-demand events**: when a major event (World Cup final) triggers 100K+ simultaneous recordings, the capture worker pool may be overwhelmed. | High | Medium | Copy-on-write means 100K users = 1 physical capture (per channel). The risk is if many different programs across many channels are recorded simultaneously. Pre-scale capture workers for known events. Monitor scheduling queue depth. Alert when queue exceeds 2x normal. |
| 3 | **AI recording suggestions fatigue**: if suggestions are irrelevant or too frequent, users will disable the feature, losing the AI engagement advantage. | Medium | Medium | Conservative confidence threshold (75%). Frequency cap (5/week). Track dismiss rates -- if a user dismisses 5 consecutive suggestions, pause suggestions for 2 weeks and notify: "We've paused recording suggestions. Re-enable anytime in Settings." |
| 4 | **Rights complexity for copy-on-write**: content providers may challenge the legal basis of shared master recordings in certain jurisdictions, arguing each user must have an individual copy. | High | Medium | Design architecture to support per-user copies from day 1 (configurable per territory). Engage legal counsel for each target market before launch. Budget for 1:1 storage in regulated markets. |
| 5 | **Quota gaming**: users may attempt to maximize value by scheduling many recordings and never deleting, or by recording content they have no intention of watching just to "have it." | Low | Medium | Quota limits provide natural constraint. Auto-delete policy ("Space needed") reclaims space for inactive recordings. Monitor recording-to-watch ratio as a health metric. No engineering mitigation needed for Phase 1 -- this is acceptable user behavior within quota limits. |
| 6 | **Chapter mark/highlight inaccuracy for sports**: if the AI misses a goal or marks a non-event as a highlight, it damages trust in the feature. Sports fans are particularly sensitive to this. | Medium | Medium | Set a high recall target (90%) and accept moderate precision (some false positives are less damaging than missed highlights). Allow user feedback ("This was not a highlight" / "Missed a moment") to improve the model. Clearly label as "AI-generated" highlights. |
| 7 | **Auto-Record (Phase 4) records unwanted content**: autonomous recording that fills the user's quota with unwanted content is a significant UX risk. | Medium | Medium | Mandatory 24-hour review window. High confidence threshold (90%). Weekly cap (10). Easy bulk cancel. If cancellation rate exceeds 30%, automatically downgrade to suggestion-only mode for that user. |

---

*This PRD defines the Cloud PVR service for the AI-native OTT streaming platform. It should be read alongside PRD-001 (Live TV) for recording capture integration, PRD-002 (TSTV) for shared infrastructure and catch-up overlap, PRD-005 (EPG) for recording scheduling, and PRD-007 (AI User Experience) for the recommendation and intelligence capabilities that power AI recording suggestions and smart retention.*
