# User Stories: PRD-007 — AI User Experience Layer

**Source PRD:** PRD-007-ai-user-experience.md
**Generated:** 2026-02-08
**Total Stories:** 30

---

## Epic 1: Recommendation Engine Core

### US-AIUX-001: Hybrid Recommendation Engine

**As a** viewer
**I want to** receive content recommendations that blend my viewing history, content similarity, current context, and trending signals
**So that** I discover relevant content from multiple angles -- not just "people like you watched this"

**Priority:** P0
**Phase:** 1
**Story Points:** XL
**PRD Reference:** AIUX-FR-001

**Acceptance Criteria:**
- [ ] Given a recommendation request, then the engine blends outputs from collaborative filtering, content-based, contextual, and trending models using a learned weighting function
- [ ] Given each model is invoked, then each contributes measurably to the final ranked list (no single model dominates > 60%)
- [ ] Performance: Recommendation serving latency < 100ms (p95)

**AI Component:** Yes -- Hybrid architecture combining collaborative filtering (TF Serving), content-based (pgvector embeddings), contextual (XGBoost), and trending (Redis aggregation) with a neural fusion model

**Dependencies:** Feature Store, KServe, pgvector, Redis, Kafka

**Technical Notes:**
- Parallel model invocations: collaborative < 30ms, content-based < 20ms, contextual < 15ms, trending < 5ms
- Fusion model combines outputs in < 10ms; re-ranking applies diversity injection, editorial pins, entitlement filter

---

### US-AIUX-002: Recommendation Explainability

**As a** viewer
**I want to** understand why each piece of content is recommended to me
**So that** I can trust the recommendations and provide better feedback

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** AIUX-FR-004, AIUX-AI-130

**Acceptance Criteria:**
- [ ] Given a recommendation is displayed, then a human-readable reason is included (e.g., "Because you watched X," "Trending in your area," "New in genres you love")
- [ ] Given the reason is shown, then it is contextually accurate and matches the actual scoring signals (not random or generic)
- [ ] Given a user long-presses a recommended title, then a dialog shows the reason and offers "Not Interested" and "See fewer like this" actions

**AI Component:** Yes -- Recommendation Service generates explainability strings based on the dominant scoring signal for each recommendation

**Dependencies:** Recommendation Service

**Technical Notes:**
- Reason determined by the highest-weighted model signal for each title; stored alongside the recommendation response

---

### US-AIUX-003: A/B Testing Framework for Recommendations

**As a** developer
**I want to** run A/B experiments on recommendation algorithms with consistent user assignment and statistical rigor
**So that** we can continuously improve recommendation quality with data-driven decisions

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** AIUX-FR-005

**Acceptance Criteria:**
- [ ] Given an A/B experiment with 2 variants and 5% traffic each, then user assignment is consistent across sessions (same user always sees same variant)
- [ ] Given the experiment runs for 7+ days with 10,000+ users per variant, then results include primary metric (CTR) and guardrail metric (session count) with statistical significance
- [ ] Given an experiment is declared significant, then the winning variant can be rolled out to 100% via configuration change

**AI Component:** Yes -- A/B framework manages model variant routing and metric collection

**Dependencies:** Feature flag service (Unleash), Analytics pipeline

**Technical Notes:**
- User assignment via consistent hashing on profile_id + experiment_id; sequential statistical testing for early stopping

---

### US-AIUX-004: Recommendation Diversity Injection

**As a** viewer
**I want to** see recommendations that include content outside my usual genres
**So that** I discover new types of content and do not get stuck in a filter bubble

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** AIUX-FR-030

**Acceptance Criteria:**
- [ ] Given a user primarily watches drama, then at least 15% of recommendations come from other genres the user has not explicitly rejected
- [ ] Given diversity ratio is configurable per surface (10-30%), then the configured ratio is enforced in the recommendation output
- [ ] Given a diversity pick is shown, then its recommendation reason reflects the diversity intent (e.g., "Something different you might enjoy")

**AI Component:** Yes -- Post-fusion diversity injection selects a configurable percentage from under-represented genres

**Dependencies:** Recommendation Service

**Technical Notes:**
- Diversity injection applied post-fusion and pre-re-ranking; configurable per surface

---

### US-AIUX-005: Editorial Override Capability

**As an** operator
**I want to** pin, boost, or suppress specific titles in recommendation surfaces
**So that** editorial curation works alongside AI to feature key content

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** AIUX-FR-031

**Acceptance Criteria:**
- [ ] Given an editor pins a title to the home hero banner, then the AI recommendation is overridden for that position for all targeted users
- [ ] Given a pin has a configurable time window, then the override expires automatically at the configured time
- [ ] Given a title is suppressed, then it does not appear in any recommendation surface for the suppression period

**AI Component:** No (this overrides AI)

**Dependencies:** CMS/Editorial tool, Recommendation Service re-ranking layer

**Technical Notes:**
- Editorial overrides applied in the re-ranking step after AI scoring; stored in a separate editorial config service

---

### US-AIUX-006: Recommendation Fallback to Popularity

**As a** viewer
**I want to** still see useful content recommendations when AI services are temporarily unavailable
**So that** my experience is not degraded by backend failures

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** AIUX-FR-033

**Acceptance Criteria:**
- [ ] Given the Recommendation Service is unavailable, then BFF returns popularity-based rails within 200ms
- [ ] Given the fallback is active, then the layout is visually indistinguishable from AI recommendations (same layout, no error messaging)
- [ ] Given 100% of surfaces have defined fallbacks, then automated failover testing confirms all surfaces render correctly

**AI Component:** No (this is the fallback when AI is unavailable)

**Dependencies:** BFF, pre-computed popularity rankings (Redis)

**Technical Notes:**
- Pre-computed top-100 per genre updated hourly; BFF returns cached fallback on Recommendation Service timeout (200ms)

---

## Epic 2: User Feedback & Control

### US-AIUX-007: Thumbs Up / Thumbs Down Ratings

**As a** viewer
**I want to** rate content with thumbs up or thumbs down
**So that** the platform learns my explicit preferences and improves recommendations

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** AIUX-FR-040

**Acceptance Criteria:**
- [ ] Given a user gives thumbs up on a title, then the explicit signal affects future recommendations within 1 hour
- [ ] Given a user gives thumbs down, then the title's recommendation score drops to 0 within 1 hour
- [ ] Given ratings are submitted, then they are visible in the user's profile as "Liked" and "Disliked" lists

**AI Component:** Yes -- Explicit signals ingested via Kafka and incorporated into Feature Store user features and model retraining

**Dependencies:** Recommendation Service, Feature Store, Kafka

**Technical Notes:**
- Rating events published to Kafka; Feature Store updates explicit rating features; collaborative model incorporates in next retraining cycle

---

### US-AIUX-008: Mark Content as "Not Interested"

**As a** viewer
**I want to** mark content as "Not Interested" to permanently exclude it from my recommendations
**So that** I stop seeing content I do not want to watch

**Priority:** P0
**Phase:** 1
**Story Points:** S
**PRD Reference:** AIUX-FR-041

**Acceptance Criteria:**
- [ ] Given a user marks a title as "Not Interested," then the title is permanently excluded from all recommendation surfaces for that profile
- [ ] Given the exclusion is applied, then it takes effect within the next recommendation refresh (< 1 hour)
- [ ] Given the user wants to undo, then they can find and remove exclusions in their profile settings

**AI Component:** Yes -- Exclusion list maintained per profile in Feature Store; applied as a hard filter in re-ranking

**Dependencies:** Profile Service, Recommendation Service

**Technical Notes:**
- Exclusion stored in Profile Service and cached in Feature Store; applied as a blocklist in re-ranking

---

### US-AIUX-009: Genre Exclusion from Recommendations

**As a** viewer
**I want to** exclude specific genres from my recommendations entirely
**So that** I never see content from genres I dislike across any recommendation surface

**Priority:** P1
**Phase:** 2
**Story Points:** M
**PRD Reference:** AIUX-FR-043

**Acceptance Criteria:**
- [ ] Given a user excludes "Horror," then no horror titles appear in any recommendation surface for that profile
- [ ] Given the exclusion is set, then it takes effect within 1 hour across all surfaces
- [ ] Given the user changes their mind, then removing the exclusion restores horror titles in recommendations

**AI Component:** Yes -- Genre exclusion applied as a hard filter in recommendation re-ranking

**Dependencies:** Profile Service, Recommendation Service

**Technical Notes:**
- Genre exclusions stored in Profile Service; applied as a filter in the re-ranking step

---

### US-AIUX-010: Reset Recommendation Profile

**As a** viewer
**I want to** reset my recommendation profile and start fresh
**So that** I can clear stale preferences and redo the onboarding process

**Priority:** P1
**Phase:** 2
**Story Points:** M
**PRD Reference:** AIUX-FR-042

**Acceptance Criteria:**
- [ ] Given a user resets recommendations, then all viewing history signals are cleared from the recommendation model for that profile
- [ ] Given the reset completes, then the onboarding quiz is presented again
- [ ] Given the user completes the quiz, then new personalized recommendations are generated based on fresh quiz answers

**AI Component:** Yes -- Feature Store entries for the profile are purged; model treats user as cold-start

**Dependencies:** Feature Store, Profile Service, Recommendation Service

**Technical Notes:**
- Profile-level feature purge in Feature Store; data deletion propagated through ML pipeline

---

### US-AIUX-011: GDPR Data Deletion for Personalization

**As a** viewer
**I want to** request deletion of all my personalization data
**So that** my right to erasure under GDPR is respected

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** AIUX-AI-134

**Acceptance Criteria:**
- [ ] Given a user exercises their right to deletion, then all personal data in the recommendation pipeline (Feature Store entries, model training data contributions, explicit ratings) is purged within 30 days
- [ ] Given deletion completes, then a confirmation is sent to the user
- [ ] Given data is deleted, then the user's future experience uses only non-personalized content

**AI Component:** Yes -- Data deletion pipeline purges personalization data across Feature Store, training data lake, and model serving cache

**Dependencies:** Data Platform, Feature Store, Profile Service

**Technical Notes:**
- Automated GDPR deletion pipeline triggered by user request; spans Feature Store (Redis), data lake, model training data, and Kafka topics

---

## Epic 3: Cold-Start & Onboarding

### US-AIUX-012: New User Onboarding Taste Quiz

**As a** viewer (new user)
**I want to** complete a quick taste quiz on first launch
**So that** the platform immediately understands my preferences and shows relevant content

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** AIUX-AI-120, AIUX-FR-020

**Acceptance Criteria:**
- [ ] Given a new user opens the app, then a 3-step quiz appears: genre selection (12 genres), title recognition (20 popular titles), and viewing context (alone/family/both)
- [ ] Given the quiz is presented, then completion rate > 70% and completion time < 60 seconds
- [ ] Given a skip option is available, then users who skip receive popularity-based recommendations

**AI Component:** Yes -- Quiz answers feed the cold-start model to generate immediate personalized recommendations

**Dependencies:** Recommendation Service (cold-start model), Profile Service

**Technical Notes:**
- Quiz responses stored in Profile Service; cold-start model generates initial taste vector from responses

---

### US-AIUX-013: Immediate Post-Quiz Personalization

**As a** viewer (new user)
**I want to** see personalized content immediately after completing the onboarding quiz
**So that** my first experience feels tailored rather than generic

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** AIUX-AI-121, AIUX-FR-021

**Acceptance Criteria:**
- [ ] Given a new user completes the quiz, then the home screen loads within 2 seconds with personalized rails based on quiz answers
- [ ] Given recommendations are shown, then they are measurably different from the default popularity baseline (CTR > 12% vs 8% random)
- [ ] Given the home screen loads, then at minimum 4 personalized rails are displayed

**AI Component:** Yes -- Cold-start content-based model generates recommendations from quiz-derived taste vector; no collaborative filtering data needed

**Dependencies:** Recommendation Service, Catalog Service

**Technical Notes:**
- Cold-start model uses content embeddings matched against quiz-derived preference vector; no dependency on other user data

---

### US-AIUX-014: Cold-Start to Hybrid Model Transition

**As a** viewer (new user)
**I want to** see my recommendations improve naturally as I watch more content
**So that** the experience becomes more personalized over time without any disruption

**Priority:** P1
**Phase:** 1
**Story Points:** M
**PRD Reference:** AIUX-FR-023

**Acceptance Criteria:**
- [ ] Given a new user has completed 5 plays across 3 sessions, then the recommendation model switches from cold-start to full hybrid
- [ ] Given the transition occurs, then it is seamless with no visible disruption or quality regression
- [ ] Given the threshold is configurable, then different values can be set per market or user segment

**AI Component:** Yes -- Model routing switches from cold-start to hybrid based on implicit signal count

**Dependencies:** Recommendation Service, Feature Store

**Technical Notes:**
- Feature Store tracks play count and session count per profile; routing logic in Recommendation Service checks threshold before selecting model

---

## Epic 4: Personalized Discovery

### US-AIUX-015: Personalized Home Hero Banner

**As a** viewer
**I want to** see a hero banner personalized to my interests each time I open the app
**So that** the first thing I see is compelling and relevant

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** AIUX-AI-001, AIUX-FR-010

**Acceptance Criteria:**
- [ ] Given 2 different users open the app, then each sees a different hero title (unless editorially pinned for all)
- [ ] Given the hero is personalized, then hero CTR > 15% (vs 8% for non-personalized baseline)
- [ ] Given a hero title pool of 20-50 eligible titles, then the model selects the top match for each user per session

**AI Component:** Yes -- Recommendation model scores hero-eligible titles per user; selects top match with engagement optimization objective

**Dependencies:** Recommendation Service, Catalog Service, CMS (editorial pool management)

**Technical Notes:**
- Hero pool managed by editorial team; AI scores and ranks within the pool; multi-armed bandit for creative variant selection (Phase 2)

---

### US-AIUX-016: Personalized Thumbnail Selection

**As a** viewer
**I want to** see thumbnail images for titles that appeal to my visual preferences
**So that** content looks more attractive and I am more likely to discover new titles

**Priority:** P1
**Phase:** 2
**Story Points:** L
**PRD Reference:** AIUX-AI-010, AIUX-AI-011, AIUX-AI-012

**Acceptance Criteria:**
- [ ] Given a title has 4+ thumbnail variants, then each user sees the variant predicted to have the highest CTR for their segment
- [ ] Given a new title launches with 4 variants, then within 7 days the system converges on the best variant per user segment with < 5% regret
- [ ] Given thumbnail selection is active, then CTR improves by > 10% vs random variant assignment

**AI Component:** Yes -- Multi-armed bandit (Thompson Sampling) learns per-user-segment click-through rates per thumbnail category

**Dependencies:** Content Enrichment Pipeline (thumbnail generation), Recommendation Service

**Technical Notes:**
- Thumbnail variants generated during ingest; each tagged by category (action, character, atmosphere, dramatic); bandit updates in near-real-time

---

### US-AIUX-017: Conversational Search

**As a** binge watcher
**I want to** search for content using natural language descriptions like "dark sci-fi with a female lead"
**So that** I can find exactly what I want without knowing the title

**Priority:** P1
**Phase:** 3
**Story Points:** XL
**PRD Reference:** AIUX-AI-020, AIUX-AI-021, AIUX-AI-022, AIUX-AI-023

**Acceptance Criteria:**
- [ ] Given a query "dark sci-fi with a female lead, like Severance but more horror," then results include semantically matching titles
- [ ] Given a follow-up query "but not too violent," then results are refined contextually (session context maintained)
- [ ] Given each result is shown, then a one-line AI-generated match explanation is displayed
- [ ] Given Bedrock is unavailable, then search falls back to keyword-based Elasticsearch with no visible error
- [ ] Performance: Conversational search latency < 2 seconds (p95)

**AI Component:** Yes -- Bedrock LLM extracts intent and entities; pgvector embedding similarity for content matching; reciprocal rank fusion combines keyword and semantic results

**Dependencies:** Search Service, Bedrock (LLM), Elasticsearch, pgvector

**Technical Notes:**
- Session context (last 3 queries) stored in Redis with 30-minute TTL; LLM generates structured queries grounded against catalog

---

### US-AIUX-018: Mood-Based Browse

**As a** casual viewer
**I want to** browse content by mood (Relaxing, Exciting, Funny, etc.) instead of traditional genres
**So that** I can find content matching how I feel right now

**Priority:** P1
**Phase:** 2
**Story Points:** L
**PRD Reference:** AIUX-AI-030, AIUX-AI-031

**Acceptance Criteria:**
- [ ] Given a user selects "Relaxing," then results include titles tagged with the "relaxing" mood by the content intelligence pipeline
- [ ] Given results are shown, then they span all content sources (VOD, catch-up, live programs)
- [ ] Given mood tags are AI-generated, then accuracy > 80% vs human-labeled ground truth

**AI Component:** Yes -- Content enrichment pipeline assigns mood tags via analysis of metadata, subtitles, audio, and visual features

**Dependencies:** Content Enrichment Pipeline, Catalog Service, Recommendation Service

**Technical Notes:**
- Mood tags stored as content features in Catalog Service; browse queries filter by mood tag and rank by personalized relevance

---

### US-AIUX-019: Weekly Personalized Content Digest

**As a** viewer
**I want to** receive a weekly personalized digest of new and relevant content
**So that** I stay informed about content worth watching without checking the app daily

**Priority:** P1
**Phase:** 2
**Story Points:** L
**PRD Reference:** AIUX-AI-040, AIUX-AI-041, AIUX-AI-042

**Acceptance Criteria:**
- [ ] Given Saturday arrives, then each profile receives a digest with 5 personalized picks via in-app notification (and optionally email)
- [ ] Given a title matching the user's taste is expiring within 7 days, then the digest includes it with a "Leaving Soon" badge
- [ ] Given 1 of 5 picks is a diversity injection from outside the user's primary genres, then this is included

**AI Component:** Yes -- Batch recommendation job generates per-profile digest; diversity injection applied; urgency signals from catalog expiry data

**Dependencies:** Recommendation Service (batch mode), Notification Service, Catalog Service

**Technical Notes:**
- Weekly batch job runs Saturday morning; generates digests for all active profiles; delivery via Notification Service and email service

---

## Epic 5: Viewing Intelligence

### US-AIUX-020: Co-Viewing Detection and Adapted Recommendations

**As a** parent
**I want to** have the platform detect when my family is watching together and adapt recommendations accordingly
**So that** we see content suitable for everyone without manual profile switching

**Priority:** P1
**Phase:** 2
**Story Points:** L
**PRD Reference:** AIUX-AI-050, AIUX-AI-051, AIUX-AI-052, AIUX-AI-053

**Acceptance Criteria:**
- [ ] Given a known co-viewing time, then the detection model correctly identifies co-viewing > 70% of the time (precision)
- [ ] Given co-viewing is detected, then recommendations blend interests of likely-present viewers (neither dominates)
- [ ] Given a child profile is part of the detected group, then all content is filtered to the child's age restriction
- [ ] Given a user taps "Watch Together," then co-viewing mode activates immediately regardless of detection model output

**AI Component:** Yes -- XGBoost classifier detects co-viewing from time, device, day-of-week, and household history; retrained weekly per household

**Dependencies:** Recommendation Service, Profile Service

**Technical Notes:**
- Detection runs at session start; confidence threshold > 0.7; user can toggle manually at any time

---

### US-AIUX-021: Smart Continue Watching Ordering

**As a** binge watcher
**I want to** see my "Continue Watching" rail ordered by what I am most likely to resume next
**So that** the most relevant in-progress title is always first

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** AIUX-AI-070, AIUX-AI-071

**Acceptance Criteria:**
- [ ] Given a user has 5 in-progress titles, then "Continue Watching" is ordered by: recency, completion proximity, new episode availability, and time-of-day patterns
- [ ] Given a title has not been watched for 30+ days, then it is auto-archived to a "Paused Shows" section
- [ ] Given the user wants to restore an archived title, then they can do so with one tap from the "See Paused Shows" link

**AI Component:** Yes -- Scoring model considers recency, completion proximity, new content availability, and contextual time-of-day patterns

**Dependencies:** Bookmark Service, Recommendation Service, Catalog Service

**Technical Notes:**
- Smart ordering applied in BFF using Recommendation Service scoring; auto-archive check runs on each home screen load

---

### US-AIUX-022: Auto-Archive with Content Awareness

**As a** viewer
**I want to** keep seeing a paused show in Continue Watching if a new season just dropped
**So that** I am reminded to pick it back up when there is new content

**Priority:** P1
**Phase:** 2
**Story Points:** S
**PRD Reference:** AIUX-AI-072

**Acceptance Criteria:**
- [ ] Given a series has not been watched for 40 days BUT a new season was released 2 days ago, then the title remains in Continue Watching with a "New Season" badge
- [ ] Given no new content is available for a 40-day-old paused title, then it is auto-archived normally
- [ ] Given the new season badge is shown, then it is based on Catalog Service metadata for new releases

**AI Component:** Yes -- Auto-archive logic checks catalog for new content releases before archiving

**Dependencies:** Catalog Service, Recommendation Service

**Technical Notes:**
- New content check queries Catalog Service for release events on the title's series; if recent release found, archiving is suppressed

---

### US-AIUX-023: Skip Intro and Skip Recap

**As a** binge watcher
**I want to** skip intros and recaps with one tap when binge-watching a series
**So that** I can get to the new content faster

**Priority:** P1
**Phase:** 2
**Story Points:** L
**PRD Reference:** AIUX-AI-080, AIUX-AI-081, AIUX-AI-082

**Acceptance Criteria:**
- [ ] Given a series episode has an AI-detected intro, then a "Skip Intro" button appears 3 seconds into the intro and disappears when it ends
- [ ] Given skip boundary accuracy, then it is within +/- 3 seconds of the actual intro boundaries
- [ ] Given detection uses audio fingerprinting + visual analysis, then accuracy > 90% across a season

**AI Component:** Yes -- Audio fingerprinting + visual analysis model detects intro and recap boundaries during content enrichment

**Dependencies:** Content Enrichment Pipeline, Player

**Technical Notes:**
- Intro/recap markers generated during ingest; stored as timed metadata in Catalog Service; player reads markers and renders skip button

---

## Epic 6: Content Intelligence

### US-AIUX-024: Automated Content Tagging

**As a** viewer
**I want to** discover content through rich tags like mood, theme, and visual style
**So that** I can find content that matches what I want beyond simple genre categories

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** AIUX-AI-090

**Acceptance Criteria:**
- [ ] Given a title is ingested, then AI-generated tags for mood, theme, visual style, pace, and content warnings are produced
- [ ] Given tag accuracy is evaluated, then it exceeds 85% vs human-labeled ground truth on a 500-title validation set
- [ ] Given tags are generated, then they are available for search, recommendation, and browse surfaces

**AI Component:** Yes -- Content enrichment pipeline analyzes metadata, subtitles, audio, and visual features to generate tags

**Dependencies:** Content Enrichment Pipeline, Metadata Service

**Technical Notes:**
- Tags stored in Metadata Service; indexed in Elasticsearch and used as features in content embeddings

---

### US-AIUX-025: AI-Generated Content Summaries

**As a** viewer
**I want to** read useful descriptions for all content, even titles without editorial summaries
**So that** I can decide whether to watch any title based on an informative synopsis

**Priority:** P1
**Phase:** 2
**Story Points:** M
**PRD Reference:** AIUX-AI-091

**Acceptance Criteria:**
- [ ] Given a program has no editorial synopsis or one < 50 characters, then an AI-generated summary of 2-3 sentences is created
- [ ] Given summaries are evaluated, then editorial team rates > 90% as "acceptable or better"
- [ ] Given summary generation is part of ingest, then summaries are stored in the Metadata Service (not generated on-the-fly)

**AI Component:** Yes -- Bedrock LLM generates summaries from available metadata (title, genre, cast, existing short description)

**Dependencies:** Content Enrichment Pipeline, Bedrock, Metadata Service

**Technical Notes:**
- Summaries generated at ingest time; quality validated by periodic editorial review; stored alongside editorial summaries in Metadata Service

---

### US-AIUX-026: Embedding-Based Content Similarity

**As a** viewer
**I want to** see "More Like This" suggestions that go beyond genre to match narrative themes, visual style, and tone
**So that** I discover deeply similar content that I actually enjoy

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** AIUX-AI-092, AIUX-FR-018

**Acceptance Criteria:**
- [ ] Given a user views "More Like This" for a title, then results include titles with similar themes, visual style, and emotional tone
- [ ] Given similarity uses 768-dimensional content embeddings, then top-50 retrieval from pgvector completes in < 20ms
- [ ] Given human relevance evaluation, then average rating > 3.5/5

**AI Component:** Yes -- Content embeddings generated from metadata and AI tags; pgvector HNSW index for nearest-neighbor retrieval

**Dependencies:** pgvector, Content Enrichment Pipeline, Recommendation Service

**Technical Notes:**
- Embeddings generated on content ingest; stored in pgvector; HNSW index for fast approximate nearest-neighbor search

---

## Epic 7: Proactive Engagement

### US-AIUX-027: AI-Timed Smart Notifications

**As a** viewer
**I want to** receive notifications timed to when I am most likely to watch
**So that** notifications arrive when they are useful, not disruptive

**Priority:** P0
**Phase:** 2
**Story Points:** L
**PRD Reference:** AIUX-AI-100, AIUX-AI-101, AIUX-AI-102

**Acceptance Criteria:**
- [ ] Given a new episode of a followed series is available, then a notification is sent within 1 hour during the user's preferred notification window
- [ ] Given a user typically opens notifications between 7-8 PM, then notifications are scheduled within that window
- [ ] Given a profile has received 5 notifications this week, then no additional notifications are sent

**AI Component:** Yes -- Notification timing model predicts optimal delivery time per user from historical engagement patterns; frequency capping enforced

**Dependencies:** Notification Service, Recommendation Service, Catalog Service

**Technical Notes:**
- Notification scheduler runs as a batch job; reads user engagement patterns from Feature Store; frequency cap per profile per week

---

### US-AIUX-028: Notification Preferences and Control

**As a** viewer
**I want to** configure which types of notifications I receive and set quiet hours
**So that** I only get notifications that I want and never during my sleep hours

**Priority:** P0
**Phase:** 2
**Story Points:** M
**PRD Reference:** AIUX-AI-103

**Acceptance Criteria:**
- [ ] Given a user sets quiet hours from 10 PM to 8 AM, then no notifications are delivered during that window
- [ ] Given a user disables "recommendation" notifications but keeps "new episodes," then only new episode notifications are delivered
- [ ] Given preferences are saved, then they apply across all devices for that profile

**AI Component:** No (this is the user control layer for AI notifications)

**Dependencies:** Profile Service, Notification Service

**Technical Notes:**
- Preferences stored in Profile Service; Notification Service reads preferences before delivery

---

### US-AIUX-029: Re-Engagement for Inactive Users

**As an** operator
**I want to** send a single personalized re-engagement notification to users inactive for 14+ days
**So that** lapsed users are reminded of content waiting for them

**Priority:** P1
**Phase:** 2
**Story Points:** M
**PRD Reference:** AIUX-AI-110, AIUX-AI-111

**Acceptance Criteria:**
- [ ] Given a user has been inactive for 14 days, then a re-engagement notification with a specific content suggestion is sent
- [ ] Given the notification is sent, then re-engagement rate > 10% (app open + play within 30 minutes)
- [ ] Given the user does not return after the notification, then no second notification is sent for at least 30 days

**AI Component:** Yes -- Recommendation Service generates a personalized re-engagement suggestion; inactivity detection from analytics pipeline

**Dependencies:** Notification Service, Recommendation Service, Analytics pipeline

**Technical Notes:**
- Batch job runs daily; identifies users inactive 14+ days; generates one re-engagement notification with personalized content pick

---

## Epic 8: Ethical AI & Non-Functional

### US-AIUX-030: Parental Control Enforcement Across All AI Surfaces

**As a** parent
**I want to** be certain that AI recommendations on my child's profile never show age-inappropriate content
**So that** parental controls are respected regardless of what the AI model predicts

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** AIUX-AI-132

**Acceptance Criteria:**
- [ ] Given a child profile with PG restriction, then no content rated above PG appears in any recommendation, search result, or notification
- [ ] Given parental controls are enforced, then they override AI scoring at the re-ranking step (hard filter)
- [ ] Given edge cases (content with missing age rating), then such content is excluded from child profiles by default

**AI Component:** Yes -- Parental control filtering applied as a hard constraint in the recommendation re-ranking pipeline

**Dependencies:** Profile Service (age restrictions), Recommendation Service, Search Service

**Technical Notes:**
- Age rating filter applied post-scoring in re-ranking; content with missing ratings treated as "adult" by default

---

### US-AIUX-031: Recommendation Service Scalability

**As a** developer
**I want to** ensure the Recommendation Service handles target throughput with acceptable latency
**So that** personalization works for all concurrent users without degradation

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** AIUX-NFR-010, AIUX-NFR-011

**Acceptance Criteria:**
- [ ] Given Phase 1 target of 3,000 RPS, then load tests pass with recommendation latency < 100ms (p95)
- [ ] Given 500,000 concurrent users at Phase 4, then each receives a unique personalized response
- [ ] Given GPU utilization on KServe inference nodes, then peak utilization stays < 70%

**AI Component:** Yes -- ML model serving at scale

**Dependencies:** KServe, Feature Store (Redis), Kubernetes GPU nodes

**Technical Notes:**
- Horizontal scaling of model serving pods; Feature Store caching reduces repeated lookups; load test with realistic recommendation request patterns

---

### US-AIUX-032: Model Monitoring and Drift Detection

**As a** developer
**I want to** detect when recommendation model quality degrades due to data or concept drift
**So that** model issues are caught and corrected before impacting users

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** AIUX-NFR-020, AIUX-NFR-021

**Acceptance Criteria:**
- [ ] Given data drift is detected (KL divergence > 0.1 on input features), then an alert fires
- [ ] Given model drift is detected (mean prediction score shifts > 10%), then an alert fires
- [ ] Given a drift alert fires, then an automated retraining pipeline is queued with human review required before deployment

**AI Component:** Yes -- Monitoring system tracks feature and prediction distributions; automated retraining trigger

**Dependencies:** ML pipeline, monitoring system (Prometheus/Grafana)

**Technical Notes:**
- KL divergence computed on hourly feature batches; prediction score distribution tracked per model variant; alerts via PagerDuty

---

*End of user stories for PRD-007 (AI User Experience Layer). Total: 30 stories covering recommendation engine (6), user feedback & control (5), cold-start (3), personalized discovery (5), viewing intelligence (4), content intelligence (3), proactive engagement (3), and ethical AI & non-functional (3).*
