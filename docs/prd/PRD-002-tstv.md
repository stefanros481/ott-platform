# PRD-002: Time-Shifted TV (Start Over & Catch-Up)
## AI-Native OTT Streaming Platform

**Document ID:** PRD-002
**Version:** 1.2
**Date:** 2026-02-24
**Status:** Draft — Updated for PoC implementation
**Author:** PRD Writer A
**References:** VIS-001 (Project Vision & Design), ARCH-001 (Platform Architecture), PRD-001 (Live TV)
**Stakeholders:** Product Management, Engineering (Platform, Client, AI/ML), Content Operations, Content Rights, SRE

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

Time-Shifted TV (TSTV) enables viewers to break free from the broadcast schedule through two complementary capabilities:

- **Start Over TV**: Allows a viewer who tunes into a currently airing program to restart it from the beginning. The transition from live to start-over is seamless -- no re-authentication, no new session creation, no perceptible interruption. The viewer gains full trick-play (pause, rewind, fast-forward) and can jump back to the live edge at any time.

- **Catch-Up TV**: Provides access to previously aired programs within a configurable rolling window (default: 7 days). Viewers can browse and play back any eligible program that aired in the past week, organized by channel, date, genre, or AI-curated personalized feeds. Catch-up content is stored as recorded segments at the origin, with program boundaries defined by EPG metadata.

TSTV is the bridge between live and on-demand viewing. It converts the rigid broadcast schedule into a flexible library of recently aired content, significantly increasing the utility of linear channels and reducing the primary frustration of live TV: "I missed it."

### Business Context

Time-shifted viewing accounts for 25-35% of total TV consumption in mature markets and is growing annually as viewer expectations shift toward on-demand flexibility. For operators, TSTV is a critical differentiator:

1. **Retention lever**: TSTV reduces the perceived cost of missing live programs, addressing a top churn driver ("I never get to watch what I want when it airs").
2. **Engagement multiplier**: Content that would otherwise be "lost" after broadcast becomes accessible for 7 days, increasing total viewing hours per subscriber by 15-25%.
3. **AI training ground**: Catch-up viewing patterns provide explicit signals about viewer preferences (what they choose to watch after the fact, as opposed to what they passively leave on live), which are high-quality training data for the recommendation engine.
4. **Upsell opportunity**: Catch-Up TV can be tiered -- basic (3 days) vs premium (7 days) -- creating upgrade paths.

### Scope

**In Scope:**
- Start Over TV: restarting a currently airing program from the beginning
- Catch-Up TV: browsing and playing previously aired programs (7-day rolling window)
- Content rights management for start-over and catch-up eligibility (per-channel, per-program, per-territory)
- Full trick-play for time-shifted content (pause, rewind, fast-forward, skip)
- Bookmarking and resume for time-shifted content across devices
- AI-powered catch-up discovery and personalized recommendations
- Integration with Live TV (PRD-001) for seamless live-to-start-over transitions
- Integration with EPG (PRD-005) for program metadata and browsing
- Integration with Cloud PVR (PRD-003) for "record for later" from catch-up browse

**Out of Scope:**
- Cloud PVR recording functionality (PRD-003)
- Downloading catch-up content for offline playback (Phase 3+ consideration)
- TSTV for FAST channels (separate scope)
- Extended catch-up windows beyond 7 days (operator-specific, Phase 2+ configuration)
- Live-to-VOD clipping and publishing (content operations workflow)

---

## 2. Goals & Non-Goals

### Goals

1. **Provide seamless Start Over initiation in < 3 seconds** from user action to playback of the program's start, with no re-authentication or session restart required.
2. **Make Catch-Up content available within 5 minutes of broadcast end**, enabling near-immediate access to recently aired programs.
3. **Support a 7-day rolling catch-up window** as the default, with per-channel and per-program configurability to accommodate content rights variations.
4. **AI-enhance catch-up discovery** with personalized "Your Catch-Up" feeds, "You Missed This" notifications, and AI-generated program summaries so viewers find relevant content without manual EPG browsing.
5. **Enable full trick-play** (pause, rewind, fast-forward at multiple speeds, skip) for all start-over and catch-up content, matching the VOD playback experience.
6. **Maintain content rights compliance** with per-program, per-channel, per-territory granularity for both start-over and catch-up eligibility, including programs excluded from time-shifting by rights holders.
7. **Support cross-device bookmarking** so a viewer who starts watching a catch-up program on one device can resume on another within 5 seconds of accuracy.
8. **Integrate AI-powered predictive cache warming** to pre-populate CDN caches with catch-up content predicted to be popular, reducing origin load and improving start times.

### Non-Goals

1. **Replacing Cloud PVR**: TSTV provides ephemeral access (content expires after the rolling window). Cloud PVR provides persistent recordings per user. They are complementary services.
2. **Extended archives**: Retaining content beyond the 7-day window is a distinct product (library/archive). This PRD covers the rolling window only.
3. **Editorial catch-up curation**: Manual editorial curation of catch-up highlights is a content operations function. This PRD covers AI-automated curation.
4. **Ad insertion in catch-up**: Server-side ad insertion (SSAI) for catch-up content is a monetization function covered in the Ad Service scope. This PRD ensures the manifest structure supports ad marker insertion.
5. **Live simulcast**: TSTV is about time-shifting existing linear channels, not creating new linear streams from VOD content.

---

## 3. User Scenarios

### Scenario 1: Proactive Start Over Suggestion

**Persona:** Erik (Sports Fan)
**Context:** Erik tunes into Channel 5 at 20:23. A Champions League match started at 20:00.

**Flow:**
1. Erik selects Channel 5. The live stream starts immediately (within 1.5s per PRD-001).
2. The platform detects that Erik tuned in 23 minutes after the program started. An overlay appears within 2 seconds of tune-in: "Champions League: Real Madrid vs Bayern Munich started 23 min ago. Start from the beginning?"
3. The overlay offers two buttons: "Start from Beginning" and "Continue Live."
4. Erik selects "Start from Beginning." Playback transitions to the program's start point within 3 seconds. A "LIVE" badge is replaced by a "START OVER" badge. A scrubber bar shows his position relative to the live edge.
5. Erik has full trick-play: he can fast-forward (2x, 4x, 8x) to catch up, pause, or rewind.
6. At any point, Erik presses "Jump to Live" to return to the live edge within 1 second.
7. During fast-forward, Erik sees trick-play thumbnails (I-frame snapshots) to help navigate.

**Success Criteria:** Start Over overlay appears within 2 seconds of late tune-in. Transition to start-over playback completes in < 3 seconds. Trick-play is fully functional. Jump to Live completes in < 1 second.

---

### Scenario 2: Catch-Up Browse by Channel and Date

**Persona:** Maria (Busy Professional)
**Context:** Maria wants to watch a documentary that aired on Channel 12 last Tuesday evening. She did not record it.

**Flow:**
1. Maria navigates to the EPG (PRD-005) and selects the "Catch-Up" tab, or navigates to a dedicated "Catch-Up" section of the app.
2. She selects Channel 12, then scrolls to Tuesday's schedule.
3. The schedule shows all programs from Tuesday with their broadcast times, titles, descriptions, and availability status (available, expired, not eligible).
4. She finds "Planet Earth: Deep Ocean" (aired 21:00-22:00). The listing shows: duration (58 min), catch-up expiry date (next Tuesday), and a play button.
5. She presses play. The catch-up program starts within 2 seconds. She has full trick-play capability.
6. After watching 30 minutes, Maria pauses and switches to the VOD section to check something. When she returns to the catch-up section, a "Resume" indicator shows on the program: "Continue from 30:12."
7. The next day, Maria opens the app on her phone. "Continue Watching" shows the catch-up documentary with her bookmark position. She resumes on her phone, exactly where she left off on the TV.

**Success Criteria:** Catch-up schedule loads in < 2 seconds. Programs display accurate availability status. Playback starts in < 2 seconds. Bookmark syncs across devices within 5 seconds.

---

### Scenario 3: AI-Curated "Your Catch-Up" Feed

**Persona:** The Okafor Family (Amara)
**Context:** Amara opens the app on Saturday afternoon. She does not know what aired during the week that she might like.

**Flow:**
1. On the home screen, Amara sees a "Your Catch-Up" rail. The rail is personalized for her profile and shows programs from the past 7 days that the AI predicts she would enjoy, regardless of channel.
2. The rail shows: "MasterChef: Season 8 Ep 4" (aired Wednesday, Channel 21), "The Great British Bake Off" (aired Friday, Channel 14), "Nature's Wonders: Amazon" (aired Thursday, Channel 12), and "Interior Design Masters" (aired Tuesday, Channel 28).
3. Each item shows: thumbnail, program title, channel, air date, duration, and a match score badge ("95% match").
4. Amara selects "MasterChef." A detail card shows: AI-generated summary (2-3 sentences), air date and time, channel, catch-up expiry date, and actions (Play, Record to PVR, Add to Watchlist).
5. She presses Play and watches the episode. After finishing, the platform suggests: "Also from this week: Great British Bake Off, Friday on Channel 14."

**Success Criteria:** "Your Catch-Up" rail populated with 10+ personalized suggestions. Recommendations reflect profile-level preferences (not household-level). Match score accuracy: 70%+ of clicked items are watched for > 50% of their duration.

---

### Scenario 4: "You Missed This" Notification

**Persona:** Erik (Sports Fan)
**Context:** Erik's favorite team played on Wednesday evening, but Erik was at a dinner and missed the match entirely.

**Flow:**
1. On Thursday morning, Erik opens the app. A notification is visible (both as an in-app notification and optionally a push notification sent the previous evening): "You missed: Champions League - Liverpool vs PSG (3-2). Available on Catch-Up for 6 more days."
2. The notification includes: match result (configurable: some users want spoiler-free, in which case the score is hidden), a "Watch Now" button, and a "Watch Highlights" button (Phase 3, AI-generated highlights per PRD-003).
3. Erik selects "Watch Now." The catch-up program starts from the beginning.
4. During playback, Erik uses fast-forward to skip through halftime. The trick-play thumbnails help him navigate to the second half kick-off.

**Success Criteria:** "You Missed This" notification sent within 2 hours of broadcast end for programs matching the user's interests (determined by Recommendation Service, confidence > 80%). Spoiler preferences respected. Notification frequency capped at maximum 3 per day to avoid fatigue.

---

### Scenario 5: Catch-Up Expiry Handling

**Persona:** Priya (Binge Watcher)
**Context:** Priya has been catching up on a weekly drama series via catch-up. The oldest episode in the 7-day window is about to expire.

**Flow:**
1. In the Catch-Up section, episodes display their expiry date. Episode 1 (aired 7 days ago) shows: "Expires today at 21:00."
2. A notification was sent 24 hours before expiry: "Episode 1 of The Bridge expires tomorrow. Watch now or record to keep it."
3. Priya selects the episode. A banner at the top of the detail card reads: "Expires in 3 hours."
4. The play button and a "Record to PVR" button are both prominently displayed. If Priya records it, the content is preserved in her Cloud PVR (PRD-003) and no longer subject to the catch-up expiry.
5. After expiry, the episode disappears from the catch-up catalog. If Priya tries to access a direct link, she sees: "This program is no longer available on Catch-Up. Available on demand?" (if a VOD version exists, a link is provided).

**Success Criteria:** Expiry date displayed on all catch-up content. Expiry notification sent 24 hours before. Expired content removed within 5 minutes of expiry time. Cross-service handoff to VOD or PVR is seamless.

---

### Scenario 6: Start Over with Catch-Up to Live

**Persona:** Thomas (Casual Viewer)
**Context:** Thomas is watching a movie that started 45 minutes ago using Start Over. He has been watching for 20 minutes (at the 20-minute mark of the film). He decides he wants to skip ahead to see "what's happening now."

**Flow:**
1. Thomas is watching in Start Over mode at position 20:00 (live is at 65:00).
2. He presses "Jump to Live." Playback jumps to the current live position (65:00) within 1 second. The "START OVER" badge transitions to "LIVE."
3. Later, Thomas wants to go back to where he was. He rewinds. The scrubber shows the full buffer from program start (0:00) to live edge. He scrubs back to approximately 20:00.
4. Thomas can freely navigate between any point from the program start to the live edge, with the same fluidity as a recorded video.

**Success Criteria:** Transition between start-over and live is seamless (< 1 second). Full scrub range from program start to live edge is available. No rebuffer events during time position jumps of < 30 seconds.

---

### Scenario 7: Rights-Restricted Content

**Persona:** System scenario
**Context:** A premium movie channel has agreed to catch-up rights for its original productions but not for licensed Hollywood films. A sports channel has no start-over rights for certain football leagues due to territorial rights restrictions.

**Flow:**
1. On Channel 87 (Premium Film), the original series "Dark Matter" is eligible for both start-over and 7-day catch-up. The movie "Inception" (licensed) is not eligible for either.
2. When a viewer tunes into "Inception" 30 minutes late, no Start Over overlay appears. The program listing in catch-up shows "Inception" with a lock icon and "Not available on Catch-Up" label.
3. On Channel 5 (Sports), the Champions League match is eligible for start-over but only 24-hour catch-up (instead of 7 days) due to rights restrictions. The EPG and catch-up listing reflect this shorter window.
4. The rights engine evaluates eligibility per content item (identified by program ID from EPG), per channel, per territory, checking: start-over rights flag, catch-up window duration (0, 24h, 48h, 72h, 7 days), and territory allowlist/blocklist.

**Success Criteria:** Rights correctly enforced per program with zero unauthorized access. Rights evaluated in < 50ms (cached in Redis, sourced from Rights Service). Non-eligible content clearly marked (lock icon + reason). No metadata leakage for fully restricted content (title and description may still be shown for marketing purposes, per operator configuration).

---

### Scenario 8: Catch-Up Content Search

**Persona:** Maria (Busy Professional)
**Context:** Maria heard a colleague mention a documentary that aired sometime last week but cannot remember the exact channel or day.

**Flow:**
1. Maria opens the search feature (within the catch-up section or global search) and types "ocean documentary."
2. Search results include both VOD content and catch-up content, clearly labeled. Catch-up results show: "Planet Earth: Deep Ocean" (Channel 12, aired Tuesday 21:00, catch-up expires in 5 days) and "Blue Planet Live" (Channel 9, aired Saturday 20:00, catch-up expires in 2 days).
3. Results are ranked by AI-assessed relevance combining: text match, user preference alignment, recency, and catch-up expiry (items expiring soon are slightly boosted to create urgency).
4. Maria selects "Planet Earth: Deep Ocean" and starts playing directly from the search results.

**Success Criteria:** Search returns relevant catch-up results within 500ms. Results clearly differentiate catch-up from VOD content. Expiry information is visible in search results. Search covers program title, description, and AI-enriched tags (mood, themes, keywords).

---

### Scenario 9: Catch-Up Trending Content

**Persona:** Thomas (Casual Viewer)
**Context:** Thomas wants to watch "what everyone else watched this week" without browsing individual channels.

**Flow:**
1. Thomas navigates to the Catch-Up section and sees a "Trending This Week" rail.
2. The rail shows the most-watched catch-up programs from the past 7 days, ranked by unique viewers in catch-up mode (not live viewers, specifically time-shifted viewers).
3. Items are diverse: news specials, sports highlights, drama finales, documentaries. The mix is not purely popularity-driven; diversity injection ensures variety across genres.
4. Thomas selects a nature documentary at position 3. It plays immediately.

**Success Criteria:** "Trending This Week" rail updates daily. Ranking based on actual catch-up viewership data. Minimum 3 genres represented in the top 10. Data freshness: trending data includes catch-up views from up to 2 hours ago.

---

### Scenario 10: Multi-Program Binge in Catch-Up

**Persona:** Priya (Binge Watcher)
**Context:** Priya discovers that 4 episodes of a weekly series are available on catch-up. She wants to binge-watch them in order.

**Flow:**
1. Priya finds "The Bridge - Season 4" in catch-up. Episodes 1-4 are available (aired over the past 4 weeks, but earlier episodes still within the 7-day rolling window due to repeat broadcasts or extended catch-up rights).
2. She selects Episode 1. After the episode finishes, auto-play (configurable, see PRD-004 binge mode) offers to play Episode 2 with a 15-second countdown.
3. Between episodes, the AI notes: "Episode 1 catch-up expires tomorrow. Record the rest to your PVR? One tap to record Episodes 2-4."
4. Skip intro and skip recap are available if AI-detected markers exist for the content (Phase 3, per PRD-007 AI UX).
5. After Episode 4, the platform suggests: "New episode airs Wednesday at 21:00 on Channel 22. Set a reminder?"

**Success Criteria:** Auto-play next episode works seamlessly across catch-up content. Episode ordering is correct (chronological by air date). PVR recording suggestion appears when catch-up expiry is within 48 hours. Reminder setting handoff to Schedule Service (PRD-005) is functional.

---

## 4. Functional Requirements

### 4.1 Start Over TV

| Req ID | Description | Priority | Phase | AI Enhancement | Acceptance Criteria |
|--------|-------------|----------|-------|---------------|-------------------|
| TSTV-FR-001 | When a viewer tunes to a live channel and the current program started more than 3 minutes ago, display a Start Over prompt offering to restart the program from the beginning | P0 | 1 | AI auto-detects late tune-in and proactively offers restart | Prompt appears within 2 seconds of tune-in. Only shown if the program has start-over rights. Prompt auto-dismisses after 10 seconds if no action taken. Does not reappear for the same program during the same session. |
| TSTV-FR-002 | Start Over playback: transition from live to the program's start point with full trick-play, within 3 seconds of user action, without re-authentication or new session creation | P0 | 1 | -- | Transition completes in < 3 seconds (p95). Same DRM session is reused. Playback position indicator shows "START OVER" badge and relative position to live edge. No audio/video glitch during transition. |
| TSTV-FR-003 | Full trick-play during Start Over: pause, rewind (2x, 4x, 8x, 16x, 32x), fast-forward (2x, 4x, 8x), and scrub bar with thumbnail preview | P0 | 1 | -- | Trick-play commands execute in < 300ms. Fast-forward is available up to (but not past) the live edge. Rewind is available to the program start. Trick-play thumbnails generated from I-frames at 10-second intervals. |
| TSTV-FR-004 | "Jump to Live" button always visible during Start Over. One press returns to the current live broadcast position. | P0 | 1 | -- | Jump to Live completes in < 1 second. Button is visually prominent (not buried in a menu). Transitions smoothly from start-over scrubber to live indicator. |
| TSTV-FR-005 | Start Over rights enforcement: per-program, per-channel eligibility check. Programs without start-over rights do not display the Start Over prompt. | P0 | 1 | -- | Rights check completes in < 50ms (Redis cache). Rights data sourced from EPG Service program metadata (field: `start_over_enabled`). |
| TSTV-FR-006 | Bookmark persistence during Start Over: if a viewer leaves mid-program during start-over, the position is saved and displayed as a resume point when the viewer returns (within the catch-up window) | P1 | 1 | -- | Bookmark saved within 5 seconds of playback stop. Resume indicator appears on the program in EPG and catch-up listings. Cross-device bookmark sync within 5 seconds. |
| TSTV-FR-007 | AI-enhanced Start Over suggestion: rather than a generic "Start from beginning?" prompt, the AI provides context-aware messaging. For sports: "Match started 23 min ago, current score: 1-0. Start from kick-off?" For series: "Episode 3 of The Bridge is 15 min in. Start from the beginning?" | P1 | 2 | Recommendation Service provides contextual metadata and the EPG Service provides program type classification | Context-aware messaging for 3+ content categories (sports, series, film, news). Sports scores displayed only if the user's spoiler preference allows it. Confidence in content type classification > 90%. |

### 4.2 Catch-Up TV

| Req ID | Description | Priority | Phase | AI Enhancement | Acceptance Criteria |
|--------|-------------|----------|-------|---------------|-------------------|
| TSTV-FR-010 | Catch-Up catalog: provide access to all eligible programs that aired within the rolling window (default 7 days, configurable per channel: 0/24h/48h/72h/7 days) | P0 | 1 | -- | Catalog updated within 5 minutes of each program's broadcast end. Catalog accurately reflects per-program rights and window duration. Programs beyond their catch-up window are automatically removed within 5 minutes of expiry. |
| TSTV-FR-011 | Browse Catch-Up by channel: select a channel, see all available catch-up programs organized by date (most recent first), with program title, time, duration, and availability status | P0 | 1 | -- | Channel-based browse loads in < 2 seconds. Displays up to 7 days of schedule per channel. Each program shows: title, start time, duration, catch-up expiry, play/resume button. |
| TSTV-FR-012 | Browse Catch-Up by date: select a date and see all available programs across all channels for that date, filterable by genre and channel | P1 | 1 | -- | Date-based browse loads in < 2 seconds. Supports 7 days backward. Filters: genre (Sports, News, Entertainment, Kids, Documentary, Film, Music), channel, and duration. |
| TSTV-FR-013 | Catch-Up playback: select a program from the catch-up catalog and start playback with full trick-play capability | P0 | 1 | -- | Playback starts in < 2 seconds (p95). Full trick-play: pause, rewind, fast-forward (2x, 4x, 8x, 16x, 32x), scrub with thumbnail preview. Behavior identical to VOD playback experience. |
| TSTV-FR-014 | Catch-Up content expiry management: display expiry date on all catch-up listings, send notification 24 hours before expiry for programs the user has started or bookmarked, and offer "Record to PVR" as alternative | P0 | 1 | -- | Expiry date visible in all catch-up browse views (channel, date, search, AI rails). Notification sent 24 hours before expiry for in-progress programs. "Record to PVR" button available on content detail if user has Cloud PVR entitlement. |
| TSTV-FR-015 | Catch-Up search: allow text search across the catch-up catalog (title, description, AI-enriched tags), with results clearly labeled as catch-up content alongside VOD results | P0 | 1 | -- | Search results return in < 500ms. Catch-up results include: source channel, air date/time, duration, expiry, availability status. Results ranked by relevance (text match + recency + AI affinity). |
| TSTV-FR-016 | Catch-Up cross-device resume: bookmarks for catch-up programs sync across all user devices. Resume position is accurate to within 5 seconds. | P0 | 1 | -- | Bookmark sync latency: < 5 seconds. Position accuracy: within 5 seconds of actual stop point. Resume works across devices (TV -> phone, phone -> tablet, etc.). Bookmark persists until content expires. |
| TSTV-FR-017 | Auto-play next episode for series in catch-up: when a viewer finishes one episode of a series, auto-offer the next episode (if available on catch-up) with a configurable countdown (default 15 seconds) | P1 | 2 | AI determines optimal countdown duration and whether to suggest the next catch-up episode or recommend a different program | Auto-play only triggers for sequential content (series episodes). Countdown is configurable by the user (5s, 10s, 15s, 30s, off). AI may override to suggest a different program if the next episode has low predicted engagement for the user. |

### 4.3 Content Rights and Availability

| Req ID | Description | Priority | Phase | AI Enhancement | Acceptance Criteria |
|--------|-------------|----------|-------|---------------|-------------------|
| TSTV-FR-020 | Per-program rights management: each program has individual start-over and catch-up eligibility flags, controlled by the content rights system | P0 | 1 | -- | Rights flags sourced from EPG Service metadata. Fields: `start_over_enabled` (bool), `catch_up_window_hours` (int: 0, 24, 48, 72, 168). Rights evaluated per program ID per channel ID per territory. |
| TSTV-FR-021 | Per-channel rights defaults: channels have default TSTV rights that apply to all programs unless overridden at the program level | P0 | 1 | -- | Channel-level defaults configurable by content operations. Program-level overrides take precedence. Default propagation: new programs on a catch-up-enabled channel automatically inherit the channel's catch-up window. |
| TSTV-FR-022 | Territory-based rights: TSTV rights may vary by geographic territory. A program available for catch-up in one territory may not be in another. | P1 | 1 | -- | Territory determined by user's account region (not IP geo-location, which can be VPN-affected). Rights evaluated as: program rights AND channel rights AND territory rights. |
| TSTV-FR-023 | Rights changes during window: if rights are revoked for a program during its catch-up window (e.g., content provider pulls the rights), the program is removed from the catch-up catalog within 15 minutes | P1 | 1 | -- | Active playback sessions for revoked content are allowed to complete (do not terminate mid-playback). New play requests are denied. Program removed from browse and search within 15 minutes of rights revocation event. |
| TSTV-FR-024 | Advertising rules for catch-up content: support ad marker insertion points (SCTE-35 or equivalent) in catch-up manifests for SSAI integration. Ad policy (pre-roll, mid-roll, no-skip, skippable) is configurable per channel and per program. | P1 | 2 | -- | Manifest includes ad break markers for SSAI. Ad policy metadata available per program. Actual ad insertion is handled by the Ad Service (out of this PRD's scope). |

### 4.4 Bookmarking and Continue Watching

| Req ID | Description | Priority | Phase | AI Enhancement | Acceptance Criteria |
|--------|-------------|----------|-------|---------------|-------------------|
| TSTV-FR-030 | Automatic bookmarking: player position is saved every 30 seconds during start-over and catch-up playback, and on stop/pause events | P0 | 1 | -- | Bookmark updates sent to Bookmark Service (Go, p99 < 50ms) via playback heartbeat. Bookmark position accurate to within 5 seconds. Stored per user profile, per program instance (channel + program ID + air date). |
| TSTV-FR-031 | Resume from bookmark: when a viewer returns to a previously started catch-up program, playback resumes from the saved position with a brief "Resuming from [time]" indicator | P0 | 1 | -- | Resume position loaded from Bookmark Service in < 100ms. Playback starts within 2 seconds of the bookmarked position. Indicator shown for 3 seconds, then auto-hides. |
| TSTV-FR-032 | TSTV content in Continue Watching rail: catch-up programs that the viewer has started but not finished appear in the "Continue Watching" rail on the home screen, alongside VOD and recording content | P0 | 1 | AI prioritizes Continue Watching items by likelihood of completion and recency, with catch-up expiry as a boosting factor | Catch-up items in Continue Watching show: thumbnail, title, channel, progress bar, time remaining, catch-up expiry. Items expiring within 24 hours are visually highlighted. AI ranking considers: recency of last play, % complete, catch-up expiry urgency. |
| TSTV-FR-033 | AI auto-bookmarking at natural chapter breaks: for long-form content (documentaries, films), the AI identifies natural chapter break points and creates bookmarks that allow "skip to next section" navigation | P2 | 3 | Scene detection model (PyTorch, served via KServe) analyzes content to identify chapter breaks based on audio silence, visual transitions, and narrative structure | Chapter marks generated during content ingest (batch processing via SageMaker). 5-15 marks per hour of content. Marks accessible as a chapter navigation overlay during playback. Accuracy: 80%+ of marks align with viewer-perceived chapter breaks (measured via user feedback). |

---

## 5. AI-Specific Features

### 5.1 Personalized Catch-Up Feed ("Your Catch-Up")

**Description:** An AI-curated rail on the home screen and catch-up section that surfaces catch-up programs the viewer is most likely to enjoy, based on their viewing history, genre preferences, and temporal patterns. This eliminates the need to browse the EPG or scan individual channel schedules to discover what aired.

**Architecture:**
- The Recommendation Service generates a catch-up recommendation set per user profile by combining:
  - Collaborative filtering: "users who watch similar content to you watched these catch-up programs"
  - Content-based filtering: genre, mood, theme, cast matching against user preferences (from Feature Store)
  - Temporal signals: programs from channels the user watches at specific times (e.g., evening news, morning cartoons)
  - Recency: slight boost for programs that aired recently (yesterday > 5 days ago)
  - Expiry urgency: slight boost for programs expiring within 48 hours
- The recommendation set is pre-computed hourly per user and cached in Redis (key: `recs:catchup:{profile_id}`, TTL: 60 minutes). The BFF serves this as the "Your Catch-Up" rail.
- The rail contains 15-20 items, paginated in groups of 5. Each item includes: program thumbnail (AI-selected variant per user, Phase 2), title, channel, air date, duration, match score, and a brief AI-generated reason ("Because you watched [related program]" or "Popular on Channel 12 this week").
- Fallback: if AI is unavailable, the rail falls back to "Most Popular Catch-Up" (sorted by catch-up viewer count from the past 24 hours).

**Acceptance Criteria:**
- [ ] "Your Catch-Up" rail populated with 15-20 personalized suggestions per profile
- [ ] Recommendations update within 1 hour of new viewing activity
- [ ] Click-through rate (CTR) on "Your Catch-Up" rail: > 12% (measured as clicks / impressions)
- [ ] 60%+ of clicked items watched for > 50% of their duration (relevance measure)
- [ ] Diversity: minimum 3 different channels and 3 different genres in the top 10 suggestions
- [ ] Explanation text ("Because you watched...") present for 80%+ of items
- [ ] Fallback to popularity-based rail within 500ms if Recommendation Service is unavailable

### 5.2 "You Missed This" Smart Notifications

**Description:** Proactive notifications alerting viewers to catch-up content they are likely to enjoy but may not discover through browsing. Notifications are personalized, frequency-capped, and respect user preferences for spoiler avoidance.

**Architecture:**
- A scheduled job runs every 2 hours, evaluating newly available catch-up programs against each user's preference profile.
- For each user, the Recommendation Service scores all new catch-up programs (aired in the last 24 hours). Programs scoring above a configurable confidence threshold (default: 80%) are candidates for notification.
- Notification candidates are filtered by:
  - Frequency cap: maximum 3 "You Missed This" notifications per user per day
  - Deduplication: no repeated notifications for the same program
  - Quiet hours: no notifications between 23:00 and 07:00 (user-configurable)
  - Content type preference: users can opt out of specific content types (e.g., "Don't notify me about news")
  - Spoiler preference: sports notifications respect "Spoiler-free" mode (no scores or results in notification text)
- Notification delivery: push notification (mobile), in-app notification (all platforms), email digest (optional, weekly).
- Notification text is generated using a template engine with AI-selected content description. Example: "You missed: MasterChef Season 8 Episode 4 (Wednesday, Channel 21). Available for 5 more days."

**Acceptance Criteria:**
- [ ] Notifications sent within 2 hours of program availability on catch-up
- [ ] Notification relevance: > 20% of "You Missed This" notifications result in a play event within 48 hours
- [ ] Frequency cap enforced: maximum 3 per user per day
- [ ] Spoiler-free mode works correctly for sports content (no scores in notification)
- [ ] Quiet hours respected per user timezone
- [ ] Users can disable "You Missed This" notifications entirely in settings
- [ ] Opt-out of specific content types is available (e.g., no news notifications)

### 5.3 AI-Generated Program Summaries

**Description:** For catch-up programs where editorial descriptions are limited or generic ("Episode 4 of Season 8"), the AI generates richer summaries that help viewers decide whether to watch. This is particularly valuable for catch-up browse where viewers are choosing between many options.

**Architecture:**
- Program summaries are generated via Amazon Bedrock (Claude 3.5 Haiku for latency-sensitive inline generation, Claude 3.5 Sonnet for batch pre-generation).
- Inputs: existing EPG metadata (title, genre, series info), AI-enriched content tags (mood, themes, content warnings), and subtitle/transcript data (if available from ingest pipeline).
- Summaries are generated in batch (overnight for next day's schedule, within 30 minutes of broadcast end for catch-up) and cached in the Metadata Service (PostgreSQL + Redis).
- Summary format: 2-3 sentences, spoiler-free for first viewing, including: what the program is about, why it might be interesting (genre/mood descriptor), and a content advisory note if applicable.
- Summaries are displayed on program detail cards in catch-up browse, search results, and the "Your Catch-Up" rail.
- Fallback: if AI summary is unavailable, display the original EPG description.

**Acceptance Criteria:**
- [ ] AI summaries generated for 90%+ of catch-up programs that have limited editorial descriptions (< 50 characters)
- [ ] Summary quality: 85%+ user satisfaction in A/B test vs no-summary control
- [ ] Summary generation latency: < 30 minutes after broadcast end (batch), < 2 seconds for inline generation (on-demand)
- [ ] Summaries are spoiler-free (no plot twists, no game results unless user opts in)
- [ ] Summaries available in the platform's primary language(s)
- [ ] LLM cost per summary: < $0.001 (using Haiku for batch)

### 5.4 Predictive Cache Warming for Catch-Up Content

**Description:** An ML model predicts which catch-up programs will be popular in the next 2-4 hours based on EPG schedule, historical viewing patterns, day-of-week patterns, and current trending signals. Predicted popular content is pre-warmed on CDN edge caches, reducing origin load and improving playback start time.

**Architecture:**
- A prediction model (XGBoost, retrained daily) runs every 2 hours and generates a ranked list of catch-up programs predicted to receive > 100 play starts in the next 4-hour window.
- Prediction features: program genre, channel popularity, time-of-day historical demand, day-of-week pattern, current trending velocity, similar program performance in past weeks, catch-up expiry proximity (expiring content gets more urgent viewing).
- Top 50 predicted programs are pre-warmed on CDN edge caches in all regions. Pre-warming sends a background request from the origin shield to each CDN edge PoP for the first 5 minutes of each predicted program's content (enough for instant playback start).
- The CDN Routing Service factors cache warm status into routing decisions: if a program is pre-warmed on CDN A but not CDN B, route the session to CDN A.

**Acceptance Criteria:**
- [ ] CDN cache hit ratio for catch-up content: > 80% (vs baseline 60% without pre-warming)
- [ ] Prediction accuracy: 70%+ of top-50 predicted programs actually appear in the top-100 most-played catch-up programs in the prediction window
- [ ] Catch-up playback start time: < 1.5 seconds (p95) for pre-warmed content (vs 2.5 seconds for non-warmed)
- [ ] Origin load reduction: 30% fewer origin requests for catch-up content during peak hours
- [ ] Pre-warming does not exceed 5% of total CDN bandwidth budget

### 5.5 Viewing Pattern Prediction for Personalized Scheduling

**Description:** The AI learns each viewer's time-shifted viewing patterns -- when they typically watch catch-up content, which genres they prefer at different times, and how far after broadcast they typically watch. This intelligence feeds into "Your Schedule" (PRD-005) and notification timing.

**Architecture:**
- The Feature Store maintains per-user temporal viewing features:
  - Catch-up viewing time distribution: probability of catch-up viewing per hour of the day, per day of week
  - Genre preference per time slot: sports catch-up on weekends, news catch-up in the morning, entertainment on weekday evenings
  - Catch-up delay: average hours between broadcast and catch-up viewing per content type (e.g., 12 hours for drama, 2 hours for sports)
- These features are computed from Kafka event streams (playback.started events filtered to catch-up sessions) by a Flink streaming job, aggregated hourly.
- Consumers: Notification Service (timing "You Missed This" notifications for optimal engagement), EPG "Your Schedule" view (PRD-005), and the Recommendation Service (boosting catch-up content likely to be watched at the current time).

**Acceptance Criteria:**
- [ ] Temporal features computed for users with > 10 catch-up viewing sessions
- [ ] Notification timing optimization: notifications sent at predicted optimal time result in 25%+ higher open rate vs random timing
- [ ] Feature freshness: updated hourly in the online Feature Store
- [ ] Feature coverage: temporal features available for 70%+ of active profiles by Phase 2 (3 months post-launch)

---

## 6. Non-Functional Requirements

### 6.1 Latency

| Requirement | Target | Measurement | Priority |
|-------------|--------|-------------|----------|
| Start Over initiation (user action to program-start playback) | < 3 seconds (p95) | Client-side telemetry | P0 |
| Catch-Up playback start | < 2 seconds (p95) for pre-warmed content, < 3 seconds for non-warmed | Client-side telemetry | P0 |
| Jump to Live (from start-over) | < 1 second | Client-side telemetry | P0 |
| Catch-Up catalog browse load | < 2 seconds (channel view or date view) | BFF API response time + client render | P0 |
| "Your Catch-Up" rail load | < 1 second | BFF API response time (pre-computed in Redis) | P1 |
| Rights eligibility check (start-over/catch-up) | < 50ms | EPG Service + Redis cache | P0 |
| Bookmark sync (cross-device) | < 5 seconds | Bookmark Service write + read from another device | P0 |

### 6.2 Availability

| Requirement | Target | Measurement |
|-------------|--------|-------------|
| Start Over service availability | 99.95% | Synthetic monitoring: Start Over initiation success rate |
| Catch-Up catalog availability | 99.95% | Synthetic monitoring: catalog browse + playback success rate |
| Catch-Up content availability after broadcast | Within 5 minutes of program end | Measured as time from broadcast end to first successful catch-up play |
| Content expiry accuracy | Within 5 minutes of scheduled expiry time | Expired content no longer playable within 5 minutes of window close |

### 6.3 Scale

| Requirement | Phase 1 Target | Phase 4 Target | Measurement |
|-------------|---------------|----------------|-------------|
| Concurrent start-over sessions | 10,000 | 100,000 | Active start-over playback sessions |
| Concurrent catch-up playback sessions | 15,000 | 150,000 | Active catch-up playback sessions |
| Catch-Up catalog size (programs in window) | ~20,000 programs (200 channels x ~15 programs/day x 7 days) | ~30,000 programs | Catalog item count |
| Catch-Up storage (origin) | 50 TB (estimated: 200 channels x ~18 hours/day x 7 days x avg 3 Gbps) | 100 TB | S3/EFS storage metrics |

### 6.4 Quality

| Requirement | Target | Measurement |
|-------------|--------|-------------|
| Start Over video quality | Same as live channel quality (VMAF > 93 for 1080p HEVC) | VMAF comparison between live and start-over streams |
| Catch-Up video quality | Same as original broadcast quality | VMAF comparison |
| Trick-play thumbnail quality | Minimum 360p, generated at 10-second intervals | Thumbnail resolution and interval audit |
| Rebuffer ratio (TSTV sessions) | < 0.3% | Client-side telemetry (Conviva) |

---

## 7. Technical Considerations

### 7.1 Start Over Architecture

Start Over leverages the same content that is being delivered for the live channel. The key architectural choice is how the time-shifted content is made available:

**Approach: Extended Live Buffer at Origin**

- The live packaging engine (USP / MediaPackage) maintains an extended DVR window per channel. For each start-over-enabled channel, the packaging engine retains segments for the duration of the longest running program (maximum 4 hours, configurable).
- When a viewer requests Start Over, the manifest proxy generates a time-shifted manifest pointing to the same segments in the extended buffer, starting from the program's start time (provided by EPG metadata).
- This approach avoids separate recording infrastructure -- start-over is simply a different view into the live segment buffer.

**Manifest Proxy:**
- A lightweight service (Go) that sits between the client and the packaging engine.
- On a Start Over request, the proxy: (a) queries the EPG Service for the program's start time, (b) generates a manifest that starts at the program start time and extends to the current live position, (c) returns the time-shifted manifest URL to the client.
- The manifest continues to grow in real-time (appending new segments as the live broadcast continues) until the program ends or the viewer returns to live.

**Segment Storage:**
- Live segments are stored on S3 (VOD-packaged catch-up) and EFS (low-latency live buffer).
- Start Over uses the EFS live buffer. Catch-Up uses S3-stored segments (see Section 7.2).
- EFS retention: 4 hours per channel (covering the longest program). Segments older than 4 hours are cleaned up by a periodic garbage collector.

### 7.2 Catch-Up Architecture

Catch-Up content requires longer retention (7 days) and different storage characteristics than the live buffer:

**Ingest-to-Catch-Up Pipeline:**
1. During live broadcast, segments are written to EFS (live buffer) and simultaneously copied to S3 (catch-up storage).
2. At program boundary (determined by SCTE-35 markers or EPG schedule), a background job creates a complete catch-up asset: a full-program manifest referencing the S3-stored segments, with program metadata (title, duration, start time, end time) from the EPG Service.
3. The catch-up asset is registered in the Catalog Service (as a catch-up-type content item) and becomes browsable/searchable within 5 minutes of broadcast end.
4. DRM: catch-up content uses the same CBCS encryption and content keys as the original live broadcast. No re-encryption required.

**Storage:**
- S3 storage: segments stored under `s3://catch-up/{channel_id}/{date}/{program_id}/`
- Lifecycle policy: segments automatically deleted after the catch-up window expires (7 days from broadcast).
- Storage estimate: 200 channels x average 18 hours of content per day x 7 days x average 3 Gbps (HEVC 1080p + all lower profiles) = approximately 50 TB (Phase 1), reducible with per-title encoding optimization (Phase 2).

**CDN Delivery:**
- Catch-up segments are served through the same multi-CDN infrastructure as live and VOD content.
- CDN caching: longer TTLs for catch-up segments (24 hours) compared to live segments (2 seconds), since catch-up content is immutable.
- Predictive cache warming (Section 5.4) pre-populates CDN edge caches for predicted popular catch-up content.

### 7.3 Program Boundary Detection

Accurate program start and end times are critical for both Start Over (knowing where to start) and Catch-Up (knowing where to cut the recording).

**Primary method: EPG schedule data.** The EPG Service provides scheduled start and end times for each program. These are used as the default program boundaries.

**Enhancement: SCTE-35 markers.** Some broadcast feeds include SCTE-35 splice points that precisely mark program boundaries and ad break locations. When available, SCTE-35 markers are used for higher accuracy than EPG schedule times (which can drift by 1-2 minutes due to schedule overruns).

**Padding:** To handle schedule drift, the ingest pipeline applies configurable padding: start 1 minute before scheduled start, end 3 minutes after scheduled end. This ensures the viewer does not miss the program beginning or end due to minor schedule variations.

### 7.4 Rights Integration

The TSTV service queries a centralized rights engine for every start-over and catch-up availability decision:

```
Rights Engine Query:
  Input: (program_id, channel_id, territory, right_type: "start_over" | "catch_up")
  Output: { eligible: bool, window_hours: int, restrictions: [...] }
```

- Rights data is sourced from content provider agreements, ingested via a rights management API, and stored in PostgreSQL (source of truth) with Redis caching (TTL: 5 minutes).
- Rights changes propagate via Kafka (`rights.updated` topic) and are consumed by the EPG Service, Catalog Service, and TSTV manifest proxy.
- All rights decisions are logged for audit compliance.

---

### 7.5 Data Model — Channel & Schedule Entry Extensions

The following columns are added to existing tables to support per-channel TSTV rules and segment time indexing.

**`channels` table additions:**

| Column | Type | Default | Purpose |
|--------|------|---------|---------|
| `cdn_channel_key` | VARCHAR(20) | — | Maps channel to CDN path and segment directory (`ch1`, `ch2`, etc.) |
| `tstv_enabled` | BOOLEAN | TRUE | Master switch — enables any TSTV capability for this channel |
| `startover_enabled` | BOOLEAN | TRUE | Can users start over currently airing programs? |
| `catchup_enabled` | BOOLEAN | TRUE | Can users access past programs (catch-up)? |
| `catchup_window_hours` | INTEGER | 168 | **Infrastructure retention** — how long segments are kept on disk (default: 7 days). Typically the same for all channels. |
| `cutv_window_hours` | INTEGER | 48 | **Business rule / viewer entitlement** — how long after broadcast a user may actually access catch-up. Varies per channel based on content rights (e.g., 2h for premium sports, 168h for entertainment). |

**Important distinction:** `catchup_window_hours` controls infrastructure (segment cleanup cron), while `cutv_window_hours` controls viewer entitlement (manifest endpoint enforcement). The infrastructure retains segments for the maximum configured window; the API enforces the viewer's entitlement window at request time.

**Example channel configurations:**

| Channel | Start-over | Catch-up | CUTV window | Notes |
|---------|-----------|----------|-------------|-------|
| NRK1 | ✅ | ✅ | 168h (7 days) | Full TSTV rights |
| TV 2 | ✅ | ✅ | 48h | Restricted catch-up window |
| Discovery | ✅ | ❌ | — | Start-over only, no catch-up |
| Eurosport | ❌ | ❌ | — | No TSTV (sports broadcast rights) |
| National Geo | ✅ | ✅ | 72h | Medium catch-up window |

**`schedule_entries` table additions:**

| Column | Type | Default | Purpose |
|--------|------|---------|---------|
| `catchup_eligible` | BOOLEAN | TRUE | Per-program catch-up eligibility (can override channel default) |
| `startover_eligible` | BOOLEAN | TRUE | Per-program start-over eligibility |
| `series_id` | VARCHAR(100) | NULL | Links episodes of the same series (used by Cloud PVR series links and auto-play next episode) |

**New `tstv_sessions` table (PoC analytics):**

```sql
CREATE TABLE tstv_sessions (
    id                SERIAL PRIMARY KEY,
    user_id           INTEGER REFERENCES users(id),
    profile_id        INTEGER REFERENCES profiles(id),
    channel_id        VARCHAR(20),
    schedule_entry_id INTEGER REFERENCES schedule_entries(id),
    session_type      VARCHAR(20) CHECK (session_type IN ('startover', 'catchup')),
    started_at        TIMESTAMPTZ DEFAULT NOW(),
    last_position_s   FLOAT DEFAULT 0,
    completed         BOOLEAN DEFAULT FALSE
);
```

**`recordings` table (Cloud PVR stub — no new infrastructure required):**

```sql
CREATE TABLE recordings (
    id                SERIAL PRIMARY KEY,
    user_id           INTEGER REFERENCES users(id),
    schedule_entry_id INTEGER REFERENCES schedule_entries(id),
    channel_id        VARCHAR(20),
    requested_at      TIMESTAMPTZ DEFAULT NOW(),
    status            VARCHAR(20) DEFAULT 'completed'
);
```

The `recordings` table is a metadata-only stub. Because segments are already persisted in the shared archive, a PVR recording is simply a pointer to a time range — no segment copying or additional infrastructure required. The TSTV catch-up manifest generator is reused as-is for PVR playback.

**`drm_keys` table (added by DRM plan — see Section 7.8):**

```sql
CREATE TABLE drm_keys (
    id          SERIAL PRIMARY KEY,
    key_id      UUID NOT NULL UNIQUE,
    key_value   BYTEA NOT NULL,
    channel_id  INTEGER REFERENCES channels(id),
    content_id  INTEGER,
    active      BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    rotated_at  TIMESTAMPTZ,
    expires_at  TIMESTAMPTZ
);
```

### 7.6 PoC Architecture — Segment Storage & Time Indexing

The production architecture (Section 7.1–7.2) references EFS, S3, and a standalone Go manifest proxy service. The PoC implementation simplifies this to run entirely within Docker Compose with no cloud dependencies.

**PoC segment storage approach:**
- FFmpeg writes HLS segments directly to a shared Docker volume (`hls_data`)
- Segment filenames encode wall-clock start time using `strftime`: `ch1-20260223143000.ts`
- This eliminates the need for a separate `hls_segments` database table — timestamps are derived directly from filenames
- A daily cron in the CDN container deletes segments older than `catchup_window_hours` (default 7 days)

**PoC manifest generator:**
- Implemented as a FastAPI router (`/tstv`) in the existing backend service
- Reads the `/hls/{channel_key}/` directory listing to enumerate available segments
- Parses segment timestamps from filenames to filter by time range
- Assembles and returns HLS manifests in-process (no separate Go service required)

**Docker Compose services (PoC):**

```yaml
services:
  simlive:               # FFmpeg ingest + HLS packaging (one process per channel)
    build: ./docker/simlive
    volumes:
      - hls_data:/hls
    depends_on: [cdn]

  cdn:                   # nginx — direct-serves segments from shared volume
    build: ./docker/cdn
    volumes:
      - hls_data:/hls
    ports:
      - "8088:80"

  backend:               # FastAPI — mounts hls_data read-only for manifest generation
    volumes:
      - hls_data:/hls:ro

volumes:
  hls_data:
```

**FFmpeg command per channel (PoC — encrypted fMP4):**

```bash
ffmpeg -stream_loop -1 -re -i /videos/channel1.mp4 \
  -vf "drawtext=text='CH1 %{localtime\:%Y-%m-%d %H\\\:%M\\\:%S}':fontsize=48:fontcolor=white:box=1:boxcolor=black@0.5:boxborderw=5:x=10:y=10" \
  -c:v libx264 -preset ultrafast -tune zerolatency -b:v 4M \
  -c:a aac -b:a 128k \
  -f hls \
  -hls_time 6 \
  -hls_list_size 30 \
  -hls_flags program_date_time+append_list \
  -hls_segment_type fmp4 \
  -hls_fmp4_init_filename 'ch1-init.mp4' \
  -hls_segment_filename '/hls/ch1/ch1-%Y%m%d%H%M%S.m4s' \
  -strftime 1 \
  -encryption_scheme cenc-aes-ctr \
  -encryption_key ${KEY_HEX} \
  -encryption_kid ${KEY_ID_HEX} \
  /hls/ch1/live.m3u8
```

**Segment format:** fMP4 (`.m4s`) with CENC AES-128-CTR encryption. The init segment (`ch1-init.mp4`) is written once per channel and contains the PSSH box and codec configuration. The `KEY_HEX` and `KEY_ID_HEX` are fetched from the Key Management Service at SimLive startup. See Section 7.8 for the DRM architecture.

**Key FFmpeg flags:**

| Flag | Purpose |
|------|---------|
| `-stream_loop -1` | Loop video indefinitely |
| `-re` | Real-time playback speed |
| `-vf drawtext=...` | Burns wall-clock time into video for time-shift verification |
| `-preset ultrafast` | Minimize CPU (required because drawtext prevents `-c:v copy`) |
| `-hls_time 6` | 6-second segments |
| `-hls_list_size 30` | Live manifest shows last 30 segments (3-minute live window) |
| `-hls_flags program_date_time` | Injects `#EXT-X-PROGRAM-DATE-TIME` per segment |
| `-hls_segment_type fmp4` | fMP4 output — required for CENC encryption |
| `-hls_fmp4_init_filename` | Init segment with codec parameters and PSSH box |
| `-strftime 1` | Enables `%Y%m%d%H%M%S` in segment filenames |
| `-encryption_scheme cenc-aes-ctr` | CENC (Common Encryption) — same scheme as Widevine/FairPlay |

**TSTV API endpoints (PoC):**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tstv/channels` | GET | List channels with TSTV eligibility flags |
| `/tstv/startover/{channel_id}` | GET | Live stream URL + start-over availability for current program |
| `/tstv/startover/{channel_id}/manifest` | GET | Start-over EVENT manifest (`?schedule_entry_id=N`) |
| `/tstv/catchup/{channel_id}` | GET | List catch-up programs for channel (past 7 days, eligible only) |
| `/tstv/catchup/{channel_id}/manifest` | GET | Catch-up VOD manifest (`?schedule_entry_id=N`) |
| `/tstv/sessions` | POST | Record TSTV session start/position for analytics |

**Performance note (PoC):** With 5 channels × 7 days × 6-second segments, each channel directory holds ~100K `.m4s` files. A directory listing + filename parse takes <50ms on Linux SSD — acceptable for a PoC. Production would use the segment index database described in Section 7.1.

### 7.7 Admin Dashboard — TSTV Controls

The admin dashboard (frontend-admin) gains a "Streaming" section with two sub-panels:

**Channel Control (SimLive Management):**
Operators can start, stop, and monitor FFmpeg streaming processes per channel. The backend maintains an in-process registry of running FFmpeg PIDs.

| Admin Endpoint | Method | Description |
|----------------|--------|-------------|
| `/admin/simlive/status` | GET | All channels: running/stopped, PID, uptime, segment count, disk usage |
| `/admin/simlive/{channel_key}/start` | POST | Start FFmpeg process for channel |
| `/admin/simlive/{channel_key}/stop` | POST | Stop FFmpeg process (SIGTERM) |
| `/admin/simlive/{channel_key}/restart` | POST | Stop + start |
| `/admin/simlive/cleanup` | POST | Delete segments older than retention window |

**TSTV Rules Editor:**
Operators can update per-channel TSTV business rules without a deployment. Changes take effect on the next manifest request.

| Admin Endpoint | Method | Description |
|----------------|--------|-------------|
| `/admin/tstv/rules` | GET | List all channels with TSTV rules |
| `/admin/tstv/rules/{channel_id}` | PUT | Update: `tstv_enabled`, `startover_enabled`, `catchup_enabled`, `cutv_window_hours` |

Admin UI shows a table with toggles and a CUTV window dropdown (2h / 6h / 12h / 24h / 48h / 72h / 168h) per channel.

**DRM Management panel:**
Operators can inspect encryption keys, trigger key rotation, and monitor license activity.

| Admin Endpoint | Method | Description |
|----------------|--------|-------------|
| `/admin/drm/keys` | GET | List all keys: channel, KID (truncated), active/rotated status, created date |
| `/admin/drm/keys/channel/{id}/rotate` | POST | Rotate encryption key for channel (deactivates current, generates new, restarts SimLive) |
| `/admin/drm/license-stats` | GET | License request counts: granted vs denied, broken down by channel and denial reason |

Admin UI shows a key overview table per channel with a "Rotate Key" button (with confirmation) and a license request dashboard showing success/failure rates.

**Subscription Management panel:**
Operators can manage user subscriptions and product entitlements for testing.

| Admin Endpoint | Method | Description |
|----------------|--------|-------------|
| `/admin/subscriptions` | GET | List all users with their active subscriptions and entitled channels |
| `/admin/subscriptions` | POST | Create subscription for a user |
| `/admin/subscriptions/{id}` | PUT | Modify subscription status (activate, suspend, cancel) |
| `/admin/products` | GET | List products with channel entitlements |
| `/admin/products/{id}` | PUT | Modify product (price, included channels, active status) |

Admin UI shows a user table with subscription status and per-channel entitlement indicators. Quick actions allow adding/removing subscriptions for test users.

### 7.8 PoC DRM Architecture — ClearKey + CENC

The production architecture (Sections 7.1–7.4) references Widevine + FairPlay via CPIX. The PoC implements ClearKey — a W3C standard that is architecturally identical to production DRM but requires no commercial CDM licenses.

**What ClearKey demonstrates:**
- CENC (Common Encryption) on HLS fMP4 segments — the same encryption scheme used by Widevine and FairPlay
- EME (Encrypted Media Extensions) in the browser — the same browser API used by all production DRM systems
- A license server with authentication and entitlement-gated key delivery
- Per-channel encryption keys with rotation support
- The full chain: subscription → entitlement → license → decryption key → playback

**What ClearKey does NOT provide:** hardware-backed key protection, secure video path, or content owner certification. The PoC demonstrates the architecture and business logic; replacing ClearKey with Widevine/FairPlay in production is a license server and player configuration change, not an architectural change.

**DRM flow:**

```
SimLive (FFmpeg)
  → POST /drm/keys/channel/{ch}  →  Key Management Service
  ← { key_id_hex, key_hex }      ←  (generates + stores AES-128 key in drm_keys table)

FFmpeg encrypts segments with CENC AES-128-CTR → writes to shared volume
CDN serves encrypted .m4s segments

Player (hls.js + EME):
  1. Loads manifest → detects #EXT-X-KEY tag
  2. EME: creates MediaKeySession, sends license request
  3. POST /drm/license  (Authorization: Bearer <jwt>)
     Body: { "kids": ["base64url-key-id"], "type": "temporary" }
  4. License server: validates JWT → decodes KID → checks entitlement
     If entitled: returns { "keys": [{ "kty": "oct", "kid": "...", "k": "..." }] }
     If not entitled: returns 403 + available_products (upsell data)
  5. Browser decrypts and renders video
```

**Entitlement enforcement is layered — DRM is the definitive check:**

| Enforcement point | Failure response | Purpose |
|-------------------|-----------------|---------|
| Channel list API | Channel shown as locked | UI — indicates subscription needed |
| TSTV manifest request | 403 + upsell products | No manifest returned |
| EPG catch-up click | Redirect to upsell | Prevents player load |
| **DRM license request** | **403 + upsell products** | **Hard block — content cannot be decrypted even if API checks are bypassed** |

**Key rotation:** When a key is rotated, the old key remains in `drm_keys` (marked `active=False`). License requests for catch-up/PVR content encrypted with the old key are still resolved by KID lookup — old content remains playable. New segments use the new key. This mirrors how production DRM handles key rotation over long content windows.

**Production migration path:**

| Component | ClearKey (PoC) | Production |
|-----------|---------------|------------|
| Encryption | CENC AES-128-CTR | CENC AES-128-CTR (same) |
| Segment format | fMP4 (same) | fMP4 (same) |
| Key management | Self-hosted FastAPI | DRM vendor (Axinom, BuyDRM, PallyCon) or self-hosted |
| License server | ClearKey JSON protocol | Widevine license proxy + FairPlay KSM |
| Player | Shaka Player 4.12 EME + ClearKey | Shaka Player with Widevine/FairPlay CDM (same player, DRM config change only) |
| Entitlement check | Same logic | Same logic (vendor callback or proxy) |

The entitlement model, key storage, segment archive, and manifest generation are all reusable without change.

---

## 8. Dependencies

### 8.1 Service Dependencies

| Dependency | Service | PRD Reference | Dependency Type | Impact if Unavailable |
|------------|---------|---------------|-----------------|----------------------|
| Program schedule and metadata | EPG Service | PRD-005 | Hard | Cannot determine program boundaries for Start Over or populate catch-up catalog. Service is non-functional. |
| Live channel delivery | Live TV Service | PRD-001 | Hard | Start Over requires an active live channel feed. No live = no start-over. Catch-up is independent (uses stored segments). |
| Content rights | Rights Engine / Entitlement Service | ARCH-001 | Hard | Cannot verify start-over or catch-up eligibility. Fail-closed: deny TSTV access. |
| User authentication and profiles | Auth/Profile Service | ARCH-001 | Hard | Cannot identify user or load preferences. |
| Bookmark persistence | Bookmark Service | ARCH-001 | Soft | Bookmarks not saved. Playback still works but resume is unavailable. |
| AI recommendations | Recommendation Service | PRD-007 | Soft | "Your Catch-Up" rail falls back to popularity-based. "You Missed This" notifications suspended. |
| Content search | Search Service | ARCH-001 | Soft | Catch-up content not searchable. Browse by channel/date still works. |
| Cloud PVR | Recording Service | PRD-003 | Soft | "Record to PVR" option unavailable. Viewer can only use catch-up window. |
| CDN delivery | Multi-CDN + CAT | ARCH-001 | Hard | Segments not deliverable. TSTV service is non-functional. |
| Notifications | Notification Service | ARCH-001 | Soft | "You Missed This" notifications not delivered. Other features unaffected. |

### 8.2 Infrastructure Dependencies

| Dependency | Component | Impact if Unavailable |
|------------|-----------|----------------------|
| Live segment buffer | EFS | Start Over unavailable (no buffer to read from). Catch-up pipeline also impacted for real-time ingest. |
| Catch-up storage | S3 | Catch-up playback unavailable. Start Over unaffected (uses EFS buffer). |
| Manifest proxy | Custom Go service | Cannot generate time-shifted manifests. Start Over and Catch-Up playback unavailable. |
| Kafka | Event bus | Catch-up catalog updates delayed (events not flowing). AI features degrade. Core playback unaffected if segments are already stored. |
| Redis | Cache layer | Rights checks slow (fall back to PostgreSQL). Recommendation rails slow. Increased latency but functional. |

---

## 9. Success Metrics

| # | Metric | Baseline (Industry) | Phase 1 Target | Phase 2 Target | Phase 4 Target | Measurement Method |
|---|--------|--------------------|--------------|--------------|--------------|--------------------|
| 1 | Start Over adoption (% of late tune-ins that use start-over) | 10-15% | 30% | 40% | 50% | % of sessions where user tuned in > 3 min late and selected "Start from beginning" |
| 2 | Start Over initiation time (p95) | 3-5 seconds | < 3 seconds | < 2.5 seconds | < 2 seconds | Client-side telemetry |
| 3 | Catch-Up content availability time | 15-30 minutes | < 5 minutes | < 3 minutes | < 2 minutes | Time from broadcast end to first successful catch-up play |
| 4 | Catch-Up viewing hours as % of total live viewing | 15-20% | 20% | 30% | 35% | Total catch-up viewing hours / total live+TSTV viewing hours |
| 5 | "Your Catch-Up" rail CTR | N/A | 12% | 18% | 22% | Clicks / impressions on the personalized catch-up rail |
| 6 | "You Missed This" notification engagement | N/A | 15% open rate, 8% play rate | 20% open, 12% play | 25% open, 15% play | Notification open → play conversion |
| 7 | Catch-Up playback start time (p95) | 3-5 seconds | < 2 seconds (pre-warmed) | < 1.5 seconds | < 1.5 seconds | Client-side telemetry |
| 8 | Cross-device resume accuracy | 70% resume within 30s of stop point | 90% within 5s | 95% within 5s | 98% within 3s | Bookmark accuracy measured by resume position vs stop position |
| 9 | TSTV contribution to session duration | +5-10 min/session | +8 min/session | +12 min/session | +15 min/session | Average session duration increase for users who engage with TSTV features |
| 10 | Catch-Up CDN cache hit ratio | 50-60% | 75% | 85% | 90% | CDN cache hit metrics for catch-up segment requests |

---

## 10. Open Questions & Risks

### Open Questions

| # | Question | Owner | Impact | Target Resolution |
|---|----------|-------|--------|-------------------|
| 1 | Should the start-over buffer be shared across all users or per-user? A shared buffer (copy-on-write, like Cloud PVR) is storage-efficient. Per-user buffers are simpler but wasteful. | Platform Architect | Storage cost, architecture complexity | Phase 1 design review. Recommendation: shared buffer (same live segments, different manifest views). |
| 2 | What is the catch-up window for premium sports channels? Rights holders typically restrict time-shift windows for premium sports. Should we support 24-hour windows for sports and 7-day for entertainment on the same platform? | Business / Content Rights | Content rights compliance, UX consistency | Pre-launch rights negotiation. Support variable windows per channel in the rights engine from Phase 1. |
| 3 | How should catch-up handle programs that run over schedule? E.g., a live sports event overruns by 30 minutes, pushing the next program's start. | Platform Engineer | Program boundary accuracy, user experience | Phase 1 design. Use SCTE-35 where available, EPG-based padding (3 min) as fallback. Accept imperfect boundaries in Phase 1, improve with ML-based boundary detection in Phase 3. |
| 4 | Should catch-up content count toward Cloud PVR storage quota if a user records it? | Product Manager | UX clarity, storage model | Phase 2 planning. Recommendation: catch-up viewing does not consume PVR quota; recording catch-up to PVR does consume quota. |
| 5 | Should the AI generate summaries for all catch-up content or only when the editorial description is below a quality threshold? | AI/ML Lead | LLM cost, summary quality | Phase 2. Start with only programs with < 50 character descriptions. Expand based on cost and user feedback. |
| 6 | What is the regulatory position on catch-up viewing analytics? Can we track which catch-up programs individual users watch for personalization purposes? | Legal / Privacy | Data privacy compliance, AI effectiveness | Phase 1 legal review. Design data pipeline with consent-gated personalization from day 1. |

### Risks

| # | Risk | Severity | Likelihood | Mitigation |
|---|------|----------|------------|------------|
| 1 | **Catch-Up storage costs escalate**: 200 channels x 7 days at full ABR ladder generates ~50 TB. As channel count grows, storage becomes a significant cost. | High | High | Implement per-title encoding optimization (Phase 2) to reduce bitrate. Use S3 Intelligent-Tiering (hot for first 48 hours, then standard). Consider reducing ABR ladder depth for older catch-up content (drop highest profile after 48 hours). Target: < $0.01 per viewer per month for TSTV storage. |
| 2 | **Content rights complexity**: per-program, per-channel, per-territory rights create a combinatorial explosion of eligibility rules. Incorrect rights enforcement could lead to contractual violations. | High | Medium | Build centralized rights engine with comprehensive audit logging. Default to "not available" when rights status is ambiguous. Automated rights testing in CI/CD (simulate rights scenarios). Regular compliance audits with content providers. |
| 3 | **Program boundary inaccuracy**: EPG schedule data is not always precise. Programs overrun or start late, causing start-over to begin at the wrong point or catch-up to cut off the ending. | Medium | High | Use SCTE-35 markers where available (60%+ of channels expected to support them). Apply configurable padding (1 min pre, 3 min post). Log boundary accuracy metrics. Plan for ML-based boundary detection enhancement in Phase 3. |
| 4 | **Start Over competes with Cloud PVR**: if start-over covers the live-viewing use case well enough, Cloud PVR adoption may be lower than expected, undermining the PVR upsell business case. | Medium | Medium | Position Start Over as "quick catch-up" (current program only, no series link, no long-term storage) and PVR as "plan ahead" (schedule recordings, keep forever, AI suggestions). Ensure the UX makes the distinction clear. Monitor cannibalization metrics. |
| 5 | **AI summary accuracy for live content**: AI-generated summaries for news, sports, and live events may contain factual errors or spoilers. | Medium | Medium | Apply content-type-aware summary policies: no score/result details for sports (unless opted in), no breaking news editorial for news programs (use factual "covers..." framing). Human review for high-profile content in Phase 1. Automated quality scoring in Phase 2. |
| 6 | **CDN cache pressure from catch-up**: catch-up viewing patterns are less predictable than live (which is simultaneous), leading to lower cache hit ratios and higher origin load. | Medium | Medium | Implement predictive cache warming (Section 5.4). Use origin shield to absorb cache misses. Negotiate CDN edge cache size for catch-up segments. Monitor cache hit ratio as a key operational metric. |
| 7 | **Manifest proxy as single point of failure**: the manifest proxy generates all time-shifted manifests. If it fails, both Start Over and Catch-Up are entirely unavailable. | High | Low | Deploy manifest proxy with N+2 redundancy. Horizontal scaling with stateless design (all state in Redis/EPG). Health checks and automatic restart. Chaos engineering tests for proxy failure. |

---

*This PRD defines the Time-Shifted TV (Start Over and Catch-Up) services for the AI-native OTT streaming platform. It should be read alongside PRD-001 (Live TV) for the live channel delivery that TSTV extends, PRD-003 (Cloud PVR) for the complementary personal recording service, PRD-005 (EPG) for program metadata and schedule data, and PRD-007 (AI User Experience) for cross-service AI capabilities including personalized recommendations and smart notifications.*

*v1.1 update (2026-02-23): Added Section 7.5 (data model extensions for per-channel TSTV rules), Section 7.6 (PoC architecture — segment storage and time indexing via strftime filenames), and Section 7.7 (admin dashboard TSTV controls). The production architecture in Sections 7.1–7.4 is preserved as the long-term target. See [tstv-implementation-plan.md](../../plans/tstv-implementation-plan.md) for the PoC implementation guide.*

*v1.2 update (2026-02-24): Updated Section 7.5 to add `tstv_sessions`, `recordings` (PVR stub), and `drm_keys` tables. Updated Section 7.6 to reflect the SimLive container naming, fMP4/CENC segment format (`.m4s`), full FFmpeg command with encryption flags, Docker Compose service layout, and TSTV API endpoint table. Updated Section 7.7 to add DRM Management and Subscription Management admin panels. Added Section 7.8 (PoC DRM architecture — ClearKey + CENC, license flow, entitlement enforcement chain, and production migration path). See [drm-implementation-plan.md](../../plans/drm-implementation-plan.md) and [tstv-implementation-plan-v2.md](../../plans/tstv-implementation-plan-v2.md) for implementation details.*
