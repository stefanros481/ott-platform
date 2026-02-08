# Glossary
## AI-Native OTT Streaming Platform

**Document ID:** GLOSS-001
**Version:** 1.0
**Date:** 2026-02-08
**Status:** Draft
**Audience:** All teams (Engineering, Product, Business, Operations)

---

This glossary defines key terms, acronyms, and domain-specific vocabulary used throughout the platform documentation suite. Terms are organized alphabetically. Each entry includes a brief definition and a note on where the term is primarily used.

---

**A/B Testing** — A controlled experiment method where two or more variants (e.g., recommendation algorithms, UI layouts) are shown to different user segments to measure which performs better against defined metrics. The platform uses A/B testing extensively for ML model rollout, with a minimum 5% traffic allocation per variant and 7-day minimum runtime. Context: PRD-007 (AI UX), ARCH-001 (AI/ML Infrastructure).

**ABR (Adaptive Bitrate Streaming)** — A technique where the video player dynamically selects the best quality level (resolution and bitrate) based on current network conditions, device capability, and buffer status. The platform uses ML-enhanced ABR that makes content-aware decisions: prioritizing framerate for sports and resolution for drama. Context: ARCH-001 (Content Delivery), PRD-001 (Live TV), PRD-008 (AI Backend).

**AIOps (Artificial Intelligence for IT Operations)** — The application of machine learning to automate and improve IT operations, including anomaly detection, predictive alerting, self-healing automation, and capacity planning. The platform targets auto-remediation of 40% of incidents without human intervention. Context: PRD-008 (AI Backend & Ops), VIS-001 (Operational Intelligence pillar).

**ARPU (Average Revenue Per User)** — A business metric measuring the average monthly revenue generated per subscriber. The platform targets ARPU growth from an industry baseline of $12-15 to $18 at 18-month maturity through upsells, TVOD, and dynamic pricing. Context: VIS-001 (Success Metrics), PRD-004 (VOD/SVOD).

**AV1** — An open, royalty-free video codec developed by the Alliance for Open Media. AV1 offers approximately 30% better compression than HEVC at equivalent quality but requires more encoding compute. The platform introduces AV1 encoding for premium 4K content in Phase 3. Context: ARCH-001 (Content Delivery), PRD-006 (Multi-Client).

**AVOD (Advertising-Based Video on Demand)** — A monetization model where content is offered free to viewers, funded by advertising revenue. The platform launches an AVOD tier with SSAI in Phase 2. Context: PRD-004 (VOD/SVOD), VIS-001 (Flexible Monetization pillar).

**BFF (Backend-for-Frontend)** — An architectural pattern where a dedicated backend service is created for each client family (TV, Mobile, Web), tailoring API responses to the specific needs of that client type. The platform uses three BFFs written in Go, each optimizing payload size, layout composition, and navigation metadata for its client family. Context: ARCH-001 (Client Architecture), PRD-006 (Multi-Client).

**CAT (Common Access Token)** — A CDN-agnostic, cryptographically signed token that authorizes access to media segments at the CDN edge. CAT tokens are short-lived (5-minute expiry), signed with ECDSA (ES256), and contain claims such as session ID, content ID, and allowed URL paths. They are validated at the CDN edge without callbacks to the origin. Context: ARCH-001 (Security Architecture, Content Delivery).

**Catch-Up TV** — A TSTV capability that allows viewers to watch previously aired programs within a configurable rolling window, typically 7 days from the original broadcast. Catch-up content is stored as recorded segments at the origin, with per-program and per-channel rights controlling availability. Context: PRD-002 (TSTV), VIS-001 (Service Portfolio).

**CBCS (Common Encryption — CBC Mode with Subsample Patterns)** — The encryption scheme used across all DRM systems on the platform. CBCS enables a single encryption pass to serve Widevine, FairPlay, and PlayReady simultaneously, avoiding the need to store separate encrypted copies per DRM system. Context: ARCH-001 (Content Delivery, Security Architecture).

**CDN (Content Delivery Network)** — A geographically distributed network of edge servers that cache and deliver media content to viewers with low latency. The platform employs a multi-CDN strategy with 2-3 providers (e.g., Akamai, CloudFront, Fastly) and uses ML-based CDN routing to select the optimal provider per session. Context: ARCH-001 (Content Delivery), PRD-008 (CDN & Delivery Intelligence).

**Churn** — The rate at which subscribers cancel their subscriptions over a given period, typically expressed as a monthly percentage. Industry average for OTT platforms is 3.5-5%. The platform targets 2.5% monthly churn at 18-month maturity, aided by AI-driven churn prediction identifying 70% of at-risk subscribers 30 days before cancellation. Context: VIS-001 (Success Metrics), PRD-008 (Business Intelligence AI).

**Cloud PVR (Cloud Personal Video Recorder)** — A network-based recording service that stores subscriber recordings in cloud infrastructure rather than on a local device. The platform's Cloud PVR uses a copy-on-write architecture for storage efficiency and includes AI-powered recording suggestions, smart retention management, and auto-record capabilities. Also known as Network PVR (nPVR). Context: PRD-003 (Cloud PVR).

**CMAF (Common Media Application Format)** — An ISO standard that defines a single segment format (fragmented MP4) usable by both HLS and DASH streaming protocols. CMAF eliminates the need to store duplicate segments for different protocols, reducing storage and origin complexity. Context: ARCH-001 (Content Delivery), PRD-001 (Live TV).

**Cold Start** — The challenge of providing relevant AI recommendations for new users (who have no viewing history) or new content (which has no engagement data). The platform addresses user cold start through an onboarding taste quiz and content-based models, and content cold start through AI metadata enrichment and content similarity analysis. Context: PRD-007 (AI UX), VIS-001 (AI Capability Map).

**Collaborative Filtering** — A recommendation technique that predicts a user's preferences based on the behavior of similar users. For example, "users who watched X also watched Y." The platform uses collaborative filtering as one component of its hybrid recommendation engine, alongside content-based filtering and contextual signals. Context: PRD-007 (AI UX), ARCH-001 (AI/ML Infrastructure).

**Content-Based Filtering** — A recommendation technique that suggests content based on the attributes of items a user has previously enjoyed (genre, cast, mood, themes, visual style). The platform uses deep content embeddings to go beyond surface-level genre matching, capturing narrative structure and emotional tone. Context: PRD-007 (AI UX).

**Copy-on-Write** — A storage optimization pattern used by Cloud PVR where a single master recording is stored per program, and individual users receive entitlement pointers to that master rather than separate copies. This achieves a target storage efficiency ratio of 10:1 or better. Context: PRD-003 (Cloud PVR).

**CPIX (Content Protection Information Exchange)** — An industry standard (DASH-IF) for exchanging content protection (DRM) information between content preparation systems and DRM license servers. The platform uses CPIX 2.3 to manage multi-DRM key exchange with Widevine, FairPlay, and PlayReady from a single encryption workflow. Context: ARCH-001 (Content Delivery, Security Architecture).

**CQRS (Command Query Responsibility Segregation)** — An architectural pattern that separates read and write operations into different models, often backed by different data stores optimized for each access pattern. The platform applies CQRS to services like Catalog (writes to PostgreSQL, reads from Elasticsearch/Redis) and EPG (writes to PostgreSQL, reads from Redis). Context: ARCH-001 (Data Architecture).

**DASH (Dynamic Adaptive Streaming over HTTP)** — An adaptive bitrate streaming protocol standardized by ISO/IEC. DASH uses an MPD (Media Presentation Description) manifest and fragmented MP4 segments. The platform generates DASH manifests from shared CMAF segments alongside HLS manifests. Context: ARCH-001 (Content Delivery).

**DRM (Digital Rights Management)** — Technology used to control access to copyrighted digital media. The platform implements multi-DRM protection using Widevine (Google), FairPlay (Apple), and PlayReady (Microsoft), all encrypted with a single CBCS encryption pass and managed through the CPIX key exchange protocol. Context: ARCH-001 (Security Architecture, Content Delivery).

**EPG (Electronic Program Guide)** — A digital schedule of current and upcoming television programs. The platform's EPG extends the traditional channel-by-time grid with AI personalization including per-user channel ranking, a "Your Schedule" AI-curated timeline, per-program relevance scoring, and family viewing optimization. Context: PRD-005 (EPG), VIS-001 (Service Portfolio).

**FairPlay** — Apple's DRM system for protecting content on Apple devices (Apple TV, iOS, Safari). FairPlay uses hardware-level security on Apple devices and is integrated into the platform via the CPIX multi-DRM workflow. Context: ARCH-001 (Content Delivery, Security Architecture).

**FAST (Free Ad-Supported Television)** — A content distribution model offering linear channels funded by advertising, typically with no subscription required. FAST channels are out of scope for the initial platform release and planned for a future PRD. Context: PRD-001 (Live TV, Out of Scope).

**Feature Store** — A centralized system for storing, managing, and serving pre-computed ML features for both real-time inference (online) and model training (offline). The platform uses Feast with Redis for online serving (< 10ms latency) and S3/Iceberg for offline storage, supporting feature groups for user behavior, content metadata, channel performance, and CDN metrics. Context: ARCH-001 (AI/ML Infrastructure).

**GDPR (General Data Protection Regulation)** — European Union regulation governing the collection, processing, and storage of personal data. The platform is designed with privacy-by-default principles including data minimization, pseudonymization for ML training data, user-facing privacy controls, and consent management. Context: PRD-007 (Ethical AI), VIS-001 (Risks & Mitigations).

**GitOps** — An operational model where the desired state of infrastructure and application deployments is declared in Git, and an automated system (ArgoCD) reconciles the live environment to match. All platform deployments follow GitOps principles with ArgoCD syncing Kubernetes state from Git repositories. Context: ARCH-001 (Deployment & Infrastructure).

**H.264 (AVC)** — A widely supported video codec that serves as the fallback encoding profile on the platform. While less efficient than HEVC or AV1, H.264 is supported by virtually all devices and browsers, ensuring universal playback compatibility. Context: ARCH-001 (Content Delivery).

**HDCP (High-bandwidth Digital Content Protection)** — A form of copy protection that prevents digital content from being copied as it travels across connections (HDMI, DisplayPort). The platform enforces HDCP 2.2 for 4K content on connected devices. Context: ARCH-001 (Security Architecture, Content Delivery).

**HEVC (H.265, High Efficiency Video Coding)** — The primary video codec used by the platform, offering approximately 50% better compression than H.264 at equivalent quality. HEVC is used for all HD and UHD content delivery, with H.264 as a fallback for devices that lack HEVC support. Context: ARCH-001 (Content Delivery).

**HLS (HTTP Live Streaming)** — Apple's adaptive bitrate streaming protocol using M3U8 playlists and media segments. HLS is the primary delivery protocol for Apple devices and is widely supported across other platforms. The platform generates HLS manifests from shared CMAF segments. Context: ARCH-001 (Content Delivery).

**JWT (JSON Web Token)** — A compact, URL-safe token format used for transmitting claims between parties. The platform uses RS256-signed JWTs as access tokens with 15-minute expiry, containing claims for user ID, profile ID, subscription tier, and entitlements. JWTs are validated statelessly at the BFF layer. Context: ARCH-001 (Security Architecture).

**Kafka (Apache Kafka)** — A distributed event streaming platform that serves as the central event bus for the platform. All meaningful state changes are published as Kafka events, enabling loose coupling between services, real-time analytics, CQRS materialized views, and ML feature extraction. The platform runs dual Kafka clusters: real-time (3-day retention) and analytics (30-day retention). Context: ARCH-001 (Data Architecture).

**KServe** — A Kubernetes-native platform for serving ML models with features including autoscaling, canary deployments, and model versioning. The platform uses KServe on GPU nodes for real-time inference of recommendation, CDN routing, anomaly detection, and other ML models with p99 latency targets under 50ms. Context: ARCH-001 (AI/ML Infrastructure).

**Live TV** — The core linear television delivery service that streams 200+ live channels over IP with broadcast-grade reliability. The service supports standard latency (< 5s) and low-latency (< 3s via LL-HLS) modes, AI-personalized channel ordering, and integration with TSTV, Cloud PVR, and EPG. Context: PRD-001 (Live TV).

**LL-HLS (Low-Latency HLS)** — An extension to the HLS protocol that reduces end-to-end latency from the typical 15-30 seconds to under 3 seconds using partial segments (0.5s), blocking playlist reloads, and CDN push. The platform uses LL-HLS for sports and live events. Context: ARCH-001 (Content Delivery), PRD-001 (Live TV).

**MLflow** — An open-source platform for managing the ML lifecycle, including experiment tracking, model versioning, and model registry. The platform uses MLflow as the model registry, with staged rollout from registry to KServe via canary deployments. Context: ARCH-001 (AI/ML Infrastructure).

**MTTD (Mean Time to Detect)** — The average time between the onset of an issue and its detection. The platform targets MTTD of less than 60 seconds at 18-month maturity through ML-based anomaly detection, down from an industry baseline of 8-15 minutes. Context: VIS-001 (Success Metrics), PRD-008 (AIOps).

**MTTR (Mean Time to Resolve)** — The average time between detection of an issue and its resolution. The platform targets MTTR of 5 minutes at 18-month maturity through self-healing automation and predictive alerting, down from an industry baseline of 30-60 minutes. Context: VIS-001 (Success Metrics), PRD-008 (AIOps).

**NPS (Net Promoter Score)** — A metric measuring customer satisfaction and loyalty, calculated from responses to "how likely are you to recommend this service?" The platform targets content discovery NPS of +45 at 18-month maturity, up from an industry baseline of +15. Context: VIS-001 (Success Metrics).

**OAuth 2.0** — An industry-standard authorization framework used for user authentication on the platform. The authentication flow issues JWT access tokens (15-minute expiry) and opaque refresh tokens (30-day expiry), with device activation support for TV/STB clients using activation codes. Context: ARCH-001 (Security Architecture).

**Origin Shield** — A regional caching layer positioned between the origin server and CDN edge servers. Origin shield reduces the load on the origin by absorbing requests from multiple CDN edge nodes within a region, serving as a mid-tier cache. The platform deploys origin shields in EU, US, and APAC regions. Context: ARCH-001 (Content Delivery).

**OTT (Over-the-Top)** — Content delivered directly to viewers over the internet, bypassing traditional cable, satellite, or broadcast distribution. The platform is an OTT streaming service delivering live TV, on-demand video, and time-shifted content to consumer devices over IP. Context: all documents.

**PlayReady** — Microsoft's DRM system, used on some Smart TVs, Xbox consoles, and Windows devices. PlayReady is integrated into the platform via the CPIX multi-DRM workflow alongside Widevine and FairPlay. Context: ARCH-001 (Content Delivery, Security Architecture).

**QoE (Quality of Experience)** — A composite metric measuring the end-user's perceived quality of the streaming experience. The platform computes a per-session QoE score (0-100) based on video start time (25%), rebuffer ratio (30%), average bitrate (20%), resolution stability (15%), and error-free session (10%). Context: ARCH-001 (Observability), PRD-008 (QoE Intelligence).

**RDK (Reference Design Kit)** — An open-source software stack for powering operator set-top boxes and other connected devices. The platform supports RDK-based STB clients as a Phase 2/3 target platform. Context: PRD-006 (Multi-Client).

**SLA (Service Level Agreement)** — A formal commitment defining the expected level of service between a provider and consumer, typically specifying availability, latency, and throughput guarantees. The platform's API availability SLA target is 99.95% at launch, progressing to 99.99%. Context: ARCH-001 (Service Catalog), VIS-001 (Success Metrics).

**SLO (Service Level Objective)** — An internal performance target for a service, more granular than an SLA. Each microservice in the platform has defined SLOs, for example the Playback Session Service targets p99 latency < 200ms with 99.99% availability. SLO violations trigger automated canary rollbacks during deployment. Context: ARCH-001 (Service Catalog, Deployment).

**SSAI (Server-Side Ad Insertion)** — A technique where advertisements are stitched into the video stream on the server side before delivery to the client, making them indistinguishable from content at the player level and resistant to ad blockers. The platform uses SSAI for the AVOD tier, with AI-optimized ad targeting and yield optimization. Context: PRD-004 (VOD/SVOD), PRD-008 (Business Intelligence AI).

**Start Over** — The ability to restart a currently airing program from the beginning. When a viewer tunes into a live broadcast that is already in progress, Start Over allows them to go back to the start of that program with full trick-play controls (pause, rewind, fast-forward), while retaining the option to jump forward to the live edge at any time. The transition from live viewing to Start Over is seamless with no re-authentication required. Context: PRD-002 (TSTV), PRD-001 (Live TV).

**SVOD (Subscription Video on Demand)** — A monetization model where subscribers pay a recurring fee for access to a content library. SVOD is the platform's primary monetization model, with content included in the subscription tier. Context: PRD-004 (VOD/SVOD).

**TSTV (Time-Shifted TV)** — The umbrella term for services that allow viewers to watch content outside its original broadcast time. On this platform, TSTV encompasses two capabilities: Start Over (restart a currently airing program) and Catch-Up TV (watch previously aired programs within a 7-day window). Context: PRD-002 (TSTV).

**TVOD (Transactional Video on Demand)** — A monetization model where viewers pay per-title to rent or purchase individual pieces of content. The platform supports TVOD alongside SVOD, with AI-timed upgrade prompts and a target conversion rate of 5% of SVOD users making TVOD purchases at 18-month maturity. Context: PRD-004 (VOD/SVOD).

**VMAF (Video Multimethod Assessment Fusion)** — A video quality metric developed by Netflix that predicts human perception of video quality on a scale of 0-100. The platform uses VMAF as the primary quality target for encoding ladders, with a target of VMAF > 90 for HD content and VMAF > 95 for premium content. Context: ARCH-001 (Content Delivery), PRD-001 (Live TV).

**VOD (Video on Demand)** — Content available for viewing at any time chosen by the viewer, as opposed to linear/scheduled broadcast. On this platform, VOD encompasses the on-demand catalog delivered through SVOD, TVOD, and AVOD monetization models. Context: PRD-004 (VOD/SVOD).

**Widevine** — Google's DRM system used to protect content on Android devices, Chrome browsers, and many Smart TVs. Widevine offers two security levels: L1 (hardware-backed, required for HD/4K) and L3 (software-only, limited to SD). The platform uses Widevine as the primary DRM for non-Apple devices. Context: ARCH-001 (Content Delivery, Security Architecture).

---

*This glossary is maintained as a living document. As the platform evolves and new terms are introduced, this glossary should be updated to reflect current usage. All documents in the documentation suite should use these terms consistently as defined here.*
