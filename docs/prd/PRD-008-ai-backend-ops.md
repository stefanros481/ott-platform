# PRD-008: AI Backend & Operations Intelligence

**Document ID:** PRD-008
**Version:** 1.0
**Date:** 2026-02-08
**Status:** Draft
**Author:** PRD Writer B Agent
**References:** VIS-001 (Project Vision & Design), ARCH-001 (Platform Architecture)
**Audience:** Engineering (AI/ML, Backend, SRE, Platform), Product Management

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

The AI Backend & Operations Intelligence layer powers the invisible AI that users never see but always benefit from. While PRD-007 covers AI that enhances user-facing surfaces (recommendations, search, personalization), this PRD covers AI that optimizes how the platform itself operates: content processing, delivery infrastructure, incident management, and business intelligence.

This layer encompasses five domains:
1. **Content Operations AI** -- Automated ingest enrichment, per-title encoding optimization, and AI metadata generation
2. **CDN & Delivery Intelligence** -- Predictive CDN routing, predictive cache warming, and ML-enhanced adaptive bitrate
3. **AIOps & Infrastructure Intelligence** -- Anomaly detection, predictive alerting, self-healing automation, and capacity planning
4. **Business Intelligence AI** -- Churn prediction, dynamic pricing, content valuation, and ad optimization
5. **Quality of Experience Intelligence** -- Real-time QoE scoring, QoE-driven alerting, and viewer impact analysis

These capabilities collectively reduce operational costs, improve streaming quality, predict and prevent incidents, and generate actionable business intelligence -- enabling a team of 10 SRE engineers to manage infrastructure that traditionally requires 50.

### Business Context

Operational costs represent 30-40% of a streaming platform's total expenditure. Of that, CDN bandwidth (40%), encoding compute (20%), and operational labor (15%) are the three largest components. AI-driven optimization across these areas can yield 20-40% cost reduction while simultaneously improving quality of experience.

The AIOps capabilities are equally critical: industry average mean-time-to-detect (MTTD) for streaming quality issues is 8-15 minutes, with mean-time-to-resolve (MTTR) of 30-60 minutes. During that window, thousands of viewers experience degraded quality or outages. Predictive alerting and self-healing automation can reduce MTTD to under 60 seconds and MTTR to under 5 minutes, with 40% of incidents auto-remediated without human intervention.

### Scope

**In Scope:**
- Automated content enrichment pipeline (subtitle generation, thumbnail extraction, fingerprinting, scene detection, moderation, audio analysis)
- Per-title encoding optimization (ML-predicted encoding ladders)
- AI metadata enrichment (automated tagging, mood classification, content graph)
- Predictive CDN routing (per-session optimal CDN selection)
- Predictive cache warming (EPG-driven and pattern-driven cache pre-population)
- ML-enhanced ABR (content-aware adaptive bitrate decisions)
- Anomaly detection (per-service ML-based baselining and deviation alerting)
- Predictive alerting (alert before user impact)
- Self-healing automation (automated remediation for known failure patterns)
- Capacity planning (ML-based demand forecasting)
- Churn prediction (subscriber-level churn risk scoring)
- Dynamic pricing (AI-optimized subscription pricing, Phase 3)
- Content valuation (predicted ROI for content acquisition, Phase 4)
- QoE scoring (per-session composite quality metric)
- QoE-driven alerting (alert on quality degradation by segment)
- Viewer impact analysis (quantify user impact of incidents)

**Out of Scope:**
- User-facing AI features (recommendations, search, personalization) -- see PRD-007
- AI infrastructure provisioning (KServe, Feature Store setup) -- see ARCH-001
- Manual content operations workflows (editorial metadata, manual QC)
- Financial systems and billing (churn prediction outputs feed into these, but the systems themselves are out of scope)

---

## 2. Goals & Non-Goals

### Goals

1. **Reduce content processing time from 4-8 hours to 30 minutes** (at 18-month maturity) through fully automated AI enrichment pipeline
2. **Achieve 20-40% CDN bandwidth savings** through per-title encoding optimization
3. **Reduce MTTD from 8-15 minutes to < 60 seconds** through ML-based anomaly detection
4. **Reduce MTTR from 30-60 minutes to < 5 minutes** through predictive alerting and self-healing automation
5. **Auto-remediate 40% of incidents** without human intervention by Phase 4
6. **Identify 70%+ of churning subscribers 30 days before churn event** through ML-based churn prediction
7. **Maintain QoE score (p50) above 88** across all sessions through real-time QoE intelligence
8. **Keep AI infrastructure costs below 15% of total platform cost** while delivering all capabilities

### Non-Goals

- Replacing the SRE team entirely -- AI augments human operators, it does not eliminate them
- Building a general-purpose ML platform -- AI infrastructure serves platform-specific use cases only
- Real-time content creation or generation (AI-generated videos, synthetic content)
- Full marketing automation (email campaigns, social media) -- only churn-triggered content recommendations are in scope
- Replacing third-party observability tools (Conviva, Prometheus) -- AI layers on top of existing tooling

---

## 3. User Scenarios

The "users" for this PRD are primarily internal operators: SRE engineers, content operations teams, business analysts, and ML engineers. End users benefit indirectly through improved quality and reduced costs.

### Scenario 1: Automated Content Enrichment Pipeline

**Persona:** Content Operations Team
**Context:** A new VOD title is ingested into the platform

A content partner delivers a new movie as a mezzanine file via S3. The automated enrichment pipeline kicks in:

1. **Subtitle generation (Whisper):** AI transcribes audio in the original language, then translates to 10 target languages. Subtitles are available within 2 hours of ingest.
2. **Thumbnail extraction:** 200 candidate frames are extracted. A ResNet quality scoring model evaluates each for visual quality, composition, and representativeness. The top 8 frames become thumbnail variants, each tagged by category (action, character, atmosphere, dramatic).
3. **Content fingerprinting:** An audio+video fingerprint is generated and compared against the existing catalog to detect duplicates or alternate versions.
4. **Scene detection:** AI identifies scene boundaries and generates chapter markers. For a 2-hour movie, approximately 15-20 chapters are created.
5. **Content moderation:** A CLIP-based model classifies the content for nudity, violence, and language intensity on a 0-5 scale. Results are compared against the content's declared age rating for consistency.
6. **Audio normalization analysis:** Audio levels are analyzed for compliance with EBU R128 loudness standards. Non-compliant segments are flagged for correction.
7. **AI metadata tags:** Mood (suspenseful, uplifting, melancholic), themes (redemption, family, revenge), visual style (noir, vibrant, minimalist), and pace (slow, moderate, fast) are assigned.

The content operations team receives a summary: "Title 'X' enriched. 10 subtitle languages, 8 thumbnails, 17 chapters, moderation: Violence 3/5 (matches PG-13 rating). Ready for catalog." A human reviews the moderation results and approves for publication. Total processing time: 90 minutes (vs 4-8 hours manually).

### Scenario 2: Per-Title Encoding Optimization

**Persona:** Encoding Pipeline / CDN Operations
**Context:** Same new VOD title entering the encoding pipeline

Before encoding begins, the per-title encoding ML model analyzes the content:
- It samples 50 representative frames across the movie
- It classifies content complexity: high motion (action scenes), low motion (dialogue), high grain (film look), clean (digital)
- For each segment, it predicts the minimum bitrate needed to achieve VMAF 93 at each resolution tier

**Result:** Instead of the fixed encoding ladder (8 Mbps for 1080p HEVC), the model determines this particular film (a quiet drama with minimal motion) only needs 3.2 Mbps at 1080p to achieve VMAF 93. Across the full ladder:

| Profile | Fixed Ladder | Per-Title Ladder | Savings |
|---------|-------------|-----------------|---------|
| 1080p HEVC | 4,500 kbps | 3,200 kbps | 29% |
| 720p HEVC | 2,500 kbps | 1,800 kbps | 28% |
| 540p HEVC | 1,200 kbps | 850 kbps | 29% |
| 360p HEVC | 600 kbps | 420 kbps | 30% |

For this title, CDN bandwidth is reduced by approximately 29%. Across the catalog, the average saving is 25-35% (action content saves less; drama and documentary save more).

### Scenario 3: Predictive CDN Routing During Live Event

**Persona:** CDN Operations / Automated System
**Context:** Champions League semi-final, 200,000 concurrent viewers

A major football match starts at 8 PM. The CDN routing intelligence has been preparing since 6 PM:

1. **Predictive cache warming:** Based on EPG schedule data and historical viewing patterns for Champions League matches, the system pre-populated CDN edge caches in the top 20 ISP/region combinations 2 hours before kick-off.
2. **Initial routing:** At 8 PM, the CDN Routing Service assigns viewers to CDN providers based on real-time performance data: Akamai handles 60% (strong European PoPs), CloudFront handles 30% (good fallback), Fastly handles 10% (specific regions where it performs best).
3. **Mid-match adaptation:** At 8:25 PM, QoE telemetry shows Akamai latency increasing in the UK region (likely congestion). The routing model detects the trend and starts shifting UK traffic to CloudFront. Within 3 minutes, 15,000 UK viewers are seamlessly switched -- they notice no quality degradation because the switch happens during the next manifest refresh.
4. **Post-match CDN analysis:** After the match, the system reports: cache hit ratio 97%, average QoE score 86, CDN switches 3 (all proactive, before user impact), estimated bandwidth cost $8,400.

### Scenario 4: AIOps -- Anomaly Detection and Self-Healing

**Persona:** SRE On-Call Engineer
**Context:** Tuesday 3 AM, Playback Session Service experiencing elevated error rate

1. **Anomaly detection (T+0s):** The ML anomaly detection model (trained on 90 days of per-service behavior) detects that the Playback Session Service error rate has risen from its baseline of 0.1% to 0.8%. This is 4 standard deviations above normal for this time-of-day. Alert fires within 45 seconds.

2. **Correlation (T+15s):** The alert correlation engine identifies that the Bookmark Service (a downstream dependency) is also showing elevated latency. The Entitlement Service is healthy. Root cause hypothesis: Bookmark Service database connection pool exhaustion is causing Playback Session Service errors when it fails to write bookmarks.

3. **Self-healing attempt (T+30s):** The self-healing system identifies a matching runbook: "Bookmark Service connection pool exhaustion → restart Bookmark Service pods with increased connection pool." It triggers an automated rolling restart of Bookmark Service pods with the remediation configuration.

4. **Resolution (T+90s):** Bookmark Service pods restart with the increased pool size. Error rates return to baseline within 60 seconds. Total incident duration: 90 seconds (vs 30-60 minutes with human investigation).

5. **SRE notification (T+120s):** The on-call engineer receives a PagerDuty notification: "Incident auto-remediated: Bookmark Service connection pool exhaustion → automated restart. Error rate: 0.8% peak → 0.1% resolved. Viewer impact: ~400 bookmark write failures, no playback interruptions. Please review." The SRE reviews the incident log in the morning, approves the remediation, and creates a ticket to investigate the root cause of pool exhaustion.

### Scenario 5: Churn Prediction and Intervention

**Persona:** Business Intelligence / Retention Team
**Context:** Monthly churn prediction model run

The churn prediction model runs daily, scoring every subscriber on their probability of churning within 30 days. Today's run identifies 2,300 subscribers with churn probability > 0.7 (high risk).

The model's top churn signals for this cohort:
- 65% have declined in viewing hours per week (avg -40% over 4 weeks)
- 42% have had 2+ support contacts in the past month
- 38% have not opened the app in 7+ days
- 28% are approaching the end of a promotional pricing period

The retention team receives the report with segmented risk tiers:
- **Red (> 0.85 probability, 850 subscribers):** Immediate intervention -- personalized re-engagement notification with curated content based on their historical preferences; targeted retention offer (20% discount for 3 months)
- **Yellow (0.7-0.85, 1,450 subscribers):** Soft intervention -- increased recommendation quality (higher diversity, more new content surfacing); in-app prompt asking for feedback

The AI-powered notification system sends the right content suggestion to each at-risk user at their optimal engagement time.

### Scenario 6: ML-Enhanced ABR During Streaming

**Persona:** Automated System / End Viewer (indirect)
**Context:** A viewer watching a sports match on a moderately unstable cellular connection

The traditional ABR algorithm switches bitrates reactively based on measured throughput. The ML-enhanced ABR does more:

1. **Bandwidth prediction:** The ML model predicts bandwidth for the next 10 seconds based on: recent throughput history, connection type (cellular/Wi-Fi), time-of-day patterns for this ISP, and historical bandwidth patterns for the user's location.
2. **Content-aware quality optimization:** The model knows the current content is live sports. It prioritizes framerate (60fps) over resolution -- dropping to 720p60 is preferable to 1080p30 for sports viewing.
3. **Buffer management:** Instead of the standard 3-segment buffer, the model adapts buffer depth based on content type and connection stability. For this unstable connection, it maintains a deeper buffer (6 segments) to absorb short network dips.
4. **Result:** The viewer experiences 40% fewer rebuffer events compared to the standard ABR algorithm, with higher average perceived quality (framerate maintained).

### Scenario 7: QoE-Driven Alerting

**Persona:** SRE / Content Operations
**Context:** Wednesday evening prime-time, subtle quality degradation

QoE Intelligence detects that viewers on ISP "TelcoA" in the "EU-West" region are experiencing gradually declining QoE scores:
- QoE p25 dropped from 78 to 65 over 15 minutes
- Root cause: The CDN edge serving TelcoA viewers has increased first-byte latency by 200ms
- The issue is too subtle for traditional threshold-based alerts (error rates are still at 0%) but the QoE impact is measurable

The QoE alerting system fires: "QoE degradation: TelcoA, EU-West, 4,200 affected viewers. QoE p25: 65 (threshold: 70). Primary signal: CDN latency increase. Suggested action: shift TelcoA traffic to alternate CDN."

The CDN routing intelligence automatically executes the traffic shift. QoE scores recover within 5 minutes. An SRE reviews the incident and confirms the automated action was correct.

### Scenario 8: Capacity Planning for Upcoming Live Event

**Persona:** SRE / Platform Engineering
**Context:** Planning for a major sporting event in 2 weeks

The capacity planning model forecasts demand for the upcoming event:
- **Predicted concurrent viewers:** 180,000 (based on: historical viewership for this event, current subscriber count, day-of-week, pre-event engagement signals like recordings and reminders)
- **Infrastructure scaling plan:** Auto-generated scaling schedule:
  - T-2 hours: Scale Playback Session Service from 6 to 18 pods
  - T-2 hours: Scale CDN Routing Service from 4 to 12 pods
  - T-2 hours: Scale Token Service from 4 to 12 pods
  - T-1 hour: Activate warm CDN edge caches in predicted top regions
  - T+0: Auto-scale based on real-time demand (HPA takes over)
  - T+3 hours: Scale down to pre-event levels (30-minute cool-down)
- **Cost estimate:** Additional infrastructure cost for the event: $12,500
- **Risk factors:** "If the event exceeds 220,000 concurrent, the Kafka cluster may need additional partitions for the playback.heartbeats topic."

The SRE team reviews the plan, approves it, and the system executes automatically.

### Scenario 9: Content Valuation for Acquisition Decision

**Persona:** Content Acquisition / Business
**Context:** Evaluating a potential content acquisition (Phase 4)

The content valuation AI evaluates a catalog of 50 films offered by a distributor:
- **Input:** Title metadata, genre, cast, director, release year, budget, theatrical performance, similar content performance on platform
- **Output per title:** Predicted monthly unique viewers, predicted average completion rate, predicted engagement lift (would it increase session duration for target segments), predicted incremental subscriber value
- **Portfolio assessment:** "Of the 50 titles, 8 are predicted to be high performers (> 50K unique viewers/month), 22 are moderate, and 20 are low value. Recommended acquisition strategy: license all 8 high performers and 15 selected moderate titles. Predicted ROI: 2.1x over 12 months at the offered price."

The content acquisition team uses this analysis alongside editorial judgment to negotiate the deal.

### Scenario 10: Ad Yield Optimization (AVOD Tier)

**Persona:** Ad Operations / Automated System
**Context:** AVOD viewer watching a VOD movie (Phase 2)

The ad optimization system manages server-side ad insertion (SSAI) for AVOD viewers:
1. **Ad break detection:** AI identifies natural ad break positions in the content (scene boundaries, dramatic pauses)
2. **Ad selection:** For each break, the system selects ads maximizing yield while maintaining viewer experience:
   - Viewer's interest profile (from recommendation model -- genres, brands, demographics)
   - Frequency capping (don't show the same ad twice in one session)
   - Ad pod composition (variety of ad types within a break)
3. **Dynamic pod length:** Break length adjusts based on viewer engagement: highly engaged viewers get shorter breaks (retain them); lower-engagement viewers get standard breaks
4. **Result:** Ad CPM is 30% higher than non-targeted insertion; viewer completion rate through ad breaks is 85% (vs 70% industry average)

---

## 4. Functional Requirements

### Content Operations AI

| ID | Requirement | Priority | Phase | AI Enhancement | Acceptance Criteria |
|----|-------------|----------|-------|----------------|---------------------|
| AIOPS-FR-001 | Platform shall automatically generate subtitles for ingested content using speech-to-text (Whisper Large v3) | P1 | 2 | Yes -- Whisper STT | Given a title is ingested with audio, then subtitles are generated in the original language within 2 hours; word error rate (WER) < 8% for clear speech content |
| AIOPS-FR-002 | Generated subtitles shall be automatically translated to at minimum 10 target languages | P1 | 2 | Yes -- Machine translation | Given subtitles are generated in the original language, then translations to 10 configured languages are available within 4 hours of ingest; BLEU score > 35 for major language pairs |
| AIOPS-FR-003 | Platform shall extract 100+ candidate thumbnail frames per title and score them for visual quality using a ResNet-based quality model | P0 | 1 | Yes -- ResNet quality scoring | Given a title is ingested, then 100+ candidate frames are extracted and scored; the top 8 frames are selected as thumbnail variants; quality score correlates with human quality judgment (Spearman's r > 0.7) |
| AIOPS-FR-004 | Platform shall generate audio+video fingerprints for duplicate detection | P1 | 1 | Yes -- Fingerprinting model | Given a title is ingested, then a fingerprint is generated and compared against the catalog; duplicates are flagged with > 95% recall and < 1% false positive rate |
| AIOPS-FR-005 | Platform shall detect scene boundaries and generate chapter markers | P1 | 2 | Yes -- Scene detection model | Given a 2-hour movie is ingested, then 15-20 chapter markers are generated at scene boundaries; boundary accuracy within ± 2 seconds of actual scene change |
| AIOPS-FR-006 | Platform shall classify content for nudity, violence, and language intensity on a 0-5 scale | P0 | 1 | Yes -- CLIP-based moderation | Given a title is ingested, then moderation scores are generated for nudity, violence, and language; classification accuracy > 90% vs human-labeled ground truth; results are compared against declared age rating for consistency alerts |
| AIOPS-FR-007 | Platform shall analyze audio for EBU R128 loudness compliance and flag non-compliant segments | P1 | 2 | No (signal processing, not ML) | Given a title is ingested, then audio is analyzed against EBU R128; segments exceeding ± 1 LU from target are flagged; report includes segment timestamps and deviation magnitude |
| AIOPS-FR-008 | AI metadata enrichment shall assign mood, theme, visual style, and pace tags to ingested content | P0 | 1 | Yes -- Multi-label classification | Given a title is ingested, then at minimum 3 mood tags, 3 theme tags, 1 visual style, and 1 pace classification are assigned; tag accuracy > 85% vs human-labeled validation set |

### Per-Title Encoding Optimization

| ID | Requirement | Priority | Phase | AI Enhancement | Acceptance Criteria |
|----|-------------|----------|-------|----------------|---------------------|
| AIOPS-FR-010 | Encoding pipeline shall use an ML model to generate per-title encoding ladders optimized for target VMAF score at minimum bitrate | P1 | 2 | Yes -- Custom CNN encoding optimizer | Given a title is submitted for encoding, then the ML model generates a custom encoding ladder per resolution tier; achieved VMAF is within ± 2 of target (93) at the predicted bitrate |
| AIOPS-FR-011 | Per-title encoding shall achieve at minimum 20% average bitrate reduction vs fixed ladder while maintaining VMAF 93 target | P0 | 2 | Yes | Given 100 titles are encoded with per-title optimization, then average bitrate savings is > 20% vs fixed ladder; no title has VMAF below 91 |
| AIOPS-FR-012 | The encoding optimization model shall support content classification: high motion, low motion, high grain, clean, animated | P1 | 2 | Yes | Given a title is analyzed, then it is classified into one of the content categories; classification accuracy > 92% vs human labeling |
| AIOPS-FR-013 | Per-title encoding results shall be logged for model improvement (actual VMAF vs predicted VMAF at predicted bitrate) | P1 | 2 | No | Given encoding completes, then actual VMAF scores are measured and compared to predictions; deviations are logged and feed into monthly model retraining |

### CDN & Delivery Intelligence

| ID | Requirement | Priority | Phase | AI Enhancement | Acceptance Criteria |
|----|-------------|----------|-------|----------------|---------------------|
| AIOPS-FR-020 | CDN Routing Service shall select the optimal CDN per session using an ML model based on real-time performance data | P1 | 2 | Yes -- XGBoost CDN routing model | Given a playback session starts, then the CDN Routing Service selects a CDN with < 30ms additional latency; selected CDN has the lowest predicted error rate and latency for the user's geo/ISP combination |
| AIOPS-FR-021 | CDN routing model inputs shall include: user geo, ISP, time-of-day, current CDN performance metrics (latency, throughput, error rate per region), CDN cost tier, and content type (live vs VOD) | P1 | 2 | Yes | Given the model receives all input features, then it produces a CDN ranking with associated confidence scores; the model is retrained hourly on latest performance data |
| AIOPS-FR-022 | CDN routing shall support mid-session CDN switching when QoE degrades below threshold | P1 | 2 | Yes -- QoE-triggered switching | Given a session's QoE score drops below 60 for 2 consecutive measurement intervals, then a CDN switch is triggered; the new manifest URL is delivered to the client within 5 seconds |
| AIOPS-FR-023 | Predictive cache warming shall pre-populate CDN edge caches based on EPG schedule and viewing pattern analysis | P1 | 2 | Yes -- Predictive model | Given a live event is scheduled in the EPG for T+2 hours, then the top 20 geo/ISP combinations (by predicted viewership) have warm caches by T-30 minutes; cache hit ratio for the first 5 minutes of the event > 90% |
| AIOPS-FR-024 | Predictive cache warming shall also warm caches for predicted popular catch-up content | P2 | 2 | Yes | Given a program aired yesterday with high viewership, then catch-up content is pre-cached in regions with high predicted catch-up demand; cache hit ratio for catch-up content in the first hour > 85% |
| AIOPS-FR-025 | ML-enhanced ABR shall incorporate content type awareness and bandwidth prediction for quality optimization | P1 | 3 | Yes -- ABR ML model | Given the ML ABR is active, then sports content prioritizes framerate (60fps) over resolution when bandwidth is constrained; rebuffer rate decreases by > 25% vs standard ABR algorithm on unstable connections |
| AIOPS-FR-026 | ML-enhanced ABR shall predict bandwidth for the next 10-second window based on connection history and contextual features | P2 | 3 | Yes | Given the ABR model receives connection telemetry, then it predicts available bandwidth for the next 10 seconds with < 20% mean absolute error |

### AIOps & Infrastructure Intelligence

| ID | Requirement | Priority | Phase | AI Enhancement | Acceptance Criteria |
|----|-------------|----------|-------|----------------|---------------------|
| AIOPS-FR-030 | Platform shall implement ML-based anomaly detection for all backend services | P0 | 2 | Yes -- PyTorch anomaly model | Given a service's error rate exceeds 3 standard deviations from its time-of-day baseline, then an anomaly alert fires within 60 seconds; false positive rate < 5% per week per service |
| AIOPS-FR-031 | Anomaly detection shall baseline normal behavior per service per time-of-day per day-of-week | P0 | 2 | Yes | Given 30 days of historical data, then a per-service baseline is established that accounts for daily and weekly patterns; baselines are updated weekly |
| AIOPS-FR-032 | Anomaly detection shall monitor: error rate, latency (p50, p95, p99), throughput (RPS), CPU utilization, memory utilization, and custom service-specific metrics | P0 | 2 | Yes | Given monitoring is active, then each metric has an anomaly detection model; alert includes: metric name, current value, baseline value, deviation magnitude |
| AIOPS-FR-033 | Alert correlation shall group related alerts across services into a single incident | P1 | 2 | Yes -- Correlation model | Given 3 related alerts fire (CDN latency + playback error rate + QoE drop), then they are grouped into a single incident with a root cause hypothesis: "CDN degradation in region X"; correlation reduces alert volume by > 60% |
| AIOPS-FR-034 | Alert correlation shall suggest probable root cause based on correlated signals | P1 | 2 | Yes | Given correlated alerts are grouped, then a root cause suggestion is included with confidence level; root cause suggestions are correct > 60% of the time (validated by SRE post-incident review) |
| AIOPS-FR-035 | Downstream alerts shall be suppressed when upstream root cause is identified | P1 | 2 | Yes | Given a CDN incident is identified as root cause, then downstream alerts (playback errors, QoE drops) are suppressed with a note "suppressed -- related to CDN incident #X"; suppression reduces alert noise by > 50% |
| AIOPS-FR-036 | Self-healing automation shall execute automated remediation for defined failure patterns | P1 | 3 | Yes -- Runbook automation | Given a known failure pattern is detected (e.g., connection pool exhaustion, memory leak, pod crash loop), then automated remediation (pod restart, scaling, traffic shift) executes within 60 seconds; human approval not required for pre-approved runbooks |
| AIOPS-FR-037 | Self-healing runbooks shall be versioned, reviewed, and require SRE approval before activation | P0 | 3 | No | Given a new runbook is created, then it requires SRE review and approval; runbooks are version-controlled in Git; execution is audited |
| AIOPS-FR-038 | Self-healing shall include a safety mechanism: maximum 1 automated remediation per service per 15-minute window to prevent remediation storms | P0 | 3 | No | Given a remediation was executed for Service X at T=0, then no further automated remediation runs for Service X until T+15 minutes; the second alert escalates to human on-call |
| AIOPS-FR-039 | Predictive alerting shall fire warnings before user impact for predictable failure modes (capacity exhaustion, disk fill, certificate expiry, quota approaching) | P1 | 3 | Yes -- Time-series forecasting | Given a disk is filling at a predictable rate, then an alert fires at least 2 hours before the disk reaches 90% capacity; prediction accuracy within ± 10% of actual time |
| AIOPS-FR-040 | ML-based capacity forecasting shall predict concurrent user demand per hour for the next 7 days | P2 | 3 | Yes -- Demand forecasting model | Given 90 days of historical data and the upcoming EPG schedule, then the model predicts hourly concurrent users for the next 7 days with < 15% mean absolute percentage error |

### Business Intelligence AI

| ID | Requirement | Priority | Phase | AI Enhancement | Acceptance Criteria |
|----|-------------|----------|-------|----------------|---------------------|
| AIOPS-FR-050 | Churn prediction model shall score every subscriber daily on 30-day churn probability | P1 | 2 | Yes -- XGBoost churn model | Given the model runs daily, then every subscriber has a churn probability score (0.0-1.0); the model identifies > 70% of actual churners 30 days before churn event; precision at 0.7 threshold > 50% |
| AIOPS-FR-051 | Churn prediction signals shall include: viewing hour decline, session frequency decline, support contacts, payment failures, app uninstall signals, engagement score trend | P1 | 2 | Yes | Given the model is trained, then all specified signal categories are used as features; feature importance is logged and reviewed monthly |
| AIOPS-FR-052 | High-risk churn subscribers (probability > 0.7) shall trigger automated retention workflows: personalized content recommendations, in-app feedback prompts, and configurable retention offers | P1 | 2 | Yes | Given a subscriber is scored > 0.7, then within 24 hours they receive a personalized re-engagement notification; if > 0.85, then a retention offer is queued for review by the retention team |
| AIOPS-FR-053 | Dynamic pricing engine shall optimize subscription pricing per user segment based on engagement patterns and willingness-to-pay signals | P2 | 3 | Yes -- Pricing optimization model | Given the model is deployed on 10% of users (A/B test), then revenue per user in the test group increases by > 5% vs control; churn rate does not increase by > 0.5% |
| AIOPS-FR-054 | Content valuation AI shall predict monthly unique viewers and engagement metrics for candidate content acquisitions | P2 | 4 | Yes -- Content performance prediction | Given a candidate title with metadata (genre, cast, director, similar content performance), then the model predicts monthly unique viewers within ± 25% of actual (validated on historical catalog data) |
| AIOPS-FR-055 | Ad optimization for AVOD tier shall select ads per viewer maximizing yield while respecting frequency caps and viewer experience constraints | P2 | 2 | Yes -- Ad selection model | Given an AVOD viewer hits an ad break, then ad selection completes within 200ms; targeted ad CPM is > 25% higher than non-targeted; viewer completion through ad breaks > 80% |

### Quality of Experience Intelligence

| ID | Requirement | Priority | Phase | AI Enhancement | Acceptance Criteria |
|----|-------------|----------|-------|----------------|---------------------|
| AIOPS-FR-060 | QoE Service shall compute a per-session quality score (0-100) combining: video start time (25%), rebuffer ratio (30%), average bitrate as % of max (20%), resolution stability (15%), and error-free session (10%) | P0 | 1 | No (composite scoring) | Given a session is active, then a QoE score is computed every 30 seconds from client-reported metrics; score calculation is consistent and deterministic per the weighted formula |
| AIOPS-FR-061 | QoE alerting shall trigger when QoE score (p25) drops below 70 for any segment dimension: CDN, ISP (top 20), region, device platform, channel (live), or content type (VOD) | P0 | 1 | No (threshold alerting with segment analysis) | Given QoE p25 for "ISP TelcoA, EU-West" drops to 65, then an alert fires within 2 minutes including: affected segment, current score, baseline score, estimated affected viewers, primary contributing factor (start time / rebuffer / bitrate) |
| AIOPS-FR-062 | Viewer impact analysis shall quantify the user impact of every operational incident | P1 | 2 | Yes -- Impact estimation model | Given an incident affecting CDN A in EU-West is resolved, then the post-incident report includes: total affected viewers, affected session minutes, QoE score degradation, % of affected viewers who abandoned, and estimated revenue impact |
| AIOPS-FR-063 | Real-time QoE dashboards shall show: overall platform QoE, per-CDN QoE, per-ISP QoE, per-device QoE, per-channel QoE (live) with 30-second refresh | P0 | 1 | No | Given the QoE dashboard is open, then all dimensions are visible with 30-second data freshness; drill-down from any dimension to individual session level is available |
| AIOPS-FR-064 | QoE trends shall be tracked over time to detect gradual degradation that threshold-based alerts would miss | P1 | 2 | Yes -- Trend detection model | Given QoE for a segment degrades by 5% over 7 days (too gradual for threshold alerts), then a trend alert fires: "QoE for [segment] has been declining for 7 days. Current: 74, 7 days ago: 79. Investigate." |

---

## 5. AI-Specific Features

### 5.1 Content Operations AI -- Detailed

**Automated Ingest Enrichment Pipeline:**

The enrichment pipeline is orchestrated by Apache Airflow. Each ingested title triggers a DAG that runs the following tasks in dependency order:

```
Ingest → [Audio Extract, Video Decode] →
         Audio Extract → [Whisper STT, Loudness Analysis, Audio Fingerprint]
         Video Decode → [Thumbnail Extract, Scene Detection, Visual Fingerprint, Content Moderation]
         Whisper STT → [Translation (10 languages)]
         Thumbnail Extract → [Quality Scoring → Variant Selection]
         Scene Detection → [Chapter Marker Generation]
         All AI tasks → [Metadata Tag Generation]
         All complete → [Enrichment Complete Event → Kafka]
```

**Processing Time Targets:**
| Task | Phase 1 | Phase 2 (optimized) |
|------|---------|---------------------|
| Subtitle generation (2-hour content) | N/A | < 1.5 hours (0.5x real-time with Whisper Large v3) |
| Translation (10 languages) | N/A | < 30 minutes after STT |
| Thumbnail extraction + scoring | < 15 minutes | < 10 minutes |
| Scene detection + chapters | N/A | < 20 minutes |
| Content moderation | < 10 minutes | < 10 minutes |
| Fingerprint generation | < 5 minutes | < 5 minutes |
| AI metadata tags | < 10 minutes | < 5 minutes |
| **Total pipeline** | **< 45 minutes (partial)** | **< 2 hours (full)** |

### 5.2 CDN & Delivery Intelligence -- Detailed

**Predictive CDN Routing Model:**

| Aspect | Detail |
|--------|--------|
| Model | XGBoost 2.0 gradient-boosted trees |
| Input features | User geo (country, region, city), ISP, current CDN performance per region (latency p50/p99, error rate, throughput, measured every 30 seconds), CDN cost tier, content type (live/VOD/TSTV), time-of-day, day-of-week |
| Output | Ranked list of CDN providers with predicted QoE score per CDN for this session |
| Training data | Historical session-level CDN performance data (QoE score per session per CDN, 90 days) |
| Retraining | Hourly (on latest 24 hours of data) |
| Inference latency | < 10ms (XGBoost on CPU, via KServe) |
| Fallback | Round-robin with geo-affinity (no ML) |

**Predictive Cache Warming Model:**

| Aspect | Detail |
|--------|--------|
| Model | Custom time-series model combining EPG schedule data with historical viewing patterns |
| Input | EPG schedule (next 24 hours), historical viewership per channel per time-slot per region, real-time engagement signals (reminders, recordings) |
| Output | Per-region per-content cache warming priority list (top 100 content items to warm per CDN edge) |
| Execution | Runs every 30 minutes; warming requests sent to CDN APIs 2 hours before predicted peak |
| Target | Cache hit ratio for first 5 minutes of live events > 90%; catch-up content first-hour cache hit > 85% |

### 5.3 AIOps -- Detailed

**Anomaly Detection Architecture:**

Each service has a dedicated anomaly detection model that baselines its normal behavior:

| Aspect | Detail |
|--------|--------|
| Model | Isolation Forest + seasonal decomposition (STL) for each metric |
| Metrics monitored (per service) | Error rate, latency p50/p95/p99, throughput (RPS), CPU %, memory %, custom metrics (e.g., concurrent sessions for Playback, cache hit ratio for CDN) |
| Baseline | 90 days of 1-minute granularity metric data; seasonal decomposition captures daily and weekly patterns |
| Detection | Alert when current value exceeds 3 sigma from predicted baseline for 2 consecutive minutes (avoids transient spikes) |
| Retraining | Weekly on latest 90 days of data |
| Alert routing | PagerDuty with severity based on deviation magnitude and service criticality tier |

**Self-Healing Runbook Library:**

| Failure Pattern | Detection | Remediation | Safety Limit |
|----------------|-----------|-------------|--------------|
| Pod crash loop | > 3 restarts in 5 minutes | Delete pod, trigger fresh schedule on different node | 1 per service per 15 min |
| Connection pool exhaustion | DB connection errors > 5/min + connection count at max | Rolling restart with increased pool config | 1 per service per 15 min |
| Memory leak | Memory growth > 10% over 30 min without proportional load increase | Rolling restart of affected pods | 1 per service per 15 min |
| CDN degradation | QoE p25 < 65 for CDN in a region | Shift traffic to alternate CDN for affected region | 1 per CDN per 30 min |
| Kafka consumer lag | Lag > 100,000 messages for > 5 minutes | Scale consumer group replicas by 2x | 1 per consumer group per 30 min |
| Disk nearing capacity | Disk > 85% and growing | Trigger log rotation and cold storage archival; alert if > 90% | 1 per volume per 1 hour |

### 5.4 Business Intelligence AI -- Detailed

**Churn Prediction Model:**

| Aspect | Detail |
|--------|--------|
| Model | XGBoost 2.0 classifier |
| Target variable | Binary -- did the subscriber churn within 30 days of scoring date |
| Features (60+) | Viewing hours/week (4-week trend), session frequency (4-week trend), genre diversity, device diversity, content completion rate, search frequency, support tickets (30-day count), payment failure count, days since last session, subscription age, subscription tier, promotional status, app version (outdated?), notification engagement rate, recommendation CTR, churn risk of similar users (collaborative) |
| Training data | 12 months of subscriber-level data, balanced via SMOTE for churn class |
| Evaluation | AUC > 0.82, precision@70 > 50%, recall@70 > 70% |
| Refresh | Daily retraining on latest 30 days of data |
| Output | Per-subscriber churn probability (0.0-1.0), top 5 contributing features per subscriber |

**Content Valuation Model (Phase 4):**

| Aspect | Detail |
|--------|--------|
| Model | Gradient-boosted regression + collaborative filtering |
| Input | Title metadata (genre, cast, director, release year, budget, theatrical box office), similar content performance on platform, genre trend data, seasonal factors |
| Output | Predicted monthly unique viewers, predicted average completion rate, predicted incremental subscriber value (new subscribers attracted) |
| Validation | Back-tested against 500 historical catalog additions; prediction within ± 25% for monthly viewers |

### 5.5 QoE Intelligence -- Detailed

**QoE Scoring Formula:**

```
QoE = 0.25 * start_time_score +
      0.30 * rebuffer_score +
      0.20 * bitrate_score +
      0.15 * resolution_stability_score +
      0.10 * error_free_score

Where:
  start_time_score = max(0, 100 - ((start_time_ms - 1000) / 40))  // Linear: 1s=100, 5s=0
  rebuffer_score = max(0, 100 - (rebuffer_ratio * 10000))          // 0%=100, 1%=0
  bitrate_score = (avg_bitrate / max_available_bitrate) * 100       // Ratio of achieved vs max
  resolution_stability_score = max(0, 100 - (resolution_drops * 10)) // Each drop = -10
  error_free_score = 100 if no errors, 0 if any error
```

**Contextual QoE Adjustment:**
The raw QoE score is adjusted for device context:
- Mobile on cellular: max expected quality is lower, so scores are normalized upward (a 720p stream on cellular is "expected quality" whereas on a 4K TV it would be a degradation)
- Content type: Live sports on LL-HLS has different latency expectations than VOD
- Network conditions: Known poor ISPs have adjusted baselines

---

## 6. Non-Functional Requirements

### Performance

| ID | Requirement | Target | Measurement |
|----|-------------|--------|-------------|
| AIOPS-NFR-001 | Anomaly detection latency (event to alert) | < 60 seconds | Time delta between metric exceeding threshold and alert firing |
| AIOPS-NFR-002 | Self-healing execution time (alert to remediation complete) | < 90 seconds | Time delta between alert and verified remediation |
| AIOPS-NFR-003 | CDN routing decision latency (additional to session start) | < 30ms | Server-side CDN Routing Service response time |
| AIOPS-NFR-004 | QoE score computation frequency | Every 30 seconds per active session | QoE Service processing throughput |
| AIOPS-NFR-005 | Churn model daily execution time | < 2 hours for full subscriber base | Batch processing time for daily scoring run |
| AIOPS-NFR-006 | Content enrichment pipeline total time | < 2 hours (full pipeline, Phase 2) | Pipeline DAG execution time from ingest to enrichment complete |
| AIOPS-NFR-007 | Per-title encoding analysis time | < 5 minutes per title | ML analysis time (excluding actual encoding) |

### Scale

| ID | Requirement | Target | Measurement |
|----|-------------|--------|-------------|
| AIOPS-NFR-010 | Anomaly detection: services monitored | All backend services (20+) with 6+ metrics each | Service coverage audit |
| AIOPS-NFR-011 | QoE scoring: concurrent sessions | 500,000 concurrent sessions scored every 30 seconds | QoE Service throughput under load |
| AIOPS-NFR-012 | Churn prediction: subscriber base | Score up to 2 million subscribers daily | Batch job scaling |
| AIOPS-NFR-013 | Content enrichment: throughput | 50 titles/day (Phase 1), 200 titles/day (Phase 4) | Pipeline throughput measurement |
| AIOPS-NFR-014 | CDN routing decisions | 5,000 decisions/second (Phase 1), 25,000/second (Phase 4) | Load test |

### Availability

| ID | Requirement | Target | Measurement |
|----|-------------|--------|-------------|
| AIOPS-NFR-020 | CDN Routing Service availability | 99.99% (critical path for playback) | Server-side uptime monitoring |
| AIOPS-NFR-021 | QoE Service availability | 99.95% | Server-side uptime monitoring |
| AIOPS-NFR-022 | Anomaly detection availability | 99.9% | Detection system uptime; gaps in detection coverage < 5 min/month |
| AIOPS-NFR-023 | Content enrichment pipeline availability | 99.5% (non-critical path; retries handle failures) | Pipeline execution success rate |

### AI Infrastructure Cost

| ID | Requirement | Target | Measurement |
|----|-------------|--------|-------------|
| AIOPS-NFR-030 | Total AI infrastructure cost (inference + training + storage) shall remain below 15% of total platform cost | < 15% | Monthly cost attribution: AI GPU compute, training jobs, Feature Store, model storage, Bedrock API calls |
| AIOPS-NFR-031 | Per-model cost tracking | Each model has a tracked cost-per-inference and cost-per-training-run | Model cost attribution dashboard |
| AIOPS-NFR-032 | GPU utilization efficiency | < 70% average GPU utilization at peak (headroom for burst) | GPU monitoring on KServe nodes |

---

## 7. Technical Considerations

### AI Model Deployment Pipeline

All AI models follow the same deployment lifecycle defined in ARCH-001:

```
1. Training (SageMaker)
   → Triggered by: scheduled retraining or drift alert
   → Output: model artifact in S3

2. Evaluation (Automated)
   → Offline metrics computed on held-out test set
   → Quality gates: must exceed previous production model on all primary metrics
   → Bias checks: evaluated across user segments

3. Registration (MLflow)
   → Model artifact registered with version, metrics, and metadata
   → Approved for deployment by ML engineer

4. Canary Deployment (KServe)
   → New model serves 5% of traffic for 1 hour
   → Automated SLO check: latency, throughput, business metrics
   → If SLO met: promote to 50% for 4 hours, then 100%
   → If SLO violated: automatic rollback

5. Monitoring (Continuous)
   → Data drift: KL divergence on input features
   → Model drift: prediction distribution shift
   → Performance: latency, throughput, error rate
   → Business metrics: A/B test against control
```

### Content Enrichment Pipeline Architecture

```
S3 (mezzanine file) → Content Ingest Service → Airflow DAG trigger
                                                      │
                                       ┌──────────────┼──────────────┐
                                       │              │              │
                                  Audio Extract   Video Decode   Fingerprint
                                       │              │
                                 ┌─────┼─────┐   ┌───┼───┐
                                 │     │     │   │   │   │
                              Whisper  EBU   │  Scene Thumb  CLIP
                                STT   R128  │  Detect Extract Moder.
                                 │          │         │
                              Translation   │   Quality Score
                              (10 langs)    │
                                            │
                                    Metadata Tag Gen
                                            │
                                  Enrichment Complete → Kafka
```

**Compute Requirements:**
- Whisper (STT): GPU required (A10G), ~0.5x real-time processing
- Thumbnail scoring (ResNet): GPU required (T4), < 1 minute per 100 frames
- Content moderation (CLIP): GPU required (A10G), < 10 minutes per title
- Scene detection: GPU preferred, CPU fallback, < 20 minutes per title
- Metadata tagging: GPU required (T4), < 5 minutes per title
- Translation: CPU-based (transformer model), < 30 minutes for 10 languages

### CDN Routing Integration

The CDN Routing Service sits in the critical path for playback initiation:

```
Client → BFF → Playback Session Service → CDN Routing Service → Token Service
                                                 │
                                          ┌──────┴──────┐
                                          │ ML Model    │
                                          │ (XGBoost)   │
                                          └──────┬──────┘
                                                 │
                                          CDN Selection
                                          + Manifest URL
```

**Latency Budget:**
- Total playback initiation target: < 200ms (from BFF request to manifest URL returned)
- CDN Routing Service budget: < 30ms (including model inference)
- XGBoost inference: < 10ms (CPU, cached features)
- Feature lookup (Redis): < 5ms
- Response composition: < 5ms

**Mid-Session CDN Switching:**
When QoE monitoring detects degradation during an active session:
1. QoE Service publishes `qoe.alert.triggered` to Kafka
2. CDN Routing Service consumes the alert, evaluates alternative CDNs
3. New manifest URL is generated with the alternate CDN
4. Manifest proxy serves the updated manifest on the next client manifest request (standard: every 2 seconds for live, every segment for VOD)
5. Client seamlessly switches to the new CDN on the next segment download

### AIOps Integration with Observability Stack

```
Prometheus (metrics) ──→ Anomaly Detection Models ──→ Alert Manager
Loki (logs) ──────────→ Log Pattern Analysis ──────→ Alert Correlation
Tempo (traces) ───────→ Latency Anomaly Detection ─→ Root Cause Analysis
QoE Service ──────────→ QoE Trend Analysis ─────────→    │
                                                          │
                                                    ┌─────┴─────┐
                                                    │ Incident  │
                                                    │ Manager   │
                                                    └─────┬─────┘
                                                          │
                                                    ┌─────┴─────┐
                                                    │ Self-Heal │
                                                    │ or Page   │
                                                    └───────────┘
```

The AIOps layer sits between the observability stack (Prometheus, Loki, Tempo) and the incident management system (PagerDuty). It adds intelligence to raw observability data.

---

## 8. Dependencies

### Upstream Dependencies

| Dependency | Service/Component | Nature | Impact if Unavailable |
|------------|------------------|--------|----------------------|
| Prometheus + Grafana | ARCH-001 (Observability) | Metrics data source for anomaly detection | No anomaly detection; fall back to static threshold alerts |
| Kafka Event Bus | ARCH-001 (Data Architecture) | Event stream for real-time signals (QoE, viewing, CDN) | QoE scoring stops; anomaly detection loses real-time signals; CDN routing uses cached data |
| KServe (GPU nodes) | ARCH-001 (AI/ML Infrastructure) | Model serving for all ML models | All AI features fall back to rule-based defaults |
| Feature Store (Feast) | ARCH-001 (AI/ML Infrastructure) | Features for CDN routing, churn prediction | Models operate without features; degraded accuracy |
| SageMaker | ARCH-001 (AI/ML Infrastructure) | Model training and batch inference | No model retraining; existing models continue serving until drift is detected |
| CDN Provider APIs | External (Akamai, CloudFront, Fastly) | Cache warming API, performance data API | Cannot warm caches; CDN routing operates on stale data |
| EPG Service | PRD-005 | Schedule data for predictive cache warming and capacity planning | Cache warming predictions degrade; capacity planning uses historical patterns only |
| Playback Session Service | ARCH-001 | Active session data for concurrent viewer counts, QoE input | QoE scoring unavailable; capacity planning uses estimated data |
| Conviva SDK (client-side) | PRD-006 (Multi-Client) | Client-side QoE telemetry | No client-side QoE data; server-side metrics only (reduced accuracy) |

### Downstream Dependencies (services depend on AI Ops)

| Dependent | PRD | Nature |
|-----------|-----|--------|
| Live TV | PRD-001 | CDN routing for live streams, ABR optimization for live content, anomaly detection for live encoder health |
| TSTV | PRD-002 | Predictive cache warming for catch-up content |
| Cloud PVR | PRD-003 | Content enrichment (chapter marks for recordings), encoding pipeline health monitoring |
| VOD/SVOD | PRD-004 | Per-title encoding optimization, content enrichment pipeline, CDN routing for VOD streams |
| EPG | PRD-005 | AI metadata tags displayed in EPG program detail |
| Multi-Client | PRD-006 | Client telemetry feeds QoE scoring; CDN routing decisions affect all clients |
| AI User Experience | PRD-007 | Shares Feature Store, KServe infrastructure, ML pipeline; content enrichment generates metadata used by recommendations |

### Cross-PRD Integration Points

- **PRD-001 (Live TV):** CDN routing (AIOPS-FR-020) is critical for live playback quality. ML-enhanced ABR (AIOPS-FR-025) optimizes live sports viewing. Anomaly detection monitors live encoder health.
- **PRD-002 (TSTV):** Predictive cache warming (AIOPS-FR-024) pre-caches popular catch-up content. Content enrichment provides chapter markers for catch-up navigation.
- **PRD-003 (Cloud PVR):** Content enrichment pipeline (AIOPS-FR-005) generates chapter markers used in recording playback (skip to highlights for sports).
- **PRD-004 (VOD/SVOD):** Per-title encoding (AIOPS-FR-010) applies to all VOD content, directly reducing bandwidth costs. AI metadata tags (AIOPS-FR-008) power VOD discovery and recommendations.
- **PRD-005 (EPG):** EPG schedule data feeds predictive cache warming and capacity planning models.
- **PRD-006 (Multi-Client):** Client-side Conviva SDK provides QoE telemetry. CDN routing decisions are consumed by client players.
- **PRD-007 (AI UX):** Shares the Feature Store (user and content features), KServe GPU cluster, and ML pipeline infrastructure. Content enrichment outputs (tags, embeddings, thumbnails) are consumed by the recommendation engine.

---

## 9. Success Metrics

| Metric | Description | Baseline | Phase 1 Target | Phase 2 Target | Phase 4 Target | Measurement Method |
|--------|-------------|----------|---------------|---------------|---------------|-------------------|
| Content Processing Time | Ingest to catalog availability (full enrichment) | 4-8 hours (manual) | 45 min (partial) | 2 hours (full) | 30 min (full, optimized) | Pipeline DAG execution time |
| Encoding Bandwidth Savings | Average bitrate reduction vs fixed ladder | 0% | N/A | 20% | 35% | Actual bitrate / fixed-ladder bitrate per title |
| CDN Cache Hit Ratio (Live, first 5 min) | Cache hit ratio for first 5 minutes of live events | 80% | 85% | 92% | 95% | CDN analytics per event |
| MTTD (Mean Time to Detect) | Time from anomaly start to alert fire | 8-15 min | 5 min (static alerts) | < 60 sec (ML) | < 30 sec | Alert timestamp - anomaly start (estimated from metric data) |
| MTTR (Mean Time to Resolve) | Time from alert to resolution | 30-60 min | 20 min | 10 min | 5 min | Incident lifecycle tracking |
| Auto-Remediation Rate | % of incidents resolved without human intervention | 0% | 0% | 15% | 40% | Incident classification: auto-remediated vs human-resolved |
| Alert Noise Reduction | % reduction in total alerts via correlation and suppression | 0% | 0% | 50% | 65% | Alert count with correlation vs without |
| Churn Prediction Recall@70 | % of actual churners identified by model at p > 0.7 threshold | N/A | N/A | 60% | 70% | Model evaluation against actual churn outcomes |
| QoE Score (platform p50) | Median quality of experience score across all sessions | 72 (industry) | 80 | 85 | 88 | QoE Service aggregation |
| AI Infrastructure Cost Ratio | AI infra cost as % of total platform cost | N/A | 12% | 14% | < 15% | Monthly cost attribution |

---

## 10. Open Questions & Risks

### Open Questions

| ID | Question | Owner | Impact | Target Decision Date |
|----|----------|-------|--------|---------------------|
| AIOPS-OQ-001 | Should per-title encoding use a single model or separate models per content type (live vs VOD, film vs animation)? | AI/ML Engineering | Affects encoding accuracy and model complexity | Month 6 |
| AIOPS-OQ-002 | What is the right threshold for self-healing activation? Too sensitive = unnecessary remediations; too conservative = missed automation opportunities. | SRE / AI/ML | Affects auto-remediation rate and system stability | Month 10 (iterative tuning) |
| AIOPS-OQ-003 | Should the churn prediction model use payment data (failed payment attempts, payment method changes)? Privacy and access considerations. | AI/ML / Legal / Finance | Affects model accuracy (payment signals are strong churn indicators) | Month 8 |
| AIOPS-OQ-004 | For ML-enhanced ABR, should the model run server-side (in the manifest proxy) or client-side (in the player)? Server-side gives more data but adds latency; client-side has device constraints. | Engineering (Platform + Client) | Affects ABR effectiveness and implementation complexity | Month 12 (Phase 3 planning) |
| AIOPS-OQ-005 | How should we handle content enrichment for live content (subtitles, chapter markers for live events)? Live enrichment has strict latency requirements. | AI/ML / Content Ops | Affects live content accessibility and highlights feature | Month 8 |

### Risks

| ID | Risk | Severity | Likelihood | Mitigation |
|----|------|----------|------------|------------|
| AIOPS-R-001 | **Self-healing causes cascading failures** -- automated remediation (e.g., pod restart, traffic shift) introduces instability or worsens the original issue | High | Medium | Implement strict safety limits: max 1 remediation per service per 15 minutes; all runbooks require SRE review before activation; rollback mechanism for every remediation action; "big red button" to disable all self-healing globally |
| AIOPS-R-002 | **Anomaly detection false positive fatigue** -- too many false alerts erode SRE trust in the system, leading to ignored alerts | High | High | Tune models for precision over recall (< 5% false positive rate per service per week); implement alert suppression during known maintenance windows; monthly false positive review with SRE team; continuous model improvement based on false positive feedback |
| AIOPS-R-003 | **Per-title encoding model inaccuracy** -- model predicts bitrate that is too low, resulting in visible quality degradation for some titles | High | Medium | Always validate: encode at predicted bitrate, measure actual VMAF, reject if VMAF < 91 and re-encode at higher bitrate; maintain a quality floor (never go below 80% of fixed-ladder bitrate); human QC spot-check 5% of titles |
| AIOPS-R-004 | **CDN routing model makes suboptimal decisions during novel events** -- a new CDN failure mode or unprecedented traffic pattern confuses the model | Medium | Medium | Maintain rule-based fallback (round-robin with geo-affinity); model confidence scoring -- if model confidence < 0.6, use fallback; continuous monitoring of routing decision quality via QoE correlation |
| AIOPS-R-005 | **Churn prediction leads to inappropriate retention offers** -- model identifies at-risk users but retention offers alienate users who were not actually going to churn (false positives receive discounts unnecessarily, costing revenue) | Medium | Medium | Target retention offers only at p > 0.85 (high confidence); use soft interventions (content recommendations) for p 0.7-0.85; A/B test retention offers vs no-offer control to measure true incremental retention; track offer cost vs retained revenue |
| AIOPS-R-006 | **GPU cost escalation** -- AI model serving and training costs grow faster than revenue as more models are deployed | High | Medium | Track per-model cost-per-inference as a first-class metric; use spot instances for all training jobs; right-size GPU instances (T4 for inference, A10G for training); batch inference where real-time is not required; set AI cost budget at 15% of total platform cost with alerts at 12% |
| AIOPS-R-007 | **Content moderation AI misclassifies content** -- AI assigns incorrect age rating (either too permissive or too restrictive), leading to inappropriate content exposure or unnecessary content suppression | High | Medium | Always require human review for moderation results before final age rating assignment; flag discrepancies between AI classification and declared rating for priority review; maintain a human-labeled validation set and measure accuracy quarterly |
| AIOPS-R-008 | **Whisper STT accuracy varies by language and content type** -- subtitle quality for non-English languages or content with background noise / music is significantly lower | Medium | High | Validate WER per language; set WER thresholds (< 8% for Tier 1 languages, < 12% for Tier 2); flag titles with high WER for human review; do not auto-publish subtitles for languages with WER > 12% |

---

*This PRD defines the AI Backend & Operations Intelligence layer -- the invisible AI that optimizes platform operations, reduces costs, predicts and prevents incidents, and generates business intelligence. It shares AI infrastructure (KServe, Feature Store, ML pipeline) with PRD-007 (AI User Experience) and is supported by the architecture defined in ARCH-001. Implementation priority: QoE scoring and content enrichment in Phase 1, anomaly detection and CDN routing in Phase 2, self-healing and advanced ABR in Phase 3, content valuation and full AIOps maturity in Phase 4.*
