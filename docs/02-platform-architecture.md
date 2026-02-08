# Platform Architecture Document
## AI-Native OTT Streaming Platform

**Document ID:** ARCH-001
**Version:** 1.0
**Date:** 2026-02-08
**Status:** Draft
**Author:** Platform Architecture Agent
**Reference:** VIS-001 (Project Vision & Design Document)
**Audience:** Engineering Leadership, Principal Engineers, SRE, AI/ML Engineers

---

## Table of Contents

1. [Architecture Principles](#1-architecture-principles)
2. [High-Level Architecture](#2-high-level-architecture)
3. [Service Catalog](#3-service-catalog)
4. [Data Architecture](#4-data-architecture)
5. [Content Delivery Architecture](#5-content-delivery-architecture)
6. [AI/ML Infrastructure](#6-aiml-infrastructure)
7. [Client Architecture](#7-client-architecture)
8. [Security Architecture](#8-security-architecture)
9. [Observability Architecture](#9-observability-architecture)
10. [Deployment & Infrastructure](#10-deployment--infrastructure)
11. [Technology Stack Summary](#11-technology-stack-summary)

---

## 1. Architecture Principles

The following principles govern all architectural decisions. When principles conflict, higher-numbered principles yield to lower-numbered ones.

### P1: AI-Native

ML models are first-class citizens in the architecture, not afterthoughts bolted onto existing services. Every service design includes:
- An AI integration point (how this service feeds or consumes ML models)
- A fallback path (what happens when the AI model is unavailable or underperforming)
- A feedback loop (how user interactions with this service improve model quality)

ML inference infrastructure (KServe, feature stores, vector databases) is planned, provisioned, and monitored with the same rigor as core microservices.

### P2: Event-Driven

Apache Kafka serves as the central nervous system. All meaningful state changes are published as events. Services communicate primarily through asynchronous event streams. Synchronous API calls are reserved for request-response paths where the caller needs an immediate answer (playback session start, entitlement check).

**Rationale:** Event-driven architecture enables loose coupling between services, natural support for CQRS, real-time analytics, and ML feature extraction from live event streams.

### P3: API-First

Every capability is exposed via versioned, documented APIs before a UI is built. Internal services communicate through well-defined API contracts (gRPC for service-to-service, REST/GraphQL for client-facing). API contracts are defined in OpenAPI 3.1 (REST) or Protocol Buffers (gRPC) and live in a shared schema registry.

### P4: Observability-First

Every service emits structured metrics (Prometheus), structured logs (JSON), and distributed traces (OpenTelemetry) from day one. Observability is not added after launch — it is a prerequisite for the first deployment. Every new service template includes: health check endpoints, readiness/liveness probes, metric exporters, and trace context propagation.

### P5: Cloud-Native and Immutable

All services run on Kubernetes. Infrastructure is immutable — no SSH into production, no manual changes. All infrastructure is defined as code (Terraform for cloud resources, Helm/Kustomize for Kubernetes workloads). Deployments are automated through GitOps (ArgoCD).

### P6: Secure by Default

Zero-trust networking (Istio service mesh with mTLS). No service trusts another by default — all service-to-service communication is authenticated and authorized. Secrets are managed centrally (HashiCorp Vault). Security scanning (SAST, DAST, container scanning) runs in every CI/CD pipeline.

### P7: Progressive Enhancement with Graceful Degradation

The platform is designed in layers where each enhancement is optional. When AI models are unavailable, the platform falls back to rule-based or popularity-based defaults. When a CDN degrades, traffic shifts to an alternative. When a non-critical service fails, the user experience degrades gracefully rather than erroring completely.

### P8: Multi-Tenant Ready

The architecture supports white-label deployment from day one. Tenant configuration (branding, feature flags, content catalogs, business rules) is externalized. The same codebase serves multiple operator deployments. Data isolation is enforced at the service level.

### P9: Cost-Aware

Architectural decisions include cost projections. Every service has a cost budget. Compute is right-sized (spot instances for batch, reserved for baseline, on-demand for burst). Storage tiering is automatic (hot → warm → cold → archive). AI inference costs are tracked per-model and per-request.

### P10: Domain-Driven Boundaries

Service boundaries follow domain-driven design. Each microservice owns its data, exposes capabilities through APIs, and publishes events for state changes. Shared databases are prohibited. Data duplication across services is acceptable and managed through eventual consistency via Kafka.

---

## 2. High-Level Architecture

### System Context

```
                            ┌─────────────────────────────────┐
                            │       Client Applications       │
                            │  Android TV | Apple TV | Web    │
                            │  iOS | Android | Smart TVs     │
                            │  STBs | Chromecast | AirPlay   │
                            └──────────────┬──────────────────┘
                                           │
                                    ┌──────┴──────┐
                                    │  CDN Layer  │
                                    │ Multi-CDN   │
                                    │ + CAT Tokens│
                                    └──────┬──────┘
                                           │
                          ┌────────────────┼────────────────┐
                          │                │                │
                   ┌──────┴──────┐  ┌──────┴──────┐  ┌─────┴──────┐
                   │ API Gateway │  │ Manifest    │  │ Media      │
                   │ (Kong)      │  │ Proxy       │  │ Origin     │
                   └──────┬──────┘  └──────┬──────┘  └─────┬──────┘
                          │                │                │
                   ┌──────┴──────┐  ┌──────┴──────┐  ┌─────┴──────┐
                   │  BFF Layer  │  │ Packaging   │  │ Storage    │
                   │ (per-client)│  │ (USP/CMAF)  │  │ (S3/EFS)   │
                   └──────┬──────┘  └─────────────┘  └────────────┘
                          │
           ┌──────────────┼──────────────────────────┐
           │              │                          │
    ┌──────┴──────┐┌──────┴──────┐           ┌──────┴──────┐
    │  Backend    ││  AI/ML      │           │  Data       │
    │  Micro-     ││  Services   │           │  Platform   │
    │  services   ││  Layer      │           │             │
    └──────┬──────┘└──────┬──────┘           └──────┬──────┘
           │              │                          │
           └──────────────┼──────────────────────────┘
                          │
                   ┌──────┴──────┐
                   │   Kafka     │
                   │  Event Bus  │
                   └─────────────┘
```

### Subsystem Descriptions

**1. Content Ingest & Enrichment Pipeline**

Content enters the platform through two paths: (a) live feeds via satellite/fiber/IP ingest (SDI/SMPTE ST 2110) for linear channels, and (b) file-based ingest (mezzanine files via S3/SFTP) for VOD. Both paths feed into the Content Enrichment Pipeline, which runs AI processing: automated subtitle generation (Whisper), thumbnail extraction with quality scoring, content fingerprinting (deduplication), scene detection (chapter markers), content moderation (nudity/violence/language classification), and audio normalization analysis. Output: enriched metadata written to the Metadata Service, processing status events published to Kafka.

**2. Encoding / Transcoding Farm**

VOD content is encoded via a distributed transcoding farm running on Kubernetes (FFmpeg + hardware acceleration on GPU instances). The encoding pipeline supports per-title optimization: an ML model analyzes content complexity (motion, grain, texture) and generates a custom encoding ladder that achieves the target VMAF score at minimum bitrate. Live content is transcoded in real-time using dedicated encoder appliances (Elemental/Harmonic) with redundant failover. Output: encoded ABR assets stored in origin storage (S3), encoding completion events published to Kafka.

**3. Packaging & Origin**

Encoded content is packaged into CMAF segments with HLS and DASH manifests. For VOD, packaging is done ahead-of-time (offline). For live, packaging is done in real-time using Unified Streaming Platform (USP) or AWS MediaPackage. The origin server generates just-in-time (JIT) manifests per DRM system (Widevine, FairPlay, PlayReady) using CPIX key exchange. CBCS encryption mode is used across all DRM systems. Origin storage uses S3 with EFS for live segment write/read performance.

**4. CDN Layer**

Content is delivered via a multi-CDN topology: Origin → Shield (regional cache) → Edge (PoP). The platform integrates with 2-3 CDN providers (e.g., Akamai, CloudFront, Fastly). A CDN Routing Service selects the optimal CDN per session based on real-time performance data, user location, ISP, and historical performance. Access is secured via Common Access Token (CAT) — short-lived, cryptographically signed tokens that authorize CDN access per session. Token validation happens at the CDN edge.

**5. Backend Microservices**

20+ microservices running on Kubernetes, primarily written in Go (high-throughput services: playback, CDN routing, auth) and Python (AI-adjacent services: recommendations, search, content enrichment). Services communicate via gRPC (synchronous) and Kafka (asynchronous). Each service owns its data store (PostgreSQL, Redis, Elasticsearch as appropriate). Services are deployed independently with their own CI/CD pipelines.

**6. AI/ML Services Layer**

A dedicated ML serving infrastructure runs alongside the backend microservices. Real-time inference is served via KServe on Kubernetes (GPU nodes). Batch inference (content enrichment, model retraining) runs on dedicated GPU instances or SageMaker. The Feature Store (Feast) serves pre-computed features for online inference with < 10ms latency. LLM inference for conversational search and content summarization uses Amazon Bedrock (managed) or self-hosted vLLM (for cost-sensitive workloads). Vector search for semantic content similarity uses pgvector.

**7. BFF Layer (Backend-for-Frontend)**

Three BFF services serve tailored responses per client family:
- **TV BFF** (Go): Android TV, Apple TV, Smart TVs, STBs — optimized for 10-foot UI, remote control navigation, pre-composed screen layouts
- **Mobile BFF** (Go): iOS, Android — optimized for touch interaction, cellular bandwidth, offline sync
- **Web BFF** (Go): Browsers — optimized for responsive layouts, SEO, progressive web app

Each BFF aggregates data from multiple backend services, applies client-specific transformations, and returns pre-composed responses that minimize client-side logic.

**8. Client Applications**

Native applications per platform (see Client Architecture section). All clients share: API contract definitions, design system tokens, telemetry schema, and feature flag integration. Player integration is per-platform: ExoPlayer/Media3 (Android), AVPlayer (Apple), Shaka Player (Web/Smart TVs).

**9. Observability Stack**

Prometheus + Grafana for infrastructure metrics. OpenTelemetry for distributed tracing. Structured JSON logs aggregated via Fluentd to Elasticsearch/Loki. QoE metrics collected via Conviva SDK (client-side) and correlated with server-side telemetry. AI-powered alert correlation reduces alert noise. PagerDuty for on-call alerting.

**10. Data Platform**

Events flow from clients and services → Kafka → data lake (S3 + Apache Iceberg). The data platform serves three purposes: (a) real-time analytics dashboards (Kafka Streams/Flink → Druid/ClickHouse), (b) batch analytics and reporting (Spark on Iceberg → BI tools), (c) ML training data (feature extraction from event streams → Feature Store → training pipelines).

---

## 3. Service Catalog

### Core User Services

| Service | Language | Primary DB | Cache | Events Produced | Events Consumed | Key Dependencies | SLO |
|---------|----------|-----------|-------|-----------------|-----------------|-----------------|-----|
| **User Service** | Go | PostgreSQL 16 | Redis | `user.created`, `user.updated`, `user.deleted` | — | — | p99 < 50ms, 99.99% |
| **Auth Service** | Go | PostgreSQL 16 | Redis (sessions) | `auth.login`, `auth.logout`, `auth.token.refreshed` | `user.created` | User Service | p99 < 100ms, 99.99% |
| **Entitlement Service** | Go | PostgreSQL 16 | Redis (entitlement cache) | `entitlement.granted`, `entitlement.revoked`, `entitlement.checked` | `user.created`, `subscription.changed` | User Service, Subscription Service | p99 < 30ms, 99.99% |
| **Profile Service** | Go | PostgreSQL 16 | Redis | `profile.created`, `profile.updated`, `profile.switched` | `user.created` | User Service | p99 < 50ms, 99.95% |

### Content & Metadata Services

| Service | Language | Primary DB | Cache | Events Produced | Events Consumed | Key Dependencies | SLO |
|---------|----------|-----------|-------|-----------------|-----------------|-----------------|-----|
| **Catalog Service** | Go | PostgreSQL 16 | Redis + Elasticsearch 8 | `catalog.title.added`, `catalog.title.updated`, `catalog.availability.changed` | `ingest.completed`, `metadata.enriched` | Metadata Service | p99 < 100ms, 99.95% |
| **Metadata Service** | Python | PostgreSQL 16 + pgvector | Redis | `metadata.enriched`, `metadata.tags.updated` | `ingest.completed`, `ai.enrichment.completed` | — | p99 < 150ms, 99.95% |
| **EPG Service** | Go | PostgreSQL 16 | Redis (schedule cache) | `epg.schedule.updated`, `epg.program.changed` | `epg.ingest.completed` | — | p99 < 100ms, 99.95% |
| **Content Ingest Service** | Python | PostgreSQL 16 | — | `ingest.started`, `ingest.completed`, `ingest.failed` | — | S3 (storage), Encoding Pipeline | p99 < 500ms, 99.9% |
| **Encoding Pipeline Service** | Go | PostgreSQL 16 | — | `encoding.started`, `encoding.completed`, `encoding.failed` | `ingest.completed` | GPU compute, S3 | Completion < 4hrs (VOD), 99.9% |

### Playback & Recording Services

| Service | Language | Primary DB | Cache | Events Produced | Events Consumed | Key Dependencies | SLO |
|---------|----------|-----------|-------|-----------------|-----------------|-----------------|-----|
| **Playback Session Service** | Go | PostgreSQL 16 | Redis (active sessions) | `playback.started`, `playback.stopped`, `playback.heartbeat`, `playback.error` | `entitlement.checked` | Entitlement, Token, CDN Routing | p99 < 200ms, 99.99% |
| **Bookmark Service** | Go | PostgreSQL 16 | Redis | `bookmark.updated`, `bookmark.resumed` | `playback.heartbeat`, `playback.stopped` | Profile Service | p99 < 50ms, 99.95% |
| **Recording Service** | Go | PostgreSQL 16 | Redis (schedule cache) | `recording.scheduled`, `recording.started`, `recording.completed`, `recording.deleted` | `epg.schedule.updated`, `playback.stopped` | EPG Service, Entitlement, Encoding Pipeline | p99 < 200ms, 99.95% |
| **Schedule Service** | Go | PostgreSQL 16 | Redis | `schedule.reminder.set`, `schedule.reminder.triggered` | `epg.schedule.updated`, `recording.scheduled` | EPG Service, Notification Service | p99 < 100ms, 99.95% |

### AI & Discovery Services

| Service | Language | Primary DB | Cache | Events Produced | Events Consumed | Key Dependencies | SLO |
|---------|----------|-----------|-------|-----------------|-----------------|-----------------|-----|
| **Recommendation Service** | Python | PostgreSQL 16 + pgvector | Redis (precomputed recs) | `recommendation.served`, `recommendation.clicked` | `playback.started`, `playback.stopped`, `bookmark.updated`, `catalog.title.added` | Feature Store, Model Serving | p99 < 100ms, 99.9% |
| **Search Service** | Python | Elasticsearch 8 + pgvector | Redis | `search.query`, `search.result.clicked` | `catalog.title.added`, `metadata.enriched` | Metadata Service | p99 < 200ms, 99.9% |
| **AI Model Serving** | Python | — | — | `model.prediction.served` | varies by model | Feature Store, GPU compute | p99 < 50ms, 99.9% |
| **Feature Store** | Python | Redis (online) + S3/Iceberg (offline) | — | `features.updated` | All playback/browse events | — | p99 < 10ms (online), 99.95% |

### Delivery & Infrastructure Services

| Service | Language | Primary DB | Cache | Events Produced | Events Consumed | Key Dependencies | SLO |
|---------|----------|-----------|-------|-----------------|-----------------|-----------------|-----|
| **CDN Routing Service** | Go | — | Redis (CDN metrics) | `cdn.route.selected`, `cdn.switch.triggered` | `playback.heartbeat`, `qoe.metric` | QoE Service | p99 < 30ms, 99.99% |
| **Token Service (CAT)** | Go | — | Redis (token cache) | `token.issued` | `playback.started` | Auth Service | p99 < 20ms, 99.99% |
| **Notification Service** | Go | PostgreSQL 16 | Redis (rate limiting) | `notification.sent`, `notification.clicked` | `schedule.reminder.triggered`, `recommendation.served` | User Service, Profile Service | p99 < 200ms, 99.9% |
| **Ad Service (SSAI)** | Go | PostgreSQL 16 | Redis | `ad.decision.made`, `ad.impression`, `ad.completed` | `playback.started`, `entitlement.checked` | Playback Session, Entitlement | p99 < 100ms, 99.9% |
| **QoE Service** | Go | ClickHouse | Redis | `qoe.score.calculated`, `qoe.alert.triggered` | `playback.heartbeat`, `playback.error` | — | p99 < 100ms, 99.95% |
| **Analytics Collector** | Go | Kafka → S3/Iceberg | — | — | All events (sink) | Kafka, S3 | p99 < 50ms, 99.9% |

### Capacity Planning (Phase 1: 50K Concurrent)

| Service | Expected RPS | Instances (min) | CPU (per instance) | Memory (per instance) |
|---------|-------------|-----------------|--------------------|-----------------------|
| Playback Session | 5,000 | 6 | 2 vCPU | 4 GB |
| Entitlement | 8,000 | 4 | 2 vCPU | 2 GB |
| Token (CAT) | 5,000 | 4 | 1 vCPU | 1 GB |
| Recommendation | 3,000 | 8 | 4 vCPU | 8 GB |
| CDN Routing | 5,000 | 4 | 2 vCPU | 2 GB |
| EPG | 2,000 | 4 | 2 vCPU | 4 GB |
| Catalog | 2,000 | 4 | 2 vCPU | 4 GB |
| Search | 1,000 | 4 | 4 vCPU | 8 GB |
| Bookmark | 10,000 | 6 | 2 vCPU | 2 GB |
| BFF (TV) | 4,000 | 6 | 2 vCPU | 4 GB |
| BFF (Mobile) | 3,000 | 4 | 2 vCPU | 4 GB |
| BFF (Web) | 2,000 | 4 | 2 vCPU | 4 GB |

**Scaling strategy:** Horizontal pod autoscaling (HPA) based on CPU utilization (target 60%) and custom metrics (request latency p99). Vertical pod autoscaling (VPA) for recommendation and search services where memory usage is less predictable.

---

## 4. Data Architecture

### Event-Driven Architecture (Kafka)

**Kafka Cluster Configuration:**
- **Real-time cluster:** 6 brokers, SSD storage, 3-day retention, dedicated for playback events, session events, and real-time signals
- **Analytics cluster:** 4 brokers, HDD storage, 30-day retention, receives all events for downstream processing
- **Serialization:** Apache Avro with Confluent Schema Registry for schema evolution
- **Partitioning strategy:** User ID-based partitioning for user-centric topics (ensures ordering per user), content ID-based for content-centric topics

**Kafka Topic Catalog:**

| Topic | Partition Count | Retention | Throughput (Phase 1) | Schema | Owner |
|-------|----------------|-----------|---------------------|--------|-------|
| `playback.sessions` | 32 | 3 days | ~5,000 msg/s | Avro | Playback Session Service |
| `playback.heartbeats` | 64 | 1 day | ~50,000 msg/s | Avro | Playback Session Service |
| `user.events` | 16 | 7 days | ~500 msg/s | Avro | User Service |
| `catalog.changes` | 8 | 30 days | ~50 msg/s | Avro | Catalog Service |
| `epg.updates` | 8 | 7 days | ~200 msg/s | Avro | EPG Service |
| `recommendations.served` | 16 | 3 days | ~3,000 msg/s | Avro | Recommendation Service |
| `search.queries` | 8 | 3 days | ~1,000 msg/s | Avro | Search Service |
| `recordings.events` | 16 | 30 days | ~200 msg/s | Avro | Recording Service |
| `bookmarks.updates` | 32 | 7 days | ~10,000 msg/s | Avro | Bookmark Service |
| `notifications.events` | 8 | 7 days | ~500 msg/s | Avro | Notification Service |
| `qoe.metrics` | 32 | 3 days | ~20,000 msg/s | Avro | QoE Service |
| `cdn.routing.events` | 16 | 3 days | ~5,000 msg/s | Avro | CDN Routing Service |
| `ad.events` | 16 | 30 days | ~2,000 msg/s | Avro | Ad Service |
| `ai.features.updates` | 16 | 7 days | ~5,000 msg/s | Avro | Feature Store |
| `content.ingest.events` | 4 | 30 days | ~10 msg/s | Avro | Content Ingest Service |

### Database Architecture

Each service owns its database. Cross-service data access is via APIs or Kafka events — never by direct database access.

| Database | Technology | Services | Storage Estimate (Phase 1) | Backup Strategy |
|----------|-----------|----------|---------------------------|-----------------|
| User/Auth DB | PostgreSQL 16 (RDS) | User, Auth, Profile | 50 GB | Automated daily + continuous WAL archiving |
| Entitlement DB | PostgreSQL 16 (RDS) | Entitlement, Subscription | 20 GB | Automated daily + WAL |
| Catalog DB | PostgreSQL 16 (RDS) | Catalog, Metadata | 100 GB | Automated daily + WAL |
| EPG DB | PostgreSQL 16 (RDS) | EPG, Schedule | 200 GB (14-day schedule data) | Automated daily |
| Playback DB | PostgreSQL 16 (RDS) | Playback Session | 30 GB (active sessions only) | Automated daily |
| Bookmark DB | PostgreSQL 16 (RDS) | Bookmark | 50 GB | Automated daily + WAL |
| Recording DB | PostgreSQL 16 (RDS) | Recording | 100 GB | Automated daily + WAL |
| Vector DB | PostgreSQL 16 + pgvector | Metadata, Recommendation, Search | 50 GB (embeddings) | Automated daily |
| Cache Layer | Redis 7 Cluster | All services (distributed cache) | 64 GB total across cluster | Redis AOF + RDB snapshots |
| Search Index | Elasticsearch 8 | Catalog, Search, EPG | 200 GB | Snapshot to S3 daily |
| QoE/Analytics DB | ClickHouse | QoE, Analytics | 500 GB (hot), 5 TB (cold) | S3 tiered storage |
| Feature Store (Online) | Redis 7 | Feature Store | 32 GB | Rebuilt from offline store |
| Feature Store (Offline) | S3 + Apache Iceberg | Feature Store, ML Training | 2 TB | S3 versioning |

### Data Lake Architecture

```
Client Events → Kafka → Flink (stream processing) → S3 (Iceberg tables)
                                                          │
                                                ┌─────────┼──────────┐
                                                │         │          │
                                          Real-time    Batch      ML Training
                                          Analytics    Reports    Pipelines
                                          (ClickHouse) (Spark)   (SageMaker)
```

**Data Lake Layers:**
- **Bronze (Raw):** Raw events as-received, Avro format, partitioned by date and event type. Retention: 90 days.
- **Silver (Cleaned):** Deduplicated, validated, and enriched events. Parquet format on Iceberg tables. Retention: 1 year.
- **Gold (Aggregated):** Pre-computed aggregations (daily active users, content engagement scores, session summaries). Parquet on Iceberg. Retention: indefinite.
- **ML Features:** Extracted and pre-computed features for model training. Parquet on Iceberg, managed by Feature Store pipeline.

**CQRS Patterns:**

CQRS is applied where read and write patterns diverge significantly:

- **Catalog Service:** Writes go to PostgreSQL (source of truth). Reads for browse/search go to Elasticsearch (materialized view updated via Kafka consumer). Recommendation reads go to Redis (precomputed recommendation sets).
- **EPG Service:** Writes from EPG ingest go to PostgreSQL. Reads for grid display go to Redis (pre-composed schedule grids per channel per day).
- **Bookmark Service:** Writes from playback heartbeats go to PostgreSQL. Reads for "Continue Watching" go to Redis (pre-sorted per-profile list maintained by background worker).

### Data Retention Policies

| Data Category | Hot Storage | Warm Storage | Cold/Archive | Total Retention |
|---------------|-------------|-------------|-------------|-----------------|
| Playback events | 3 days (Kafka) | 90 days (Iceberg) | 2 years (S3 Glacier) | 2 years |
| User profiles | Indefinite (PostgreSQL) | — | — | Account lifetime + 30 days |
| Content metadata | Indefinite (PostgreSQL + ES) | — | — | Catalog lifetime |
| EPG schedule | 14 days (PostgreSQL + Redis) | 1 year (Iceberg) | — | 1 year |
| Recordings metadata | Indefinite (PostgreSQL) | — | — | User account lifetime |
| QoE metrics | 30 days (ClickHouse) | 1 year (Iceberg) | — | 1 year |
| ML training data | — | 1 year (Iceberg) | Indefinite (S3 Glacier) | Indefinite |
| Audit logs | 90 days (Elasticsearch) | 1 year (S3) | 7 years (Glacier) | 7 years |

---

## 5. Content Delivery Architecture

### CMAF Packaging Strategy

All content is packaged using CMAF (Common Media Application Format) to produce a single set of media segments that serve both HLS and DASH clients. This eliminates the need for duplicate segment storage and simplifies origin management.

**VOD Packaging:**
- Pre-packaged: CMAF segments (fMP4) stored on S3
- Manifests: Generated at request time by the manifest proxy
- HLS: Playlist generated from CMAF segments (.m3u8 → .m4s)
- DASH: MPD generated from CMAF segments (.mpd → .m4s)
- Segment duration: 6 seconds (VOD standard), aligned to GOP boundaries

**Live Packaging:**
- Real-time packaging via Unified Streaming Platform (USP) or AWS MediaPackage v2
- Input: CMAF segments from encoder (2-second segments for standard, 0.5-second partial segments for LL-HLS)
- Output: HLS + DASH manifests with DRM signaling
- Segment duration: 2 seconds (standard live), 0.5 seconds partial segments (LL-HLS)
- Manifest update interval: Every segment (standard), every partial segment (LL-HLS)

**Segment Naming Convention:**
```
/{content-type}/{content-id}/{profile}/{segment-number}.m4s
Example: /live/ch-001/1080p-h264-5000k/seg-0014521.m4s
```

### DRM Integration (Multi-DRM via CPIX)

**Encryption:** CBCS (Common Encryption — CBC mode with subsample patterns) across all DRM systems. Single encryption, multi-DRM signaling.

**CPIX Workflow:**
1. Content Ingest Service requests content keys from Key Management Service
2. Key Management Service generates a content key and registers it with all DRM backends:
   - Google Widevine (via Widevine Cloud API)
   - Apple FairPlay (via FairPlay Streaming Key Server)
   - Microsoft PlayReady (via PlayReady License Server)
3. CPIX document is generated containing key IDs and DRM system-specific data (PSSH boxes)
4. Encoding pipeline encrypts content using the content key (CBCS mode)
5. Packaging embeds PSSH data and key IDs in manifests
6. Client requests a license from the appropriate DRM license server using the key ID

**DRM Per-Platform:**

| Platform | DRM | Security Level | HDCP Required | Offline License |
|----------|-----|---------------|---------------|-----------------|
| Android TV | Widevine L1 | Hardware TEE | HDCP 2.2 (4K) | Yes (if OEM supports) |
| Apple TV | FairPlay | Hardware | HDCP 2.2 (4K) | No |
| Web (Chrome) | Widevine L1/L3 | Hardware (L1) / Software (L3) | HDCP 2.2 (4K, L1 only) | No |
| Web (Safari) | FairPlay | Software | HDCP via Safari | No |
| iOS | FairPlay | Hardware | N/A (mobile) | Yes |
| Android Mobile | Widevine L1/L3 | Hardware (L1) / Software (L3) | N/A (mobile) | Yes (L1) |
| Samsung Tizen | Widevine L1 | Hardware TEE | HDCP 2.2 | No |
| LG webOS | Widevine L1 | Hardware TEE | HDCP 2.2 | No |

### CDN Topology

```
                    ┌──────────────────────┐
                    │   Origin (S3 + USP)  │
                    │   - VOD segments     │
                    │   - Live segments    │
                    │   - Manifests        │
                    └──────────┬───────────┘
                               │
                    ┌──────────┴───────────┐
                    │   Origin Shield      │
                    │   (Regional Cache)   │
                    │   EU, US, APAC       │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
     ┌────────┴───────┐┌──────┴──────┐┌────────┴───────┐
     │   CDN A Edge   ││  CDN B Edge  ││  CDN C Edge   │
     │   (Akamai)     ││ (CloudFront) ││  (Fastly)     │
     │   Global PoPs  ││  Global PoPs ││  Regional     │
     └────────┬───────┘└──────┬──────┘└────────┬───────┘
              │                │                │
              └────────────────┼────────────────┘
                               │
                         Client (Player)
```

**CDN Selection Logic:**
1. Client requests playback → Playback Session Service creates session
2. CDN Routing Service evaluates: user geo, ISP, current CDN performance (latency, throughput, error rate), CDN cost tier, content type (live vs VOD)
3. CDN Routing Service selects optimal CDN and returns CDN-specific manifest URL
4. During playback, QoE monitoring tracks quality. If QoE degrades below threshold, mid-session CDN switch is triggered (new manifest URL via manifest proxy)

**CDN SLOs:**
- Cache hit ratio (edge): > 90% (VOD), > 95% (live — due to predictable access patterns)
- First byte latency (edge to client): < 50ms (p95)
- Throughput: Sufficient to sustain max ABR tier per user

### Common Access Token (CAT) Flow

CAT provides CDN-agnostic token-based authorization for media segment access.

1. Client starts playback, requests session token from Token Service
2. Token Service generates a CAT token:
   - Signed with ECDSA (ES256)
   - Claims: session ID, user ID, content ID, CDN hostname, expiry (5 minutes), allowed paths (regex)
   - Short-lived: 5-minute rolling window, refreshed transparently by client
3. Client appends CAT token to media segment requests (URL query parameter)
4. CDN edge validates token: signature, expiry, path match, hostname match
5. CDN serves segment if token is valid; returns 403 if invalid

**Token Refresh:** The player refreshes the CAT token every 4 minutes (1 minute before expiry). Refresh is a lightweight call to the Token Service (< 20ms).

### ABR Ladder Definitions

**VOD — HEVC (Primary):**

| Profile | Resolution | Bitrate | VMAF Target | Use Case |
|---------|-----------|---------|-------------|----------|
| 1080p-hevc-high | 1920x1080 | 6,000 kbps | 95+ | Premium |
| 1080p-hevc | 1920x1080 | 4,500 kbps | 93 | Standard HD |
| 720p-hevc | 1280x720 | 2,500 kbps | 90 | Good quality |
| 540p-hevc | 960x540 | 1,200 kbps | 85 | Mobile HD |
| 360p-hevc | 640x360 | 600 kbps | 78 | Low bandwidth |
| 240p-hevc | 426x240 | 300 kbps | 70 | Minimum viable |

**VOD — H.264 (Fallback):**

| Profile | Resolution | Bitrate | VMAF Target | Use Case |
|---------|-----------|---------|-------------|----------|
| 1080p-h264 | 1920x1080 | 8,000 kbps | 93 | Legacy HD |
| 720p-h264 | 1280x720 | 4,000 kbps | 90 | Legacy standard |
| 480p-h264 | 854x480 | 1,500 kbps | 82 | Legacy mobile |
| 360p-h264 | 640x360 | 800 kbps | 75 | Low bandwidth |
| 240p-h264 | 426x240 | 400 kbps | 68 | Minimum viable |

**Live — Standard Latency:**

| Profile | Resolution | Bitrate | Segment Duration | GOP |
|---------|-----------|---------|-----------------|-----|
| 1080p | 1920x1080 | 6,000 kbps | 2s | 2s |
| 720p | 1280x720 | 3,000 kbps | 2s | 2s |
| 480p | 854x480 | 1,500 kbps | 2s | 2s |
| 360p | 640x360 | 800 kbps | 2s | 2s |

**Live — LL-HLS (Sports/Events):**

| Profile | Resolution | Bitrate | Partial Segment | Part Target |
|---------|-----------|---------|-----------------|-------------|
| 1080p | 1920x1080 | 6,000 kbps | 0.5s | 0.5s |
| 720p | 1280x720 | 3,000 kbps | 0.5s | 0.5s |
| 480p | 854x480 | 1,500 kbps | 0.5s | 0.5s |

**AV1 (Premium — Phase 3):**

| Profile | Resolution | Bitrate | VMAF Target |
|---------|-----------|---------|-------------|
| 4K-av1 | 3840x2160 | 8,000 kbps | 95+ |
| 1080p-av1 | 1920x1080 | 3,000 kbps | 95 |
| 720p-av1 | 1280x720 | 1,500 kbps | 92 |

### Low-Latency Live Architecture (LL-HLS)

```
Live Feed → Encoder → 0.5s partial segments → USP → CDN → Client

Timeline:
  Encoder output:        0.0s
  USP packaging:        +0.1s
  CDN edge propagation: +0.3s
  Client buffer:        +1.0s (2 partial segments)
  Total glass-to-glass: ~1.5-3.0s
```

**LL-HLS Implementation Details:**
- Encoder produces 0.5-second partial segments (CMAF chunks) with independent decode points
- USP pushes partial segments to CDN via HTTP chunked transfer encoding
- Manifest includes `EXT-X-PART` tags for partial segments and `EXT-X-PRELOAD-HINT` for prefetch
- Client uses blocking playlist reload (`_HLS_msn` and `_HLS_part` query parameters)
- CDN holds the playlist reload request open until new partial segment is available (long polling)
- Client maintains a 1-2 second buffer (2-4 partial segments) for resilience

---

## 6. AI/ML Infrastructure

### Model Serving Architecture

```
                    ┌─────────────────────────────────────────┐
                    │           AI/ML Serving Layer            │
                    │                                          │
                    │  ┌──────────────────────────────────┐   │
                    │  │  KServe (Kubernetes-native)      │   │
                    │  │  - Real-time inference            │   │
                    │  │  - Autoscaling (GPU + CPU)        │   │
                    │  │  - Canary deployments             │   │
                    │  │  - Model versioning               │   │
                    │  │                                    │   │
                    │  │  Models:                           │   │
                    │  │  - Recommendation (TF Serving)     │   │
                    │  │  - CDN Routing (XGBoost)           │   │
                    │  │  - Anomaly Detection (PyTorch)     │   │
                    │  │  - Churn Prediction (XGBoost)      │   │
                    │  │  - Content Moderation (CLIP)       │   │
                    │  │  - Thumbnail Quality (ResNet)      │   │
                    │  └──────────────────────────────────┘   │
                    │                                          │
                    │  ┌──────────────────────────────────┐   │
                    │  │  Amazon Bedrock (Managed)         │   │
                    │  │  - Conversational search (LLM)    │   │
                    │  │  - Content summarization (LLM)    │   │
                    │  │  - Program descriptions (LLM)     │   │
                    │  └──────────────────────────────────┘   │
                    │                                          │
                    │  ┌──────────────────────────────────┐   │
                    │  │  Self-Hosted vLLM                  │   │
                    │  │  - Embedding generation            │   │
                    │  │  - Semantic search embeddings      │   │
                    │  │  - Batch content analysis          │   │
                    │  └──────────────────────────────────┘   │
                    │                                          │
                    │  ┌──────────────────────────────────┐   │
                    │  │  SageMaker (Batch)                 │   │
                    │  │  - Model training pipelines        │   │
                    │  │  - Batch inference (enrichment)    │   │
                    │  │  - Hyperparameter tuning           │   │
                    │  └──────────────────────────────────┘   │
                    └─────────────────────────────────────────┘
```

**Model Inventory:**

| Model | Framework | Serving | Latency (p99) | GPU | Refresh Cycle |
|-------|-----------|---------|--------------|-----|---------------|
| Recommendation (collaborative) | TensorFlow 2.16 | KServe | < 30ms | T4 (inference) | 6 hours |
| Recommendation (content-based) | PyTorch 2.3 | KServe | < 20ms | T4 | Daily |
| CDN Routing | XGBoost 2.0 | KServe (CPU) | < 10ms | None | Hourly |
| Anomaly Detection | PyTorch 2.3 | KServe | < 50ms | T4 | Weekly |
| Churn Prediction | XGBoost 2.0 | KServe (CPU) | < 15ms | None | Daily |
| Content Moderation | CLIP (OpenAI) | KServe | < 200ms | A10G | Static (fine-tuned) |
| Thumbnail Quality Scoring | ResNet-50 | KServe | < 100ms | T4 | Monthly |
| Embedding Generation | sentence-transformers | vLLM | < 50ms | A10G | Static |
| Per-Title Encoding | Custom CNN | SageMaker Batch | < 5s per title | A10G | Monthly |
| Subtitle Generation (Whisper) | Whisper Large v3 | SageMaker Batch | ~0.5x real-time | A10G | Static |

### Feature Store Design

**Technology:** Feast (Feature Store) with Redis (online) and S3/Iceberg (offline).

**Online Feature Store (Redis):**
- Serves pre-computed features for real-time inference (< 10ms latency)
- Features organized by entity: user features, content features, context features
- Updated continuously from Kafka event streams via Flink processing jobs
- Storage: 32 GB Redis cluster (3 primary + 3 replica)

**Offline Feature Store (S3/Iceberg):**
- Historical feature values for model training and batch inference
- Computed from data lake (Spark jobs on Iceberg tables)
- Point-in-time correct feature retrieval for training data generation
- Storage: 2 TB, growing ~100 GB/month

**Feature Groups:**

| Feature Group | Entity | Feature Count | Update Frequency | Online Latency |
|---------------|--------|--------------|------------------|----------------|
| User viewing history | user_id | 25 | Every playback event | < 5ms |
| User genre preferences | user_id | 15 | Hourly aggregation | < 5ms |
| User device/context | user_id | 10 | Every session | < 5ms |
| Content metadata | content_id | 30 | On catalog change | < 5ms |
| Content embeddings | content_id | 1 (768-dim vector) | On enrichment | < 10ms |
| Content popularity | content_id | 8 | Hourly | < 5ms |
| Channel performance | channel_id | 12 | Every minute | < 5ms |
| CDN performance | cdn_id × region | 10 | Every 30 seconds | < 5ms |
| Session context | session_id | 8 | Every heartbeat | < 5ms |

### ML Pipeline (Training to Production)

```
1. Data Collection     2. Feature           3. Training          4. Evaluation
   (Kafka → S3)         Engineering          (SageMaker)         (Offline metrics)
                         (Flink → Feast)
         │                    │                    │                    │
         ▼                    ▼                    ▼                    ▼
5. Model Registry     6. Staged Rollout    7. Online A/B        8. Monitoring
   (MLflow)              (Canary via           (5% → 50% →         (Drift detection,
                          KServe)              100%)                 performance)
```

**Training Pipeline:**
- Orchestration: Apache Airflow DAGs trigger training jobs
- Compute: SageMaker Training Jobs (GPU instances: ml.g5.xlarge for standard, ml.g5.12xlarge for large models)
- Data: Feature Store (offline) provides point-in-time correct training datasets
- Tracking: MLflow for experiment tracking, parameter logging, model versioning
- Frequency: Per-model schedule (see Model Inventory above)

**Evaluation:**
- Offline metrics computed on held-out test set: AUC, NDCG, precision@k, recall@k (for recommendations), F1, accuracy (for classification)
- Minimum quality gates: Model must exceed previous production model on all primary metrics
- Bias checks: Evaluated across user segments (age, region, subscription tier)

**Deployment:**
- Model artifact stored in S3, registered in MLflow Model Registry
- KServe InferenceService updated with new model version (canary strategy)
- Canary rollout: 5% traffic for 1 hour → automatic promotion if SLO met, rollback if not
- Full rollout: 50% for 4 hours → 100% if stable

**Monitoring:**
- Data drift: Monitor input feature distributions (KL divergence) against training data
- Model drift: Monitor prediction distribution shifts
- Performance: Track real-time inference latency, throughput, error rate
- Business metrics: A/B test against control (click-through rate, watch time, session duration)
- Alert: Automated alert if drift exceeds threshold → trigger retraining pipeline

### LLM Integration

**Amazon Bedrock (Managed LLM):**
- Used for: Conversational search, content summarization, program description generation
- Model: Claude 3.5 Sonnet (or latest available) for quality, Claude 3.5 Haiku for latency-sensitive
- Integration: Via AWS SDK, synchronous for search, asynchronous for content enrichment
- Cost management: Request caching for common queries, rate limiting per user
- Prompt engineering: Versioned prompts stored in configuration service, A/B testable

**Self-Hosted Embeddings (vLLM):**
- Used for: Content embedding generation (for vector search), user interest embedding
- Model: sentence-transformers/all-MiniLM-L6-v2 (384-dim) or instructor-xl (768-dim)
- Deployed on: KServe with GPU autoscaling (A10G instances)
- Batch: New content embeddings generated on ingest. User embeddings updated hourly.

**Vector Database (pgvector):**
- Extension on PostgreSQL 16 for vector similarity search
- Stores: Content embeddings (768-dim), user interest embeddings
- Index: HNSW index for approximate nearest neighbor (< 20ms for top-50 retrieval)
- Used by: Recommendation Service (content-based), Search Service (semantic search)

### A/B Testing Framework for ML

- **Platform:** Custom A/B framework built on feature flags (Unleash)
- **Traffic allocation:** Minimum 5% per experiment variant, maximum 50% for new model rollout
- **Assignment:** Consistent hashing on user ID ensures stable assignment across sessions
- **Metrics:** Defined per experiment (primary: click-through rate or watch time; guardrail: session count, error rate)
- **Statistical rigor:** Sequential testing with always-valid p-values, minimum 7-day runtime, minimum sample size per variant
- **Concurrent experiments:** Maximum 3 concurrent experiments per recommendation surface to limit interaction effects

### Fallback Strategy

When AI models are unavailable (outage, deployment, cold start), every AI-powered surface has a defined fallback:

| AI Feature | Primary Source | Fallback | Degradation |
|-----------|---------------|----------|-------------|
| Home recommendations | ML model | Popularity-based (pre-computed top-100 per genre) | Reduced personalization |
| Personalized EPG order | ML model | Default channel number order | No personalization |
| Conversational search | Bedrock LLM | Keyword search (Elasticsearch) | No semantic understanding |
| CDN routing | ML model | Round-robin with geo-affinity | Suboptimal routing |
| Anomaly detection | ML model | Static threshold alerts | Higher false positive rate |
| Content thumbnails | ML-selected variant | Default editorial thumbnail | No personalization |
| Churn prediction | ML model | Rule-based (engagement threshold) | Lower accuracy |

---

## 7. Client Architecture

### Shared Architecture Pattern

```
┌─────────────────────────────────────────────────────┐
│                  Client Application                  │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │           Presentation Layer                    │ │
│  │  - Platform-native UI (Compose/SwiftUI/React)  │ │
│  │  - Design system components                     │ │
│  │  - Navigation & routing                         │ │
│  └────────────────┬───────────────────────────────┘ │
│                   │                                  │
│  ┌────────────────┴───────────────────────────────┐ │
│  │           Business Logic Layer                  │ │
│  │  - View models / state management               │ │
│  │  - Playback controller                          │ │
│  │  - Authentication manager                       │ │
│  │  - Feature flag evaluation                      │ │
│  │  - Telemetry manager                            │ │
│  └────────────────┬───────────────────────────────┘ │
│                   │                                  │
│  ┌────────────────┴───────────────────────────────┐ │
│  │           Platform Integration Layer            │ │
│  │  - Player (ExoPlayer / AVPlayer / Shaka)        │ │
│  │  - DRM module                                   │ │
│  │  - Network layer (HTTP client, caching)         │ │
│  │  - Local storage (offline, settings)            │ │
│  │  - Push notifications                           │ │
│  │  - Cast/AirPlay                                 │ │
│  └────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
                          │
                    ┌─────┴─────┐
                    │  BFF API  │
                    │ (per-client│
                    │  family)   │
                    └───────────┘
```

### Per-Platform Player Integration

| Platform | Player | DRM Module | Codecs | Max Resolution |
|----------|--------|-----------|--------|----------------|
| Android TV | ExoPlayer/Media3 3.3+ | Widevine (L1 on certified devices) | HEVC, H.264, AV1 (device-dependent) | 4K HDR |
| Apple TV | AVPlayer | FairPlay | HEVC, H.264 | 4K HDR (Dolby Vision) |
| Web (Chrome) | Shaka Player 4.x | Widevine (L1 via EME) | H.264, VP9, AV1 | 4K (L1 hardware security) |
| Web (Safari) | Shaka Player 4.x | FairPlay (via EME) | HEVC, H.264 | 4K |
| iOS | AVPlayer | FairPlay | HEVC, H.264 | 1080p (phone), 4K (iPad) |
| Android Mobile | ExoPlayer/Media3 3.3+ | Widevine (L1/L3) | HEVC, H.264 | 1080p (L1), 540p (L3) |
| Samsung Tizen | Shaka Player 4.x | Widevine (L1) | HEVC, H.264 | 4K HDR |
| LG webOS | Shaka Player 4.x | Widevine (L1) | HEVC, H.264 | 4K HDR |

### BFF Pattern

Three BFF services optimize API responses per client family:

**TV BFF (Go):**
- Clients: Android TV, Apple TV, Samsung Tizen, LG webOS, STBs
- Optimization: Pre-composed screen layouts (JSON with positioned tiles), image URLs pre-sized for TV resolution, lazy-loaded sections, pagination tuned for remote control (page-by-page scroll)
- Input model: D-pad navigation focus management metadata in API responses
- Payload size target: < 50KB for home screen initial load

**Mobile BFF (Go):**
- Clients: iOS, Android
- Optimization: Compact payloads (mobile bandwidth), image URLs for mobile DPI, offline manifest generation (download support), touch-optimized layout hints
- Payload size target: < 30KB for home screen initial load
- Additional: Push notification registration endpoints, download management APIs

**Web BFF (Go):**
- Clients: Web browsers
- Optimization: SEO-friendly metadata, responsive layout hints, progressive loading waterfall, service worker cache hints
- Payload size target: < 40KB for home screen initial load
- Additional: Server-side rendering (SSR) data endpoints for initial page load

### Offline Support Strategy

- **Scope:** Mobile clients (iOS, Android) only. TV and web clients are online-only.
- **Downloads:** VOD titles with offline rights can be downloaded for offline playback.
- **License:** Offline DRM license valid for 48 hours (configurable). Auto-renews when online.
- **Quality:** User selects download quality (Low/Medium/High). Default: Medium (720p).
- **Storage:** Client-side storage management with configurable limit. Auto-delete oldest completed downloads when limit approached.
- **Sync:** Bookmarks sync when device comes back online. Viewing events buffered locally and flushed on reconnect.

### Feature Flag Integration

- **Platform:** Unleash (self-hosted) for server-side flags, Unleash SDK for client-side evaluation
- **Granularity:** Flags can target by: user ID, profile ID, device type, platform, OS version, app version, subscription tier, market/region, percentage rollout
- **Client-side:** Flags are fetched on app launch and cached locally. Polling interval: 60 seconds. Fallback to cached values when offline.
- **Use cases:** Feature rollout (per-platform), A/B experiments, kill switches (disable broken feature without app update), configuration (server-driven UI layout changes)

---

## 8. Security Architecture

### Zero-Trust Service Mesh (Istio)

All service-to-service communication runs through Istio sidecar proxies with:
- **mTLS:** Mutual TLS for all internal communication. No plaintext traffic between services.
- **Authorization policies:** Per-service RBAC rules defining which services can call which endpoints
- **Rate limiting:** Per-service rate limits at the mesh level to prevent cascade failures
- **Traffic management:** Circuit breaking, retry policies, timeout enforcement

### DRM Key Management (CPIX Workflow)

```
Content Ingest → Key Management Service → DRM Backends
                         │
                  ┌──────┴──────┐
                  │  Key Store  │
                  │  (Vault)    │
                  └─────────────┘

Key Rotation: Per-content key (not shared across titles)
Key Storage: HashiCorp Vault (encrypted at rest, audit logged)
CPIX Exchange: Standards-based key exchange with DRM providers
```

- Content keys are generated per title (VOD) or per channel per day (live)
- Keys are stored in HashiCorp Vault, never in application databases
- CPIX documents are generated on-demand and cached (TTL: 1 hour for live, 24 hours for VOD)
- Key rotation for live: Every 24 hours with overlap period for client key refresh

### API Authentication (OAuth 2.0 + JWT)

**User Authentication Flow:**
1. User logs in with credentials (email + password) or social login (Google, Apple)
2. Auth Service validates credentials, issues:
   - Access token (JWT, RS256 signed, 15-minute expiry)
   - Refresh token (opaque, stored server-side, 30-day expiry)
3. Access token contains claims: user ID, profile ID, subscription tier, device ID, entitlements (compact representation)
4. Client includes access token in Authorization header for all API calls
5. BFF validates JWT signature and expiry. No call to Auth Service for validation (stateless).
6. Token refresh: Client uses refresh token to obtain new access token before expiry

**Device Activation (TV/STB):**
1. TV app displays activation code (6-character alphanumeric)
2. User visits activation URL on phone/web, enters code
3. User authenticates on phone/web
4. Auth Service links device to user account, issues device-specific token pair
5. TV app polls for activation completion, receives tokens

**Concurrent Stream Enforcement:**
- Playback Session Service tracks active sessions per user
- Session limit: Configurable per subscription tier (e.g., 2 concurrent for basic, 4 for premium)
- When limit exceeded: Newest session denied with user-friendly message showing active devices
- Grace period: 60 seconds between stop and new start to handle device switching

### CDN Token Security (CAT)

- **Algorithm:** ECDSA (ES256) for signature performance
- **Token lifetime:** 5 minutes, refreshed at 4-minute intervals by client
- **Claims:** Session ID, user ID, content ID, CDN hostname, path pattern (regex), expiry timestamp, IP restriction (optional)
- **Validation:** CDN edge validates signature, expiry, and path. No callback to origin.
- **Key rotation:** Signing keys rotated weekly. CDN edge caches both current and previous key for seamless rotation.

### Data Encryption

| Layer | Mechanism | Key Management |
|-------|-----------|---------------|
| Data at rest (S3) | AES-256 (SSE-S3 or SSE-KMS) | AWS KMS |
| Data at rest (RDS) | AES-256 (TDE) | AWS KMS |
| Data at rest (Redis) | AES-256 (encryption at rest) | AWS KMS |
| Data in transit (service mesh) | mTLS (TLS 1.3) | Istio CA (auto-rotated) |
| Data in transit (client to CDN) | TLS 1.3 | CDN-managed certificates |
| Data in transit (client to API) | TLS 1.3 | ACM-managed certificates |
| Content encryption | CBCS (AES-128) | DRM key management (Vault) |
| Secrets | Vault transit engine | Vault auto-unseal (KMS) |

### Content Watermarking Strategy

- **Forensic watermarking:** Applied to premium content (TVOD, early-window VOD) via A/B watermarking at the CDN edge
- **Implementation:** Two slightly different encodes (A and B). CDN selects segments from A or B based on session token, creating a unique per-session watermark pattern
- **Detection:** Watermark pattern maps to session ID → user ID for piracy investigation
- **Phase:** Phase 2 for premium content, Phase 3 for all content

---

## 9. Observability Architecture

### Three Pillars + QoE

```
                    ┌────────────────────────────────────┐
                    │        Observability Platform       │
                    │                                     │
                    │  ┌─────────┐  ┌──────────┐        │
                    │  │ Metrics │  │  Logs    │        │
                    │  │(Prom/   │  │(Loki/    │        │
                    │  │ Grafana)│  │ Elastic) │        │
                    │  └────┬────┘  └────┬─────┘        │
                    │       │            │               │
                    │  ┌────┴────┐  ┌────┴─────┐        │
                    │  │ Traces  │  │  QoE     │        │
                    │  │(Tempo/  │  │(Conviva/ │        │
                    │  │ Jaeger) │  │ Custom)  │        │
                    │  └────┬────┘  └────┬─────┘        │
                    │       │            │               │
                    │  ┌────┴────────────┴─────┐        │
                    │  │   Alert Manager       │        │
                    │  │   (AI-Correlated)      │        │
                    │  │   → PagerDuty          │        │
                    │  └───────────────────────┘        │
                    └────────────────────────────────────┘
```

### Metrics (Prometheus + Grafana)

**Infrastructure Metrics:**
- Collection: Prometheus scraping Kubernetes pods (via pod annotations) + node exporter
- Storage: Prometheus with Thanos sidecar for long-term storage (S3)
- Retention: 15 days local (Prometheus), 1 year remote (Thanos on S3)
- Dashboards: Grafana with pre-built dashboards per service, infrastructure tier, and business view

**Standard Service Metrics (RED):**
Every service exposes:
- **Rate:** Request rate (requests per second)
- **Errors:** Error rate (4xx, 5xx counts and percentages)
- **Duration:** Latency histograms (p50, p90, p95, p99)

**Custom Business Metrics:**
- Active sessions (gauge, by content type, device, region)
- Concurrent viewers per channel (gauge)
- Playback start count (counter, by content type)
- Recommendation impressions and clicks (counter)
- Recording scheduled/completed/failed (counter)
- Search queries (counter, by type: text, conversational, voice)

### Logs (Structured Logging)

**Format:** JSON structured logs with standard fields:

```json
{
  "timestamp": "2026-02-08T14:30:00.123Z",
  "level": "INFO",
  "service": "playback-session",
  "trace_id": "abc123def456",
  "span_id": "789ghi012",
  "user_id": "usr_12345",
  "message": "Playback session started",
  "attributes": {
    "content_id": "vod_67890",
    "device_type": "android_tv",
    "cdn": "akamai",
    "drm": "widevine"
  }
}
```

**Pipeline:** Application → stdout → Fluentd (DaemonSet) → Loki (or Elasticsearch) → Grafana
**Retention:** 30 days searchable (Loki), 1 year archived (S3)
**PII Handling:** User IDs are pseudonymized in logs. Email, IP addresses, and other PII are masked before storage. Full PII available only in audit logs (restricted access, 7-year retention).

### Traces (Distributed Tracing)

**Protocol:** OpenTelemetry (OTel SDK instrumented in all services)
**Backend:** Grafana Tempo (or Jaeger)
**Sampling:** Adaptive sampling — 100% for errors, 10% for normal traffic, 100% for flagged users (debugging)
**Context Propagation:** W3C Trace Context headers propagated through HTTP/gRPC and Kafka messages

**Key Traced Journeys:**
1. **Playback start:** Client → BFF → Entitlement → Token → CDN Routing → Playback Session
2. **Search:** Client → BFF → Search → Elasticsearch → (optional: Bedrock LLM) → Response
3. **Home page:** Client → BFF → Recommendation → Feature Store → Model Serving → Response
4. **Recording schedule:** Client → BFF → Recording → EPG → Entitlement → Notification

### QoE (Quality of Experience)

**Client-Side Collection (Conviva SDK):**
- Video start time (time from play press to first frame rendered)
- Rebuffer events (count, duration, position)
- Bitrate (current, average, switches count)
- Resolution (current, drops)
- Frame drops / rendering errors
- Playback errors (with error codes)
- Session duration and abandonment

**Server-Side QoE Scoring:**
The QoE Service computes a per-session quality score (0-100) combining:

| Factor | Weight | Measurement |
|--------|--------|-------------|
| Video start time | 25% | < 2s = 100, 2-5s linear decrease, > 5s = 0 |
| Rebuffer ratio | 30% | 0% = 100, 0-1% linear decrease, > 1% = 0 |
| Average bitrate (% of max) | 20% | 100% of max = 100, linear decrease |
| Resolution stability | 15% | No drops = 100, each drop = -10 |
| Error-free session | 10% | No errors = 100, any error = 0 |

**QoE Alerting Dimensions:**
Alerts trigger when QoE score (p25) drops below 70 for any segment:
- By CDN provider
- By ISP (top 20)
- By region
- By device platform
- By channel (live)
- By content type (VOD)

### AI-Powered Alert Correlation

- **Anomaly detection:** ML models (see AI/ML Infrastructure) baseline normal behavior per service per time-of-day
- **Alert grouping:** Related alerts across services are grouped into a single incident (e.g., CDN latency spike + playback error rate increase + QoE drop = single CDN incident)
- **Root cause suggestion:** AI analyzes correlated signals and suggests probable root cause (e.g., "CDN A degradation in EU-West region affecting 3,200 live TV sessions")
- **Alert suppression:** Downstream alerts suppressed when upstream root cause is identified (e.g., suppress playback errors when CDN incident detected)
- **Integration:** Correlated alerts sent to PagerDuty with severity, impact assessment, and suggested runbook

### Dashboard Hierarchy

| Dashboard | Audience | Key Panels |
|-----------|----------|-----------|
| **Executive** | Business leadership | Active users, concurrent streams, churn rate, ARPU, top content, revenue |
| **Operations** | SRE, on-call | System health, error rates, latency, CDN performance, QoE score, active incidents |
| **Per-Service** | Service owners | Service-specific RED metrics, dependency health, deployment status |
| **Live TV** | Content ops | Per-channel viewer count, quality score, encoder status, CDN distribution |
| **AI/ML** | ML engineers | Model latency, prediction throughput, drift metrics, A/B experiment results |
| **Content Pipeline** | Content ops | Ingest queue, encoding progress, enrichment status, catalog additions |
| **Business Intelligence** | Product, business | Feature adoption, funnel metrics, recommendation effectiveness, search success |

---

## 10. Deployment & Infrastructure

### Kubernetes Cluster Topology

**Primary Region (EU-West-1):**

| Node Group | Instance Type | Count (Phase 1) | Purpose |
|-----------|--------------|-----------------|---------|
| System | m6i.xlarge | 3 | Kubernetes system (kube-system, istio, monitoring) |
| General Workloads | m6i.2xlarge | 12 | Backend microservices, BFFs |
| Memory Optimized | r6i.2xlarge | 4 | Redis, Elasticsearch, in-memory caches |
| GPU Inference | g5.xlarge | 4 | KServe model serving (T4 GPU) |
| GPU Compute | g5.4xlarge | 2 (spot) | Batch inference, encoding (A10G GPU) |
| Data Processing | m6i.4xlarge | 4 | Kafka consumers, Flink, Spark |

**Total Phase 1 compute:** ~29 nodes, ~116 vCPU, ~464 GB RAM, 6 GPUs

**Scaling to Phase 4 (500K concurrent):**

| Node Group | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|-----------|---------|---------|---------|---------|
| General | 12 | 24 | 40 | 60 |
| Memory | 4 | 8 | 12 | 16 |
| GPU Inference | 4 | 8 | 12 | 16 |
| GPU Compute | 2 | 4 | 6 | 8 |
| Data Processing | 4 | 8 | 12 | 16 |
| **Total Nodes** | **29** | **55** | **85** | **119** |

### CI/CD Pipeline

```
Developer → GitHub PR → CI Pipeline → Staging → Canary → Production

CI Pipeline:
  1. Lint + Format (golangci-lint / ruff)
  2. Unit Tests (go test / pytest)
  3. SAST Scan (Semgrep)
  4. Container Build (Docker)
  5. Container Scan (Trivy)
  6. Integration Tests (against staging deps)
  7. Push to ECR (tagged with git SHA)
  8. Update Helm chart values (new image tag)
  9. ArgoCD detects change, syncs to staging

Staging → Production:
  1. ArgoCD syncs staging deployment
  2. Automated smoke tests pass
  3. Manual approval gate (for production)
  4. ArgoCD syncs production with canary strategy
  5. Canary: 5% traffic for 15 minutes
  6. Automated SLO check (latency, error rate)
  7. If SLO met: progressive rollout (25% → 50% → 100%)
  8. If SLO violated: automatic rollback
```

**Toolchain:**
- SCM: GitHub (monorepo for platform services, separate repos for clients)
- CI: GitHub Actions (self-hosted runners on EC2 for performance)
- CD: ArgoCD (GitOps — Kubernetes state matches Git)
- Container registry: Amazon ECR
- Artifact storage: S3 (Helm charts, test results, build artifacts)
- Secret injection: HashiCorp Vault via Vault Agent sidecar

### Infrastructure as Code (Terraform)

**Repository structure:**
```
terraform/
├── modules/
│   ├── eks/              # Kubernetes cluster
│   ├── rds/              # PostgreSQL instances
│   ├── elasticache/      # Redis clusters
│   ├── msk/              # Kafka clusters
│   ├── s3/               # Storage buckets
│   ├── cloudfront/       # CDN distribution
│   ├── ecr/              # Container registry
│   ├── iam/              # IAM roles and policies
│   ├── vpc/              # Networking
│   └── monitoring/       # CloudWatch, Prometheus setup
├── environments/
│   ├── dev/
│   ├── staging/
│   └── production/
└── global/
    ├── dns/
    ├── certificates/
    └── shared-services/
```

**State management:** Terraform state stored in S3 with DynamoDB locking. Per-environment state files. State access restricted by IAM role.

### Environment Strategy

| Environment | Purpose | Scale | Data | Deployment |
|------------|---------|-------|------|-----------|
| **Dev** | Developer testing | 10% of prod | Synthetic + anonymized sample | Continuous (on PR merge to dev) |
| **Staging** | Integration testing, QA | 25% of prod | Anonymized production mirror | Automatic (on PR merge to main) |
| **Canary** | Production subset | 5% of prod traffic | Production | Automatic (post-staging approval) |
| **Production** | Live users | Full scale | Production | Progressive rollout from canary |

### Multi-Region Considerations

**Phase 1:** Single region (EU-West-1), multi-AZ within region for high availability
**Phase 2:** CDN edge in 3+ regions, origin remains single region
**Phase 3:** Read replicas (RDS, Redis) in second region for reduced latency
**Phase 4:** Active-active in 2 regions with global load balancing

**Multi-region data strategy:**
- Kafka: MirrorMaker 2 for cross-region event replication (async)
- PostgreSQL: Cross-region read replicas (async replication, < 1s lag)
- Redis: Redis Global Datastore for active-active cache replication
- S3: Cross-region replication for media assets

### Cost Optimization Strategy

| Strategy | Savings | Phase |
|----------|---------|-------|
| Spot instances for batch workloads (encoding, ML training) | 60-70% on batch compute | 1 |
| Reserved instances for baseline (general, memory nodes) | 30-40% on steady-state | 1 |
| Per-title encoding optimization | 20-40% on CDN bandwidth | 2 |
| S3 Intelligent-Tiering for data lake | 30-50% on storage | 1 |
| Kafka tiered storage | 40% on Kafka storage | 2 |
| Right-sizing via continuous profiling | 10-20% on over-provisioned services | 2 |
| CDN volume tier negotiation | 10-20% on CDN | 1 |

**Cost Targets:**

| Category | Phase 1 (50K) | Phase 4 (500K) | Monthly |
|----------|--------------|----------------|---------|
| Compute (EKS + EC2) | $35,000 | $180,000 | - |
| Database (RDS + Redis + ES) | $15,000 | $60,000 | - |
| Kafka (MSK) | $8,000 | $30,000 | - |
| Storage (S3 + EFS) | $5,000 | $40,000 | - |
| CDN bandwidth | $30,000 | $200,000 | - |
| GPU (inference + training) | $12,000 | $50,000 | - |
| Other (DNS, LB, monitoring) | $5,000 | $20,000 | - |
| **Total** | **~$110,000/mo** | **~$580,000/mo** | - |
| **Cost per concurrent user** | **$2.20/mo** | **$1.16/mo** | - |

---

## 11. Technology Stack Summary

### Core Platform

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| Container Orchestration | Kubernetes (EKS) | 1.30 | Service deployment and orchestration |
| Service Mesh | Istio | 1.22 | mTLS, traffic management, observability |
| API Gateway | Kong | 3.7 | External API routing, rate limiting, authentication |
| Message Broker | Apache Kafka (MSK) | 3.7 | Event streaming backbone |
| Schema Registry | Confluent Schema Registry | 7.6 | Avro schema management and evolution |
| Service Discovery | Kubernetes DNS + Istio | — | Internal service routing |

### Backend Services

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| Primary Language (high-throughput) | Go | 1.22 | Playback, auth, CDN routing, BFFs |
| Secondary Language (AI-adjacent) | Python | 3.12 | Recommendations, search, content enrichment |
| gRPC Framework | gRPC-Go / grpcio | 1.64 / 1.64 | Service-to-service communication |
| REST Framework (Go) | Chi | 5.0 | HTTP routing for BFFs and external APIs |
| REST Framework (Python) | FastAPI | 0.111 | HTTP APIs for AI services |

### Data Storage

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| Relational Database | PostgreSQL | 16 | Primary data store for most services |
| Vector Extension | pgvector | 0.7 | Vector similarity search for embeddings |
| In-Memory Cache | Redis | 7.2 | Caching, session storage, online feature store |
| Search Engine | Elasticsearch | 8.14 | Full-text search, catalog search, log aggregation |
| Analytics Database | ClickHouse | 24.5 | Real-time analytics, QoE metrics |
| Data Lake Format | Apache Iceberg | 1.6 | Table format for data lake on S3 |
| Stream Processing | Apache Flink | 1.19 | Real-time event processing |
| Batch Processing | Apache Spark | 3.5 | Batch analytics and ML feature computation |

### AI/ML

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| Model Serving | KServe | 0.13 | Real-time ML inference on Kubernetes |
| ML Training | Amazon SageMaker | — | Model training, hyperparameter tuning |
| ML Tracking | MLflow | 2.14 | Experiment tracking, model registry |
| Feature Store | Feast | 0.38 | Online + offline feature serving |
| LLM (Managed) | Amazon Bedrock | — | Conversational search, summarization |
| LLM (Self-Hosted) | vLLM | 0.5 | Embedding generation, batch inference |
| ML Frameworks | TensorFlow 2.16, PyTorch 2.3, XGBoost 2.0 | — | Model development |
| ML Pipeline Orchestration | Apache Airflow | 2.9 | Training pipeline DAGs |

### Content Delivery

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| Media Packaging (Live) | Unified Streaming Platform (USP) | 1.12 | Live CMAF packaging, JIT manifests |
| Media Packaging (VOD) | Shaka Packager | 3.1 | VOD CMAF packaging |
| Transcoding | FFmpeg | 7.0 | VOD encoding pipeline |
| Live Encoding | AWS Elemental MediaLive | — | Live transcoding |
| DRM | Widevine + FairPlay + PlayReady | — | Content protection |
| DRM Key Exchange | CPIX 2.3 | — | Multi-DRM key management |
| CDN (Primary) | Akamai | — | Global content delivery |
| CDN (Secondary) | Amazon CloudFront | — | Backup CDN, origin shield |
| Origin Storage | Amazon S3 | — | Media segment storage |
| Live Segment Storage | Amazon EFS | — | Low-latency live segment I/O |

### Client Platforms

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| Android TV / Mobile | Kotlin + Jetpack Compose | 2.0 | Android client applications |
| Android Player | ExoPlayer / Media3 | 3.3 | Android video playback |
| Apple TV / iOS | Swift + SwiftUI | 5.10 | Apple client applications |
| Apple Player | AVPlayer / AVKit | — | Apple video playback |
| Web | TypeScript + React | 18.3 | Web client application |
| Web Player | Shaka Player | 4.10 | Web video playback |
| Smart TV (Tizen/webOS) | TypeScript + React (adapted) | — | Smart TV client applications |

### Observability

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| Metrics | Prometheus | 2.53 | Metric collection and storage |
| Metrics Visualization | Grafana | 11.0 | Dashboards and alerting |
| Long-term Metrics | Thanos | 0.35 | Prometheus long-term storage on S3 |
| Logging | Grafana Loki | 3.1 | Log aggregation and search |
| Tracing | Grafana Tempo | 2.5 | Distributed trace storage |
| Tracing SDK | OpenTelemetry | 1.35 | Instrumentation |
| QoE Analytics | Conviva | — | Client-side video quality analytics |
| Alerting | PagerDuty | — | On-call management and escalation |
| Log Collector | Fluentd | 1.17 | Log shipping from pods |

### Infrastructure & DevOps

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| Cloud Provider | AWS | — | Primary infrastructure |
| Infrastructure as Code | Terraform | 1.8 | Cloud resource provisioning |
| GitOps | ArgoCD | 2.11 | Kubernetes deployment from Git |
| CI | GitHub Actions | — | Build, test, deploy pipelines |
| Container Registry | Amazon ECR | — | Docker image storage |
| Secret Management | HashiCorp Vault | 1.17 | Secrets, encryption keys, certificates |
| Feature Flags | Unleash | 5.12 | Feature flag management |
| Package Manager | Helm | 3.15 | Kubernetes package management |

### Security

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| Service Mesh Security | Istio (mTLS) | 1.22 | Zero-trust networking |
| API Authentication | OAuth 2.0 + JWT (RS256) | — | User authentication |
| Secret Storage | HashiCorp Vault | 1.17 | Centralized secret management |
| SAST | Semgrep | — | Static code analysis |
| Container Scanning | Trivy | — | Container vulnerability scanning |
| TLS Certificates | AWS Certificate Manager | — | TLS certificate provisioning |
| WAF | AWS WAF | — | Web application firewall |

---

*This architecture document defines the technical foundation for the AI-native OTT streaming platform. All subsequent PRDs, service designs, and implementation plans should reference this document for technology choices, service boundaries, data flows, and infrastructure patterns. Architectural decisions documented here should be treated as defaults — deviations require an ADR (Architecture Decision Record) with justification.*
