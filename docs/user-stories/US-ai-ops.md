# User Stories: PRD-008 — AI Backend & Operations Intelligence

**Source PRD:** PRD-008-ai-backend-ops.md
**Generated:** 2026-02-08
**Total Stories:** 30

---

## Epic 1: Content Operations AI

### US-AIOPS-001: Automated Thumbnail Extraction and Quality Scoring

**As a** developer
**I want to** automatically extract and quality-score thumbnail candidates from ingested content
**So that** every title has high-quality thumbnail variants without manual frame selection

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** AIOPS-FR-003

**Acceptance Criteria:**
- [ ] Given a title is ingested, then 100+ candidate frames are extracted and scored by a ResNet quality model
- [ ] Given scoring completes, then the top 8 frames are selected as thumbnail variants tagged by category (action, character, atmosphere, dramatic)
- [ ] Given quality scores are evaluated, then they correlate with human quality judgment (Spearman's r > 0.7)
- [ ] Performance: Thumbnail extraction + scoring completes in < 15 minutes per title

**AI Component:** Yes -- ResNet-based quality scoring model evaluates visual quality, composition, and representativeness

**Dependencies:** Content Ingest Service, Airflow, GPU compute (T4)

**Technical Notes:**
- Runs as a step in the Airflow enrichment DAG; T4 GPU for inference; < 1 minute per 100 frames

---

### US-AIOPS-002: Content Moderation Classification

**As a** developer
**I want to** automatically classify ingested content for nudity, violence, and language intensity
**So that** content moderation is consistent and discrepancies with declared age ratings are flagged

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** AIOPS-FR-006

**Acceptance Criteria:**
- [ ] Given a title is ingested, then moderation scores (0-5) are generated for nudity, violence, and language
- [ ] Given classification accuracy is evaluated, then it exceeds 90% vs human-labeled ground truth
- [ ] Given a discrepancy between AI classification and declared age rating, then the title is flagged for human review
- [ ] Performance: Content moderation completes in < 10 minutes per title

**AI Component:** Yes -- CLIP-based multi-label classification model

**Dependencies:** Content Ingest Service, Airflow, GPU compute (A10G)

**Technical Notes:**
- Human review always required before final age rating assignment; AI results are advisory

---

### US-AIOPS-003: AI Metadata Tag Generation

**As a** developer
**I want to** automatically generate mood, theme, visual style, and pace tags for ingested content
**So that** every title has rich metadata for recommendation, search, and browse surfaces

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** AIOPS-FR-008

**Acceptance Criteria:**
- [ ] Given a title is ingested, then at minimum 3 mood tags, 3 theme tags, 1 visual style, and 1 pace classification are assigned
- [ ] Given tag accuracy is evaluated against a 500-title validation set, then accuracy exceeds 85%
- [ ] Given tags are generated, then they are stored in the Metadata Service and available for search and recommendation
- [ ] Performance: Metadata tagging completes in < 10 minutes per title (Phase 1), < 5 minutes (Phase 2)

**AI Component:** Yes -- Multi-label classification model analyzing title metadata, subtitles, audio features, and visual features

**Dependencies:** Content Ingest Service, Airflow, GPU compute (T4), Metadata Service

**Technical Notes:**
- Tags stored in Metadata Service; indexed in Elasticsearch; used as features in content embeddings for PRD-007

---

### US-AIOPS-004: Automated Subtitle Generation (Whisper STT)

**As a** developer
**I want to** automatically generate subtitles from audio using speech-to-text
**So that** subtitle availability is expanded without manual transcription

**Priority:** P1
**Phase:** 2
**Story Points:** L
**PRD Reference:** AIOPS-FR-001

**Acceptance Criteria:**
- [ ] Given a title is ingested with audio, then subtitles are generated in the original language within 2 hours
- [ ] Given clear speech content, then word error rate (WER) < 8% for Tier 1 languages
- [ ] Given high-WER results (> 12%), then the title is flagged for human review and subtitles are not auto-published

**AI Component:** Yes -- Whisper Large v3 speech-to-text model

**Dependencies:** Airflow, GPU compute (A10G), Subtitle storage

**Technical Notes:**
- ~0.5x real-time processing with Whisper Large v3 on A10G GPU; WER validated per language

---

### US-AIOPS-005: Automated Subtitle Translation

**As a** developer
**I want to** automatically translate generated subtitles to 10 target languages
**So that** multi-language subtitle coverage is expanded quickly

**Priority:** P1
**Phase:** 2
**Story Points:** M
**PRD Reference:** AIOPS-FR-002

**Acceptance Criteria:**
- [ ] Given subtitles are generated in the original language, then translations to 10 configured languages are available within 4 hours of ingest
- [ ] Given translation quality is evaluated, then BLEU score > 35 for major language pairs
- [ ] Given all translations complete, then subtitles are available across all client platforms

**AI Component:** Yes -- Transformer-based machine translation model

**Dependencies:** STT pipeline (US-AIOPS-004), Translation model (CPU-based)

**Technical Notes:**
- CPU-based transformer model; < 30 minutes for 10 languages; runs after STT step in Airflow DAG

---

### US-AIOPS-006: Scene Detection and Chapter Markers

**As a** developer
**I want to** automatically detect scene boundaries and generate chapter markers
**So that** viewers can navigate long content using chapter-based skip navigation

**Priority:** P1
**Phase:** 2
**Story Points:** M
**PRD Reference:** AIOPS-FR-005

**Acceptance Criteria:**
- [ ] Given a 2-hour movie is ingested, then 15-20 chapter markers are generated at scene boundaries
- [ ] Given boundary accuracy is evaluated, then markers are within +/- 2 seconds of actual scene changes
- [ ] Given chapter markers are generated, then they are stored as timed metadata and available to players on all platforms

**AI Component:** Yes -- Scene detection model (visual + audio transition analysis)

**Dependencies:** Content Ingest Service, Airflow, GPU compute, Catalog Service (for marker storage)

**Technical Notes:**
- GPU preferred, CPU fallback; < 20 minutes per title; markers stored in Catalog Service as timed metadata

---

### US-AIOPS-007: Content Fingerprinting for Duplicate Detection

**As a** developer
**I want to** generate audio+video fingerprints for ingested content and check for duplicates
**So that** duplicate or alternate versions of content are detected before catalog pollution

**Priority:** P1
**Phase:** 1
**Story Points:** M
**PRD Reference:** AIOPS-FR-004

**Acceptance Criteria:**
- [ ] Given a title is ingested, then an audio+video fingerprint is generated and compared against the catalog
- [ ] Given a duplicate exists, then it is flagged with > 95% recall and < 1% false positive rate
- [ ] Performance: Fingerprint generation completes in < 5 minutes per title

**AI Component:** Yes -- Audio and video fingerprinting model

**Dependencies:** Content Ingest Service, Fingerprint database, Airflow

**Technical Notes:**
- Fingerprints stored in a dedicated database; comparison performed against all existing catalog entries

---

## Epic 2: Per-Title Encoding Optimization

### US-AIOPS-008: ML-Optimized Per-Title Encoding Ladder

**As a** developer
**I want to** use an ML model to generate custom encoding ladders per title optimized for target VMAF at minimum bitrate
**So that** CDN bandwidth is reduced by 20-40% without visible quality degradation

**Priority:** P1
**Phase:** 2
**Story Points:** XL
**PRD Reference:** AIOPS-FR-010, AIOPS-FR-011, AIOPS-FR-012

**Acceptance Criteria:**
- [ ] Given a title is submitted for encoding, then the ML model generates a custom ladder per resolution tier with VMAF within +/- 2 of target (93)
- [ ] Given 100 titles are encoded, then average bitrate savings > 20% vs fixed ladder with no title below VMAF 91
- [ ] Given content is classified (high motion, low motion, high grain, clean, animated), then classification accuracy > 92%
- [ ] Performance: ML analysis completes in < 5 minutes per title (excluding actual encoding)

**AI Component:** Yes -- Custom CNN encoding optimizer that analyzes content complexity and predicts optimal bitrate per resolution tier

**Dependencies:** Encoding Pipeline, GPU compute (for analysis), VMAF measurement

**Technical Notes:**
- Model samples 50 representative frames; classifies content complexity; predicts minimum bitrate per tier; actual VMAF validated post-encode with re-encode if below 91

---

### US-AIOPS-009: Per-Title Encoding Quality Validation and Feedback Loop

**As a** developer
**I want to** validate actual VMAF scores against ML predictions and feed results back for model improvement
**So that** the encoding model continuously improves its accuracy

**Priority:** P1
**Phase:** 2
**Story Points:** M
**PRD Reference:** AIOPS-FR-013

**Acceptance Criteria:**
- [ ] Given encoding completes, then actual VMAF scores are measured and compared to ML predictions
- [ ] Given deviations are found, then they are logged with content characteristics for monthly model retraining
- [ ] Given a title has VMAF < 91 at the predicted bitrate, then it is automatically re-encoded at a higher bitrate

**AI Component:** Yes -- Feedback loop: actual results feed into model retraining

**Dependencies:** Encoding Pipeline, VMAF measurement tool, ML training pipeline

**Technical Notes:**
- Automated post-encode VMAF measurement; re-encode triggered if below quality floor; deviation logs feed SageMaker retraining

---

## Epic 3: CDN & Delivery Intelligence

### US-AIOPS-010: Predictive CDN Routing Per Session

**As a** developer
**I want to** select the optimal CDN for each playback session using an ML model
**So that** viewers get the best possible streaming quality from the CDN with lowest predicted error rate and latency

**Priority:** P1
**Phase:** 2
**Story Points:** L
**PRD Reference:** AIOPS-FR-020, AIOPS-FR-021

**Acceptance Criteria:**
- [ ] Given a playback session starts, then the CDN Routing Service selects a CDN with < 30ms additional latency
- [ ] Given the model receives input features (geo, ISP, time, CDN performance, cost tier, content type), then it produces a CDN ranking with confidence scores
- [ ] Given the model is retrained hourly, then routing decisions reflect current CDN performance
- [ ] Given model confidence < 0.6, then the system falls back to round-robin with geo-affinity

**AI Component:** Yes -- XGBoost CDN routing model trained on 90 days of session-level CDN performance data; retrained hourly

**Dependencies:** CDN provider performance APIs, Feature Store (Redis), KServe (CPU inference)

**Technical Notes:**
- Inference latency < 10ms; feature lookup < 5ms; total CDN routing budget < 30ms; in critical playback initiation path

---

### US-AIOPS-011: Mid-Session CDN Switching on QoE Degradation

**As a** viewer
**I want to** have the platform seamlessly switch my CDN mid-session if quality degrades
**So that** streaming quality recovers without me needing to restart playback

**Priority:** P1
**Phase:** 2
**Story Points:** L
**PRD Reference:** AIOPS-FR-022

**Acceptance Criteria:**
- [ ] Given a session's QoE score drops below 60 for 2 consecutive intervals, then a CDN switch is triggered
- [ ] Given a switch is triggered, then the new manifest URL is delivered to the client within 5 seconds
- [ ] Given the switch occurs, then the viewer experiences no playback interruption (seamless on next segment download)

**AI Component:** Yes -- QoE-triggered CDN switching with ML-selected alternate CDN

**Dependencies:** QoE Service, CDN Routing Service, Manifest proxy

**Technical Notes:**
- QoE alert published to Kafka; CDN Routing Service evaluates alternates; manifest proxy serves updated manifest on next client request

---

### US-AIOPS-012: Predictive Cache Warming for Live Events

**As a** developer
**I want to** pre-populate CDN edge caches before predicted live event peaks
**So that** cache hit ratio is high from the first minute of a live event

**Priority:** P1
**Phase:** 2
**Story Points:** L
**PRD Reference:** AIOPS-FR-023

**Acceptance Criteria:**
- [ ] Given a live event is scheduled in EPG for T+2 hours, then the top 20 geo/ISP combinations have warm caches by T-30 minutes
- [ ] Given cache warming is executed, then cache hit ratio for the first 5 minutes of the event > 90%
- [ ] Given the warming model runs every 30 minutes, then warming requests are sent to CDN APIs 2 hours before predicted peak

**AI Component:** Yes -- Time-series model combining EPG schedule data with historical viewership per channel per time-slot per region

**Dependencies:** EPG Service, CDN provider APIs, Historical viewership data

**Technical Notes:**
- Model runs every 30 minutes; outputs per-region per-content cache warming priority list; warming requests sent to CDN edge cache APIs

---

### US-AIOPS-013: Predictive Cache Warming for Catch-Up Content

**As a** developer
**I want to** pre-cache popular catch-up content in predicted high-demand regions
**So that** catch-up viewers get fast playback start times

**Priority:** P2
**Phase:** 2
**Story Points:** M
**PRD Reference:** AIOPS-FR-024

**Acceptance Criteria:**
- [ ] Given a program aired yesterday with high viewership, then catch-up content is pre-cached in high-demand regions
- [ ] Given cache warming is active, then cache hit ratio for catch-up content in the first hour > 85%
- [ ] Given warming predictions are generated, then they use yesterday's viewership + time-of-day patterns

**AI Component:** Yes -- Demand prediction model for catch-up content

**Dependencies:** Viewership analytics, CDN provider APIs, TSTV Service

**Technical Notes:**
- Catch-up warming runs as a separate model from live event warming; uses historical catch-up viewership patterns

---

### US-AIOPS-014: ML-Enhanced Adaptive Bitrate (ABR)

**As a** viewer
**I want to** experience fewer rebuffer events through smarter bandwidth prediction and content-aware quality decisions
**So that** streaming is smooth even on unstable connections

**Priority:** P1
**Phase:** 3
**Story Points:** XL
**PRD Reference:** AIOPS-FR-025, AIOPS-FR-026

**Acceptance Criteria:**
- [ ] Given the ML ABR is active for sports content, then framerate (60fps) is prioritized over resolution when bandwidth is constrained
- [ ] Given the ABR model predicts bandwidth for the next 10 seconds, then mean absolute error < 20%
- [ ] Given the ML ABR is active on unstable connections, then rebuffer rate decreases by > 25% vs standard ABR

**AI Component:** Yes -- ABR ML model incorporates bandwidth prediction, content type awareness, and adaptive buffer management

**Dependencies:** Player integration, bandwidth telemetry, KServe or client-side ML

**Technical Notes:**
- Decision on server-side vs client-side implementation is an open question (AIOPS-OQ-004); content type (sports vs drama) from Catalog Service metadata

---

## Epic 4: AIOps & Infrastructure Intelligence

### US-AIOPS-015: ML-Based Anomaly Detection for Backend Services

**As an** SRE engineer
**I want to** receive alerts when any backend service metric deviates significantly from its learned baseline
**So that** I detect issues in < 60 seconds rather than waiting for threshold-based alerts

**Priority:** P0
**Phase:** 2
**Story Points:** XL
**PRD Reference:** AIOPS-FR-030, AIOPS-FR-031, AIOPS-FR-032

**Acceptance Criteria:**
- [ ] Given a service's error rate exceeds 3 standard deviations from its time-of-day baseline for 2 consecutive minutes, then an alert fires within 60 seconds
- [ ] Given 30 days of data, then a per-service baseline is established accounting for daily and weekly patterns
- [ ] Given monitoring covers error rate, latency (p50/p95/p99), throughput, CPU, memory, and custom metrics, then each metric has its own anomaly model
- [ ] Given false positive rate is tracked, then it remains < 5% per service per week

**AI Component:** Yes -- Isolation Forest + seasonal decomposition (STL) per metric per service

**Dependencies:** Prometheus (metrics source), Alert Manager, PagerDuty

**Technical Notes:**
- Models retrained weekly on latest 90 days; 1-minute granularity; 2-minute sustained deviation required to avoid transient spikes

---

### US-AIOPS-016: Alert Correlation and Root Cause Suggestion

**As an** SRE engineer
**I want to** see related alerts grouped into a single incident with a root cause hypothesis
**So that** I can focus on the actual problem rather than investigating multiple symptoms

**Priority:** P1
**Phase:** 2
**Story Points:** L
**PRD Reference:** AIOPS-FR-033, AIOPS-FR-034, AIOPS-FR-035

**Acceptance Criteria:**
- [ ] Given 3 related alerts fire (CDN latency + playback error rate + QoE drop), then they are grouped into a single incident with a root cause hypothesis
- [ ] Given root cause suggestions are evaluated, then they are correct > 60% of the time (post-incident SRE review)
- [ ] Given an upstream root cause is identified, then downstream alerts are suppressed with a note linking to the parent incident
- [ ] Given alert correlation is active, then total alert volume is reduced by > 60%

**AI Component:** Yes -- Correlation model uses service dependency graph, temporal proximity, and metric co-occurrence to group alerts

**Dependencies:** Anomaly detection (US-AIOPS-015), Service dependency map, Incident Manager

**Technical Notes:**
- Correlation engine processes alerts in sliding 5-minute windows; uses pre-defined service dependency graph + learned co-occurrence patterns

---

### US-AIOPS-017: Self-Healing Automation for Known Failure Patterns

**As an** SRE engineer
**I want to** have pre-approved runbooks automatically execute remediation for known failure patterns
**So that** common incidents are resolved in < 90 seconds without human intervention

**Priority:** P1
**Phase:** 3
**Story Points:** XL
**PRD Reference:** AIOPS-FR-036, AIOPS-FR-037, AIOPS-FR-038

**Acceptance Criteria:**
- [ ] Given a known failure pattern is detected (e.g., connection pool exhaustion), then automated remediation executes within 60 seconds
- [ ] Given safety limits are enforced, then maximum 1 automated remediation per service per 15-minute window
- [ ] Given a runbook is new, then it requires SRE review and approval before activation; runbooks are version-controlled in Git
- [ ] Given remediation succeeds, then a notification is sent to SRE with full incident details for review

**AI Component:** Yes -- Pattern matching from anomaly detection triggers pre-approved runbook execution

**Dependencies:** Anomaly detection (US-AIOPS-015), Kubernetes API (for pod operations), Runbook repository (Git)

**Technical Notes:**
- Safety mechanism: 1 remediation per service per 15 minutes; second alert escalates to human; global kill switch available

---

### US-AIOPS-018: Predictive Alerting for Capacity and Resource Exhaustion

**As an** SRE engineer
**I want to** receive alerts before user-impacting failures occur for predictable issues like disk fill, capacity exhaustion, and certificate expiry
**So that** I can proactively resolve issues hours before they cause incidents

**Priority:** P1
**Phase:** 3
**Story Points:** L
**PRD Reference:** AIOPS-FR-039

**Acceptance Criteria:**
- [ ] Given a disk is filling at a predictable rate, then an alert fires at least 2 hours before 90% capacity
- [ ] Given prediction accuracy is evaluated, then predicted time is within +/- 10% of actual
- [ ] Given predictable failure modes (capacity, disk, certificates, quotas), then each has a predictive alert configured

**AI Component:** Yes -- Time-series forecasting model extrapolates resource usage trends

**Dependencies:** Prometheus (metrics), Alert Manager

**Technical Notes:**
- Linear extrapolation for simple trends; ARIMA/Prophet for seasonal patterns; alerts routed via existing Alert Manager pipeline

---

### US-AIOPS-019: ML-Based Capacity Forecasting

**As an** SRE engineer
**I want to** see predicted concurrent user demand per hour for the next 7 days
**So that** I can plan infrastructure scaling and review auto-generated scaling schedules for major events

**Priority:** P2
**Phase:** 3
**Story Points:** L
**PRD Reference:** AIOPS-FR-040

**Acceptance Criteria:**
- [ ] Given 90 days of historical data and the upcoming EPG schedule, then the model predicts hourly concurrent users for 7 days with < 15% MAPE
- [ ] Given a major event is upcoming, then an auto-generated scaling schedule is produced for SRE review and approval
- [ ] Given the scaling schedule is approved, then it executes automatically (pre-scale before event, scale-down after)

**AI Component:** Yes -- Demand forecasting model using historical viewership, EPG schedule, and engagement signals

**Dependencies:** EPG Service, Historical analytics, Kubernetes (for scaling execution)

**Technical Notes:**
- Model outputs hourly demand forecast; scaling schedule translates forecast to pod counts per service; SRE approval required before execution

---

## Epic 5: Business Intelligence AI

### US-AIOPS-020: Daily Churn Prediction Scoring

**As an** operator
**I want to** score every subscriber daily on their 30-day churn probability
**So that** the retention team can intervene before high-risk subscribers leave

**Priority:** P1
**Phase:** 2
**Story Points:** XL
**PRD Reference:** AIOPS-FR-050, AIOPS-FR-051

**Acceptance Criteria:**
- [ ] Given the model runs daily, then every subscriber has a churn probability score (0.0-1.0)
- [ ] Given actual churn outcomes are evaluated, then the model identifies > 70% of churners 30 days before churn at the 0.7 threshold
- [ ] Given precision at 0.7 threshold, then > 50% of flagged subscribers actually churn
- [ ] Given features include viewing hour decline, session frequency, support contacts, payment failures, app uninstall, and engagement trends, then all signal categories contribute

**AI Component:** Yes -- XGBoost churn classifier trained on 12 months of subscriber data; daily retraining on latest 30 days

**Dependencies:** Data lake (subscriber activity data), Feature Store, SageMaker (training)

**Technical Notes:**
- Batch job runs daily; scores up to 2 million subscribers in < 2 hours; output includes per-subscriber top 5 contributing features

---

### US-AIOPS-021: Automated Churn Retention Workflows

**As an** operator
**I want to** automatically trigger retention interventions for high-risk churn subscribers
**So that** at-risk subscribers receive timely, personalized engagement before they leave

**Priority:** P1
**Phase:** 2
**Story Points:** L
**PRD Reference:** AIOPS-FR-052

**Acceptance Criteria:**
- [ ] Given a subscriber is scored > 0.7, then within 24 hours they receive a personalized re-engagement notification with curated content
- [ ] Given a subscriber is scored > 0.85, then a retention offer is queued for retention team review
- [ ] Given retention workflows are active, then churn rate for the treated group decreases measurably vs untreated control

**AI Component:** Yes -- Churn score triggers automated workflow; personalized content recommendation from PRD-007 Recommendation Service

**Dependencies:** Churn prediction model (US-AIOPS-020), Notification Service, Recommendation Service (PRD-007)

**Technical Notes:**
- Subscribers at 0.7-0.85: soft intervention (content recommendations, feedback prompt); > 0.85: hard intervention (retention offer queued for human review)

---

### US-AIOPS-022: Dynamic Pricing Optimization

**As an** operator
**I want to** optimize subscription pricing per user segment using AI
**So that** revenue per user increases without increasing churn

**Priority:** P2
**Phase:** 3
**Story Points:** XL
**PRD Reference:** AIOPS-FR-053

**Acceptance Criteria:**
- [ ] Given the model is deployed on 10% of users via A/B test, then revenue per user in the test group increases by > 5% vs control
- [ ] Given the pricing model is active, then churn rate does not increase by > 0.5% vs control
- [ ] Given pricing decisions are generated, then they are reviewable by the business team before deployment

**AI Component:** Yes -- Pricing optimization model using engagement patterns and willingness-to-pay signals

**Dependencies:** Billing system, A/B testing framework, Analytics pipeline

**Technical Notes:**
- A/B tested with strict guardrail metrics on churn; human review required before any pricing changes go live

---

### US-AIOPS-023: Ad Optimization for AVOD Tier

**As an** operator
**I want to** optimize ad selection per viewer to maximize yield while maintaining viewer experience
**So that** ad revenue is maximized without driving viewer abandonment

**Priority:** P2
**Phase:** 2
**Story Points:** L
**PRD Reference:** AIOPS-FR-055

**Acceptance Criteria:**
- [ ] Given an AVOD viewer hits an ad break, then ad selection completes within 200ms
- [ ] Given targeted ads are served, then CPM is > 25% higher than non-targeted insertion
- [ ] Given viewer completion through ad breaks is tracked, then it exceeds 80%

**AI Component:** Yes -- Ad selection model using viewer interest profile, frequency capping, and ad pod composition optimization

**Dependencies:** SSAI service, Recommendation Service (for viewer interest profile), Ad server

**Technical Notes:**
- Uses recommendation model's viewer interest profile (from PRD-007) for ad targeting; SSAI ensures seamless insertion

---

## Epic 6: Quality of Experience Intelligence

### US-AIOPS-024: Per-Session QoE Score Computation

**As a** developer
**I want to** compute a composite quality score (0-100) for every active session every 30 seconds
**So that** platform quality is quantified and alertable in real-time

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** AIOPS-FR-060

**Acceptance Criteria:**
- [ ] Given a session is active, then QoE score is computed every 30 seconds from client-reported metrics
- [ ] Given the score formula weights start time (25%), rebuffer ratio (30%), average bitrate (20%), resolution stability (15%), and error-free (10%), then computation is consistent and deterministic
- [ ] Given 500,000 concurrent sessions, then QoE Service computes scores for all sessions within each 30-second window

**AI Component:** No (composite scoring formula, not ML)

**Dependencies:** Client telemetry (Conviva SDK), QoE Service

**Technical Notes:**
- Client sends heartbeats every 30 seconds; QoE Service aggregates and computes score; contextual adjustments for device type and content type

---

### US-AIOPS-025: QoE Segment-Level Alerting

**As an** SRE engineer
**I want to** receive alerts when QoE drops below threshold for any segment (CDN, ISP, region, device, channel)
**So that** I can identify and resolve quality issues affecting specific user groups

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** AIOPS-FR-061

**Acceptance Criteria:**
- [ ] Given QoE p25 for "ISP TelcoA, EU-West" drops to 65 (threshold: 70), then an alert fires within 2 minutes
- [ ] Given the alert fires, then it includes affected segment, current score, baseline score, estimated affected viewers, and primary contributing factor
- [ ] Given segmentation dimensions include CDN, ISP (top 20), region, device platform, channel, and content type, then all dimensions are monitored

**AI Component:** No (threshold alerting with segment analysis)

**Dependencies:** QoE Service, Alert Manager, PagerDuty

**Technical Notes:**
- Segment-level p25 computed from aggregated QoE scores; thresholds configurable per segment dimension

---

### US-AIOPS-026: Real-Time QoE Dashboards

**As an** SRE engineer
**I want to** view real-time QoE dashboards showing quality across all dimensions with 30-second refresh
**So that** I have instant visibility into platform quality during incidents and normal operations

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** AIOPS-FR-063

**Acceptance Criteria:**
- [ ] Given the dashboard is open, then overall platform QoE, per-CDN, per-ISP, per-device, and per-channel metrics are visible with 30-second data freshness
- [ ] Given a dimension is selected, then drill-down to individual session level is available
- [ ] Given historical data is available, then trend comparison (current vs same time yesterday/last week) is visible

**AI Component:** No

**Dependencies:** QoE Service, Grafana

**Technical Notes:**
- Dashboard built in Grafana consuming QoE Service metrics; pre-aggregated per dimension in Redis for fast rendering

---

### US-AIOPS-027: QoE Trend Detection for Gradual Degradation

**As an** SRE engineer
**I want to** be alerted when QoE for a segment degrades gradually over days (too slow for threshold alerts)
**So that** slow-burning quality issues are caught before they become severe

**Priority:** P1
**Phase:** 2
**Story Points:** M
**PRD Reference:** AIOPS-FR-064

**Acceptance Criteria:**
- [ ] Given QoE for a segment degrades by 5% over 7 days, then a trend alert fires with current value, 7-day-ago value, and degradation rate
- [ ] Given the trend is identified, then the alert suggests investigation of the contributing QoE component (start time, rebuffer, bitrate)
- [ ] Given trend detection runs, then it covers all segment dimensions (CDN, ISP, region, device, channel)

**AI Component:** Yes -- Trend detection model monitors multi-day QoE patterns per segment

**Dependencies:** QoE Service (historical data), Alert Manager

**Technical Notes:**
- Linear regression on 7-day rolling window per segment; alert on statistically significant negative slope

---

### US-AIOPS-028: Viewer Impact Analysis for Incidents

**As an** SRE engineer
**I want to** see the quantified user impact of every operational incident after resolution
**So that** I can prioritize post-incident improvements based on actual viewer impact

**Priority:** P1
**Phase:** 2
**Story Points:** L
**PRD Reference:** AIOPS-FR-062

**Acceptance Criteria:**
- [ ] Given an incident is resolved, then the post-incident report includes: total affected viewers, affected session minutes, QoE score degradation, % of viewers who abandoned, and estimated revenue impact
- [ ] Given impact estimation is generated, then it is available within 30 minutes of incident resolution
- [ ] Given impact data is historical, then incidents can be compared by viewer impact to prioritize improvements

**AI Component:** Yes -- Impact estimation model correlates incident timeline with viewer-level QoE and session data

**Dependencies:** QoE Service, Incident Manager, Session analytics

**Technical Notes:**
- Post-incident analysis correlates incident time window with per-session QoE data; abandonment defined as session end during incident without restart

---

## Epic 7: AI Infrastructure & Non-Functional

### US-AIOPS-029: AI Model Deployment Pipeline (Training to Production)

**As a** developer
**I want to** deploy ML models through a standardized pipeline with canary rollout and automatic rollback
**So that** model updates are safe, auditable, and reversible

**Priority:** P0
**Phase:** 1
**Story Points:** XL
**PRD Reference:** AIOPS-NFR-001 through AIOPS-NFR-007

**Acceptance Criteria:**
- [ ] Given a model is trained, then it passes automated quality gates (must exceed previous production model on all primary metrics)
- [ ] Given a model is approved, then canary deployment serves 5% of traffic for 1 hour with automated SLO check
- [ ] Given SLO is met, then promotion to 50% (4 hours) then 100% proceeds automatically
- [ ] Given SLO is violated during canary, then automatic rollback to previous version occurs

**AI Component:** Yes -- ML pipeline infrastructure

**Dependencies:** SageMaker (training), MLflow (registry), KServe (serving), monitoring system

**Technical Notes:**
- Pipeline: SageMaker training -> MLflow registration -> KServe canary deployment -> Prometheus SLO monitoring -> promotion or rollback

---

### US-AIOPS-030: AI Infrastructure Cost Monitoring and Budget Enforcement

**As an** operator
**I want to** track AI infrastructure costs per model and enforce the 15% budget cap
**So that** AI costs remain sustainable as more models are deployed

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** AIOPS-NFR-030, AIOPS-NFR-031, AIOPS-NFR-032

**Acceptance Criteria:**
- [ ] Given per-model cost tracking is active, then each model has a tracked cost-per-inference and cost-per-training-run
- [ ] Given total AI cost approaches 12% of platform cost, then a budget alert fires
- [ ] Given total AI cost reaches 15%, then escalation to engineering leadership is triggered
- [ ] Given GPU utilization is monitored, then peak utilization stays < 70% (headroom for burst)

**AI Component:** No (this monitors AI infrastructure costs)

**Dependencies:** Cloud cost attribution, GPU monitoring, Budget alerting system

**Technical Notes:**
- Cost attribution tags on all AI compute (GPU instances, SageMaker jobs, Bedrock API calls); monthly cost reports per model; spot instances for training to reduce costs

---

*End of user stories for PRD-008 (AI Backend & Operations Intelligence). Total: 30 stories covering content operations AI (7), per-title encoding (2), CDN & delivery intelligence (5), AIOps & infrastructure (5), business intelligence AI (4), QoE intelligence (5), and AI infrastructure (2).*
