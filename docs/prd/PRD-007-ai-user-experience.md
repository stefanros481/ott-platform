# PRD-007: AI User Experience Layer

**Document ID:** PRD-007
**Version:** 1.0
**Date:** 2026-02-08
**Status:** Draft
**Author:** PRD Writer B Agent
**References:** VIS-001 (Project Vision & Design), ARCH-001 (Platform Architecture)
**Audience:** Product Management, AI/ML Engineering, UX Design, Backend Engineering

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

The AI User Experience Layer is the cross-cutting intelligence that powers every personalized surface across the platform. It is not a standalone product feature visible to users as "the AI" -- rather, it is the underlying engine that makes the home screen uniquely relevant, search results uncannily accurate, thumbnails distinctly appealing, and notifications precisely timed for each individual viewer.

This PRD defines the AI capabilities that directly enhance the end-user experience across all services: Live TV, TSTV, Cloud PVR, VOD/SVOD, EPG, and Multi-Client. It covers the Recommendation Engine, Personalized Discovery, Viewing Intelligence, Content Intelligence, and Proactive Engagement systems. Backend/operational AI capabilities (AIOps, CDN intelligence, content operations) are covered separately in PRD-008.

### Business Context

AI-powered personalization is the platform's primary competitive differentiator. The vision document (VIS-001) establishes that "every surface personalizes" -- and this PRD makes that commitment concrete. Industry data supports the investment: Netflix attributes over $1B annually in subscriber retention to its recommendation system. Platforms with mature personalization see 30-40% higher engagement and 15-25% lower churn compared to those relying on editorial curation alone.

However, the AI UX layer must be invisible when it works well and gracefully absent when it does not. Users should feel that the platform "understands" them without feeling surveilled. Every AI feature includes an explainability requirement ("Because you watched X") and a fallback path (what happens when the model is unavailable).

### Scope

**In Scope:**
- Recommendation Engine (hybrid architecture, 10+ surfaces, cold-start, diversity, A/B testing)
- Personalized Discovery (AI hero banner, personalized thumbnails, content digest, conversational search, mood-based browse)
- Viewing Intelligence (co-viewing detection, context awareness, smart continue watching, skip intelligence)
- Content Intelligence (AI-generated metadata, summaries, trailer selection, content similarity)
- Proactive Engagement (smart notifications, re-engagement, onboarding personalization)
- Ethical AI requirements (transparency, control, privacy, bias monitoring, age-appropriate AI)
- Fallback strategies for all AI features

**Out of Scope:**
- Backend/operational AI (AIOps, CDN routing, per-title encoding) -- see PRD-008
- AI infrastructure provisioning (KServe, Feature Store, model training pipelines) -- see ARCH-001
- Client-side rendering of AI features -- see PRD-006 (Multi-Client)
- Business intelligence AI (churn prediction, dynamic pricing, content valuation) -- see PRD-008

---

## 2. Goals & Non-Goals

### Goals

1. **Increase browse-to-play rate from 45% to 65%** by providing highly relevant personalized recommendations on every surface
2. **Reduce mean time-to-play from 10.5 minutes to 3.5 minutes** (at 18-month maturity) through proactive, context-aware content suggestions
3. **Achieve 22% recommendation click-through rate** (from 8% industry baseline) via hybrid recommendation models with diversity injection
4. **Deliver personalization across 10+ surfaces** -- home hero banner, home rails, EPG channel order, EPG "Your Schedule," search results, post-play, notifications, Cloud PVR suggestions, content detail, and weekly digest
5. **Handle cold-start effectively** -- new users should see personalized recommendations within their first session via onboarding taste profiling and content-based models
6. **Maintain user trust and transparency** -- every recommendation includes an explainable reason; users can control, reset, or opt out of personalization
7. **Operate within strict performance budgets** -- recommendation serving < 100ms (p95), no visible delay for personalized surfaces compared to non-personalized

### Non-Goals

- Replacing human editorial curation entirely -- editorial teams retain the ability to pin, boost, or feature content alongside AI recommendations
- Building a general-purpose conversational AI assistant ("chat with the platform") -- conversational search is scoped to content discovery
- Real-time social features (live chat, viewer reactions, social watching parties)
- Advertising personalization / ad targeting (covered in monetization scope)
- Predictive content creation (telling studios what content to produce)

---

## 3. User Scenarios

### Scenario 1: Personalized Home Screen Experience

**Persona:** Priya (The Binge Watcher)
**Context:** Saturday 2 PM, LG webOS TV, long browse session

Priya opens the app. The hero banner shows a personalized spotlight: a new sci-fi series with a tagline tailored to her interests -- "From the creators of Westworld, a mind-bending journey into parallel realities." The thumbnail is an AI-selected variant featuring the female lead (Priya responds more to character-driven imagery than action shots, based on her click patterns).

Below the hero, personalized rails are ordered by AI:
1. **"Continue Watching"** -- 3 active series, AI-prioritized: the one she's closest to finishing is first
2. **"Because You Loved Severance"** -- 6 titles with similar themes (corporate thriller, psychological mystery)
3. **"New This Week"** -- personalized selection from new arrivals matching her taste profile
4. **"Hidden Gems for You"** -- niche titles with high content-based similarity to her viewing history, injecting diversity beyond her usual genres
5. **"Trending"** -- popular content filtered to exclude genres she consistently skips

Each rail is unique to Priya. Another user opening the app at the same time would see entirely different rail content, order, and thumbnails.

### Scenario 2: Conversational Search

**Persona:** Priya (The Binge Watcher)
**Context:** Searching for something specific but can't remember the title

Priya opens the search bar and types: "that show about the office where people don't remember their personal lives." The conversational search engine (backed by an LLM) interprets the semantic intent and returns "Severance" as the top result, along with "Counterpart" and "Homecoming" as related suggestions. No exact keyword match was needed -- the LLM understood the narrative description.

She then types: "something like that but darker, with a horror element." The search refines contextually, returning psychological horror series with corporate/institutional themes. Each result includes a one-line AI-generated explanation of why it matches her query.

### Scenario 3: Cold-Start Onboarding

**Persona:** New user (just signed up)
**Context:** First app launch, no viewing history

A new user opens the app for the first time. Before seeing the home screen, they are presented with a brief taste profiling quiz:
1. "Pick 3 genres you enjoy" (visual grid of genre cards)
2. "Select any shows you've watched and liked" (grid of 20 popular titles across genres)
3. "How do you usually watch?" (Alone / With family / Both)

Based on these 3 answers, the Recommendation Engine generates an immediate personalized home screen. The user sees:
- A hero banner for a title matching their selected genres
- "Picked for You" rail based on genre and title selections
- "Popular Right Now" rail (popularity fallback for sparse signal)
- "Start Here" rail: editor-curated introductory content

Within the first session (after 2-3 play events), the model has enough implicit signal to start refining recommendations. By session 3, the cold-start overlay fades and the full hybrid recommendation model takes over.

### Scenario 4: Co-Viewing Detection and Adaptation

**Persona:** The Okafor Family
**Context:** Sunday evening, living room Android TV

David and Amara are watching TV together after the kids are in bed. The platform detects a likely co-viewing session based on:
- Time of day (Sunday 9:30 PM = historical David+Amara viewing time)
- Device (living room TV = shared device)
- Recent profile activity (both profiles were active on the household earlier today)

The home screen subtly adapts: recommendations blend David's and Amara's interests. Instead of David's sports-heavy recommendations or Amara's cooking shows, the "For You" rail shows dramas and thrillers they've both watched or rated positively. A subtle badge reads: "Suggestions for David & Amara."

They can dismiss this with one tap to return to David's individual profile recommendations.

### Scenario 5: Smart Continue Watching

**Persona:** Priya (The Binge Watcher)
**Context:** 6 titles in "Continue Watching," some stale

Priya's "Continue Watching" rail is managed by AI:
- **Position 1:** "Silo S2" -- watched yesterday, 2 episodes left (high priority: recent + near completion)
- **Position 2:** "3 Body Problem" -- watched 3 days ago, mid-season (moderate recency)
- **Position 3:** "The Bear S3" -- watched last week, new episode available (boosted by new content)
- **Auto-archived:** "The Crown" -- last watched 45 days ago, moved to "Paused Shows" section (not cluttering the main rail)
- **Auto-archived:** "Lupin" -- last watched 60 days ago, Season 1 finished, no Season 2 scheduled

Priya sees 3 relevant titles instead of 6, with the most actionable one first. She can access archived titles via a "See Paused Shows" link.

### Scenario 6: Personalized Thumbnails

**Persona:** Erik (The Sports Fan) and Priya (The Binge Watcher)
**Context:** Same title, different users, different thumbnails

A new action-drama series appears on the platform. The content enrichment pipeline has generated 8 thumbnail variants:
- Variants 1-2: Action scenes (explosions, chases)
- Variants 3-4: Character close-ups (male lead, female lead)
- Variants 5-6: Dramatic moments (confrontation scenes)
- Variants 7-8: Atmospheric shots (moody landscapes)

When Erik sees this title, he gets Variant 1 (action scene) -- his click history shows strong response to action imagery. When Priya sees it, she gets Variant 4 (female lead close-up) -- her click history shows preference for character-driven thumbnails. The selection is driven by a multi-armed bandit algorithm that continuously optimizes thumbnail-to-click conversion per user segment.

### Scenario 7: AI-Timed Smart Notification

**Persona:** Maria (The Busy Professional)
**Context:** Thursday 8:30 PM, not currently using the app

Maria receives a push notification: "New episode of The Bear just dropped. 28 min -- perfect for tonight?"

This notification was triggered because:
- The Recommendation Service detected a new episode of a show Maria is actively following
- The notification timing model predicted 8:30 PM Thursday as Maria's highest-probability viewing time (based on her 6-week viewing pattern)
- Maria has not yet opened the app today (re-engagement signal)
- She has not received a notification in 3 days (frequency cap respected)
- The episode duration (28 min) was included because Maria's profile indicates sensitivity to episode length on weeknights

Maria taps the notification and is taken directly to the episode playback screen.

### Scenario 8: Mood-Based Browse

**Persona:** Thomas (The Casual Viewer)
**Context:** Friday evening, not sure what to watch

Thomas opens the app and sees a "What are you in the mood for?" prompt with mood options: "Relaxing," "Exciting," "Funny," "Inspiring," "Gripping." He taps "Relaxing." The app shows a curated grid of content tagged by the AI content intelligence system as relaxing: nature documentaries, slow-paced dramas, travel shows, ambient music programs. Content is drawn from all sources -- VOD, catch-up, and live programs currently airing that match the mood. Thomas picks a nature documentary within 30 seconds.

### Scenario 9: Weekly Content Digest

**Persona:** Maria (The Busy Professional)
**Context:** Saturday morning, email notification

Maria receives the weekly "What's New & Worth It" digest via email and in-app notification:

> **Your Week in Streaming**
> 1. "The Bear S3E05" -- New episode, 28 min (Continue your binge)
> 2. "Blue Planet III" -- Just added, documentary (You loved Planet Earth)
> 3. "Past Lives" -- Leaving in 5 days (A24 drama matching your taste profile)
> 4. "Tokyo Vice S2" -- Premieres Wednesday (International crime drama -- you might like this)
> 5. "Live: Roland Garros Final" -- Sunday 2 PM (Based on your sports catch-up viewing)

The digest is personalized per profile and limited to 5 items to respect attention. Each item includes a deep link to the app. Item 3 includes urgency ("Leaving in 5 days") to drive engagement. Item 5 was included because Maria occasionally watches sports catch-up, injecting diversity beyond her core drama preferences.

### Scenario 10: Post-Play Recommendations

**Persona:** Priya (The Binge Watcher)
**Context:** Just finished a movie

Priya finishes watching a Japanese animated film. The post-play screen shows:
- **Auto-play countdown (15 seconds):** "Up Next: Spirited Away" -- the highest-rated AI recommendation based on what she just watched
- **"More Like This" rail:** 6 titles with thematic and stylistic similarity (not just "anime" but specifically atmospheric, emotionally resonant anime)
- **"From the Same Director" link:** 3 other films by the same director
- **"You Might Also Enjoy" rail:** 4 titles from adjacent genres (live-action films with similar thematic elements)

The auto-play countdown title is specifically chosen for binge continuation. If Priya watches 3+ titles in a session, the auto-play timer shortens to 5 seconds (she has opted into "binge mode").

---

## 4. Functional Requirements

### Recommendation Engine Core

| ID | Requirement | Priority | Phase | Acceptance Criteria |
|----|-------------|----------|-------|---------------------|
| AIUX-FR-001 | Recommendation Engine shall implement a hybrid architecture combining collaborative filtering, content-based filtering, contextual signals, and trending data | P0 | 1 | Given the engine receives a recommendation request, then it blends outputs from collaborative, content-based, and contextual models using a learned weighting function, with each model contributing measurably to the final ranked list |
| AIUX-FR-002 | Recommendation Engine shall serve personalized results across at minimum 10 distinct surfaces (see surface catalog below) | P0 | 1-3 | Each surface returns content ranked by a surface-specific objective function (e.g., home hero optimizes for engagement, post-play optimizes for continuation) |
| AIUX-FR-003 | Recommendations shall incorporate both implicit signals (watch time, completion rate, browse behavior) and explicit signals (thumbs up/down, "not interested," ratings) | P0 | 1 | Given a user gives "thumbs down" on a title, then that title's recommendation score drops to 0 within 1 hour; given a user watches 90% of a title, then similar titles' scores increase within the next recommendation refresh |
| AIUX-FR-004 | Each recommendation shall include an explainability reason selectable from a defined set: "Because you watched X," "Trending in your area," "New in genres you love," "Popular this week," "Recommended for [profile name]" | P0 | 1 | Given a recommendation is displayed, then a human-readable reason is included; the reason is contextually accurate (not random or generic) |
| AIUX-FR-005 | Recommendation Engine shall support A/B testing with minimum 5% traffic allocation per variant, consistent user assignment, and sequential statistical testing | P0 | 1 | Given an A/B experiment is running with 2 variants, then user assignment is consistent across sessions (same user always sees same variant); experiment results include primary metric (CTR) and guardrail metric (session count) with statistical significance |

### Recommendation Surfaces Catalog

| ID | Surface | Location | Optimization Objective | Phase |
|----|---------|----------|----------------------|-------|
| AIUX-FR-010 | Home Hero Banner | Home screen top | Engagement (click-through rate) | 1 |
| AIUX-FR-011 | Home Personalized Rails | Home screen body | Discovery (unique title plays) | 1 |
| AIUX-FR-012 | Post-Play Recommendations | After content ends | Continuation (next play rate) | 1 |
| AIUX-FR-013 | EPG Channel Order | EPG grid | Channel engagement (tune-in rate) | 1 |
| AIUX-FR-014 | EPG "Your Schedule" | EPG personalized view | Cross-source engagement | 2 |
| AIUX-FR-015 | Search Results Ranking | Search results page | Search-to-play rate | 1 |
| AIUX-FR-016 | Smart Notifications | Push / in-app | Re-engagement (notification-to-play) | 2 |
| AIUX-FR-017 | Cloud PVR Suggestions | PVR management | Recording adoption | 2 |
| AIUX-FR-018 | Content Detail ("More Like This") | Title detail page | Discovery (related play rate) | 1 |
| AIUX-FR-019 | Weekly Digest | Email / in-app | Weekly engagement (digest-to-play) | 2 |
| AIUX-FR-019b | In-Player Suggestions | Player overlay during credits | Binge continuation rate | 2 |

### Cold-Start Handling

| ID | Requirement | Priority | Phase | Acceptance Criteria |
|----|-------------|----------|-------|---------------------|
| AIUX-FR-020 | Platform shall present a 3-step onboarding taste quiz to new users on first launch | P0 | 1 | Given a new user opens the app, then a quiz with genre selection, title recognition, and viewing context questions appears; completion rate > 70%; quiz takes < 60 seconds |
| AIUX-FR-021 | Recommendation Engine shall generate personalized recommendations immediately after onboarding quiz completion (no viewing history required) | P0 | 1 | Given a new user completes the onboarding quiz, then the home screen shows personalized rails based on quiz answers within 2 seconds; recommendations are measurably different from the default popularity baseline |
| AIUX-FR-022 | Content-based recommendations shall function without collaborative filtering data (for new users and new content) | P0 | 1 | Given a new title is added to the catalog with no viewing data, then it appears in recommendations for users whose taste profiles match its content embeddings within 1 hour of ingest |
| AIUX-FR-023 | Cold-start model shall transition to full hybrid model after a minimum threshold of implicit signals (configurable, default: 5 play events over 3 sessions) | P1 | 1 | Given a new user has completed 5 plays across 3 sessions, then the recommendation model switches from cold-start to hybrid; the transition is seamless with no visible disruption |

### Diversity and Fairness

| ID | Requirement | Priority | Phase | Acceptance Criteria |
|----|-------------|----------|-------|---------------------|
| AIUX-FR-030 | Recommendations shall include configurable diversity injection to prevent filter bubbles | P0 | 1 | Given a user primarily watches drama, then at least 15% of recommendations come from other genres the user has not explicitly rejected; diversity ratio is configurable per surface (10-30%) |
| AIUX-FR-031 | Editorial teams shall have the ability to pin, boost, or suppress specific titles in recommendation surfaces | P0 | 1 | Given an editor pins a title to the home hero banner for all users, then the AI recommendation is overridden for the pinned position; the pin has a configurable time window |
| AIUX-FR-032 | Recommendation Engine shall undergo monthly bias audits evaluating representation across content categories, languages, and production origins | P1 | 2 | Given a monthly audit runs, then a report is generated showing: % of recommendations per genre, language, and production country vs catalog distribution; flagging deviations > 20% from catalog representation |
| AIUX-FR-033 | When AI recommendations are unavailable (model outage, cold-start timeout), the system shall fall back to popularity-based recommendations (pre-computed top-100 per genre) | P0 | 1 | Given the Recommendation Service is unavailable, then BFF returns popularity-based rails within 200ms; the fallback is visually indistinguishable from AI recommendations (same layout, no error messaging) |

### User Feedback and Control

| ID | Requirement | Priority | Phase | Acceptance Criteria |
|----|-------------|----------|-------|---------------------|
| AIUX-FR-040 | Users shall be able to rate content with thumbs up / thumbs down on any title | P0 | 1 | Given a user gives thumbs up on a title, then the explicit signal is ingested by the Recommendation Service and affects future recommendations within 1 hour |
| AIUX-FR-041 | Users shall be able to mark content as "Not Interested" to exclude it from recommendations | P0 | 1 | Given a user marks a title as "Not Interested," then the title is permanently excluded from all recommendation surfaces for that profile |
| AIUX-FR-042 | Users shall be able to reset their recommendation profile to start fresh | P1 | 2 | Given a user resets recommendations, then all viewing history signals are cleared from the recommendation model; the user is presented with the onboarding quiz again |
| AIUX-FR-043 | Users shall be able to exclude specific genres from recommendations | P1 | 2 | Given a user excludes "Horror" from their preferences, then no horror titles appear in any recommendation surface for that profile |
| AIUX-FR-044 | Users shall be able to view a "Why was this recommended?" explanation for any recommended title | P1 | 2 | Given a user long-presses a recommended title, then a dialog shows the recommendation reason and offers "Not Interested" and "See fewer like this" actions |

---

## 5. AI-Specific Features

### 5.1 Recommendation Engine Architecture

**Hybrid Model Design:**

The Recommendation Engine combines four model families:

1. **Collaborative Filtering (Matrix Factorization + Neural CF)**
   - Learns user-item affinities from viewing behavior across the entire user base
   - Strong for mainstream content and users with sufficient history
   - Weak for: new users (cold start), new content (no interactions), niche content (sparse signal)
   - Framework: TensorFlow 2.16 (TF Serving on KServe)
   - Refresh: Full retraining every 6 hours on latest viewing data

2. **Content-Based Filtering (Embedding Similarity)**
   - Computes content similarity using 768-dimensional embeddings from title metadata, visual features, and AI-generated tags
   - Strong for: new content (no viewing data needed), niche discovery, "more like this" scenarios
   - Weak for: cannot capture emergent viewing patterns or cultural trends
   - Framework: PyTorch 2.3, sentence-transformers for embeddings
   - Storage: pgvector (HNSW index, < 20ms for top-50 retrieval)
   - Refresh: Embeddings generated on content ingest; user taste vectors updated hourly

3. **Contextual Model (Gradient-Boosted Trees)**
   - Incorporates real-time context: time-of-day, day-of-week, device type, session length, last-watched content type
   - Strong for: time-sensitive recommendations, device-aware suggestions
   - Framework: XGBoost 2.0 (KServe, CPU inference)
   - Refresh: Hourly retraining on latest contextual viewing data

4. **Trending/Popularity Model (Real-Time Aggregation)**
   - Tracks real-time viewership, social buzz, and content freshness
   - Strong for: surfacing culturally relevant content, sports events, premieres
   - Implementation: Kafka Streams aggregation → Redis cache (updated every minute)
   - No ML model -- pure aggregation and ranking

**Fusion Strategy:**
- A learned fusion model (lightweight neural network) combines outputs from all four model families
- Fusion weights are surface-specific: home hero leans toward collaborative (engagement), "More Like This" leans toward content-based (similarity), EPG leans toward contextual (time-sensitivity)
- Diversity injection is applied post-fusion: a configurable percentage (default 15%) of recommendations are drawn from under-represented genres or content categories
- Re-ranking applies business rules: content pinned by editors, suppressed titles, entitlement filtering, parental control filtering

### 5.2 Personalized Discovery

#### AI Hero Spotlight

**Description:** The home screen hero banner is personalized per session. The system selects the optimal title and creative variant for each viewer.

**Implementation:**
- A pool of 20-50 hero-eligible titles is maintained (mix of new releases, editorial picks, and AI-identified high-engagement titles)
- For each user session, the model scores each title and selects the top match
- Multiple creative variants exist per title (different key art, different tagline emphasis)
- A multi-armed bandit algorithm selects the creative variant most likely to drive click-through for the user's segment
- Each hero display is logged as an impression; click-through and subsequent play events feed the bandit

| ID | Requirement | Priority | Phase | Acceptance Criteria |
|----|-------------|----------|-------|---------------------|
| AIUX-AI-001 | Home hero banner shall display a personalized title selection per user per session | P0 | 1 | Given 2 different users open the app, then each sees a different hero title (unless the same title is editorially pinned for all users); hero CTR > 15% (vs 8% for non-personalized) |
| AIUX-AI-002 | Hero banner shall support multi-variant creative (different thumbnails, taglines) with per-user optimization | P1 | 2 | Given a title has 4 creative variants, then each user sees the variant predicted to have the highest CTR for their segment; variant selection adapts over time via multi-armed bandit |

#### Personalized Thumbnails

**Description:** Each title can have multiple thumbnail variants. The AI selects the variant most likely to attract each user based on their visual preference patterns.

| ID | Requirement | Priority | Phase | Acceptance Criteria |
|----|-------------|----------|-------|---------------------|
| AIUX-AI-010 | The content enrichment pipeline shall generate at minimum 4 thumbnail variants per title (action, character, atmosphere, dramatic moment) | P1 | 2 | Given a title is ingested, then 4+ thumbnail variants are extracted and quality-scored within the enrichment pipeline; each variant is tagged by category |
| AIUX-AI-011 | Recommendation surfaces shall display the AI-selected thumbnail variant per user per title | P1 | 2 | Given a title appears for 2 different users, then each may see a different thumbnail variant; variant selection is based on the user's historical click-through patterns by thumbnail category |
| AIUX-AI-012 | Thumbnail selection shall adapt over time using a multi-armed bandit with per-user-segment optimization | P2 | 2 | Given a new title launches with 4 variants, then within 7 days the system converges on the best variant per user segment with < 5% regret |

#### Conversational Search

**Description:** Users can search for content using natural language descriptions, narrative queries, or contextual requests. The search engine combines keyword search (Elasticsearch) with semantic search (LLM + embeddings) to understand intent.

| ID | Requirement | Priority | Phase | Acceptance Criteria |
|----|-------------|----------|-------|---------------------|
| AIUX-AI-020 | Search shall support natural language queries beyond keyword matching ("show me something like X but more Y") | P1 | 3 | Given a query "dark sci-fi with a female lead, like Severance but more horror," then results include titles matching the semantic intent, not just keyword matches; search success rate (search-to-play) > 65% for conversational queries |
| AIUX-AI-021 | Conversational search shall maintain context within a session for follow-up refinements | P1 | 3 | Given a user searches "action movies," then follows with "but not too violent," then results are refined contextually; the system does not treat the second query independently |
| AIUX-AI-022 | Search results shall include an AI-generated explanation for why each result matches the query | P2 | 3 | Given a conversational search returns results, then each result shows a one-line match explanation (e.g., "Psychological thriller set in a corporate environment, matches your query about an office where people don't remember their lives") |
| AIUX-AI-023 | Conversational search shall fall back to keyword search (Elasticsearch) when the LLM is unavailable | P0 | 3 | Given Bedrock is unavailable, then search functions using Elasticsearch keyword matching with no visible error; response time remains < 500ms |

#### Mood-Based Browse

**Description:** Users can browse content by mood/feeling rather than traditional genre categories.

| ID | Requirement | Priority | Phase | Acceptance Criteria |
|----|-------------|----------|-------|---------------------|
| AIUX-AI-030 | Platform shall offer mood-based browse with at minimum 8 mood categories: Relaxing, Exciting, Funny, Inspiring, Gripping, Romantic, Thought-Provoking, Nostalgic | P1 | 2 | Given a user selects "Relaxing" mood, then results include titles tagged with the "relaxing" mood by the content intelligence pipeline; results span all content sources (VOD, catch-up, live programs) |
| AIUX-AI-031 | Mood categories shall be populated by AI content analysis, not manual editorial tagging | P1 | 2 | Given a title is ingested, then mood tags are assigned automatically by the content enrichment pipeline (analyzing metadata, subtitles, audio features, and visual features); accuracy > 80% vs human-labeled ground truth |
| AIUX-AI-032 | Mood browse results shall be personalized within the mood category | P2 | 3 | Given 2 users both browse "Funny," then results are ordered differently based on each user's sub-preferences within comedy (slapstick vs dry humor vs dark comedy) |

#### Weekly Content Digest

| ID | Requirement | Priority | Phase | Acceptance Criteria |
|----|-------------|----------|-------|---------------------|
| AIUX-AI-040 | Platform shall generate a weekly personalized "What's New & Worth It" digest per profile | P1 | 2 | Given Saturday arrives, then each profile receives a digest with 5 personalized picks via in-app notification and optionally email; each pick includes title, source type, and relevance reason |
| AIUX-AI-041 | Digest shall include urgency signals for expiring content | P2 | 2 | Given a title matching the user's taste is expiring within 7 days, then the digest includes it with an "Leaving Soon" badge |
| AIUX-AI-042 | Digest shall inject at least 1 diversity pick from outside the user's primary genres | P1 | 2 | Given a user primarily watches drama, then 1 of the 5 digest picks is from a different genre the user has not explicitly rejected |

### 5.3 Viewing Intelligence

#### Co-Viewing Detection

**Description:** The platform detects when multiple household members are likely watching together and adapts recommendations accordingly.

**Detection Model:**
- Input features: time-of-day, day-of-week, device type, household size, historical co-viewing patterns (labeled from profile switches and "watching together" activations)
- Output: probability of co-viewing (0.0-1.0) and most likely viewer combination
- Threshold: co-viewing suggestions appear when probability > 0.7
- Model: XGBoost classifier, retrained weekly per household

| ID | Requirement | Priority | Phase | Acceptance Criteria |
|----|-------------|----------|-------|---------------------|
| AIUX-AI-050 | Platform shall detect likely co-viewing sessions with > 70% precision at the 0.7 confidence threshold | P1 | 2 | Given it is a known co-viewing time for the household, then the co-viewing detection model correctly identifies the session as co-viewing > 70% of the time (measured by subsequent profile interaction confirmation) |
| AIUX-AI-051 | During detected co-viewing, recommendations shall blend interests of likely-present viewers | P1 | 2 | Given David (sports) and Amara (cooking) are detected as co-viewing, then recommendations include titles with broad appeal plus both sports-related and cooking-related content; neither viewer's preferences dominate |
| AIUX-AI-052 | Co-viewing mode shall respect the most restrictive parental control of present viewers | P0 | 2 | Given a co-viewing session includes a child profile with PG restriction, then all recommendations and search results are filtered to PG or below |
| AIUX-AI-053 | Users shall be able to manually toggle co-viewing mode on/off regardless of AI detection | P0 | 2 | Given a user taps "Watch Together," then co-viewing mode activates immediately regardless of the detection model's output |

#### Context Awareness

| ID | Requirement | Priority | Phase | Acceptance Criteria |
|----|-------------|----------|-------|---------------------|
| AIUX-AI-060 | Recommendations shall adapt based on device type (TV: long-form; mobile: short-form; tablet: mixed) | P0 | 1 | Given a user on a phone at 8 AM, then recommendations prioritize content < 30 min duration; given the same user on TV at 9 PM, then long-form content (movies, 45+ min episodes) is prioritized |
| AIUX-AI-061 | Recommendations shall adapt based on time-of-day patterns learned per profile | P1 | 2 | Given Maria watches news in the morning and drama in the evening, then morning recommendations on any device prioritize news/short content and evening recommendations prioritize drama |
| AIUX-AI-062 | Recommendations shall consider available viewing time when duration signals are available (e.g., "I have 30 minutes") | P2 | 3 | Given a user signals "30 minutes," then only content with runtime 20-35 minutes appears in top recommendations |

#### Smart Continue Watching

| ID | Requirement | Priority | Phase | Acceptance Criteria |
|----|-------------|----------|-------|---------------------|
| AIUX-AI-070 | "Continue Watching" rail shall be AI-sorted by likelihood of resume (not just recency) | P0 | 1 | Given a user has 5 in-progress titles, then the "Continue Watching" order considers: recency, completion proximity, new episode availability, and time-of-day patterns; the most likely resume is in position 1 |
| AIUX-AI-071 | Titles not interacted with for 30+ days shall be auto-archived to a "Paused" section | P1 | 1 | Given a title in "Continue Watching" has not been watched for 35 days, then it moves to "Paused Shows" section; the user can restore it with one tap |
| AIUX-AI-072 | Auto-archive logic shall consider content availability (do not archive if new season just released) | P1 | 2 | Given a series in "Continue Watching" has not been watched for 40 days BUT a new season was released 2 days ago, then the title remains in "Continue Watching" and is boosted with a "New Season" badge |

#### Skip Intelligence

| ID | Requirement | Priority | Phase | Acceptance Criteria |
|----|-------------|----------|-------|---------------------|
| AIUX-AI-080 | Player shall support "Skip Intro" for series episodes with AI-detected intro markers | P1 | 2 | Given a series episode has an AI-detected intro segment, then a "Skip Intro" button appears 3 seconds into the intro and disappears when the intro ends; skip boundary accuracy is within ± 3 seconds |
| AIUX-AI-081 | Player shall support "Skip Recap" for series episodes with AI-detected recap segments | P2 | 3 | Given a series episode has an AI-detected recap segment, then a "Skip Recap" button appears at the start; accuracy within ± 5 seconds |
| AIUX-AI-082 | Intro and recap detection shall use audio fingerprinting combined with visual analysis | P1 | 2 | Given a series with consistent intro music/visuals, then the detection model identifies intro boundaries with > 90% accuracy across the season |

### 5.4 Content Intelligence

| ID | Requirement | Priority | Phase | Acceptance Criteria |
|----|-------------|----------|-------|---------------------|
| AIUX-AI-090 | Content enrichment pipeline shall automatically generate tags for: mood, theme, visual style, pace, and content warnings | P0 | 1 | Given a title is ingested, then AI-generated tags are produced within the enrichment pipeline processing time; tag accuracy > 85% vs human-labeled ground truth on a 500-title validation set |
| AIUX-AI-091 | Content enrichment shall generate 2-3 sentence AI summaries for titles lacking editorial descriptions | P1 | 2 | Given a program has no editorial synopsis or a synopsis < 50 characters, then an AI-generated summary is created via Bedrock LLM and stored in the Metadata Service; summary quality rated "acceptable or better" by editorial team in > 90% of cases |
| AIUX-AI-092 | Content similarity shall use embedding-based deep similarity (not just genre matching) | P0 | 1 | Given a user views "More Like This" for a title, then results include titles with similar narrative themes, visual style, and emotional tone -- not just the same genre; evaluated by human relevance rating > 3.5/5 on average |
| AIUX-AI-093 | AI shall select the optimal trailer variant per user when multiple trailers exist for a title | P2 | 3 | Given a title has 3 trailer variants (action cut, emotional cut, mystery cut), then the variant shown to a user is selected based on their engagement patterns with previous trailers; trailer-to-play conversion improves by > 10% vs random selection |

### 5.5 Proactive Engagement

#### Smart Notifications

| ID | Requirement | Priority | Phase | Acceptance Criteria |
|----|-------------|----------|-------|---------------------|
| AIUX-AI-100 | Platform shall send AI-timed push notifications for: new episodes of followed series, expiring content in watchlist, live events matching interests, and weekly digest | P0 | 2 | Given a new episode of a user's followed series is available, then a notification is sent within 1 hour of availability during the user's preferred notification window |
| AIUX-AI-101 | Notification timing shall be personalized per user based on historical engagement patterns | P1 | 2 | Given a user typically opens notifications between 7-8 PM, then AI schedules notifications within that window (not at 3 AM when the episode actually drops) |
| AIUX-AI-102 | Notifications shall be frequency capped: maximum 5 notifications per week per profile (configurable) | P0 | 2 | Given a profile has received 5 notifications this week, then no additional notifications are sent regardless of qualifying events |
| AIUX-AI-103 | Users shall be able to configure notification preferences: on/off per category (new episodes, recommendations, live events), quiet hours, and frequency | P0 | 2 | Given a user sets quiet hours from 10 PM to 8 AM, then no notifications are delivered during that window |

#### Re-Engagement

| ID | Requirement | Priority | Phase | Acceptance Criteria |
|----|-------------|----------|-------|---------------------|
| AIUX-AI-110 | Users who have not opened the app in 14+ days shall receive a personalized re-engagement notification | P1 | 2 | Given a user has been inactive for 14 days, then a re-engagement notification is sent with a specific content suggestion (e.g., "3 new episodes of your show are waiting"); re-engagement rate > 10% |
| AIUX-AI-111 | Re-engagement notifications shall be limited to 1 per inactive period (no repeated badgering) | P0 | 2 | Given a re-engagement notification was sent and the user did not return, then no second notification is sent for at least 30 days |

#### Onboarding Personalization

| ID | Requirement | Priority | Phase | Acceptance Criteria |
|----|-------------|----------|-------|---------------------|
| AIUX-AI-120 | Onboarding quiz shall present 3 steps: genre selection (multi-select from 12 genres), title recognition (select from 20 popular titles), and viewing context (alone/family/both) | P0 | 1 | Given a new user starts onboarding, then the quiz appears with genre grid, title grid, and context selection; quiz completion time < 60 seconds; skip option available |
| AIUX-AI-121 | Quiz answers shall immediately generate a personalized home screen with minimum 4 personalized rails | P0 | 1 | Given a user completes the quiz, then the home screen loads within 2 seconds with personalized content based on quiz answers; recommendations are measurably better than random (CTR > 12% vs 8% random baseline) |
| AIUX-AI-122 | Users who skip the quiz shall receive popularity-based recommendations that gradually personalize as viewing data accumulates | P0 | 1 | Given a user skips onboarding, then home screen shows popularity-based rails; after 3 play events, recommendations begin personalizing |

### 5.6 Ethical AI Requirements

| ID | Requirement | Priority | Phase | Acceptance Criteria |
|----|-------------|----------|-------|---------------------|
| AIUX-AI-130 | Every recommendation surface shall include an explainability mechanism (visible reason for each recommendation) | P0 | 1 | Given a recommendation is displayed, then a human-readable reason is available (hover/long-press on any surface) |
| AIUX-AI-131 | Users shall have full control over their recommendation data: view data collected, delete data, opt out of personalization entirely | P0 | 1 | Given a user navigates to Privacy settings, then they can view a summary of collected data, delete all recommendation data, and toggle personalization off; when off, all surfaces show popularity-based content |
| AIUX-AI-132 | AI recommendations shall respect parental control boundaries at all times, on all surfaces | P0 | 1 | Given a child profile with PG restriction, then no content rated above PG appears in any recommendation, search result, or notification -- including AI-generated suggestions |
| AIUX-AI-133 | Monthly bias audits shall evaluate recommendation distribution across content language, production country, genre, and content age | P1 | 2 | Given a monthly audit runs, then a report identifies any content category receiving < 50% of its catalog proportion in recommendations; flagged disparities trigger model tuning investigation |
| AIUX-AI-134 | GDPR compliance: all personalization data shall be deletable per user request within 30 days; data processing shall follow purpose limitation and data minimization principles | P0 | 1 | Given a user exercises their right to deletion, then all personal data in the recommendation pipeline (Feature Store entries, model training data contributions, explicit ratings) is purged within 30 days; confirmation is sent to the user |
| AIUX-AI-135 | AI models shall not use protected attributes (race, gender, age, religion) as direct input features | P0 | 1 | Given the feature engineering pipeline, then no feature directly encodes protected attributes; model fairness is validated during training evaluation |

---

## 6. Non-Functional Requirements

### Performance

| ID | Requirement | Target | Measurement |
|----|-------------|--------|-------------|
| AIUX-NFR-001 | Recommendation serving latency (real-time surfaces: home, EPG, detail) | < 100ms (p95) | Server-side: Recommendation Service response time |
| AIUX-NFR-002 | Recommendation serving latency (batch surfaces: digest, notifications) | < 5 seconds per user | Batch processing time / user count |
| AIUX-NFR-003 | Conversational search latency (LLM + retrieval) | < 2 seconds (p95) | Server-side: Search Service → Bedrock → response time |
| AIUX-NFR-004 | Feature Store online read latency | < 10ms (p95) | Feature Store (Redis) read latency |
| AIUX-NFR-005 | Thumbnail selection latency (per user per title) | < 20ms (p95) | Model serving inference time |
| AIUX-NFR-006 | Cold-start recommendation generation (post-quiz) | < 2 seconds | Server-side: quiz answers → personalized home screen response |

### Scale

| ID | Requirement | Target | Measurement |
|----|-------------|--------|-------------|
| AIUX-NFR-010 | Recommendation Service throughput | 3,000 RPS (Phase 1), 15,000 RPS (Phase 4) | Load test with simulated recommendation requests |
| AIUX-NFR-011 | Concurrent personalization | Unique personalized responses for 500,000 concurrent users | Load test: verify all users receive distinct, profile-specific recommendations |
| AIUX-NFR-012 | Content catalog size | Support 50,000 content items with embeddings in vector database | pgvector query performance with 50K 768-dim embeddings, HNSW index |
| AIUX-NFR-013 | Model serving GPU utilization | < 70% GPU utilization at peak load (headroom for burst) | GPU monitoring on KServe inference nodes |

### Model Quality

| ID | Requirement | Target | Measurement |
|----|-------------|--------|-------------|
| AIUX-NFR-020 | Recommendation model signal incorporation | New viewing signals reflected in recommendations within 1 hour | End-to-end: play event → Feature Store update → model re-score → changed recommendation |
| AIUX-NFR-021 | Collaborative filtering model retraining | Full retraining every 6 hours | Training pipeline execution time and schedule |
| AIUX-NFR-022 | Content embedding generation | New content embeddings generated within 30 minutes of ingest | Content Ingest → Embedding Generation → pgvector store pipeline time |
| AIUX-NFR-023 | A/B experiment minimum runtime | 7 days with minimum 10,000 users per variant before declaring significance | A/B framework experiment management |

### Availability

| ID | Requirement | Target | Measurement |
|----|-------------|--------|-------------|
| AIUX-NFR-030 | Recommendation Service availability | 99.9% monthly uptime | Server-side uptime monitoring |
| AIUX-NFR-031 | Fallback coverage | 100% of surfaces have a defined fallback when AI is unavailable | Automated failover testing: disable AI models, verify all surfaces render |
| AIUX-NFR-032 | Search Service availability (including conversational) | 99.9% (keyword), 99.5% (conversational via Bedrock) | Server-side uptime; Bedrock availability is dependent on AWS |

---

## 7. Technical Considerations

### Recommendation Service Architecture

```
Client → BFF → Recommendation Service → [Feature Store, Model Serving, Catalog Service]
                      │
                      ├── Collaborative Model (TF Serving on KServe)
                      ├── Content-Based Model (pgvector similarity)
                      ├── Contextual Model (XGBoost on KServe)
                      ├── Trending Aggregation (Redis)
                      └── Fusion + Re-Ranking + Diversity Injection
```

**Request Flow (Home Screen):**
1. Client opens app → BFF sends request to Recommendation Service with: profile_id, device_type, timestamp, session_context
2. Recommendation Service reads user features from Feature Store (< 10ms)
3. Parallel model invocations: collaborative (< 30ms), content-based (< 20ms), contextual (< 15ms), trending (< 5ms)
4. Fusion model combines outputs into a single scored list (< 10ms)
5. Re-ranking applies: diversity injection (15%), editorial pins, entitlement filter, parental filter (< 5ms)
6. Response returned to BFF with: ordered title list, per-title thumbnail variant, per-title recommendation reason
7. Total: < 100ms (p95)

### Conversational Search Architecture

```
User Query → BFF → Search Service → [Elasticsearch (keyword), Bedrock LLM (semantic)]
                                              │
                                      ┌───────┼───────┐
                                      │       │       │
                                  Keyword   Semantic  Context
                                  Results   Results   Refinement
                                      │       │       │
                                      └───────┼───────┘
                                              │
                                      Fusion + Ranking
                                              │
                                     Personalized Results
```

**Flow:**
1. User enters natural language query
2. Search Service sends query to Elasticsearch (keyword search) and Bedrock LLM (semantic understanding) in parallel
3. Bedrock extracts: intent, entities (genre, actor, mood, era), and generates a structured query
4. Structured query is used to filter and rank content in Elasticsearch and pgvector (embedding similarity)
5. Results from keyword and semantic paths are fused using reciprocal rank fusion
6. Personalization re-ranking applies the user's taste profile to boost relevant results
7. Each result receives an AI-generated match explanation
8. Latency: < 2 seconds (p95) including LLM call

**Session Context:**
- Conversational search maintains a session context (last 3 queries) stored in Redis (TTL: 30 minutes)
- Follow-up queries are prepended with session context before LLM processing
- Context is cleared on new search session (user leaves search and returns)

### Thumbnail Personalization Architecture

- Content Enrichment Pipeline generates thumbnail variants during ingest (4-8 variants per title)
- Each variant is tagged by category (action, character, atmosphere, dramatic)
- A lightweight bandit model (Thompson Sampling) learns per-user-segment click-through rates per thumbnail category
- On recommendation serving, the model selects the variant with the highest expected CTR for the user's segment
- Segments are defined by: primary genre preference, visual preference history (click-through rates per thumbnail category)
- Bandit updates in near-real-time (click events feed back within 5 minutes)

### Feature Store Integration

The Recommendation Service relies on the Feature Store (Feast) for pre-computed user and content features:

**User Features (online, per-profile):**
- Genre preference distribution (15 features: one per genre, normalized probability)
- Recent viewing history (last 20 titles, encoded as embeddings)
- Time-of-day preference distribution (6 time buckets, normalized)
- Device preference distribution
- Explicit ratings summary (thumbs up/down counts per genre)
- Session statistics (avg session length, avg plays per session, browse-to-play ratio)

**Content Features (online, per-title):**
- Content embeddings (768-dim vector)
- Genre, mood, theme tags (multi-hot encoding)
- Popularity score (real-time, hourly updated)
- Freshness score (days since release, decaying function)
- Quality score (average viewer rating, completion rate)
- Availability metadata (which platforms, DRM constraints)

### Model Monitoring and Drift Detection

- **Data drift:** KL divergence monitored on input feature distributions vs training data; alert if KL > 0.1 for any feature group
- **Model drift:** Prediction score distribution monitored; alert if mean score shifts > 10% from baseline
- **Business metric monitoring:** CTR, play rate, session duration tracked per model variant; alert if any metric drops > 5% vs baseline
- **Automated retraining trigger:** When drift alert fires, the training pipeline is automatically queued; human review required before deployment

---

## 8. Dependencies

### Upstream Dependencies

| Dependency | Service/Component | Nature | Impact if Unavailable |
|------------|------------------|--------|----------------------|
| Feature Store (Feast + Redis) | ARCH-001 (AI/ML Infrastructure) | Pre-computed user and content features for real-time inference | Recommendations fall back to popularity-based; no personalization |
| KServe Model Serving | ARCH-001 (AI/ML Infrastructure) | Real-time model inference (collaborative, contextual, anomaly) | Models unavailable; all surfaces fall back to popularity |
| Amazon Bedrock | ARCH-001 (AI/ML Infrastructure) | LLM for conversational search, content summarization | Conversational search falls back to keyword; summaries unavailable |
| pgvector | ARCH-001 (Data Architecture) | Vector similarity search for content-based recommendations | Content-based model unavailable; collaborative + contextual still functional |
| Catalog Service | ARCH-001 (Content Services) | Content metadata for recommendation rendering | Cannot display recommendations without title metadata |
| Profile Service | ARCH-001 (Core Services) | User profile identity for personalization | Cannot personalize; single default experience |
| Entitlement Service | ARCH-001 (Core Services) | Content access filtering for recommendations | Risk of recommending content user cannot access; add runtime entitlement check |
| Kafka Event Bus | ARCH-001 (Data Architecture) | Viewing events for model feedback and feature updates | Features become stale; models do not learn from new behavior |

### Downstream Dependencies (services depend on AI UX)

| Dependent | PRD | Nature |
|-----------|-----|--------|
| Live TV | PRD-001 | Personalized channel order, AI channel surfing suggestions |
| TSTV | PRD-002 | "Your Catch-Up" personalized rail, "You missed this" suggestions |
| Cloud PVR | PRD-003 | AI recording suggestions, smart retention recommendations |
| VOD/SVOD | PRD-004 | Home screen personalization, search, all recommendation surfaces |
| EPG | PRD-005 | AI channel ordering, "Your Schedule," relevance scoring, smart reminders |
| Multi-Client | PRD-006 | All AI features are rendered through client apps; context signals come from clients |
| AI Backend/Ops | PRD-008 | Shares Feature Store, model serving infrastructure, and ML pipeline |

### Cross-PRD Integration Points

- **PRD-001 (Live TV):** AI powers personalized channel ordering (EPG-AI-001), live popularity signals ("Trending Now"), and smart channel surfing suggestions.
- **PRD-002 (TSTV):** "Your Catch-Up" rail is generated by the Recommendation Engine using catch-up content as a candidate source. "You missed this" notifications use the smart notification system.
- **PRD-003 (Cloud PVR):** Recording suggestions (AIUX-FR-017) are generated by scoring upcoming EPG programs against the user's taste profile. Smart retention recommendations use viewing history and content availability signals.
- **PRD-004 (VOD/SVOD):** The primary consumer of all recommendation surfaces -- home screen, detail page, search, post-play, and the core discovery experience.
- **PRD-005 (EPG):** "Your Schedule" (EPG-AI-010) is generated by the multi-source ranking model in the Recommendation Service. Channel ordering (EPG-AI-001) uses the contextual model.
- **PRD-006 (Multi-Client):** Client context signals (device type, network, screen size) feed the contextual recommendation model. On-device AI (MC-AI-010) caches personalized state from the Recommendation Service.
- **PRD-008 (AI Ops):** Shares the Feature Store, model serving cluster (KServe), and ML pipeline infrastructure. AI UX models and AI Ops models run on the same GPU inference cluster.

---

## 9. Success Metrics

| Metric | Description | Baseline | Phase 1 Target | Phase 2 Target | Phase 4 Target | Measurement Method |
|--------|-------------|----------|---------------|---------------|---------------|-------------------|
| Browse-to-Play Rate | % of sessions that result in a play event | 45% | 55% | 60% | 65% | Client telemetry: session start → play event |
| Mean Time to Play | Time from app open to first play event | 10.5 min | 6 min | 4.5 min | 3.5 min | Client telemetry: app launch → first play timestamp |
| Recommendation CTR | Click-through rate across all recommendation surfaces | 8% | 15% | 18% | 22% | Impression → click event tracking per surface |
| Home Hero CTR | Click-through rate on personalized hero banner | 8% | 15% | 20% | 25% | Impression → click event for hero surface |
| Content Discovery NPS | User satisfaction with content discovery | +15 | +30 | +38 | +45 | Quarterly user survey |
| Cold-Start Effectiveness | CTR for users in their first 3 sessions (vs population average) | N/A | > 70% of mature user CTR | > 80% | > 85% | Segment analysis: new user CTR / overall CTR |
| Search Success Rate | % of searches resulting in a play within 2 minutes | 55% | 65% | 72% | 80% | Client telemetry: search → play event |
| Conversational Search Satisfaction | % of conversational searches rated "relevant" by user feedback | N/A | N/A | N/A | > 75% | In-search relevance feedback widget |
| Smart Notification Engagement | % of AI notifications resulting in app open + play within 30 min | N/A | N/A | 18% | 25% | Notification delivery → app open → play tracking |
| Diversity Index | % of recommendations from genres outside user's top 3 | N/A | > 15% | > 18% | > 20% | Recommendation log analysis |

---

## 10. Open Questions & Risks

### Open Questions

| ID | Question | Owner | Impact | Target Decision Date |
|----|----------|-------|--------|---------------------|
| AIUX-OQ-001 | Should the onboarding quiz be mandatory or skippable? Mandatory improves cold-start quality but may increase drop-off. | Product / UX | Affects cold-start effectiveness and onboarding completion rate | Month 2 |
| AIUX-OQ-002 | What LLM model should power conversational search? Claude (via Bedrock) offers quality but latency. A smaller model may be faster but less accurate. | AI/ML Engineering | Affects search latency and quality | Month 6 (Phase 3 planning) |
| AIUX-OQ-003 | Should personalized thumbnails be an opt-in feature or default? Some users find it "creepy" that thumbnails change. | Product / UX | Affects user trust and engagement | Month 6 |
| AIUX-OQ-004 | How aggressively should diversity injection be set? Too low = filter bubbles. Too high = irrelevant recommendations. | AI/ML / Product | Affects recommendation relevance and content exposure | Month 3 (tunable, start at 15%) |
| AIUX-OQ-005 | Should co-viewing detection use only behavioral signals, or should we incorporate audio/video signals (voice detection, face detection) from smart TVs? Privacy implications are significant. | Product / Legal / AI | Affects detection accuracy and privacy posture | Month 4 |

### Risks

| ID | Risk | Severity | Likelihood | Mitigation |
|----|------|----------|------------|------------|
| AIUX-R-001 | **Recommendation quality is poor at launch** -- insufficient data, cold-start problem, and model immaturity lead to irrelevant suggestions that damage user trust in the AI features | High | High | Launch with robust fallback strategy (popularity-based defaults are high quality); require onboarding quiz for initial personalization; set minimum confidence threshold (do not recommend below 0.6 confidence); A/B test against editorial curation baseline; invest in content-based model (works without viewing history) |
| AIUX-R-002 | **Filter bubble effect** -- AI amplifies existing preferences and users never discover new content, leading to engagement plateau and eventual boredom | High | Medium | Implement configurable diversity injection (default 15%); weekly digest includes at least 1 out-of-comfort-zone pick; monthly bias audits; editorial override capability; track diversity index as a first-class metric |
| AIUX-R-003 | **Conversational search hallucinations** -- LLM returns fabricated content descriptions or recommends titles that don't exist in the catalog | High | Medium | Ground all LLM outputs against the catalog database; LLM generates structured queries (not free-text descriptions) that are executed against Elasticsearch/pgvector; validate every title ID returned by the LLM exists in the catalog; display "I couldn't find an exact match" when confidence is low |
| AIUX-R-004 | **Personalized thumbnail backlash** -- users perceive different thumbnails for the same title as "manipulative" or "deceptive" | Medium | Medium | Start with subtle variations (different scene from the same content, not misleading imagery); be transparent ("We personalize thumbnails to show you what you might like about this title"); allow opt-out; A/B test user sentiment before wide rollout |
| AIUX-R-005 | **Co-viewing false positives cause annoyance** -- platform suggests "watching together" when only one person is present, feeling intrusive | Low | High | Set high confidence threshold (0.7); make suggestion easily dismissable (one-tap); learn from dismissals to reduce false positives for the household; never block content access based on co-viewing detection |
| AIUX-R-006 | **AI model latency causes visible UX delays** -- recommendation serving takes > 200ms, causing visible placeholder states or loading spinners | High | Medium | Cache aggressively: pre-compute home screen recommendations per profile (refreshed every 5 minutes); serve cached version immediately while fresh computation runs in background; BFF returns cached data if recommendation call exceeds 200ms timeout |
| AIUX-R-007 | **GDPR and privacy compliance gaps** -- AI data collection practices violate GDPR requirements around consent, purpose limitation, or right to deletion | High | Medium | Engage privacy counsel during architecture design; implement data minimization (collect only what models need); build consent management into onboarding; implement automated data deletion pipeline; conduct Data Protection Impact Assessment (DPIA) before launch |
| AIUX-R-008 | **Feature Store cold-start for the entire platform** -- at platform launch, there is zero historical data for any user, making Feature Store effectively empty | Medium | High | Pre-populate content features from catalog data (genres, metadata, embeddings) before launch; user features start empty but are populated from first interaction; cold-start models (content-based, onboarding quiz) do not depend on Feature Store user features; popularity features can be bootstrapped from beta/soft-launch data |

---

*This PRD defines the AI User Experience Layer -- the cross-cutting intelligence that powers personalization across every user-facing surface. It is the central AI capabilities document referenced by all service PRDs (001-006) and supported by the AI infrastructure defined in ARCH-001 and the operational AI defined in PRD-008. Implementation priority should follow the surface catalog: home screen and search in Phase 1, EPG and notifications in Phase 2, conversational search and advanced features in Phase 3.*
