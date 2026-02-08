# PRD-004: VOD / SVOD (Video on Demand)
## AI-Native OTT Streaming Platform

**Document ID:** PRD-004
**Version:** 1.0
**Date:** 2026-02-08
**Status:** Draft
**Author:** PRD Writer A
**References:** VIS-001 (Project Vision & Design), ARCH-001 (Platform Architecture), PRD-001 (Live TV), PRD-007 (AI UX)
**Stakeholders:** Product Management, Engineering (Platform, Client, AI/ML), Content Acquisition, Monetization, SRE

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

The VOD/SVOD service is the on-demand content platform delivering a catalog of movies, series, documentaries, kids content, and specialty programming to subscribers. Unlike live TV (where the schedule dictates what airs when), VOD puts the viewer in control: they browse, search, or receive AI recommendations, then play content at their convenience with full trick-play control.

The service supports multiple monetization models on the same catalog:
- **SVOD (Subscription VOD)**: Content included with the subscriber's base package or premium add-ons. The primary model.
- **TVOD (Transactional VOD)**: Rent or buy individual titles (typically new releases, premium films). Pay-per-title, with rental windows (48 hours) and permanent ownership.
- **AVOD (Ad-Supported VOD)**: Free or reduced-price tier with server-side ad insertion. Phase 2 launch.
- **Premium Add-Ons**: Additional content packages purchasable as subscription add-ons (e.g., HBO pack, Sports VOD pack, Kids Premium). Hybrid SVOD model.

The VOD catalog is the primary canvas for the platform's AI capabilities. Every surface -- from the home screen hero banner to the detail page "More Like This" rail, from search results to post-play suggestions, from notifications to weekly digests -- is AI-personalized. VOD browsing generates the richest engagement signals (browse, search, play, pause, complete, abandon, rate, add-to-list) that feed the platform's recommendation and personalization engines.

### Business Context

VOD/SVOD is the platform's primary revenue engine and the foundation of subscriber value:

1. **Content investment vehicle**: VOD is where content acquisition investment materializes as subscriber value. The catalog size, quality, and freshness directly correlate with subscriber satisfaction and retention.
2. **ARPU driver**: TVOD transactions and premium add-on upsells increase average revenue per user beyond the base subscription price. AI-driven discovery directly impacts TVOD conversion.
3. **Engagement anchor**: VOD sessions are longer on average (42 minutes per session) than live TV sessions (28 minutes), and engaged viewers churn less. Every 10% increase in weekly VOD viewing hours correlates with a 5% reduction in monthly churn (industry benchmark).
4. **AI showcase**: VOD is where AI personalization has the most visible impact. The difference between a generic home screen and a personalized one is the difference between 15 minutes of browsing and 3 minutes to play. This is the surface that justifies the "AI-native" positioning.

### Scope

**In Scope:**
- Content catalog management (hierarchical: titles, seasons, episodes)
- Content metadata management (editorial + AI-enriched)
- Browse experience (home screen, category, genre, editorial collections, AI-curated rails)
- Search (text, voice, conversational/semantic)
- Content detail pages (metadata, trailers, related content, reviews/ratings)
- Playback (ABR streaming, trick-play, multi-audio, subtitles, binge mode)
- Continue Watching (AI-managed)
- Watchlist/My List
- Monetization integration (SVOD entitlement, TVOD purchase/rental, AVOD ad markers)
- Download for offline playback (mobile only, where rights permit)
- AI-powered discovery (recommendations, personalized thumbnails, hero banner, conversational search)
- Content availability windows (per-territory, per-platform, per-monetization model)

**Out of Scope:**
- Content acquisition strategy and licensing negotiations (business function)
- Content encoding/transcoding pipeline (covered in ARCH-001)
- Ad insertion mechanics and ad targeting (Ad Service PRD)
- Live-to-VOD clipping and publishing (content operations)
- User-generated content (not part of initial platform)
- Interactive content (choose-your-own-adventure, Phase 4+ consideration)

---

## 2. Goals & Non-Goals

### Goals

1. **Launch with a catalog of 5,000+ titles** (movies, series, documentaries, kids) with complete metadata (title, synopsis, cast, crew, genres, ratings, duration, AI-enriched tags), growing to 15,000+ by Phase 2.
2. **Reduce mean time to play from 10.5 minutes (industry average) to 6 minutes at launch and 3.5 minutes at 18 months**, primarily through AI-powered discovery that surfaces the right content quickly.
3. **Achieve 55% browse-to-play rate at launch (vs 45% industry baseline)** through personalized home screens, AI hero banners, and smart continue watching.
4. **Support SVOD, TVOD, and AVOD monetization models** on a unified catalog with per-title, per-territory entitlement management.
5. **Deliver AI-personalized discovery** across 10+ surfaces: home screen rails, hero banner, detail page "more like this," post-play suggestions, search results, notifications, weekly digest, EPG cross-promotion, in-player recommendations, and catch-up/PVR cross-references.
6. **Enable conversational search** (Phase 3) allowing viewers to express intent in natural language ("something like Severance but more horror") with semantic understanding.
7. **Provide seamless cross-device continue watching** with bookmark accuracy within 5 seconds, AI-prioritized ordering, and automatic archival of stale entries.
8. **Support download for offline playback** on mobile devices (iOS, Android) with DRM-protected downloads and configurable quality selection.

### Non-Goals

1. **Competing with Netflix on catalog size**: The platform differentiates on AI-powered discovery, not catalog volume. Quality of curation matters more than quantity of titles.
2. **Live content in VOD**: VOD is strictly on-demand. Live content is handled by PRD-001 and PRD-002. Live-to-VOD conversion is a content operations workflow.
3. **Social features**: Reviews, ratings by friends, watch parties, and social sharing are Phase 3+ features not covered here.
4. **Content creation tools**: The platform does not provide tools for content creators (editing, uploading). Content enters through the ingest pipeline.
5. **Physical media (DVD/Blu-ray) integration**: Digital-only platform.

---

## 3. User Scenarios

### Scenario 1: Personalized Home Screen Experience

**Persona:** Maria (Busy Professional)
**Context:** Maria opens the app on her Smart TV on Friday evening at 20:00. She wants to find something to watch.

**Flow:**
1. The home screen loads in < 2 seconds. Every element is personalized for Maria's profile:
   - **Hero Banner**: An AI-selected spotlight on "The Signal" -- a new international thriller that matches Maria's affinity for slow-burn drama and subtitled content. The banner includes a personalized tagline: "Because you loved Dark and enjoyed international thrillers." A "Play" and "My List" button are available.
   - **Continue Watching**: Maria's in-progress content, AI-sorted by likelihood of resumption: "Silo S2E5 (42 min left)" at position 1, "Planet Earth III Ep 2 (38 min left)" at position 2. Stale entries (not watched in 30+ days) are auto-archived to a "Paused" section.
   - **"New for You"**: New catalog additions in Maria's preferred genres, ordered by predicted interest.
   - **"Trending Now"**: Popular content across the platform, with diversity injection (not just the top-3 most-watched).
   - **"Because You Watched Dark"**: A "more like this" rail seeded by Maria's highest-rated recent watch.
   - **"Friday Night Picks"**: Time-of-day and day-of-week contextual rail (longer-form content for Friday evening).
2. Maria selects "The Signal" from the hero banner and presses "Play." Playback starts within 2 seconds.

**Success Criteria:** Home screen loads in < 2 seconds. All rails are personalized per profile. Hero banner CTR > 25% (vs 8% for non-personalized). Continue Watching rail accurately reflects in-progress content sorted by AI-predicted resumption likelihood.

---

### Scenario 2: Conversational Semantic Search (Phase 3)

**Persona:** Priya (Binge Watcher)
**Context:** Priya knows the kind of content she wants but not the specific title. She wants to search by describing what she is in the mood for.

**Flow:**
1. Priya opens search and types: "dark sci-fi with a female lead, something like Severance but more horror."
2. The Search Service processes this via the semantic search pipeline:
   a. The query is sent to Amazon Bedrock (Claude 3.5 Haiku) for intent extraction: genre="sci-fi, horror," mood="dark," character="female protagonist," reference="Severance."
   b. A vector embedding of the query is generated and compared against content embeddings in pgvector.
   c. Results are ranked by: vector similarity (semantic match), user preference alignment, catalog availability.
3. Results appear within 1 second:
   - "Silo" (95% match) -- "A woman investigates the truth of her underground community"
   - "The OA" (88% match) -- "A woman explores alternate dimensions with eerie undertones"
   - "Devs" (85% match) -- "A programmer uncovers a dark tech conspiracy"
   - Each result shows a match quality indicator and a brief AI-generated explanation of why it matches.
4. Priya selects "Silo." The detail page shows full metadata plus an AI-generated "Why this matches" section.

**Success Criteria:** Conversational search returns semantically relevant results within 1 second. Search success rate (search -> play within 2 minutes) > 70% for conversational queries. At least 5 results for well-formed queries. Explanation text accurately reflects the match logic.

---

### Scenario 3: Binge-Watching with Smart Controls

**Persona:** Priya (Binge Watcher)
**Context:** Priya is binge-watching a series on a Saturday afternoon. She is on Episode 3 of Season 2.

**Flow:**
1. Episode 3 ends. An auto-play countdown appears: "Episode 4 starts in 15 seconds." (Countdown duration is user-configurable: 5s, 10s, 15s, 30s, off.)
2. Episode 4 begins. AI-detected "skip intro" marker triggers a "Skip Intro" button overlaying the title sequence (fades after the intro ends if not pressed).
3. If Episode 4 has a "previously on" recap, a "Skip Recap" button appears.
4. After Episode 4, the auto-play countdown appears for Episode 5.
5. At the end of Episode 5 (3 episodes in a row, approximately 3 hours), a gentle "Still watching?" prompt appears: "You've been watching for 3 hours. Continue?" This is configurable (can be disabled, or set to trigger after 2/3/4/5 consecutive episodes).
6. Priya selects "Continue." Episode 6 plays.
7. At the end of Season 2, a "Season Complete" screen shows:
   - "Season 3 available -- Start Episode 1?"
   - Or, if Season 3 is not yet available: "Season 3 premieres March 15. Set a reminder?" and "You might also like: [recommendations]."

**Success Criteria:** Auto-play between episodes activates with < 1 second gap. Skip intro accuracy: 90%+ (button appears within 3 seconds of intro start, disappears at intro end). Skip recap accuracy: 85%+. "Still watching" prompt is configurable and defaults to 4 consecutive episodes. Season transition is seamless.

---

### Scenario 4: TVOD Rental and Purchase

**Persona:** David (Okafor Family)
**Context:** David wants to watch a recently released film that is not included in his SVOD subscription but is available as a TVOD rental.

**Flow:**
1. David searches for "Dune: Part Three." The search result shows the title with a price indicator: "Rent from $4.99 | Buy from $14.99."
2. He selects the title. The detail page shows:
   - Full metadata (synopsis, cast, director, duration, ratings, trailer)
   - Monetization options: "Rent: $4.99 (48-hour access, SD/HD/4K pricing tiers)" and "Buy: $14.99 (permanent access)"
   - "Included with Premium Film Pack" -- an upsell prompt if David does not have this add-on
3. David selects "Rent in 4K ($6.99)." A purchase confirmation dialog appears with his payment method on file (last 4 digits).
4. He confirms. The transaction is processed (via Stripe/Adyen integration). Playback is immediately available.
5. A "48 hours remaining" countdown is visible on the title in his library and on the player.
6. If David does not finish the film, his bookmark is saved. He can resume within the 48-hour rental window.
7. After 48 hours, the rental expires. The title is no longer playable. If David wants to watch again, he must rent again or buy.

**Success Criteria:** TVOD purchase flow completes in < 3 clicks (select -> confirm -> play). Payment processing: < 5 seconds. Rental countdown accurate to the minute. Rental content playable immediately after purchase. Clear pricing and rental terms displayed before purchase.

---

### Scenario 5: Content Discovery via AI "What's New & Worth It" Digest

**Persona:** Maria (Busy Professional)
**Context:** Maria receives a weekly personalized digest notification on Saturday morning highlighting new content added to the platform that week.

**Flow:**
1. Saturday at 09:00, Maria receives a push notification (mobile) and in-app notification (all devices): "Your weekly picks are ready: 5 new titles worth watching."
2. She opens the digest. It shows 5 AI-curated titles:
   - 1 title from a genre she frequently watches (international thriller)
   - 1 title from a genre she occasionally explores (documentary)
   - 1 trending title across the platform (popular regardless of her preferences -- diversity injection)
   - 1 title from a genre she rarely watches but might enjoy (comedy -- "stretch" recommendation with explanation)
   - 1 new episode of a series she follows
3. Each title includes: personalized thumbnail, title, one-sentence AI-generated description, match score, "Play" and "My List" buttons.
4. Maria adds one title to her list and plays another directly from the digest.

**Success Criteria:** Weekly digest delivered on Saturday 09:00 (user-configurable time and day). Digest engagement: > 30% open rate, > 15% play rate. Diversity: at least 3 genres represented. "Stretch" recommendation included (one title outside usual preferences). Users can unsubscribe from the digest.

---

### Scenario 6: Personalized Thumbnails

**Persona:** System scenario (all viewers)
**Context:** The platform selects different thumbnail images for the same title depending on the viewer's preferences, maximizing the likelihood of a click.

**Flow:**
1. The content "Stranger Things" has 5 thumbnail variants in the system: (a) action scene, (b) group of kids, (c) the Upside Down, (d) Eleven close-up, (e) 80s nostalgia aesthetic.
2. For Priya (sci-fi, horror fan), the AI selects variant (c) -- the Upside Down -- because her viewing history signals a preference for dark, atmospheric visuals.
3. For the Okafor Family (Amara's profile, who watches family-friendly content), the AI selects variant (b) -- the group of kids -- because her profile responds to ensemble casts and lighter imagery.
4. For Thomas (casual viewer), the AI selects variant (e) -- the 80s nostalgia aesthetic -- because his viewing history shows a preference for classic and retro content.
5. Thumbnail selection is determined at recommendation serving time by the Recommendation Service, using a multi-armed bandit model that learns from impression -> click conversion per user segment per thumbnail variant.

**Success Criteria:** Personalized thumbnails increase title CTR by 12% vs static thumbnails (A/B test). 5-10 thumbnail variants per title (editorial or AI-extracted). Multi-armed bandit model converges to optimal variant per user segment within 1,000 impressions. Fallback to editorial default thumbnail if model is unavailable.

---

### Scenario 7: Download for Offline Playback (Mobile)

**Persona:** Maria (Busy Professional)
**Context:** Maria is about to take a 4-hour flight. She wants to download a film and two series episodes to watch offline.

**Flow:**
1. Maria opens the app on her iPhone and navigates to "Dune: Part Two" (SVOD-included, offline rights granted).
2. A "Download" button is visible on the detail page. She taps it.
3. Quality selection: "Low (360p, ~300 MB)", "Medium (720p, ~800 MB)", "High (1080p, ~2 GB)." She selects "Medium."
4. The download begins. Progress is visible in a "Downloads" section. Estimated time: 4 minutes on WiFi.
5. She downloads two episodes of "Silo" (also Medium quality).
6. On the plane (offline), Maria opens the app. The "Downloads" section shows her 3 downloaded items. She plays "Dune: Part Two." Full trick-play is available.
7. The offline DRM license is valid for 48 hours from download. A "License expires in 46 hours" indicator is subtle but visible.
8. When Maria's phone reconnects to the internet, the viewing event (play, pause, complete, bookmark) is synced to the platform. Her "Continue Watching" is updated across all devices.

**Success Criteria:** Download initiation: < 2 seconds. Download speed: limited by network bandwidth, not platform (up to 20 Mbps). Offline playback: identical trick-play to online. DRM license: 48 hours, auto-renewed when online. Downloaded content is not transferable (DRM-protected). Storage management: users can set a download storage limit.

---

### Scenario 8: Co-Viewing Detection and Adaptation

**Persona:** The Okafor Family
**Context:** David and Amara sit down together on Friday evening to watch something on the living room TV. The platform detects a co-viewing session.

**Flow:**
1. David's profile is active on the living room TV. He starts browsing.
2. The platform detects co-viewing signals:
   - Multiple profile switch signals within 5 minutes (David logged in, but Amara's phone is also in proximity)
   - Time-of-day pattern: Friday evening is historically a shared viewing session for this household
   - Content selection pattern: David is browsing genres outside his normal profile (looking at drama instead of sports)
3. A subtle prompt appears: "Watching together? Switch to Family mode for recommendations everyone will enjoy." Options: "Family Mode" or "Keep David's Profile."
4. David selects "Family Mode." The home screen transforms:
   - Recommendations shift to content suitable for both David and Amara (intersecting preferences: drama series, high-quality documentaries, light comedy)
   - Content rated above the household's "co-viewing" threshold (configurable, default: age 16+) is deprioritized
   - Hero banner shows a film that both profiles have not seen but that matches their shared interest
5. They select a drama film. During playback, the session is attributed to the "Family" pseudo-profile for recommendation training.

**Success Criteria:** Co-viewing detection confidence threshold: 70% before prompting. False positive rate: < 10% (prompts when only one person is actually watching). Family Mode recommendations incorporate preferences from all detected household profiles. Co-viewing prompt is dismissible and can be disabled in settings.

---

### Scenario 9: Content Availability Windows and Territory Management

**Persona:** System scenario
**Context:** A title "Northern Lights" is available with different entitlements in different territories and different monetization windows.

**Flow:**
1. In Territory A: "Northern Lights" is SVOD-included from January 1.
2. In Territory B: "Northern Lights" is TVOD-only for 30 days (January 1-30), then SVOD from February 1.
3. In Territory C: "Northern Lights" is not available at all (no rights acquired).
4. A viewer in Territory A searches for "Northern Lights" and sees it in their SVOD catalog with a "Play" button.
5. A viewer in Territory B searches on January 15 and sees it with a "Rent from $4.99" button. On February 1, the same viewer sees it with a "Play" button (now SVOD-included).
6. A viewer in Territory C does not see the title in search results, browse, or recommendations. The title is invisible (not just locked).
7. Availability windows are managed in the Catalog Service with per-territory, per-monetization-model, per-platform start and end dates.

**Success Criteria:** Correct entitlement displayed per territory per monetization window with zero leakage (no unauthorized access). Window transitions (TVOD -> SVOD) happen automatically at scheduled time with < 5-minute propagation delay. Titles with no rights in a territory are completely invisible (not shown as locked).

---

### Scenario 10: Post-Play Recommendation

**Persona:** Any viewer
**Context:** A viewer finishes watching a film. The platform presents contextual recommendations.

**Flow:**
1. The film's credits begin rolling. The credits shrink to a partial screen (20% of screen).
2. The remaining 80% shows a post-play recommendation screen:
   - "Because you just watched [Film Name]:"
   - 6-8 recommended titles, AI-curated based on: content similarity to the just-watched film, viewer profile preferences, novelty (titles the viewer has not seen), and diversity (multiple genres represented).
   - If the film is part of a series: "Next: [sequel/next film]" is the primary recommendation.
3. The recommendations include personalized thumbnails and one-line AI-generated descriptions.
4. A "Rate this film" prompt (thumbs up / thumbs down / skip) is available. The rating feeds the recommendation engine immediately.
5. If the viewer does not interact within 30 seconds, the screen remains static (no auto-play of a random title).

**Success Criteria:** Post-play screen renders within 1 second of credits starting. Recommendation CTR on post-play: > 20%. Rating prompt does not impede navigation (dismissible). Sequel/series next-title detection accuracy: 99%+. Auto-play a random title: never (user must choose).

---

## 4. Functional Requirements

### 4.1 Catalog and Content Management

| Req ID | Description | Priority | Phase | AI Enhancement | Acceptance Criteria |
|--------|-------------|----------|-------|---------------|-------------------|
| VOD-FR-001 | Hierarchical content catalog: Titles (movies, specials) and Series (series → seasons → episodes). Each level has its own metadata record. | P0 | 1 | -- | Catalog supports: movies, series (multi-season), documentaries (standalone or series), kids, music, specials. Series grouping accurate. Season/episode numbering correct. |
| VOD-FR-002 | Content metadata per title: title (original + localized), synopsis (short + long), genres (primary + secondary), cast, crew (director, writer, producer), rating (age rating, content advisories), duration, release year, country of origin, language, and availability status. | P0 | 1 | AI-enriched metadata appended: mood tags, theme tags, visual style tags, content warnings, similarity scores | Metadata completeness: 95%+ of titles have all core fields populated. AI-enriched tags available for 80%+ of titles within 30 days of launch. Localized metadata available for all platform-supported languages. |
| VOD-FR-003 | Content availability windows: per-title, per-territory, per-platform, per-monetization model. Start and end dates define when a title is visible and playable. | P0 | 1 | -- | Availability window accuracy: titles appear/disappear within 5 minutes of window open/close. Territory enforcement via account region. Platform enforcement via BFF filtering. Monetization model enforcement via Entitlement Service. |
| VOD-FR-004 | Content freshness indicators: "New" badge for titles added in the last 14 days, "Expiring Soon" badge for titles with < 7 days remaining availability, "Just Added" for < 48 hours | P0 | 1 | -- | Badges are computed server-side and included in catalog API responses. Badge logic is configurable per operator. |
| VOD-FR-005 | Catalog search index: all catalog metadata is indexed in Elasticsearch for full-text search with relevance scoring. Index updates within 5 minutes of catalog change. | P0 | 1 | Semantic search via pgvector (Phase 3) supplements keyword search | Search index covers: title, synopsis, cast, crew, genre, AI tags. Index update latency: < 5 minutes. Search relevance: 80%+ of queries return the intended title in the top 3 results. |
| VOD-FR-006 | Content images: each title has editorial images (poster, landscape, logo) in multiple resolutions for different devices and aspect ratios. AI-generated thumbnail variants (Phase 2) supplement editorial images. | P0 | 1 | AI thumbnail selection per user (Phase 2) | Minimum image set per title: 1 poster (2:3), 1 landscape (16:9), 1 logo (transparent). Images served in multiple resolutions (device-appropriate, determined by BFF). |

### 4.2 Browse and Discovery

| Req ID | Description | Priority | Phase | AI Enhancement | Acceptance Criteria |
|--------|-------------|----------|-------|---------------|-------------------|
| VOD-FR-010 | Personalized home screen with multiple content rails: Continue Watching, For You, New Releases, Trending, Genre-specific, Editorial collections | P0 | 1 | All rails except Editorial are AI-personalized per profile | Home screen loads in < 2 seconds. Minimum 8 rails on home screen. Rails are personalized per profile (not per household). Rail ordering is AI-determined (most relevant rail first). |
| VOD-FR-011 | AI hero banner: top-of-home spotlight featuring one or more titles, personalized per profile per session, with multi-variant creative (different background images, different taglines) | P0 | 1 | Multi-armed bandit model selects hero variant per user session from a pool of 5-10 candidates | Hero banner loads with the home screen (no lazy-load delay). CTR > 20% (vs 8% for non-personalized). Candidate pool curated by editorial + AI (editorial provides 5-10 candidates with creative variants, AI selects per user). |
| VOD-FR-012 | Category browse: viewers can browse by genre, mood, decade, language, content type (movie/series/documentary), and custom editorial collections | P0 | 1 | AI-personalized ordering within each category | Categories display within 500ms of selection. Minimum 15 genres, 5 moods, 5 decades, 10 languages. Results within each category are AI-ranked per user (most relevant titles first). |
| VOD-FR-013 | Text search: keyword search across title, synopsis, cast, crew, and genre. Results include VOD, catch-up, and recording content, clearly labeled by source. | P0 | 1 | AI-augmented relevance scoring (viewing history influences result ranking) | Search results in < 500ms. Auto-suggest after 3 characters. Results show: thumbnail, title, year, rating, availability (SVOD/TVOD/AVOD), match reason. |
| VOD-FR-014 | Conversational semantic search: natural language queries with intent extraction and semantic matching. "Find me a thriller from the 90s with a twist ending." | P2 | 3 | Amazon Bedrock (Claude) for intent extraction + pgvector for semantic similarity | Results in < 1.5 seconds. Intent extraction accuracy: 85%+ (correctly identifies genre, era, characteristics). Semantic results are relevant (70%+ of top-5 results match user intent based on evaluation). Fallback to keyword search if LLM unavailable. |
| VOD-FR-015 | Voice search: speech-to-text conversion on-device, with text query sent to the search backend. Support on Android TV, Apple TV, iOS, Android. | P1 | 2 | Voice query processed as text search (or conversational search in Phase 3) | Speech recognition accuracy: > 90% for title names, > 80% for conversational queries. Response time: < 2 seconds from voice input end to results display. Languages: platform primary language(s). |
| VOD-FR-016 | Filtering within browse results: viewers can filter by: resolution (HD, 4K, HDR), audio format (Dolby Atmos, stereo), subtitle availability, duration range, age rating | P1 | 1 | -- | Filters applied in < 500ms. Multiple filters composable. Filter counts displayed (e.g., "4K (234 titles)"). Filters persist within the browse session. |

### 4.3 Content Detail Page

| Req ID | Description | Priority | Phase | AI Enhancement | Acceptance Criteria |
|--------|-------------|----------|-------|---------------|-------------------|
| VOD-FR-020 | Content detail page: title, synopsis, cast, crew, genres, rating, duration, release year, trailer, availability (SVOD/TVOD/price), "Play," "My List," "Download" (mobile), "Share." For series: season/episode selector. | P0 | 1 | -- | Detail page loads in < 1.5 seconds. All metadata fields populated. Trailer auto-plays (muted) as background on TV clients. Season/episode selector supports 20+ seasons. |
| VOD-FR-021 | "More Like This" rail on detail page: AI-curated similar content based on deep content similarity (not just genre). | P0 | 1 | Content-based recommendation model using embeddings (genre, mood, theme, visual style, cast overlap, narrative structure) | Rail shows 10+ recommendations. Similarity goes beyond genre: considers mood, pacing, visual style, thematic overlap. CTR on "More Like This": > 15%. |
| VOD-FR-022 | Cast/crew deep links: tapping on a cast or crew member shows their filmography (filtered to platform-available titles). | P1 | 2 | AI highlights: "Most popular" and "Recommended for you" within filmography | Filmography loads in < 1 second. Titles sorted by: relevance to user, then by popularity. Only platform-available titles shown. |
| VOD-FR-023 | User rating: thumbs up / thumbs down per title per profile. Rating feeds the recommendation engine as an explicit preference signal. | P0 | 1 | Thumbs up/down immediately adjusts recommendation weights for genre, cast, theme | Rating persists per profile. Rating change (up to down or vice versa) supported. Explicit rating signal weighted 3x vs implicit signals in the recommendation model. |
| VOD-FR-024 | Watchlist ("My List"): users can add titles to a personal watchlist. Watchlist persists per profile, syncs across devices, and surfaces as a home screen rail. | P0 | 1 | AI-managed: watchlist items are AI-sorted by predicted viewing likelihood. Stale items (on list > 90 days, never played) are auto-archived with a notification. | Watchlist add/remove: < 500ms. Max 200 items. Sync: < 5 seconds. Watchlist rail on home screen: AI-sorted (most likely to watch first). Stale archival notification before removal. |

### 4.4 Playback

| Req ID | Description | Priority | Phase | AI Enhancement | Acceptance Criteria |
|--------|-------------|----------|-------|---------------|-------------------|
| VOD-FR-030 | VOD playback with adaptive bitrate streaming (CMAF, HLS/DASH). ABR ladder per ARCH-001 Section 5. HEVC primary, H.264 fallback, AV1 for premium (Phase 3). | P0 | 1 | -- | Playback starts in < 2 seconds (p95). ABR step-down: < 2 seconds from bandwidth drop detection. Step-up: < 5 seconds (conservative). Zero codec mismatch errors. |
| VOD-FR-031 | Full trick-play: pause, rewind (2x, 4x, 8x, 16x, 32x), fast-forward (same speeds), scrub with thumbnail preview, skip forward/backward (10s, 30s configurable). | P0 | 1 | -- | All trick-play commands: < 300ms response. Thumbnail preview at 10-second intervals. Scrubber bar with visual chapter markers (if available). |
| VOD-FR-032 | Multi-audio and multi-subtitle selection: list all available tracks with human-readable language labels. Audio: original, dubbed, audio description. Subtitles: multiple languages + closed captions. | P0 | 1 | -- | Track switch: < 500ms without playback interruption. Default audio/subtitle based on profile language preference. Audio description tracks clearly labeled "AD." |
| VOD-FR-033 | Continue Watching: resume from the last position when returning to a previously started title. Position saved every 30 seconds and on stop/pause events. Cross-device sync within 5 seconds. | P0 | 1 | AI-managed Continue Watching rail: sorted by predicted resumption likelihood (recently watched, partially complete, time-of-day affinity). Stale entries auto-archived after 30 days. | Bookmark accuracy: within 5 seconds. Continue Watching rail on home screen: AI-sorted. Stale archival: items not played in 30 days moved to "Paused" section. Restored by one tap. |
| VOD-FR-034 | Binge mode (auto-play next episode): configurable countdown between episodes (5s, 10s, 15s, 30s, off). "Still watching?" prompt after configurable number of consecutive episodes (default 4). | P0 | 1 | -- | Auto-play gap: < 1 second between episodes. Countdown is configurable per profile. "Still watching?" prompt defaults to 4 episodes, configurable (2-10 or off). Prompt does not auto-exit playback -- viewer must respond or it remains. |
| VOD-FR-035 | Skip Intro / Skip Recap: AI-detected markers enable one-press skip buttons at the start of series episodes. | P1 | 2 | Scene detection model (audio + visual analysis) identifies intro/recap boundaries | Skip Intro button appears within 3 seconds of intro start. Disappears at intro end if not pressed. Marker accuracy: 90%+ within 3 seconds of actual boundary. Skip Recap similarly handled. |
| VOD-FR-036 | Post-play recommendation screen: at credits, display AI-curated next-watch suggestions. For series: next episode as primary recommendation. For movies: similar content. | P0 | 1 | Contextual recommendation model considers: just-watched content, time of day, session history, profile preferences | Screen appears within 1 second of credits. 6-8 recommendations displayed. No auto-play of a random title. Rating prompt included. |
| VOD-FR-037 | Download for offline playback: mobile clients (iOS, Android) can download VOD content with DRM protection. Quality selection: Low (360p), Medium (720p), High (1080p). | P1 | 2 | -- | Download respects content rights (offline rights flag per title). DRM offline license: 48 hours, auto-renewed on connectivity. Storage management: user-configurable limit. Download queue management (pause, cancel, delete). |

### 4.5 Monetization Integration

| Req ID | Description | Priority | Phase | AI Enhancement | Acceptance Criteria |
|--------|-------------|----------|-------|---------------|-------------------|
| VOD-FR-040 | SVOD entitlement: titles included in the user's subscription package are playable without additional payment. Entitlement checked at playback start via Entitlement Service. | P0 | 1 | -- | Entitlement check: < 30ms (Redis cache). Clear "Included with your subscription" indicator on SVOD content. |
| VOD-FR-041 | TVOD rental and purchase: titles available for individual rental (48-hour access) or purchase (permanent). Pricing per territory per quality tier (SD/HD/4K). | P0 | 1 | -- | Purchase flow: < 3 clicks. Payment processing: < 5 seconds (Stripe/Adyen). Rental timer accurate to the minute. Purchased titles accessible indefinitely. |
| VOD-FR-042 | Premium add-on packages: viewers can subscribe to add-on content packages (e.g., HBO, sports VOD) that unlock additional SVOD content. | P1 | 1 | -- | Add-on subscription flow: integrated in-app. Content immediately accessible after subscription. Clear labeling of which content requires which add-on. |
| VOD-FR-043 | AVOD tier (Phase 2): ad-supported free or reduced-price access. Manifests include SSAI ad break markers. Ad frequency and placement configurable per operator/content. | P1 | 2 | -- | AVOD content playable with ads. Ad markers in manifest. SSAI integration point available for Ad Service. Clear labeling of AVOD content ("Free with ads"). |
| VOD-FR-044 | Paywall UX: non-entitled content shows clear messaging about how to access: "Subscribe to Premium" or "Rent from $4.99" or "Add HBO Pack." No dead ends. | P0 | 1 | AI selects the most persuasive upgrade prompt based on user engagement patterns (Phase 3) | Paywall message is clear, non-technical. CTA (call to action) button links directly to upgrade/purchase flow. Preview (trailer or first 5 minutes) available for TVOD titles per operator configuration. |
| VOD-FR-045 | Churn-targeted recommendations (Phase 2): users identified as at-risk by the churn prediction model receive boosted content recommendations featuring high-engagement titles matching their preferences. | P2 | 2 | Churn prediction model (XGBoost) feeds risk score to Recommendation Service; at-risk users receive a modified recommendation strategy emphasizing high-engagement content | At-risk user identification: 70%+ of users who churn in 30 days were flagged. Recommendation modification: subtle (no "We see you're leaving" messaging). Retention-focused content rails: "We think you'll love this" with top-matched titles. |

---

## 5. AI-Specific Features

### 5.1 Hybrid Recommendation Engine

**Description:** The platform's core recommendation engine powers all personalized surfaces across VOD and the broader platform. It combines four recommendation strategies in a hybrid ensemble to maximize discovery effectiveness while avoiding filter bubbles.

**Architecture:**
- **Collaborative filtering (TensorFlow, KServe):** "Users similar to you watched these." A two-tower neural network trained on the user-item interaction matrix (views, completions, ratings). Excels for popular content with rich interaction data.
- **Content-based filtering (PyTorch, KServe):** "Based on the attributes of content you enjoy." Uses content embeddings (768-dimension vectors from sentence-transformers, stored in pgvector) to find similar content based on: genre, mood, theme, visual style, cast, narrative structure. Excels for niche content and cold-start scenarios.
- **Contextual signals:** Time-of-day, day-of-week, device type, session history (what the viewer browsed/played earlier in this session). Modifies the ranking of collaborative + content-based candidates.
- **Trending/popularity:** Platform-wide and per-genre popularity signals computed in real-time from Kafka event streams (Flink). Provides freshness and social proof.
- **Ensemble:** A lightweight ranking model (XGBoost) combines scores from all four strategies with learned weights per recommendation surface per user segment. The ensemble is the final ranker.

**Recommendation Surfaces (10+):**
1. Home screen "For You" rail
2. Home screen hero banner
3. Home screen "Because You Watched [X]" rail
4. Category/genre browse (personalized ordering)
5. Content detail "More Like This"
6. Post-play suggestions
7. Search result ranking boost
8. "What's New & Worth It" weekly digest
9. Smart notifications
10. EPG cross-promotion ("Available on demand" in EPG)
11. Cloud PVR suggestions ("Record this based on your taste")
12. Continue Watching prioritization

**Cold-Start Handling:**
- New users: Onboarding taste quiz (3-5 genre/title preference questions) seeds the collaborative model. Content-based recommendations (popularity + genre affinity) fill the gaps. After 10 viewing sessions, collaborative filtering begins to dominate.
- New content: Content-based recommendations kick in immediately (embeddings computed at ingest). Collaborative signal accumulates as users watch. Editorial boost ensures new content is surfaced.

**Diversity Injection:**
- Every recommendation rail includes at least 20% "exploration" items -- content from genres or themes the user has not explored recently.
- Exploration items are labeled with gentle explanations: "Something different: try this based on users who share your other tastes."
- Diversity parameters are configurable per operator (some may want higher diversity, others more precise personalization).

**Acceptance Criteria:**
- [ ] Recommendation latency: < 100ms (p95) for real-time surfaces (home, detail, post-play)
- [ ] Browse-to-play rate increase: +20% vs non-personalized baseline (A/B test)
- [ ] Recommendation CTR per surface: home rail > 15%, detail "More Like This" > 15%, post-play > 20%
- [ ] Cold-start: new user receives meaningful (non-random) recommendations within 10 seconds of completing onboarding quiz
- [ ] Diversity: 20%+ exploration items per rail, spanning at least 3 genres
- [ ] Model retraining: collaborative model every 6 hours, content-based model daily, ensemble retraining weekly
- [ ] Feedback loop: thumbs up/down rating immediately influences the next recommendation served (within the same session)

### 5.2 Personalized Thumbnails

**Description:** For each title, the platform maintains multiple thumbnail variants. An AI model selects the variant most likely to generate a click for each specific viewer, based on their demonstrated visual preferences.

**Architecture:**
- **Thumbnail generation:** During ingest, the Encoding Pipeline extracts candidate thumbnails at scene-change points. A ResNet-50 quality scoring model (KServe) evaluates each candidate for: visual quality, composition, facial clarity, emotional expression, and representativeness of the content. Top 5-10 candidates are stored as variants alongside editorial thumbnails.
- **Variant selection:** A contextual multi-armed bandit model (Thompson Sampling) learns which thumbnail variant performs best for which user segment. User segments are defined by: primary genre preference, mood preference, and content affinity cluster (derived from the collaborative filtering model).
- **Optimization loop:** Every impression (thumbnail shown on a rail) and every click is logged. The bandit model updates its belief about variant performance per segment in near-real-time (Flink streaming job updates every 5 minutes).
- **Serving:** The BFF requests thumbnail variants from the Recommendation Service as part of the rail API. The service returns the optimal variant URL per title per user.

**Acceptance Criteria:**
- [ ] 5-10 thumbnail variants per title (editorial + AI-extracted)
- [ ] CTR improvement: +12% vs static editorial thumbnail (A/B test over 30 days)
- [ ] Bandit convergence: optimal variant identified per segment within 1,000 impressions
- [ ] Variant selection latency: < 5ms (part of recommendation serving, not a separate call)
- [ ] Fallback: editorial default thumbnail if variant selection is unavailable

### 5.3 Smart Continue Watching

**Description:** The Continue Watching rail is one of the highest-engagement surfaces on the platform. Rather than a simple chronologically-sorted list of in-progress content, the AI manages it to maximize resumption rate and minimize clutter.

**Architecture:**
- **Sorting model:** A lightweight XGBoost model predicts the probability of resumption for each in-progress title, considering:
  - Recency: when was it last played (hours ago)
  - Completion: how much is remaining (titles near completion are boosted)
  - Time-of-day affinity: does the user typically watch this type of content at the current time?
  - Device affinity: is the user on the device they typically use for this content?
  - Series momentum: is the viewer mid-binge (watched multiple episodes recently)?
- **Stale archival:** Titles not played for 30+ days are auto-archived to a "Paused" section (accessible but not cluttering the main rail). A notification is sent before archival: "We moved [title] to Paused since you haven't watched in a while. Tap to restore."
- **Maximum rail size:** 20 items. If more than 20 in-progress titles exist, the lowest-predicted-resumption items are suppressed to "Paused."

**Acceptance Criteria:**
- [ ] Continue Watching items sorted by predicted resumption (highest first)
- [ ] Resumption prediction accuracy: the top-ranked item is actually the next-played in 60%+ of sessions
- [ ] Stale archival: items not played for 30 days archived with notification
- [ ] Rail clutter reduction: -40% items visible vs unsorted chronological list
- [ ] "Paused" section accessible with one tap from the Continue Watching rail
- [ ] Restoration from "Paused" is immediate (one tap, item returns to active rail)

### 5.4 AI Hero Banner Selection

**Description:** The hero banner at the top of the home screen is the highest-value real estate on the platform. An AI model selects the optimal title and creative variant for each viewer per session from a pool of editorial-curated candidates.

**Architecture:**
- **Candidate pool:** Editorial team curates 5-15 hero candidates weekly (new releases, platform exclusives, trending titles, seasonal content). Each candidate has 2-3 creative variants (different background images, different taglines).
- **Selection model:** A contextual bandit (similar to personalized thumbnails but at the hero level) selects the optimal candidate + variant per user per session. Features: user genre preference, recent viewing, session history, time-of-day, day-of-week.
- **Session freshness:** A different hero is shown on each app open (if the user visited < 4 hours ago, the hero changes; if > 4 hours, the same hero may repeat).
- **Tagline personalization:** AI-generated explanation text per user ("Because you loved [X]") appended to editorial taglines.

**Acceptance Criteria:**
- [ ] Hero banner CTR: > 25% (vs 8-10% for static editorial banner)
- [ ] Hero selection latency: < 50ms (pre-computed and cached per user)
- [ ] Session freshness: different hero on consecutive app opens within 24 hours
- [ ] Explanation text ("Because you loved...") present for 80%+ of hero impressions
- [ ] Fallback: editorial default hero if AI model is unavailable

---

## 6. Non-Functional Requirements

### 6.1 Latency

| Requirement | Target | Measurement | Priority |
|-------------|--------|-------------|----------|
| Home screen load (all rails) | < 2 seconds (p95) | Client-side telemetry: app open to all visible rails rendered | P0 |
| VOD playback start | < 2 seconds (p95) | Client-side telemetry: play press to first frame | P0 |
| Search results (text) | < 500ms (p95) | BFF API response + client render | P0 |
| Search results (conversational, Phase 3) | < 1.5 seconds (p95) | BFF API response (includes LLM call) | P1 |
| Content detail page load | < 1.5 seconds (p95) | BFF API response + client render | P0 |
| Recommendation serving per rail | < 100ms (p95) | Recommendation Service API response | P0 |
| Entitlement check | < 30ms (p95) | Entitlement Service (Redis cache) | P0 |
| Bookmark sync (cross-device) | < 5 seconds | Bookmark write + read from another device | P0 |
| TVOD purchase processing | < 5 seconds | Payment API round-trip | P0 |

### 6.2 Availability

| Requirement | Target | Measurement |
|-------------|--------|-------------|
| VOD catalog browse | 99.95% | Synthetic monitoring: browse and detail page success |
| VOD playback | 99.95% | Synthetic monitoring: playback initiation success |
| Search | 99.9% | Synthetic monitoring: search query success |
| Recommendation Service | 99.9% (with fallback to popularity-based) | Service uptime + fallback activation rate |
| Payment processing (TVOD) | 99.9% | TVOD purchase success rate |

### 6.3 Scale

| Requirement | Phase 1 Target | Phase 4 Target | Measurement |
|-------------|---------------|----------------|-------------|
| Catalog size | 5,000+ titles | 15,000+ titles | Catalog item count |
| Concurrent VOD playback sessions | 20,000 | 200,000 | Active playback sessions |
| Search queries per second | 1,000 | 10,000 | Search Service RPS |
| Recommendation requests per second | 3,000 | 30,000 | Recommendation Service RPS |
| Home screen loads per second | 2,000 | 20,000 | BFF API RPS |
| TVOD transactions per day | 5,000 | 50,000 | Payment transaction count |

### 6.4 Quality

| Requirement | Target | Measurement |
|-------------|--------|-------------|
| VOD VMAF (1080p HEVC) | > 93 | Per-title VMAF analysis |
| VOD VMAF (1080p H.264) | > 90 | Per-title VMAF analysis |
| Rebuffer ratio (VOD sessions) | < 0.2% | Client-side telemetry (Conviva) |
| Video start failures | < 0.3% | Playback Session Service error rate |
| Search relevance (intended title in top 3) | > 80% | Search quality evaluation (manual + automated) |
| Recommendation relevance (clicked items watched > 50%) | > 60% | Implicit feedback: play duration / content duration |

---

## 7. Technical Considerations

### 7.1 Catalog Service Architecture

The Catalog Service (Go, PostgreSQL + Redis + Elasticsearch) is the source of truth for all content metadata:

**Write Path:**
- Content ingested via Content Ingest Service (file-based for VOD, PRD-002 for catch-up conversion).
- Metadata entered via CMS (content management system) by editorial team, supplemented by AI enrichment from the Metadata Service.
- Catalog changes published to Kafka (`catalog.changes` topic) for downstream consumers (Search index, Recommendation Service, BFF cache invalidation).

**Read Path (via BFF):**
- BFF requests catalog data from the Catalog Service API (gRPC).
- Hot data (home screen rails, trending, new releases) served from Redis cache (TTL: 5 minutes).
- Search queries routed to Elasticsearch (full-text) or pgvector (semantic, Phase 3).
- Catalog API response includes: metadata, availability windows (pre-filtered by territory + platform), entitlement type (SVOD/TVOD/AVOD), and recommendation metadata (thumbnail variant, match score, explanation).

### 7.2 Search Architecture

**Phase 1 (Keyword Search):**
- Elasticsearch 8 index covering: title (boosted 5x), synopsis, cast (boosted 3x), crew, genres, AI tags.
- Auto-suggest: prefix-based title search with popular completions.
- Spelling correction: fuzzy matching (Levenshtein distance <= 2).
- Results ranked by: text relevance score * user preference boost (from Recommendation Service).

**Phase 3 (Conversational Semantic Search):**
- Natural language queries routed to Amazon Bedrock (Claude 3.5 Haiku) for intent extraction.
- Intent extraction output: structured query (genre, mood, era, characteristics, reference titles).
- Structured query used for: (a) keyword search in Elasticsearch, and (b) vector similarity search in pgvector (query embedding compared against content embeddings).
- Final ranking: weighted combination of keyword relevance (30%), semantic similarity (40%), and user preference (30%).
- LLM cost management: response caching for common queries (LRU cache, 1-hour TTL). Rate limiting per user (10 conversational queries per hour).

### 7.3 Playback Architecture

VOD playback follows the standard platform playback flow:

1. Client requests playback via BFF.
2. BFF calls Entitlement Service (< 30ms, Redis cached) to verify access.
3. BFF calls Playback Session Service to create a session (includes: CDN selection via CDN Routing Service, DRM token issuance via Token Service, CAT token issuance).
4. Playback Session Service returns manifest URL (CDN-specific, DRM-specific) and session token.
5. Client player fetches manifest, acquires DRM license, and begins playback.
6. Client sends playback heartbeats every 30 seconds (position, quality metrics) to Playback Session Service.
7. Heartbeats update Bookmark Service (for resume) and feed Kafka (for analytics, QoE, recommendation signals).

**VOD-Specific Considerations:**
- VOD segments are pre-packaged and stored on S3. Long CDN cache TTL (24 hours) for high cache hit ratio.
- Per-title encoding (Phase 2): ML model determines optimal encoding ladder per title based on content complexity. Saves 20-40% bandwidth.
- AV1 encoding (Phase 3): premium titles encoded in AV1 for devices that support it (further 30-40% bandwidth savings over HEVC at equivalent quality).

### 7.4 Monetization Architecture

**SVOD:**
- Entitlement Service maintains a mapping: `(user_id, subscription_tier) → [list of content_package_ids]`
- Catalog Service tags each title with `[content_package_ids]`
- Entitlement check: `title.packages ∩ user.packages != ∅`

**TVOD:**
- Purchase/rental transactions handled by a Payment Service (Go) integrating with Stripe/Adyen.
- Transaction record: `(user_id, content_id, type: rent|buy, quality: SD|HD|4K, price, timestamp, expiry)`
- Entitlement check for TVOD: existence of a valid (non-expired) transaction record.
- Rental expiry: 48 hours from first play (not from purchase). If never played, rental expires after 30 days.

**AVOD (Phase 2):**
- AVOD entitlement: either a separate "free" tier or a reduced-price tier.
- Manifests for AVOD content include SCTE-35 ad break markers.
- SSAI (Server-Side Ad Insertion) handled by Ad Service, which intercepts manifest requests for AVOD sessions and stitches ad segments into the manifest.

### 7.5 Download Architecture (Mobile Offline)

- Download requests create a background task on the mobile client.
- Content is downloaded as encrypted CMAF segments with an offline DRM license.
- License validity: 48 hours from issuance. License auto-renewed when the device connects to the internet.
- Downloaded content stored in app-internal storage (not accessible to other apps).
- Playback events from offline sessions are buffered locally and flushed to the server when connectivity returns.
- Storage management: users set a maximum download storage (default: 5 GB). Oldest completed downloads are auto-removed when limit is reached and a new download is queued.

---

## 8. Dependencies

### 8.1 Service Dependencies

| Dependency | Service | PRD Reference | Dependency Type | Impact if Unavailable |
|------------|---------|---------------|-----------------|----------------------|
| Content metadata | Catalog Service / Metadata Service | ARCH-001 | Hard | Cannot display titles. VOD is non-functional. |
| Search index | Elasticsearch / Search Service | ARCH-001 | Soft | Text search unavailable. Browse still works. Conversational search unavailable. |
| Entitlements | Entitlement Service | ARCH-001 | Hard | Cannot verify content access. Playback denied. Browse may still show content but play is blocked. |
| AI recommendations | Recommendation Service | PRD-007 | Soft | Home screen rails fall back to popularity-based. Personalized thumbnails fall back to editorial default. Still functional but not personalized. |
| Playback session | Playback Session Service | ARCH-001 | Hard | Cannot create playback sessions. VOD playback is fully unavailable. |
| DRM and CDN tokens | Token Service (CAT) | ARCH-001 | Hard | Cannot authorize playback. VOD unavailable. |
| CDN delivery | Multi-CDN | ARCH-001 | Hard | Segments not deliverable. VOD unavailable. |
| Bookmarks | Bookmark Service | ARCH-001 | Soft | Continue Watching unavailable. Playback works but no resume. |
| Payment processing | Payment Service (Stripe/Adyen) | ARCH-001 | Soft | TVOD purchases unavailable. SVOD playback unaffected. |
| AI model serving | KServe | ARCH-001 | Soft | Personalization degrades to popularity-based. Semantic search falls back to keyword search. |
| EPG cross-promotion | EPG Service | PRD-005 | Soft | "Available on demand" cross-references in EPG not shown. VOD unaffected. |
| User profiles | Profile Service | ARCH-001 | Hard | Cannot load preferences. Falls back to household-level defaults. |

### 8.2 Infrastructure Dependencies

| Dependency | Component | Impact if Unavailable |
|------------|-----------|----------------------|
| PostgreSQL (Catalog DB) | RDS | Catalog reads fall back to Redis/ES cache (stale but functional). If all caches miss: VOD browse unavailable. |
| Redis | ElastiCache | Increased latency on all reads. Entitlement checks slow (fall to PostgreSQL). Still functional but degraded. |
| Elasticsearch | Managed ES | Search unavailable. Browse still works (Catalog Service directly). |
| pgvector | PostgreSQL extension | Semantic search and content-based recommendations unavailable. Collaborative filtering still works. |
| S3 | Media storage | VOD segments unavailable. Total playback outage. |
| Kafka | Event bus | Recommendation signals delayed. Continue Watching updates delayed. Core playback unaffected. |
| Bedrock | Managed LLM | Conversational search unavailable. Falls back to keyword search. |

---

## 9. Success Metrics

| # | Metric | Baseline (Industry) | Phase 1 Target | Phase 2 Target | Phase 4 Target | Measurement Method |
|---|--------|--------------------|--------------|--------------|--------------|--------------------|
| 1 | Browse-to-play rate | 45% | 55% | 62% | 70% | Sessions with play event / total sessions with browse activity |
| 2 | Mean time to play (from app open) | 10.5 minutes | 6 minutes | 4.5 minutes | 3.5 minutes | Client-side telemetry: app open to first play event |
| 3 | VOD playback start time (p95) | 3-5 seconds | < 2 seconds | < 1.5 seconds | < 1.5 seconds | Client-side telemetry (Conviva) |
| 4 | Home screen hero banner CTR | 8-10% | 25% | 28% | 32% | Clicks / impressions on hero banner |
| 5 | Recommendation CTR (all surfaces avg) | 8% | 15% | 18% | 22% | Clicks / impressions on AI recommendation rails |
| 6 | Search success rate (search -> play within 2 min) | 55% | 65% | 72% | 80% | Play events within 2 min of search query / total search sessions |
| 7 | Content discovery NPS | +15 | +30 | +38 | +45 | NPS survey focused on content discovery experience |
| 8 | TVOD conversion rate (SVOD users making TVOD purchase) | 2% | 3% | 4% | 5% | Users with TVOD purchase / total SVOD users per month |
| 9 | Session duration (VOD sessions) | 42 minutes | 48 minutes | 52 minutes | 55 minutes | Average active session duration (play time, not idle) |
| 10 | Continue Watching resumption rate | 55% | 70% | 75% | 80% | % of Continue Watching items that are actually resumed within 7 days |

---

## 10. Open Questions & Risks

### Open Questions

| # | Question | Owner | Impact | Target Resolution |
|---|----------|-------|--------|-------------------|
| 1 | What is the TVOD rental window: 48 hours from purchase or 48 hours from first play? "From first play" is more user-friendly but adds complexity (must track first play event and start expiry timer). | Product Manager | UX, engineering complexity | Phase 1 design. Recommendation: 48 hours from first play, with 30-day maximum from purchase. |
| 2 | Should AVOD content be fully free or require a (lower-priced) subscription? A free tier maximizes reach but complicates the business model. | Business | Revenue model, marketing | Pre-launch business case. Recommendation: reduced-price subscription with ads, not fully free (protects SVOD value). |
| 3 | How many thumbnail variants per title should editorial provide vs AI-extract? Editorial variants are higher quality but costly to produce for 15,000+ titles. | Content Ops / AI | Thumbnail quality, production cost | Phase 2 planning. Start with AI-extracted for bulk catalog, editorial for top 500 titles. |
| 4 | Should conversational search support multi-turn dialogue ("That one but with more action") or single-query only? Multi-turn significantly increases LLM cost and complexity. | Product / AI | LLM cost, UX quality | Phase 3 design. Start with single-query. Evaluate multi-turn based on user demand and cost. |
| 5 | What is the download quality strategy: should users choose quality, or should it auto-select based on available storage and network? | Product Manager | UX simplicity vs user control | Phase 2 design. Recommendation: default to "Auto" (AI selects based on storage and content type) with manual override. |
| 6 | Should the platform support 4K HDR downloads? File sizes (5-10 GB per film) create storage management challenges on mobile. | Product / Engineering | Storage, download time | Phase 3. Start with maximum 1080p downloads. Evaluate 4K based on device capability and user demand. |
| 7 | How should co-viewing detection work on devices without proximity sensors or multi-user signal? | AI/ML Lead | Feature availability | Phase 2 design. Primary signals: time-of-day pattern, content selection deviation, explicit "Watch Together" activation. Proximity (Bluetooth) as supplementary on mobile. |

### Risks

| # | Risk | Severity | Likelihood | Mitigation |
|---|------|----------|------------|------------|
| 1 | **AI recommendation filter bubble**: over-personalization causes viewers to see only content matching their established preferences, reducing catalog utilization and viewer satisfaction over time. | High | High | 20% diversity injection in all recommendation rails. Monthly bias audits. "Explore" section with editorial-curated diverse content. Explicit user control: "I want more variety" toggle in settings. Track catalog coverage metric (% of catalog surfaced to each user per month). |
| 2 | **Conversational search accuracy**: LLM misinterprets user intent, returns irrelevant results, or hallucinates titles that do not exist in the catalog. | Medium | Medium | Constrain LLM to intent extraction only (structured output), not freeform generation. Results always sourced from the real catalog index (no hallucinated titles). Fallback to keyword search if LLM confidence is low. Track search-to-play conversion as quality metric. |
| 3 | **TVOD payment fraud**: stolen payment methods used for TVOD purchases. | Medium | Medium | Standard payment fraud prevention (Stripe Radar, 3D Secure). Transaction velocity limits per account. Manual review for high-value transactions. Chargeback monitoring. |
| 4 | **Catalog metadata quality**: poor or inconsistent metadata from content providers undermines search and recommendation quality. | High | High | AI metadata enrichment fills gaps (80%+ coverage target). Automated quality scoring for metadata completeness. Content provider SLAs for metadata quality. Manual enrichment for top 500 titles. |
| 5 | **Content availability window errors**: titles becoming available early or remaining available after rights expire is a contractual violation. | High | Medium | Automated window enforcement in Catalog Service (scheduled jobs check windows every 5 minutes). Alerting when a window change fails. Rights audit trail. Pre-launch validation: all windows verified against content provider contracts. |
| 6 | **Download piracy**: downloaded content is extracted from the DRM container and redistributed. | Medium | Medium | Widevine L1 / FairPlay hardware-level DRM prevents extraction on compliant devices. L3 (software) downloads limited to 720p. Forensic watermarking for premium TVOD content. Monitor piracy channels for platform content. |
| 7 | **Home screen load time degradation**: as more personalization features are added, the home screen API response grows, risking > 2 second load times. | Medium | Medium | BFF pre-composes home screen responses (cached in Redis, invalidated on profile switch or hourly). Lazy-load rails below the fold. Parallel API calls from BFF to backend services. Performance budget: 50 KB max payload for initial home screen load. |
| 8 | **LLM cost for conversational search**: at scale (10K+ conversational queries per day), Bedrock LLM costs may be significant. | Medium | Medium | Use Claude 3.5 Haiku (cheapest, fastest) for intent extraction. Implement response caching for common queries. Rate limit per user (10 conversational queries per hour). Track cost per query and total monthly spend. Budget: < $5,000/month for conversational search LLM at Phase 3 scale. |

---

*This PRD defines the VOD/SVOD service for the AI-native OTT streaming platform. It should be read alongside ARCH-001 (Platform Architecture) for technical implementation details, PRD-007 (AI User Experience) for cross-service AI capabilities, PRD-001 (Live TV) for cross-promotion between live and VOD, PRD-002 (TSTV) for catch-up-to-VOD handoffs, and PRD-003 (Cloud PVR) for recording-to-VOD relationships.*
