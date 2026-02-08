# Integration Points
## Cross-Cutting Concerns — AI-Native OTT Streaming Platform

**Document ID:** XC-004
**Version:** 1.0
**Date:** 2026-02-08
**Status:** Draft
**Author:** Integration Analyst Agent
**References:** ARCH-001, VIS-001, PRD-001 through PRD-008, XC-001 through XC-003
**Audience:** Backend Engineers, Platform Architects, SRE, Integration Engineers

---

## Table of Contents

1. [Overview](#1-overview)
2. [Service Dependency Map](#2-service-dependency-map)
3. [API Gateway Configuration](#3-api-gateway-configuration)
4. [Kafka Topic Ownership](#4-kafka-topic-ownership)
5. [Third-Party Integrations](#5-third-party-integrations)
6. [Data Flow: User Starts Watching Live TV](#6-data-flow-user-starts-watching-live-tv)
7. [Data Flow: User Records a Program](#7-data-flow-user-records-a-program)
8. [Data Flow: User Browses and Plays VOD](#8-data-flow-user-browses-and-plays-vod)
9. [Data Flow: AI Generates a Recommendation](#9-data-flow-ai-generates-a-recommendation)
10. [Data Flow: Content Is Ingested and Becomes Available](#10-data-flow-content-is-ingested-and-becomes-available)
11. [Error Handling & Fallback Patterns](#11-error-handling--fallback-patterns)
12. [Integration Testing Strategy](#12-integration-testing-strategy)

---

## 1. Overview

The platform comprises 20+ microservices, 3 BFF layers, multiple AI/ML serving components, and a dozen third-party integrations. This document maps every service-to-service dependency, defines the contracts and SLAs for each integration point, and traces the data flows for the five most critical user journeys across the system.

### Integration Principles

- **API contracts are the source of truth.** Every service-to-service integration is defined by a versioned API contract (gRPC protobuf or OpenAPI 3.1). Changes to contracts require backward-compatible evolution or a new version.
- **Synchronous for the request path, asynchronous for everything else.** The playback start path (user presses play → video starts) uses synchronous gRPC calls for latency-critical steps. All side effects (analytics, bookmark updates, recommendation signals) are asynchronous via Kafka.
- **Every integration has a fallback.** If a dependency is unavailable, the calling service degrades gracefully rather than failing completely. Fallback behaviors are documented per integration point.
- **Circuit breakers everywhere.** All synchronous service-to-service calls use circuit breakers (via Istio or application-level) to prevent cascade failures. Circuit breaker settings: 5 consecutive failures → open for 30 seconds → half-open probe.
- **Timeouts are explicit.** Every gRPC and HTTP call has an explicit timeout. No service waits indefinitely for another.

---

## 2. Service Dependency Map

### 2.1 Critical Path Dependencies (Playback Start)

These dependencies are in the synchronous playback start path. Failure of any of these blocks playback.

```
Client
  │
  ▼
BFF (TV/Mobile/Web)
  │
  ├──► Auth (JWT validation — local, no call needed)
  │
  ├──► Entitlement Service ──► Redis Cache ──► PostgreSQL
  │         │
  │         └──► Subscription Service (cache miss only)
  │
  ├──► Playback Session Service
  │         │
  │         ├──► CDN Routing Service ──► Redis (CDN metrics)
  │         │         │
  │         │         └──► QoE Service (CDN performance data)
  │         │
  │         ├──► Token Service (CAT) ──► Vault (signing key)
  │         │
  │         └──► Bookmark Service ──► Redis (resume position)
  │
  └──► Manifest Proxy ──► Origin (S3/USP)
```

**Total synchronous hops (worst case):** Client → BFF → 3 parallel calls (Entitlement + Playback Session + Bookmark) → Playback Session makes 2 parallel calls (CDN Routing + Token) → Response assembled.

**Target latency budget:**

| Hop | Service | Budget | Actual SLO |
|-----|---------|--------|-----------|
| 1 | BFF receives request, validates JWT | 5ms | p99 < 5ms |
| 2a | Entitlement check (Redis cache hit) | 30ms | p99 < 30ms |
| 2b | Playback Session creation | 100ms | p99 < 200ms |
| 2b.1 | CDN Routing decision | 30ms | p99 < 30ms |
| 2b.2 | CAT token issuance | 20ms | p99 < 20ms |
| 2c | Bookmark lookup (Redis) | 10ms | p99 < 50ms |
| 3 | BFF assembles response | 5ms | p99 < 5ms |
| **Total** | **End-to-end** | **200ms** | **p99 < 340ms** |

Steps 2a, 2b, and 2c are parallelized by the BFF. Steps 2b.1 and 2b.2 are parallelized by the Playback Session Service.

### 2.2 Full Service Dependency Matrix

| Service | Depends On (Synchronous) | Depends On (Asynchronous / Kafka) | Depended On By |
|---------|--------------------------|-----------------------------------|----------------|
| **TV BFF** | Auth (JWT), Entitlement, Playback Session, Bookmark, Catalog, EPG, Recommendation, Profile, Search, Recording | — | Client apps |
| **Mobile BFF** | Same as TV BFF + Notification registration | — | Client apps |
| **Web BFF** | Same as TV BFF | — | Client apps |
| **Auth Service** | User Service | `user.created` | All BFFs (JWT validation is local) |
| **User Service** | PostgreSQL | — | Auth, Profile, Entitlement, Notification |
| **Profile Service** | User Service, PostgreSQL | `user.created` | BFFs, Recommendation, Bookmark |
| **Entitlement Service** | Redis, PostgreSQL, Subscription Service | `subscription.changed`, `tvod.purchased`, `promotion.activated` | BFFs, Playback Session, Recording, Catalog (filtering) |
| **Subscription Service** | PostgreSQL, Payment Provider (Stripe/Adyen) | — | Entitlement |
| **Catalog Service** | PostgreSQL, Elasticsearch, Redis, Metadata Service | `ingest.completed`, `metadata.enriched`, `catalog.availability.changed` | BFFs, Recommendation, Search |
| **Metadata Service** | PostgreSQL + pgvector, Redis | `ingest.completed`, `ai.enrichment.completed` | Catalog, Search, Recommendation |
| **EPG Service** | PostgreSQL, Redis | `epg.ingest.completed` | BFFs, Recording, Schedule, Recommendation |
| **Playback Session Service** | Entitlement, CDN Routing, Token Service, Bookmark, Redis, PostgreSQL | `entitlement.checked` | BFFs |
| **Bookmark Service** | Redis, PostgreSQL, Profile Service | `playback.heartbeat`, `playback.stopped` | BFFs, Playback Session |
| **Recording Service** | EPG, Entitlement, PostgreSQL, Redis | `epg.schedule.updated` | BFFs |
| **Schedule Service** | EPG, Notification, PostgreSQL | `epg.schedule.updated`, `recording.scheduled` | BFFs |
| **Recommendation Service** | Feature Store, AI Model Serving, Catalog, pgvector, Redis | `playback.started`, `playback.stopped`, `catalog.title.added` | BFFs |
| **Search Service** | Elasticsearch, pgvector, Redis, (Bedrock for conversational) | `catalog.title.added`, `metadata.enriched` | BFFs |
| **CDN Routing Service** | Redis (CDN metrics), QoE Service | `playback.heartbeat`, `qoe.metric` | Playback Session |
| **Token Service (CAT)** | Vault (signing keys), Redis | `playback.started` | Playback Session |
| **Notification Service** | User Service, Profile Service, Redis, PostgreSQL, Push providers (FCM/APNs) | `schedule.reminder.triggered`, `recommendation.served` | BFFs (registration), Schedule |
| **Ad Service (SSAI)** | Playback Session, Entitlement, PostgreSQL, Redis, Ad Exchange | `playback.started`, `entitlement.checked` | Manifest Proxy |
| **QoE Service** | ClickHouse, Redis | `playback.heartbeat`, `playback.error` | CDN Routing, Dashboards |
| **Analytics Collector** | Kafka | All client events (via HTTPS) | Data lake, Feature Store, QoE |
| **Content Ingest Service** | S3, PostgreSQL, Encoding Pipeline | — | Catalog, Metadata |
| **Encoding Pipeline** | S3, GPU compute, Key Management Service | `ingest.completed` | Catalog (on completion) |
| **AI Model Serving (KServe)** | Feature Store, GPU compute | — | Recommendation, CDN Routing, Search |
| **Feature Store** | Redis (online), S3 (offline), Flink | All playback/browse events | AI Model Serving |

### 2.3 Dependency Risk Assessment

| Dependency | Blast Radius if Down | Mitigation |
|-----------|---------------------|------------|
| **Entitlement Service** | All playback blocked | Redis cache (60s TTL) serves stale entitlements. Fallback: allow playback for existing sessions, deny new sessions. |
| **Playback Session Service** | No new playback starts | No cache possible (stateful). Mitigation: multi-instance with zero-downtime deployment. |
| **CDN Routing Service** | Suboptimal CDN selection | Fallback: round-robin with geo-affinity. Playback still works, just not optimally routed. |
| **Token Service** | No CDN access (no valid CAT tokens) | Redis caches signing keys. Fallback: pre-issued long-lived tokens (15 min) for emergency mode. |
| **Recommendation Service** | No personalized content | Fallback: pre-computed popularity-based top-100 per genre (cached in Redis). |
| **EPG Service** | No EPG data | Redis cache serves stale EPG (up to 24h stale is acceptable for grid view). |
| **Kafka** | All async processing stops | Clients buffer events locally. Server-side producers buffer in-memory (up to 1 min). Core playback path is synchronous and unaffected. |
| **Redis** | Degraded performance across most services | Each service falls back to its PostgreSQL database. Latency increases but functionality preserved. |
| **Elasticsearch** | No search, degraded catalog browse | Fallback: basic PostgreSQL LIKE queries for search (very limited). Browse via Redis-cached category lists. |
| **Feature Store (online)** | AI models receive stale/default features | Models use default feature vectors. Recommendation quality degrades but service stays up. |

---

## 3. API Gateway Configuration

### 3.1 Kong API Gateway

Kong serves as the single entry point for all client-to-platform API traffic.

```
Internet → WAF (AWS WAF) → ALB → Kong API Gateway → BFF Layer → Backend Services
```

### 3.2 Route Configuration

| Route Pattern | Upstream | Auth Required | Rate Limit | Cache |
|--------------|----------|---------------|-----------|-------|
| `POST /v1/auth/login` | Auth Service (direct) | No | 10 req/min per IP | No |
| `POST /v1/auth/refresh` | Auth Service (direct) | Refresh token | 20 req/min per user | No |
| `POST /v1/auth/device/code` | Auth Service (direct) | No | 1 req/2 min per device | No |
| `GET /v1/tv/*` | TV BFF | JWT | 100 req/min per user | Varies by endpoint |
| `GET /v1/mobile/*` | Mobile BFF | JWT | 100 req/min per user | Varies by endpoint |
| `GET /v1/web/*` | Web BFF | JWT | 100 req/min per user | Varies by endpoint |
| `POST /v1/events` | Analytics Collector | JWT (or anonymous token) | 60 req/min per device | No |
| `POST /v1/drm/license` | DRM Proxy (via BFF) | Session token | 10 req/min per session | No |
| `GET /v1/health` | Kong health aggregator | No | None | No |

### 3.3 Kong Plugins

| Plugin | Purpose | Configuration |
|--------|---------|---------------|
| **JWT** | Validate access tokens on protected routes | RS256, key rotation via Vault integration |
| **Rate Limiting** | Prevent abuse, protect backends | Per-user (JWT `sub` claim), per-IP (anonymous), Redis-backed counters |
| **CORS** | Cross-origin support for web clients | Allow origins: platform domains only |
| **Request Transformer** | Add internal headers (trace ID, user ID) | Extract from JWT and inject into upstream request |
| **Response Transformer** | Strip internal headers from responses | Remove `X-Internal-*` headers |
| **IP Restriction** | Block known malicious IPs | Updated daily from threat intelligence feed |
| **Bot Detection** | Identify and block automated scrapers | User-Agent analysis + behavioral rate patterns |
| **Prometheus** | Expose gateway metrics | Per-route request count, latency, status code |
| **OpenTelemetry** | Inject trace context into upstream requests | W3C Trace Context propagation |

### 3.4 API Versioning

- **URL path versioning:** `/v1/`, `/v2/` etc.
- **Strategy:** New versions are introduced when breaking changes are required. Old versions are supported for a minimum of 6 months after the new version is stable.
- **Deprecation process:** Header `X-API-Deprecated: true` added to responses on deprecated endpoints. Client telemetry tracks usage of deprecated endpoints. Push notification to app developers (for third-party integrations) when deprecation is scheduled.

---

## 4. Kafka Topic Ownership

### 4.1 Topic Ownership Registry

Each Kafka topic has a single producing service (owner). Multiple services may consume from a topic.

| Topic | Owner (Producer) | Key Consumers | Partitions | Retention | Schema |
|-------|-----------------|---------------|-----------|-----------|--------|
| `playback.sessions` | Playback Session Service | Analytics, QoE, Feature Store | 32 | 3 days | `PlaybackSession.avsc` |
| `playback.heartbeats` | Playback Session Service | Bookmark, Analytics, QoE, Feature Store, CDN Routing | 64 | 1 day | `PlaybackHeartbeat.avsc` |
| `user.events` | User Service, Auth Service | Analytics, Entitlement, Profile, Notification | 16 | 7 days | `UserEvent.avsc` |
| `catalog.changes` | Catalog Service | Search, Recommendation, BFF cache, EPG | 8 | 30 days | `CatalogChange.avsc` |
| `epg.updates` | EPG Service | Recording, Schedule, BFF cache, Recommendation | 8 | 7 days | `EpgUpdate.avsc` |
| `recommendations.served` | Recommendation Service | Analytics, Feature Store | 16 | 3 days | `RecommendationServed.avsc` |
| `search.queries` | Search Service | Analytics, Feature Store | 8 | 3 days | `SearchQuery.avsc` |
| `recordings.events` | Recording Service | Analytics, Notification, EPG | 16 | 30 days | `RecordingEvent.avsc` |
| `bookmarks.updates` | Bookmark Service | Analytics, Feature Store | 32 | 7 days | `BookmarkUpdate.avsc` |
| `notifications.events` | Notification Service | Analytics | 8 | 7 days | `NotificationEvent.avsc` |
| `qoe.metrics` | QoE Service | CDN Routing, Analytics, Alerting | 32 | 3 days | `QoeMetric.avsc` |
| `cdn.routing.events` | CDN Routing Service | Analytics, QoE | 16 | 3 days | `CdnRoutingEvent.avsc` |
| `ad.events` | Ad Service | Analytics, Billing | 16 | 30 days | `AdEvent.avsc` |
| `ai.features.updates` | Feature Store | ML Model Serving | 16 | 7 days | `FeatureUpdate.avsc` |
| `content.ingest.events` | Content Ingest Service | Catalog, Metadata, Encoding Pipeline | 4 | 30 days | `IngestEvent.avsc` |
| `subscription.changed` | Subscription Service | Entitlement, Analytics, Notification | 8 | 30 days | `SubscriptionChanged.avsc` |
| `tvod.purchased` | Subscription Service | Entitlement, Analytics | 8 | 30 days | `TvodPurchased.avsc` |
| `promotion.activated` | Promotion Service | Entitlement, Analytics, Notification | 4 | 30 days | `PromotionActivated.avsc` |

### 4.2 Consumer Group Conventions

Consumer group naming: `{consuming-service}.{topic-name}.{purpose}`

Examples:
- `bookmark-service.playback-heartbeats.position-update`
- `analytics-collector.playback-sessions.data-lake-sink`
- `feature-store.playback-heartbeats.user-features`
- `qoe-service.playback-heartbeats.quality-scoring`

### 4.3 Kafka Governance Rules

- **Single owner per topic.** Only the owning service may produce to a topic. Other services that need to publish related events create their own topic.
- **Schema compatibility.** All schemas use FORWARD compatibility (consumers can read data written by a newer schema). Schema changes require Data Platform team review.
- **Partition key stability.** Partition keys (typically `user_id` or `content_id`) must not change once established. Repartitioning requires a new topic.
- **Consumer lag monitoring.** Every consumer group has a Grafana alert on consumer lag. Lag exceeding 5 minutes triggers a warning; lag exceeding 15 minutes triggers an alert.
- **Dead letter queues.** Every consumer group has a DLQ topic (`{topic}.dlq`) for messages that fail processing after 3 retries. DLQ topics are monitored and manually investigated.

---

## 5. Third-Party Integrations

### 5.1 Integration Registry

| Integration | Provider | Purpose | Protocol | SLA | Fallback | Owner Team |
|------------|----------|---------|----------|-----|----------|-----------|
| **CDN (Primary)** | Akamai | Global content delivery | HTTP/HTTPS, CDN API | 99.99% | CloudFront (secondary CDN) | Platform/CDN |
| **CDN (Secondary)** | Amazon CloudFront | Backup CDN, origin shield | HTTP/HTTPS, AWS SDK | 99.99% | Fastly (tertiary) | Platform/CDN |
| **CDN (Tertiary)** | Fastly | Regional CDN for specific markets | HTTP/HTTPS, Fastly API | 99.99% | Akamai | Platform/CDN |
| **DRM — Widevine** | Google | Widevine license server | Widevine Cloud API (REST) | 99.9% | Cached licenses (short-term) | Security |
| **DRM — FairPlay** | Apple | FairPlay key server module | HTTPS (custom protocol) | Self-hosted (99.95% target) | N/A (self-hosted) | Security |
| **DRM — PlayReady** | Microsoft | PlayReady license server | SOAP/REST | 99.9% | Cached licenses (short-term) | Security |
| **Payment** | Stripe / Adyen | TVOD payments, subscription billing | REST API | 99.99% | Queue failed payments for retry | Billing |
| **Push — Android** | Google FCM | Push notifications to Android devices | HTTP/2 (FCM API) | 99.95% | In-app notification on next launch | Client/Notification |
| **Push — Apple** | Apple APNs | Push notifications to iOS/tvOS devices | HTTP/2 (APNs) | 99.95% | In-app notification on next launch | Client/Notification |
| **EPG Data** | Gracenote / ERICSSON | Electronic program guide schedule data | XMLTV / REST API | 99.9% (data freshness: 15 min) | Cached EPG (up to 24h stale) | Content |
| **GeoIP** | MaxMind | IP geolocation and VPN detection | Local database (GeoIP2) | Self-hosted (100%) | N/A (local DB) | Platform |
| **LLM** | Amazon Bedrock | Conversational search, content summaries | AWS SDK (REST) | 99.9% | Keyword search fallback (Elasticsearch) | AI/ML |
| **QoE Analytics** | Conviva | Client-side video quality analytics | Conviva SDK → Conviva cloud | 99.9% | Custom QoE scoring (server-side only) | Platform/QoE |
| **Email** | Amazon SES | Transactional emails (verification, receipts) | AWS SDK | 99.9% | Queue and retry | Platform |
| **SMS** | Twilio (Phase 2) | 2FA, account recovery | REST API | 99.95% | Email fallback | Auth |
| **Encoding (Live)** | AWS Elemental MediaLive | Live transcoding | AWS SDK | 99.99% | Redundant encoder pair (active-standby) | Encoding |
| **Encoding (VOD)** | FFmpeg (self-hosted) | VOD transcoding | Internal (K8s jobs) | Self-hosted | Queue-based retry with spot instance fallback | Encoding |
| **Packaging (Live)** | Unified Streaming (USP) | Live CMAF packaging | HTTP API | Self-hosted (99.95% target) | AWS MediaPackage v2 (managed fallback) | Packaging |
| **Object Storage** | Amazon S3 | Media segments, data lake, artifacts | AWS SDK | 99.99% | Cross-region replication (Phase 3) | Platform |
| **Secrets** | HashiCorp Vault | Secrets, encryption keys, certificates | Vault API (via Agent sidecar) | Self-hosted (99.95% target) | Cached secrets (short-term) | Security |
| **Feature Flags** | Unleash | Feature flag management | REST API + SDK | Self-hosted (99.95% target) | Cached flag values on client (up to 24h stale) | Platform |

### 5.2 Integration Health Monitoring

Each third-party integration has a health check in the observability stack:

| Integration | Health Check Method | Interval | Alert Threshold |
|------------|-------------------|----------|-----------------|
| CDN (each provider) | Synthetic probe: fetch a known segment from edge | 30 seconds | 3 consecutive failures |
| DRM (Widevine) | License acquisition test with known key | 60 seconds | 2 consecutive failures |
| DRM (FairPlay) | License acquisition test | 60 seconds | 2 consecutive failures |
| Payment (Stripe) | Stripe API status endpoint | 60 seconds | 1 failure (critical path for purchases) |
| Push (FCM/APNs) | Send test notification to internal device | 5 minutes | 3 consecutive failures |
| EPG Data | Check last update timestamp vs expected | 5 minutes | No update in 30 minutes |
| Bedrock (LLM) | Inference test with known prompt | 60 seconds | 3 consecutive failures |
| Conviva | SDK heartbeat check | 5 minutes | No heartbeats received for 10 minutes |
| Vault | Vault health endpoint | 15 seconds | 1 failure (critical for DRM and auth) |

---

## 6. Data Flow: User Starts Watching Live TV

**Scenario:** A user on Android TV selects Channel 42 from the EPG to watch live football.

```
Step  Component               Action                                    Latency
─────────────────────────────────────────────────────────────────────────────────
1     Android TV Client       User presses OK on Channel 42             0ms
                              Client sends POST /v1/tv/playback/start
                              {channel_id: "ch-042", content_type: "live"}

2     Kong API Gateway        Validates JWT signature (local)            2ms
                              Rate limit check (Redis)
                              Routes to TV BFF

3     TV BFF                  Extracts user_id, profile_id from JWT     1ms
                              Initiates 3 parallel calls:

4a    Entitlement Service     CheckAccess(user, channel, "ch-042")     15ms
      (parallel)              Redis cache hit → user has Sports Package
                              Returns: {allowed: true, startover: true, pvr: true}

4b    Playback Session Svc    CreateSession(user, channel, device)      80ms
      (parallel)              │
      4b.1  CDN Routing Svc   │ SelectCDN(user_geo: "UK", isp: "BT",  20ms
            (sub-parallel)    │  content: "live", channel: "ch-042")
                              │ Redis: Akamai perf=good for UK/BT
                              │ Returns: cdn=akamai, edge=lon-edge-01
                              │
      4b.2  Token Service     │ IssueCAT(session, cdn: "akamai",       12ms
            (sub-parallel)    │  paths: ["/live/ch-042/*"])
                              │ Signs with ES256, 5-min expiry
                              │ Returns: cat_token
                              │
                              Assembles manifest URL:
                              https://lon-edge-01.akamai.net/live/ch-042/
                              master.m3u8?cat={token}
                              Creates session record in Redis

4c    Bookmark Service        GetBookmark(user, "ch-042")              8ms
      (parallel)              No bookmark for live → returns null

5     TV BFF                  Assembles response:                       3ms
                              {manifest_url, session_id, cat_token,
                               resume_position: null, drm_config: {
                                 system: "widevine", license_url: "..."
                               }, channel_meta: {name, logo, current_program}}

6     Android TV Client       ExoPlayer loads manifest                  50ms
                              Fetches DRM license (Widevine L1)         80ms
                              Acquires first segments from CDN           100ms
                              Renders first frame                        ~350ms total

7     Android TV Client       Begins heartbeat (every 30s)
      (async, ongoing)        Heartbeat → Kafka → Bookmark, Analytics,
                              QoE, Feature Store

8     Analytics Collector     Publishes `playback.started` event        async
      (async)                 to Kafka (playback.sessions topic)

9     QoE Service             Consumes heartbeats, computes QoE score   async
      (async)                 Alerts if score < 70 for this session
```

**Total time from button press to first frame: ~350ms (target: < 1,500ms p95).**

**Error scenarios:**

| Error | Detection | Handling |
|-------|-----------|----------|
| Entitlement denied | Step 4a returns `allowed: false` | BFF returns 403 with upgrade options. Client shows paywall. |
| CDN Routing fails | Step 4b.1 timeout (30ms) | Fallback: round-robin CDN selection. Playback proceeds with potentially suboptimal CDN. |
| Token Service fails | Step 4b.2 timeout (20ms) | Fallback: Playback Session issues a longer-lived token (15 min) directly. Reduced security window accepted temporarily. |
| DRM license fails | Step 6, license request returns error | Client retries once. If still failing, shows "Playback temporarily unavailable." |
| CDN segment fetch fails | Step 6, HTTP 4xx/5xx from CDN | Player retries on same CDN. After 3 failures, CDN Routing triggers mid-session switch to secondary CDN. |
| Stream limit exceeded | Step 4b, active session count >= max | BFF returns 409 with active device list. Client shows "Already watching on [device]." |

---

## 7. Data Flow: User Records a Program

**Scenario:** A user on iOS sees an AI suggestion "Record Champions League tonight at 20:00" and taps "Record."

```
Step  Component               Action                                    Latency
─────────────────────────────────────────────────────────────────────────────────
1     iOS Client              User taps "Record" on AI suggestion       0ms
                              Client sends POST /v1/mobile/recordings
                              {program_id: "prg-8821", channel_id: "ch-042",
                               recording_type: "single", source: "ai_suggestion"}

2     Kong API Gateway        JWT validation, rate limit, route         3ms

3     Mobile BFF              Extracts user context                     1ms
                              Calls Recording Service

4     Recording Service       Validates request:                        60ms
      │                       │
      4a  EPG Service         │ GetProgram("prg-8821")                 15ms
      │                       │ Returns: title, start: 20:00, end: 21:45,
      │                       │ channel: ch-042, pvr_allowed: true
      │                       │
      4b  Entitlement Service │ CheckAccess(user, channel: "ch-042",   12ms
      │                       │  right: "pvr")
      │                       │ Returns: {allowed: true, quota_remaining: 42h}
      │                       │
                              Validates: program exists, PVR rights OK,
                              quota sufficient (1h 45m < 42h remaining)
                              Creates recording record in PostgreSQL:
                              {id: "rec-5567", user_id, program_id, channel_id,
                               status: "scheduled", start_at, end_at}

5     Recording Service       Publishes `recording.scheduled` to Kafka  async
      (async)

6     Mobile BFF              Returns to client:                        2ms
                              {recording_id: "rec-5567", status: "scheduled",
                               program: {title, start, end, channel_name}}

7     iOS Client              Shows confirmation: "Recording scheduled" 0ms
                              Client sends analytics event:
                              recording.scheduled {ai_suggested: true}

--- At 20:00 (scheduled time) ---

8     Recording Service       Cron job detects due recording            0ms
      (scheduled)             Triggers recording start for rec-5567

9     Recording Service       The recording process is a metadata       5ms
                              operation — live content is already being
                              encoded and segmented (it is broadcast live).
                              Recording = entitlement pointer to the
                              live segment range [start_time, end_time]
                              on the content store.

10    Recording Service       Updates record: status = "recording"      10ms
                              Publishes `recording.started` to Kafka

--- At 21:45 (program end + 2 min buffer) ---

11    Recording Service       Detects program end (EPG boundary)        0ms
                              Updates record: status = "completed"
                              Publishes `recording.completed` to Kafka

12    Notification Service    Consumes `recording.completed`            async
      (async)                 Sends push notification to user:
                              "Champions League recording ready to watch"

13    Feature Store           Consumes `recording.scheduled` event      async
      (async)                 Updates user recording preferences:
                              {genre: "sports", ai_acceptance: +1}
                              Feeds recommendation model for future
                              AI recording suggestions
```

**Key integration points:**

| Integration | Contract | SLA | Fallback |
|-------------|----------|-----|----------|
| Recording → EPG | gRPC: `GetProgram(program_id)` | p99 < 100ms | Fail request (cannot schedule without program metadata) |
| Recording → Entitlement | gRPC: `CheckAccess(user, channel, "pvr")` | p99 < 30ms | Cache: if Entitlement Service is down but user had recent successful PVR check (within 5 min), allow scheduling optimistically |
| Recording → Kafka | Async: `recording.scheduled` event | p99 < 50ms | In-memory buffer (up to 60s). Recording proceeds regardless of Kafka availability. |
| Notification → Push (FCM/APNs) | HTTP/2: push notification | p99 < 1s delivery | In-app notification on next launch |

---

## 8. Data Flow: User Browses and Plays VOD

**Scenario:** A user on the web opens the home page, browses recommendations, selects a movie, and starts playback.

```
Step  Component               Action                                    Latency
─────────────────────────────────────────────────────────────────────────────────
1     Web Client              App launches, fetches home screen         0ms
                              GET /v1/web/home

2     Kong → Web BFF          JWT validated                             2ms
                              BFF initiates parallel calls:

3a    Recommendation Service  GetHomeRails(user_id, profile_id)        70ms
                              │
                              ├─ Feature Store: get user features       5ms
                              │  (viewing history, genre prefs, context)
                              │
                              ├─ AI Model Serving: score candidates     25ms
                              │  (hybrid collaborative + content-based)
                              │
                              ├─ Catalog Service: get title metadata    15ms
                              │  (batch: 50 titles across 6 rails)
                              │
                              └─ Entitlement Service: filter by access  10ms
                                 (batch: which of these 50 can the user
                                  access or purchase?)

                              Returns 6 rails:
                              - "Continue Watching" (from Bookmark)
                              - "Recommended For You" (AI model)
                              - "Trending This Week" (popularity)
                              - "New Releases" (recency)
                              - "Because You Watched [title]" (AI model)
                              - "Top Picks in Drama" (AI + genre)

3b    Bookmark Service        GetContinueWatching(user, profile)       12ms
      (parallel)              Returns: 3 titles with resume positions

3c    Profile Service         GetActiveProfile(user)                   8ms
      (parallel)              Returns: profile name, parental rating,
                              preferences

4     Web BFF                 Assembles home screen response:           5ms
                              - Personalized hero banner (AI-selected)
                              - 6 content rails with metadata
                              - Thumbnail URLs (AI-selected variant per user)
                              - Entitlement badges (included/rent/buy)

5     Web Client              Renders home screen                       ~200ms
                              Sends analytics: screen.view, rail.impression,
                              tile.impression (batched)

--- User browses and clicks a movie tile ---

6     Web Client              User clicks movie "Northern Lights"       0ms
                              GET /v1/web/content/vod_12345

7     Web BFF                 Parallel calls:
7a    Catalog Service         GetTitle("vod_12345")                    20ms
                              Returns: full metadata (synopsis, cast,
                              crew, genres, rating, duration, seasons)
7b    Recommendation Service  GetRelated("vod_12345", user)            40ms
                              Returns: "More Like This" (10 titles)
7c    Entitlement Service     CheckAccess(user, "vod_12345")           12ms
                              Returns: {allowed: true, monetization: "svod"}
7d    Bookmark Service        GetBookmark(user, "vod_12345")           8ms
                              Returns: {position: 1823000ms, updated_at: ...}

8     Web BFF                 Assembles detail response:                3ms
                              Title metadata + related content +
                              {can_play: true, resume_at: "30:23"} +
                              trailer URL + AI-selected thumbnail

9     Web Client              Renders detail page                       ~150ms
                              User sees "Resume from 30:23" button
                              Sends analytics: content_detail.view

--- User presses "Resume" ---

10    Web Client              POST /v1/web/playback/start               0ms
                              {content_id: "vod_12345", resume_at: 1823000}

11-16 [Same as Live TV flow steps 3-6]                                  ~300ms
      Entitlement → Session → CDN Routing → CAT → Manifest → DRM

      Key difference: resume_at position is passed to the player,
      which seeks to the bookmark position after loading the manifest.

17    Web Client              Playback starts at 30:23                  ~450ms total
                              Shaka Player: HLS manifest loaded,
                              Widevine license acquired, seek to
                              1823000ms, render first frame.
```

**Key integration points specific to VOD browse:**

| Integration | Contract | SLA | Fallback |
|-------------|----------|-----|----------|
| BFF → Recommendation | gRPC: `GetHomeRails(user, profile)` | p99 < 100ms | Fallback: pre-computed popularity rails (cached in Redis per genre, refreshed hourly) |
| Recommendation → Feature Store | gRPC: `GetFeatures(user_id, feature_group)` | p99 < 10ms | Default feature vector (average user profile) |
| Recommendation → Model Serving | gRPC: `Predict(features, candidates)` | p99 < 30ms | Popularity-based ranking (no personalization) |
| Recommendation → Catalog | gRPC: `BatchGetTitles(title_ids)` | p99 < 50ms (batch of 50) | Reduced rail size (return fewer titles) |
| BFF → Bookmark | gRPC: `GetContinueWatching(user, profile)` | p99 < 50ms | Skip "Continue Watching" rail (hide from response) |

---

## 9. Data Flow: AI Generates a Recommendation

**Scenario:** The Recommendation Service responds to a real-time request for personalized home screen content.

```
Step  Component               Action                                    Latency
─────────────────────────────────────────────────────────────────────────────────
1     BFF                     Calls Recommendation Service              0ms
                              GetHomeRails(user_id: "usr_x1y2z3",
                               profile_id: "prf_a1b2c3",
                               context: {device: "android_tv",
                                         time: "20:30", day: "friday"})

2     Recommendation Service  Fetches user features from Feature Store  5ms
      │
      │  Feature Store        Returns (from Redis, < 5ms):
      │  (online)             - User genre vector: [0.8 drama, 0.7 thriller, ...]
      │                       - Last 10 watched content IDs
      │                       - Avg session duration: 45 min
      │                       - Preferred content length: 40-60 min
      │                       - Viewing frequency: daily
      │                       - Active profile: adult
      │                       - Time-of-day preference: evening = long-form

3     Recommendation Service  Fetches candidate set:                    8ms
                              - Catalog Service: new + trending titles (pre-cached)
                              - Content embeddings from pgvector (semantic similarity
                                to user's recent watches, top-50 nearest neighbors)
                              Candidate pool: ~500 titles

4     Recommendation Service  Scores candidates via AI Model Serving:   25ms
      │
      │  KServe               Collaborative model: P(watch | user, title)
      │  (TF Serving)         for each of 500 candidates
      │                       Input: user features + title features + context
      │                       Output: probability score [0.0, 1.0]
      │
      │  KServe               Content-based model: cosine similarity
      │  (PyTorch)            between user embedding and title embedding
      │                       Output: similarity score [0.0, 1.0]

5     Recommendation Service  Blends scores:                            3ms
                              final_score = 0.5 * collaborative +
                                           0.3 * content_based +
                                           0.15 * trending_boost +
                                           0.05 * recency_boost

                              Applies business rules:
                              - Remove already-watched content (>90% completion)
                              - Remove content above parental rating
                              - Inject diversity (max 3 titles per genre per rail)
                              - Apply A/B experiment variant (if in experiment)

6     Recommendation Service  Organizes into rails:                     2ms
                              Rail 1: "Continue Watching" (from Bookmark)
                              Rail 2: "Recommended For You" (top 15 by score)
                              Rail 3: "Trending This Week" (trending_boost > 0.5)
                              Rail 4: "New Releases" (added in last 7 days)
                              Rail 5: "Because You Watched [last title]"
                                      (content-based similar to last watch)
                              Rail 6: "Top Drama" (top genre for this user)

7     Recommendation Service  Selects thumbnail variant per title:      5ms
                              For each title, select from 3-5 thumbnail
                              variants based on user profile (genre
                              emphasis, mood, actor visibility)

8     Recommendation Service  Returns response to BFF                   1ms
                              {rails: [...], experiment_variant: "v2",
                               model_version: "rec-v3.2.1"}

9     Recommendation Service  Publishes async events to Kafka:          async
      (async)                 `recommendations.served` with:
                              - user_id, profile_id
                              - rail_contents (item IDs + positions)
                              - model_version, experiment_variant
                              - scoring_latency_ms

                              These events feed:
                              - Analytics (recommendation effectiveness)
                              - Feature Store (update user interaction features
                                when user later clicks/watches a recommendation)
```

**Model fallback chain:**

| Level | Condition | Strategy | Quality |
|-------|-----------|----------|---------|
| 1 (Normal) | All models healthy | Full hybrid recommendation | Best |
| 2 (Partial) | One model down | Use available model only (e.g., content-based without collaborative) | Good |
| 3 (Feature Store down) | Online features unavailable | Use default feature vectors (average user) | Moderate |
| 4 (Model Serving down) | All models unavailable | Pre-computed popularity rails from Redis (top-100 per genre, refreshed hourly) | Basic |
| 5 (Redis down) | Popularity cache unavailable | Static editorial rails from BFF config | Minimal |

---

## 10. Data Flow: Content Is Ingested and Becomes Available

**Scenario:** A new movie "Midnight Signal" is ingested, enriched by AI, encoded, packaged, and made available in the catalog.

```
Step  Component               Action                                    Duration
─────────────────────────────────────────────────────────────────────────────────
1     Content Operations      Uploads mezzanine file to S3 ingest       External
                              bucket. Creates ingest request via
                              Content Ops Portal:
                              {title: "Midnight Signal", type: "movie",
                               territories: ["GB", "DE", "FR"],
                               monetization: "svod", package: "pkg_premium"}

2     Content Ingest Service  Detects new file in S3 (event notification) 1 min
                              Validates file format (ProRes/XDNHD)
                              Creates ingest record in PostgreSQL
                              Publishes `ingest.started` to Kafka

3     AI Enrichment Pipeline  Triggered by `ingest.started` event       15-45 min
      (Apache Airflow DAG)    Runs in dependency order:
      │
      3a  Whisper STT         Audio → subtitles (EN) → translations     20 min
      │                       (DE, FR). Output: SRT/VTT files → S3
      │
      3b  Thumbnail Extract   Extract candidate thumbnails every 10s    5 min
      │   + Quality Scoring   Score each with ResNet quality model
      │                       Select top 5 variants. Output: JPEGs → S3
      │
      3c  Content Fingerprint Perceptual hash for dedup detection       3 min
      │                       Check against existing fingerprint DB
      │                       No duplicate found → proceed
      │
      3d  Scene Detection     Detect scene boundaries for chapter       5 min
      │                       markers. Output: chapter list with timestamps
      │
      3e  Content Moderation  CLIP-based classification:                5 min
      │                       nudity: none, violence: mild,
      │                       language: moderate → rating suggestion: 15
      │
      3f  Audio Analysis      Loudness normalization analysis           2 min
      │                       Dialogue level detection
      │
      3g  Embedding Gen       Generate 768-dim content embedding        1 min
      │   (vLLM)              from combined metadata + visual features
      │                       Store in pgvector for similarity search
      │
      3h  AI Metadata Tags    LLM-based tagging (Bedrock):              3 min
          (Bedrock)           mood: "tense, suspenseful"
                              themes: "technology, isolation, paranoia"
                              similar_to: ["Ex Machina", "Black Mirror"]

                              Publishes `ai.enrichment.completed` to Kafka

4     Metadata Service        Consumes `ai.enrichment.completed`        5 min
                              Stores: subtitles, thumbnails, chapters,
                              moderation results, tags, embedding
                              Merges with editorial metadata (manual
                              input from Content Ops: synopsis, cast, crew)
                              Publishes `metadata.enriched` to Kafka

5     Per-Title Encoding      ML model analyzes mezzanine content:      5 min
      Analysis (SageMaker)    complexity, motion, grain, texture
                              Generates optimized encoding ladder:
                              - 1080p HEVC: 3800 kbps (vs default 4500)
                              - 720p HEVC: 1900 kbps (vs default 2500)
                              → Saves ~20% bitrate for this title

6     Encoding Pipeline       Encodes mezzanine to optimized ABR ladder 2-4 hours
                              Output: encoded segments per profile → S3
                              Publishes `encoding.completed` to Kafka

7     Packaging               Shaka Packager: CMAF packaging            30 min
                              CBCS encryption (content key from KMS)
                              HLS + DASH manifests with DRM signaling
                              Output: encrypted segments + manifests → S3
                              Publishes `packaging.completed` to Kafka

8     Catalog Service         Consumes `packaging.completed`            2 min
                              Creates catalog entry:
                              {title, metadata, availability windows,
                               thumbnail URLs, manifest template,
                               subtitle tracks, audio tracks, chapters}
                              Indexes in Elasticsearch for search
                              Publishes `catalog.title.added` to Kafka

9     Consumers of
      `catalog.title.added`:
      │
      9a  Search Service      Indexes new title in search               30s
      │                       (text fields + embedding for semantic search)
      │
      9b  Recommendation Svc  Adds to candidate pool                    60s
      │                       Computes similarity to existing titles
      │
      9c  BFF Cache           Invalidates home screen cache             5s
      │                       New title appears in "New Releases" rail
      │
      9d  Notification Service Triggers notifications for users who     async
                               may be interested (based on recommendation
                               model: "New movie matching your taste")

TOTAL TIME: Ingest trigger → available in catalog: ~3-5 hours
(dominated by encoding step; AI enrichment runs in parallel)
```

**Key integration points:**

| Integration | Contract | SLA | Fallback |
|-------------|----------|-----|----------|
| Ingest → Airflow (AI pipeline) | Kafka event: `ingest.started` | Pipeline completion < 45 min | Skip AI enrichment; catalog with editorial metadata only |
| Airflow → Whisper (STT) | SageMaker Batch Transform | < 1x real-time | Manual subtitle upload by Content Ops |
| Airflow → Bedrock (LLM tagging) | AWS SDK: InvokeModel | p99 < 30s per title | Skip AI tags; rely on editorial tags only |
| Encoding → KMS | gRPC: `GetContentKey(title_id)` | p99 < 100ms | Fail encoding (cannot encrypt without key) |
| Packaging → S3 | AWS SDK: PutObject | p99 < 100ms per segment | Retry with exponential backoff |
| Catalog → Elasticsearch | REST: index document | p99 < 200ms | Title visible via PostgreSQL queries but not searchable until ES catches up |

---

## 11. Error Handling & Fallback Patterns

### 11.1 Circuit Breaker Configuration

All synchronous service-to-service calls use circuit breakers (via Istio DestinationRule or application-level):

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Consecutive failures to open | 5 | Avoid opening on transient errors |
| Open duration | 30 seconds | Give the downstream service time to recover |
| Half-open probe count | 1 | Single request to test recovery |
| Timeout per request | Service-specific (see below) | Prevent hanging requests |

### 11.2 Timeout Configuration

| Calling Service | Called Service | Timeout | Retry | Retry Backoff |
|----------------|---------------|---------|-------|---------------|
| BFF | Entitlement | 100ms | 1 retry | 50ms |
| BFF | Playback Session | 500ms | 0 retries | N/A |
| BFF | Recommendation | 300ms | 0 retries | N/A |
| BFF | Bookmark | 100ms | 1 retry | 50ms |
| BFF | Catalog | 200ms | 1 retry | 100ms |
| BFF | EPG | 200ms | 1 retry | 100ms |
| BFF | Search | 500ms | 0 retries | N/A |
| Playback Session | CDN Routing | 100ms | 1 retry | 50ms |
| Playback Session | Token Service | 100ms | 1 retry | 50ms |
| Playback Session | Entitlement | 100ms | 1 retry | 50ms |
| Recommendation | Feature Store | 50ms | 1 retry | 25ms |
| Recommendation | Model Serving | 100ms | 0 retries | N/A |
| Recommendation | Catalog (batch) | 200ms | 1 retry | 100ms |
| Recording | EPG | 200ms | 1 retry | 100ms |
| Recording | Entitlement | 100ms | 1 retry | 50ms |

### 11.3 Graceful Degradation Matrix

| Service Down | Affected Feature | Degraded Behavior | User Impact |
|-------------|-----------------|-------------------|-------------|
| Recommendation Service | Home screen rails | Popularity-based rails (pre-cached in Redis) | Less personalized but functional home screen |
| Search Service | Content search | Disabled. "Search is temporarily unavailable" message. | Cannot search; browse still works |
| Bedrock (LLM) | Conversational search | Falls back to keyword search (Elasticsearch) | No natural language understanding |
| EPG Service | TV Guide | Stale cached EPG (up to 24h) from Redis | EPG may show outdated schedule |
| Bookmark Service | Continue watching, resume | "Continue Watching" rail hidden; playback starts from beginning | Minor inconvenience |
| Notification Service | Push notifications | Notifications queued for later delivery | Delayed notifications |
| QoE Service | Quality monitoring | No QoE alerts; CDN routing uses static metrics | Reduced observability |
| Feature Store (online) | AI personalization | Default feature vectors; all models produce less personalized output | Generic recommendations |
| Ad Service | AVOD ad insertion | Content plays without ads (revenue loss, not user-facing failure) | Better user experience, revenue impact |

---

## 12. Integration Testing Strategy

### 12.1 Testing Levels

| Level | Scope | Tools | Frequency | Environment |
|-------|-------|-------|-----------|-------------|
| **Contract tests** | API schema compliance between producer and consumer | Pact (consumer-driven contracts) | Every PR | CI (mocked dependencies) |
| **Integration tests** | Service + its real dependencies (DB, Redis, Kafka) | Testcontainers (Go/Python) | Every PR | CI (Docker containers) |
| **BFF integration tests** | BFF + all backend services (mocked) | Custom BFF test suite | Every PR | CI |
| **End-to-end flow tests** | Full user journey (login → browse → play) | Playwright (web), Appium (mobile) | Daily | Staging environment |
| **Chaos tests** | Dependency failure scenarios | Litmus Chaos, custom fault injection | Weekly | Staging environment |
| **Load tests** | Scale and performance under load | k6, Locust | Before each release | Staging (scaled to 25% prod) |

### 12.2 Contract Test Coverage

Every service-to-service integration has a contract test:

| Producer | Consumer | Contract | What's Tested |
|----------|----------|----------|--------------|
| Entitlement Service | BFF (all) | `CheckAccess` gRPC | Request/response schema, allowed/denied responses, error codes |
| Playback Session | BFF (all) | `CreateSession` gRPC | Session creation request, manifest URL format, error responses |
| Recommendation | BFF (all) | `GetHomeRails` gRPC | Rail structure, tile schema, empty rail handling |
| Catalog | BFF, Recommendation, Search | `GetTitle`, `BatchGetTitles` gRPC | Title schema, availability window format, batch response |
| EPG | BFF, Recording, Schedule | `GetSchedule`, `GetProgram` gRPC | Schedule schema, program metadata, rights flags |
| Bookmark | BFF, Playback Session | `GetBookmark`, `SetBookmark` gRPC | Bookmark schema, resume position format, missing bookmark |
| Recording | BFF | `CreateRecording`, `ListRecordings` gRPC | Recording schema, quota response, status transitions |
| Feature Store | Recommendation, CDN Routing | `GetFeatures` gRPC | Feature vector schema, missing feature handling, latency |
| Token Service | Playback Session | `IssueCAT` gRPC | Token format, claims structure, error responses |
| CDN Routing | Playback Session | `SelectCDN` gRPC | CDN selection response, fallback CDN, error handling |

### 12.3 Critical Path Chaos Scenarios

| Scenario | Services Affected | Expected Behavior | Validation |
|----------|------------------|-------------------|-----------|
| Kill Entitlement Service | All playback | Redis cache serves stale entitlements for 60s. New playback works. After 60s cache expiry, playback denied for new sessions. | Verify: playback continues for cached users; new users get graceful error after cache expiry |
| Kill Recommendation Service | Home screen | Fallback popularity rails served from Redis. "Recommended For You" rail shows "Trending" instead. | Verify: home screen loads within SLO; no errors shown to user |
| CDN A failure (Akamai) | All active streams on Akamai | CDN Routing switches new sessions to CloudFront. Existing sessions get mid-session CDN switch on next manifest refresh. | Verify: < 30s to detect and switch; rebuffer during switch < 3s |
| Kafka cluster failure | All async processing | Playback (synchronous path) unaffected. Analytics events buffered client-side. Bookmarks stop updating. Recommendations become stale. | Verify: playback works; events are buffered and flushed when Kafka recovers |
| Redis cluster failure | All services using cache | Services fall back to PostgreSQL. Latency increases across the board (~5-10x for cached paths). | Verify: all services remain functional; latency stays within degraded SLO (< 1s) |
| Feature Store (Redis) failure | AI recommendations | Models use default feature vectors. Recommendations become less personalized. | Verify: recommendation service still responds within SLO; quality degrades but no errors |
| Vault unavailable | Auth (key rotation), Token Service (CAT signing), DRM (key management) | Cached signing keys used. New content keys cannot be generated (ingest blocked). Existing content playback unaffected. | Verify: playback works with cached keys; ingest queue pauses; alert fires within 15s |

---

*This document maps the integration architecture of the AI-native OTT streaming platform. Every service-to-service dependency, third-party integration, and critical data flow is documented with contracts, SLAs, error handling, and fallback behaviors. Changes to any integration point — adding a new dependency, modifying a Kafka topic schema, or changing a third-party provider — require review against this document to assess impact across the system.*
