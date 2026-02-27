# Roadmap

This roadmap tracks what's been built and what's planned. Each completed feature corresponds to a numbered branch (`001-*`, `002-*`, ...) in the repo.

## Completed

| # | Feature | Branch | Description |
|---|---------|--------|-------------|
| 001 | Parental Rating Enforcement | `001-parental-rating-enforcement` | Age-based content filtering per profile |
| 001 | Content Analytics Agent | `001-content-analytics-agent` | Natural language analytics queries over viewing data |
| 002 | Video Player Controls | `002-video-player-controls` | Shaka Player integration with playback UI |
| 003 | Semantic Search | `003-semantic-search` | pgvector-powered similarity search over catalog |
| 004 | Continue Watching & Bookmarks | `004-continue-watching-bookmarks` | Resume playback and bookmark management |
| 005 | Backend Hardening | `005-backend-hardening` | Input validation, error handling, config cleanup |
| 006 | Viewing Time Limits | `006-viewing-time-limits` | Per-profile daily viewing limits with PIN override |
| 007 | Security Hardening | `007-security-hardening` | Auth security, rate limiting, header protections |
| 008 | Security Medium Fixes | `008-security-medium-fixes` | Follow-up security improvements |
| 009 | Backend Performance | `009-backend-performance` | Query optimization, connection pooling, async improvements |
| 010 | Production Hardening | `010-production-hardening` | Health checks, graceful shutdown, logging |
| 011 | Recs, Watchlist & Live TV | `011-recs-watchlist-livetv` | AI recommendations, watchlist, live TV player |
| 012 | Entitlements & TVOD | `012-entitlements-tvod` | Subscription tiers, pay-per-view purchases, rate limiting |
| 013 | Admin Analytics UI | `013-admin-analytics-ui` | Admin dashboard with analytics query interface |
| 014 | Nordic Currencies | `014-nordic-currencies` | Multi-currency support (SEK, NOK, DKK, EUR) |
| 015 | Apache License | `015-apache-license` | Open-source licensing |
| 016 | TSTV (Start Over & Catch-Up) | `016-tstv` | **In progress** — restart live programs, 7-day catch-up catalog, ClearKey DRM |

## Up Next

Priority order for upcoming features:

### Phase 1 — Core Platform

| Feature | PRD | Description |
|---------|-----|-------------|
| Cloud PVR | [PRD-003](docs/prd/PRD-003-cloud-pvr.md) | Recording pipeline — schedule, capture, store, and play back recordings |
| AI Personalized Home | [PRD-007](docs/prd/PRD-007-ai-user-experience.md) | AI-driven hero banner and content rails per profile |
| Enhanced Recommendations | [PRD-007](docs/prd/PRD-007-ai-user-experience.md) | Hybrid ensemble — content-based + collaborative + contextual signals |

### Phase 2 — Experience & Intelligence

| Feature | PRD | Description |
|---------|-----|-------------|
| EPG Intelligence | [PRD-005](docs/prd/PRD-005-epg.md) | "Your Schedule" personalized view, smart channel ordering, reminders |
| Conversational Search | [PRD-007](docs/prd/PRD-007-ai-user-experience.md) | Natural language content discovery ("show me 90s comedies") |
| AI Thumbnails & Digests | [PRD-007](docs/prd/PRD-007-ai-user-experience.md) | Personalized artwork and content summaries |
| Live TV Enhancements | [PRD-001](docs/prd/PRD-001-live-tv.md) | Mini EPG overlay, popularity signals, trick-play buffer |

### Phase 3 — Operations & Scale

| Feature | PRD | Description |
|---------|-----|-------------|
| Admin Dashboard v2 | [PRD-010](docs/prd/PRD-010-subscriber-admin-dashboard.md) | Subscriber management, churn dashboards, content scheduling |
| AI Backend Ops | [PRD-008](docs/prd/PRD-008-ai-backend-ops.md) | Anomaly detection, churn prediction, CDN optimization |
| Multi-Client | [PRD-006](docs/prd/PRD-006-multi-client.md) | Native iOS, Android, and Smart TV apps |

## Overall Coverage

Rough estimate of PRD feature coverage by area:

| Area | Built | Key Gaps |
|------|-------|----------|
| VOD / SVOD | ~50% | AI hero banner, personalized rails, post-play recs |
| EPG | ~40% | AI schedule, smart channel ordering, reminders |
| Live TV | ~40% | Trick-play buffer, popularity signals, mini EPG overlay |
| TSTV | ~20% | Start Over and Catch-Up in progress (branch `016-tstv`) |
| AI UX Layer | ~25% | Hybrid ensemble, conversational search, thumbnails |
| Cloud PVR | ~5% | Recording pipeline essentially unstarted |
| AI Backend/Ops | ~20% | Anomaly detection, churn prediction, CDN optimization |
| Multi-Client | ~50% | Web only — native apps not started |

## Design Documents

Full PRDs, user stories, and architecture docs live in [`docs/`](docs/). The doc generation workflow is described in [`docs/agent-prompts.md`](docs/agent-prompts.md).
