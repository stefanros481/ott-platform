# User Stories: Time-Shifted TV — Start Over & Catch-Up (PRD-002)

**Source PRD:** PRD-002-tstv.md
**Generated:** 2026-02-08
**Total Stories:** 28

---

## Epic 1: Start Over TV

### US-TSTV-001: Proactive Start Over Prompt on Late Tune-In

**As a** viewer
**I want to** be offered a "Start from Beginning" option when I tune into a program that has already started
**So that** I can watch the program from the beginning without missing any content

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** TSTV-FR-001

**Acceptance Criteria:**
- [ ] Given a viewer tunes to a live channel where the current program started more than 3 minutes ago, when the channel starts playing, then a Start Over prompt appears within 2 seconds
- [ ] Given the prompt is displayed, when 10 seconds pass without user action, then the prompt auto-dismisses
- [ ] Given the prompt was dismissed for a program, when the viewer stays on the same channel, then the prompt does not reappear for the same program during the same session
- [ ] Given a program does not have start-over rights, when a viewer tunes in late, then no Start Over prompt is shown
- [ ] Performance: Rights check completes in < 50ms (Redis-cached); prompt appears within 2 seconds of tune-in

**AI Component:** Yes -- AI auto-detects late tune-in and proactively offers restart with contextual messaging

**Dependencies:** EPG Service (PRD-005) for program start times, Rights Engine for start-over eligibility

**Technical Notes:**
- Start Over eligibility determined by EPG program metadata field `start_over_enabled`
- Prompt includes program title and time elapsed since start (e.g., "Started 23 min ago")

---

### US-TSTV-002: Seamless Live-to-Start Over Transition

**As a** viewer
**I want to** transition from live to the program's start point seamlessly within 3 seconds
**So that** I can restart the program without any disruption or delay

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** TSTV-FR-002

**Acceptance Criteria:**
- [ ] Given a viewer selects "Start from Beginning," when the transition initiates, then playback begins at the program start within 3 seconds (p95)
- [ ] Given the transition occurs, when playing from the start, then no re-authentication or new DRM session is required
- [ ] Given Start Over is active, when the player UI displays, then a "START OVER" badge replaces the "LIVE" badge and a scrubber bar shows position relative to live edge
- [ ] Given the transition, when audio/video plays, then there are no glitches or interruptions during the switch

**AI Component:** No

**Dependencies:** Manifest proxy service, EFS live buffer, EPG Service for program start time

**Technical Notes:**
- Manifest proxy generates a time-shifted manifest pointing to live segments from program start
- Same DRM session reused; manifest URL swap only

---

### US-TSTV-003: Full Trick-Play During Start Over

**As a** viewer
**I want to** use pause, rewind, and fast-forward at multiple speeds during Start Over playback
**So that** I can control my viewing experience just like watching a recording

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** TSTV-FR-003

**Acceptance Criteria:**
- [ ] Given Start Over is active, when the viewer presses pause/rewind/fast-forward, then the command executes within 300ms
- [ ] Given fast-forward is active, when approaching the live edge, then fast-forward stops and playback transitions to live mode
- [ ] Given rewind is active, when reaching the program start, then rewind stops at the program's first frame
- [ ] Given trick-play is used, when thumbnails are available, then I-frame thumbnail previews are displayed at 10-second intervals during scrubbing

**AI Component:** No

**Dependencies:** EFS live buffer, I-frame extraction in packaging pipeline

**Technical Notes:**
- Rewind speeds: 2x, 4x, 8x, 16x, 32x
- Fast-forward speeds: 2x, 4x, 8x
- Trick-play thumbnails generated from I-frames during live packaging

---

### US-TSTV-004: Jump to Live from Start Over

**As a** viewer
**I want to** press "Jump to Live" at any time during Start Over to return to the live broadcast
**So that** I can quickly switch back to real-time viewing

**Priority:** P0
**Phase:** 1
**Story Points:** S
**PRD Reference:** TSTV-FR-004

**Acceptance Criteria:**
- [ ] Given Start Over is active, when the viewer presses "Jump to Live," then playback returns to the live edge within 1 second
- [ ] Given the "Jump to Live" button, when rendered, then it is visually prominent in the player controls (not buried in a menu)
- [ ] Given the viewer returns to live, when the badge updates, then "START OVER" transitions smoothly to "LIVE"

**AI Component:** No

**Dependencies:** US-TSTV-002

**Technical Notes:**
- Jump to live resets manifest position to the latest segment
- Scrubber transitions from start-over range to live indicator

---

### US-TSTV-005: Start Over Rights Enforcement

**As an** operator
**I want to** enforce per-program, per-channel start-over rights
**So that** only authorized content offers the Start Over feature, respecting content rights agreements

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** TSTV-FR-005

**Acceptance Criteria:**
- [ ] Given a program with `start_over_enabled = false`, when a viewer tunes in late, then no Start Over prompt or button is displayed
- [ ] Given rights data, when queried, then the rights check completes in < 50ms from Redis cache
- [ ] Given rights data is sourced from EPG metadata, when a program's rights change, then the change propagates via Kafka (`rights.updated`) within 5 minutes

**AI Component:** No

**Dependencies:** Rights Engine, EPG Service, Redis cache

**Technical Notes:**
- Rights query: `(program_id, channel_id, territory, right_type: "start_over")` -> `{ eligible: bool }`
- Fail-closed: deny start-over if rights status is ambiguous

---

### US-TSTV-006: Bookmark Persistence During Start Over

**As a** viewer
**I want to** have my viewing position saved when I leave a program during Start Over
**So that** I can resume from where I left off later (within the catch-up window)

**Priority:** P1
**Phase:** 1
**Story Points:** M
**PRD Reference:** TSTV-FR-006

**Acceptance Criteria:**
- [ ] Given a viewer stops playback during Start Over, when the position is saved, then a bookmark is stored within 5 seconds
- [ ] Given a bookmark exists for a program, when the viewer returns to the program in catch-up or EPG, then a resume indicator shows with the bookmarked position
- [ ] Given a bookmark exists, when the viewer opens the app on a different device, then the bookmark is synced within 5 seconds (cross-device)

**AI Component:** No

**Dependencies:** Bookmark Service (Go, p99 < 50ms)

**Technical Notes:**
- Bookmark stored per: user profile, program ID, channel ID, air date
- Bookmark updates sent via playback heartbeat every 30 seconds

---

### US-TSTV-007: AI Context-Aware Start Over Messaging

**As a** viewer
**I want to** see context-aware Start Over prompts tailored to the content type
**So that** I get relevant information when deciding whether to start from the beginning

**Priority:** P1
**Phase:** 2
**Story Points:** M
**PRD Reference:** TSTV-FR-007

**Acceptance Criteria:**
- [ ] Given a sports program, when the Start Over prompt appears, then it includes match/game context (e.g., "Match started 23 min ago, current score: 1-0. Start from kick-off?") -- respecting spoiler preferences
- [ ] Given a series episode, when the prompt appears, then it shows episode context (e.g., "Episode 3 of The Bridge is 15 min in. Start from the beginning?")
- [ ] Given a film, when the prompt appears, then it shows runtime context (e.g., "This film started 45 min ago (1h 32min remaining). Start from the beginning?")
- [ ] Given the user has spoiler-free mode enabled for sports, when the prompt appears, then no scores or results are included
- [ ] Performance: Content type classification confidence > 90%

**AI Component:** Yes -- Recommendation Service provides contextual metadata; EPG Service provides program type classification

**Dependencies:** Recommendation Service (PRD-007), EPG Service (PRD-005)

**Technical Notes:**
- Content type categories: sports, series, film, news, documentary, other
- Spoiler preference stored per profile in Profile Service

---

## Epic 2: Catch-Up TV Core

### US-TSTV-008: Catch-Up Catalog Availability

**As a** viewer
**I want to** access previously aired programs on catch-up within 5 minutes of broadcast end
**So that** I can watch recently aired content almost immediately after it finishes

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** TSTV-FR-010

**Acceptance Criteria:**
- [ ] Given a program finishes broadcasting, when the catch-up pipeline processes it, then the program is available for catch-up playback within 5 minutes of broadcast end
- [ ] Given a channel with a 7-day catch-up window, when the window is active, then all eligible programs from the past 7 days are available
- [ ] Given a program's catch-up window expires, when the expiry time passes, then the program is automatically removed from the catalog within 5 minutes

**AI Component:** No

**Dependencies:** Live ingest pipeline, S3 catch-up storage, Catalog Service, EPG Service

**Technical Notes:**
- Ingest-to-catch-up pipeline: live segments copied to S3 during broadcast; full manifest assembled at program boundary
- Program boundaries from SCTE-35 markers or EPG schedule with padding (1 min pre, 3 min post)

---

### US-TSTV-009: Browse Catch-Up by Channel

**As a** viewer
**I want to** browse catch-up programs organized by channel and date
**So that** I can find a specific program I know aired on a particular channel

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** TSTV-FR-011

**Acceptance Criteria:**
- [ ] Given a viewer selects a channel in catch-up browse, when the schedule loads, then all available catch-up programs are displayed organized by date (most recent first)
- [ ] Given each program entry, when displayed, then it shows: title, start time, duration, catch-up expiry date, and play/resume button
- [ ] Performance: Channel-based browse loads in < 2 seconds; displays up to 7 days of schedule per channel

**AI Component:** No

**Dependencies:** EPG Service for schedule data, Catalog Service for catch-up availability

**Technical Notes:**
- Schedule data sourced from EPG Service; availability status from Catalog Service
- Programs without catch-up rights shown with a lock icon and "Not available on Catch-Up" label

---

### US-TSTV-010: Browse Catch-Up by Date

**As a** viewer
**I want to** browse catch-up programs by selecting a date and seeing all available content across channels
**So that** I can find content from a specific day without knowing which channel it aired on

**Priority:** P1
**Phase:** 1
**Story Points:** M
**PRD Reference:** TSTV-FR-012

**Acceptance Criteria:**
- [ ] Given a viewer selects a date in catch-up browse, when the listings load, then all available catch-up programs from that date across all channels are displayed
- [ ] Given the listings are displayed, when filters are available, then the viewer can filter by: genre (Sports, News, Entertainment, Kids, Documentary, Film, Music), channel, and duration
- [ ] Performance: Date-based browse loads in < 2 seconds; supports 7 days backward

**AI Component:** No

**Dependencies:** EPG Service, Catalog Service

**Technical Notes:**
- Cross-channel view aggregates data from EPG Service with catch-up availability from Catalog Service
- Filters applied client-side on pre-fetched data for instant response

---

### US-TSTV-011: Catch-Up Playback with Full Trick-Play

**As a** viewer
**I want to** play a catch-up program with full trick-play capability (pause, rewind, fast-forward, scrub)
**So that** I can control my viewing experience as if watching a recording or VOD content

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** TSTV-FR-013

**Acceptance Criteria:**
- [ ] Given a viewer selects a catch-up program, when playback starts, then the program begins playing within 2 seconds (p95)
- [ ] Given catch-up playback is active, when trick-play controls are used, then pause, rewind, fast-forward (2x, 4x, 8x, 16x, 32x), and scrub all function with < 300ms response time
- [ ] Given scrubbing, when thumbnail previews are available, then I-frame thumbnails are displayed for navigation
- [ ] Performance: Rebuffer ratio < 0.3% for catch-up sessions

**AI Component:** No

**Dependencies:** S3 catch-up storage, CDN delivery, player per platform

**Technical Notes:**
- Catch-up content served as standard VOD-like manifests from S3 storage via CDN
- Same player components used for VOD and catch-up playback

---

### US-TSTV-012: Catch-Up Content Expiry Handling

**As a** viewer
**I want to** see clear expiry dates on catch-up content and receive notifications before content expires
**So that** I can watch or record content before it becomes unavailable

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** TSTV-FR-014

**Acceptance Criteria:**
- [ ] Given any catch-up listing (browse, search, rail), when displayed, then the expiry date is visible on all catch-up content
- [ ] Given a catch-up program the viewer has started, when it is within 24 hours of expiry, then a notification is sent: "Expires tomorrow. Watch now or record to keep it."
- [ ] Given a "Record to PVR" button, when the user has Cloud PVR entitlement, then the button is available on expiring catch-up content to preserve it
- [ ] Given content has expired, when the viewer attempts to access a direct link, then a message shows: "This program is no longer available on Catch-Up" with a link to VOD if a VOD version exists

**AI Component:** No

**Dependencies:** Notification Service, Recording Service (PRD-003), VOD Catalog (PRD-004)

**Technical Notes:**
- Expiry notification job runs hourly, checking for programs expiring within 24 hours that the user has bookmarked
- Cross-service handoff to Cloud PVR and VOD for alternative access

---

### US-TSTV-013: Catch-Up Content Search

**As a** viewer
**I want to** search for catch-up content by title, description, or topic
**So that** I can find a specific program without browsing through channel schedules

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** TSTV-FR-015

**Acceptance Criteria:**
- [ ] Given a viewer searches for catch-up content, when results return, then they include catch-up programs matching the query within 500ms
- [ ] Given search results, when displayed, then each catch-up result shows: source channel, air date/time, duration, catch-up expiry, and availability status
- [ ] Given results include both catch-up and VOD content, when listed, then results are clearly labeled by type (catch-up vs. VOD)
- [ ] Given search, when ranking results, then relevance combines: text match, recency, user preference alignment, and catch-up expiry urgency

**AI Component:** No (standard search; AI-enriched tags improve results quality)

**Dependencies:** Search Service (Elasticsearch), EPG Service, Catalog Service

**Technical Notes:**
- Search covers: program title, description, and AI-enriched tags (mood, themes, keywords)
- Items expiring soon receive a slight boost in ranking to create urgency

---

### US-TSTV-014: Cross-Device Resume for Catch-Up

**As a** viewer
**I want to** resume a catch-up program on a different device from where I left off
**So that** I can continue watching seamlessly when switching between devices

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** TSTV-FR-016

**Acceptance Criteria:**
- [ ] Given a viewer pauses a catch-up program on one device, when opening the app on another device, then the bookmark is synced within 5 seconds
- [ ] Given a bookmark exists, when resuming, then playback starts within 5 seconds of the bookmarked position
- [ ] Given the viewer resumes, when the UI shows, then a brief "Resuming from [time]" indicator appears for 3 seconds
- [ ] Given a bookmark exists, when the catch-up content expires, then the bookmark is automatically cleaned up

**AI Component:** No

**Dependencies:** Bookmark Service, Profile Service for device sync

**Technical Notes:**
- Bookmark stored per: user profile, program ID (channel + program + air date)
- Automatic bookmark cleanup on content expiry via TTL or batch job

---

### US-TSTV-015: Auto-Play Next Episode in Catch-Up

**As a** binge watcher
**I want to** have the next episode of a series automatically offered when the current catch-up episode ends
**So that** I can binge-watch a series without manual navigation between episodes

**Priority:** P1
**Phase:** 2
**Story Points:** M
**PRD Reference:** TSTV-FR-017

**Acceptance Criteria:**
- [ ] Given a viewer finishes a series episode on catch-up, when the next episode is available on catch-up, then an auto-play countdown (default 15 seconds) offers the next episode
- [ ] Given the countdown is displayed, when configurable by the user, then the countdown can be set to 5s, 10s, 15s, 30s, or off
- [ ] Given auto-play, when triggered, then it only activates for sequential series content (not for unrelated programs)
- [ ] Given an AI override, when the next episode has low predicted engagement, then the AI may suggest a different program instead

**AI Component:** Yes -- AI determines whether to suggest next episode or recommend alternative content based on predicted engagement

**Dependencies:** EPG Service for series/episode metadata, Recommendation Service (PRD-007)

**Technical Notes:**
- Episode ordering based on air date chronology from EPG data
- AI override threshold configurable; default: suggest alternative only if next-episode engagement prediction < 30%

---

## Epic 3: Content Rights and Availability

### US-TSTV-016: Per-Channel Catch-Up Rights Defaults

**As an** operator
**I want to** configure default catch-up window durations per channel
**So that** new programs inherit the channel's catch-up policy automatically

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** TSTV-FR-020, TSTV-FR-021

**Acceptance Criteria:**
- [ ] Given a channel has a default catch-up window of 7 days, when a new program airs, then it automatically inherits the 7-day catch-up window
- [ ] Given a program-level override exists (e.g., 24-hour window for licensed films), when the override is set, then the program-level setting takes precedence over the channel default
- [ ] Given configurable window options, when set per channel, then supported values are: 0 (no catch-up), 24h, 48h, 72h, 168h (7 days)

**AI Component:** No

**Dependencies:** Rights Engine, EPG Service, Content Operations tooling

**Technical Notes:**
- Channel-level defaults stored in Rights Engine (PostgreSQL, Redis-cached)
- Program-level overrides propagated via Kafka `rights.updated` topic

---

### US-TSTV-017: Territory-Based TSTV Rights

**As an** operator
**I want to** enforce territory-specific TSTV rights so that catch-up and start-over availability varies by region
**So that** territorial content rights agreements are respected

**Priority:** P1
**Phase:** 1
**Story Points:** M
**PRD Reference:** TSTV-FR-022

**Acceptance Criteria:**
- [ ] Given a program is eligible for catch-up in Territory A but not Territory B, when a viewer in Territory B browses catch-up, then the program is not available (shown with lock icon)
- [ ] Given territory is determined, when the rights engine evaluates, then it uses the user's account region (not IP geo-location)
- [ ] Given combined rights evaluation, when all rights are checked, then the result is: program rights AND channel rights AND territory rights

**AI Component:** No

**Dependencies:** Rights Engine, User Account Service (account region)

**Technical Notes:**
- Account-based territory avoids VPN circumvention issues
- Rights engine supports allowlist and blocklist per territory

---

### US-TSTV-018: Mid-Window Rights Revocation

**As an** operator
**I want to** revoke catch-up rights for a program mid-window and have it removed promptly
**So that** contractual obligations are met if a content provider pulls rights

**Priority:** P1
**Phase:** 1
**Story Points:** M
**PRD Reference:** TSTV-FR-023

**Acceptance Criteria:**
- [ ] Given rights are revoked for a catch-up program, when the revocation event fires, then the program is removed from browse and search within 15 minutes
- [ ] Given an active playback session for revoked content, when the session is in progress, then the session is allowed to complete (not terminated mid-playback)
- [ ] Given a new play request for revoked content, when access is checked, then the request is denied with an appropriate message

**AI Component:** No

**Dependencies:** Rights Engine, Kafka (`rights.updated` topic), Catalog Service

**Technical Notes:**
- Rights revocation propagated via Kafka event consumed by Catalog Service and EPG Service
- Grace period for active sessions prevents poor user experience

---

## Epic 4: AI-Powered Catch-Up Discovery

### US-TSTV-019: Personalized "Your Catch-Up" Rail

**As a** viewer
**I want to** see an AI-curated "Your Catch-Up" rail showing programs from the past week that match my interests
**So that** I discover relevant catch-up content without manually browsing schedules

**Priority:** P1
**Phase:** 1
**Story Points:** XL
**PRD Reference:** AI Section 5.1

**Acceptance Criteria:**
- [ ] Given a viewer opens the home screen or catch-up section, when "Your Catch-Up" rail loads, then it shows 15-20 personalized suggestions
- [ ] Given each suggestion, when displayed, then it shows: thumbnail, title, channel, air date, duration, match score, and a reason ("Because you watched [X]")
- [ ] Given recommendations, when diverse, then the top 10 contain at minimum 3 different channels and 3 different genres
- [ ] Given explanation text, when present, then "Because you watched..." reasons appear for 80%+ of items
- [ ] Given the Recommendation Service is unavailable, when fallback occurs, then the rail switches to "Most Popular Catch-Up" within 500ms
- [ ] Performance: Rail loads in < 1 second (pre-computed in Redis, hourly refresh); CTR target > 12%

**AI Component:** Yes -- Recommendation Service generates per-profile catch-up recommendation set combining collaborative filtering, content-based filtering, temporal signals, recency, and expiry urgency

**Dependencies:** Recommendation Service (PRD-007), Feature Store, Catalog Service, Redis

**Technical Notes:**
- Pre-computed hourly per user, cached in Redis: `recs:catchup:{profile_id}`, TTL 60 minutes
- Includes diversity injection to prevent filter bubble

---

### US-TSTV-020: "You Missed This" Smart Notifications

**As a** viewer
**I want to** receive personalized notifications about catch-up programs I am likely to enjoy
**So that** I am made aware of content I would otherwise miss

**Priority:** P1
**Phase:** 2
**Story Points:** L
**PRD Reference:** AI Section 5.2

**Acceptance Criteria:**
- [ ] Given a new catch-up program matches the user's preferences (confidence > 80%), when the notification job runs, then a "You Missed This" notification is sent within 2 hours of program availability
- [ ] Given notification delivery, when sent, then notifications are delivered as: push (mobile), in-app (all platforms), and optionally email digest (weekly)
- [ ] Given frequency capping, when enforced, then a maximum of 3 "You Missed This" notifications per user per day are sent
- [ ] Given quiet hours, when configured (default 23:00-07:00), then no notifications are sent during quiet hours (per user timezone)
- [ ] Given sports content with spoiler-free mode, when a notification is sent, then no scores or results are included
- [ ] Given a user opts out, when configured in settings, then "You Missed This" notifications can be disabled entirely or per content type
- [ ] Performance: > 20% of notifications result in a play event within 48 hours

**AI Component:** Yes -- Recommendation Service scores new catch-up programs per user; notification timing optimized by viewing pattern prediction model

**Dependencies:** Recommendation Service (PRD-007), Notification Service, Profile Service (spoiler preferences)

**Technical Notes:**
- Scheduled job runs every 2 hours evaluating new catch-up programs
- Notification text generated via template engine with AI-selected content description

---

### US-TSTV-021: AI-Generated Program Summaries

**As a** viewer
**I want to** see rich AI-generated descriptions for catch-up programs when editorial descriptions are limited
**So that** I can make better-informed decisions about what to watch

**Priority:** P1
**Phase:** 2
**Story Points:** L
**PRD Reference:** AI Section 5.3

**Acceptance Criteria:**
- [ ] Given a catch-up program has a limited editorial description (< 50 characters), when displayed, then an AI-generated summary of 2-3 sentences is shown instead
- [ ] Given AI summaries, when generated, then they cover 90%+ of catch-up programs with limited editorial descriptions
- [ ] Given AI summaries, when read by users, then satisfaction is 85%+ vs no-summary control in A/B test
- [ ] Given summary content, when generated, then summaries are spoiler-free (no plot twists, no game results unless opted in)
- [ ] Performance: Batch generation within 30 minutes of broadcast end; inline generation < 2 seconds; cost < $0.001 per summary

**AI Component:** Yes -- Amazon Bedrock (Claude Haiku for batch, Claude Sonnet for on-demand); inputs: EPG metadata, AI-enriched tags, subtitle/transcript data

**Dependencies:** Metadata Service, EPG Service, AI content enrichment pipeline

**Technical Notes:**
- Summaries cached in Metadata Service (PostgreSQL + Redis)
- Fallback: display original EPG description if AI summary unavailable

---

### US-TSTV-022: Catch-Up Trending Content Rail

**As a** casual viewer
**I want to** see a "Trending This Week" rail showing the most-watched catch-up programs
**So that** I can easily discover popular content without browsing individual channels

**Priority:** P1
**Phase:** 1
**Story Points:** M
**PRD Reference:** Scenario 9

**Acceptance Criteria:**
- [ ] Given a viewer opens the catch-up section, when the "Trending This Week" rail loads, then it shows the top programs ranked by catch-up viewership (not live viewership)
- [ ] Given the ranking, when diversity is applied, then a minimum of 3 genres are represented in the top 10
- [ ] Given trending data, when updated, then the rail updates daily with data including catch-up views from up to 2 hours ago

**AI Component:** Yes -- Flink streaming job aggregates catch-up viewership; diversity injection ensures genre variety

**Dependencies:** Playback Session Service (catch-up session data), Flink pipeline, Redis

**Technical Notes:**
- Ranking based specifically on catch-up unique viewers, not live viewers
- Diversity injection prevents a single genre (e.g., sports) from dominating the rail

---

### US-TSTV-023: Predictive Cache Warming for Catch-Up

**As a** viewer
**I want to** experience fast playback start times for popular catch-up content
**So that** I do not wait long for content to buffer when starting a catch-up program

**Priority:** P2
**Phase:** 2
**Story Points:** XL
**PRD Reference:** AI Section 5.4

**Acceptance Criteria:**
- [ ] Given predictive cache warming is active, when catch-up content is predicted to be popular, then the first 5 minutes of content are pre-warmed on CDN edge caches
- [ ] Given pre-warmed content, when a viewer starts playback, then playback begins in < 1.5 seconds (p95) compared to < 2.5 seconds for non-warmed
- [ ] Given the prediction model, when evaluated, then 70%+ of top-50 predicted programs appear in the actual top-100 most-played
- [ ] Given cache warming, when bandwidth is measured, then pre-warming does not exceed 5% of total CDN bandwidth budget
- [ ] Performance: CDN cache hit ratio for catch-up > 80% (vs 60% baseline); origin load reduced by 30% during peak hours

**AI Component:** Yes -- XGBoost prediction model retrained daily; runs every 2 hours; top 50 programs pre-warmed on CDN edges

**Dependencies:** CDN Routing Service, CDN infrastructure, ML pipeline

**Technical Notes:**
- Prediction features: genre, channel popularity, time-of-day demand, day-of-week pattern, trending velocity, expiry proximity
- CDN Routing Service factors cache warm status into routing decisions

---

### US-TSTV-024: Viewing Pattern Prediction

**As a** viewer
**I want to** receive notifications and recommendations timed to when I typically watch catch-up content
**So that** suggestions arrive at the most relevant time for me

**Priority:** P2
**Phase:** 2
**Story Points:** L
**PRD Reference:** AI Section 5.5

**Acceptance Criteria:**
- [ ] Given a user has > 10 catch-up viewing sessions, when temporal features are computed, then per-user catch-up viewing time distribution, genre preferences per time slot, and catch-up delay patterns are available
- [ ] Given notification timing optimization, when notifications are sent at predicted optimal times, then open rate improves by 25%+ vs random timing
- [ ] Given feature freshness, when features are updated, then temporal features refresh hourly in the online Feature Store
- [ ] Given feature coverage, when measured at Phase 2 (3 months post-launch), then temporal features are available for 70%+ of active profiles

**AI Component:** Yes -- Flink streaming job computes per-user temporal viewing features from Kafka event streams; consumed by Notification Service, EPG "Your Schedule" (PRD-005), and Recommendation Service

**Dependencies:** Feature Store (Feast), Flink pipeline, Kafka

**Technical Notes:**
- Feature Store key: `user:{profile_id}:tstv_temporal`
- Features: catch-up viewing probability per hour, genre affinity per time slot, average catch-up delay per content type

---

## Epic 5: Bookmarking and Continue Watching

### US-TSTV-025: Automatic Bookmark Saving

**As a** viewer
**I want to** have my viewing position automatically saved during catch-up and start-over playback
**So that** I can resume from where I left off without manually tracking my position

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** TSTV-FR-030

**Acceptance Criteria:**
- [ ] Given a viewer is playing catch-up or start-over content, when the heartbeat fires every 30 seconds, then a bookmark update is sent to the Bookmark Service
- [ ] Given a viewer stops or pauses playback, when the stop/pause event fires, then a bookmark is saved immediately
- [ ] Given a bookmark, when stored, then it is accurate to within 5 seconds of the actual stop point
- [ ] Performance: Bookmark Service write latency p99 < 50ms

**AI Component:** No

**Dependencies:** Bookmark Service, Playback Session heartbeat mechanism

**Technical Notes:**
- Bookmark key: user profile + program instance (channel + program ID + air date)
- Bookmark updates are fire-and-forget from the client perspective (non-blocking)

---

### US-TSTV-026: TSTV Content in Continue Watching Rail

**As a** viewer
**I want to** see partially watched catch-up programs in my "Continue Watching" rail on the home screen
**So that** I can easily resume catch-up content alongside my VOD and recording content

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** TSTV-FR-032

**Acceptance Criteria:**
- [ ] Given a viewer has partially watched catch-up content, when the home screen loads, then the "Continue Watching" rail includes catch-up items alongside VOD and recordings
- [ ] Given a catch-up item in Continue Watching, when displayed, then it shows: thumbnail, title, channel, progress bar, time remaining, and catch-up expiry date
- [ ] Given items expiring within 24 hours, when displayed, then they are visually highlighted (e.g., "Expires today" badge)
- [ ] Given AI ranking, when items are ordered, then the AI considers: recency of last play, % complete, and catch-up expiry urgency

**AI Component:** Yes -- AI prioritizes Continue Watching items by likelihood of completion, recency, and catch-up expiry as a boosting factor

**Dependencies:** Bookmark Service, Catalog Service, Recommendation Service

**Technical Notes:**
- Continue Watching rail aggregates bookmarks from catch-up, VOD, and Cloud PVR
- Expiry urgency: items expiring soon are boosted in rank to encourage completion

---

### US-TSTV-027: AI Auto-Bookmarking at Chapter Breaks

**As a** viewer
**I want to** navigate long catch-up programs using AI-detected chapter markers
**So that** I can skip to specific sections of documentaries or films without manually scrubbing

**Priority:** P2
**Phase:** 3
**Story Points:** XL
**PRD Reference:** TSTV-FR-033

**Acceptance Criteria:**
- [ ] Given a long-form catch-up program (> 30 minutes), when chapter marks are available, then a chapter navigation overlay is accessible during playback
- [ ] Given chapter marks, when generated, then 5-15 marks per hour of content are created
- [ ] Given chapter accuracy, when measured via user feedback, then 80%+ of marks align with viewer-perceived chapter breaks
- [ ] Given the scene detection model, when processing, then marks are generated during content ingest (batch processing via SageMaker)

**AI Component:** Yes -- PyTorch scene detection model (served via KServe) analyzes content for chapter breaks based on audio silence, visual transitions, and narrative structure

**Dependencies:** AI content enrichment pipeline, SageMaker batch processing, KServe inference

**Technical Notes:**
- Chapter marks stored in Metadata Service alongside program metadata
- Chapter overlay UI: list of chapters with timestamps and optional AI-generated section titles

---

## Epic 6: Non-Functional and Technical Enablers

### US-TSTV-028: TSTV Telemetry and Observability

**As a** developer
**I want to** have comprehensive telemetry for all start-over and catch-up sessions
**So that** we can monitor performance, track success metrics, and detect issues

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** NFR Section 6, Metrics Section 9

**Acceptance Criteria:**
- [ ] Given any TSTV session, when telemetry is captured, then the following are recorded: session type (start-over/catch-up), playback start time, trick-play usage, bookmark events, content rights checks, and errors
- [ ] Given Conviva integration, when reporting, then QoE metrics are available per TSTV session within 30 seconds
- [ ] Given server-side metrics, when reported, then manifest proxy RPS, catch-up catalog size, rights check latency, and bookmark sync accuracy are available in Grafana
- [ ] Given success metrics, when measured, then Start Over adoption rate, catch-up viewing hours, "Your Catch-Up" CTR, and cross-device resume accuracy are trackable in dashboards

**AI Component:** No

**Dependencies:** Conviva SDK, Prometheus + Grafana, Kafka telemetry pipeline

**Technical Notes:**
- Session type tag distinguishes TSTV telemetry from live TV and VOD telemetry
- Key operational metrics: manifest proxy latency, catch-up catalog freshness, rights check cache hit rate

---

### US-TSTV-029: Catch-Up Storage Lifecycle Management

**As an** operator
**I want to** have automated lifecycle management for catch-up storage
**So that** storage costs are optimized while maintaining availability for the full catch-up window

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** NFR Section 6.3

**Acceptance Criteria:**
- [ ] Given S3 lifecycle policy, when configured, then catch-up segments are automatically deleted after the catch-up window expires (7 days from broadcast)
- [ ] Given storage optimization, when S3 Intelligent-Tiering is applied, then content moves from hot to standard tier after 48 hours
- [ ] Given Phase 2, when per-title encoding is active, then catch-up storage is reduced by 20-40% through bitrate optimization
- [ ] Performance: Target storage cost < $0.01 per viewer per month for TSTV storage

**AI Component:** No

**Dependencies:** S3 lifecycle policies, cost monitoring

**Technical Notes:**
- Storage path: `s3://catch-up/{channel_id}/{date}/{program_id}/`
- Consider reducing ABR ladder depth for older catch-up content (drop highest profile after 48 hours) to save storage

---

### US-TSTV-030: Advertising Marker Support for Catch-Up

**As an** operator
**I want to** have ad break markers embedded in catch-up content manifests
**So that** server-side ad insertion (SSAI) can inject targeted ads during catch-up playback

**Priority:** P1
**Phase:** 2
**Story Points:** M
**PRD Reference:** TSTV-FR-024

**Acceptance Criteria:**
- [ ] Given a catch-up manifest, when ad markers exist, then SCTE-35 or equivalent markers are present at ad break positions
- [ ] Given ad policy metadata, when available per program, then it specifies: pre-roll, mid-roll, no-skip, and skippable policies
- [ ] Given the Ad Service (out of scope for this PRD), when SSAI is active, then ad insertion is handled by the Ad Service using the markers in the catch-up manifest

**AI Component:** No

**Dependencies:** Ad Service (separate PRD), SCTE-35 marker passthrough in packaging pipeline

**Technical Notes:**
- SCTE-35 markers from the original live broadcast are preserved in catch-up segments
- Ad policy metadata stored alongside program rights in Rights Engine

---

### US-TSTV-031: Manifest Proxy High Availability

**As a** developer
**I want to** ensure the manifest proxy service is highly available with N+2 redundancy
**So that** Start Over and Catch-Up services remain operational even during infrastructure failures

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** Risk #7 (Manifest proxy SPOF)

**Acceptance Criteria:**
- [ ] Given the manifest proxy, when deployed, then it runs with N+2 redundancy across availability zones
- [ ] Given a proxy instance fails, when the failure is detected, then traffic is automatically routed to healthy instances within 5 seconds
- [ ] Given the proxy design, when implemented, then it is stateless (all state in Redis/EPG) for horizontal scaling
- [ ] Given chaos engineering tests, when proxy failure is simulated, then the service recovers automatically with no user impact

**AI Component:** No

**Dependencies:** Kubernetes deployment, health check configuration, Redis

**Technical Notes:**
- Stateless Go service; all state derived from Redis (program metadata) and EPG Service
- Horizontal pod autoscaler configured for CPU and RPS-based scaling

---

*End of User Stories for PRD-002: Time-Shifted TV (Start Over & Catch-Up)*
*Total: 28 stories (13 core functional, 7 AI enhancement, 4 non-functional, 4 technical/integration)*
