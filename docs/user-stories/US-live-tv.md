# User Stories: Live TV & Linear Channels (PRD-001)

**Source PRD:** PRD-001-live-tv.md
**Generated:** 2026-02-08
**Total Stories:** 28

---

## Epic 1: Channel Acquisition and Tuning

### US-LTV-001: Channel Tune and Playback

**As a** viewer
**I want to** select a channel from the channel list, EPG, deep link, or channel number entry and start watching live TV
**So that** I can enjoy linear programming with minimal delay

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** LTV-FR-001

**Acceptance Criteria:**
- [ ] Given a viewer selects a channel from the channel list, when the channel is entitled, then playback begins within 1.5s (p95) from user input to first rendered frame
- [ ] Given a viewer enters a channel number, when the 3-digit entry completes (1.5s auto-commit), then the channel tunes within 1.5s of the final digit
- [ ] Given a viewer selects a channel via deep link, when the app opens, then the channel starts playing within 1.5s
- [ ] Performance: Channel change time < 1.5s (p95), < 1.0s (p50) measured via Conviva client-side telemetry

**AI Component:** No

**Dependencies:** Playback Session Service, Token Service (CAT), CDN Routing Service, Entitlement Service

**Technical Notes:**
- Session creation flow: BFF -> Entitlement check -> Playback Session Service -> CDN token -> manifest URL
- Pre-fetch DRM licenses for adjacent channels to reduce channel change time
- Each platform uses its native player (ExoPlayer, AVPlayer, Shaka)

---

### US-LTV-002: Channel Up/Down Navigation

**As a** viewer
**I want to** press channel-up or channel-down on my remote to cycle through channels
**So that** I can quickly browse available channels without opening the channel list

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** LTV-FR-002

**Acceptance Criteria:**
- [ ] Given a viewer presses channel-up, when in numeric ordering mode, then the next sequential channel tunes within 1.5s (p95)
- [ ] Given a viewer presses channel-up, when in AI-ordered mode, then the next AI-ranked channel tunes within 1.5s (p95)
- [ ] Given a viewer reaches the end of the channel list, when pressing channel-up, then the list wraps around to the first channel

**AI Component:** Yes -- AI-ordered channel list determines next/previous channel based on predicted relevance

**Dependencies:** US-LTV-001, US-LTV-012 (AI channel ordering)

**Technical Notes:**
- Channel order served by BFF as part of channel list API response
- AI order cached in Redis per user per 30-minute window

---

### US-LTV-003: Last Channel Recall

**As a** viewer
**I want to** press a "Back" button to return to the previously watched channel
**So that** I can quickly toggle between two channels (e.g., during commercial breaks)

**Priority:** P1
**Phase:** 1
**Story Points:** S
**PRD Reference:** LTV-FR-004

**Acceptance Criteria:**
- [ ] Given a viewer presses the back/recall button, when a previous channel exists in history, then the previous channel tunes within 1.5s
- [ ] Given a viewer has surfed multiple channels, when navigating history, then a minimum of 5 channels are stored in history
- [ ] Given no channel history exists (fresh session), when pressing back, then no action is taken and no error is displayed

**AI Component:** No

**Dependencies:** US-LTV-001

**Technical Notes:**
- Channel history maintained in client-side state per session
- History persists across app minimize/resume within same session

---

### US-LTV-004: Fast Channel Zapping Preview

**As a** viewer
**I want to** see a low-res thumbnail preview of a channel while browsing the channel list before committing to a full tune
**So that** I can quickly decide whether to watch a channel without waiting for a full tune

**Priority:** P1
**Phase:** 2
**Story Points:** L
**PRD Reference:** LTV-FR-005

**Acceptance Criteria:**
- [ ] Given a viewer highlights a channel in the channel list, when hovering for 500ms, then a live thumbnail preview appears within 2s
- [ ] Given a preview is displayed, when the viewer moves to a different channel, then the previous preview is released and a new one loads
- [ ] Performance: Preview resolution minimum 360p; preview does not consume a full playback session (lightweight preview mechanism)

**AI Component:** No

**Dependencies:** US-LTV-001, CDN delivery infrastructure

**Technical Notes:**
- Consider using low-latency thumbnail service or I-frame extraction from live manifests
- Preview streams must not count against concurrent session limits

---

## Epic 2: Channel List Management

### US-LTV-005: Channel List Display

**As a** viewer
**I want to** see a channel list with channel number, name, logo, and the currently airing program
**So that** I can quickly identify channels and decide what to watch

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** LTV-FR-010

**Acceptance Criteria:**
- [ ] Given a viewer opens the channel list, when data is loaded, then the list renders within 500ms
- [ ] Given each channel entry, when displayed, then it shows: channel number, name, logo, current program title, and time remaining
- [ ] Given channel logos, when rendered, then logos are cached on-device for instant rendering

**AI Component:** No

**Dependencies:** EPG Service (PRD-005) for current program metadata, Profile Service for favorites

**Technical Notes:**
- Channel logos bundled in a sprite sheet and cached locally
- Current program data fetched from EPG Service and refreshed on program boundaries

---

### US-LTV-006: Channel List Filtering

**As a** viewer
**I want to** filter the channel list by category (All, Favorites, Genre, Package)
**So that** I can quickly narrow down channels to find what I want to watch

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** LTV-FR-011

**Acceptance Criteria:**
- [ ] Given a viewer selects a filter (Favorites, Sports, News, Kids, Entertainment, Movies, Music, Documentary), when applied, then the list updates in < 100ms
- [ ] Given a filter is applied, when the viewer navigates within the filtered list, then channel-up/down only cycles through filtered channels
- [ ] Given a session, when a filter was previously applied, then the filter persists for the duration of the session

**AI Component:** No

**Dependencies:** EPG Service for genre assignment, Profile Service for favorites

**Technical Notes:**
- Filters applied client-side on pre-fetched channel list data
- Genre data sourced from EPG Service metadata

---

### US-LTV-007: Channel Favorites Management

**As a** viewer
**I want to** add or remove channels to/from a personal favorites list that syncs across all my devices
**So that** my preferred channels are always easily accessible

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** LTV-FR-012

**Acceptance Criteria:**
- [ ] Given a viewer toggles a channel as favorite, when the toggle completes, then the change is reflected immediately in the UI with server sync within 2s
- [ ] Given a viewer has favorites on one device, when opening the app on another device, then favorites are synced within 5s
- [ ] Given a profile, when favorites are managed, then a maximum of 50 favorites per profile is enforced
- [ ] Given AI ordering is enabled, when displaying channels, then favorites always appear at the top regardless of AI ordering mode

**AI Component:** No

**Dependencies:** Profile Service for persistence and cross-device sync

**Technical Notes:**
- Favorites stored per profile, not per device
- Optimistic UI update with background server sync

---

### US-LTV-008: Channel Badge Display

**As a** viewer
**I want to** see HD/UHD, audio format, and recording indicator badges on channels in the list
**So that** I can quickly identify channel quality and recording status

**Priority:** P1
**Phase:** 1
**Story Points:** S
**PRD Reference:** LTV-FR-014

**Acceptance Criteria:**
- [ ] Given a channel supports HD/UHD, when displayed in the list, then an appropriate badge (HD, UHD, 4K) is shown
- [ ] Given a channel has Dolby audio, when displayed, then a Dolby badge is shown
- [ ] Given a channel is currently being recorded by Cloud PVR, when displayed, then a recording indicator icon is visible
- [ ] Given badges are rendered, when the list loads, then badges appear inline without layout shift

**AI Component:** No

**Dependencies:** EPG Service for channel metadata, Recording Service (PRD-003) for recording status

**Technical Notes:**
- Badge data derived from channel metadata and current program metadata
- Recording indicator requires a lightweight polling or WebSocket subscription to Recording Service

---

## Epic 3: Mini EPG Overlay

### US-LTV-009: Mini EPG Display During Live Viewing

**As a** viewer
**I want to** see an info overlay with the current program name, time remaining, and next program while watching live TV
**So that** I can know what is on and what is coming up without leaving the player

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** LTV-FR-020

**Acceptance Criteria:**
- [ ] Given a viewer presses the info button or changes channel, when triggered, then the mini EPG overlay appears within 300ms
- [ ] Given the mini EPG is displayed, when 5 seconds pass without user interaction, then it auto-hides
- [ ] Given the overlay is shown, when rendered, then it does not obscure more than 25% of the video area
- [ ] Given the overlay shows current program info, when displayed, then it includes: title, start/end time, and a progress bar

**AI Component:** No

**Dependencies:** EPG Service (PRD-005) for program metadata

**Technical Notes:**
- Overlay renders as a client-side component on top of the video layer
- Program data pre-fetched and cached per channel

---

### US-LTV-010: Mini EPG Quick Actions

**As a** viewer
**I want to** access "Start Over," "Record," "Set Reminder," and "Full EPG" actions from the mini EPG overlay
**So that** I can interact with programs without navigating away from the player

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** LTV-FR-021

**Acceptance Criteria:**
- [ ] Given a viewer selects "Start Over" from mini EPG, when the program supports it, then playback transitions to TSTV start-over mode within 3s (handoff to PRD-002)
- [ ] Given a viewer selects "Record," when pressed, then the Cloud PVR recording workflow initiates within 2s (handoff to PRD-003)
- [ ] Given a viewer selects "Set Reminder" for the next program, when confirmed, then a reminder notification is scheduled
- [ ] Given "Start Over" is not available for the current program, when rendering the overlay, then the "Start Over" button is hidden (not grayed out)
- [ ] Performance: Action buttons respond within 200ms of press; "Start Over" availability check completes in < 100ms

**AI Component:** No

**Dependencies:** TSTV Service (PRD-002), Recording Service (PRD-003), EPG Service (PRD-005)

**Technical Notes:**
- "Start Over" availability determined by rights check against TSTV Service
- "Record" triggers Cloud PVR session creation via Recording Service API

---

### US-LTV-011: AI-Enhanced Mini EPG "Up Next for You"

**As a** viewer
**I want to** see an AI-suggested "Up Next for You" recommendation alongside the scheduled next program in the mini EPG
**So that** I can discover relevant content on other channels without browsing

**Priority:** P1
**Phase:** 2
**Story Points:** M
**PRD Reference:** LTV-FR-023

**Acceptance Criteria:**
- [ ] Given AI confidence for a suggestion exceeds 70%, when the mini EPG displays, then an "Up Next for You" suggestion appears alongside the scheduled next program
- [ ] Given a suggestion is shown, when displayed, then it includes a brief reason (e.g., "Popular right now" or "You usually watch news at this time")
- [ ] Given a viewer selects "Don't suggest this," when feedback is submitted, then the recommendation model incorporates the negative signal
- [ ] Given AI confidence is below 70%, when the mini EPG displays, then no AI suggestion is shown

**AI Component:** Yes -- Recommendation Service provides contextual "next channel" suggestion based on current viewing, time-of-day, and historical patterns

**Dependencies:** Recommendation Service (PRD-007), EPG Service (PRD-005)

**Technical Notes:**
- Suggestion fetched as part of mini EPG data from BFF
- Confidence threshold configurable per operator

---

## Epic 4: Trick-Play (Pause Live, Rewind)

### US-LTV-012: Pause Live TV

**As a** viewer
**I want to** pause live TV and resume from the paused point
**So that** I can take a break without missing content

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** LTV-FR-030

**Acceptance Criteria:**
- [ ] Given a viewer presses pause, when playing live, then video freezes within 200ms and a pause overlay is displayed
- [ ] Given a viewer presses play after pausing, when resumed, then playback continues from the paused point (time-shifted behind live)
- [ ] Given a viewer has been paused for more than 60 minutes (configurable), when the maximum pause duration is exceeded, then the player jumps to live with a notification
- [ ] Performance: Pause activates in < 200ms; buffer maintained server-side (CDN/origin)

**AI Component:** No

**Dependencies:** CDN live buffer infrastructure, Playback Session Service

**Technical Notes:**
- Buffer depth of 60 minutes maintained at origin/CDN level
- Buffer is per-channel at the CDN edge, not per-user

---

### US-LTV-013: Rewind Within Live Buffer

**As a** viewer
**I want to** rewind live TV at multiple speeds (2x, 4x, 8x, 16x, 32x) up to the buffer start
**So that** I can re-watch moments I missed during live viewing

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** LTV-FR-031

**Acceptance Criteria:**
- [ ] Given a viewer presses rewind, when playing or paused, then rewind initiates within 300ms at 2x speed
- [ ] Given a viewer presses rewind repeatedly, when cycling through speeds, then speed increases through 2x, 4x, 8x, 16x, 32x
- [ ] Given the viewer reaches the buffer start (60 minutes behind live), when at buffer boundary, then rewind stops and playback resumes at buffer start
- [ ] Given the viewer is rewinding, when a trick-play thumbnail strip is available, then thumbnail previews are displayed for navigation

**AI Component:** No

**Dependencies:** CDN live buffer, I-frame extraction for thumbnails

**Technical Notes:**
- Trick-play thumbnails generated from I-frames during live packaging
- Scrubber bar shows position relative to live edge

---

### US-LTV-014: Jump to Live

**As a** viewer
**I want to** press a "Jump to Live" button to return to the live edge instantly
**So that** I can get back to real-time viewing after pausing or rewinding

**Priority:** P0
**Phase:** 1
**Story Points:** S
**PRD Reference:** LTV-FR-032

**Acceptance Criteria:**
- [ ] Given a viewer is behind the live edge (paused or rewound), when pressing "Jump to Live," then playback returns to the live edge within 1s
- [ ] Given a viewer is behind live by more than 5 seconds, when the player controls are visible, then the "Jump to Live" button is prominently displayed
- [ ] Given a viewer is at the live edge, when the player controls are visible, then the "Jump to Live" button is hidden or dimmed

**AI Component:** No

**Dependencies:** US-LTV-012, US-LTV-013

**Technical Notes:**
- Jump to live resets the player to the latest segment in the manifest
- "LIVE" indicator animates/pulses when at the live edge

---

### US-LTV-015: Fast-Forward When Behind Live

**As a** viewer
**I want to** fast-forward at multiple speeds to catch up to the live edge after pausing or rewinding
**So that** I can quickly return to live without missing all intermediate content

**Priority:** P0
**Phase:** 1
**Story Points:** S
**PRD Reference:** LTV-FR-033

**Acceptance Criteria:**
- [ ] Given a viewer is behind live, when pressing fast-forward, then playback accelerates through 2x, 4x, 8x on repeated presses
- [ ] Given the viewer reaches the live edge during fast-forward, when live edge is reached, then the player automatically transitions to live mode with a "LIVE" indicator
- [ ] Given the viewer is at the live edge, when pressing fast-forward, then the button is disabled or hidden

**AI Component:** No

**Dependencies:** US-LTV-012, US-LTV-014

**Technical Notes:**
- Fast-forward speeds selectable via repeated remote button presses
- Transition to live mode should be seamless (no visible rebuffer)

---

## Epic 5: Audio, Subtitles, and Accessibility

### US-LTV-016: Multi-Audio Track Selection

**As a** viewer
**I want to** switch between available audio tracks (original, dubbed, audio description) during live playback
**So that** I can watch in my preferred language or access accessibility audio

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** LTV-FR-040

**Acceptance Criteria:**
- [ ] Given a viewer opens the audio menu, when available tracks are listed, then each track shows a human-readable language label (e.g., "English," "French (Original)," "English (Audio Description)")
- [ ] Given a viewer selects a different audio track, when the switch occurs, then audio changes within 500ms without stream restart or visible interruption
- [ ] Given a channel provides audio description, when the track is listed, then it appears with a distinct "AD" label

**AI Component:** No

**Dependencies:** Content packaging (CMAF multi-audio), player capabilities per platform

**Technical Notes:**
- Audio tracks embedded in the CMAF manifest as alternate renditions
- Switch handled at the player level by selecting a different rendition group

---

### US-LTV-017: Multi-Subtitle Track Selection

**As a** viewer
**I want to** enable, disable, or switch subtitle languages during live playback
**So that** I can follow content in my preferred language or access closed captions

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** LTV-FR-041, LTV-FR-042

**Acceptance Criteria:**
- [ ] Given a viewer selects a subtitle language, when applied, then subtitles appear within 300ms
- [ ] Given a viewer toggles subtitles off, when toggled, then subtitles disappear immediately with a single button press
- [ ] Given the platform supports CEA-608/708 (NA) and DVB subtitles (EU), when source feeds include these, then they are rendered correctly per platform
- [ ] Given a viewer customizes caption appearance (size, color, background), when applied, then changes render immediately per platform accessibility settings

**AI Component:** No

**Dependencies:** Content packaging (subtitle tracks), platform accessibility APIs

**Technical Notes:**
- Subtitle rendering follows platform-specific accessibility guidelines
- Caption customization integrates with OS-level accessibility settings

---

### US-LTV-018: Language Preference Persistence

**As a** viewer
**I want to** have my audio and subtitle preferences remembered across sessions and devices
**So that** I do not have to re-select my preferred language every time I tune to a channel

**Priority:** P1
**Phase:** 1
**Story Points:** M
**PRD Reference:** LTV-FR-043

**Acceptance Criteria:**
- [ ] Given a viewer sets a language preference, when tuning to a new channel in the same session, then the preferred audio and subtitle language are auto-selected if available
- [ ] Given a viewer's preferences are stored, when opening the app on another device, then the same preferences are applied
- [ ] Given a channel does not offer the preferred language, when tuning, then the platform selects the best available alternative and displays a brief notification

**AI Component:** Yes (Phase 2) -- AI learns per-context preferences (e.g., French audio on film channels, English on sports channels)

**Dependencies:** Profile Service for cross-device sync

**Technical Notes:**
- Default preferences stored per profile in Profile Service
- Phase 2: AI-enhanced per-channel-genre preference learning via Feature Store

---

## Epic 6: Playback Quality and Resilience

### US-LTV-019: Adaptive Bitrate Streaming

**As a** viewer
**I want to** experience smooth playback that automatically adjusts quality based on my network conditions
**So that** I have uninterrupted viewing with the best possible quality at all times

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** LTV-FR-050, LTV-FR-051

**Acceptance Criteria:**
- [ ] Given bandwidth degrades, when the ABR algorithm detects the change, then quality steps down within 2 seconds without rebuffering
- [ ] Given bandwidth recovers, when the ABR algorithm detects improvement, then quality steps up within 5 seconds (conservative to avoid oscillation)
- [ ] Given a device supports HEVC, when a manifest is served, then HEVC profiles are included; H.264 profiles are provided as fallback
- [ ] Given a Widevine L3 device, when manifest filtering occurs, then resolution is capped at 720p
- [ ] Performance: VMAF > 93 for 1080p HEVC; VMAF > 90 for 1080p H.264; rebuffer ratio < 0.3%

**AI Component:** No (standard ABR; see US-LTV-025 for ML-enhanced ABR)

**Dependencies:** CDN infrastructure, BFF manifest filtering, player ABR implementation per platform

**Technical Notes:**
- Server-side manifest filtering by BFF based on device capabilities reported at session creation
- ABR ladder defined in ARCH-001 Section 5

---

### US-LTV-020: Graceful Degradation on Feed Loss

**As an** operator
**I want to** display a branded "Temporarily Unavailable" slate when a channel's ingest feed fails
**So that** viewers see a professional message instead of a black screen or error code

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** LTV-FR-070

**Acceptance Criteria:**
- [ ] Given an ingest feed fails, when feed loss is detected, then a branded slate displays within 5 seconds
- [ ] Given a slate is displayed, when the feed recovers, then live playback auto-resumes within 5 seconds
- [ ] Given a slate is shown, when displayed, then it includes channel branding and a "We're working on it" message

**AI Component:** No

**Dependencies:** Ingest monitoring, encoder farm failover

**Technical Notes:**
- Slate is a pre-encoded segment injected by the packaging layer on feed loss detection
- Automatic failover to backup ingest path within 10 seconds

---

### US-LTV-021: CDN Failover

**As a** viewer
**I want to** experience seamless playback even when a CDN provider degrades
**So that** my viewing is not interrupted by infrastructure issues

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** LTV-FR-072

**Acceptance Criteria:**
- [ ] Given the primary CDN error rate exceeds 1% or p95 latency exceeds 500ms, when the CDN Routing Service detects degradation, then a mid-session CDN switch triggers
- [ ] Given a CDN switch occurs, when switching, then the switch completes in < 5 seconds with no rebuffer event
- [ ] Given all CDN Routing ML models are unavailable, when fallback is needed, then round-robin CDN selection with geo-affinity is used

**AI Component:** Yes -- CDN Routing ML model (XGBoost) evaluates CDN performance per session in real-time

**Dependencies:** CDN Routing Service, multi-CDN infrastructure (Akamai, CloudFront, Fastly)

**Technical Notes:**
- Pre-buffer segments from alternative CDN before switching
- CDN switch transparent to the user (manifest URL rewrite at BFF/token level)

---

### US-LTV-022: Player Error Recovery

**As a** viewer
**I want to** have the player automatically retry after transient errors without manual intervention
**So that** brief network glitches do not interrupt my viewing experience

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** LTV-FR-073

**Acceptance Criteria:**
- [ ] Given a transient playback error occurs (manifest fetch failure, segment decode failure), when the player retries with exponential backoff (1s, 2s, 4s, 8s), then automatic recovery succeeds within 15 seconds
- [ ] Given a persistent error remains after 4 retry attempts, when retries are exhausted, then a user-friendly error message displays with a "Try Again" button
- [ ] Given an error occurs, when logged, then error codes and context are sent to the telemetry pipeline for debugging

**AI Component:** No

**Dependencies:** Player implementation per platform, telemetry pipeline

**Technical Notes:**
- Retry logic includes DRM license re-acquisition on DRM errors
- Error categorization: transient (retry) vs. permanent (show error)

---

## Epic 7: Entitlements and Access Control

### US-LTV-023: Channel Entitlement Enforcement

**As a** viewer
**I want to** see only the channels I am entitled to watch, with clear messaging for premium channels
**So that** I understand my subscription and can upgrade if desired

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** LTV-FR-060

**Acceptance Criteria:**
- [ ] Given a viewer selects an entitled channel, when the entitlement check completes, then access is granted in < 30ms (from Entitlement Service cache)
- [ ] Given a viewer selects a non-entitled channel, when access is denied, then a clear "Upgrade to [package]" message is displayed with an upgrade CTA
- [ ] Given entitlement data is unavailable (service down), when access is checked, then fail-closed: deny access with "Service temporarily unavailable" message

**AI Component:** No

**Dependencies:** Entitlement Service (ARCH-001)

**Technical Notes:**
- Entitlement checks use Redis-cached data for low latency
- Fail-closed approach for security; no fallback to permissive access

---

### US-LTV-024: Parental Controls for Live Channels

**As a** parent
**I want to** restrict age-inappropriate live channels from my child's profile so they are completely invisible
**So that** my children cannot access or even see restricted content

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** Scenario 6 (Parental Controls)

**Acceptance Criteria:**
- [ ] Given a Kids profile with PG maximum rating, when the channel list is displayed, then channels rated above PG are completely invisible (not present in list, not searchable)
- [ ] Given a child enters a restricted channel number directly, when submitted, then a "Content not available on this profile" message appears with no preview or metadata leakage
- [ ] Given a parent wants to unlock adult content, when switching profiles with a PIN (4-6 digits), then PIN entry completes within 5 seconds and profile switches
- [ ] Given a PIN entry screen, when idle for 30 seconds, then it times out and returns to the Kids profile

**AI Component:** No

**Dependencies:** Profile Service (parental control settings), Entitlement Service

**Technical Notes:**
- Parental controls enforced consistently across Live TV, EPG, TSTV, and VOD
- Restricted channels filtered server-side in BFF, not just client-side

---

## Epic 8: AI-Powered Features

### US-LTV-025: AI Personalized Channel Order

**As a** viewer
**I want to** have my channel list automatically ordered by AI-predicted relevance based on my viewing habits and the current time of day
**So that** the channels I am most likely to watch appear first

**Priority:** P1
**Phase:** 1
**Story Points:** XL
**PRD Reference:** LTV-FR-013, AI Section 5.1, AI Section 5.3

**Acceptance Criteria:**
- [ ] Given AI ordering is enabled, when the channel list loads, then channels are sorted by predicted relevance for the active profile
- [ ] Given time-of-day changes (e.g., morning to evening), when the list refreshes, then channel order updates to reflect temporal patterns (sports higher in evening, news higher in morning)
- [ ] Given a viewer toggles between "Smart Order" and "Numeric Order" in settings, when toggled, then the list re-sorts immediately
- [ ] Given favorites are set, when AI ordering is active, then favorites always appear at the top regardless of AI rank
- [ ] Given the Recommendation Service is unavailable, when fallback occurs, then the channel list defaults to numeric order with favorites first
- [ ] Performance: AI ranking adds < 50ms latency to channel list API response; list cached in Redis per user per 30-minute window

**AI Component:** Yes -- TensorFlow two-tower model (user tower + channel-context tower) served via KServe with < 30ms inference; trained on viewing session data every 6 hours

**Dependencies:** Recommendation Service (PRD-007), Feature Store (Feast), KServe inference cluster

**Technical Notes:**
- Model inputs: user viewing history, time-of-day, day-of-week, channel metadata
- Feature Store maintains per-user temporal features: channel affinity per 2-hour window per day-of-week
- A/B test framework required to validate +20% engagement lift target

---

### US-LTV-026: Live Popularity Signals ("Trending Live")

**As a** viewer
**I want to** see real-time viewer counts and trending indicators on live channels
**So that** I can discover popular live content and feel the social buzz of live events

**Priority:** P1
**Phase:** 1
**Story Points:** L
**PRD Reference:** AI Section 5.2

**Acceptance Criteria:**
- [ ] Given a viewer opens the home screen, when a "Trending Live" rail is displayed, then it shows the top 10 channels ranked by weighted score (60% absolute viewers, 40% trend velocity)
- [ ] Given viewer counts are displayed, when updated, then they are accurate within +/- 5% and refresh every 30 seconds
- [ ] Given a channel's viewership increases by > 50% in 5 minutes, when a spike is detected, then opted-in users receive a notification ("Breaking: [Event] -- 45K viewers watching now")
- [ ] Given operator configuration disables viewer counts, when configured, then viewer counts are hidden and "Trending Live" rail uses trend signals only

**AI Component:** Yes -- Flink streaming job computes real-time viewer counts, trend velocity, and spike detection from Playback Session Service events

**Dependencies:** Playback Session Service, Flink streaming pipeline, Redis for aggregated data, Notification Service

**Technical Notes:**
- Data pipeline: Playback Session Service -> Kafka (playback.sessions) -> Flink -> Redis -> BFF -> Client
- Spike threshold and notification frequency capping configurable per operator

---

### US-LTV-027: AI Quality Monitoring and Anomaly Detection

**As an** operator
**I want to** have ML-based anomaly detection monitoring every live channel in real-time
**So that** quality degradation is detected and remediated before viewers file complaints

**Priority:** P1
**Phase:** 2
**Story Points:** XL
**PRD Reference:** AI Section 5.5

**Acceptance Criteria:**
- [ ] Given a channel's quality degrades, when the anomaly detection model detects an anomaly, then an alert is generated within 60 seconds of degradation onset
- [ ] Given alerts are generated, when analyzed over time, then the false positive rate is < 5%
- [ ] Given an Emergency-severity anomaly (feed loss), when detected, then automated remediation (encoder restart, feed failover) triggers within 30 seconds
- [ ] Given the anomaly model, when retraining, then it retrains weekly on the latest quality data
- [ ] Given detection coverage, when monitoring, then audio sync, video artifacts, bitrate anomalies, feed loss, encoder failures, and CDN degradation are all covered

**AI Component:** Yes -- PyTorch autoencoder model trained on normal quality patterns per channel per time-of-day; evaluated every 30 seconds

**Dependencies:** QoE Service (ClickHouse + Flink), Conviva SDK (client-side), PagerDuty for alerting

**Technical Notes:**
- Anomaly severity levels: Warning (investigate), Critical (confirmed user impact), Emergency (auto-remediate)
- Client-side metrics: Conviva SDK; server-side metrics: encoder health, ingest status, CDN delivery rates

---

### US-LTV-028: ML-Enhanced ABR

**As a** viewer
**I want to** experience smarter adaptive bitrate streaming that predicts bandwidth changes and optimizes for content type
**So that** I have fewer rebuffering events and better overall video quality

**Priority:** P2
**Phase:** 3
**Story Points:** XL
**PRD Reference:** LTV-FR-053

**Acceptance Criteria:**
- [ ] Given ML-enhanced ABR is enabled, when compared to standard ABR in A/B test, then rebuffer events are reduced by 25%
- [ ] Given ML-enhanced ABR is active, when compared to standard ABR, then average delivered bitrate increases by 8%
- [ ] Given sports content is playing, when ABR decisions are made, then framerate is prioritized over resolution
- [ ] Given drama content is playing, when ABR decisions are made, then resolution is prioritized over framerate
- [ ] Given the ML ABR model is unavailable, when inference fails, then the player falls back to standard ABR algorithm seamlessly

**AI Component:** Yes -- KServe-served ABR model (XGBoost or lightweight neural net) with < 10ms inference latency; predicts bandwidth trajectory and considers content complexity

**Dependencies:** KServe inference cluster, Feature Store (historical QoE per device/ISP), EPG metadata (content type)

**Technical Notes:**
- Model runs at CDN Routing Service level, parameters passed to client at session creation
- Content classification: sports, news, entertainment, kids derived from EPG metadata

---

## Epic 9: Non-Functional and Technical Enablers

### US-LTV-029: Live TV Telemetry and Observability

**As a** developer
**I want to** have comprehensive client-side and server-side telemetry for all live TV sessions
**So that** we can monitor performance, detect issues, and measure success metrics

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** NFR Section 6, Metrics Section 9

**Acceptance Criteria:**
- [ ] Given any live TV session, when telemetry is captured, then the following client-side events are recorded: channel tune time, time-to-first-frame, rebuffer events, bitrate changes, errors, trick-play actions
- [ ] Given Conviva SDK integration, when reporting, then QoE metrics are available per session within 30 seconds
- [ ] Given server-side metrics, when reported, then Playback Session Service RPS, error rates, and latency (p50, p95, p99) are available in Grafana
- [ ] Performance: Telemetry collection adds < 1% overhead to client resource usage

**AI Component:** No

**Dependencies:** Conviva SDK, Prometheus + Grafana, Kafka telemetry pipeline

**Technical Notes:**
- Client-side: Conviva SDK for QoE, custom events for business metrics
- Server-side: Prometheus metrics from each microservice, structured logs to centralized aggregation

---

### US-LTV-030: Emergency Alert System Integration

**As a** viewer
**I want to** receive emergency alerts (severe weather, AMBER alerts) while watching live TV
**So that** I am informed of emergencies in my geographic area

**Priority:** P1
**Phase:** 1
**Story Points:** L
**PRD Reference:** Scenario 9 (EAS), LTV-FR-070

**Acceptance Criteria:**
- [ ] Given an EAS alert is triggered for a geographic region, when the viewer is in the affected region, then the alert overlay displays within 10 seconds
- [ ] Given a mandatory alert, when displayed, then the viewer cannot dismiss it until the mandated duration expires
- [ ] Given a channel carries in-band EAS (SCTE-35), when the signal is present, then the native broadcast alert is passed through
- [ ] Given a channel without in-band EAS, when an alert is triggered, then a server-side overlay is injected
- [ ] Given alert delivery, when logged, then all alert deliveries are recorded for regulatory compliance

**AI Component:** No

**Dependencies:** EAS API integration, geo-location service (IP-based, 95%+ accuracy)

**Technical Notes:**
- EAS overlay injected server-side for channels without in-band signals
- Alert does not interrupt ongoing Cloud PVR recordings

---

### US-LTV-031: Blackout Enforcement

**As an** operator
**I want to** enforce geographic blackout rules on specific programs
**So that** territorial content rights are respected and regulatory compliance is maintained

**Priority:** P1
**Phase:** 1
**Story Points:** M
**PRD Reference:** LTV-FR-062

**Acceptance Criteria:**
- [ ] Given a program is blacked out in the viewer's region, when the viewer is watching the channel, then a blackout message displays with an explanation and alternative viewing options
- [ ] Given blackout rules, when evaluated, then they are checked per-program using SCTE-35 markers or EPG metadata
- [ ] Given geo-location, when determined, then IP-based location is accurate to 95%+ for region determination

**AI Component:** No

**Dependencies:** EPG Service (blackout metadata), geo-location service

**Technical Notes:**
- Blackout rules evaluated server-side during session creation and at program boundaries
- Alternative viewing suggestions (e.g., "Watch on [alternative channel]") sourced from EPG metadata

---

### US-LTV-032: Picture-in-Picture While Browsing

**As a** viewer
**I want to** shrink the live channel into a PiP window while browsing the EPG, recordings, or VOD catalog
**So that** I can explore other content without losing sight of the live action

**Priority:** P1
**Phase:** 2
**Story Points:** L
**PRD Reference:** Scenario 4 (PiP)

**Acceptance Criteria:**
- [ ] Given a viewer presses Home while watching live, when PiP is supported, then the live channel shrinks to a PiP window in < 500ms
- [ ] Given PiP is active, when the viewer browses EPG/VOD/recordings, then live audio continues uninterrupted
- [ ] Given PiP is active, when the viewer presses "Return to Full Screen," then full-screen live viewing resumes in < 300ms
- [ ] Given PiP has been active for 10 minutes (configurable), when the timer expires, then a "Still watching?" prompt appears before auto-closing
- [ ] Performance: PiP video quality minimum 540p

**AI Component:** No

**Dependencies:** Platform-specific PiP APIs (Android TV, Apple TV, Web)

**Technical Notes:**
- PiP implementation varies significantly per platform
- Consider phased rollout per platform based on implementation complexity

---

### US-LTV-033: Intelligent Buffer Management

**As a** viewer
**I want to** have the player's buffer depth automatically optimized based on content type and network conditions
**So that** sports content has minimal latency while other content has maximum quality stability

**Priority:** P2
**Phase:** 2
**Story Points:** L
**PRD Reference:** AI Section 5.4

**Acceptance Criteria:**
- [ ] Given sports content is playing, when buffer parameters are set, then buffer depth is 1-2 seconds (LL-HLS) to minimize latency
- [ ] Given standard content is playing, when buffer parameters are set, then buffer depth is 3-6 seconds for quality stability
- [ ] Given the buffer ML model is active, when compared to fixed buffer in A/B test, then rebuffer rate is reduced by 15%
- [ ] Given buffer parameters, when determined at session creation, then the decision adds < 10ms latency
- [ ] Given the buffer model is unavailable, when fallback occurs, then default buffer of 3 seconds is used

**AI Component:** Yes -- XGBoost classification model at CDN Routing Service; inputs: content type, network type, ISP, device type, historical QoE

**Dependencies:** CDN Routing Service, Feature Store, EPG metadata (content type)

**Technical Notes:**
- Buffer parameters returned in playback session creation response
- Model inputs sourced from Feature Store (historical QoE per device/ISP) and EPG (content type)

---

### US-LTV-034: Channel Upsell for Non-Entitled Channels

**As a** viewer
**I want to** see a brief preview and clear upgrade prompt when I try to access a channel outside my subscription
**So that** I can make an informed decision about upgrading my package

**Priority:** P1
**Phase:** 2
**Story Points:** M
**PRD Reference:** LTV-FR-061

**Acceptance Criteria:**
- [ ] Given a viewer selects a non-entitled channel, when the channel loads, then a 5-second DRM-protected preview (or blurred feed) is shown followed by an upgrade prompt
- [ ] Given an upgrade prompt, when displayed, then it includes the package name, price, and key content highlights
- [ ] Given Phase 3 AI upsell, when enabled, then the AI selects the most persuasive upsell message per user (e.g., "This package includes 12 sports channels you watch regularly")

**AI Component:** Yes (Phase 3) -- AI-selected persuasive messaging based on user engagement patterns

**Dependencies:** Entitlement Service, payment/subscription service, Recommendation Service (Phase 3)

**Technical Notes:**
- Preview is time-limited (5 seconds) and DRM-protected to prevent content piracy
- Upsell CTA deep-links to subscription management flow

---

*End of User Stories for PRD-001: Live TV & Linear Channels*
*Total: 28 stories (14 core functional, 7 AI enhancement, 4 non-functional, 3 technical/integration)*
