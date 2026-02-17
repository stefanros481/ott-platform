# Claude Code Agents — AI-Native OTT Streaming Platform
## Documentation Generation Prompt Suite

**Purpose:** Generate complete project design, PRDs, and user stories for a greenfield AI-powered OTT streaming platform using Claude Code's Agent Teams feature.

**How to use:** This prompt suite is designed for Claude Code's **Agent Teams** — an experimental feature (shipped with Opus 4.6, February 2026) that lets a single Claude Code session spawn and coordinate multiple teammate instances working in parallel. No separate terminals needed. You can also run these prompts individually as sequential tasks or as subagents.

---

## Prerequisites

### Enable Agent Teams

Agent Teams are experimental and disabled by default. Enable with one of:

```bash
# Option A: Environment variable
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1

# Option B: Add to settings.json
{
  "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
}
```

### How Agent Teams Work

- **Team Lead**: Your main Claude Code session. Creates the team, spawns teammates, assigns tasks, synthesizes results.
- **Teammates**: Separate Claude Code instances, each with its own context window. They load project context (CLAUDE.md, MCP servers, skills) and work independently.
- **Communication**: Teammates coordinate through a shared task list and direct messaging (inbox system). Unlike subagents, teammates can message each other — not just report back to the lead.
- **Token Usage**: Each teammate is a full Claude instance. A 5-teammate team uses ~5× the tokens of a single session. Budget accordingly (see Token Estimates below).

### Agent Teams vs Subagents vs Sequential

| Approach | Best For | Communication | Overhead |
|----------|----------|---------------|----------|
| **Agent Teams** | Parallel work where teammates need to coordinate | Shared task list + direct messaging | High (5× tokens) |
| **Subagents** | Parallel focused tasks that report back | Report to parent only | Medium (per-subagent context) |
| **Sequential** | First run, tight dependencies, budget-conscious | Manual handoff via files | Low (1× tokens) |

**Recommendation for this project:** Use **Agent Teams** for the PRD generation phase (Agents 3–10 can run in parallel). Use **sequential** execution for the foundation documents (Agents 1–2) and the synthesis phases (Agents 11–12) since they depend on earlier outputs.

### Token & Cost Estimates

| Component | Input Tokens | Output Tokens | Total |
|-----------|-------------|---------------|-------|
| Orchestrator | ~3K | ~500 | ~3.5K |
| Agent 1–2 (Vision + Architecture) | ~13K | ~23K | ~36K |
| Agents 3–10 (8 PRDs) | ~220K | ~63K | ~283K |
| Agent 11 (User Stories) | ~82K | ~25K | ~107K |
| Agent 12 (Cross-Cutting) | ~87K | ~12K | ~99K |
| **Total** | **~408K** | **~123K** | **~530K** |

**Cost estimates (single pass):**
- Claude Sonnet 4: ~$3
- Claude Opus 4: ~$15

**With 1.5× iteration multiplier** (revisions, retries): Sonnet ~$5, Opus ~$23.

**Output:** ~93,000 words across 16 documents (~265 pages), ~200 user stories.

---

## Table of Contents

0. [Quick Start — Agent Teams Launch Prompt](#0-quick-start)
1. [Orchestrator Prompt (Team Lead)](#1-orchestrator-prompt)
2. [Agent 1: Project Vision & Design Document](#2-agent-1-project-vision--design)
3. [Agent 2: Platform Architecture Document](#3-agent-2-platform-architecture)
4. [Agent 3: PRD — Live TV & Linear Channels](#4-agent-3-prd-live-tv)
5. [Agent 4: PRD — Time-Shifted TV (Start Over, Catch-Up)](#5-agent-4-prd-tstv)
6. [Agent 5: PRD — Cloud PVR](#6-agent-5-prd-cloud-pvr)
7. [Agent 6: PRD — VOD / SVOD](#7-agent-6-prd-vod-svod)
8. [Agent 7: PRD — TV Guide / EPG](#8-agent-7-prd-epg)
9. [Agent 8: PRD — Multi-Client Support](#9-agent-8-prd-multi-client)
10. [Agent 9: PRD — AI User Experience Layer](#10-agent-9-prd-ai-ux)
11. [Agent 10: PRD — AI Backend & Operations](#11-agent-10-prd-ai-ops)
12. [Agent 11: User Story Generator](#12-agent-11-user-stories)
13. [Agent 12: Cross-Cutting Concerns & Integration](#13-agent-12-cross-cutting)
14. [Execution Guide](#14-execution-guide)

---

## 0. Quick Start — Agent Teams Launch Prompt

> **Copy-paste this into Claude Code to launch the entire documentation team.**
> Requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` to be set.

```
Create an agent team to generate a complete documentation suite for an AI-native 
OTT streaming platform. The project directory is at ./ott-platform-docs/ with 
subdirectories: docs/, docs/prd/, docs/user-stories/, docs/cross-cutting/.

Read CLAUDE.md for full orchestrator instructions and agent prompt details.

Spawn these teammates in two waves:

WAVE 1 — Foundation (run first, others wait):
- "Vision Architect": Creates docs/01-project-vision-and-design.md and 
  docs/02-platform-architecture.md. Signal completion via task list when done.

WAVE 2 — PRDs (spawn after Wave 1 signals complete):  
- "PRD Writer A": Writes PRD-001 (Live TV), PRD-002 (TSTV), PRD-003 (Cloud PVR), 
  PRD-004 (VOD/SVOD). Uses architecture doc as context.
- "PRD Writer B": Writes PRD-005 (EPG), PRD-006 (Multi-Client), PRD-007 (AI UX), 
  PRD-008 (AI Backend/Ops). Uses architecture doc as context.

WAVE 3 — Synthesis (spawn after Wave 2 signals complete):
- "Story Writer": Reads all PRDs, generates user stories in docs/user-stories/
- "Integration Analyst": Reads all docs, writes cross-cutting concerns in 
  docs/cross-cutting/

Coordinate through the shared task list. Each teammate should:
1. Read the relevant agent prompt section from CLAUDE.md
2. Read the architecture doc (once available) for consistency
3. Signal completion via task list when their documents are done
4. Use consistent terminology per the glossary in CLAUDE.md

Ensure all PRDs include AI-specific features, measurable acceptance criteria, 
phase assignments (1-4), and cross-PRD dependency references.
```

### Project Setup (run before launching the team)

```bash
# Create project structure
mkdir -p ott-platform-docs/docs/{prd,user-stories,cross-cutting}

# Copy the orchestrator + all agent prompts into CLAUDE.md
cp claude-code-agents-ott-prompts.md ott-platform-docs/CLAUDE.md

# Navigate to project
cd ott-platform-docs

# Enable agent teams
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1

# Launch Claude Code
claude
```

Then paste the Quick Start prompt above.

### Alternative: Sequential Execution (no Agent Teams needed)

If you prefer running agents one at a time (simpler, fewer tokens, easier to review):

```bash
cd ott-platform-docs

# Phase 1: Foundation
claude "Read CLAUDE.md. Execute Agent 1: Create docs/01-project-vision-and-design.md"
claude "Read CLAUDE.md and docs/01-project-vision-and-design.md. Execute Agent 2: Create docs/02-platform-architecture.md"

# Phase 2: PRDs (run each, or batch)
claude "Read CLAUDE.md, the vision doc, and architecture doc. Execute Agent 3: Create docs/prd/PRD-001-live-tv.md"
claude "Read CLAUDE.md, the vision doc, and architecture doc. Execute Agent 4: Create docs/prd/PRD-002-tstv.md"
claude "Read CLAUDE.md, the vision doc, and architecture doc. Execute Agent 5: Create docs/prd/PRD-003-cloud-pvr.md"
claude "Read CLAUDE.md, the vision doc, and architecture doc. Execute Agent 6: Create docs/prd/PRD-004-vod-svod.md"
claude "Read CLAUDE.md, the vision doc, and architecture doc. Execute Agent 7: Create docs/prd/PRD-005-epg.md"
claude "Read CLAUDE.md, the vision doc, and architecture doc. Execute Agent 8: Create docs/prd/PRD-006-multi-client.md"
claude "Read CLAUDE.md, the vision doc, and architecture doc. Execute Agent 9: Create docs/prd/PRD-007-ai-user-experience.md"
claude "Read CLAUDE.md, the vision doc, and architecture doc. Execute Agent 10: Create docs/prd/PRD-008-ai-backend-ops.md"

# Phase 3: Synthesis
claude "Read CLAUDE.md and all docs in docs/prd/. Execute Agent 11: Generate user stories in docs/user-stories/"
claude "Read CLAUDE.md and all docs/. Execute Agent 12: Create cross-cutting docs in docs/cross-cutting/"
```

### Alternative: Subagents (parallel without inter-agent communication)

```bash
cd ott-platform-docs

# Run foundation sequentially
claude "Execute Agents 1 and 2 from CLAUDE.md to create the vision and architecture docs."

# Then use subagents for parallel PRD generation
claude "Using subagents, execute Agents 3-10 from CLAUDE.md in parallel. \
  Each subagent should read the architecture doc for context. \
  Each produces one PRD in docs/prd/."

# Then synthesis
claude "Execute Agents 11 and 12 from CLAUDE.md to generate user stories and cross-cutting docs."
```

---

## 1. Orchestrator Prompt

> **Use this as the CLAUDE.md file in your project root.**
> When using Agent Teams, the team lead reads this file and delegates to teammates.
> When running sequentially, each `claude` invocation reads this for its agent instructions.

```markdown
# ORCHESTRATOR: AI-Native OTT Streaming Platform Documentation

You are the lead architect orchestrating the creation of a complete documentation 
suite for a greenfield AI-native OTT streaming platform. You coordinate multiple 
specialist agents to produce consistent, high-quality documentation.

## Platform Scope
A next-generation OTT streaming platform with these core services:
- **Live TV** — Linear channel delivery with low-latency streaming
- **TSTV** — Start Over TV and Catch-Up TV (7-day rolling window)
- **Cloud PVR** — Network-based personal recording with AI suggestions
- **VOD/SVOD** — On-demand catalog with subscription and transactional models
- **TV Guide (EPG)** — AI-personalized electronic program guide
- **Multi-Client** — Android TV, Apple TV, iOS, Android, Web, Smart TVs, STBs

## AI Differentiation Strategy
AI is not a bolt-on feature — it is a first-class design principle:
- **User Experience:** Personalized recommendations, conversational search, 
  AI-curated EPG, smart thumbnails, co-viewing detection, content digests
- **Backend/Operations:** ML-based ABR, predictive CDN routing, AIOps, 
  automated content enrichment, churn prediction, dynamic pricing

## Technical Foundation
- Streaming: CMAF with HLS/DASH manifests, LL-HLS for live
- Codecs: HEVC primary, H.264 fallback, AV1 for premium titles
- DRM: Widevine + FairPlay + PlayReady via CBCS encryption
- CDN: Multi-CDN with origin shield, Common Access Token (CAT)
- Backend: Kubernetes microservices, Kafka event-driven, Go + Python
- AI/ML: Hybrid cloud (Bedrock/SageMaker) + self-hosted inference (KServe)
- Scale: 50,000–500,000 concurrent users

## Your Coordination Responsibilities
1. Ensure all agents/teammates use consistent terminology and service names
2. Verify cross-references between documents are accurate
3. Maintain a shared glossary across all outputs
4. Ensure AI capabilities are threaded through every PRD (not siloed)
5. Validate that user stories trace back to PRD requirements
6. Flag gaps or contradictions between agent/teammate outputs
7. When using Agent Teams: coordinate wave execution (Foundation → PRDs → Synthesis)
8. When using Agent Teams: monitor teammate progress via shared task list

## Output Structure
Each agent produces Markdown files. Final structure:
```
docs/
├── 01-project-vision-and-design.md
├── 02-platform-architecture.md
├── prd/
│   ├── PRD-001-live-tv.md
│   ├── PRD-002-tstv.md
│   ├── PRD-003-cloud-pvr.md
│   ├── PRD-004-vod-svod.md
│   ├── PRD-005-epg.md
│   ├── PRD-006-multi-client.md
│   ├── PRD-007-ai-user-experience.md
│   └── PRD-008-ai-backend-ops.md
├── user-stories/
│   ├── US-live-tv.md
│   ├── US-tstv.md
│   ├── US-cloud-pvr.md
│   ├── US-vod-svod.md
│   ├── US-epg.md
│   ├── US-multi-client.md
│   ├── US-ai-ux.md
│   └── US-ai-ops.md
├── cross-cutting/
│   ├── authentication-entitlements.md
│   ├── analytics-telemetry.md
│   ├── content-security.md
│   └── integration-points.md
└── glossary.md
```

## Agent Execution Order

### Wave Model (for Agent Teams)
- **Wave 1: Foundation** → Vision Architect creates vision + architecture docs
- **Wave 2: PRDs** → PRD Writer A (001-004) + PRD Writer B (005-008) in parallel
- **Wave 3: Synthesis** → Story Writer + Integration Analyst in parallel

### Sequential Model (for single-session or subagent execution)
1. **Vision & Design** → establishes scope, principles, success metrics
2. **Platform Architecture** → technical foundation all PRDs reference
3. **PRDs 001–008** → can run in parallel (subagents) after architecture is complete
4. **User Stories** → runs after all PRDs, generates stories per PRD
5. **Cross-Cutting** → runs last, captures integration points and shared concerns

### Teammate Communication Protocol (Agent Teams only)
- Each teammate signals completion via shared task list: "DONE: PRD-001-live-tv.md"
- Wave 2 teammates should NOT start until Wave 1 signals: "DONE: architecture"
- Wave 3 teammates should NOT start until all Wave 2 tasks show DONE
- If a teammate finds a cross-PRD dependency issue, message the affected teammate directly

Delegate each section to the appropriate specialist agent prompt below.
When reviewing outputs, verify that every PRD includes:
- AI-specific features (not just traditional functionality)
- Clear acceptance criteria with measurable targets
- Phase assignment (Phase 1–4)
- Dependencies on other PRDs clearly stated
```

---

## 2. Agent 1: Project Vision & Design

```markdown
# AGENT: Project Vision & Design Document

You are a senior product strategist creating the foundational vision document 
for a greenfield AI-native OTT streaming platform. This document sets the 
direction that all subsequent PRDs and architecture documents will follow.

## Your Output: `docs/01-project-vision-and-design.md`

## Document Structure

### 1. Executive Summary
Write a compelling 1-page summary covering:
- What we are building (AI-native OTT platform, not a traditional TV platform with AI added)
- Why now (market opportunity, competitive landscape, technology readiness)
- Key differentiators vs incumbent platforms
- Target timeline and investment thesis

### 2. Problem Statement
Define the problems this platform solves:
- For **end users**: fragmented experience, poor discovery, one-size-fits-all EPG, 
  no intelligent recording, context-unaware recommendations
- For **operators**: high operational cost, manual content operations, reactive 
  incident management, limited personalization capabilities, legacy platform constraints
- For the **business**: churn from poor experience, inability to monetize data 
  insights, inflexible business models, slow time-to-market for new features

### 3. Vision Statement
A concise, memorable vision statement for the platform. Something that captures:
"An AI-native streaming platform where every interaction learns, every surface 
personalizes, and every operation self-optimizes."

### 4. Strategic Pillars
Define 4-5 strategic pillars, each with:
- Pillar name and one-line description
- Key capabilities enabled
- Success metrics (quantitative)
- AI role in the pillar

Suggested pillars:
1. **AI-First Personalization** — Every user sees a uniquely curated platform
2. **Operational Intelligence** — Self-monitoring, self-healing infrastructure
3. **Content Intelligence** — Automated enrichment from ingest to recommendation
4. **Flexible Monetization** — AI-optimized pricing, packaging, and ad targeting
5. **Platform Openness** — API-first, multi-client, partner-ready

### 5. Target Users & Personas
Define 4-5 user personas with:
- Name, demographic, viewing habits
- Primary device and context (couch, commute, etc.)
- Pain points with current TV experience
- What AI-native means for this persona
- Key scenarios / jobs-to-be-done

Suggested personas:
- **The Busy Professional** — Wants smart catch-up and curated "what to watch"
- **The Family Household** — Multiple profiles, parental controls, co-viewing
- **The Sports Fan** — Live is king, start-over critical, PVR for conflicts
- **The Binge Watcher** — Deep catalog discovery, "more like this", continuity
- **The Casual Viewer** — Low effort, AI-driven "just play something good"

### 6. Service Portfolio
For each service (Live TV, TSTV, Cloud PVR, VOD/SVOD, EPG, Multi-Client), provide:
- One-paragraph service description
- Traditional capability vs AI-enhanced capability (side by side comparison)
- Priority level (Must-have / Should-have / Nice-to-have) for Phase 1 launch

### 7. AI Capability Map
A structured overview of ALL AI capabilities across the platform:
| AI Capability | Service Area | User-Facing / Backend | Phase | Business Impact |
Create this as a comprehensive table with 20-30 AI capabilities.

### 8. Success Metrics & KPIs
Define metrics in three categories:
- **User Experience**: engagement, retention, discovery effectiveness, NPS
- **Operational**: MTTR, automation rate, cost per stream, QoE scores
- **Business**: churn rate, ARPU, conversion, content ROI

For each metric, provide: current industry baseline, target at launch, target at 18 months.

### 9. Implementation Phases
| Phase | Timeline | Focus | Key Deliverables |
Define 4 phases with clear milestones.

### 10. Risks & Mitigations
Top 10 risks with severity, likelihood, and mitigation strategy.
Include AI-specific risks: model accuracy, data privacy, explainability, bias.

### 11. Dependencies & Assumptions
List key assumptions about: content rights, existing infrastructure, team 
capabilities, third-party services, regulatory environment.

## Writing Guidelines
- Be specific and opinionated — avoid vague statements
- Include concrete numbers where possible (targets, benchmarks, timelines)
- Frame everything through the "AI-native" lens — how does AI change this?
- Write for a mixed audience: technical leaders + business stakeholders
- Use tables for structured comparisons
- Every section should answer "so what?" — tie to business value
```

---

## 3. Agent 2: Platform Architecture

```markdown
# AGENT: Platform Architecture Document

You are a principal streaming platform architect designing the technical 
architecture for an AI-native OTT streaming platform. You have 15+ years 
of experience at Netflix-scale platforms.

## Your Output: `docs/02-platform-architecture.md`

## Reference Context
This architecture must support: Live TV, TSTV (Start Over + Catch-Up), Cloud PVR, 
VOD/SVOD, AI-personalized EPG, and multi-client delivery to 50K-500K concurrent users.

## Document Structure

### 1. Architecture Principles
Define 8-10 guiding principles, for example:
- AI-native: ML models are first-class citizens, not afterthoughts
- Event-driven: Kafka backbone for all state changes
- API-first: Every capability exposed via versioned APIs
- Observability-first: Every service emits structured metrics, logs, traces
- Cloud-native: Kubernetes, immutable infrastructure, GitOps
- Multi-tenant ready: Architecture supports white-label deployment
- Progressive enhancement: Graceful degradation when AI models are unavailable

### 2. High-Level Architecture Diagram
Describe (in text, for Mermaid diagram generation) the major subsystems:
- Content Ingest & Enrichment Pipeline
- Encoding / Transcoding Farm
- Packaging & Origin (USP/MediaPackage)
- CDN Layer (multi-CDN with CAT)
- Backend Microservices (Go/Python)
- AI/ML Services Layer (hybrid cloud + self-hosted)
- BFF Layer (per-client backends-for-frontends)
- Client Applications
- Observability Stack
- Data Platform (analytics + ML training)

### 3. Service Catalog
For each microservice, define:
| Service | Language | Primary DB | Events Produced | Events Consumed | Dependencies |

Cover at minimum these services:
- User Service, Auth/Entitlement Service, Profile Service
- Catalog Service, Metadata Service, EPG Service
- Playback Session Service, Bookmark/Continue Watching Service
- Recording Service (Cloud PVR), Schedule Service
- Recommendation Service, Search Service
- Content Ingest Service, Encoding Pipeline Service
- CDN Routing Service, Token Service (CAT)
- Analytics Collector, QoE Service
- Notification Service, Ad Service (SSAI)
- AI Model Serving (KServe), Feature Store

### 4. Data Architecture
- Event schemas (Kafka topics, Avro/Protobuf)
- Database choices per service (PostgreSQL, Redis, Elasticsearch, pgvector)
- Data lake architecture for ML training
- CQRS patterns where applicable
- Data retention policies

### 5. Content Delivery Architecture
- CMAF packaging strategy (HLS + DASH from single segments)
- DRM integration (multi-DRM via CPIX)
- CDN topology (origin → shield → edge)
- Common Access Token (CAT) flow
- ABR ladder definitions (per codec, per content type)
- Low-latency live architecture (LL-HLS, chunked transfer)

### 6. AI/ML Infrastructure
- Model serving architecture (KServe on K8s for real-time, SageMaker for batch)
- Feature store design (online + offline)
- ML pipeline (training → evaluation → deployment → monitoring)
- LLM integration (Bedrock for generative, self-hosted for embeddings)
- Vector database for semantic search (pgvector)
- A/B testing framework for model experiments
- Fallback strategy when models are unavailable

### 7. Client Architecture
- Shared business logic layer (API contracts)
- Per-platform player integration (Shaka, ExoPlayer, AVPlayer)
- BFF pattern (one BFF per client family)
- Offline support strategy
- Feature flag integration (LaunchDarkly/Unleash)

### 8. Security Architecture
- Zero-trust service mesh (Istio)
- DRM key management (CPIX workflow)
- API authentication (OAuth 2.0 + JWT)
- CDN token security (CAT with short-lived tokens)
- Data encryption (at rest + in transit)
- Content watermarking strategy

### 9. Observability Architecture
- Metrics: Prometheus + Grafana (infrastructure), Conviva/Mux (QoE)
- Logs: Structured logging → aggregation → searchable store
- Traces: Distributed tracing across microservices
- Alerts: PagerDuty integration, AI-powered alert correlation
- Dashboards: Operational, business, per-service

### 10. Deployment & Infrastructure
- Kubernetes cluster topology
- CI/CD pipeline (GitHub Actions → ArgoCD)
- Infrastructure as Code (Terraform)
- Environment strategy (dev → staging → canary → production)
- Multi-region considerations
- Cost optimization strategy

### 11. Technology Stack Summary
Comprehensive table of all technologies with version and purpose.

## Writing Guidelines
- Be specific: name exact technologies, versions, and configurations
- Include capacity planning numbers (RPS, storage, bandwidth)
- Define SLOs for critical paths (playback start < 2s, API latency p99 < 200ms)
- Call out trade-offs and ADR-worthy decisions
- Reference industry benchmarks (Netflix, Disney+, etc.)
```

---

## 4. Agent 3: PRD — Live TV

```markdown
# AGENT: PRD-001 — Live TV & Linear Channels

You are a senior product manager writing the PRD for the Live TV service 
of an AI-native OTT streaming platform.

## Your Output: `docs/prd/PRD-001-live-tv.md`

## PRD Template

### 1. Overview
- Service description: Live linear TV channel delivery over OTT
- Business context: Why live TV remains critical (sports, news, events)
- Scope: What's in and out of this PRD

### 2. Goals & Non-Goals
**Goals:**
- Deliver 200+ live channels with < 5 second glass-to-glass latency
- Support LL-HLS for sports/events (< 3 second latency)
- AI-enhanced channel surfing and discovery
- Seamless integration with EPG, TSTV, and Cloud PVR

**Non-Goals:**
- FAST channels (separate PRD)
- Ad insertion for live (covered in monetization PRD)

### 3. User Scenarios
Write 8-10 detailed user scenarios covering:
- Channel surfing with AI-suggested next channel
- Joining a live event mid-stream (with instant catch-up option)
- Multi-angle/multi-audio selection
- Picture-in-picture while browsing
- "What's popular right now" live discovery
- Parental controls on live content
- Recording from live (handoff to Cloud PVR)
- Sports with real-time stats overlay

### 4. Functional Requirements
For each requirement, specify:
- Requirement ID (LTV-FR-001)
- Description
- Priority (P0/P1/P2)
- Phase (1-4)
- AI Enhancement (if applicable)
- Acceptance Criteria (testable, measurable)

Cover:
- Channel acquisition and tuning
- Channel list management and favorites
- Mini EPG overlay during viewing
- Trick-play (pause live, rewind to buffer start)
- Multi-audio and subtitle selection
- Accessibility (audio description, closed captions)
- Channel resolution and codec negotiation
- Graceful degradation (codec fallback, resolution step-down)
- Emergency Alert System integration

### 5. AI-Specific Features
Detail each AI feature:
- **Smart Channel Surfing**: AI predicts next channel based on viewing history + time
- **Live Popularity Signals**: Real-time "trending now" across channels
- **Personalized Channel Order**: AI-ranked channel list per user/household
- **Intelligent Buffer**: ML-predicted buffer depth based on content type
- **AI Quality Monitoring**: Automated quality degradation detection per channel

### 6. Non-Functional Requirements
- Latency: Channel change < 1.5s (p95), live delay < 5s standard / < 3s LL-HLS
- Availability: 99.95% per channel
- Scale: 200+ simultaneous channels, 500K concurrent viewers
- Quality: VMAF > 90 for HD channels

### 7. Technical Considerations
- Ingest architecture (redundant feeds, failover)
- Packaging (CMAF, JIT manifests per DRM)
- CDN delivery (live edge, segment duration optimization)
- Player integration (ABR, codec selection)

### 8. Dependencies
- EPG Service (PRD-005) for program metadata
- Cloud PVR (PRD-003) for record-from-live
- TSTV (PRD-002) for start-over capability
- Auth/Entitlement for channel package access
- CDN with CAT token support

### 9. Success Metrics
| Metric | Baseline | Target | Measurement |
Define 8-10 metrics specific to live TV.

### 10. Open Questions & Risks
List unresolved decisions and key risks.
```

---

## 5. Agent 4: PRD — TSTV

```markdown
# AGENT: PRD-002 — Time-Shifted TV (Start Over & Catch-Up)

You are a senior product manager writing the PRD for TSTV services.

## Your Output: `docs/prd/PRD-002-tstv.md`

## Scope
- **Start Over TV**: Restart a currently airing program from the beginning
- **Catch-Up TV**: Watch previously aired programs (7-day rolling window)

## Key Requirements to Cover

### Start Over TV
- Seamless transition from live → start-over (no re-authentication)
- UI affordance: "This program started 20 min ago — Start from beginning?"
- AI suggestion: Auto-detect when user tunes in late and proactively offer restart
- Content rights: Per-channel/per-program start-over eligibility
- Trick-play: Full trick-play (FF, RW, pause) in start-over mode
- Catch-up to live: Option to jump back to live at any point
- Bookmark: If user leaves mid-program, resume from bookmark

### Catch-Up TV
- 7-day rolling window (configurable per channel/content rights)
- Browse by: channel → day → program, or search, or AI-curated
- AI feature: "You missed this" — personalized catch-up suggestions
- AI feature: "Trending yesterday" — popular catch-up content
- Content rights management (some programs excluded from catch-up)
- Expiry handling: Clear UI when content is about to expire
- Integration with EPG for program metadata

### AI Enhancements
- Personalized catch-up feed ("Your Catch-Up" rail)
- Smart notifications: "The show you usually watch aired yesterday"
- AI-generated program summaries for catch-up browse
- Viewing pattern prediction: Pre-warm CDN cache for likely catch-up viewing
- Auto-bookmarking: AI detects natural chapter breaks

### Non-Functional
- Start-over initiation: < 3 seconds
- Catch-up catalog availability: Within 5 minutes of broadcast end
- Storage: Estimate per-channel storage for 7-day window
- Rights: Per-program, per-channel, per-territory granularity

Follow the same PRD template structure as PRD-001 (overview, goals, scenarios, 
functional requirements with IDs, AI features, NFRs, dependencies, metrics, risks).
```

---

## 6. Agent 5: PRD — Cloud PVR

```markdown
# AGENT: PRD-003 — Cloud PVR (Network PVR)

You are a senior product manager writing the PRD for Cloud PVR.

## Your Output: `docs/prd/PRD-003-cloud-pvr.md`

## Scope
Network-based personal video recording service where recordings are stored 
in the cloud, accessible from any device.

## Key Requirements to Cover

### Core Recording
- Manual recording: Single program or series recording
- Series link: Record all episodes (new only / all / new + repeats)
- Conflict-free: Cloud = no tuner conflicts (unlike traditional PVR)
- Storage model: Per-user quota (e.g., 100 hours base, expandable)
- Copy-on-write: Single master recording, per-user entitlement pointers
- Retention: User-configurable auto-delete (oldest first / never)
- Recording management: List, sort, filter, delete recordings

### AI-Powered Recording
- **Smart Suggestions**: "Based on your viewing, you might want to record..."
  - Sources: viewing history, genre preferences, trending content, social signals
  - Confidence scoring: Only suggest above threshold to avoid fatigue
  - One-tap accept from notification or EPG
- **Auto-Record (Phase 4)**: Autonomous recording based on learned preferences
  - User opts in, can review and remove before storage quota hit
  - Learns from accepts/rejects to improve accuracy
- **AI Reminders**: "New season of [show] starts Tuesday — record it?"
- **Smart Retention**: AI suggests recordings to delete when quota approached
  - Considers: watched %, availability elsewhere (catch-up/VOD), age, user rating
- **Recording Highlights**: AI-generated chapter marks and highlights for sports

### Playback from Recording
- Full trick-play (FF at multiple speeds, RW, pause, skip)
- Resume from bookmark across devices
- Skip intro / skip recap (AI-detected markers)
- AI-generated chapter navigation for long recordings

### Rights & Business Rules
- Per-channel recording eligibility
- Advertising rules in recordings (SSAI, no skip in some markets)
- Regulatory compliance (varies by market — some require individual copies)
- Expiry rules (e.g., recording expires if re-run rights lapse)

### Non-Functional
- Recording start accuracy: ± 5 seconds of scheduled time
- Recording availability: Playable within 2 minutes of program end
- Storage: Copy-on-write to minimize physical storage (target 10:1 ratio)
- Quota management: Real-time usage tracking

Follow full PRD template structure.
```

---

## 7. Agent 6: PRD — VOD / SVOD

```markdown
# AGENT: PRD-004 — VOD / SVOD

You are a senior product manager writing the PRD for the on-demand video service.

## Your Output: `docs/prd/PRD-004-vod-svod.md`

## Scope
On-demand content catalog supporting multiple monetization models:
- **SVOD**: Subscription-included content
- **TVOD**: Transactional rent/buy
- **AVOD**: Ad-supported free tier (Phase 2)
- **Premium Add-ons**: Channel/package add-ons (e.g., HBO, sports packs)

## Key Requirements to Cover

### Catalog & Content Management
- Hierarchical catalog: Titles → Seasons → Episodes
- Multi-format: Movies, series, documentaries, kids, music, shorts
- Metadata: Title, synopsis, cast, crew, genres, tags, ratings, duration
- AI-enriched metadata: Mood, themes, visual style, content warnings, AI-generated tags
- Availability windows: Per-territory, per-platform, per-monetization model
- Content freshness: New arrivals, expiring soon, seasonal promotions

### Discovery & Browse
- Home screen: Personalized rails (Continue Watching, For You, Trending, New, etc.)
- Category browse: Genre, mood, decade, language, etc.
- Search: Text search + AI conversational search ("show me something like X but funnier")
- Collections: Editorial + AI-curated thematic collections
- Filtering: Resolution, audio format, subtitle availability, duration

### AI-Powered Discovery
- **Recommendation Engine**: Hybrid collaborative + content-based + contextual
  - 7+ recommendation surfaces (home, detail, post-play, search, notifications, etc.)
  - Cold-start handling for new users and new content
  - Diversity injection to avoid filter bubbles
- **Personalized Thumbnails**: AI-selected thumbnail per user per title
- **AI Hero Spotlight**: Personalized hero banner selection per session
- **Conversational Search**: Natural language queries with semantic understanding
- **"What's New & Worth It" Digest**: Weekly personalized discovery feed
- **Co-viewing Detection**: Adapt recommendations when multiple people watching

### Playback
- Adaptive bitrate streaming (CMAF, HLS/DASH)
- Multi-audio and subtitle selection
- Resume/continue watching across devices
- Binge mode: Configurable auto-play next episode
- Skip intro / skip recap (AI-detected or manual markers)
- Download for offline (where rights permit)
- Quality selection (auto / manual resolution preference)

### Monetization Integration
- Entitlement checks: Real-time verification per title per user
- Paywall UX: Clear messaging for TVOD/upgrade prompts
- Dynamic pricing (Phase 3): AI-optimized pricing per user segment
- Churn prediction: Surface at-risk users with targeted content recommendations

Follow full PRD template structure.
```

---

## 8. Agent 7: PRD — TV Guide / EPG

```markdown
# AGENT: PRD-005 — TV Guide / Electronic Program Guide (EPG)

You are a senior product manager writing the PRD for the AI-personalized EPG.

## Your Output: `docs/prd/PRD-005-epg.md`

## Scope
A next-generation electronic program guide that goes beyond the traditional 
grid to become an AI-driven discovery and planning tool.

## Key Requirements to Cover

### Traditional EPG
- Grid view: Channels × time (standard 7-day forward schedule)
- Channel filtering: By package, favorites, genre, HD/UHD
- Program details: Synopsis, cast, ratings, availability (catch-up, recording)
- Quick actions from EPG: Watch live, Start over, Record, Set reminder
- Navigation: Time-scroll, channel-scroll, jump to now, jump to date
- Search within EPG

### AI-Personalized EPG ("Your Schedule")
- **Personalized Channel Order**: AI-ranked by relevance per user per time-of-day
- **"Your Schedule" View**: AI-curated timeline showing recommended programs
  - Considers: viewing history, time preferences, genre preferences, household profiles
  - Mix of: live programs, upcoming must-watch, catch-up suggestions
  - Includes cross-source: live + catch-up + VOD + recordings
- **Relevance Scoring**: Each program scored 0-100 for the active viewer profile
  - Factors: genre match, cast match, trending score, time appropriateness
  - Visible as subtle indicator (star rating, "recommended for you" badge)
- **"Family Schedule"**: Co-viewing optimized view for shared viewing sessions
  - Detects household members present, recommends content suitable for group
- **Smart Reminders**: AI-triggered notifications for programs matching interests
  - "New episode of [show] in 30 minutes on [channel]"
  - Frequency capped to avoid notification fatigue

### Program Enrichment
- AI-generated program summaries (when editorial summary unavailable)
- Related content links (similar programs, same series, same actor)
- Social signals ("trending", "most recorded", viewer count for live)
- AI content tags visible in EPG (mood, theme, suitability)

### Non-Functional
- EPG data freshness: Updated within 5 minutes of source change
- EPG load time: < 2 seconds for initial grid render
- Personalization latency: AI scoring completes within request lifecycle (< 200ms)
- 7-day forward + 7-day backward schedule data

### Diversity & Fairness
- Diversity injection: Ensure AI doesn't create filter bubbles
- Editorial override: Human curation can boost/pin programs
- Graceful degradation: When AI unavailable, fall back to standard grid view

Follow full PRD template structure.
```

---

## 9. Agent 8: PRD — Multi-Client Support

```markdown
# AGENT: PRD-006 — Multi-Client Platform Support

You are a senior product manager writing the PRD for multi-client support.

## Your Output: `docs/prd/PRD-006-multi-client.md`

## Scope
Define the client platform strategy, shared capabilities, and per-platform 
considerations for delivering a consistent yet platform-optimized experience.

## Target Platforms
| Platform | Priority | Technology | Player |
|----------|----------|------------|--------|
| Android TV / Google TV | P0 - Launch | Kotlin + Compose | ExoPlayer/Media3 |
| Apple TV (tvOS) | P0 - Launch | Swift + SwiftUI | AVPlayer |
| Web Browser | P0 - Launch | TypeScript + React | Shaka Player |
| iOS (iPhone/iPad) | P1 - Launch | Swift + SwiftUI | AVPlayer |
| Android Mobile | P1 - Launch | Kotlin + Compose | ExoPlayer/Media3 |
| Samsung Tizen | P1 - Phase 2 | TypeScript + React | Shaka Player |
| LG webOS | P1 - Phase 2 | TypeScript + React | Shaka Player |
| Operator STB (RDK/Android) | P2 - Phase 2 | Varies | Varies |
| Chromecast / AirPlay | P2 - Phase 2 | Cast SDK | Per-platform |

## Key Requirements to Cover

### Shared Architecture
- BFF (Backend-for-Frontend) pattern: One BFF per client family
- API contracts: Shared API specs, per-client response tailoring
- Design system: Cross-platform component library with platform adaptations
- Feature flags: Per-platform feature rollout capability
- Configuration: Remote config for client behavior tuning

### Per-Platform Considerations
For each platform, cover:
- Native capabilities and platform guidelines
- Player integration and DRM specifics
- Input model (remote, touch, mouse/keyboard, voice)
- Platform-specific features (PiP, notifications, widgets, deep links)
- App lifecycle and background behavior
- Performance targets (launch time, memory, battery)
- Accessibility requirements per platform

### Cross-Device Experience
- Profile sync: Seamless handoff between devices
- Continue watching: Accurate bookmark sync (< 5 second accuracy)
- Second screen: Companion app features (browse while watching on TV)
- Cast/AirPlay: Seamless protocol support
- Device management: View and manage authorized devices
- Concurrent stream limits: Per-subscription enforcement

### AI on Client
- On-device ML for: UI personalization, pre-fetching, local quality optimization
- Edge inference: Where latency-sensitive personalization runs on-device
- Client-side telemetry: Feeding engagement signals back to recommendation models

### Quality Assurance
- Device matrix: Supported devices, minimum OS versions, test coverage
- Automated testing strategy per platform
- Performance benchmarks per platform tier
- Certification requirements (Google, Apple, Samsung, LG)

Follow full PRD template structure.
```

---

## 10. Agent 9: PRD — AI User Experience Layer

```markdown
# AGENT: PRD-007 — AI User Experience Layer

You are a senior AI product manager writing the PRD for all user-facing AI 
capabilities that span across services.

## Your Output: `docs/prd/PRD-007-ai-user-experience.md`

## Scope
This PRD covers AI capabilities that enhance the end-user experience across 
all services. It is the cross-cutting AI UX layer that other PRDs reference.

## AI Capabilities to Cover

### 1. Recommendation Engine
- Architecture: Hybrid collaborative + content-based + contextual + trending
- Surfaces: Home, detail page, post-play, search, EPG, notifications, digest, 
  in-player, Cloud PVR suggestions, editorial lanes
- Cold-start strategy: New users (onboarding quiz + popularity), new content (content-based)
- Diversity: Configurable diversity injection to prevent filter bubbles
- Explainability: "Because you watched X", "Trending in your area", "New in genres you love"
- A/B testing: Framework for testing recommendation algorithms
- Feedback loop: Implicit (watch time, completion) + explicit (thumbs up/down, "not interested")

### 2. Personalized Discovery
- **AI Hero Spotlight**: Per-session personalized hero banner with multi-variant creative
- **Personalized Thumbnails**: AI-selected thumbnail variant per user per title
- **"What's New & Worth It" Digest**: Weekly personalized content discovery
- **Smart Search**: Semantic search + conversational ("find me a thriller from the 90s")
- **Mood-Based Browse**: "I feel like something light and funny" → curated results

### 3. Viewing Intelligence
- **Co-Viewing Detection**: Detect multiple viewers, adapt content suggestions
  - Household profiles, confidence scoring (0.0–1.0)
  - "Watch Together" mode vs individual profile
- **Viewing Context Awareness**: Time of day, device type, duration available
  - Morning commute (phone) → short content
  - Evening couch (TV) → long-form
- **Smart Continue Watching**: AI-prioritized, stale content auto-archived
- **Skip Intelligence**: AI-detected intro/recap/credits markers

### 4. Content Intelligence
- **AI-Generated Metadata**: Tags, mood, themes, content warnings
- **AI Summaries**: Program descriptions when editorial unavailable
- **Trailer Selection**: AI-picked trailer variant per user interest
- **Content Similarity**: Deep content-based similarity beyond genre

### 5. Proactive Engagement
- **Smart Notifications**: AI-timed, personalized, frequency-capped
  - "New episode available", "Live event starting", "Expiring soon"
- **Re-engagement**: Churn-risk users get targeted content suggestions
- **Onboarding Personalization**: New user taste profiling (3-5 question quiz)

### Ethical AI Requirements
- Transparency: Users can see why content was recommended
- Control: Users can reset recommendations, exclude genres, "not interested"
- Privacy: Clear data usage policy, GDPR compliance, data minimization
- Bias monitoring: Regular audits for demographic or content bias
- Age-appropriate: AI respects parental control boundaries

### Non-Functional
- Recommendation latency: < 100ms (p95) for real-time surfaces
- Model refresh: < 1 hour for incorporating new viewing signals
- Fallback: Graceful degradation to popularity-based when AI unavailable
- A/B framework: Minimum 5% traffic allocation per experiment

Follow full PRD template structure with detailed acceptance criteria.
```

---

## 11. Agent 10: PRD — AI Backend & Operations

```markdown
# AGENT: PRD-008 — AI Backend & Operations Intelligence

You are a senior platform engineer writing the PRD for backend AI capabilities 
and AIOps that power the platform's operational intelligence.

## Your Output: `docs/prd/PRD-008-ai-backend-ops.md`

## Scope
AI capabilities that optimize backend operations, infrastructure management, 
and business intelligence — not directly visible to end users.

## AI Capabilities to Cover

### 1. Content Operations AI
- **Automated Ingest Enrichment**: AI processes every piece of ingested content
  - Automatic subtitle generation (Whisper STT → translation)
  - Thumbnail extraction and AI quality scoring
  - Content fingerprinting for duplicate detection
  - Scene detection for chapter markers
  - Content moderation (nudity, violence, language classification)
  - Audio normalization analysis
- **Per-Title Encoding**: ML model predicts optimal encoding ladder per title
  - Based on: content complexity, motion, grain, target quality (VMAF)
  - Saves 20-40% bandwidth vs fixed ladder
- **AI Metadata Enrichment**: Automated tagging, mood classification, content graph

### 2. CDN & Delivery Intelligence
- **Predictive CDN Routing**: ML model selects optimal CDN per session
  - Inputs: user location, ISP, time, historical CDN performance, load
  - Real-time switching on quality degradation
- **Predictive Cache Warming**: Pre-populate CDN edge caches
  - Based on: EPG schedule, trending content, time-of-day viewing patterns
  - Reduces origin load and improves cache hit ratio
- **ABR Optimization**: ML-enhanced ABR algorithm
  - Predicts bandwidth trajectory, reduces rebuffering
  - Content-aware: Sports = prioritize framerate, drama = prioritize resolution

### 3. AIOps & Infrastructure Intelligence
- **Anomaly Detection**: ML models baseline normal behavior per service
  - Auto-detect anomalies in: error rates, latency, throughput, resource usage
  - Correlate anomalies across services for root cause analysis
- **Predictive Alerting**: Alert BEFORE impact reaches users
  - Predict: capacity exhaustion, cascade failures, degradation trends
- **Self-Healing**: Automated remediation for known failure patterns
  - Auto-scale, auto-restart, traffic shift, circuit break
  - Runbook automation integrated with incident management
- **Capacity Planning**: ML-based demand forecasting
  - Predict: concurrent users per hour, encoding queue depth, storage growth

### 4. Business Intelligence AI
- **Churn Prediction**: ML model identifies at-risk subscribers
  - Signals: declining engagement, support contacts, payment failures, viewing pattern changes
  - Triggers: Targeted content recommendations, retention offers, proactive support
  - Target: Identify 70%+ of churning users 30 days before churn event
- **Dynamic Pricing (Phase 3)**: AI-optimized pricing per segment
- **Content Valuation**: Predict content ROI before acquisition
  - Based on: similar content performance, genre trends, cast popularity, market data
- **Ad Optimization (AVOD)**: AI-targeted ad insertion, yield optimization

### 5. Quality of Experience Intelligence
- **Real-Time QoE Scoring**: Per-session quality score combining:
  - Video start time, rebuffer ratio, bitrate, resolution changes, errors
  - Contextual: device capability, network quality expectations
- **QoE-Driven Alerting**: Alert on QoE degradation by segment
  - Dimensions: ISP, device, region, channel, content type
- **Viewer Impact Analysis**: Quantify user impact of every incident
  - "This outage affected 12,000 viewers, 3,200 during live sports"

### Non-Functional
- Anomaly detection latency: < 60 seconds from event to alert
- Churn model refresh: Daily retraining with latest signals
- CDN routing decision: < 50ms additional latency
- Model monitoring: Drift detection with automated retraining triggers

### AI Infrastructure Requirements
- ML pipeline: Training → evaluation → staged rollout → monitoring
- Feature store: Online (Redis) + offline (data lake) feature serving
- Model registry: Versioned models with A/B deployment capability
- GPU allocation: Shared inference cluster with autoscaling
- Cost targets: AI infrastructure < 15% of total platform cost

Follow full PRD template structure with detailed acceptance criteria.
```

---

## 12. Agent 11: User Story Generator

```markdown
# AGENT: User Story Generator

You are a senior scrum master generating user stories from the completed PRDs. 
You create well-structured stories with clear acceptance criteria that 
development teams can immediately pick up.

## Your Output: One file per PRD in `docs/user-stories/`

## User Story Format

For each story, use this format:

```
### US-{PRD}-{NNN}: {Title}

**As a** {persona/role}
**I want to** {action/capability}
**So that** {benefit/value}

**Priority:** P0/P1/P2
**Phase:** 1/2/3/4
**Story Points:** S/M/L/XL (relative sizing)
**PRD Reference:** {requirement ID}

**Acceptance Criteria:**
- [ ] Given {context}, when {action}, then {expected result}
- [ ] Given {context}, when {action}, then {expected result}
- [ ] Performance: {measurable target}

**AI Component:** {Yes/No — if yes, describe the AI element}

**Dependencies:** {list of dependent stories or services}

**Technical Notes:**
- {implementation hints, architecture considerations}
```

## Story Generation Rules

1. **One story per user-facing capability** — don't combine unrelated features
2. **Vertical slices** — each story delivers end-to-end value (not "build API" then "build UI")
3. **Include AI variants** — traditional capability + AI enhancement as separate stories
4. **Include non-functional stories** — performance, security, observability per service
5. **Include technical enabler stories** — infrastructure, CI/CD, shared services
6. **Epic grouping** — group stories into epics that map to PRD sections
7. **Acceptance criteria must be testable** — include specific numbers, behaviors, edge cases
8. **Definition of Done** — each story implies: code reviewed, tested, documented, monitored

## Per-PRD Story Generation

For each PRD, generate:
- **8-15 core functional stories** (P0 features)
- **5-10 AI enhancement stories** (the AI differentiators)
- **3-5 non-functional stories** (performance, security, monitoring)
- **2-3 technical enabler stories** (infrastructure, integration)

## Example Stories

**Live TV — Core:**
US-LTV-001: Channel Tune & Playback
As a viewer, I want to select a channel and start watching live TV 
so that I can enjoy linear programming.
AC: Channel starts playing within 1.5s (p95), ABR starts at appropriate 
quality, audio is in sync, EPG mini-bar shows current program info.

**Live TV — AI:**
US-LTV-010: AI Smart Channel Order
As a viewer, I want my channel list ordered by AI-predicted relevance 
so that channels I'm likely to watch appear first.
AC: Channel order personalized per profile, updates based on time-of-day, 
fallback to default order if AI unavailable, user can pin favorites 
to override AI ordering.

Generate the complete set for all 8 PRDs.
```

---

## 13. Agent 12: Cross-Cutting Concerns

```markdown
# AGENT: Cross-Cutting Concerns & Integration Points

You are a senior architect documenting the shared concerns that span 
across all services and PRDs.

## Your Outputs:
- `docs/cross-cutting/authentication-entitlements.md`
- `docs/cross-cutting/analytics-telemetry.md`
- `docs/cross-cutting/content-security.md`
- `docs/cross-cutting/integration-points.md`

## Authentication & Entitlements
- User authentication flow (OAuth 2.0, device activation, SSO)
- Session management (concurrent stream limits, device management)
- Entitlement model: Packages, add-ons, TVOD purchases, promotions
- Per-service entitlement checks (live channel access, recording rights, VOD access)
- Parental controls and PIN management
- Guest/trial access model

## Analytics & Telemetry
- Client-side event taxonomy (play, pause, seek, browse, search, error, etc.)
- Server-side event collection (API calls, service metrics)
- Data pipeline: Client → collector → Kafka → data lake → ML training
- Real-time analytics vs batch analytics
- Privacy: Data minimization, anonymization, consent management, GDPR
- Key business dashboards and reports

## Content Security
- DRM implementation details per platform
- Widevine security levels (L1/L3) per device
- HDCP enforcement
- Watermarking strategy (forensic watermarking for premium content)
- Anti-piracy monitoring
- Geo-blocking enforcement
- Token security (CAT implementation details)

## Integration Points
- Service-to-service dependency map
- API gateway configuration
- Event-driven integration patterns (Kafka topic ownership)
- Third-party integrations (EPG providers, content providers, payment, CDN, DRM)
- Data flow diagrams for key user journeys:
  1. User starts watching live TV
  2. User records a program
  3. User browses and plays VOD
  4. AI generates a recommendation
  5. Content is ingested and becomes available

For each integration point, document: owner, contract, SLA, error handling, 
monitoring, and fallback behavior.
```

---

## 14. Execution Guide

### Execution Approaches Compared

| Approach | Total Time | Token Cost | Complexity | Best When |
|----------|-----------|------------|------------|-----------|
| **Agent Teams (5 teammates)** | ~30-45 min | ~530K tokens (5× parallel) | Medium | You want speed and have budget |
| **Subagents (parallel PRDs)** | ~45-60 min | ~530K tokens | Low | PRDs can be independent, no cross-talk needed |
| **Sequential (one at a time)** | ~2-3 hours | ~530K tokens | Lowest | First run, tight budget, maximum control |

Note: Total tokens consumed is similar across approaches — the difference is wall-clock time and coordination overhead.

### Recommended Approach: Hybrid

The most practical approach combines sequential foundation work with parallel PRD generation:

```
Phase 1 (Sequential):   Agent 1 → Agent 2         (~15 min)
Phase 2 (Parallel):     Agents 3-10 via team/sub   (~15-20 min)  
Phase 3 (Sequential):   Agent 11 → Agent 12        (~15-20 min)
```

### Agent Teams Execution (Recommended)

```bash
# 1. Setup
mkdir -p ott-platform-docs/docs/{prd,user-stories,cross-cutting}
cp claude-code-agents-ott-prompts.md ott-platform-docs/CLAUDE.md
cd ott-platform-docs
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1

# 2. Launch Claude Code and paste the Quick Start prompt from Section 0
claude
```

**What happens:**
1. Claude (team lead) reads CLAUDE.md and creates the team structure
2. Vision Architect teammate spawns and creates foundation docs
3. Once foundation is done, two PRD Writer teammates spawn in parallel
4. Once PRDs are done, Story Writer and Integration Analyst spawn
5. Team lead synthesizes and reports completion

**Monitoring:** You can interact with individual teammates directly during execution to check progress, provide guidance, or adjust scope.

**Known Limitations (Agent Teams is experimental):**
- Session resumption may not work reliably — complete in one sitting if possible
- Task coordination has known edge cases — review outputs for gaps
- Shutdown behavior can be unpredictable — save/commit outputs frequently
- Each teammate reloads project context independently (CLAUDE.md, etc.)

### Sequential Execution

```bash
cd ott-platform-docs

# Foundation (must run first)
claude "Read CLAUDE.md. Execute Agent 1: Create docs/01-project-vision-and-design.md"
# Review output, then:
claude "Read CLAUDE.md and docs/01-project-vision-and-design.md. Execute Agent 2: Create docs/02-platform-architecture.md"
# Review architecture, then:

# PRDs (run each separately — order doesn't matter within this phase)
for agent in 3 4 5 6 7 8 9 10; do
  claude "Read CLAUDE.md, the vision doc, and architecture doc. Execute Agent ${agent} from CLAUDE.md."
done

# Synthesis (run after all PRDs complete)
claude "Read CLAUDE.md and all files in docs/prd/. Execute Agent 11: Generate user stories."
claude "Read CLAUDE.md and all files in docs/. Execute Agent 12: Create cross-cutting docs."
```

### Subagent Execution (Parallel PRDs, No Inter-Agent Communication)

```bash
cd ott-platform-docs

# Foundation (sequential)
claude "Execute Agents 1 and 2 from CLAUDE.md to create vision and architecture docs."

# PRDs (parallel via subagents — Claude spawns 8 subagents internally)
claude "Using subagents, execute Agents 3 through 10 from CLAUDE.md in parallel. \
  Each subagent should read the architecture doc for context and produce its PRD."

# Synthesis (parallel via subagents)
claude "Using subagents, execute Agents 11 and 12 from CLAUDE.md in parallel. \
  Agent 11 reads all PRDs. Agent 12 reads all docs."
```

### Post-Generation Review Checklist

After all agents complete, review the outputs against these criteria:

- [ ] **Consistency:** Do all PRDs use the same service names and terminology?
- [ ] **AI Threading:** Does every PRD include AI-specific features (not just traditional)?
- [ ] **Cross-References:** Do dependency sections accurately reference other PRDs?
- [ ] **Phase Alignment:** Are phase assignments (1–4) realistic and not overloading Phase 1?
- [ ] **Acceptance Criteria:** Are all requirements measurable and testable?
- [ ] **User Stories:** Do stories trace back to specific PRD requirement IDs?
- [ ] **Glossary:** Is terminology consistent across all documents?
- [ ] **Gaps:** Any services or integrations mentioned but not covered?

### Iteration Tips

1. **Fix foundation first:** If architecture doc has issues, fix it before regenerating PRDs
2. **Regenerate selectively:** You can re-run a single agent to regenerate one PRD
3. **Feed corrections forward:** Add review notes to CLAUDE.md so agents incorporate feedback
4. **Use Agent Teams for review:** Spawn review teammates (security reviewer, consistency checker) to audit the complete doc set
5. **Version your outputs:** Commit to git after each phase so you can diff changes

### Customization Points

- **Scale:** Adjust concurrent user targets (currently 50K-500K)
- **Platforms:** Add/remove client platforms from PRD-006
- **AI Ambition:** Adjust phase assignments to match your AI maturity
- **Market:** Add market-specific requirements (regulatory, language, etc.)
- **Monetization:** Adjust SVOD/TVOD/AVOD mix for your business model
- **Existing Systems:** Add migration/integration requirements for legacy platforms
- **Model Selection:** Use `claude --model sonnet` for initial generation, `claude --model opus` for review/refinement

## Active Technologies
- Python 3.12 (backend), TypeScript 5+ (frontend) + FastAPI 0.115+, SQLAlchemy 2.0+ async, React 18, TanStack Query (001-parental-rating-enforcement)
- PostgreSQL 16 + pgvector (001-parental-rating-enforcement)
- TypeScript 5+ / React 18 + shaka-player 4.12+, React, Tailwind CSS 3+ (002-video-player-controls)
- N/A (UI-only, no data changes) (002-video-player-controls)
- Python 3.12 (backend), TypeScript 5+ (frontend) + FastAPI 0.115+, SQLAlchemy 2.0+ async, React 18, TanStack Query, Shaka Player 4+, Tailwind CSS 3+ (004-continue-watching-bookmarks)
- PostgreSQL 16 + pgvector, Redis 7 (optional for caching) (004-continue-watching-bookmarks)
- Python 3.12 + FastAPI 0.115+, SQLAlchemy 2.0+ (async), Pydantic Settings, python-jose, bcryp (005-backend-hardening)
- PostgreSQL 16 + pgvector 0.7+ (existing — no schema changes) (005-backend-hardening)
- Python 3.12 + FastAPI 0.115+, SQLAlchemy 2.0+ (async), Pydantic Settings, python-jose (JWT), bcrypt (PIN hashing) (006-viewing-time-limits)
- PostgreSQL 16 + pgvector 0.7+ (5 new tables, 1 migration) (006-viewing-time-limits)
- Python 3.12 + FastAPI 0.115+, SQLAlchemy 2.0+ (async), bcrypt, python-jose (JWT), Pydantic Settings (009-backend-performance)
- PostgreSQL 16 + pgvector 0.7+ (asyncpg driver) (009-backend-performance)

## Recent Changes
- 001-parental-rating-enforcement: Added Python 3.12 (backend), TypeScript 5+ (frontend) + FastAPI 0.115+, SQLAlchemy 2.0+ async, React 18, TanStack Query
