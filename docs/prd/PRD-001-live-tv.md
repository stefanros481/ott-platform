# PRD-001: Live TV & Linear Channels
## AI-Native OTT Streaming Platform

**Document ID:** PRD-001
**Version:** 1.0
**Date:** 2026-02-08
**Status:** Draft
**Author:** PRD Writer A
**References:** VIS-001 (Project Vision & Design), ARCH-001 (Platform Architecture)
**Stakeholders:** Product Management, Engineering (Platform, Client, AI/ML), Content Operations, SRE

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

Live TV is the core linear television delivery service of the AI-native OTT streaming platform. It delivers 200+ live channels to subscribers over IP, replacing or complementing traditional satellite/cable feeds with a fully software-defined, cloud-native delivery chain. The service ingests live feeds from satellite, fiber, and IP sources, transcodes them in real-time using redundant encoder infrastructure, packages content into CMAF segments (serving both HLS and DASH manifests), and delivers segments to clients via a multi-CDN topology secured with Common Access Token (CAT) authentication.

What differentiates this live TV service from legacy OTT live implementations is the AI layer woven into every aspect of the experience: from how channels are ordered on screen to how the CDN routes segments, from how the player selects bitrates to how operations teams detect and resolve quality issues. AI is not a feature added to live TV -- it is integral to how live TV works.

### Business Context

Live TV remains the anchor service for pay-TV subscribers. Despite the growth of on-demand consumption, live content -- particularly sports, news, and tentpole events -- drives 55-65% of total viewing hours on traditional platforms and is the primary reason subscribers maintain their subscriptions. In churn analysis across the industry, loss of live sports is the single highest-correlated factor with subscription cancellation.

For this platform, Live TV serves three strategic purposes:
1. **Subscriber acquisition and retention**: Live sports, news, and events are the primary draw for new subscribers and the strongest retention lever.
2. **Gateway to AI-enhanced features**: Live TV viewing generates high-frequency engagement signals (channel changes, viewing duration per channel, time-of-day patterns) that feed the recommendation engine and personalization models across the entire platform.
3. **Integration anchor**: Live TV connects directly to TSTV (Start Over, Catch-Up), Cloud PVR (record from live), EPG (program guide), and the AI recommendation engine, making it the hub of the cross-service experience.

### Scope

**In Scope:**
- Live linear channel acquisition, transcoding, packaging, and delivery
- Channel list management, ordering, and favorites
- Live playback with trick-play (pause live, rewind within buffer)
- Multi-audio and multi-subtitle track selection
- Mini EPG overlay during live viewing
- Channel change experience and performance optimization
- AI-powered channel surfing, discovery, and personalization
- Low-latency live (LL-HLS) for sports and events
- Emergency Alert System (EAS) integration
- Parental controls for live channels
- Integration points with TSTV, Cloud PVR, and EPG services

**Out of Scope:**
- FAST (Free Ad-Supported Television) channels -- separate future PRD
- Server-side ad insertion for live channels -- covered in monetization/ad service PRD
- Detailed EPG grid functionality -- covered in PRD-005 (EPG)
- Start Over and Catch-Up TV features -- covered in PRD-002 (TSTV)
- Recording from live -- covered in PRD-003 (Cloud PVR)
- Multi-angle camera selection for sports -- Phase 3+ consideration
- Interactive overlays (voting, shopping) -- Phase 4 consideration

---

## 2. Goals & Non-Goals

### Goals

1. **Deliver 200+ live channels** with broadcast-grade reliability (99.95% per-channel availability) and quality (VMAF > 90 for HD channels).
2. **Achieve channel change time < 1.5 seconds (p95)** from user input to first frame rendered, competitive with traditional set-top box experience.
3. **Support standard and low-latency live delivery**: < 5 seconds glass-to-glass for standard channels, < 3 seconds for LL-HLS sports/events channels.
4. **AI-enhance the live viewing experience** with personalized channel ordering, smart channel surfing suggestions, real-time popularity signals, and intelligent buffer management.
5. **Seamlessly integrate with adjacent services**: EPG (program metadata), TSTV (start-over and catch-up), Cloud PVR (record from live), ensuring fluid transitions between live and time-shifted modes.
6. **Support multi-audio and multi-subtitle** for all channels where source material provides them, including accessibility tracks (audio description, closed captions).
7. **Deliver consistent quality across all client platforms**: Android TV, Apple TV, Web, iOS, Android, with platform-appropriate codec negotiation and resolution management.
8. **Provide real-time AI quality monitoring** per channel with automated detection of quality degradation, feed loss, and encoder issues within 60 seconds.

### Non-Goals

1. **FAST channels**: Free ad-supported linear channels are a distinct product with different ingest, monetization, and content rights models. They will be addressed in a separate PRD.
2. **Live ad insertion (SSAI)**: Server-side ad insertion into live streams is a monetization concern covered by the Ad Service PRD. This PRD covers the manifest and segment delivery infrastructure that SSAI will hook into.
3. **Interactive live features**: Viewer polls, live shopping overlays, synchronized social features, and gamification during live events are Phase 4+ features not covered here.
4. **IP multicast delivery**: The platform uses unicast OTT delivery exclusively. Managed multicast (e.g., for operator STBs on managed networks) is out of scope.
5. **Live-to-VOD conversion**: Automated clipping and publishing of live content as VOD assets is a content operations workflow not covered in this PRD.

---

## 3. User Scenarios

### Scenario 1: Evening Channel Surfing with AI Suggestions

**Persona:** Thomas (Casual Viewer)
**Context:** Thomas turns on his Samsung Smart TV at 8 PM after dinner. He wants to watch something live but does not know what is on.

**Flow:**
1. Thomas opens the app. The home screen shows a "Live Now" rail at the top, AI-curated with programs predicted to interest Thomas based on his viewing history and the current time of day. The rail shows: a nature documentary on Channel 12, the evening news on Channel 3, and a classic film on Channel 45.
2. He selects the nature documentary. The channel starts playing within 1.2 seconds.
3. While watching, a subtle "Next for You" overlay appears in the corner during a commercial break, suggesting "Classic Film Festival on Channel 45 starts in 10 minutes."
4. Thomas presses the channel-up button. Instead of going to Channel 13 (the next sequential channel), the AI-ordered channel list takes him to Channel 3 (evening news), which the AI predicts is his next most likely watch based on time-of-day and historical patterns.
5. After watching news for 20 minutes, he returns to the channel list. The channel he was watching before (Channel 12) shows a "Resume" indicator with the current program progress.

**Success Criteria:** Thomas finds something to watch within 30 seconds without browsing the EPG. Channel changes complete in < 1.5s. AI channel ordering reflects his demonstrated time-of-day preferences.

---

### Scenario 2: Joining a Live Sports Event Mid-Stream

**Persona:** Erik (Sports Fan)
**Context:** Erik arrives home 25 minutes late for a Champions League football match. He opens the app on his Android TV.

**Flow:**
1. A prominent notification is visible on the home screen: "Champions League: Real Madrid vs Bayern Munich -- LIVE NOW (25 min in). Start from kick-off?"
2. Erik selects "Start from kick-off," which initiates a TSTV Start Over session (handoff to PRD-002).
3. Alternatively, Erik selects "Watch Live." The channel starts in LL-HLS mode with < 3 second delay from broadcast.
4. During the match, Erik presses the info button. A mini EPG overlay shows: current match details, score (if enabled), and upcoming program. Action buttons include: "Start Over," "Record Rest of Match," and "Picture-in-Picture."
5. At half-time, Erik's phone shows a notification: "Half-time stats available -- open companion app." (Second screen integration, Phase 3.)

**Success Criteria:** Erik is watching live within 2 seconds of selecting "Watch Live." Live delay is < 3 seconds behind broadcast. Start Over handoff to TSTV completes in < 3 seconds.

---

### Scenario 3: Multi-Audio and Accessibility Selection

**Persona:** Maria (Busy Professional)
**Context:** Maria is watching a French-language film broadcast live on a premium channel. She prefers to watch in original French audio with English subtitles. Maria's elderly mother, who is hard of hearing, visits and they switch to the English audio description track.

**Flow:**
1. Maria tunes to Channel 87 (Premium Film). The channel starts playing in the default audio track (French original).
2. Maria opens the audio/subtitle menu (accessible via the player controls or a dedicated remote button).
3. Available options display: Audio: French (Original), English (Dub), English (Audio Description). Subtitles: Off, English, French, Dutch, German.
4. Maria selects French audio + English subtitles. The change applies within 500ms without interrupting playback or restarting the stream.
5. When her mother arrives, Maria switches to "English (Audio Description)." The platform remembers this preference for this specific combination (Channel 87, film genre) for future sessions.

**Success Criteria:** Audio/subtitle changes apply in < 500ms without stream restart. Available tracks accurately reflect what the source feed provides. The platform learns language preferences per context (channel, genre, time).

---

### Scenario 4: Picture-in-Picture While Browsing

**Persona:** Erik (Sports Fan)
**Context:** Erik is watching a football match but wants to check what else is on without losing sight of the live action.

**Flow:**
1. While watching Channel 5 (live football), Erik presses the "Home" button on his remote.
2. The live channel shrinks into a picture-in-picture (PiP) window in the corner of the screen. Live audio continues.
3. Erik browses the EPG, checks his recordings, and looks at the VOD catalog -- all while the PiP continues showing the live match.
4. When a goal is scored, Erik notices the action in PiP and presses a "Return to Full Screen" shortcut to instantly go back to full-screen live viewing.
5. PiP remains available for a configurable duration (default 10 minutes) before auto-closing with a "Still watching?" prompt.

**Success Criteria:** PiP activates in < 500ms. PiP video quality is appropriate for reduced size (min 540p). Live audio continues uninterrupted. Return to full-screen is < 300ms.

---

### Scenario 5: "What's Popular Right Now" Live Discovery

**Persona:** Priya (Binge Watcher)
**Context:** Priya does not regularly watch live TV but sees a "Trending Live" rail on the home screen showing a spike in viewers for a particular channel. She is curious.

**Flow:**
1. Priya opens the app and notices a "Trending Live" rail showing real-time popularity signals. The rail indicates: "Breaking News -- 45K viewers" (Channel 3), "Champions League Final -- 120K viewers" (Channel 5), "Season Finale of The Bridge -- 28K viewers" (Channel 22).
2. Viewer counts update in near-real-time (every 30 seconds). A subtle trend indicator shows if viewership is rising or falling.
3. Priya selects the season finale. Because she has not watched this series, an AI-generated context card appears: "Season 4 finale of The Bridge. Previously: [brief AI summary]. You can catch up on Seasons 1-3 on demand."
4. She decides to watch live. The channel starts within 1.5 seconds.
5. After the episode ends, the platform suggests: "Want to watch The Bridge from Season 1? First episode available now." (Cross-service handoff to VOD.)

**Success Criteria:** Viewer counts are accurate within +/- 5% and update every 30 seconds. Context card appears within 200ms of channel selection. AI summary is factually accurate and spoiler-conscious.

---

### Scenario 6: Parental Controls on Live Content

**Persona:** The Okafor Family
**Context:** 8-year-old Tobi is watching cartoons on the living room TV using the Kids profile. He tries to access an adult channel.

**Flow:**
1. Tobi is watching Channel 8 (Kids). He presses channel-up and navigates toward Channel 15 (rated 16+).
2. The platform detects that the active profile (Kids - Tobi) has a maximum rating of PG. Channel 15 does not appear in the channel list at all -- the list skips from Channel 14 (PG-rated) to Channel 18 (PG-rated).
3. If Tobi enters the channel number directly (1-5), a "Content not available on this profile" message appears with no preview or metadata about the blocked channel.
4. David (parent) can unlock by switching to his profile using a PIN (4-6 digits). The PIN entry UI times out after 30 seconds and returns to the Kids profile.
5. The parental control system works identically across live TV, EPG, TSTV catch-up, and VOD -- blocked content is invisible, not just inaccessible.

**Success Criteria:** Age-restricted channels are completely invisible to restricted profiles (not present in channel list, not searchable, no metadata leakage). PIN switch completes within 5 seconds. Parental controls are enforced consistently across all content sources.

---

### Scenario 7: Recording from Live (Handoff to Cloud PVR)

**Persona:** The Okafor Family (David)
**Context:** David is watching a live football match and realizes he needs to leave before it ends. He wants to record the rest.

**Flow:**
1. During live viewing, David presses the "Record" button on his remote (or selects "Record" from the player overlay menu).
2. A recording options panel appears: "Record this program" (records from now to scheduled end), "Record from beginning" (if Start Over content is available, records the entire program), "Record series" (series-link if applicable).
3. David selects "Record this program." A confirmation appears: "Recording Champions League Semi-Final. Estimated: 67 minutes remaining. Storage used: 82/100 hours."
4. A subtle recording indicator icon appears on the player overlay.
5. David leaves. The Cloud PVR service (PRD-003) continues recording the remainder of the program from the live feed.
6. When David returns, he can resume watching from where he left off, with the recording available in his PVR library.

**Success Criteria:** Recording initiation completes in < 2 seconds. Recording starts within 5 seconds of the user action. Storage quota feedback is immediate and accurate. Handoff to Cloud PVR is seamless from the user's perspective.

---

### Scenario 8: Graceful Degradation Under Network Stress

**Persona:** Maria (Busy Professional)
**Context:** Maria is watching a live channel on her iPhone during her commute. The train enters a tunnel with degraded cellular connectivity.

**Flow:**
1. Maria is watching at 720p on her iPhone over LTE.
2. The train enters a tunnel. Bandwidth drops from 8 Mbps to 1.5 Mbps.
3. The ABR algorithm (ML-enhanced) detects the bandwidth decline within 2 seconds and switches to 480p (1,500 kbps H.264), maintaining continuous playback with no rebuffer event.
4. Bandwidth drops further to 500 kbps. The player steps down to 360p (800 kbps). A subtle "Low quality" indicator appears but playback continues.
5. If bandwidth drops below the minimum viable quality (240p at 400 kbps), the player pauses with a "Waiting for connection..." message rather than showing frozen or heavily pixelated video.
6. When the train exits the tunnel and bandwidth recovers, the player ramps back up to 720p within 10 seconds. The "Low quality" indicator disappears.

**Success Criteria:** Zero rebuffer events during gradual bandwidth decline. Resolution step-down occurs within 2 seconds of bandwidth change detection. Recovery to maximum sustainable quality within 10 seconds of bandwidth improvement. No audio interruption during quality transitions.

---

### Scenario 9: Emergency Alert System Integration

**Persona:** All viewers
**Context:** A national emergency alert is issued (e.g., severe weather warning, AMBER alert). The platform must display the alert to all affected viewers.

**Flow:**
1. The EAS system triggers an alert for a specific geographic region.
2. All live TV viewers in the affected region see an alert overlay on their screen, regardless of which channel they are watching. The overlay includes the alert text, severity level, and an audio tone (following national EAS standards).
3. For channels that carry the EAS signal in-band (SCTE-35 markers), the native broadcast alert is passed through.
4. For channels without in-band EAS, the platform injects a server-side overlay triggered by the EAS API integration.
5. The alert remains on screen for the mandated duration. Viewers cannot dismiss mandatory alerts. Informational alerts can be acknowledged and dismissed.
6. Alert delivery is logged for regulatory compliance reporting.

**Success Criteria:** Alert displayed within 10 seconds of EAS trigger. 100% of affected viewers receive the alert. Alert does not interrupt ongoing recordings (Cloud PVR). Compliance with national EAS regulations.

---

### Scenario 10: Channel Resolution and Codec Negotiation

**Persona:** All viewers (system scenario)
**Context:** Different devices have different capabilities. The platform must deliver the best possible quality per device without manual configuration.

**Flow:**
1. A viewer starts a live channel on an Apple TV 4K (supports HEVC, 4K HDR, Dolby Vision).
2. The BFF (TV BFF) returns the channel manifest URL. The manifest includes all available profiles: 4K HEVC HDR, 1080p HEVC, 1080p H.264, 720p, etc.
3. The player (AVPlayer) negotiates the highest quality its hardware supports and the network can sustain. Starting with 1080p HEVC (fast start), ramping to 4K HDR within 10 seconds if bandwidth permits.
4. A viewer on a web browser (Chrome, Widevine L3 -- software DRM) receives a manifest limited to 720p H.264 (L3 security level restriction). No 4K or HEVC profiles are included.
5. A viewer on an older Android phone (H.264 only, Widevine L3) receives a manifest with H.264 profiles up to 540p.
6. The BFF performs capability-based manifest filtering server-side, ensuring clients never see profiles they cannot play, reducing client-side complexity and error surfaces.

**Success Criteria:** Correct codec and resolution negotiation for 100% of supported device/DRM combinations. No playback failures due to unsupported codec delivery. Server-side manifest filtering matches the device capability matrix defined in ARCH-001 Section 7.

---

## 4. Functional Requirements

### 4.1 Channel Acquisition and Tuning

| Req ID | Description | Priority | Phase | AI Enhancement | Acceptance Criteria |
|--------|-------------|----------|-------|---------------|-------------------|
| LTV-FR-001 | Channel selection and playback initiation from channel list, EPG, deep link, or channel number entry | P0 | 1 | -- | Channel starts playing within 1.5s (p95) from user input to first rendered frame. Verified across Android TV, Apple TV, and Web. |
| LTV-FR-002 | Channel-up / channel-down navigation cycling through the user's channel list | P0 | 1 | AI-ordered channel list determines next/previous channel | Channel transition completes within 1.5s (p95). Channel order respects AI-personalized ordering (if enabled) or sequential numbering (fallback). |
| LTV-FR-003 | Direct channel number entry via remote control numeric keypad or on-screen input | P0 | 1 | -- | 3-digit channel number entry with 1.5s auto-commit timeout. Channel tunes within 1.5s of final digit. Invalid channel numbers display "Channel not available" message. |
| LTV-FR-004 | Last channel recall ("Back" or dedicated button returns to previously watched channel) | P1 | 1 | -- | Switching between two channels completes in < 1.5s each direction. History depth: minimum 5 channels. |
| LTV-FR-005 | Fast channel zapping preview: while browsing the channel list, a thumbnail preview of the live channel appears before committing to a full tune | P1 | 2 | -- | Preview appears within 2s of highlighting a channel in the list. Preview resolution: minimum 360p. Preview does not consume a full playback session (lightweight preview mechanism). |

### 4.2 Channel List Management

| Req ID | Description | Priority | Phase | AI Enhancement | Acceptance Criteria |
|--------|-------------|----------|-------|---------------|-------------------|
| LTV-FR-010 | Display channel list with channel number, name, logo, and current program information | P0 | 1 | -- | Channel list renders within 500ms. Current program title and time remaining displayed for each visible channel. Channel logos are cached on-device for instant rendering. |
| LTV-FR-011 | Filter channel list by: All, Favorites, Package/Tier, Genre (Sports, News, Kids, Entertainment, Movies, Music, Documentary) | P0 | 1 | -- | Filter application is instant (< 100ms). Genre assignment is maintained by the EPG Service. Filters persist per session. |
| LTV-FR-012 | User-managed favorites: add/remove channels to favorites list, with favorites persisted per profile across devices | P0 | 1 | -- | Favorite toggle is immediate with server sync within 2s. Maximum 50 favorites per profile. Favorites sync across all devices within 5s of change. |
| LTV-FR-013 | AI-personalized channel ordering: channels sorted by predicted relevance for the active viewer profile, considering viewing history, time-of-day, and day-of-week patterns | P1 | 1 | Recommendation Service scores channels per user per time window | AI-ordered list updates on app launch and every 30 minutes during active sessions. User can toggle between AI order and numeric order. Favorites always appear at the top regardless of ordering mode. |
| LTV-FR-014 | Channel list displays HD/UHD badge, audio format badge (Dolby, stereo), and recording indicator (if the channel is being recorded) | P1 | 1 | -- | Badges are derived from channel metadata and current program metadata. Badges render inline without layout shift. |

### 4.3 Mini EPG Overlay

| Req ID | Description | Priority | Phase | AI Enhancement | Acceptance Criteria |
|--------|-------------|----------|-------|---------------|-------------------|
| LTV-FR-020 | Mini EPG overlay during live viewing showing: current program (title, start/end time, progress bar), next program, and channel name/number | P0 | 1 | -- | Overlay appears within 300ms of trigger (info button, channel change, or auto-show). Auto-hides after 5 seconds of inactivity. Does not obscure more than 25% of the video area. |
| LTV-FR-021 | Mini EPG provides quick-action buttons: "Start Over" (if available per PRD-002), "Record" (handoff to PRD-003), "Set Reminder" for next program, "Full EPG" navigation | P0 | 1 | -- | Action buttons respond within 200ms of press. "Start Over" availability determined by rights check in < 100ms. "Record" initiates PVR workflow per PRD-003. |
| LTV-FR-022 | Mini EPG shows program ratings (age rating, content advisory) and availability indicators (catch-up available, recordable) | P1 | 1 | -- | Ratings sourced from EPG Service metadata. Availability indicators accurately reflect current rights status. |
| LTV-FR-023 | AI-enhanced mini EPG: "Up Next for You" suggestion shown alongside the scheduled next program, recommending a different channel if the AI predicts higher relevance | P1 | 2 | Recommendation Service provides a contextual "next channel" suggestion based on current viewing and time | Suggestion appears only when confidence > 70%. Includes brief reason ("Popular right now" or "You usually watch news at this time"). Dismissible, with "Don't suggest this" feedback option. |

### 4.4 Trick-Play (Pause Live, Rewind)

| Req ID | Description | Priority | Phase | AI Enhancement | Acceptance Criteria |
|--------|-------------|----------|-------|---------------|-------------------|
| LTV-FR-030 | Pause live TV: pressing pause freezes the video and shows a pause overlay. Live content continues buffering. Pressing play resumes from the pause point (time-shifted). | P0 | 1 | -- | Pause activates in < 200ms. Maximum pause duration: 60 minutes (configurable per operator). Buffer is maintained server-side (CDN/origin). |
| LTV-FR-031 | Rewind within the live buffer: viewer can rewind up to the buffer start (default: 60 minutes behind live). Standard rewind speeds: 2x, 4x, 8x, 16x, 32x. | P0 | 1 | -- | Rewind initiates within 300ms of button press. Trick-play thumbnail strip displayed during rewind (generated from I-frames). Position indicator shows current position relative to live edge. |
| LTV-FR-032 | "Jump to Live" button visible whenever the viewer is behind the live edge (paused or rewound). One press returns to the live edge. | P0 | 1 | -- | Jump to live completes in < 1s. Button is prominently visible in the player controls whenever the viewer is > 5 seconds behind live. |
| LTV-FR-033 | Fast-forward when behind live: viewer can fast-forward (2x, 4x, 8x) to catch up to the live edge. Fast-forward disabled when at the live edge. | P0 | 1 | -- | Fast-forward speeds are selectable via repeated presses. Reaching the live edge automatically transitions back to live mode with a subtle "LIVE" indicator. |
| LTV-FR-034 | Time-shift position indicator: a scrubber bar showing the viewer's position relative to live, with the live edge marked and the buffer start marked | P0 | 1 | -- | Scrubber is accurate to within 2 seconds. Live edge marker pulses/animates to indicate live. Buffer start is clearly marked. |

### 4.5 Audio and Subtitle Selection

| Req ID | Description | Priority | Phase | AI Enhancement | Acceptance Criteria |
|--------|-------------|----------|-------|---------------|-------------------|
| LTV-FR-040 | Multi-audio track selection: viewer can switch between available audio tracks (original language, dubbed, audio description) during live playback | P0 | 1 | -- | Audio track switch completes in < 500ms without stream restart or visible interruption. Available tracks sourced from the manifest and presented with human-readable language labels. |
| LTV-FR-041 | Multi-subtitle track selection: viewer can enable/disable subtitles and switch between available subtitle languages during live playback | P0 | 1 | -- | Subtitle selection applies in < 300ms. Subtitle rendering follows platform accessibility guidelines (font size, color, background). Subtitle off/on toggle is a single press. |
| LTV-FR-042 | Accessibility: audio description tracks are labeled and easily discoverable. Closed captions (CEA-608/708 for North America, DVB subtitles for Europe) are supported where provided in the source feed. | P0 | 1 | -- | Audio description tracks appear with a distinct "AD" label. Closed caption rendering matches platform-standard styles. Users can customize caption appearance (size, color, background opacity) per platform accessibility settings. |
| LTV-FR-043 | Language preference persistence: the platform remembers the viewer's audio and subtitle preferences per profile and auto-selects them on subsequent channel tunes | P1 | 1 | AI learns language preferences per context (channel, genre, time-of-day) | Default preferences stored per profile. AI refinement in Phase 2: if a viewer always watches French audio with English subtitles on premium film channels but English audio on sports channels, the system adapts per channel genre. |

### 4.6 Playback Quality and Codec Management

| Req ID | Description | Priority | Phase | AI Enhancement | Acceptance Criteria |
|--------|-------------|----------|-------|---------------|-------------------|
| LTV-FR-050 | Adaptive bitrate streaming per the ABR ladder defined in ARCH-001 Section 5: HEVC primary, H.264 fallback, with per-device manifest filtering | P0 | 1 | -- | ABR switches between profiles without visible artifacts or audio glitches. Step-down latency: < 2 seconds from bandwidth detection to quality change. Step-up latency: < 5 seconds (conservative to avoid oscillation). |
| LTV-FR-051 | Codec negotiation: server-side manifest filtering ensures clients only receive profiles their device supports (HEVC, H.264, AV1 per device capability matrix in ARCH-001 Section 7) | P0 | 1 | -- | Zero playback failures due to unsupported codec delivery. Manifest filtering is performed by the BFF based on device capabilities reported during session creation. |
| LTV-FR-052 | DRM-gated quality tiers: 4K and HDR content restricted to Widevine L1 and FairPlay devices per the DRM matrix in ARCH-001 Section 5 | P0 | 1 | -- | Widevine L3 (software) devices capped at 720p. L1 (hardware) devices serve full resolution. DRM security level is validated during playback session creation. |
| LTV-FR-053 | ML-enhanced ABR (Phase 3): an ML model predicts bandwidth trajectory and content complexity (sports = prioritize framerate, drama = prioritize resolution) to make smarter ABR decisions | P2 | 3 | KServe-served ABR model (XGBoost or lightweight neural net) with < 10ms inference latency | Rebuffer events reduced by 25% compared to standard ABR in A/B test. Average delivered bitrate increased by 8%. Model falls back to standard ABR algorithm if inference unavailable. |

### 4.7 Channel Availability and Entitlements

| Req ID | Description | Priority | Phase | AI Enhancement | Acceptance Criteria |
|--------|-------------|----------|-------|---------------|-------------------|
| LTV-FR-060 | Channel access controlled by subscription package entitlements: each channel belongs to one or more packages, and only subscribers to those packages can view the channel | P0 | 1 | -- | Entitlement check completes in < 30ms (from Entitlement Service cache). Unauthorized channel access returns a clear "Upgrade to [package]" message with upgrade CTA. |
| LTV-FR-061 | Upsell for non-entitled channels: when a viewer attempts to access a channel outside their subscription, display channel preview (5-second teaser or blurred feed) and a clear upgrade prompt | P1 | 2 | AI selects the most persuasive upsell message per user based on engagement patterns | Preview is DRM-protected and time-limited (5 seconds). Upgrade prompt includes package name, price, and key content highlights. AI-selected messaging in Phase 3 (e.g., "This package includes 12 sports channels you watch regularly"). |
| LTV-FR-062 | Blackout enforcement: specific programs on specific channels may be blacked out in certain geographic regions (e.g., sports territorial rights). Blacked-out content displays an explanatory message. | P1 | 1 | -- | Blackout rules evaluated per program (SCTE-35 markers or EPG metadata). Blackout message includes reason and alternative viewing options (if available). Geo-location determined from IP with 95%+ accuracy. |

### 4.8 Error Handling and Resilience

| Req ID | Description | Priority | Phase | AI Enhancement | Acceptance Criteria |
|--------|-------------|----------|-------|---------------|-------------------|
| LTV-FR-070 | Graceful degradation on source feed loss: if a channel's ingest feed fails, display a branded "Temporarily Unavailable" slate rather than a black screen or error code | P0 | 1 | -- | Slate displays within 5 seconds of feed loss detection. Slate includes channel branding and "We're working on it" message. Auto-recovers within 5 seconds of feed restoration. |
| LTV-FR-071 | Codec fallback: if the primary HEVC feed is unavailable for a channel, automatically fall back to the H.264 feed without user intervention or visible error | P0 | 1 | -- | Fallback occurs within 3 seconds. No user-visible interruption (seamless fallback preferred, brief loading indicator acceptable). Metrics track fallback events for operational monitoring. |
| LTV-FR-072 | CDN failover: if the primary CDN for a live channel degrades (error rate > 1% or p95 latency > 500ms), the CDN Routing Service triggers a mid-session CDN switch | P0 | 1 | CDN Routing ML model (XGBoost) evaluates CDN performance per session in real-time | CDN switch completes in < 5 seconds. No rebuffer event during switch (pre-buffered from alternative CDN). Automatic -- no user intervention required. |
| LTV-FR-073 | Player error recovery: on encountering a playback error (manifest fetch failure, segment decode failure, DRM license error), the player retries with exponential backoff (1s, 2s, 4s, 8s) before showing an error message | P0 | 1 | -- | Automatic recovery succeeds for transient errors (network glitch, CDN hiccup) within 15 seconds. Persistent errors display a user-friendly message with "Try Again" button. Error codes are logged for debugging. |

---

## 5. AI-Specific Features

### 5.1 Smart Channel Surfing

**Description:** The AI predicts the viewer's next most likely channel based on their viewing history, the current time of day, day of week, content currently airing across channels, and the viewing patterns of similar users. Instead of sequential channel navigation (Channel 1 -> 2 -> 3), the "smart" channel order puts the most relevant channels first.

**Architecture:**
- The Recommendation Service scores all channels for the active user profile using a collaborative filtering model combined with temporal features (time-of-day, day-of-week). The model is trained on viewing session data: which channels were watched, for how long, at what times, and transition patterns (Channel A -> Channel B sequences).
- The model is a TensorFlow two-tower model (user tower + channel-context tower) served via KServe with < 30ms inference latency. It outputs a ranked list of channel IDs with confidence scores.
- The ranked list is cached in Redis (per user, per 30-minute time window) and served by the TV BFF as part of the channel list API response. Cache TTL: 30 minutes. Refresh triggered on profile switch, app foreground, or explicit channel list reload.
- Fallback: if the model is unavailable, the channel list falls back to numeric order with user favorites pinned at the top.

**Acceptance Criteria:**
- [ ] AI-ranked channel list increases time-on-channel by 15% vs numeric ordering (measured in A/B test over 30 days)
- [ ] Channel ranking latency: < 50ms additional latency on channel list API response (model inference + cache lookup)
- [ ] User can toggle between "Smart Order" and "Numeric Order" in settings
- [ ] Favorites always appear at the top of the list, regardless of AI ordering
- [ ] Model retrains every 6 hours on latest viewing data from Feature Store

### 5.2 Live Popularity Signals

**Description:** Real-time "trending now" signals indicate how many viewers are watching each channel and whether viewership is rising or falling. This creates a social proof mechanism that helps viewers discover popular live content they might otherwise miss.

**Architecture:**
- The Playback Session Service maintains an active session count per channel, aggregated every 30 seconds and published to Kafka (`playback.sessions` topic).
- A Flink streaming job consumes these events and computes: (a) current viewer count per channel, (b) viewer count trend (rising/stable/falling based on 5-minute rolling window), (c) spikes (viewer count increase > 50% in 5 minutes, indicating a notable live event).
- Aggregated popularity data is stored in Redis (key: `live:popularity:{channel_id}`, updated every 30 seconds) and served via the BFF as part of channel list and "Trending Live" rail APIs.
- A "Trending Live" rail on the home screen surfaces channels with the highest absolute viewership and the strongest upward trend, combining both signals.

**Acceptance Criteria:**
- [ ] Viewer counts displayed on the UI are accurate within +/- 5% of actual concurrent sessions
- [ ] Popularity data updates on the client every 30 seconds via polling or server-push
- [ ] "Trending Live" rail shows the top 10 channels by a weighted score of absolute viewers (60%) and trend velocity (40%)
- [ ] Spike detection triggers a real-time notification to opted-in users: "Breaking: [Event] -- 45K viewers watching now"
- [ ] Viewer count display is optional per operator configuration (some operators may not want to expose audience size)

### 5.3 Personalized Channel Order

**Description:** Beyond the Smart Channel Surfing model, the Personalized Channel Order feature dynamically reorders the entire channel lineup based on predicted relevance. The ordering adapts to time-of-day patterns: sports channels rise in the evening and on weekends, news channels rise in the morning and early evening, kids channels rise in the afternoon.

**Architecture:**
- Uses the same Recommendation Service model as Smart Channel Surfing but applied to the full channel list rendering, not just next-channel navigation.
- Time-of-day features: The Feature Store (Feast) maintains per-user temporal features computed from historical viewing data -- for each user, a matrix of channel affinity scores per 2-hour time window (0-2, 2-4, 4-6, ..., 22-24) per day-of-week (Mon-Sun). These features are updated hourly.
- The ranked channel list is materialized in Redis and served by the BFF. A background job refreshes the list every 30 minutes or on profile switch.

**Acceptance Criteria:**
- [ ] Channel order changes reflect time-of-day patterns (e.g., sports channels rank higher during prime sporting hours)
- [ ] A/B test shows > 20% increase in channel engagement (defined as time-on-channel after tune-in) vs static numeric ordering
- [ ] Users can pin channels to specific positions, overriding AI ordering
- [ ] Fallback to numeric order with favorites first when AI is unavailable
- [ ] No latency impact on channel list load (list is pre-computed and cached)

### 5.4 Intelligent Buffer Management

**Description:** An ML model predicts the optimal buffer depth for the live player based on content type, network conditions, and historical playback quality for the user's device/ISP combination. Sports content receives a shorter buffer (to minimize latency) while documentary content receives a deeper buffer (to maximize quality stability).

**Architecture:**
- A lightweight classification model (XGBoost) runs on the CDN Routing Service to determine buffer parameters per playback session at session start time.
- Inputs: content type (sports/news/entertainment/kids -- from EPG metadata), network type (WiFi/cellular/ethernet -- from client), ISP identifier, device type, historical QoE metrics for this device/ISP (from Feature Store).
- Outputs: recommended initial buffer (seconds), recommended max buffer (seconds), latency target (standard or low-latency).
- The buffer parameters are returned as part of the playback session creation response and consumed by the client player.

**Acceptance Criteria:**
- [ ] Sports content buffer: 1-2 seconds (LL-HLS), minimizing latency
- [ ] Standard content buffer: 3-6 seconds, optimizing for quality stability
- [ ] Rebuffer rate reduced by 15% vs fixed buffer configuration (A/B test)
- [ ] Buffer parameters determined in < 10ms (within playback session creation latency budget)
- [ ] Fallback to default buffer values (3 seconds) if model is unavailable

### 5.5 AI Quality Monitoring

**Description:** ML-based anomaly detection monitors the quality of every live channel in real-time, detecting degradation (audio sync issues, video artifacts, bitrate drops, feed loss, encoder failures) before viewers file complaints. The system alerts operations within 60 seconds of anomaly onset and can trigger automated remediation.

**Architecture:**
- The QoE Service (ClickHouse + Flink) aggregates per-channel quality metrics from two sources:
  - Client-side: Conviva SDK reports (video start time, rebuffer ratio, bitrate, resolution drops, errors) aggregated per channel per 30-second window
  - Server-side: Encoder health metrics, ingest feed status, CDN segment delivery success rate
- An anomaly detection model (PyTorch autoencoder trained on normal quality patterns per channel per time-of-day) evaluates the aggregated metrics every 30 seconds.
- Anomalies are classified by severity: Warning (potential degradation, investigate), Critical (confirmed user impact, immediate action), Emergency (feed loss, auto-remediate).
- Critical and Emergency alerts are sent to PagerDuty and displayed on the Operations dashboard. Automated remediation (encoder restart, CDN switch, feed failover) triggers for known patterns.

**Acceptance Criteria:**
- [ ] Anomaly detection latency: < 60 seconds from degradation onset to alert generation
- [ ] False positive rate: < 5% of generated alerts are false positives
- [ ] Detection coverage: audio sync, video artifact, bitrate anomaly, feed loss, encoder failure, CDN degradation
- [ ] Automated remediation for feed failover (switch to backup ingest) triggers within 30 seconds of Emergency classification
- [ ] Anomaly model retrains weekly on latest quality data

---

## 6. Non-Functional Requirements

### 6.1 Latency

| Requirement | Target | Measurement | Priority |
|-------------|--------|-------------|----------|
| Channel change time (user input to first frame) | < 1.5s (p95), < 1.0s (p50) | Client-side telemetry (Conviva) | P0 |
| Live delay -- standard channels | < 5 seconds glass-to-glass | Measured against broadcast reference signal | P0 |
| Live delay -- LL-HLS channels (sports/events) | < 3 seconds glass-to-glass | Measured against broadcast reference signal | P0 (Phase 3 for LL-HLS) |
| Audio/subtitle track switch | < 500ms | Client-side telemetry | P0 |
| Mini EPG overlay render | < 300ms from trigger | Client-side telemetry | P1 |
| Channel list load | < 500ms | BFF API response time + client render | P0 |
| Trick-play response (pause, FF, RW) | < 300ms from button press | Client-side telemetry | P0 |

### 6.2 Availability

| Requirement | Target | Measurement |
|-------------|--------|-------------|
| Per-channel availability | 99.95% (measured per calendar month) | Synthetic monitoring + real user monitoring |
| Platform-wide live TV service availability | 99.99% | At least one channel playable at all times |
| Ingest feed redundancy | Every channel has a minimum of 2 independent ingest paths | Infrastructure audit |
| Failover time (primary to backup ingest) | < 10 seconds | Synthetic failover test |

### 6.3 Scale

| Requirement | Phase 1 Target | Phase 4 Target | Measurement |
|-------------|---------------|----------------|-------------|
| Simultaneous live channels | 200+ | 300+ | Channel count in EPG |
| Concurrent live viewers (platform-wide) | 50,000 | 500,000 | Active playback sessions |
| Peak concurrent viewers per channel | 25,000 | 200,000 | Per-channel session counter |
| Channel changes per second (platform-wide) | 5,000 | 50,000 | Playback Session Service RPS |
| CDN bandwidth (peak) | 50 Gbps | 500 Gbps | CDN analytics |

### 6.4 Quality

| Requirement | Target | Measurement |
|-------------|--------|-------------|
| VMAF score (1080p HEVC) | > 93 | VMAF analysis on encoded output |
| VMAF score (1080p H.264) | > 90 | VMAF analysis on encoded output |
| Rebuffer ratio (live TV sessions) | < 0.3% | Client-side telemetry (Conviva) |
| Video start failures | < 0.5% of play attempts | Playback Session Service error rate |
| Audio-video sync | Within +/- 40ms | Automated A/V sync measurement |

---

## 7. Technical Considerations

### 7.1 Ingest Architecture

Live channels are ingested through redundant paths to ensure continuous availability:

- **Primary ingest**: Satellite/fiber feed received at the platform's ingest PoP (co-located with the encoder farm). SDI or SMPTE ST 2110 input.
- **Backup ingest**: Secondary feed from an independent satellite transponder, fiber path, or IP ingest (RIST/SRT protocol).
- **Automatic failover**: Ingest monitoring detects primary feed loss (audio silence, video freeze, SCTE-35 signal loss) and switches to backup within 10 seconds.
- **Ingest PoP**: Minimum 2 geographically separated ingest PoPs for disaster recovery (Phase 2+).

### 7.2 Encoding and Packaging

- **Live transcoding**: AWS Elemental MediaLive (managed) or Harmonic VOS (self-hosted) with N+1 redundancy. Each channel has a primary and standby encoder pipeline.
- **Encoding profiles**: Per the ABR ladder in ARCH-001 Section 5 -- standard live (2s segments, 2s GOP) and LL-HLS (0.5s partial segments with independent decode points).
- **CMAF packaging**: Unified Streaming Platform (USP) produces CMAF segments that serve both HLS (.m3u8) and DASH (.mpd) manifests.
- **DRM**: CBCS encryption with JIT manifest generation per DRM system. CPIX key exchange with daily key rotation per channel.

### 7.3 CDN Delivery

- **Multi-CDN**: Akamai (primary), CloudFront (secondary), Fastly (regional supplement). CDN selection per session by CDN Routing Service.
- **Origin shield**: Regional caching layer between origin and CDN edge to reduce origin load. Shield in EU-West, US-East, and APAC.
- **CAT tokens**: Short-lived (5 minutes), ECDSA-signed tokens per session. Validated at CDN edge with no origin callback.
- **Segment naming**: `/{content-type}/{channel-id}/{profile}/{segment-number}.m4s`
- **Cache TTL**: Live segments: 2 seconds (equal to segment duration). Manifests: 1 second (to ensure freshness).

### 7.4 Player Integration

Each client platform uses its native player for optimal codec support and DRM integration:

| Platform | Player | DRM | Max Resolution | LL-HLS Support |
|----------|--------|-----|----------------|----------------|
| Android TV | ExoPlayer/Media3 3.3+ | Widevine L1 | 4K HDR | Yes (via ExoPlayer LL-HLS) |
| Apple TV | AVPlayer | FairPlay | 4K HDR (Dolby Vision) | Yes (native LL-HLS) |
| Web (Chrome) | Shaka Player 4.x | Widevine L1/L3 | 4K (L1) / 720p (L3) | Yes (via Shaka LL-HLS) |
| Web (Safari) | Shaka Player 4.x | FairPlay | 4K | Yes (native LL-HLS) |
| iOS | AVPlayer | FairPlay | 1080p (phone) / 4K (iPad) | Yes (native) |
| Android Mobile | ExoPlayer/Media3 3.3+ | Widevine L1/L3 | 1080p (L1) / 540p (L3) | Yes |

### 7.5 Session Management

- Each live playback creates a session via the Playback Session Service (Go, p99 < 200ms).
- The session encapsulates: user ID, profile ID, channel ID, device ID, CDN assignment, DRM token, CAT token, quality parameters (buffer depth, ABR constraints), and entitlement verification result.
- Heartbeats are sent every 30 seconds from the client to maintain the session. Sessions without heartbeats for 2 minutes are terminated.
- Concurrent stream limits are enforced per subscription tier (e.g., 2 concurrent for basic, 4 for premium). Live TV sessions count toward the concurrent limit.

---

## 8. Dependencies

### 8.1 Service Dependencies

| Dependency | Service | PRD Reference | Dependency Type | Impact if Unavailable |
|------------|---------|---------------|-----------------|----------------------|
| Program metadata for channels | EPG Service | PRD-005 | Hard | Mini EPG shows "No information available." Channel list shows channel name only. |
| Start Over capability | TSTV Service | PRD-002 | Soft | "Start Over" button hidden in mini EPG and player controls. Live-only viewing. |
| Record from live | Recording Service | PRD-003 | Soft | "Record" button hidden in mini EPG and player controls. Viewing unaffected. |
| Channel entitlements | Entitlement Service | ARCH-001 | Hard | Cannot verify channel access. Fail-closed: deny access with "Service temporarily unavailable" message. |
| Session management | Playback Session Service | ARCH-001 | Hard | Cannot create playback sessions. Live TV is fully unavailable. |
| CDN token issuance | Token Service (CAT) | ARCH-001 | Hard | Cannot authorize CDN access. Live TV is fully unavailable. |
| CDN routing | CDN Routing Service | ARCH-001 | Soft | Falls back to round-robin CDN selection with geo-affinity. Suboptimal but functional. |
| AI channel ranking | Recommendation Service | PRD-007 | Soft | Channel list falls back to numeric order with favorites first. |
| Popularity signals | Flink / Playback Session Service | ARCH-001 | Soft | "Trending Live" rail hidden. Viewer counts not displayed. |
| User profile | Profile Service | ARCH-001 | Hard | Cannot load user preferences (audio, subtitle, favorites). Falls back to defaults. |

### 8.2 Infrastructure Dependencies

| Dependency | Component | Impact if Unavailable |
|------------|-----------|----------------------|
| Ingest feeds | Satellite/fiber/IP | Channel slate displayed. Automatic failover to backup ingest. |
| Encoder farm | MediaLive / Harmonic | Channel unavailable. Failover to standby encoder within 10s. |
| Packaging | USP / MediaPackage | No manifests generated. Channel unavailable. |
| CDN | Akamai / CloudFront / Fastly | CDN failover to alternative provider. If all CDNs fail: total outage. |
| Kafka | Event bus | Session events not published. AI features degrade (stale popularity, stale recommendations). Core playback unaffected. |
| Redis | Cache layer | Increased latency on entitlement checks, channel list, session lookups. Falls back to database reads. |
| PostgreSQL | Persistent storage | Entitlement checks fail (if Redis cache also missed). Critical impact. |

---

## 9. Success Metrics

| # | Metric | Baseline (Industry) | Phase 1 Target | Phase 2 Target | Phase 4 Target | Measurement Method |
|---|--------|--------------------|--------------|--------------|--------------|--------------------|
| 1 | Channel change time (p95) | 2.5-4.0 seconds | < 1.5 seconds | < 1.2 seconds | < 1.0 seconds | Client-side telemetry (Conviva SDK) |
| 2 | Live delay (standard) | 8-15 seconds | < 5 seconds | < 5 seconds | < 4 seconds | Broadcast reference comparison |
| 3 | Live delay (LL-HLS) | 5-8 seconds | -- | < 3 seconds | < 2.5 seconds | Broadcast reference comparison |
| 4 | Per-channel availability | 99.5-99.9% | 99.95% | 99.95% | 99.99% | Synthetic monitoring + RUM |
| 5 | Rebuffer ratio (live sessions) | 0.5-1.5% | < 0.3% | < 0.2% | < 0.1% | Client-side telemetry (Conviva) |
| 6 | Video start failures | 1-3% | < 0.5% | < 0.3% | < 0.1% | Playback Session Service metrics |
| 7 | AI channel order engagement lift | N/A | +15% time-on-channel | +20% | +25% | A/B test: AI order vs numeric order |
| 8 | "Trending Live" rail CTR | N/A | 10% | 15% | 20% | Click-through rate on trending rail items |
| 9 | Start Over adoption (from live) | 10-15% of late tune-ins | 30% | 40% | 50% | % of late tune-in sessions offering Start Over where user accepts |
| 10 | QoE score (p50) for live sessions | 70-75 | 82 | 86 | 90 | QoE Service composite score (ARCH-001 Section 9) |

---

## 10. Open Questions & Risks

### Open Questions

| # | Question | Owner | Impact | Target Resolution |
|---|----------|-------|--------|-------------------|
| 1 | What is the maximum number of LL-HLS channels to support simultaneously in Phase 3? Cost increases with each LL-HLS channel due to faster segment generation and higher CDN request rates. | Platform Architect | Infrastructure cost, CDN capacity | Phase 2 planning |
| 2 | Should channel-up/down in AI-ordered mode follow the AI ranking or maintain a consistent order during a session? Changing order mid-session could disorient users. | Product Manager | UX consistency | Phase 1 design review |
| 3 | How should popularity signals handle privacy? Displaying viewer counts could reveal viewership for niche/sensitive content. Should there be a minimum threshold before displaying counts? | Privacy/Legal | Legal compliance | Phase 1 legal review |
| 4 | What is the expected ratio of standard vs LL-HLS channels at Phase 4? This affects encoder and CDN capacity planning significantly. | Business / Content | Capacity planning | Phase 2 planning |
| 5 | Should the pause-live buffer (60 minutes) be per-channel or shared across channels? Per-channel is more user-friendly but requires significantly more origin/CDN buffer storage. | Platform Architect | Origin storage cost | Phase 1 architecture review |
| 6 | What is the regulatory position on EAS integration for OTT platforms in the target market? Broadcast EAS requirements may not fully apply to OTT delivery. | Legal/Regulatory | Compliance requirements | Phase 1 legal review |
| 7 | Should PiP be supported on all platforms from Phase 1 or phased per platform? PiP implementation varies significantly across Android TV, Apple TV, and Web. | Client Engineering | Development scope | Phase 1 sprint planning |

### Risks

| # | Risk | Severity | Likelihood | Mitigation |
|---|------|----------|------------|------------|
| 1 | **Channel change time exceeds 1.5s target** due to DRM license acquisition latency, manifest fetch latency, or CDN first-byte time | High | Medium | Pre-fetch DRM licenses for channels adjacent to the current channel. Pre-load manifests for the top-5 AI-predicted next channels. Optimize CDN edge cache for live manifest freshness. Implement channel preview (low-res thumbnail) during tune. |
| 2 | **LL-HLS latency exceeds 3s target** due to CDN propagation delay, encoder packaging latency, or client-side buffer configuration | High | Medium | Require CDN partners to support chunked transfer encoding for live. Optimize USP partial segment publishing. Tune client buffer to 1-2 seconds for LL-HLS mode. Conduct end-to-end latency testing per CDN provider before launch. |
| 3 | **Multi-CDN live delivery inconsistency**: different CDNs have different segment availability times, causing mid-session CDN switches to fail or cause rebuffering | Medium | High | Implement segment availability verification before triggering CDN switch. Use origin shield to normalize segment availability across CDNs. Test CDN switch scenarios extensively in staging. |
| 4 | **AI channel ordering confuses users**: users expect channels in numeric order and are disoriented when channels are reordered | Medium | Medium | Default to numeric order, offer AI ordering as an opt-in feature. Clearly label the mode ("Sorted by: Relevance" vs "Sorted by: Channel number"). Run A/B test before full rollout. Provide an easy toggle in the channel list header. |
| 5 | **Ingest feed quality variability**: source feeds from content providers have inconsistent quality (bitrate, resolution, audio levels) requiring per-channel tuning of the encoding pipeline | Medium | High | Implement automated ingest quality monitoring. Normalize audio levels (loudness normalization per EBU R128). Auto-detect and report source quality issues. Maintain a quality scorecard per content provider. |
| 6 | **Scale spike during major live events** (e.g., World Cup final) causes CDN capacity exhaustion and platform degradation | High | Medium | Pre-scale infrastructure 24 hours before known major events. Work with CDN partners on reserved capacity for tentpole events. Implement graceful degradation (reduce quality tiers during peak load). Load test at 2x expected peak. |
| 7 | **Encoder pipeline single point of failure** for a specific channel causes extended outage | High | Low | N+1 redundancy for all encoder instances. Automatic failover within 10 seconds. Geographically separated backup encoding for critical channels (sports, news). Regular failover testing. |

---

*This PRD defines the Live TV & Linear Channels service for the AI-native OTT streaming platform. It should be read in conjunction with ARCH-001 (Platform Architecture) for technical details, PRD-002 (TSTV) for Start Over and Catch-Up integration, PRD-003 (Cloud PVR) for recording from live, PRD-005 (EPG) for program metadata, and PRD-007 (AI User Experience) for cross-service AI capabilities.*
