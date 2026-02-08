# PRD-005: TV Guide / Electronic Program Guide (EPG)

**Document ID:** PRD-005
**Version:** 1.0
**Date:** 2026-02-08
**Status:** Draft
**Author:** PRD Writer B Agent
**References:** VIS-001 (Project Vision & Design), ARCH-001 (Platform Architecture)
**Audience:** Product Management, Engineering, AI/ML, UX Design

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

The Electronic Program Guide (EPG) is the central discovery and planning hub for all linear TV content on the platform. It provides a comprehensive 7-day forward and 7-day backward schedule of programming across 200+ live channels, integrated with Live TV, TSTV (Start Over and Catch-Up), Cloud PVR, and VOD services.

Unlike traditional EPGs that present an undifferentiated grid of channels sorted by number, this EPG is designed as an **AI-driven discovery and viewing planning tool**. It transforms the passive channel-by-time grid into an intelligent surface that understands each viewer's preferences, context, and household composition to deliver a uniquely personalized experience.

### Business Context

The EPG remains one of the most frequently accessed surfaces in any TV platform. Industry data shows that 68% of live TV viewing sessions begin with an EPG interaction, and viewers spend an average of 3.2 minutes in the EPG per session. Despite this, the EPG has seen minimal innovation since the 1990s -- every user sees the same grid, sorted by channel number, with no awareness of individual preferences.

This represents a significant opportunity. A personalized EPG that surfaces relevant content proactively can reduce the time-to-play for live and catch-up content, increase viewer engagement with the broader linear catalog, and serve as the primary integration point between live, time-shifted, recorded, and on-demand content.

### Scope

**In Scope:**
- Traditional EPG grid view (channels x time) with full navigation
- AI-personalized "Your Schedule" view with cross-source recommendations
- Per-user personalized channel ordering
- Per-program relevance scoring
- "Family Schedule" co-viewing optimized view
- AI-triggered smart reminders and notifications
- Program enrichment (AI-generated summaries, related content, social signals)
- Quick actions from EPG (Watch Live, Start Over, Record, Set Reminder)
- EPG data ingest pipeline and schedule management
- Search within EPG

**Out of Scope:**
- FAST (Free Ad-Supported TV) channel management (separate future PRD)
- Detailed SSAI/ad insertion within EPG-linked playback (covered in monetization)
- EPG data licensing negotiations (business operations)
- Companion app / second screen EPG (covered in PRD-006 Multi-Client)

---

## 2. Goals & Non-Goals

### Goals

1. **Deliver a best-in-class traditional EPG** that supports 200+ channels with a 14-day window (7 forward, 7 backward), fast navigation, and comprehensive program metadata
2. **Personalize the EPG per viewer** through AI-ranked channel ordering, per-program relevance scoring, and a curated "Your Schedule" timeline
3. **Unify content discovery** across live, catch-up, recordings, and VOD within a single EPG surface, eliminating the need to navigate between separate app sections
4. **Support household viewing** with a "Family Schedule" mode that detects co-viewing sessions and recommends content suitable for the entire group
5. **Drive engagement** by reducing mean time-to-play from EPG interactions by 40% compared to a traditional grid
6. **Enable proactive discovery** through AI-triggered smart reminders that notify viewers of programs matching their interests, with frequency capping to prevent fatigue
7. **Integrate seamlessly** with Live TV (PRD-001), TSTV (PRD-002), Cloud PVR (PRD-003), and VOD (PRD-004) for one-click actions from any program entry

### Non-Goals

- Building a standalone "discover" or "explore" tab -- the EPG complements but does not replace the VOD home screen (PRD-004)
- Real-time social features (live chat, reactions) during programs
- User-generated schedule sharing (e.g., "share my schedule with a friend")
- Interactive overlays during live viewing (stats, polls) -- covered by client-specific features in PRD-006
- EPG for radio channels (audio-only)

---

## 3. User Scenarios

### Scenario 1: Evening Channel Browse

**Persona:** Thomas (The Casual Viewer)
**Context:** 7:30 PM, living room Samsung Smart TV, after dinner

Thomas opens the EPG to see what is on now. The grid loads with channels ordered by his AI-personalized ranking -- documentary and news channels appear at the top, not buried at position 150+. He scrolls down to see a nature documentary starting at 8 PM, highlighted with a "Recommended for you" badge and a relevance score indicator. He selects the program, reads the AI-generated synopsis, and sets a reminder. At 7:58 PM, a notification appears: "Wild Africa starts in 2 minutes on Discovery." He taps the notification and is taken directly to the live stream.

### Scenario 2: Personalized "Your Schedule" Morning Commute Planning

**Persona:** Maria (The Busy Professional)
**Context:** 7:15 AM, iPhone, preparing for work

Maria opens the EPG "Your Schedule" view on her phone. Instead of a grid of channels, she sees a personalized timeline for the day:
- **8:00 AM:** "Morning News Roundup" (Live, Channel 1) -- "Your daily watch"
- **9:30 PM:** "The Bear, S3E04" (Catch-Up, available since yesterday) -- "You're 3 episodes in"
- **10:00 PM:** "Severance, S2E08" (VOD, new episode) -- "New this week"

The timeline mixes live, catch-up, and VOD content into a single unified schedule tailored to her. She taps the catch-up entry to bookmark it for tonight.

### Scenario 3: Sports Fan Checking Today's Schedule

**Persona:** Erik (The Sports Fan)
**Context:** Saturday 10 AM, Android TV, checking the day's schedule

Erik opens "Your Schedule" and sees a sports-heavy day laid out:
- **1:00 PM:** Premier League -- Arsenal vs Chelsea (Live, Sky Sports)
- **3:00 PM:** F1 Qualifying -- Monaco GP (Live, Sport1)
- **5:30 PM:** Tennis -- Roland Garros SF (Live, Eurosport)
- **9:00 PM:** Match of the Day (Catch-Up, BBC) -- "You usually watch this"

Each entry shows a "Record" button for one-tap recording. Erik records the F1 qualifying (he'll be watching the football) and sets a reminder for the tennis. The EPG flags that Arsenal vs Chelsea is available on LL-HLS for ultra-low latency viewing.

### Scenario 4: Family Friday Night Co-Viewing

**Persona:** The Okafor Family
**Context:** Friday 7:00 PM, living room Android TV, whole family present

David opens the EPG. The platform detects that multiple household profiles are likely present (Friday evening pattern, co-viewing history). The EPG switches to "Family Schedule" mode, showing a curated selection:
- **7:30 PM:** "Planet Earth III" (Live, BBC) -- "Great for the whole family" (relevance: 92)
- **8:00 PM:** "Lego Masters" (Catch-Up, yesterday) -- "The kids loved Season 2"
- **8:30 PM:** "Paddington 2" (VOD) -- "Family movie night suggestion"

Content rated above PG-13 is filtered out. David can switch back to his personal view by tapping his profile icon.

### Scenario 5: Quick Action -- Record from EPG

**Persona:** Erik (The Sports Fan)
**Context:** Browsing EPG 3 days forward, Wednesday evening

Erik scrolls the EPG grid to Wednesday and finds a Champions League match at 8 PM that conflicts with a dinner commitment. Without leaving the EPG, he:
1. Selects the program entry
2. Taps "Record" on the program detail overlay
3. Sees confirmation: "Recording scheduled. You'll be notified when it's ready."
4. Optionally taps "Record all matches" for series-link recording of the tournament

The recording request is sent to the Cloud PVR service (PRD-003). The EPG entry now shows a red recording indicator.

### Scenario 6: Late Tune-In with Start Over Suggestion

**Persona:** Maria (The Busy Professional)
**Context:** Tuesday 9:20 PM, Apple TV, just got home

Maria opens the EPG and sees that a drama she follows started at 9:00 PM and is 20 minutes in. The EPG program entry shows: "Started 20 min ago -- Start from beginning?" She taps the suggestion and is taken into Start Over mode (TSTV, PRD-002), beginning the program from the opening scene. The EPG mini-overlay shows her current position relative to the live broadcast.

### Scenario 7: Discovering Catch-Up Content Through EPG

**Persona:** Priya (The Binge Watcher)
**Context:** Sunday afternoon, LG webOS TV, browsing what she missed this week

Priya navigates the EPG backward to Thursday evening. She sees a documentary highlighted with a "Trending in Catch-Up" badge -- 45,000 viewers watched it via catch-up this week. The program entry shows an AI-generated summary: "A visually stunning exploration of deep-sea ecosystems, with a meditative soundtrack and unexpected narrative twists." She taps "Watch Now" and begins catch-up playback directly from the EPG.

### Scenario 8: Smart Notification from EPG Intelligence

**Persona:** Erik (The Sports Fan)
**Context:** Push notification received at 2:45 PM on a Saturday

Erik receives a notification: "F1 Qualifying starts in 15 minutes on Sport1. Tap to watch." He is not currently using the app. The notification was triggered because:
- The EPG AI knows Erik watches F1 regularly (viewing history signal)
- It's a qualifying session (high relevance for F1 fans)
- Erik hasn't already set a reminder or recording for this event
- The notification frequency cap allows it (max 3 EPG notifications per day)

Erik taps the notification and is taken directly to the live stream.

### Scenario 9: Searching Within the EPG

**Persona:** Priya (The Binge Watcher)
**Context:** Looking for a specific show in the EPG schedule

Priya uses the EPG search to type "nature documentary this week." The search returns EPG schedule entries matching her query across all channels and the 7-day window, ranked by relevance. Results include both upcoming programs and catch-up available programs. Each result shows the channel, date/time, availability (live, catch-up, recording), and the AI relevance score.

### Scenario 10: Exploring Related Content from Program Detail

**Persona:** Maria (The Busy Professional)
**Context:** Viewing a program detail overlay in the EPG

Maria selects a true crime documentary in the EPG. The program detail overlay shows:
- Synopsis, cast, runtime, age rating
- "Related programs this week": 3 similar documentaries airing on other channels
- "Available on demand": 2 related VOD titles
- "Viewers also recorded": 3 programs commonly recorded by viewers who recorded this one
- Quick actions: Watch Live, Start Over, Record, Add to Watchlist, Set Reminder

---

## 4. Functional Requirements

### EPG Data Management

| ID | Requirement | Priority | Phase | AI Enhancement | Acceptance Criteria |
|----|-------------|----------|-------|----------------|---------------------|
| EPG-FR-001 | EPG shall display a 7-day forward schedule for all available channels | P0 | 1 | No | Given a user opens the EPG, when they navigate forward in time, then schedule data is available for up to 7 days ahead with < 2s load time per day |
| EPG-FR-002 | EPG shall display a 7-day backward schedule for catch-up eligible channels | P0 | 1 | No | Given a channel supports catch-up, when the user navigates backward, then program entries for the past 7 days are visible with catch-up availability indicators |
| EPG-FR-003 | EPG data shall be refreshed within 5 minutes of any schedule change at the source | P0 | 1 | No | Given a schedule change occurs at the EPG data provider, when 5 minutes have elapsed, then the updated data is reflected in the EPG across all clients |
| EPG-FR-004 | EPG shall support schedule data for 200+ channels simultaneously | P0 | 1 | No | Given the full channel lineup is loaded, when 200+ channels have active schedule data, then the EPG renders without performance degradation |
| EPG-FR-005 | EPG shall handle schedule changes gracefully (program overruns, breaking news, schedule shifts) | P1 | 1 | No | Given a live program overruns its scheduled end time, when the schedule is updated, then the EPG reflects the change within 5 minutes and downstream recordings/reminders are adjusted |

### Grid View Navigation

| ID | Requirement | Priority | Phase | AI Enhancement | Acceptance Criteria |
|----|-------------|----------|-------|----------------|---------------------|
| EPG-FR-010 | EPG shall provide a grid view with channels on the vertical axis and time on the horizontal axis | P0 | 1 | No | Given a user opens the EPG grid, then channels are displayed vertically and time slots horizontally, with the current time centered and a "now" indicator visible |
| EPG-FR-011 | Users shall be able to scroll horizontally through time (past 7 days to future 7 days) | P0 | 1 | No | Given a user is in the EPG grid, when they scroll horizontally, then time navigation is smooth at 60fps with no visible loading delays between adjacent time blocks |
| EPG-FR-012 | Users shall be able to scroll vertically through channels | P0 | 1 | No | Given a user is in the EPG grid, when they scroll vertically, then channel navigation is smooth and responsive across the full 200+ channel list |
| EPG-FR-013 | Users shall be able to jump to "Now" (current time) from any position in the EPG | P0 | 1 | No | Given a user has navigated to a different time or date, when they press the "Now" button, then the EPG scrolls to the current time within 300ms |
| EPG-FR-014 | Users shall be able to jump to a specific date within the 14-day window | P1 | 1 | No | Given a user opens the date picker, when they select a date, then the EPG navigates to that date's schedule within 500ms |
| EPG-FR-015 | EPG shall display a mini-guide overlay during live TV viewing showing current and next program on the active channel | P0 | 1 | No | Given a user is watching live TV, when they press the info/guide button, then a mini EPG overlay shows the current program (with progress bar) and next 2 programs within 200ms |

### Channel Filtering and Favorites

| ID | Requirement | Priority | Phase | AI Enhancement | Acceptance Criteria |
|----|-------------|----------|-------|----------------|---------------------|
| EPG-FR-020 | Users shall be able to filter channels by category (All, Favorites, HD/UHD, Genre, Package) | P0 | 1 | No | Given a user selects a channel filter, when the filter is applied, then only matching channels are displayed and the filter state persists within the session |
| EPG-FR-021 | Users shall be able to mark channels as favorites and view a favorites-only EPG | P0 | 1 | No | Given a user adds a channel to favorites, when they select the "Favorites" filter, then only favorite channels are displayed in the grid |
| EPG-FR-022 | Favorite channels shall be synced across all devices for the same profile | P0 | 1 | No | Given a user sets favorites on one device, when they open the EPG on another device under the same profile, then the same favorites are displayed within 5 seconds of the change |
| EPG-FR-023 | Channel list shall respect entitlement -- channels not in the user's subscription package shall be visually distinguished and not playable | P0 | 1 | No | Given a channel is outside the user's package, when it appears in the EPG, then it is visually dimmed with an "Upgrade" badge, and selecting it shows an upgrade prompt |

### Program Details and Quick Actions

| ID | Requirement | Priority | Phase | AI Enhancement | Acceptance Criteria |
|----|-------------|----------|-------|----------------|---------------------|
| EPG-FR-030 | Selecting a program in the EPG shall display a detail overlay with: title, synopsis, duration, genre, age rating, cast, episode info (if series), and availability indicators | P0 | 1 | No | Given a user selects a program entry, when the detail overlay appears, then all metadata fields are populated within 300ms |
| EPG-FR-031 | Program detail shall show available actions: Watch Live (if airing now), Start Over (if eligible), Record (if eligible), Set Reminder (if future), Watch Catch-Up (if available) | P0 | 1 | No | Given a program detail is displayed, when the program is currently airing and eligible, then "Watch Live" and "Start Over" actions are both available |
| EPG-FR-032 | "Record" action shall create a Cloud PVR recording request and show confirmation within the EPG | P0 | 2 | No | Given a user taps "Record" on a future program, when the recording is scheduled successfully, then a red recording indicator appears on the EPG entry within 1 second |
| EPG-FR-033 | "Set Reminder" action shall schedule a notification for a configurable time before the program starts (5, 10, 15, 30 minutes) | P1 | 1 | No | Given a user sets a reminder for 15 minutes before a program, when the time arrives, then a notification is delivered across all registered devices within 30 seconds of the target time |
| EPG-FR-034 | Programs with active recordings shall display a recording indicator in the EPG grid | P0 | 2 | No | Given a program has a scheduled or in-progress recording, when it appears in the EPG grid, then a recording icon is visible on the program cell |
| EPG-FR-035 | Program detail shall show series information (season, episode number, series link status) for episodic content | P1 | 1 | No | Given an episodic program is selected, then the detail overlay shows season number, episode number, episode title, and next episode information |

### Search Within EPG

| ID | Requirement | Priority | Phase | AI Enhancement | Acceptance Criteria |
|----|-------------|----------|-------|----------------|---------------------|
| EPG-FR-040 | Users shall be able to search within the EPG schedule by program title, genre, or keyword | P0 | 1 | No | Given a user enters a search query in the EPG, when results are returned, then matching programs across all channels and the 14-day window are displayed within 500ms |
| EPG-FR-041 | EPG search results shall indicate program availability (live now, upcoming, catch-up available, recordable) | P1 | 1 | No | Given search results are displayed, then each result shows an availability badge (Live Now, Upcoming, Catch-Up, Recordable) |
| EPG-FR-042 | EPG search shall support AI-powered semantic search for natural language queries | P1 | 3 | Yes -- Conversational search via Bedrock LLM | Given a user searches "funny cooking shows this week," when results are returned, then semantically relevant programs are ranked above keyword-only matches |

### Accessibility

| ID | Requirement | Priority | Phase | AI Enhancement | Acceptance Criteria |
|----|-------------|----------|-------|----------------|---------------------|
| EPG-FR-050 | EPG shall be fully navigable via screen reader on all platforms | P0 | 1 | No | Given a screen reader is active, when navigating the EPG grid, then every program entry announces: channel name, program title, start time, duration, and genre |
| EPG-FR-051 | EPG shall support high-contrast mode for visually impaired users | P1 | 1 | No | Given high-contrast mode is enabled, when the EPG is displayed, then all text and UI elements meet WCAG 2.1 AA contrast ratios (minimum 4.5:1) |
| EPG-FR-052 | EPG time navigation shall provide audio cues for time boundary crossings (e.g., new day) | P2 | 2 | No | Given a screen reader user scrolls past midnight in the EPG, then an audio cue announces the new date |

---

## 5. AI-Specific Features

### 5.1 Personalized Channel Order

**Description:** The AI engine reorders the channel list per user profile based on viewing history, time-of-day patterns, and content preferences. A sports fan sees sports channels at the top during match evenings; a documentary viewer sees documentary channels first after dinner.

**Algorithm Inputs:**
- Per-profile viewing history (channels watched, duration, frequency, time-of-day patterns)
- Current time and day of week (weekday evening vs weekend morning have different patterns)
- Active content on channels (e.g., a big live event boosts the hosting channel)
- Channel genre affinity per profile (derived from viewing patterns)
- Trending signals (channels with above-average viewership right now)

**Behavior:**
- Channel order is computed per profile per session and refreshed every 30 minutes
- Users can pin favorite channels to specific positions; pinned channels override AI ordering
- The AI-ordered list is used as the default; users can switch to "Traditional" (number-sorted) order
- New users with no viewing history see a popularity-weighted channel order

**Requirements:**

| ID | Requirement | Priority | Phase | Acceptance Criteria |
|----|-------------|----------|-------|---------------------|
| EPG-AI-001 | EPG shall display channels in AI-personalized order by default per user profile | P0 | 1 | Given a profile with 30+ days of viewing history, when the EPG opens, then channels watched most frequently at the current time-of-day appear in the top 10 positions with > 80% accuracy |
| EPG-AI-002 | Users shall be able to toggle between AI-personalized and traditional (number-sorted) channel order | P1 | 1 | Given a user switches to traditional order, then channels sort by number immediately; the preference persists until changed |
| EPG-AI-003 | Pinned favorite channels shall override AI ordering and remain in user-specified positions | P0 | 1 | Given a user pins Channel X to position 3, when the EPG refreshes, then Channel X remains at position 3 regardless of AI scoring |
| EPG-AI-004 | Channel order shall update within the EPG session to reflect time-of-day changes | P1 | 2 | Given a user has the EPG open at 6 PM and keeps it open until 8 PM, then the channel order updates at the 30-minute refresh to reflect evening viewing patterns |

### 5.2 "Your Schedule" AI-Curated Timeline

**Description:** An alternative to the traditional grid view, "Your Schedule" presents a personalized timeline of recommended programs throughout the day. It pulls from all content sources -- live programs, catch-up content, recordings, and VOD -- and presents them as a curated viewing plan.

**Design:**
- Vertical timeline layout (morning → evening)
- Each entry shows: program thumbnail, title, source type (Live / Catch-Up / VOD / Recording), channel (if applicable), start time, duration, and relevance reason
- Mix ratio: approximately 50% live (upcoming/current), 25% catch-up, 15% VOD, 10% recordings
- Maximum 12-15 entries per day to avoid overwhelming the viewer
- Each entry includes a one-line AI-generated reason: "Because you love nature documentaries" or "Trending -- 32,000 viewers yesterday"

**Requirements:**

| ID | Requirement | Priority | Phase | Acceptance Criteria |
|----|-------------|----------|-------|---------------------|
| EPG-AI-010 | EPG shall provide a "Your Schedule" view as an alternative to the grid view | P0 | 2 | Given a user selects "Your Schedule," then a personalized timeline for today is displayed within 2 seconds, containing 10-15 recommended entries across live, catch-up, VOD, and recordings |
| EPG-AI-011 | "Your Schedule" entries shall include an AI-generated recommendation reason | P1 | 2 | Given a program appears in "Your Schedule," then a one-line explanation is displayed (e.g., "Because you watched similar shows" or "Trending this week") |
| EPG-AI-012 | "Your Schedule" shall be navigable forward by day (up to 7 days) and backward (up to 7 days) | P1 | 2 | Given a user navigates to tomorrow in "Your Schedule," then a curated timeline for tomorrow is generated within 2 seconds |
| EPG-AI-013 | Each "Your Schedule" entry shall provide one-tap access to the appropriate playback mode (live, catch-up, VOD, recording) | P0 | 2 | Given a user taps a catch-up entry in "Your Schedule," then catch-up playback begins within 3 seconds with no additional navigation required |
| EPG-AI-014 | "Your Schedule" shall de-duplicate content that appears in multiple sources (e.g., a show airing live and available on VOD) and present the optimal source | P1 | 2 | Given a program is available both live (upcoming) and on VOD, then "Your Schedule" shows it once with the recommended source (e.g., "Watch on VOD -- available now" if the live airing is hours away) |

### 5.3 Per-Program Relevance Scoring

**Description:** Every program in the EPG receives a relevance score (0-100) for the active viewer profile. This score powers channel ordering, "Your Schedule" curation, and visual indicators in the grid view.

**Scoring Factors:**

| Factor | Weight | Description |
|--------|--------|-------------|
| Genre match | 25% | How well the program's genre matches the profile's genre preferences |
| Viewing history match | 20% | Whether the profile watches this program, series, or channel regularly |
| Cast/creator match | 10% | Whether the program features actors or creators the profile has watched |
| Time-of-day appropriateness | 15% | Whether the program type matches the profile's time-of-day viewing patterns |
| Trending score | 10% | Real-time popularity signals (above-average viewership, social buzz) |
| Content freshness | 10% | New/premiere content scores higher than repeats |
| AI tag match | 10% | Mood, theme, and content tag alignment with profile preferences |

**Requirements:**

| ID | Requirement | Priority | Phase | Acceptance Criteria |
|----|-------------|----------|-------|---------------------|
| EPG-AI-020 | Every program in the EPG shall receive a relevance score (0-100) per profile | P0 | 1 | Given a profile is active, when the EPG loads, then every visible program has a computed relevance score available for ranking and display |
| EPG-AI-021 | Programs with relevance scores above 80 shall display a "Recommended" badge in the EPG grid | P1 | 1 | Given a program has a relevance score of 85 for the active profile, when it appears in the grid, then a "Recommended for you" badge is visible |
| EPG-AI-022 | Relevance scoring shall complete within the request lifecycle (< 200ms for a visible page of programs) | P0 | 1 | Given the EPG loads a page of 50 program entries, when relevance scores are computed, then all scores are available within 200ms |
| EPG-AI-023 | Users shall be able to provide feedback on relevance (e.g., "Not interested" on a recommended program) | P1 | 2 | Given a user marks a recommended program as "Not interested," then the program's relevance score is suppressed for that profile and the signal feeds back to the recommendation model within 1 hour |

### 5.4 "Family Schedule" Co-Viewing Mode

**Description:** When the platform detects that multiple household members are watching together (based on time, device, and historical co-viewing patterns), the EPG offers a "Family Schedule" mode optimized for group viewing.

**Detection Signals:**
- Time-of-day and day-of-week patterns (Friday evening = typical family time)
- Device type (living room TV = more likely co-viewing than mobile)
- Historical co-viewing sessions (if the household frequently watches together at this time)
- Active profile switches (if profiles were recently switched or the "family" profile is active)

**Behavior:**
- "Family Schedule" is suggested as an overlay: "Watching together? Try Family Schedule"
- Content is filtered by the most restrictive parental control setting of present household members
- Recommendations blend interests of all likely-present members, weighted by co-viewing history
- The user can dismiss the suggestion or manually toggle Family Schedule on/off

**Requirements:**

| ID | Requirement | Priority | Phase | Acceptance Criteria |
|----|-------------|----------|-------|---------------------|
| EPG-AI-030 | EPG shall detect likely co-viewing sessions and suggest "Family Schedule" mode | P1 | 2 | Given it is Friday 7 PM and the household has co-viewed on 3+ previous Friday evenings, when the EPG opens on the living room TV, then a "Family Schedule" suggestion appears with > 70% precision |
| EPG-AI-031 | "Family Schedule" mode shall filter out content above the most restrictive age rating of household members | P0 | 2 | Given a household includes an 8-year-old with a kids profile (max PG), when "Family Schedule" is active, then no programs rated above PG are displayed |
| EPG-AI-032 | "Family Schedule" recommendations shall blend interests of all likely-present household members | P1 | 2 | Given David likes sports and Amara likes cooking, when "Family Schedule" is active, then recommendations include programs with broad appeal plus a mix of both interests |
| EPG-AI-033 | Users shall be able to dismiss "Family Schedule" suggestion or toggle it off at any time | P0 | 2 | Given the "Family Schedule" suggestion appears, when the user dismisses it, then the EPG returns to the individual profile view and the dismissal is recorded to reduce future suggestion frequency |

### 5.5 Smart Reminders and Notifications

**Description:** The EPG AI proactively notifies viewers about upcoming programs that match their interests, without requiring manual reminder setup.

**Rules:**
- Notifications are triggered based on viewing history and relevance scoring (programs scoring > 85 for the profile)
- Frequency capped: maximum 3 EPG-triggered notifications per day per profile
- Time sensitivity: notifications sent 15-30 minutes before the program starts (configurable)
- Channel: push notification (mobile), on-screen notification (TV if app is open), or in-app badge
- Smart deduplication: if a user has already set a manual reminder or scheduled a recording, no AI notification is sent
- Opt-out: users can disable smart reminders entirely or per channel/genre

**Requirements:**

| ID | Requirement | Priority | Phase | Acceptance Criteria |
|----|-------------|----------|-------|---------------------|
| EPG-AI-040 | EPG shall trigger smart notifications for programs with relevance score > 85 for the active profile | P1 | 2 | Given a program scores 90 for Erik's profile and airs in 30 minutes, when no manual reminder or recording exists, then a push notification is sent 15 minutes before start |
| EPG-AI-041 | Smart notifications shall be frequency capped at a maximum of 3 per day per profile | P0 | 2 | Given a profile has already received 3 smart notifications today, when a 4th qualifying program is identified, then no notification is sent |
| EPG-AI-042 | Users shall be able to configure smart reminder preferences (enable/disable, frequency, genre exclusions, time window) | P1 | 2 | Given a user disables smart reminders for "Reality TV," when a reality show scores > 85, then no notification is sent for that genre |
| EPG-AI-043 | Smart reminders shall not duplicate manually set reminders or recording notifications | P0 | 2 | Given a user has set a manual reminder for a program, when the smart reminder system evaluates the same program, then it skips notification |

### 5.6 Program Enrichment

**Description:** The EPG leverages AI to enrich program metadata beyond what is provided by the EPG data feed. This includes generating summaries when editorial descriptions are unavailable, adding social signals, and linking related content.

**Requirements:**

| ID | Requirement | Priority | Phase | Acceptance Criteria |
|----|-------------|----------|-------|---------------------|
| EPG-AI-050 | EPG shall display AI-generated program summaries when editorial summaries are unavailable or insufficient (< 50 characters) | P1 | 2 | Given a program lacks an editorial summary, when its detail overlay is shown, then an AI-generated summary of 2-3 sentences is displayed, generated by the content enrichment pipeline |
| EPG-AI-051 | EPG shall display social signals on programs: "Trending" badge for above-average viewership, viewer count for live programs, "Most Recorded" for popular recordings | P1 | 2 | Given a live program has 2x the average viewership for its time slot, when it appears in the EPG, then a "Trending" badge is displayed |
| EPG-AI-052 | Program detail shall show AI-generated related content: similar programs this week, related VOD titles, and "viewers also watched" suggestions | P1 | 2 | Given a user views a program detail, then at least 3 related content items are displayed (mix of EPG entries and VOD titles) |
| EPG-AI-053 | AI-generated content tags (mood, theme, suitability) shall be visible in the EPG program detail | P2 | 3 | Given the content enrichment pipeline has tagged a program with mood/theme tags, when the detail overlay is shown, then tags like "Suspenseful," "Family-Friendly," or "Feel-Good" are displayed |

---

## 6. Non-Functional Requirements

### Performance

| ID | Requirement | Target | Measurement |
|----|-------------|--------|-------------|
| EPG-NFR-001 | EPG initial grid load time | < 2 seconds (p95) from EPG open to first visible grid | Client-side telemetry: time from EPG navigation action to first rendered grid frame |
| EPG-NFR-002 | EPG time scroll latency | < 100ms (p95) per scroll step (smooth 60fps scrolling) | Client-side frame rate and input-to-render latency |
| EPG-NFR-003 | EPG channel scroll latency | < 100ms (p95) per scroll step | Client-side frame rate measurement |
| EPG-NFR-004 | Program detail overlay load time | < 300ms (p95) from selection to full detail display | Client-side telemetry |
| EPG-NFR-005 | "Your Schedule" load time | < 2 seconds (p95) from view switch to rendered timeline | Client-side telemetry |
| EPG-NFR-006 | Personalized relevance scoring latency | < 200ms (p95) for scoring a page of 50 programs | Server-side (Recommendation Service) latency measurement |
| EPG-NFR-007 | Search results latency | < 500ms (p95) for keyword search; < 1 second for semantic search | Server-side (Search Service) latency measurement |
| EPG-NFR-008 | Channel order personalization computation | < 500ms (p95) for computing personalized order for 200+ channels | Server-side (Recommendation Service) latency |

### Availability and Reliability

| ID | Requirement | Target | Measurement |
|----|-------------|--------|-------------|
| EPG-NFR-010 | EPG Service availability | 99.95% monthly uptime | Server-side uptime monitoring (excluding scheduled maintenance) |
| EPG-NFR-011 | EPG data freshness | Schedule data updated within 5 minutes of source change | Time delta between EPG provider update and platform EPG update |
| EPG-NFR-012 | Graceful degradation under AI failure | EPG falls back to traditional grid with popularity-weighted channel order when AI is unavailable | Automated failover test: disable AI services and verify EPG functionality |

### Scale

| ID | Requirement | Target | Measurement |
|----|-------------|--------|-------------|
| EPG-NFR-020 | Concurrent EPG users | Support 500,000 concurrent EPG sessions at Phase 4 | Load test: 500K simulated EPG sessions with grid navigation |
| EPG-NFR-021 | Channel count | Support 200+ channels with full schedule data | Functional test with 250-channel dataset |
| EPG-NFR-022 | Schedule data volume | 14-day schedule for 200+ channels (~400,000 program entries) | Database and cache capacity verification |
| EPG-NFR-023 | EPG API throughput | EPG Service handles 2,000 RPS at Phase 1, scaling to 10,000 RPS at Phase 4 | Load test with target RPS and p99 latency < 100ms |

### Data Quality

| ID | Requirement | Target | Measurement |
|----|-------------|--------|-------------|
| EPG-NFR-030 | Schedule data completeness | > 99% of programs have title, start time, end time, genre, and synopsis | Automated completeness audit against EPG data feed |
| EPG-NFR-031 | AI relevance scoring accuracy | Recommended programs (score > 80) result in a play event > 25% of the time | A/B test: compare play rate for AI-recommended vs non-recommended programs |
| EPG-NFR-032 | Channel order accuracy | AI-personalized top-10 channels contain > 6 of the user's most-watched channels at that time-of-day | Offline evaluation against held-out viewing data |

---

## 7. Technical Considerations

### EPG Data Ingest Pipeline

The EPG data ingest pipeline receives schedule data from external EPG data providers (e.g., Gracenote, TiVo/Rovi) via scheduled XML/JSON feeds or real-time API updates.

**Ingest Flow:**
1. **Receiver:** EPG Ingest Service polls the provider API at 5-minute intervals (or receives webhook notifications for real-time changes)
2. **Validation:** Incoming schedule data is validated against a schema (mandatory fields: channel ID, program title, start time, end time, genre)
3. **Normalization:** Program IDs are mapped to internal content IDs; genre taxonomies are normalized to the platform's standard taxonomy
4. **Enrichment:** The Metadata Service runs AI enrichment for programs lacking editorial summaries or tags
5. **Storage:** Schedule data is written to PostgreSQL (source of truth) and pre-composed grid data is pushed to Redis (CQRS read model)
6. **Events:** `epg.schedule.updated` events are published to Kafka for downstream consumers (Recording Service, Notification Service, Recommendation Service)

**Technology:**
- EPG Service: Go, PostgreSQL 16, Redis 7 (as per ARCH-001)
- Schedule cache in Redis: pre-composed per-channel per-day schedule grids (JSON) for fast client retrieval
- Elasticsearch index for EPG search across programs

### Client-Side EPG Rendering

**Grid Rendering Strategy:**
- The EPG grid is rendered using a virtualized list approach -- only visible cells are rendered in the DOM/view hierarchy
- Cells outside the visible viewport are recycled to maintain performance across 200+ channels
- Time-axis scrolling loads data in 6-hour blocks, pre-fetching adjacent blocks during scroll
- Channel-axis scrolling loads data in 20-channel blocks with pre-fetch

**BFF Integration:**
- The TV BFF (and Mobile/Web BFFs) compose EPG API responses tailored per client:
  - **TV BFF:** Pre-composed grid layouts with focus management metadata, image URLs pre-sized for TV resolution
  - **Mobile BFF:** Compact schedule payloads, touch-optimized layout hints
  - **Web BFF:** SEO-friendly schedule data, responsive grid hints

### AI Integration Architecture

**Personalized Channel Order:**
1. Client requests EPG grid from BFF
2. BFF calls Recommendation Service with profile ID, time-of-day, device type
3. Recommendation Service queries Feature Store for user channel affinity features
4. Model scores and ranks channels, applies pin overrides, returns ordered list
5. BFF composes EPG response with AI-ordered channel list
6. Fallback: If Recommendation Service is unavailable (timeout after 200ms), BFF returns channels in default number order

**Relevance Scoring:**
1. When BFF composes EPG response, it includes program IDs for visible entries
2. BFF calls Recommendation Service in parallel for batch relevance scoring
3. Recommendation Service scores up to 50 programs per request using online features from Feature Store
4. Scores are cached per profile per program (TTL: 30 minutes) in Redis
5. Fallback: Programs without scores are displayed without recommendation badges

**"Your Schedule" Generation:**
1. Client requests "Your Schedule" from BFF with profile ID, date, and device type
2. BFF calls Recommendation Service for a curated timeline
3. Recommendation Service queries: live schedule (EPG Service), catch-up catalog (TSTV/Catalog Service), VOD catalog (Catalog Service), user recordings (Recording Service)
4. Multi-source ranking model produces a scored list of 12-15 items per day
5. BFF composes response with unified timeline entries
6. Fallback: If AI unavailable, BFF returns a popularity-based timeline from pre-computed cache

### Caching Strategy

| Cache Layer | Data | TTL | Storage |
|-------------|------|-----|---------|
| Redis (EPG grid) | Pre-composed per-channel per-day schedule | 5 minutes (refreshed on schedule change) | ~200 MB for 200 channels x 14 days |
| Redis (relevance scores) | Per-profile per-program relevance scores | 30 minutes | ~5 MB per 10,000 active profiles |
| Redis (channel order) | Per-profile AI-computed channel order | 30 minutes | ~1 MB per 10,000 active profiles |
| Redis ("Your Schedule") | Per-profile curated daily timeline | 15 minutes | ~2 MB per 10,000 active profiles |
| CDN (EPG images) | Program thumbnails and channel logos | 24 hours | Managed by CDN |

---

## 8. Dependencies

### Upstream Dependencies (EPG depends on)

| Dependency | Service/PRD | Nature | Impact if Unavailable |
|------------|------------|--------|----------------------|
| EPG data provider | External (Gracenote/TiVo) | Schedule data feed | EPG shows stale data; degrade to last-known-good schedule |
| Recommendation Service | ARCH-001 (AI/ML Services) | AI scoring, channel ordering, "Your Schedule" | EPG falls back to popularity-based ordering and no personalization |
| Feature Store | ARCH-001 (AI/ML Infrastructure) | User features for scoring | AI models cannot score; fallback to non-personalized EPG |
| Entitlement Service | ARCH-001 (Core Services) | Channel package verification | Cannot filter channels by subscription; show all with warning |
| Profile Service | ARCH-001 (Core Services) | Active profile identity | Cannot personalize; show default household view |

### Downstream Dependencies (services that depend on EPG)

| Dependent | PRD | Nature | Integration |
|-----------|-----|--------|-------------|
| Live TV | PRD-001 | EPG provides program metadata for live playback (mini-guide, now/next) | EPG Service API + Kafka `epg.schedule.updated` events |
| TSTV (Start Over / Catch-Up) | PRD-002 | EPG provides schedule data to determine start-over eligibility and catch-up catalog | EPG Service API + catch-up availability flags in schedule data |
| Cloud PVR | PRD-003 | EPG provides schedule data for recording scheduling, series-link detection | EPG Service API + Kafka events for schedule changes (conflict resolution) |
| VOD/SVOD | PRD-004 | EPG "Your Schedule" references VOD content alongside linear programs | Catalog Service API for VOD metadata; cross-reference in Recommendation Service |
| Multi-Client | PRD-006 | All clients render the EPG; BFF layer tailors responses per client | BFF layer consumes EPG Service API; per-client rendering logic in client apps |
| AI User Experience | PRD-007 | EPG is a primary surface for AI recommendations; shares the Recommendation Service | Recommendation Service is shared; EPG-specific recommendation models configured in model serving |
| AI Backend/Ops | PRD-008 | Predictive cache warming uses EPG schedule data to pre-populate CDN caches | EPG schedule data consumed by CDN intelligence module via Kafka events |

### Cross-PRD Integration Points

- **PRD-001 (Live TV):** "Watch Live" action from EPG initiates a live playback session. Mini-guide overlay during live viewing pulls data from EPG Service.
- **PRD-002 (TSTV):** "Start Over" action from EPG initiates TSTV playback. Catch-up availability flags in EPG entries come from TSTV rights data.
- **PRD-003 (Cloud PVR):** "Record" action from EPG creates a recording request via the Recording Service. Schedule changes in EPG trigger recording conflict checks.
- **PRD-004 (VOD):** "Your Schedule" includes VOD recommendations alongside linear content. Program detail shows related VOD titles.
- **PRD-006 (Multi-Client):** EPG rendering is platform-specific (remote navigation on TV, touch on mobile, click on web). BFF layer handles per-platform adaptation.
- **PRD-007 (AI UX):** EPG relevance scoring uses the shared Recommendation Service. Personalized EPG is a primary surface for AI-powered discovery.
- **PRD-008 (AI Ops):** EPG schedule data feeds predictive cache warming and demand forecasting models.

---

## 9. Success Metrics

| Metric | Description | Baseline | Phase 1 Target | Phase 2 Target | Phase 4 Target | Measurement Method |
|--------|-------------|----------|---------------|---------------|---------------|-------------------|
| EPG-to-Play Rate | % of EPG sessions that result in a play event (live, catch-up, or VOD) | 42% | 50% | 58% | 65% | Client telemetry: EPG open → play event within session |
| Mean Time to Play from EPG | Time from EPG open to first play event | 3.2 min | 2.5 min | 1.8 min | 1.2 min | Client telemetry: timestamp delta |
| AI Channel Order Accuracy | % of top-10 AI-ordered channels matching user's actual top-10 viewed | N/A | 60% | 72% | 80% | Offline evaluation against actual viewing data |
| "Your Schedule" Adoption | % of EPG sessions using "Your Schedule" view (vs grid) | N/A | N/A | 25% | 45% | Client telemetry: view selection tracking |
| "Your Schedule" Play Rate | % of "Your Schedule" entries that result in a play event | N/A | N/A | 35% | 50% | Client telemetry: entry tap → play event |
| Smart Reminder Engagement | % of AI-triggered notifications that result in a tune-in | N/A | N/A | 22% | 30% | Notification delivery → play event within 5 minutes |
| "Family Schedule" Usage | % of co-viewing sessions that activate "Family Schedule" | N/A | N/A | 15% | 30% | Client telemetry: co-viewing detection → family mode activation |
| EPG Grid Load Time (p95) | Time from EPG open to first rendered grid | 3.5 sec | < 2 sec | < 1.5 sec | < 1 sec | Client telemetry |
| Relevance Score Precision | % of programs scored > 80 that are actually viewed | N/A | 20% | 28% | 35% | Offline precision@k evaluation |
| EPG Search Success Rate | % of EPG searches resulting in a play within 2 min | 48% | 55% | 65% | 75% | Client telemetry: search → play event tracking |

---

## 10. Open Questions & Risks

### Open Questions

| ID | Question | Owner | Impact | Target Decision Date |
|----|----------|-------|--------|---------------------|
| EPG-OQ-001 | Which EPG data provider(s) will supply schedule data? Gracenote and TiVo/Rovi have different coverage and API models. | Business / Content Ops | Determines ingest pipeline design and schedule data quality | Month 1 |
| EPG-OQ-002 | Should "Your Schedule" be the default view for new users, or should users discover it manually? | Product / UX | Impacts adoption rate and first-time user experience | Month 3 |
| EPG-OQ-003 | How should channel ordering handle channel number regulations (some markets require specific numbering)? | Product / Legal | May constrain AI channel ordering in certain markets | Month 2 |
| EPG-OQ-004 | Should the EPG display programs from channels outside the user's subscription (with upgrade prompts), or hide them entirely? | Product / Business | Impacts upsell opportunity vs EPG clutter | Month 2 |
| EPG-OQ-005 | What is the minimum viewing history threshold before enabling AI personalization? (e.g., 7 days vs 14 days) | AI/ML | Affects cold-start behavior and first-week experience | Month 4 |

### Risks

| ID | Risk | Severity | Likelihood | Mitigation |
|----|------|----------|------------|------------|
| EPG-R-001 | **EPG data quality is poor** -- missing program entries, incorrect times, or incomplete metadata from provider leads to bad user experience | High | Medium | Validate all ingest data against schema; run automated quality audits daily; flag programs with missing metadata for AI enrichment; negotiate data quality SLAs with provider |
| EPG-R-002 | **AI channel ordering feels "wrong" to users** -- AI reordering violates user expectations (users expect familiar channel positions) and causes confusion | Medium | High | Default to AI order but make "Traditional" order one tap away; provide gradual onboarding (explain personalization); pin favorites to anchor familiar channels; A/B test adoption |
| EPG-R-003 | **"Your Schedule" relevance is poor at launch** -- insufficient data or model immaturity leads to irrelevant suggestions, undermining trust | High | Medium | Launch "Your Schedule" in Phase 2 (not Phase 1) to allow viewing data accumulation; use editorial curation as supplement; set quality threshold -- only show entries with relevance > 70 |
| EPG-R-004 | **Co-viewing detection false positives** -- "Family Schedule" is suggested when only one person is watching, creating annoyance | Low | High | Set high confidence threshold (> 0.7) for co-viewing detection; make suggestion dismissable with one action; reduce suggestion frequency after repeated dismissals |
| EPG-R-005 | **Smart notification fatigue** -- even with frequency capping, AI notifications feel intrusive or irrelevant | Medium | Medium | Start with conservative cap (2/day), measure engagement before increasing; allow granular opt-out (per genre, per channel); suppress notifications during "do not disturb" hours |
| EPG-R-006 | **EPG grid performance on low-end Smart TVs** -- rendering 200+ channels with AI personalization data strains resource-constrained Tizen/webOS devices | High | High | Implement virtualized rendering (only visible cells in DOM); compute all personalization server-side (BFF); test on lowest-tier target devices early; define device-tier feature sets (basic EPG for low-end) |
| EPG-R-007 | **Regulatory requirements for channel ordering** -- some markets mandate specific channel numbering (e.g., public broadcasters at positions 1-5), conflicting with AI ordering | Medium | Medium | Implement per-market channel ordering rules as constraints; AI ordering operates within regulatory constraints; consult legal team for target market requirements |

---

*This PRD defines the requirements for the AI-personalized Electronic Program Guide. It serves as the reference for engineering design, user story generation, and acceptance testing. Cross-PRD integration points should be validated against PRD-001 (Live TV), PRD-002 (TSTV), PRD-003 (Cloud PVR), PRD-004 (VOD/SVOD), PRD-006 (Multi-Client), PRD-007 (AI User Experience), and PRD-008 (AI Backend/Ops).*
