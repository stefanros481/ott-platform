# User Stories: VOD / SVOD (PRD-004)

**Source PRD:** PRD-004-vod-svod.md
**Generated:** 2026-02-08
**Total Stories:** 30

---

## Epic 1: Catalog and Content Management

### US-VOD-001: Hierarchical Content Catalog

**As a** viewer
**I want to** browse a content catalog organized by titles, series (with seasons and episodes), and content types
**So that** I can find and navigate content in a logical, structured way

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** VOD-FR-001

**Acceptance Criteria:**
- [ ] Given the catalog, when browsing, then it supports: movies, series (multi-season), documentaries (standalone or series), kids content, music, and specials
- [ ] Given a series, when viewing its detail page, then seasons and episodes are correctly grouped with accurate episode numbering
- [ ] Given the catalog, when queried, then series grouping is accurate and season/episode ordering is correct across all content types
- [ ] Performance: Catalog serves 5,000+ titles at launch, scaling to 15,000+ by Phase 2

**AI Component:** No

**Dependencies:** Catalog Service (Go, PostgreSQL + Redis + Elasticsearch), Content Ingest Service

**Technical Notes:**
- Hierarchical data model: Title -> Season -> Episode with metadata at each level
- Catalog changes published to Kafka (`catalog.changes` topic) for downstream consumers

---

### US-VOD-002: AI-Enriched Content Metadata

**As a** viewer
**I want to** see rich metadata including mood tags, theme tags, and content descriptions for every title
**So that** I can quickly understand what a title is about and whether it matches my interests

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** VOD-FR-002

**Acceptance Criteria:**
- [ ] Given core metadata fields (title, synopsis, genres, cast, crew, rating, duration, release year), when measured, then 95%+ of titles have all core fields populated
- [ ] Given AI-enriched tags (mood, theme, visual style, content warnings, similarity scores), when measured, then 80%+ of titles have AI tags within 30 days of launch
- [ ] Given localized metadata, when the platform supports multiple languages, then localized versions are available for all supported languages
- [ ] Given AI enrichment, when generating tags, then mood tags (e.g., "dark," "uplifting"), theme tags (e.g., "redemption," "betrayal"), and visual style tags (e.g., "noir," "colorful") are assigned

**AI Component:** Yes -- AI metadata enrichment pipeline generates mood, theme, visual style tags, content warnings, and similarity scores from content analysis

**Dependencies:** Metadata Service, AI content enrichment pipeline (SageMaker)

**Technical Notes:**
- AI enrichment runs as batch processing on content ingest
- Tags stored in Metadata Service (PostgreSQL + Redis) alongside editorial metadata

---

### US-VOD-003: Content Availability Windows

**As an** operator
**I want to** manage per-title, per-territory, per-platform, per-monetization-model availability windows
**So that** content appears and disappears according to licensing agreements

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** VOD-FR-003

**Acceptance Criteria:**
- [ ] Given an availability window with a start date, when the start date arrives, then the title becomes visible and playable within 5 minutes
- [ ] Given an availability window with an end date, when the end date passes, then the title is removed from browse, search, and recommendations within 5 minutes
- [ ] Given territory enforcement, when a title is unavailable in a territory, then it is completely invisible (not shown as locked) to users in that territory
- [ ] Given TVOD-to-SVOD window transitions, when the transition date arrives, then the monetization model updates automatically

**AI Component:** No

**Dependencies:** Catalog Service, Entitlement Service, Rights Engine

**Technical Notes:**
- Territory determined by account region (not IP geo-location)
- Window enforcement via scheduled jobs checking every 5 minutes

---

### US-VOD-004: Content Freshness Badges

**As a** viewer
**I want to** see badges like "New," "Just Added," and "Expiring Soon" on titles
**So that** I can easily identify recent additions and time-sensitive content

**Priority:** P0
**Phase:** 1
**Story Points:** S
**PRD Reference:** VOD-FR-004

**Acceptance Criteria:**
- [ ] Given a title added within the last 14 days, when displayed, then a "New" badge is shown
- [ ] Given a title added within the last 48 hours, when displayed, then a "Just Added" badge is shown
- [ ] Given a title with < 7 days remaining availability, when displayed, then an "Expiring Soon" badge is shown
- [ ] Given badges, when computed, then they are calculated server-side and included in catalog API responses

**AI Component:** No

**Dependencies:** Catalog Service

**Technical Notes:**
- Badge logic configurable per operator
- Badges are mutually prioritized: "Just Added" takes precedence over "New"

---

## Epic 2: Browse and Discovery

### US-VOD-005: Personalized Home Screen with AI Rails

**As a** viewer
**I want to** see a personalized home screen with multiple content rails tailored to my preferences
**So that** I quickly find content I want to watch without extensive browsing

**Priority:** P0
**Phase:** 1
**Story Points:** XL
**PRD Reference:** VOD-FR-010

**Acceptance Criteria:**
- [ ] Given a viewer opens the app, when the home screen loads, then it renders in < 2 seconds with minimum 8 personalized rails
- [ ] Given personalization, when rails are displayed, then they are personalized per profile (not per household) and include: Continue Watching, For You, New Releases, Trending, genre-specific, and editorial collections
- [ ] Given rail ordering, when displayed, then AI determines the most relevant rail order for each profile
- [ ] Given the Recommendation Service is unavailable, when fallback occurs, then rails switch to popularity-based ordering

**AI Component:** Yes -- All rails except Editorial are AI-personalized per profile; rail ordering determined by AI based on predicted engagement

**Dependencies:** Recommendation Service (PRD-007), Catalog Service, BFF

**Technical Notes:**
- BFF pre-composes home screen response (cached in Redis, invalidated on profile switch or hourly)
- Lazy-load rails below the fold for performance; max 50 KB initial payload

---

### US-VOD-006: AI Hero Banner

**As a** viewer
**I want to** see a personalized hero banner at the top of the home screen featuring content selected for me
**So that** I discover high-quality content immediately upon opening the app

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** VOD-FR-011, AI Section 5.4

**Acceptance Criteria:**
- [ ] Given the hero banner, when displayed, then it features a title selected by AI from 5-15 editorial-curated candidates with multi-variant creative
- [ ] Given hero selection, when the viewer opens the app on consecutive sessions (within 24 hours), then a different hero is shown each time
- [ ] Given explanation text, when shown, then "Because you loved [X]" reasons appear for 80%+ of hero impressions
- [ ] Given the AI model is unavailable, when fallback occurs, then the editorial default hero is shown
- [ ] Performance: Hero banner CTR > 25% (vs 8-10% for static editorial); selection latency < 50ms (pre-computed)

**AI Component:** Yes -- Contextual bandit model selects optimal candidate + creative variant per user per session; features include genre preference, recent viewing, time-of-day

**Dependencies:** Recommendation Service (PRD-007), Editorial team (candidate pool), BFF

**Technical Notes:**
- Bandit model: Thompson Sampling; updates belief based on impression -> click conversion
- Session freshness: different hero if user visited < 4 hours ago

---

### US-VOD-007: Category and Genre Browse

**As a** viewer
**I want to** browse content by genre, mood, decade, language, and content type
**So that** I can explore the catalog based on what I am in the mood for

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** VOD-FR-012

**Acceptance Criteria:**
- [ ] Given a viewer selects a category, when results display, then they appear within 500ms
- [ ] Given categories, when listed, then minimum 15 genres, 5 moods, 5 decades, and 10 languages are available
- [ ] Given results within a category, when ordered, then titles are AI-ranked per user (most relevant first)
- [ ] Given filters, when applied within browse, then viewers can filter by: resolution (HD, 4K, HDR), audio (Dolby Atmos), subtitles, duration, age rating

**AI Component:** Yes -- AI-personalized ordering within each category

**Dependencies:** Catalog Service, Recommendation Service

**Technical Notes:**
- Category data pre-computed and cached
- Filters applied in < 500ms; multiple filters composable

---

### US-VOD-008: Text Search with AI-Augmented Ranking

**As a** viewer
**I want to** search for content by title, cast, or keywords and receive relevant results quickly
**So that** I can find specific content efficiently

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** VOD-FR-013

**Acceptance Criteria:**
- [ ] Given a viewer types a search query, when results return, then they appear within 500ms
- [ ] Given auto-suggest, when 3 characters are typed, then title suggestions appear
- [ ] Given search results, when displayed, then each shows: thumbnail, title, year, rating, availability (SVOD/TVOD/AVOD), and match reason
- [ ] Given results include both VOD and catch-up content, when displayed, then each is clearly labeled by source type
- [ ] Given search relevance, when measured, then 80%+ of queries return the intended title in the top 3 results
- [ ] Performance: Search covers title, synopsis, cast, crew, genre, and AI tags; spelling correction via fuzzy matching

**AI Component:** Yes -- User viewing history influences search result ranking (AI-augmented relevance scoring)

**Dependencies:** Search Service (Elasticsearch 8), Recommendation Service

**Technical Notes:**
- Elasticsearch index: title (5x boost), synopsis, cast (3x boost), crew, genres, AI tags
- Results ranked by: text relevance * user preference boost from Recommendation Service

---

### US-VOD-009: Conversational Semantic Search

**As a** viewer
**I want to** search using natural language like "dark sci-fi with a female lead, like Severance but more horror"
**So that** I can find content that matches my mood and preferences without knowing exact titles

**Priority:** P2
**Phase:** 3
**Story Points:** XL
**PRD Reference:** VOD-FR-014

**Acceptance Criteria:**
- [ ] Given a conversational query, when processed, then results return within 1.5 seconds
- [ ] Given intent extraction, when the LLM processes the query, then genre, mood, era, characteristics, and reference titles are correctly extracted with 85%+ accuracy
- [ ] Given semantic results, when displayed, then each includes a match quality indicator and an AI-generated explanation of why it matches
- [ ] Given results, when sourced, then all results come from the actual catalog (no hallucinated titles)
- [ ] Given the LLM is unavailable, when fallback occurs, then the query falls back to keyword search
- [ ] Performance: Search success rate (search -> play within 2 min) > 70% for conversational queries; rate limited to 10 conversational queries per user per hour

**AI Component:** Yes -- Amazon Bedrock (Claude Haiku) for intent extraction + pgvector for semantic similarity; final ranking: keyword (30%) + semantic (40%) + user preference (30%)

**Dependencies:** Amazon Bedrock, pgvector, Search Service, Recommendation Service

**Technical Notes:**
- Response caching for common queries (LRU cache, 1-hour TTL) to manage LLM cost
- Budget target: < $5,000/month for conversational search LLM at Phase 3 scale

---

### US-VOD-010: Voice Search

**As a** viewer
**I want to** search for content using voice on my TV or mobile device
**So that** I can find content hands-free, especially on devices where typing is cumbersome

**Priority:** P1
**Phase:** 2
**Story Points:** L
**PRD Reference:** VOD-FR-015

**Acceptance Criteria:**
- [ ] Given a viewer uses voice search, when speech is recognized, then text is sent to the search backend and results appear within 2 seconds
- [ ] Given speech recognition, when measured, then accuracy is > 90% for title names and > 80% for conversational queries
- [ ] Given voice search, when supported, then it works on Android TV, Apple TV, iOS, and Android

**AI Component:** Yes -- Voice query processed via on-device speech-to-text, then routed to text or conversational search

**Dependencies:** Platform-native speech-to-text APIs, Search Service

**Technical Notes:**
- On-device speech recognition (no server-side transcription needed for Phase 2)
- In Phase 3, voice queries route to conversational semantic search

---

## Epic 3: Content Detail and Interaction

### US-VOD-011: Content Detail Page

**As a** viewer
**I want to** see a comprehensive detail page for any title with metadata, trailer, and actions
**So that** I can make an informed decision about whether to watch

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** VOD-FR-020

**Acceptance Criteria:**
- [ ] Given a viewer selects a title, when the detail page loads, then it appears within 1.5 seconds showing: title, synopsis, cast, crew, genres, rating, duration, release year, trailer, availability, and action buttons (Play, My List, Download)
- [ ] Given a series, when the detail page shows, then a season/episode selector supports 20+ seasons with correct episode ordering
- [ ] Given trailer availability, when shown on TV clients, then the trailer auto-plays (muted) as the detail page background

**AI Component:** No

**Dependencies:** Catalog Service, Metadata Service, BFF

**Technical Notes:**
- Detail page data from Catalog Service via BFF
- Trailer auto-play uses a lightweight preview player (no full session)

---

### US-VOD-012: "More Like This" AI Recommendations on Detail Page

**As a** viewer
**I want to** see a rail of similar content on any title's detail page
**So that** I can discover related content I might enjoy

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** VOD-FR-021

**Acceptance Criteria:**
- [ ] Given a detail page, when the "More Like This" rail loads, then it shows 10+ AI-curated similar titles
- [ ] Given similarity, when computed, then it goes beyond genre to consider: mood, pacing, visual style, thematic overlap, cast overlap, narrative structure
- [ ] Performance: "More Like This" CTR > 15%

**AI Component:** Yes -- Content-based recommendation model using 768-dimension embeddings (sentence-transformers) stored in pgvector; considers deep content similarity

**Dependencies:** Recommendation Service (PRD-007), pgvector

**Technical Notes:**
- Content embeddings computed during ingest and stored in pgvector
- Similarity computed via cosine distance on embedding vectors

---

### US-VOD-013: User Ratings (Thumbs Up / Down)

**As a** viewer
**I want to** rate titles with thumbs up or thumbs down
**So that** the platform learns my preferences and improves its recommendations

**Priority:** P0
**Phase:** 1
**Story Points:** S
**PRD Reference:** VOD-FR-023

**Acceptance Criteria:**
- [ ] Given a viewer rates a title, when the rating is submitted, then it persists per profile and syncs across devices
- [ ] Given a rating, when submitted, then it immediately adjusts recommendation weights for genre, cast, and theme (within the same session)
- [ ] Given a rating change (up to down or vice versa), when submitted, then the change is supported and reflected immediately
- [ ] Given explicit rating signals, when weighted in the model, then they are weighted 3x vs implicit signals

**AI Component:** Yes -- Rating feeds the Recommendation Service as an explicit preference signal

**Dependencies:** Recommendation Service, Profile Service

**Technical Notes:**
- Rating stored per profile, not per household
- Fire-and-forget from client; background sync to Recommendation Service via Kafka

---

### US-VOD-014: Watchlist ("My List")

**As a** viewer
**I want to** add titles to a personal watchlist and see it as a rail on the home screen
**So that** I can save titles for later and quickly access them

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** VOD-FR-024

**Acceptance Criteria:**
- [ ] Given a viewer adds a title to My List, when added, then the action completes in < 500ms
- [ ] Given My List, when synced, then it syncs across all devices within 5 seconds
- [ ] Given My List on the home screen, when displayed, then items are AI-sorted by predicted viewing likelihood (most likely to watch first)
- [ ] Given items on the list for > 90 days without being played, when auto-archival runs, then a notification is sent before the item is archived
- [ ] Given the list, when managed, then maximum 200 items are supported

**AI Component:** Yes -- AI-managed sorting by predicted viewing likelihood; stale auto-archival after 90 days with notification

**Dependencies:** Profile Service (list storage), Recommendation Service (sorting)

**Technical Notes:**
- Watchlist stored per profile
- Stale archival: notification sent before removal; one-tap restore

---

## Epic 4: Playback

### US-VOD-015: VOD Playback with ABR Streaming

**As a** viewer
**I want to** stream VOD content with adaptive bitrate that adjusts to my network conditions
**So that** I have the best possible quality with no interruptions

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** VOD-FR-030

**Acceptance Criteria:**
- [ ] Given a viewer presses play, when the session starts, then playback begins within 2 seconds (p95)
- [ ] Given network degradation, when the ABR algorithm detects it, then quality steps down within 2 seconds without rebuffering
- [ ] Given network recovery, when bandwidth improves, then quality steps up within 5 seconds (conservative)
- [ ] Performance: VMAF > 93 for 1080p HEVC; VMAF > 90 for 1080p H.264; rebuffer ratio < 0.2%; video start failures < 0.3%

**AI Component:** No (standard ABR; ML-enhanced ABR in Phase 3 per PRD-008)

**Dependencies:** CDN delivery, Playback Session Service, BFF, player per platform

**Technical Notes:**
- CMAF packaging with HLS/DASH manifests
- HEVC primary, H.264 fallback; AV1 for premium titles in Phase 3
- VOD segments pre-packaged on S3 with 24-hour CDN cache TTL

---

### US-VOD-016: Full Trick-Play for VOD

**As a** viewer
**I want to** use pause, rewind, fast-forward, and skip controls during VOD playback
**So that** I can control my viewing pace

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** VOD-FR-031

**Acceptance Criteria:**
- [ ] Given trick-play controls, when used, then all commands (pause, rewind, fast-forward, skip) respond in < 300ms
- [ ] Given scrubbing, when thumbnail previews are available, then I-frame thumbnails are shown at 10-second intervals
- [ ] Given skip controls, when configured, then skip forward/backward in 10s or 30s increments (user-configurable)
- [ ] Given the scrubber bar, when chapter markers are available, then visual chapter markers are displayed

**AI Component:** No

**Dependencies:** Player per platform, CDN delivery

**Technical Notes:**
- Same player components used across VOD, catch-up, and recordings
- Trick-play thumbnails generated during encoding pipeline

---

### US-VOD-017: Continue Watching with AI Sorting

**As a** viewer
**I want to** see my in-progress content in a "Continue Watching" rail sorted by likelihood of resumption
**So that** I can quickly resume what I am most likely to watch next

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** VOD-FR-033, AI Section 5.3

**Acceptance Criteria:**
- [ ] Given a viewer has in-progress content, when the Continue Watching rail loads, then items are sorted by AI-predicted resumption likelihood
- [ ] Given the AI sorting, when measured, then the top-ranked item is actually the next-played in 60%+ of sessions
- [ ] Given stale items (not played for 30+ days), when detected, then they are auto-archived to a "Paused" section with a notification
- [ ] Given the rail, when displayed, then a maximum of 20 items are shown; lower-predicted items are suppressed to "Paused"
- [ ] Given bookmarks, when synced, then position accuracy is within 5 seconds across devices; sync latency < 5 seconds

**AI Component:** Yes -- XGBoost model predicts resumption probability based on: recency, completion %, time-of-day affinity, device affinity, series momentum

**Dependencies:** Bookmark Service, Recommendation Service, Profile Service

**Technical Notes:**
- Continue Watching aggregates bookmarks from VOD, catch-up, and Cloud PVR
- "Paused" section accessible with one tap from Continue Watching rail

---

### US-VOD-018: Binge Mode (Auto-Play Next Episode)

**As a** binge watcher
**I want to** have the next episode automatically play with a configurable countdown after the current one ends
**So that** I can binge-watch a series seamlessly

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** VOD-FR-034

**Acceptance Criteria:**
- [ ] Given an episode ends, when the next episode is available, then an auto-play countdown appears (default 15 seconds)
- [ ] Given the countdown, when configured by the user, then options are: 5s, 10s, 15s, 30s, or off
- [ ] Given the viewer has watched consecutive episodes, when the "Still watching?" threshold is reached (default 4 episodes), then a prompt appears
- [ ] Given the "Still watching?" prompt, when displayed, then the viewer must respond to continue (no auto-play past prompt)
- [ ] Performance: Auto-play gap between episodes < 1 second

**AI Component:** No

**Dependencies:** Catalog Service (episode ordering), player per platform

**Technical Notes:**
- "Still watching?" threshold configurable per profile: 2-10 episodes or off
- Countdown duration stored per profile preference

---

### US-VOD-019: Skip Intro and Skip Recap

**As a** binge watcher
**I want to** skip intro sequences and "previously on" recaps with one button press
**So that** I can get straight to new content when binge-watching

**Priority:** P1
**Phase:** 2
**Story Points:** L
**PRD Reference:** VOD-FR-035

**Acceptance Criteria:**
- [ ] Given an episode has AI-detected intro markers, when the intro begins, then a "Skip Intro" button appears within 3 seconds of intro start
- [ ] Given an episode has AI-detected recap markers, when the recap begins, then a "Skip Recap" button appears
- [ ] Given the skip button, when not pressed, then it auto-dismisses after the intro/recap ends
- [ ] Given marker accuracy, when measured, then 90%+ of intro markers and 85%+ of recap markers are correct within 3 seconds of actual boundaries

**AI Component:** Yes -- Scene detection model (audio pattern analysis for theme music + visual pattern analysis for title cards) identifies intro/recap boundaries

**Dependencies:** AI content enrichment pipeline, SageMaker

**Technical Notes:**
- Markers generated during content encoding/ingest pipeline
- Markers stored in Metadata Service alongside content metadata

---

### US-VOD-020: Post-Play Recommendations

**As a** viewer
**I want to** see contextual recommendations when credits begin after finishing a film or episode
**So that** I can easily find my next watch without going back to the home screen

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** VOD-FR-036

**Acceptance Criteria:**
- [ ] Given credits start rolling, when the post-play screen appears, then it renders within 1 second showing 6-8 AI-curated recommendations
- [ ] Given the film is part of a series/franchise, when detected, then the next entry is the primary recommendation
- [ ] Given a rating prompt (thumbs up/down), when displayed, then it is dismissible and does not block navigation
- [ ] Given 30 seconds of inactivity on the post-play screen, when the timer expires, then the screen remains static (no auto-play of a random title)
- [ ] Performance: Post-play recommendation CTR > 20%

**AI Component:** Yes -- Contextual recommendation model considers: just-watched content, time of day, session history, profile preferences

**Dependencies:** Recommendation Service, Catalog Service

**Technical Notes:**
- Credits detection: percentage-based (last 5% of content duration) or marker-based
- Sequel/series detection accuracy must be 99%+

---

### US-VOD-021: Download for Offline Playback (Mobile)

**As a** viewer
**I want to** download VOD content to my phone or tablet for offline watching
**So that** I can watch during flights, commutes, or areas with no connectivity

**Priority:** P1
**Phase:** 2
**Story Points:** XL
**PRD Reference:** VOD-FR-037

**Acceptance Criteria:**
- [ ] Given a title has offline rights, when the Download button is shown on the detail page, then it is available on iOS and Android
- [ ] Given quality selection, when downloading, then options are: Low (360p, ~300 MB), Medium (720p, ~800 MB), High (1080p, ~2 GB)
- [ ] Given offline playback, when playing downloaded content, then full trick-play is available identical to online playback
- [ ] Given the offline DRM license, when issued, then it is valid for 48 hours and auto-renewed when the device connects to the internet
- [ ] Given offline viewing events, when the device reconnects, then play/pause/complete/bookmark data syncs to the platform
- [ ] Given storage management, when configured, then users can set a maximum download storage (default 5 GB); oldest completed downloads auto-removed when limit is reached

**AI Component:** No

**Dependencies:** DRM offline license infrastructure, mobile client download manager

**Technical Notes:**
- Downloaded content: encrypted CMAF segments with offline DRM license
- Downloaded content stored in app-internal storage (not transferable)
- Widevine L3 downloads limited to 720p

---

## Epic 5: Monetization

### US-VOD-022: SVOD Entitlement Check

**As a** viewer
**I want to** play SVOD-included content seamlessly with a clear "Included" indicator
**So that** I know which content is part of my subscription

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** VOD-FR-040

**Acceptance Criteria:**
- [ ] Given an SVOD title, when the entitlement is checked, then verification completes in < 30ms (Redis cache)
- [ ] Given an SVOD title, when displayed, then a clear "Included with your subscription" indicator is shown
- [ ] Given a non-entitled title, when displayed, then the appropriate monetization option is shown (TVOD price or add-on upsell)

**AI Component:** No

**Dependencies:** Entitlement Service (Redis-cached)

**Technical Notes:**
- Entitlement check: `title.packages intersection user.packages != empty`
- Fail-closed: deny playback if entitlement status is ambiguous

---

### US-VOD-023: TVOD Rental and Purchase

**As a** viewer
**I want to** rent or buy individual titles with a clear pricing display and quick purchase flow
**So that** I can access premium and new-release content not included in my subscription

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** VOD-FR-041

**Acceptance Criteria:**
- [ ] Given a TVOD title, when the detail page loads, then it shows: "Rent from $X.XX (48-hour access)" and "Buy from $X.XX (permanent)" with per-quality pricing (SD/HD/4K)
- [ ] Given a purchase flow, when a viewer selects rent or buy, then the flow completes in < 3 clicks (select -> confirm -> play)
- [ ] Given payment processing, when a transaction is submitted, then it completes in < 5 seconds
- [ ] Given a rental, when the 48-hour window starts, then a countdown is visible on the title in the library and during playback
- [ ] Given a rental expires, when the 48-hour window ends, then the title is no longer playable

**AI Component:** No

**Dependencies:** Payment Service (Stripe/Adyen), Entitlement Service

**Technical Notes:**
- Rental expiry: 48 hours from first play, with 30-day maximum from purchase (if never played)
- Purchased titles accessible indefinitely (as long as rights remain valid)

---

### US-VOD-024: Premium Add-On Package Subscription

**As a** viewer
**I want to** subscribe to premium add-on content packages (e.g., HBO, Sports VOD) from within the app
**So that** I can unlock additional content without leaving the platform

**Priority:** P1
**Phase:** 1
**Story Points:** M
**PRD Reference:** VOD-FR-042

**Acceptance Criteria:**
- [ ] Given add-on packages are available, when the user browses non-entitled content, then the required add-on is clearly labeled (e.g., "Part of HBO Pack")
- [ ] Given a viewer subscribes to an add-on, when the subscription is confirmed, then content is immediately accessible
- [ ] Given add-on management, when the user views their subscriptions, then active add-ons are visible with pricing and cancel options

**AI Component:** No

**Dependencies:** Subscription Service, Entitlement Service, Payment Service

**Technical Notes:**
- In-app subscription flow for add-ons
- Add-on entitlements propagate immediately to the Entitlement Service

---

### US-VOD-025: Paywall UX with Clear Upgrade Path

**As a** viewer
**I want to** see clear messaging and a direct upgrade path when I encounter non-entitled content
**So that** I am never stuck at a dead end and can easily access any content I want

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** VOD-FR-044

**Acceptance Criteria:**
- [ ] Given a non-entitled title, when the viewer reaches a paywall, then a clear, non-technical message explains how to access: "Subscribe to Premium," "Rent from $X.XX," or "Add HBO Pack"
- [ ] Given a CTA button, when pressed, then it links directly to the upgrade/purchase flow (no dead ends)
- [ ] Given TVOD titles, when configured per operator, then a preview (trailer or first 5 minutes) may be available before purchase

**AI Component:** Yes (Phase 3) -- AI selects the most persuasive upgrade prompt per user based on engagement patterns

**Dependencies:** Entitlement Service, Subscription Service, Payment Service

**Technical Notes:**
- Paywall rendering handled by BFF based on entitlement check result
- Phase 3: AI-optimized messaging (e.g., "This package includes 8 titles you've shown interest in")

---

## Epic 6: AI-Powered Discovery

### US-VOD-026: Hybrid Recommendation Engine

**As a** viewer
**I want to** receive personalized content recommendations across all surfaces of the platform
**So that** I discover content I enjoy without spending excessive time browsing

**Priority:** P0
**Phase:** 1
**Story Points:** XL
**PRD Reference:** AI Section 5.1

**Acceptance Criteria:**
- [ ] Given the recommendation engine, when serving any personalized surface, then recommendation latency is < 100ms (p95)
- [ ] Given A/B testing, when personalized vs non-personalized, then browse-to-play rate increases by +20%
- [ ] Given recommendation CTR, when measured per surface, then: home rail > 15%, detail "More Like This" > 15%, post-play > 20%
- [ ] Given diversity injection, when applied, then 20%+ of items per rail are "exploration" items spanning at least 3 genres
- [ ] Given model retraining, when scheduled, then collaborative model retrains every 6 hours, content-based daily, ensemble weekly
- [ ] Given a user rates a title, when the rating is processed, then the next recommendation served in the same session reflects the rating

**AI Component:** Yes -- Hybrid ensemble: collaborative filtering (TensorFlow two-tower), content-based (PyTorch embeddings in pgvector), contextual signals (time/device/session), trending/popularity (Flink), with XGBoost final ranker

**Dependencies:** KServe inference cluster, Feature Store (Feast), pgvector, Flink

**Technical Notes:**
- 12+ recommendation surfaces across the platform
- Cold-start: onboarding quiz seeds collaborative model; content-based fills gaps
- Diversity parameters configurable per operator

---

### US-VOD-027: Personalized Thumbnails

**As a** viewer
**I want to** see thumbnail images for titles that are selected based on my visual preferences
**So that** the content I see feels more relevant and appealing to me

**Priority:** P1
**Phase:** 2
**Story Points:** L
**PRD Reference:** AI Section 5.2

**Acceptance Criteria:**
- [ ] Given a title, when displayed, then the thumbnail shown is selected from 5-10 variants based on the viewer's demonstrated visual preferences
- [ ] Given A/B testing, when personalized vs static thumbnails are compared, then CTR increases by 12%
- [ ] Given the multi-armed bandit model, when learning, then optimal variant per user segment is identified within 1,000 impressions
- [ ] Given variant selection, when served, then selection adds < 5ms latency (part of recommendation serving)
- [ ] Given fallback, when the model is unavailable, then the editorial default thumbnail is shown

**AI Component:** Yes -- Multi-armed bandit model (Thompson Sampling) learns optimal thumbnail variant per user segment; ResNet-50 quality scoring model evaluates candidates

**Dependencies:** Recommendation Service, content encoding pipeline (thumbnail extraction), KServe

**Technical Notes:**
- Thumbnail variants: editorial (manual) + AI-extracted (scene-change detection + quality scoring)
- Bandit model updates every 5 minutes via Flink streaming job

---

### US-VOD-028: "What's New & Worth It" Weekly Digest

**As a** viewer
**I want to** receive a personalized weekly notification highlighting new content worth watching
**So that** I stay informed about platform additions without manually browsing

**Priority:** P1
**Phase:** 2
**Story Points:** M
**PRD Reference:** Scenario 5

**Acceptance Criteria:**
- [ ] Given the weekly digest, when delivered, then it arrives on a configurable day and time (default: Saturday 09:00)
- [ ] Given digest content, when curated, then it includes 5 titles: 1 from a frequent genre, 1 from an occasional genre, 1 trending, 1 "stretch" (outside usual preferences), and 1 series episode
- [ ] Given engagement, when measured, then digest open rate > 30% and play rate > 15%
- [ ] Given diversity, when applied, then at least 3 genres are represented in the 5 titles
- [ ] Given user control, when configured, then users can unsubscribe from the digest

**AI Component:** Yes -- Recommendation Service generates personalized digest per profile with diversity injection and "stretch" recommendation

**Dependencies:** Recommendation Service, Notification Service

**Technical Notes:**
- Digest generated as batch job weekly
- Delivery: push notification (mobile), in-app (all platforms), optional email

---

### US-VOD-029: Co-Viewing Detection and Adaptation

**As a** viewer
**I want to** have the platform detect when multiple household members are watching together and adapt recommendations accordingly
**So that** shared viewing sessions surface content everyone will enjoy

**Priority:** P2
**Phase:** 2
**Story Points:** L
**PRD Reference:** Scenario 8

**Acceptance Criteria:**
- [ ] Given co-viewing signals are detected (profile switches, time-of-day pattern, content deviation), when confidence exceeds 70%, then a "Watching together?" prompt appears
- [ ] Given the viewer confirms Family Mode, when activated, then recommendations shift to content intersecting preferences of all detected profiles
- [ ] Given Family Mode, when content is deprioritized, then titles above the household's co-viewing rating threshold are lower-ranked
- [ ] Given false positives, when measured, then < 10% of prompts appear when only one person is watching
- [ ] Given user control, when configured, then co-viewing prompts can be disabled in settings

**AI Component:** Yes -- Co-viewing detection model uses: time-of-day pattern, content selection deviation, explicit "Watch Together" activation, household profile intersection for recommendations

**Dependencies:** Recommendation Service, Profile Service

**Technical Notes:**
- Primary signals: time-of-day + content deviation; Bluetooth proximity as supplementary on mobile (Phase 3)
- Co-viewing session attributed to a "Family" pseudo-profile for training

---

## Epic 7: Non-Functional and Technical Enablers

### US-VOD-030: Churn-Targeted Content Recommendations

**As an** operator
**I want to** surface high-engagement content to subscribers identified as at-risk of churning
**So that** targeted content discovery helps retain subscribers who might otherwise cancel

**Priority:** P2
**Phase:** 2
**Story Points:** L
**PRD Reference:** VOD-FR-045

**Acceptance Criteria:**
- [ ] Given the churn prediction model, when identifying at-risk users, then 70%+ of users who churn within 30 days were flagged
- [ ] Given at-risk users, when served recommendations, then the strategy emphasizes high-engagement titles matching their preferences
- [ ] Given the retention strategy, when implemented, then it is subtle (no "We see you're leaving" messaging); instead, enhanced "We think you'll love this" rails
- [ ] Performance: Measure churn rate delta for flagged users who engage with retention rails vs those who do not

**AI Component:** Yes -- Churn prediction model (XGBoost) feeds risk score to Recommendation Service; at-risk users receive modified recommendation strategy

**Dependencies:** Recommendation Service, churn prediction model (PRD-008), Feature Store

**Technical Notes:**
- Churn signals: declining engagement, support contacts, payment failures, viewing pattern changes
- Retention rails visually indistinguishable from normal recommendations

---

### US-VOD-031: VOD Telemetry and Observability

**As a** developer
**I want to** have comprehensive telemetry for VOD browse, search, playback, and AI features
**So that** we can monitor performance, measure success metrics, and debug issues

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** NFR Section 6, Metrics Section 9

**Acceptance Criteria:**
- [ ] Given VOD sessions, when telemetry is captured, then events are recorded for: browse actions, search queries, play starts, playback quality, trick-play usage, bookmarks, ratings, watchlist changes, and errors
- [ ] Given Conviva integration, when reporting, then QoE metrics are available per VOD session
- [ ] Given AI metrics, when tracked, then recommendation CTR per surface, browse-to-play rate, mean time to play, search success rate, and Continue Watching resumption rate are tracked in dashboards
- [ ] Performance: Telemetry adds < 1% overhead to client resource usage

**AI Component:** No

**Dependencies:** Conviva SDK, Prometheus + Grafana, Kafka telemetry pipeline

**Technical Notes:**
- Key VOD-specific metrics: browse-to-play rate, mean time to play, hero banner CTR, recommendation CTR
- A/B test framework integration for recommendation experiments

---

### US-VOD-032: New User Onboarding Taste Quiz

**As a** new viewer
**I want to** answer a brief taste preference quiz when I first open the app
**So that** the platform can immediately personalize my experience without a cold-start period

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** AI Section 5.1 (Cold-Start Handling)

**Acceptance Criteria:**
- [ ] Given a new user opens the app for the first time, when onboarding begins, then a taste quiz of 3-5 questions is presented (genre preferences, sample titles)
- [ ] Given the quiz is completed, when the home screen loads, then recommendations are meaningfully personalized (non-random) within 10 seconds
- [ ] Given the quiz, when optional, then it can be skipped (recommendations fall back to popularity-based until sufficient viewing data is collected)
- [ ] Given quiz data, when processed, then it seeds the collaborative filtering model and is supplemented by content-based recommendations

**AI Component:** Yes -- Quiz responses seed the collaborative filtering model; content-based and popularity signals fill remaining gaps

**Dependencies:** Recommendation Service, Profile Service

**Technical Notes:**
- Quiz data stored per profile as initial preference signals
- After 10 viewing sessions, collaborative filtering begins to dominate over quiz-based preferences

---

### US-VOD-033: AVOD Tier with Ad Support

**As a** viewer
**I want to** access ad-supported content at a reduced price or for free
**So that** I can watch content without a full subscription commitment

**Priority:** P1
**Phase:** 2
**Story Points:** L
**PRD Reference:** VOD-FR-043

**Acceptance Criteria:**
- [ ] Given AVOD content, when played, then ads are inserted via SSAI at designated break markers
- [ ] Given AVOD content, when displayed in the catalog, then it is clearly labeled ("Free with ads")
- [ ] Given AVOD manifests, when ad markers are present, then SCTE-35 markers are embedded for the Ad Service
- [ ] Given ad frequency, when configured per operator/content, then ad placement and frequency follow operator configuration

**AI Component:** No (ad targeting handled by Ad Service)

**Dependencies:** Ad Service (SSAI), Catalog Service, Entitlement Service

**Technical Notes:**
- AVOD entitlement: separate tier (free or reduced-price)
- SSAI intercepts manifest requests for AVOD sessions and stitches ad segments

---

### US-VOD-034: Multi-Audio and Subtitle Selection for VOD

**As a** viewer
**I want to** select audio language and subtitle language during VOD playback
**So that** I can watch content in my preferred language or with accessibility features

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** VOD-FR-032

**Acceptance Criteria:**
- [ ] Given a VOD title with multiple audio tracks, when the audio menu is opened, then all available tracks (original, dubbed, audio description) are listed with human-readable labels
- [ ] Given a viewer switches audio or subtitle tracks, when the switch occurs, then changes apply in < 500ms without playback interruption
- [ ] Given a viewer's language preference is stored per profile, when tuning to a new title, then the preferred language is auto-selected if available
- [ ] Given audio description tracks, when available, then they are clearly labeled "AD"

**AI Component:** No

**Dependencies:** Content packaging (multi-audio/subtitle CMAF), player per platform

**Technical Notes:**
- Language preference persistence: same as Live TV (PRD-001 LTV-FR-043)
- Subtitle customization (size, color, background) per platform accessibility settings

---

*End of User Stories for PRD-004: VOD / SVOD*
*Total: 30 stories (14 core functional, 8 AI enhancement, 4 non-functional, 4 technical/integration)*
