# Analytics & Telemetry
## Cross-Cutting Concerns — AI-Native OTT Streaming Platform

**Document ID:** XC-002
**Version:** 1.0
**Date:** 2026-02-08
**Status:** Draft
**Author:** Integration Analyst Agent
**References:** ARCH-001, VIS-001, PRD-001 through PRD-008
**Audience:** Data Engineers, ML Engineers, Backend Engineers, Product Managers, BI Analysts

---

## Table of Contents

1. [Overview](#1-overview)
2. [Client-Side Event Taxonomy](#2-client-side-event-taxonomy)
3. [Server-Side Event Collection](#3-server-side-event-collection)
4. [Data Pipeline Architecture](#4-data-pipeline-architecture)
5. [Real-Time Analytics](#5-real-time-analytics)
6. [Batch Analytics & Reporting](#6-batch-analytics--reporting)
7. [ML Training Data Pipeline](#7-ml-training-data-pipeline)
8. [Privacy, Consent & GDPR](#8-privacy-consent--gdpr)
9. [Key Dashboards & Reports](#9-key-dashboards--reports)
10. [Event Schema Standards](#10-event-schema-standards)
11. [Data Quality & Governance](#11-data-quality--governance)

---

## 1. Overview

Analytics and telemetry form the intelligence layer of the platform. Every user action, system event, and infrastructure metric flows through a unified data pipeline that serves three purposes:

1. **Real-time operational intelligence.** Live dashboards and alerts that tell the operations team what is happening right now (concurrent viewers, QoE scores, error rates, CDN health).
2. **Batch business analytics.** Daily and weekly reports for product, content, and business teams (engagement trends, content performance, funnel metrics, churn analysis).
3. **ML training and feature computation.** The raw event stream feeds the AI/ML infrastructure — recommendation models, churn prediction, anomaly detection, and all other AI capabilities documented in PRD-007 and PRD-008.

### Design Principles

- **Collect once, use many times.** Events are published once to Kafka and consumed by multiple downstream systems (real-time analytics, batch analytics, ML pipelines, QoE scoring).
- **Schema-first.** Every event has an Avro schema registered in the Confluent Schema Registry. Schema evolution follows forward-compatibility rules: new fields may be added, existing fields may not be removed or renamed.
- **Privacy by design.** PII is separated from behavioral data at the collection layer. User IDs are pseudonymized in the analytics pipeline. Consent status determines what data is collected and how it is used.
- **Client-side is the source of truth for UX events.** The client knows what the user saw and interacted with. Server-side events capture what the backend did in response.
- **Exactly-once semantics where it matters.** Kafka consumer groups for billing, entitlement, and engagement metrics use idempotent consumers to prevent double-counting.

### Key Services

| Service | Role | SLO |
|---------|------|-----|
| **Analytics Collector** (Go) | Receives client-side events via HTTPS, validates, enriches, publishes to Kafka | p99 < 50ms, 99.9% availability |
| **QoE Service** (Go) | Computes per-session quality scores from playback telemetry | p99 < 100ms, 99.95% availability |
| **Feature Store** (Python) | Extracts ML features from event streams (Flink) and serves them for inference | p99 < 10ms (online), 99.95% availability |
| **Data Platform** (Spark/Flink) | Processes events from Kafka into the data lake (S3/Iceberg) for batch analytics | Processing latency < 5 minutes for real-time, < 1 hour for batch |

---

## 2. Client-Side Event Taxonomy

All client platforms (Android TV, Apple TV, iOS, Android, Web, Smart TVs) emit a standardized set of telemetry events. Events are batched on the client and sent to the Analytics Collector every 5 seconds or when 20 events accumulate, whichever comes first.

### 2.1 Event Categories

#### Navigation Events

| Event Name | Trigger | Key Properties | PRD Reference |
|-----------|---------|----------------|---------------|
| `app.launch` | App opens (cold or warm start) | launch_type (cold/warm), launch_duration_ms, platform, os_version, app_version | PRD-006 |
| `app.background` | App moves to background | session_duration_ms, active_screen | PRD-006 |
| `app.foreground` | App returns to foreground | background_duration_ms | PRD-006 |
| `screen.view` | Screen becomes visible | screen_name, referrer_screen, navigation_method (tap/remote/deeplink) | PRD-006 |
| `screen.leave` | Screen is navigated away from | screen_name, dwell_time_ms, interaction_count | PRD-006 |

#### Browse & Discovery Events

| Event Name | Trigger | Key Properties | PRD Reference |
|-----------|---------|----------------|---------------|
| `rail.impression` | Content rail becomes visible | rail_id, rail_type (editorial/ai_recommended/continue_watching/trending), rail_position, items_visible | PRD-007 |
| `rail.scroll` | User scrolls within a rail | rail_id, scroll_direction, items_scrolled, scroll_depth_percent | PRD-007 |
| `tile.impression` | Content tile becomes visible for > 1 second | content_id, tile_position, rail_id, thumbnail_variant, is_personalized | PRD-007 |
| `tile.click` | User selects a content tile | content_id, tile_position, rail_id, time_to_click_ms | PRD-007 |
| `hero.impression` | Hero banner becomes visible | content_id, hero_variant, is_personalized, creative_id | PRD-007 |
| `hero.click` | User interacts with hero banner | content_id, hero_variant, action (play/details) | PRD-007 |
| `content_detail.view` | Content detail page opened | content_id, referrer (rail/search/deeplink/notification), content_type | PRD-004 |

#### Search Events

| Event Name | Trigger | Key Properties | PRD Reference |
|-----------|---------|----------------|---------------|
| `search.initiated` | User opens search interface | search_type (text/voice/conversational), referrer_screen | PRD-007 |
| `search.query` | Search query submitted | query_text, search_type, query_length, is_conversational | PRD-007 |
| `search.results` | Search results displayed | query_text, result_count, result_ids (top 10), latency_ms, ai_enhanced (bool) | PRD-007 |
| `search.result.click` | User selects a search result | query_text, content_id, result_position, time_to_click_ms | PRD-007 |
| `search.abandoned` | User exits search without selecting | query_text, results_seen_count, dwell_time_ms | PRD-007 |

#### EPG Events

| Event Name | Trigger | Key Properties | PRD Reference |
|-----------|---------|----------------|---------------|
| `epg.open` | EPG screen opened | epg_view (grid/your_schedule/family), referrer_screen | PRD-005 |
| `epg.navigate` | User navigates EPG grid | direction (time/channel), channels_scrolled, time_scrolled_hours | PRD-005 |
| `epg.program.select` | User selects a program in EPG | channel_id, program_id, action (watch/record/remind/details), is_live, is_ai_recommended | PRD-005 |
| `epg.filter.apply` | User applies channel filter | filter_type (favorites/genre/hd/package), filter_value | PRD-005 |

#### Playback Events

| Event Name | Trigger | Key Properties | PRD Reference |
|-----------|---------|----------------|---------------|
| `playback.requested` | User presses play | content_id, content_type (live/vod/catchup/startover/pvr), referrer | PRD-001-004 |
| `playback.started` | First frame rendered | content_id, content_type, start_time_ms, initial_bitrate_kbps, initial_resolution, cdn, drm_type | PRD-001-004 |
| `playback.heartbeat` | Every 30 seconds during playback | content_id, session_id, position_ms, bitrate_kbps, resolution, buffer_length_ms, dropped_frames, cdn | PRD-001-004 |
| `playback.paused` | User pauses | content_id, position_ms, content_type | PRD-001-004 |
| `playback.resumed` | User resumes from pause | content_id, position_ms, pause_duration_ms | PRD-001-004 |
| `playback.seeked` | User seeks to position | content_id, from_position_ms, to_position_ms, seek_method (scrub/chapter/skip_intro) | PRD-001-004 |
| `playback.quality_changed` | ABR bitrate switch | content_id, old_bitrate_kbps, new_bitrate_kbps, old_resolution, new_resolution, reason (abr/user_selection) | PRD-001-004 |
| `playback.rebuffer` | Rebuffering event | content_id, position_ms, rebuffer_duration_ms, bitrate_at_rebuffer | PRD-001-004 |
| `playback.error` | Playback error | content_id, error_code, error_message, error_category (drm/network/decode/manifest), position_ms | PRD-001-004 |
| `playback.stopped` | Playback ends | content_id, position_ms, total_duration_ms, completion_percent, stop_reason (user/end_of_content/error/session_limit) | PRD-001-004 |

#### Live TV Specific Events

| Event Name | Trigger | Key Properties | PRD Reference |
|-----------|---------|----------------|---------------|
| `channel.tune` | Channel change | channel_id, previous_channel_id, tune_source (epg/surfing/search/ai_suggestion), tune_time_ms | PRD-001 |
| `channel.tune_away` | User leaves channel | channel_id, view_duration_ms, tune_away_reason (channel_change/app_exit/recording_start) | PRD-001 |
| `startover.initiated` | User triggers start-over | channel_id, program_id, offset_from_start_ms, was_ai_suggested (bool) | PRD-002 |
| `catchup.play` | User plays catch-up content | channel_id, program_id, days_since_broadcast, was_ai_suggested (bool) | PRD-002 |

#### Recording Events

| Event Name | Trigger | Key Properties | PRD Reference |
|-----------|---------|----------------|---------------|
| `recording.scheduled` | User schedules recording | program_id, channel_id, recording_type (single/series), is_ai_suggested (bool), source (epg/search/notification) | PRD-003 |
| `recording.cancelled` | User cancels recording | recording_id, reason (user_cancel/quota_exceeded) | PRD-003 |
| `recording.played` | User plays a recording | recording_id, program_id, days_since_recorded | PRD-003 |
| `recording.deleted` | User deletes recording | recording_id, watched_percent, was_ai_suggested_delete (bool) | PRD-003 |

#### Notification Events

| Event Name | Trigger | Key Properties | PRD Reference |
|-----------|---------|----------------|---------------|
| `notification.received` | Push notification delivered | notification_id, notification_type (reminder/recommendation/system), ai_generated (bool) | PRD-007 |
| `notification.clicked` | User taps notification | notification_id, notification_type, action_taken (view/dismiss) | PRD-007 |
| `notification.dismissed` | User dismisses notification | notification_id, notification_type | PRD-007 |

#### Monetization Events

| Event Name | Trigger | Key Properties | PRD Reference |
|-----------|---------|----------------|---------------|
| `paywall.shown` | Entitlement denial triggers paywall | content_id, paywall_type (subscribe/tvod_rent/tvod_buy/upgrade), current_tier | PRD-004 |
| `paywall.action` | User interacts with paywall | content_id, action (subscribe/rent/buy/dismiss), price, currency | PRD-004 |
| `purchase.completed` | TVOD transaction completes | content_id, transaction_type (rental/purchase), price, currency, payment_method | PRD-004 |

### 2.2 Common Event Envelope

Every client event is wrapped in a standard envelope:

```json
{
  "event_id": "evt_a1b2c3d4-e5f6-7890",
  "event_name": "playback.started",
  "event_timestamp": "2026-02-08T14:30:00.123Z",
  "client_timestamp": "2026-02-08T14:29:59.987Z",
  "session_id": "sess_m1n2o3p4",
  "user_id": "usr_x1y2z3",
  "profile_id": "prf_a1b2c3",
  "device_id": "dev_d1e2f3",
  "device_type": "android_tv",
  "platform": "android_tv",
  "app_version": "2.3.1",
  "os_version": "Android TV 14",
  "market": "GB",
  "connection_type": "wifi",
  "consent": {
    "analytics": true,
    "personalization": true,
    "ad_targeting": false
  },
  "properties": {
    "content_id": "vod_12345",
    "content_type": "vod",
    "start_time_ms": 1847,
    "initial_bitrate_kbps": 4500,
    "initial_resolution": "1080p",
    "cdn": "akamai",
    "drm_type": "widevine"
  }
}
```

### 2.3 Client-Side Batching & Delivery

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Batch interval | 5 seconds | Balance between real-time and network efficiency |
| Batch size limit | 20 events | Prevent oversized payloads on bursty interactions |
| Max payload size | 100 KB | Protects against client bugs flooding the collector |
| Retry policy | Exponential backoff: 1s, 2s, 4s, 8s, max 60s | Handle transient collector failures |
| Offline buffer | Up to 1,000 events stored locally | Mobile clients in poor connectivity can buffer events and flush on reconnect |
| Transport | HTTPS POST to `/v1/events` | Standard encrypted transport |
| Compression | gzip | Reduces payload size by ~70% for batched events |
| Authentication | Access token (JWT) in Authorization header | Events are attributable to authenticated users |

---

## 3. Server-Side Event Collection

Server-side events are published directly to Kafka by backend microservices. These events capture what the system did, not what the user saw (that is the client's responsibility).

### 3.1 Key Server-Side Events

| Topic | Event Examples | Producer | Throughput (Phase 1) |
|-------|---------------|----------|---------------------|
| `playback.sessions` | session.created, session.ended, session.error | Playback Session Service | ~5,000 msg/s |
| `playback.heartbeats` | heartbeat with position, quality metrics | Playback Session Service | ~50,000 msg/s |
| `catalog.changes` | title.added, title.updated, availability.changed | Catalog Service | ~50 msg/s |
| `epg.updates` | schedule.updated, program.changed | EPG Service | ~200 msg/s |
| `recommendations.served` | recommendation.request, recommendation.response | Recommendation Service | ~3,000 msg/s |
| `recordings.events` | recording.scheduled, recording.started, recording.completed | Recording Service | ~200 msg/s |
| `bookmarks.updates` | bookmark.set, bookmark.resumed | Bookmark Service | ~10,000 msg/s |
| `user.events` | auth events, profile changes, entitlement changes | Auth/User/Entitlement | ~500 msg/s |
| `qoe.metrics` | per-session QoE scores, degradation alerts | QoE Service | ~20,000 msg/s |
| `cdn.routing.events` | route.selected, cdn.switched | CDN Routing Service | ~5,000 msg/s |
| `search.queries` | query submitted, results served | Search Service | ~1,000 msg/s |
| `ad.events` | ad.decision, ad.impression, ad.completed | Ad Service | ~2,000 msg/s |
| `ai.features.updates` | feature vector updates | Feature Store | ~5,000 msg/s |
| `notifications.events` | sent, delivered, clicked | Notification Service | ~500 msg/s |
| `content.ingest.events` | ingest.started, ingest.completed, enrichment.completed | Content Ingest Service | ~10 msg/s |

### 3.2 Server-Side Event Enrichment

The Analytics Collector enriches client events before publishing to Kafka:

| Enrichment | Source | Purpose |
|------------|--------|---------|
| Geo-location (country, region, city) | IP → MaxMind GeoIP2 database | Regional analytics, geo-restriction validation |
| ISP identification | IP → MaxMind ISP database | QoE analysis by ISP |
| Device classification | User-Agent parsing + device_type from JWT | Device analytics, DRM level correlation |
| Content metadata | In-memory cache from Catalog Service | Denormalize content attributes (genre, channel name) for faster analytics queries |
| Subscription tier | From JWT claims | Segmented analytics without additional lookup |

---

## 4. Data Pipeline Architecture

### 4.1 High-Level Flow

```
Client Events ─────┐
                    │    ┌──────────────┐     ┌──────────────┐
                    ├───>│  Analytics    │────>│    Kafka     │
                    │    │  Collector    │     │  (Real-time  │
Server Events ──────┘    │  (Go)        │     │   cluster)   │
                         └──────────────┘     └──────┬───────┘
                                                     │
                              ┌───────────────┬──────┼───────────┬──────────────┐
                              │               │      │           │              │
                        ┌─────▼─────┐   ┌─────▼────┐│     ┌─────▼─────┐ ┌─────▼─────┐
                        │ Real-Time │   │  Flink   │      │   S3      │ │  Feature  │
                        │ Analytics │   │ Stream   │      │ (Iceberg) │ │  Store    │
                        │(ClickHouse│   │ Processing│     │ Data Lake │ │ (Feast)   │
                        │  / Druid) │   │          │      │           │ │           │
                        └─────┬─────┘   └─────┬────┘      └─────┬─────┘ └─────┬─────┘
                              │               │                  │              │
                        ┌─────▼─────┐   ┌─────▼────┐      ┌─────▼─────┐ ┌─────▼─────┐
                        │  Grafana  │   │  Alerts  │      │  Spark    │ │ ML Train  │
                        │ Dashboards│   │(PagerDuty│      │ Batch     │ │ Pipelines │
                        │           │   │  / Slack)│      │ Analytics │ │(SageMaker)│
                        └───────────┘   └──────────┘      └─────┬─────┘ └───────────┘
                                                                │
                                                          ┌─────▼─────┐
                                                          │    BI     │
                                                          │  Tools   │
                                                          │(Metabase/│
                                                          │ Superset)│
                                                          └───────────┘
```

### 4.2 Kafka Configuration

**Two Kafka clusters** (AWS MSK) with different profiles:

| Cluster | Brokers | Storage | Retention | Purpose |
|---------|---------|---------|-----------|---------|
| **Real-time** | 6 brokers (m5.2xlarge) | SSD (gp3) | 3 days | Playback events, session events, real-time signals for Flink/ClickHouse |
| **Analytics** | 4 brokers (m5.xlarge) | HDD (st1) | 30 days | All events mirrored for batch processing, ML training, compliance |

**Event routing:** The Analytics Collector publishes client events to the real-time cluster. A Kafka MirrorMaker 2 instance replicates all topics from the real-time cluster to the analytics cluster. Server-side services publish directly to the real-time cluster.

### 4.3 Stream Processing (Apache Flink)

Flink jobs consume from Kafka and produce:

| Flink Job | Input Topics | Output | Purpose | Latency |
|-----------|-------------|--------|---------|---------|
| **Session aggregator** | playback.heartbeats, playback.sessions | ClickHouse (real-time), S3 (Iceberg) | Aggregate heartbeats into per-session summaries | < 30s |
| **QoE calculator** | playback.heartbeats, cdn.routing.events | qoe.metrics (Kafka), ClickHouse | Compute real-time QoE scores per session | < 10s |
| **Concurrent viewer counter** | playback.sessions | ClickHouse, Grafana (push) | Count concurrent viewers per channel, per content, per platform | < 5s |
| **Feature extractor** | All user-facing events | Feature Store (Redis via Feast) | Update user viewing history features, content popularity features | < 60s |
| **Anomaly baseline** | All service metrics | AI anomaly model input | Compute rolling baselines for anomaly detection | < 60s |
| **Event deduplicator** | All client events | Deduplicated Kafka topic | Remove duplicate events (client retries, network glitches) | < 5s |

### 4.4 Data Lake (S3 + Apache Iceberg)

Events land in the data lake organized by the medallion architecture:

**Bronze Layer (Raw):**
- All events as received from Kafka, in Avro format.
- Partitioned by: `event_date` / `event_hour` / `event_name`.
- Retention: 90 days.
- No transformations — raw data for debugging and reprocessing.

**Silver Layer (Cleaned):**
- Deduplicated, schema-validated, and enriched events.
- Format: Parquet on Apache Iceberg tables.
- Partitioned by: `event_date` / `content_type` / `platform`.
- Enrichments: content metadata joined, geo enrichment, session grouping.
- Retention: 1 year.

**Gold Layer (Aggregated):**
- Pre-computed aggregations optimized for BI queries.
- Format: Parquet on Apache Iceberg tables.
- Key aggregation tables:

| Table | Granularity | Key Dimensions | Key Metrics |
|-------|-------------|----------------|-------------|
| `daily_active_users` | Day | market, platform, subscription_tier | unique_users, sessions, avg_session_duration |
| `content_engagement` | Day × Content | content_id, content_type | views, completions, avg_watch_time, completion_rate |
| `channel_performance` | Hour × Channel | channel_id, market | viewers, avg_view_duration, tune_ins, tune_aways |
| `search_performance` | Day | search_type, market | queries, result_clicks, zero_result_rate, avg_rank_clicked |
| `recommendation_performance` | Day × Surface | rail_type, algorithm_variant | impressions, clicks, ctr, resulting_play_rate |
| `recording_activity` | Day | market, recording_type | scheduled, completed, played, deleted, quota_utilization |
| `qoe_summary` | Hour | platform, cdn, isp, market | avg_score, p25_score, start_time_p95, rebuffer_ratio |
| `monetization_funnel` | Day | market, paywall_type | paywall_views, actions, conversions, revenue |

- Retention: Indefinite (aggregated data is compact).

---

## 5. Real-Time Analytics

### 5.1 Real-Time Database (ClickHouse)

ClickHouse stores time-series analytics data optimized for sub-second OLAP queries:

**Key tables:**

| Table | Engine | Ingestion | Retention (Hot) | Retention (Total) |
|-------|--------|-----------|-----------------|-------------------|
| `playback_sessions` | ReplacingMergeTree | Flink → ClickHouse (Kafka Engine) | 30 days | 1 year (tiered to S3) |
| `concurrent_viewers` | SummingMergeTree | Flink → ClickHouse | 7 days | 90 days |
| `qoe_scores` | MergeTree | QoE Service → Kafka → ClickHouse | 30 days | 1 year |
| `channel_tune_events` | MergeTree | Analytics Collector → Kafka → ClickHouse | 30 days | 1 year |
| `error_events` | MergeTree | Kafka → ClickHouse | 90 days | 1 year |
| `cdn_performance` | AggregatingMergeTree | CDN Routing → Kafka → ClickHouse | 30 days | 1 year |

### 5.2 Real-Time Queries

ClickHouse powers the operational dashboards (Grafana) with queries like:

**Concurrent viewers by channel (last 5 minutes):**
```sql
SELECT channel_id, count(DISTINCT session_id) AS viewers
FROM concurrent_viewers
WHERE event_time >= now() - INTERVAL 5 MINUTE
GROUP BY channel_id
ORDER BY viewers DESC
```

**QoE degradation by CDN (last hour):**
```sql
SELECT cdn, quantile(0.25)(qoe_score) AS p25_score,
       avg(qoe_score) AS avg_score,
       count(*) AS sessions
FROM qoe_scores
WHERE event_time >= now() - INTERVAL 1 HOUR
GROUP BY cdn
HAVING p25_score < 70
```

**Playback error rate by platform (last 15 minutes):**
```sql
SELECT platform,
       countIf(event_name = 'playback.error') AS errors,
       countIf(event_name = 'playback.started') AS starts,
       errors / starts AS error_rate
FROM playback_sessions
WHERE event_time >= now() - INTERVAL 15 MINUTE
GROUP BY platform
```

### 5.3 Real-Time Alerting

Real-time alerts are triggered from Flink stream processing and ClickHouse queries:

| Alert | Condition | Severity | Notification |
|-------|-----------|----------|-------------|
| QoE degradation | p25 QoE score < 70 for any (CDN, ISP, region) segment for > 5 min | P1 | PagerDuty + Slack |
| Playback error spike | Error rate > 5% for any platform for > 3 min | P1 | PagerDuty + Slack |
| Concurrent viewer drop | > 20% drop in concurrent viewers within 5 min (compared to same time yesterday) | P2 | Slack |
| Channel outage | Zero viewers on a channel that had > 100 viewers 10 min ago | P1 | PagerDuty |
| CDN performance | First byte latency p95 > 200ms for any CDN for > 5 min | P2 | Slack |
| Login failure spike | Login failure rate > 20% for > 5 min | P1 | PagerDuty + Slack |
| Recording failure | Recording failure rate > 5% for > 10 min | P2 | Slack |

---

## 6. Batch Analytics & Reporting

### 6.1 Batch Processing (Apache Spark)

Daily and weekly batch jobs run on Spark (EMR) against the Silver layer (Iceberg tables):

| Job | Schedule | Input | Output | Purpose |
|-----|----------|-------|--------|---------|
| Daily engagement report | Daily 02:00 UTC | Silver: all user events | Gold: daily_active_users, content_engagement | Executive KPIs |
| Weekly content performance | Weekly (Monday 04:00 UTC) | Silver: playback events, catalog | Gold: content_engagement (weekly rollup) | Content team reporting |
| Churn feature computation | Daily 03:00 UTC | Silver: all user events (28-day window) | Feature Store (offline) | Churn prediction model input |
| Recommendation evaluation | Daily 05:00 UTC | Silver: recommendation + playback events | Gold: recommendation_performance | ML team model evaluation |
| EPG engagement | Daily 02:30 UTC | Silver: EPG + playback events | Gold: channel_performance | Content scheduling insights |
| Recording analytics | Daily 03:30 UTC | Silver: recording events | Gold: recording_activity | PVR capacity planning, AI suggestion evaluation |
| Search effectiveness | Daily 04:00 UTC | Silver: search events | Gold: search_performance | Search quality improvement |
| Funnel analysis | Daily 06:00 UTC | Silver: navigation + monetization events | Gold: monetization_funnel | Conversion optimization |

### 6.2 Key Business Reports

**Daily Executive Dashboard (automated, emailed at 08:00 local):**
- Daily active users (DAU) by market and platform
- Concurrent viewer peak and average
- Playback starts by content type (live/VOD/catch-up/PVR)
- Top 10 content by views
- QoE average score and trend
- Churn risk: new high-risk users identified
- Revenue: TVOD transactions, subscription changes

**Weekly Content Performance Report:**
- Content catalog growth (titles added/removed)
- Top 20 content by engagement (unique viewers x completion rate)
- Content discovery effectiveness (recommendation CTR, search success rate)
- AI recommendation hit rate vs editorial curation
- Recording popularity (most recorded programs)
- Catch-up viewing patterns (most caught-up programs)

**Monthly Business Review:**
- MAU, DAU/MAU ratio
- ARPU by subscription tier and market
- Churn rate (actual vs predicted)
- Feature adoption rates (AI search, personalized EPG, smart recordings)
- Platform cost per stream
- Content ROI analysis (top/bottom performers vs acquisition cost)

---

## 7. ML Training Data Pipeline

### 7.1 From Events to Features

The analytics pipeline is the primary source of training data for all ML models:

```
Client/Server Events
        │
        ▼
    Kafka Topics
        │
        ├──── Flink (real-time) ──── Online Feature Store (Redis)
        │                              Used by: Real-time inference
        │                              Latency: < 10ms
        │
        └──── S3/Iceberg (batch) ──── Spark Feature Jobs ──── Offline Feature Store (S3)
                                                                Used by: Model training
                                                                Latency: Daily refresh
```

### 7.2 Feature Groups Fed by Analytics

| Feature Group | Source Events | Features | Update | Consumer Models |
|---------------|-------------|----------|--------|-----------------|
| **User viewing history** | playback.started, playback.stopped | last_30_day_genres (vector), avg_session_duration, completion_rate, viewing_hours_per_dow, preferred_content_type | Every playback event | Recommendation, Churn, EPG Personalization |
| **User interaction signals** | tile.click, rail.scroll, search.query, search.result.click | click_through_rate, search_frequency, browse_depth, genre_click_distribution | Every interaction event | Recommendation, Personalized Thumbnails |
| **Content popularity** | playback.started, playback.stopped | hourly_viewers, daily_unique_viewers, completion_rate, trending_velocity | Hourly | Recommendation (trending), EPG ("popular now") |
| **Content engagement** | playback events (all) | avg_watch_time, drop_off_curve, skip_intro_rate, binge_rate | Daily | Content Valuation, Recommendation |
| **Channel performance** | channel.tune, channel.tune_away | avg_tune_duration, tune_time_patterns, channel_flow_matrix | Hourly | Smart Channel Ordering, Predictive Cache |
| **QoE signals** | playback.heartbeat, playback.error, playback.rebuffer | avg_qoe_score, rebuffer_frequency, error_rate_by_cdn, start_time_trend | Every heartbeat | CDN Routing, ABR Optimization |
| **Session context** | app.launch, playback.started | time_of_day, day_of_week, device_type, connection_type, session_number_today | Every session | Context-Aware Recommendation |
| **Churn signals** | All user events (28-day window) | engagement_trend, login_frequency_trend, support_contact_count, payment_failure_count, viewing_hours_delta | Daily | Churn Prediction |

### 7.3 Training Data Generation

Training datasets are generated by Spark jobs that:

1. Extract features from the offline Feature Store with point-in-time correctness (features as they were at the time of the event, not as they are now).
2. Join features with labels (e.g., for recommendation: did the user watch the recommended content? For churn: did the user cancel within 30 days?).
3. Apply sampling and balancing (e.g., negative sampling for recommendation, class balancing for churn).
4. Output as Parquet files on S3, registered in the MLflow experiment.

**Data freshness targets:**

| Model | Training Data Freshness | Retraining Frequency |
|-------|------------------------|---------------------|
| Recommendation (collaborative) | Yesterday's events | Every 6 hours |
| Recommendation (content-based) | Latest catalog + embeddings | Daily |
| Churn prediction | 28-day rolling window through yesterday | Daily |
| CDN routing | Last 24 hours of CDN metrics | Hourly |
| Anomaly detection | 30-day rolling baseline | Weekly |
| Content moderation | Static training set + human feedback | Monthly |

---

## 8. Privacy, Consent & GDPR

### 8.1 Consent Model

The platform operates on a consent-based data collection model compliant with GDPR, ePrivacy Directive, and CCPA:

| Consent Category | Scope | Default (EU) | Default (US) | Revocable |
|-----------------|-------|-------------|-------------|-----------|
| **Essential** | Authentication, entitlement checks, playback session management, security logging | Always on (legal basis: legitimate interest) | Always on | No |
| **Analytics** | Viewing behavior, navigation patterns, feature usage, QoE metrics | Opt-in (consent required) | On (opt-out) | Yes |
| **Personalization** | Recommendation signals, AI model training, personalized EPG, content suggestions | Opt-in (consent required) | On (opt-out) | Yes |
| **Ad Targeting** | Behavioral ad targeting, interest-based ad selection | Opt-in (consent required) | On (opt-out) | Yes |

### 8.2 Consent Enforcement

Consent status is stored per user in the User Service and included in the JWT access token (the `consent` object). The Analytics Collector enforces consent at the point of collection:

| Consent Status | Client Behavior | Collector Behavior | Data Lake Behavior |
|---------------|----------------|-------------------|-------------------|
| Analytics = false | Client still sends events (for Essential category) | Collector drops non-essential events | N/A (events not stored) |
| Personalization = false | Client includes `personalization: false` flag | Collector tags events with `no_personalization` | ML pipeline excludes these events from training data |
| Ad Targeting = false | Client includes `ad_targeting: false` flag | Collector tags events | Ad Service does not use these events for targeting |

### 8.3 Data Minimization

- **User IDs are pseudonymized** in the analytics pipeline. The data lake stores a hashed user ID (`SHA-256(user_id + salt)`). The mapping from hash to real user ID is stored separately in the User Service and is only used for data subject access requests (DSAR).
- **IP addresses** are truncated to /24 (IPv4) or /48 (IPv6) before storage in the data lake. Full IP is used for geo-enrichment and then discarded.
- **PII fields** (email, name, phone) are never included in analytics events. If a service accidentally includes PII, the Analytics Collector strips it (PII detection rules based on regex patterns).
- **Retention limits** are enforced at the data lake level. Bronze data is auto-deleted after 90 days. Silver data after 1 year. Audit logs are retained for 7 years per regulatory requirements.

### 8.4 Data Subject Rights (GDPR)

| Right | Implementation | SLA |
|-------|---------------|-----|
| **Right of Access (DSAR)** | Automated export of all data associated with a user ID (User Service, Entitlement, Playback history, Recordings, Analytics events via hash lookup) | 30 days (target: 72 hours automated) |
| **Right to Erasure** | User Service marks user as deleted → Kafka event → all services purge user data → data lake purge job runs (deletes or anonymizes events by user hash) | 30 days (target: 7 days automated) |
| **Right to Rectification** | User can update profile data via account settings. Historical analytics events are not retroactively corrected (they reflect the state at the time). | Immediate for profile data |
| **Right to Data Portability** | Automated JSON export of user data (profile, viewing history, recordings list, preferences) | 30 days (target: 72 hours automated) |
| **Right to Restrict Processing** | Consent withdrawal (see Consent Model). Processing stops for non-essential categories. | Immediate (next event collection cycle) |

### 8.5 Kids Profile Data Protection

For profiles classified as kids profiles (COPPA and GDPR age restrictions):

- No behavioral data is used for ad targeting (ever, regardless of consent).
- Viewing data is collected for platform improvement (analytics consent) but is aggregated (no per-user storage) and never used for individual profiling.
- No third-party data sharing for kids profile data.
- Kids profile data is excluded from ML training datasets used for ad optimization or churn prediction.
- Kids profile data may be used for content safety ML models (age-appropriate content classification) after anonymization.

---

## 9. Key Dashboards & Reports

### 9.1 Dashboard Hierarchy

| Dashboard | Audience | Refresh Rate | Data Source | Key Panels |
|-----------|----------|-------------|-------------|-----------|
| **Executive Overview** | C-suite, VP Product | Hourly | Gold layer (batch) | DAU, MAU, ARPU, churn rate, content hours consumed, revenue |
| **Live Operations** | SRE, NOC | Real-time (5s) | ClickHouse (real-time) | Concurrent viewers, QoE score, error rates, CDN status, active incidents |
| **Live TV Control Room** | Content Ops, NOC | Real-time (5s) | ClickHouse | Per-channel viewer count, channel QoE, encoder status, EPG schedule overlay |
| **Content Performance** | Content team, Editorial | Daily | Gold layer (batch) | Content engagement ranking, new content performance, genre trends, catch-up/PVR popularity |
| **AI/ML Effectiveness** | ML Engineers, Product | Daily | Gold layer + MLflow | Recommendation CTR, A/B experiment results, model latency, feature drift indicators, fallback rate |
| **Search & Discovery** | Product, Search team | Daily | Gold layer | Search success rate, zero-result rate, conversational search adoption, top queries, search-to-play conversion |
| **Recording Analytics** | Product, Capacity | Daily | Gold layer | Recording volume, quota utilization, AI suggestion acceptance rate, storage growth projection |
| **Monetization** | Business, Finance | Daily | Gold layer | TVOD revenue, subscription conversions, paywall conversion rate, churn prediction accuracy |
| **Platform Health per Service** | Service owners | Real-time (15s) | Prometheus/Grafana | RED metrics (rate, errors, duration), dependency health, deployment status, resource utilization |
| **Client Performance** | Client Engineers | Daily | Gold layer + ClickHouse | App launch time per platform, playback start time, crash rate, ANR rate, memory usage |

### 9.2 Key Metrics Definitions

| Metric | Definition | Calculation | Target |
|--------|-----------|-------------|--------|
| **DAU** | Unique users with at least one playback event per day | `COUNT(DISTINCT user_id) WHERE event_name IN ('playback.started')` | Growth > 5% MoM |
| **Engagement Rate** | DAU / MAU | `DAU / COUNT(DISTINCT user_id in last 30 days)` | > 40% |
| **Content Hours** | Total hours of content consumed per day | `SUM(session_duration_ms) / 3600000` | Growth > 3% MoM |
| **Avg Session Duration** | Mean playback session length | `AVG(session_duration_ms)` | > 25 minutes |
| **Completion Rate** | % of VOD content watched to > 90% | `COUNT(completion > 90%) / COUNT(*)` for VOD | > 65% |
| **Recommendation CTR** | Click-through rate on AI recommendation rails | `tile.click / tile.impression` for AI rails | > 8% |
| **Search Success Rate** | % of searches resulting in a playback within 5 min | `COUNT(search → play within 300s) / COUNT(search.query)` | > 60% |
| **Channel Tune Time (p95)** | Time from channel select to first frame | `PERCENTILE(tune_time_ms, 0.95)` | < 1.5s |
| **VOD Start Time (p95)** | Time from play to first frame for VOD | `PERCENTILE(start_time_ms, 0.95)` | < 2.0s |
| **Rebuffer Ratio** | % of playback time spent rebuffering | `SUM(rebuffer_duration) / SUM(session_duration)` | < 0.2% |
| **QoE Score (p25)** | 25th percentile session quality score | `PERCENTILE(qoe_score, 0.25)` | > 75 |
| **AI PVR Suggestion Acceptance** | % of AI recording suggestions accepted by user | `COUNT(recording.scheduled WHERE ai_suggested) / COUNT(ai_suggestion.shown)` | > 15% |

---

## 10. Event Schema Standards

### 10.1 Schema Registry

All event schemas are registered in the Confluent Schema Registry:

- **Format:** Apache Avro
- **Compatibility mode:** FORWARD (new fields may be added with defaults; existing fields may not be removed)
- **Naming convention:** `com.platform.events.{domain}.{EventName}` (e.g., `com.platform.events.playback.PlaybackStarted`)
- **Versioning:** Schema versions are auto-incremented by the registry. Breaking changes require a new topic.

### 10.2 Common Schema Fields

Every event schema includes these common fields (defined in a shared Avro record `EventEnvelope`):

```avro
{
  "type": "record",
  "name": "EventEnvelope",
  "namespace": "com.platform.events.common",
  "fields": [
    {"name": "event_id", "type": "string", "doc": "Unique event identifier (UUID v7)"},
    {"name": "event_name", "type": "string", "doc": "Event type name"},
    {"name": "event_timestamp", "type": "long", "logicalType": "timestamp-millis", "doc": "Server receipt time"},
    {"name": "client_timestamp", "type": ["null", "long"], "logicalType": "timestamp-millis", "default": null, "doc": "Client-side event time"},
    {"name": "source", "type": {"type": "enum", "name": "EventSource", "symbols": ["CLIENT", "SERVER"]}, "doc": "Event origin"},
    {"name": "user_id", "type": ["null", "string"], "default": null, "doc": "Pseudonymized user ID"},
    {"name": "profile_id", "type": ["null", "string"], "default": null, "doc": "Active profile ID"},
    {"name": "session_id", "type": ["null", "string"], "default": null, "doc": "Application session ID"},
    {"name": "device_id", "type": ["null", "string"], "default": null, "doc": "Device identifier"},
    {"name": "platform", "type": ["null", "string"], "default": null, "doc": "Client platform (android_tv, ios, web, etc.)"},
    {"name": "market", "type": ["null", "string"], "default": null, "doc": "ISO 3166-1 market code"},
    {"name": "app_version", "type": ["null", "string"], "default": null, "doc": "Client application version"}
  ]
}
```

### 10.3 Schema Governance

- **Ownership:** Each Kafka topic and its schema are owned by the producing service. The owning team is responsible for schema documentation and evolution.
- **Review process:** Schema changes require review by the Data Platform team before registration (prevents breaking downstream consumers).
- **Documentation:** Each schema field includes a `doc` attribute describing its purpose and expected values.
- **Testing:** Schema compatibility is validated in CI/CD. A failed compatibility check blocks deployment.

---

## 11. Data Quality & Governance

### 11.1 Data Quality Checks

| Check | Stage | Mechanism | Action on Failure |
|-------|-------|-----------|-------------------|
| Schema validation | Analytics Collector | Avro schema validation at ingestion | Event rejected, error logged, client notified via response code |
| Timestamp sanity | Analytics Collector | Client timestamp within ±5 minutes of server time | Event enriched with server timestamp; client timestamp flagged as unreliable |
| Duplicate detection | Flink deduplicator | Event ID uniqueness within a 1-hour window | Duplicate events dropped |
| Missing required fields | Analytics Collector | Null-check on essential fields (event_name, session_id) | Event rejected |
| Referential integrity | Batch (Spark) | Content IDs and channel IDs exist in catalog/EPG | Orphaned events flagged for investigation (content may have been removed) |
| Volume anomalies | Monitoring (Grafana) | Per-topic event volume compared to same hour last week | Alert if volume differs by > 50% |
| Freshness monitoring | Monitoring (Grafana) | Time since last event on each topic | Alert if topic is silent for > 5 minutes (production hours) |

### 11.2 Data Lineage

Data lineage is tracked through:

- **Kafka headers:** Each event carries a `trace_id` (OpenTelemetry) linking it to the originating user request.
- **Flink processing tags:** Flink jobs stamp processed events with job ID and processing timestamp.
- **Iceberg metadata:** Iceberg tables maintain snapshots and manifest lists that record which Flink/Spark job produced each set of data files.
- **Data catalog:** A metadata catalog (Apache Atlas or DataHub) indexes all Kafka topics, Iceberg tables, Gold aggregations, and Feature Store feature groups with ownership, schema, lineage, and freshness metadata.

### 11.3 Data Access Control

| Data Layer | Access Level | Who |
|-----------|-------------|-----|
| Kafka (real-time) | Service accounts only | Backend services via mTLS (Istio) |
| Bronze (raw events) | Read: Data Engineers, ML Engineers | IAM roles, time-limited credentials |
| Silver (cleaned events) | Read: Data Engineers, ML Engineers, BI Analysts | IAM roles |
| Gold (aggregated) | Read: All engineering, Product, Business | IAM roles, BI tool service accounts |
| PII-containing tables | Read: Compliance team, DPO | Separate IAM role, audit-logged access |
| ML training data | Read: ML Engineers | SageMaker execution role |

---

*This document defines the analytics and telemetry architecture that feeds real-time operations, business intelligence, and the AI/ML layer. All client engineers should implement the client-side event taxonomy. All backend services should publish events to the designated Kafka topics with the correct Avro schemas. The Data Platform team owns the pipeline from Kafka to the data lake, and the ML team owns the Feature Store and training data pipelines.*
