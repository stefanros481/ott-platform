# User Stories: PRD-005 — TV Guide / Electronic Program Guide (EPG)

**Source PRD:** PRD-005-epg.md
**Generated:** 2026-02-08
**Total Stories:** 28

---

## Epic 1: EPG Grid View & Navigation

### US-EPG-001: Display EPG Grid View

**As a** viewer
**I want to** see a channel-by-time grid showing the current TV schedule
**So that** I can browse what is on now and upcoming across all channels

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** EPG-FR-010, EPG-FR-004

**Acceptance Criteria:**
- [ ] Given a user opens the EPG, when the grid loads, then channels are displayed vertically and time slots horizontally with a visible "now" indicator
- [ ] Given the EPG is opened, when 200+ channels have schedule data, then the grid renders without performance degradation
- [ ] Performance: EPG initial grid load time < 2 seconds (p95)

**AI Component:** No

**Dependencies:** EPG Service, EPG data ingest pipeline, Entitlement Service

**Technical Notes:**
- Use virtualized list rendering -- only visible cells in DOM/view hierarchy
- Pre-composed per-channel per-day schedule grids cached in Redis
- Time-axis loads in 6-hour blocks with adjacent block pre-fetch

---

### US-EPG-002: Navigate EPG Through Time

**As a** viewer
**I want to** scroll horizontally through the EPG timeline covering 7 days back and 7 days forward
**So that** I can see what was on (for catch-up) and what is coming up

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** EPG-FR-001, EPG-FR-002, EPG-FR-011

**Acceptance Criteria:**
- [ ] Given a user scrolls horizontally, when moving through the 14-day window, then schedule data is available for all days
- [ ] Given a catch-up eligible channel, when the user navigates to past days, then program entries show catch-up availability indicators
- [ ] Performance: Time scroll latency < 100ms (p95) per scroll step at smooth 60fps

**AI Component:** No

**Dependencies:** EPG Service, TSTV Service (for catch-up flags)

**Technical Notes:**
- Pre-fetch adjacent 6-hour blocks during scroll to avoid loading delays

---

### US-EPG-003: Jump to Current Time

**As a** viewer
**I want to** quickly jump back to "Now" from any position in the EPG
**So that** I can instantly see what is currently airing after browsing future/past schedules

**Priority:** P0
**Phase:** 1
**Story Points:** S
**PRD Reference:** EPG-FR-013

**Acceptance Criteria:**
- [ ] Given a user has navigated to a different date/time, when they press the "Now" button, then the EPG scrolls to the current time within 300ms
- [ ] Given the user is already at the current time, when they press "Now," then the view remains stable with no unnecessary reload

**AI Component:** No

**Dependencies:** None

**Technical Notes:**
- "Now" button should be persistently visible regardless of scroll position

---

### US-EPG-004: Jump to Specific Date

**As a** viewer
**I want to** select a specific date from a date picker in the EPG
**So that** I can quickly navigate to a day of interest without manual scrolling

**Priority:** P1
**Phase:** 1
**Story Points:** S
**PRD Reference:** EPG-FR-014

**Acceptance Criteria:**
- [ ] Given a user opens the date picker, when they select a date within the 14-day window, then the EPG navigates to that date within 500ms
- [ ] Given the date picker is open, when the user sees available dates, then dates outside the 14-day range are disabled

**AI Component:** No

**Dependencies:** None

**Technical Notes:**
- Date picker UI varies per platform (TV remote vs touch vs mouse)

---

### US-EPG-005: Mini-Guide Overlay During Live Viewing

**As a** viewer
**I want to** see a mini EPG overlay while watching live TV showing the current and next programs
**So that** I can check what is on without leaving the live stream

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** EPG-FR-015

**Acceptance Criteria:**
- [ ] Given a user is watching live TV, when they press the info/guide button, then a mini EPG overlay shows within 200ms
- [ ] Given the overlay is displayed, then it shows the current program with progress bar and the next 2 programs on the active channel
- [ ] Given the overlay is displayed, when 5 seconds pass without interaction, then it auto-dismisses

**AI Component:** No

**Dependencies:** Live TV Service (PRD-001), EPG Service

**Technical Notes:**
- Overlay must not interrupt playback; rendered as a transparent layer above the video

---

## Epic 2: Channel Filtering & Favorites

### US-EPG-006: Filter Channels by Category

**As a** viewer
**I want to** filter the EPG channel list by category (All, Favorites, HD/UHD, Genre, Package)
**So that** I can quickly narrow down to the channels I care about

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** EPG-FR-020

**Acceptance Criteria:**
- [ ] Given a user selects a channel filter, when the filter is applied, then only matching channels are displayed in the grid
- [ ] Given a filter is active, when the user navigates through time, then the filter persists within the session
- [ ] Given a genre filter "Sports" is selected, then only sports channels appear in the grid

**AI Component:** No

**Dependencies:** EPG Service, Entitlement Service (for package filter)

**Technical Notes:**
- Filter state stored client-side per session; not persisted across sessions unless user opts in

---

### US-EPG-007: Manage Favorite Channels

**As a** viewer
**I want to** mark channels as favorites and view a favorites-only EPG
**So that** I can quickly access the channels I watch most

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** EPG-FR-021, EPG-FR-022

**Acceptance Criteria:**
- [ ] Given a user adds a channel to favorites, when they select the "Favorites" filter, then only favorite channels are displayed
- [ ] Given a user sets favorites on device A, when they open EPG on device B under the same profile, then the same favorites appear within 5 seconds
- [ ] Given a user removes a channel from favorites, then it no longer appears in the favorites filter

**AI Component:** No

**Dependencies:** Profile Service (for cross-device sync)

**Technical Notes:**
- Favorites stored in Profile Service and synced via API; cached locally for offline access

---

### US-EPG-008: Display Entitlement-Restricted Channels

**As a** viewer
**I want to** see channels outside my subscription visually distinguished in the EPG
**So that** I understand which channels require an upgrade and can consider upgrading

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** EPG-FR-023

**Acceptance Criteria:**
- [ ] Given a channel is outside the user's package, when it appears in the EPG, then it is visually dimmed with an "Upgrade" badge
- [ ] Given a user selects an unsubscribed channel, then an upgrade prompt is displayed with package details
- [ ] Given a user tries to play an unsubscribed channel, then playback does not start and the upgrade flow is shown

**AI Component:** No

**Dependencies:** Entitlement Service

**Technical Notes:**
- Entitlement check performed server-side in BFF; client renders visual distinction

---

## Epic 3: Program Details & Quick Actions

### US-EPG-009: View Program Details from EPG

**As a** viewer
**I want to** select a program in the EPG and see a detail overlay with synopsis, cast, ratings, and episode info
**So that** I can decide whether to watch, record, or set a reminder

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** EPG-FR-030, EPG-FR-035

**Acceptance Criteria:**
- [ ] Given a user selects a program entry, when the detail overlay appears, then title, synopsis, duration, genre, age rating, and cast are displayed
- [ ] Given the program is episodic, then the detail overlay shows season number, episode number, and episode title
- [ ] Performance: Detail overlay loads within 300ms (p95) from selection

**AI Component:** No

**Dependencies:** EPG Service, Metadata Service

**Technical Notes:**
- Program metadata may come from cache (Redis) or Metadata Service API

---

### US-EPG-010: Quick Actions from EPG Program Detail

**As a** viewer
**I want to** take actions (Watch Live, Start Over, Record, Set Reminder) directly from the EPG program detail
**So that** I can immediately act on content I discover without navigating away

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** EPG-FR-031, EPG-FR-032, EPG-FR-033

**Acceptance Criteria:**
- [ ] Given a program is currently airing and eligible, then "Watch Live" and "Start Over" actions are both available
- [ ] Given a user taps "Record" on a future program, then a recording indicator appears on the EPG entry within 1 second
- [ ] Given a user sets a reminder, then a notification is delivered across all registered devices within 30 seconds of the configured time before the program

**AI Component:** No

**Dependencies:** Live TV Service (PRD-001), TSTV Service (PRD-002), Cloud PVR Service (PRD-003), Notification Service

**Technical Notes:**
- Action availability determined by: current time vs program time, content rights, entitlements

---

### US-EPG-011: Display Recording Indicators in EPG Grid

**As a** viewer
**I want to** see recording indicators on programs I have scheduled for recording in the EPG grid
**So that** I know at a glance which programs are being recorded

**Priority:** P0
**Phase:** 2
**Story Points:** S
**PRD Reference:** EPG-FR-034

**Acceptance Criteria:**
- [ ] Given a program has a scheduled recording, when it appears in the EPG grid, then a recording icon is visible on the program cell
- [ ] Given a recording is in progress, then the recording icon shows an "active recording" state
- [ ] Given a recording is cancelled, then the recording indicator is removed within 5 seconds

**AI Component:** No

**Dependencies:** Cloud PVR Service (PRD-003)

**Technical Notes:**
- Recording status fetched from Recording Service and merged into EPG grid data at the BFF layer

---

## Epic 4: EPG Search

### US-EPG-012: Search Within EPG Schedule

**As a** viewer
**I want to** search for programs by title, genre, or keyword within the EPG schedule
**So that** I can find specific programs across all channels and the 14-day window

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** EPG-FR-040, EPG-FR-041

**Acceptance Criteria:**
- [ ] Given a user enters a search query, when results are returned, then matching programs across all channels and the 14-day window are displayed within 500ms
- [ ] Given search results are displayed, then each result shows an availability badge (Live Now, Upcoming, Catch-Up, Recordable)
- [ ] Given a user taps a search result, then the program detail overlay appears with quick actions

**AI Component:** No

**Dependencies:** EPG Service, Elasticsearch index

**Technical Notes:**
- Elasticsearch index covers all program entries in the 14-day EPG window
- Results ranked by relevance with availability badges computed at query time

---

### US-EPG-013: AI Semantic Search in EPG

**As a** viewer
**I want to** search the EPG with natural language queries like "funny cooking shows this week"
**So that** I can discover programs using conversational language rather than exact titles

**Priority:** P1
**Phase:** 3
**Story Points:** L
**PRD Reference:** EPG-FR-042

**Acceptance Criteria:**
- [ ] Given a user searches "funny cooking shows this week," then semantically relevant programs are ranked above keyword-only matches
- [ ] Given the AI search model is unavailable, then the system falls back to keyword-based search with no user-visible error
- [ ] Performance: Semantic search results returned within 1 second (p95)

**AI Component:** Yes -- Conversational search via Bedrock LLM for semantic query understanding and program matching

**Dependencies:** Search Service, Recommendation Service, Bedrock LLM

**Technical Notes:**
- Query is processed by LLM to extract intent, then matched against program embeddings in vector DB

---

## Epic 5: AI Personalized Channel Order

### US-EPG-014: AI-Personalized Channel Ordering

**As a** viewer
**I want to** see my EPG channels ordered by AI-predicted relevance based on my viewing habits and time of day
**So that** the channels I am most likely to watch appear at the top

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** EPG-AI-001, EPG-AI-004

**Acceptance Criteria:**
- [ ] Given a profile with 30+ days of viewing history, when the EPG opens, then channels watched most frequently at the current time-of-day appear in the top 10 positions with > 80% accuracy
- [ ] Given a new user with no viewing history, then the EPG shows a popularity-weighted channel order
- [ ] Performance: Channel order personalization computed in < 500ms (p95) for 200+ channels

**AI Component:** Yes -- ML model scores channel relevance per profile using viewing history, time-of-day, and genre affinity features from the Feature Store

**Dependencies:** Recommendation Service, Feature Store, Profile Service

**Technical Notes:**
- Channel order cached per profile in Redis with 30-minute TTL
- Fallback to default number order if Recommendation Service is unavailable (200ms timeout)

---

### US-EPG-015: Toggle Between AI and Traditional Channel Order

**As a** viewer
**I want to** switch between AI-personalized and traditional number-sorted channel order
**So that** I can use the familiar channel numbering when I prefer it

**Priority:** P1
**Phase:** 1
**Story Points:** S
**PRD Reference:** EPG-AI-002

**Acceptance Criteria:**
- [ ] Given a user switches to traditional order, then channels sort by number immediately
- [ ] Given the user selects traditional order, then the preference persists until explicitly changed
- [ ] Given the user switches back to AI order, then personalized ordering resumes

**AI Component:** No (this is the toggle to opt out of AI ordering)

**Dependencies:** Profile Service (to persist preference)

**Technical Notes:**
- Preference stored per profile; default is AI order

---

### US-EPG-016: Pin Favorite Channels to Override AI Ordering

**As a** viewer
**I want to** pin specific channels to fixed positions in my EPG
**So that** my most important channels remain in predictable positions regardless of AI reordering

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** EPG-AI-003

**Acceptance Criteria:**
- [ ] Given a user pins Channel X to position 3, when the EPG refreshes, then Channel X remains at position 3 regardless of AI scoring
- [ ] Given multiple channels are pinned, then all pinned channels maintain their positions and AI ordering fills remaining slots
- [ ] Given a user unpins a channel, then it returns to AI-determined position on next refresh

**AI Component:** Yes -- AI ordering respects pin constraints as hard overrides

**Dependencies:** Profile Service, Recommendation Service

**Technical Notes:**
- Pinned positions sent to Recommendation Service as constraints; AI ranks remaining channels around pins

---

## Epic 6: "Your Schedule" AI-Curated Timeline

### US-EPG-017: View "Your Schedule" Personalized Timeline

**As a** viewer
**I want to** see a personalized daily timeline mixing live, catch-up, VOD, and recorded content recommendations
**So that** I have a curated viewing plan tailored to my interests without browsing the full grid

**Priority:** P0
**Phase:** 2
**Story Points:** XL
**PRD Reference:** EPG-AI-010, EPG-AI-012

**Acceptance Criteria:**
- [ ] Given a user selects "Your Schedule," then a personalized timeline is displayed within 2 seconds containing 10-15 recommended entries
- [ ] Given entries are displayed, then they include a mix of live (50%), catch-up (25%), VOD (15%), and recordings (10%)
- [ ] Given a user navigates forward or backward by day, then a curated timeline for that day is generated within 2 seconds

**AI Component:** Yes -- Multi-source ranking model queries live schedule, catch-up catalog, VOD catalog, and user recordings to produce a scored 12-15 item timeline

**Dependencies:** Recommendation Service, EPG Service, TSTV Service, Catalog Service, Recording Service

**Technical Notes:**
- "Your Schedule" response cached per profile in Redis with 15-minute TTL
- Fallback: popularity-based timeline from pre-computed cache if AI unavailable

---

### US-EPG-018: Recommendation Reasons in "Your Schedule"

**As a** viewer
**I want to** see why each program was recommended in "Your Schedule"
**So that** I understand the AI reasoning and can trust the suggestions

**Priority:** P1
**Phase:** 2
**Story Points:** M
**PRD Reference:** EPG-AI-011

**Acceptance Criteria:**
- [ ] Given a program appears in "Your Schedule," then a one-line explanation is displayed (e.g., "Because you watched similar shows" or "Trending this week")
- [ ] Given a recommendation reason is shown, then it is generated by the Recommendation Service and not a static template
- [ ] Given the reason generation fails, then the entry is still shown without a reason (graceful degradation)

**AI Component:** Yes -- Recommendation Service generates explainability strings for each suggested item

**Dependencies:** Recommendation Service

**Technical Notes:**
- Explainability strings generated alongside recommendations; cached together

---

### US-EPG-019: One-Tap Playback from "Your Schedule"

**As a** viewer
**I want to** tap a "Your Schedule" entry and immediately start playback in the appropriate mode
**So that** I can watch recommended content without additional navigation

**Priority:** P0
**Phase:** 2
**Story Points:** M
**PRD Reference:** EPG-AI-013

**Acceptance Criteria:**
- [ ] Given a user taps a catch-up entry, then catch-up playback begins within 3 seconds
- [ ] Given a user taps a live entry, then live playback begins within 2 seconds
- [ ] Given a user taps a VOD entry, then VOD playback begins within 3 seconds

**AI Component:** No (playback itself is not AI-driven)

**Dependencies:** Live TV Service (PRD-001), TSTV Service (PRD-002), VOD Service (PRD-004), Cloud PVR Service (PRD-003)

**Technical Notes:**
- Entry metadata includes source type and deep-link parameters for direct playback initiation

---

### US-EPG-020: De-Duplicate Cross-Source Content in "Your Schedule"

**As a** viewer
**I want to** see each recommended program listed only once in "Your Schedule" even if it is available from multiple sources
**So that** the timeline is clean and the best viewing option is automatically selected

**Priority:** P1
**Phase:** 2
**Story Points:** M
**PRD Reference:** EPG-AI-014

**Acceptance Criteria:**
- [ ] Given a program is available both live (upcoming) and on VOD, then "Your Schedule" shows it once with the recommended source
- [ ] Given de-duplication occurs, then the entry indicates the optimal source (e.g., "Watch on VOD -- available now")
- [ ] Given multiple sources exist, then the user can access alternative sources from the entry detail

**AI Component:** Yes -- Source optimization logic in Recommendation Service selects the best source based on availability, quality, and user context

**Dependencies:** Recommendation Service, Catalog Service

**Technical Notes:**
- Content matching across sources uses internal content IDs; Recommendation Service applies source preference logic

---

## Epic 7: Relevance Scoring

### US-EPG-021: Per-Program Relevance Scoring

**As a** viewer
**I want to** see "Recommended for you" badges on programs that match my interests in the EPG grid
**So that** I can quickly identify content tailored to my preferences

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** EPG-AI-020, EPG-AI-021, EPG-AI-022

**Acceptance Criteria:**
- [ ] Given a profile is active, when the EPG loads, then every visible program has a computed relevance score (0-100)
- [ ] Given a program has a relevance score above 80, then a "Recommended for you" badge is displayed on the EPG entry
- [ ] Performance: Relevance scoring completes within 200ms (p95) for a visible page of 50 programs

**AI Component:** Yes -- Hybrid scoring model considers genre match (25%), viewing history (20%), cast/creator match (10%), time-of-day (15%), trending (10%), freshness (10%), AI tags (10%)

**Dependencies:** Recommendation Service, Feature Store

**Technical Notes:**
- Scores cached per profile per program in Redis with 30-minute TTL
- Batch scoring: BFF sends program IDs for visible entries, Recommendation Service scores in parallel

---

### US-EPG-022: Provide Relevance Feedback

**As a** viewer
**I want to** mark a recommended program as "Not interested"
**So that** future recommendations better reflect my preferences

**Priority:** P1
**Phase:** 2
**Story Points:** M
**PRD Reference:** EPG-AI-023

**Acceptance Criteria:**
- [ ] Given a user marks a recommended program as "Not interested," then the badge is removed and the program is visually de-emphasized
- [ ] Given negative feedback is submitted, then the signal feeds back to the recommendation model within 1 hour
- [ ] Given a user has given feedback on multiple programs, then future relevance scores adjust accordingly

**AI Component:** Yes -- Feedback loop: explicit signal ingested via Kafka, incorporated into model retraining

**Dependencies:** Recommendation Service, Data Platform

**Technical Notes:**
- Feedback event published to Kafka topic; consumed by ML pipeline for model updates

---

## Epic 8: Family Schedule & Co-Viewing

### US-EPG-023: Detect Co-Viewing and Suggest Family Schedule

**As a** parent
**I want to** have the EPG automatically suggest "Family Schedule" mode when my family is watching together
**So that** we see content appropriate for everyone without manual setup

**Priority:** P1
**Phase:** 2
**Story Points:** L
**PRD Reference:** EPG-AI-030, EPG-AI-033

**Acceptance Criteria:**
- [ ] Given it is a typical co-viewing time (e.g., Friday 7 PM) and the household has co-viewed on 3+ previous occasions, then a "Family Schedule" suggestion appears with > 70% precision
- [ ] Given the suggestion appears, when the user dismisses it, then the EPG returns to individual profile view
- [ ] Given the user dismisses repeatedly, then suggestion frequency decreases

**AI Component:** Yes -- Co-viewing detection model uses time, device type, day-of-week, and historical co-viewing patterns

**Dependencies:** Profile Service, Recommendation Service

**Technical Notes:**
- Detection runs at EPG open; confidence threshold > 0.7 to trigger suggestion

---

### US-EPG-024: Family Schedule Content Filtering

**As a** parent
**I want to** ensure "Family Schedule" mode filters content above the most restrictive age rating in my household
**So that** my children are not exposed to inappropriate content

**Priority:** P0
**Phase:** 2
**Story Points:** M
**PRD Reference:** EPG-AI-031, EPG-AI-032

**Acceptance Criteria:**
- [ ] Given a household includes a child profile with max PG rating, when "Family Schedule" is active, then no programs rated above PG are displayed
- [ ] Given "Family Schedule" is active, then recommendations blend interests of all household members
- [ ] Given "Family Schedule" is active, then the user can switch back to their individual profile view at any time

**AI Component:** Yes -- Recommendation model blends multi-profile interests while applying the most restrictive age constraint

**Dependencies:** Profile Service (for household member age ratings), Recommendation Service

**Technical Notes:**
- Household members and their age restrictions fetched from Profile Service; Recommendation Service applies content filtering

---

## Epic 9: Smart Reminders & Notifications

### US-EPG-025: AI Smart Reminders for Relevant Programs

**As a** sports fan
**I want to** receive proactive notifications about upcoming programs that match my interests
**So that** I never miss live events or shows I care about without manually setting reminders

**Priority:** P1
**Phase:** 2
**Story Points:** L
**PRD Reference:** EPG-AI-040, EPG-AI-041, EPG-AI-043

**Acceptance Criteria:**
- [ ] Given a program scores > 85 for a profile and airs in 30 minutes with no existing reminder/recording, then a push notification is sent 15 minutes before start
- [ ] Given a profile has received 3 smart notifications today, then no additional notifications are sent
- [ ] Given a user has a manual reminder or recording for a program, then the smart reminder system skips it

**AI Component:** Yes -- Relevance scoring triggers notification pipeline; frequency capping and deduplication applied

**Dependencies:** Recommendation Service, Notification Service, Cloud PVR Service (for recording status check)

**Technical Notes:**
- Notification scheduling runs as a batch job 30 minutes ahead of each time slot; checks existing reminders/recordings before sending

---

### US-EPG-026: Configure Smart Reminder Preferences

**As a** viewer
**I want to** configure my smart reminder settings including enable/disable, frequency, and genre exclusions
**So that** I only receive notifications that are relevant and not intrusive

**Priority:** P1
**Phase:** 2
**Story Points:** M
**PRD Reference:** EPG-AI-042

**Acceptance Criteria:**
- [ ] Given a user disables smart reminders for "Reality TV," when a reality show scores > 85, then no notification is sent for that genre
- [ ] Given a user sets frequency to max 1 per day, then only the highest-scored notification is delivered
- [ ] Given a user disables smart reminders entirely, then no AI-triggered notifications are sent

**AI Component:** No (this is the preference/control layer)

**Dependencies:** Profile Service, Notification Service

**Technical Notes:**
- Preferences stored per profile in Profile Service; Notification Service reads preferences before delivery

---

## Epic 10: Program Enrichment

### US-EPG-027: AI-Generated Program Summaries

**As a** binge watcher
**I want to** see AI-generated summaries for programs that lack editorial descriptions
**So that** I have useful information to decide whether to watch even for lesser-known content

**Priority:** P1
**Phase:** 2
**Story Points:** M
**PRD Reference:** EPG-AI-050

**Acceptance Criteria:**
- [ ] Given a program lacks an editorial summary (< 50 characters), when its detail overlay is shown, then an AI-generated summary of 2-3 sentences is displayed
- [ ] Given an editorial summary exists, then the editorial version is used (not AI-generated)
- [ ] Given AI summary generation fails, then the program detail shows the available metadata without a summary

**AI Component:** Yes -- Content enrichment pipeline generates summaries via LLM during ingest

**Dependencies:** Metadata Service, Content Enrichment Pipeline

**Technical Notes:**
- Summaries generated at ingest time and stored in Metadata Service; not generated on-the-fly

---

### US-EPG-028: Social Signals and Trending Badges

**As a** casual viewer
**I want to** see "Trending" badges and viewer counts on popular programs in the EPG
**So that** I can discover what is popular and worth watching right now

**Priority:** P1
**Phase:** 2
**Story Points:** M
**PRD Reference:** EPG-AI-051, EPG-AI-052

**Acceptance Criteria:**
- [ ] Given a live program has 2x the average viewership for its time slot, then a "Trending" badge is displayed in the EPG
- [ ] Given a user views a program detail, then at least 3 related content items are displayed (mix of EPG entries and VOD titles)
- [ ] Given social signals are unavailable, then the EPG displays normally without badges (graceful degradation)

**AI Component:** Yes -- Real-time viewership aggregation and trending detection; related content via Recommendation Service

**Dependencies:** Analytics Collector (for viewership data), Recommendation Service

**Technical Notes:**
- Trending computation runs in near-real-time from streaming viewership events; results cached with 5-minute TTL

---

## Epic 11: Accessibility

### US-EPG-029: Screen Reader Support for EPG

**As a** viewer with visual impairment
**I want to** navigate the EPG fully using a screen reader
**So that** I can browse and discover TV programs independently

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** EPG-FR-050

**Acceptance Criteria:**
- [ ] Given a screen reader is active, when navigating the EPG grid, then every program entry announces channel name, program title, start time, duration, and genre
- [ ] Given a screen reader user selects a program, then the detail overlay content is fully announced
- [ ] Given focus moves between grid cells, then the screen reader announces the new cell context

**AI Component:** No

**Dependencies:** Per-platform accessibility frameworks

**Technical Notes:**
- Each platform (TV, mobile, web) has specific accessibility APIs; test with VoiceOver (Apple), TalkBack (Android), and NVDA (web)

---

### US-EPG-030: High-Contrast Mode for EPG

**As a** viewer with visual impairment
**I want to** use the EPG in high-contrast mode
**So that** I can read program information clearly

**Priority:** P1
**Phase:** 1
**Story Points:** S
**PRD Reference:** EPG-FR-051

**Acceptance Criteria:**
- [ ] Given high-contrast mode is enabled, when the EPG is displayed, then all text and UI elements meet WCAG 2.1 AA contrast ratios (minimum 4.5:1)
- [ ] Given high-contrast mode is active, then recommendation badges and recording indicators remain visible

**AI Component:** No

**Dependencies:** Design system, per-platform theme support

**Technical Notes:**
- High-contrast theme defined in shared design system; applied via platform theme mechanism

---

## Epic 12: Non-Functional & Technical Enablers

### US-EPG-031: EPG Data Ingest Pipeline

**As a** developer
**I want to** ingest, validate, and normalize EPG schedule data from external providers
**So that** the platform has accurate and complete schedule data for all channels

**Priority:** P0
**Phase:** 1
**Story Points:** XL
**PRD Reference:** EPG-FR-003, EPG-NFR-011, EPG-NFR-030

**Acceptance Criteria:**
- [ ] Given a schedule change occurs at the provider, when 5 minutes have elapsed, then the updated data is reflected in the EPG
- [ ] Given incoming data fails schema validation, then the entry is rejected and an alert is raised without corrupting existing data
- [ ] Given the ingest pipeline processes a full 14-day schedule, then > 99% of programs have title, start time, end time, genre, and synopsis

**AI Component:** No

**Dependencies:** EPG data provider (Gracenote/TiVo), Kafka, PostgreSQL, Redis

**Technical Notes:**
- Ingest Service (Go) polls provider at 5-minute intervals or receives webhook notifications
- Validated data written to PostgreSQL (source of truth), pre-composed grids pushed to Redis

---

### US-EPG-032: EPG Schedule Change Event Publishing

**As a** developer
**I want to** publish EPG schedule change events to Kafka
**So that** downstream services (Cloud PVR, Notification, Recommendation) react to schedule changes

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** EPG-FR-005

**Acceptance Criteria:**
- [ ] Given a schedule change is processed, then an `epg.schedule.updated` event is published to Kafka within 30 seconds
- [ ] Given a program overrun occurs, then the event includes affected program IDs and updated times
- [ ] Given downstream services consume the event, then recordings and reminders are adjusted accordingly

**AI Component:** No

**Dependencies:** Kafka, Cloud PVR Service, Notification Service, Recommendation Service

**Technical Notes:**
- Events published in Avro/Protobuf format to `epg.schedule.updated` Kafka topic

---

### US-EPG-033: EPG Service Scalability and Performance

**As a** developer
**I want to** ensure the EPG Service handles target throughput with acceptable latency
**So that** the EPG performs well under peak load

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** EPG-NFR-020, EPG-NFR-023

**Acceptance Criteria:**
- [ ] Given Phase 1 load, then the EPG Service handles 2,000 RPS with p99 latency < 100ms
- [ ] Given 500,000 concurrent EPG sessions at Phase 4, then the service scales horizontally to maintain latency targets
- [ ] Given the EPG Service is under load, then no schedule data or personalization requests are dropped

**AI Component:** No

**Dependencies:** Kubernetes autoscaling, Redis caching layer

**Technical Notes:**
- Horizontal scaling via Kubernetes HPA; Redis caching reduces database load; load test with simulated EPG sessions

---

### US-EPG-034: EPG Graceful Degradation Under AI Failure

**As a** viewer
**I want to** still use the EPG normally even when AI services are unavailable
**So that** my TV browsing experience is not interrupted by backend failures

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** EPG-NFR-012

**Acceptance Criteria:**
- [ ] Given the Recommendation Service is unavailable, when the EPG loads, then channels are displayed in default number order (not AI-personalized)
- [ ] Given AI scoring is unavailable, then "Recommended" badges are not shown and no errors are displayed
- [ ] Given "Your Schedule" AI generation fails, then a popularity-based timeline is shown from pre-computed cache

**AI Component:** No (this is the fallback behavior when AI is unavailable)

**Dependencies:** BFF layer (implements fallback logic)

**Technical Notes:**
- BFF implements timeout (200ms) for Recommendation Service calls; falls back to cached or default responses

---

*End of user stories for PRD-005 (EPG). Total: 28 stories covering core EPG grid (11), AI personalization (11), accessibility (2), and technical enablers (4).*
