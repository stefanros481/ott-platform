# Backend Enhancement Plan

## Context

The platform is feature-complete for a Phase 1 PoC: all 9 features (001–009) are merged to main.
The client is fully wired to 38 endpoints with proper error handling, retries, and offline fallback.
This document inventories every meaningful backend enhancement and groups them into 4 shippable features.

**Key infrastructure already in place:**
- pgvector embeddings (384-dim, SentenceTransformer)
- Redis URL in settings (unused for caching)
- Ratings table (written, never read by recommendations)
- Watchlist table (written, never surfaced in home rails)
- `UserEntitlement`/`ContentPackage`/`PackageContent` models (exist, never enforced)
- `subscription_tier` on User (exists, never checked for content access)
- `hls_live_url` on Channel (exists, EPG click handler is a no-op)
- `ai_description`, `mood_tags`, `theme_tags` on Title (exist, never populated)

---

## All Enhancement Ideas

### Category 1 — Recommendations & Personalization

| ID   | Description | Effort | Impact | Notes |
|------|-------------|--------|--------|-------|
| R-01 | **Fix thumbs-down exclusion** — currently `-1` ratings are included as positive signals in the For You centroid | S | High | Bug fix in `recommendation_service.py` |
| R-02 | **Boost thumbs-up weighting** — weight `+1` rated embeddings 2× in centroid computation | S | High | After R-01 |
| R-03 | **Add Watchlist rail** to `get_home_rails` — "My List" sorted by `added_at DESC` | S | High | Pure service change |
| R-04 | **Post-play next episode awareness** — return the actual next episode first before similarity results | S | High | Seasons/Episodes models already exist |
| R-05 | **Cold-start fallback** — new profiles with zero history get a curated top-rated rail instead of empty For You | S | High | Simple fallback path |
| R-06 | **Trending time-decay** — weight recent bookmarks higher vs all-time count using SQL window or app-side decay | M | Medium | SQL rewrite |
| R-07 | **Diversity injection** — re-rank For You results to avoid 20 titles from the same genre/series | M | Medium | Post-processing step |
| R-08 | **Recommendation explanation strings** — add `reason` field to rail items ("Because you watched X") | M | Medium | Schema + service change |
| R-09 | **Not Interested suppression** — `POST /viewing/not-interested/{title_id}` to permanently hide a title | M | Medium | New table `profile_suppressions` |
| R-10 | **Household recommendations rail** — blend signals from all profiles: "Popular in Your Household" | L | Medium | No new tables needed |
| R-11 | **Personalized featured titles** — rank `is_featured` titles by cosine similarity to profile centroid | M | High | Replaces static `is_featured` filter |

### Category 2 — AI Content Enrichment & Metadata

| ID   | Description | Effort | Impact | Notes |
|------|-------------|--------|--------|-------|
| A-01 | **Batch AI enrichment endpoint** — `POST /admin/titles/enrich` populates `mood_tags`, `theme_tags`, `ai_description` for titles where null | L | High | Calls LLM (Claude via API or heuristic) |
| A-02 | **Auto-enrich on title creation** — hook admin title create to auto-populate AI metadata + embed | M | High | FastAPI `BackgroundTasks`; depends on A-01 |
| A-03 | **Mood/theme browse filter** — `?mood=cozy&theme=crime` params on `GET /catalog/titles` | S | Medium | Depends on A-01 for data |
| A-04 | **Catalog completeness report** — `GET /admin/titles/completeness` listing titles missing poster, synopsis, embedding, mood tags | S | Medium | Helps editorial prioritize |
| A-05 | **Embedding freshness tracking** — add `updated_at` to `content_embeddings`; expose stale count in admin stats | S | Low | Migration + endpoint change |
| A-06 | **IVFFlat index on embeddings** — add pgvector IVFFlat (or HNSW) index on `content_embeddings.embedding` | S | High | Migration only, zero code change — currently full table scan on every recommendation |

### Category 3 — Content Discovery & Search

| ID   | Description | Effort | Impact | Notes |
|------|-------------|--------|--------|-------|
| S-01 | **Semantic search N+1 fix** — semantic search fetches genres per result in a loop; replace with single JOIN | S | Medium | `search_service.py` |
| S-02 | **Paginated semantic search** — add `page`/`page_size` to `GET /catalog/search/semantic` | S | Medium | Currently returns flat list |
| S-03 | **Language filter in catalog** — `?language=en` param on catalog + recommendations | S | Medium | `language` field exists on Title |
| S-04 | **Mood-based "just play something"** — `GET /recommendations/mood?mood=light&duration_max=60` returns one match | M | Medium | Needs A-01 for data |
| S-05 | **New season alert rail** — `GET /recommendations/new-episodes` returns new episodes for watchlisted/bookmarked series | L | High | New table `title_update_events` |
| S-06 | **Browsing history signal** — lightweight `title_views` table written on `GET /catalog/titles/{id}`; powers "Recently Browsed" | M | Medium | New table, background write |
| S-07 | **Content collections** — editorial playlists ("Best of 2025") with admin CRUD + public endpoint | L | Medium | 2 new tables: `collections`, `collection_items` |
| S-08 | **Fuzzy search** — replace `ILIKE` with `pg_trgm` trigram similarity to handle typos | L | Medium | Migration + service rewrite |

### Category 4 — Subscription & Entitlements

**Design principle:** A single title can simultaneously be part of an SVOD package, available to rent, and available to buy. These are not mutually exclusive — a title can offer all three access paths at once (like Amazon Prime: included with Prime, or rent for $3.99, or buy for $9.99).

**Data model approach:**
- **SVOD**: `PackageContent` (already modeled) — title assigned to a subscription package; user access via `UserEntitlement → ContentPackage`
- **Rent / Buy**: New `TitleOffer` table — `(title_id, offer_type ['rent'|'buy'|'free'], price_cents, currency, rental_window_hours)`
- **TVOD purchase**: Creates a `UserEntitlement` with `source_type='tvod'` + `expires_at` (rent) or no expiry (buy)
- **Access check**: Union of SVOD package membership + active TVOD entitlements + free offers

```
Title "Inception":
  PackageContent → "SVOD Basic" package    (SVOD subscribers: free)
  TitleOffer → type=rent, price=399        ($3.99 / 48h for anyone)
  TitleOffer → type=buy,  price=999        ($9.99 permanent for anyone)
```

| ID   | Description | Effort | Impact | Notes |
|------|-------------|--------|--------|-------|
| E-01 | **Package admin management** — CRUD for `ContentPackage` + assign titles to packages | M | High | Prerequisite for SVOD; models already exist |
| E-02 | **`TitleOffer` model + migration** — new table `(title_id, offer_type, price_cents, currency, rental_window_hours)`; allows a title to have rent, buy, and/or SVOD simultaneously | M | High | New table; prerequisite for TVOD |
| E-03 | **Subscription tier enforcement** — check `subscription_tier` against `UserEntitlement`/`PackageContent` in catalog and playback | L | High | Models exist, never enforced |
| E-04 | **`access_options` in catalog responses** — replace a single `access_level` with a list: `[{type: 'svod'}, {type: 'rent', price_cents: 399}, {type: 'buy', price_cents: 999}]` per title | M | High | Frontend needs this to show pricing options, lock icons, upgrade CTA |
| E-05 | **TVOD purchase/rental endpoint** — `POST /catalog/titles/{id}/purchase` with `offer_type=rent\|buy`; creates `UserEntitlement` with correct `expires_at` | L | High | Depends on E-02; `UserEntitlement.source_type='tvod'` already modeled |
| E-06 | **Entitlement expiry enforcement** — check `expires_at` on `UserEntitlement` (field exists, never checked) | S | Medium | Service change only |
| E-07 | **Concurrent stream limit** — enforce per-subscription active session count via `ViewingSession` | M | Medium | Depends on E-03 |
| E-08 | **Admin user tier management** — `PATCH /admin/users/{id}/subscription` | S | Medium | Manual subscription ops |
| E-09 | **Subscription upgrade webhook** — endpoint for payment provider callbacks to update tier + entitlements | L | Medium | Depends on E-01, E-03 |

### Category 5 — User Preferences & Profiles

| ID   | Description | Effort | Impact | Notes |
|------|-------------|--------|--------|-------|
| P-01 | **Explicit genre preferences** — new `profile_preferences` table + GET/PUT endpoints; feed into recommendation centroid | L | High | New table |
| P-02 | **Preferred language** — add `preferred_language` to `Profile` model + migration; filter recommendations | M | Medium | Model + migration |
| P-03 | **Profile viewing stats** — `GET /profiles/{id}/stats` — total hours, genre breakdown, top titles (not just for parents) | M | Medium | No new tables; uses ViewingSession |
| P-04 | **Profile max enforcement** — limit to 5 profiles per user | S | Low | Router check, no schema change |
| P-05 | **Preset avatar gallery** — `GET /catalog/avatars` for platform avatar options | S | Low | Static endpoint |

### Category 6 — EPG & Live TV

| ID   | Description | Effort | Impact | Notes |
|------|-------------|--------|--------|-------|
| L-01 | **EPG click-to-play** — `GET /epg/channels/{id}/playback-token` returns signed URL; fix dead click handler in frontend | M | High | `hls_live_url` already in Channel model |
| L-02 | **Multi-day EPG batch endpoint** — `GET /epg/schedule/multi?channel_ids=...` replaces N×1 per-channel fetches | M | Medium | Frontend currently makes O(N) requests |
| L-03 | **EPG now-playing N+1 fix** — replace per-channel loop in `get_now_playing` with single LATERAL join | M | Medium | `epg_service.py` |
| L-04 | **Channel genre filter** — `?genre=Sports` param on `GET /epg/channels` | S | Medium | Field exists |
| L-05 | **Entitled channels filter** — `?profile_id=` on `/epg/now` to return only entitled channels | S | Medium | Depends on E-02 |
| L-06 | **Channel viewing history** — `channel_views` table + heartbeat-like endpoint for live TV | M | Medium | New table; enables personalized channel order |
| L-07 | **Personalized EPG rail** — `GET /epg/personalized?date=...` ranks programs by profile embedding similarity | L | High | Needs L-06 + embeddings on schedule entries |
| L-08 | **EPG program reminders** — `schedule_reminders` table + POST/DELETE endpoints | L | Medium | Prerequisite for notifications (N-01) |

### Category 7 — Notifications & Reminders

| ID   | Description | Effort | Impact | Notes |
|------|-------------|--------|--------|-------|
| N-01 | **In-app notification store** — `notifications` table + GET/PATCH endpoints | L | High | Prerequisite for all notifications |
| N-02 | **New-content notification** — notify watchlisted profiles when new title/season added | M | High | Depends on N-01 |
| N-03 | **EPG reminder delivery** — generate notification when `remind_at` passes | M | Medium | Depends on N-01 + L-08 |
| N-04 | **Notification preferences** — per-profile opt-out/frequency cap | M | Medium | Depends on N-01 |
| N-05 | **Push token registration** — `POST /devices/push-token` for FCM/APNs tokens | M | Medium | Independent of N-01 |

### Category 8 — Admin & Operations

| ID   | Description | Effort | Impact | Notes |
|------|-------------|--------|--------|-------|
| O-01 | **Content analytics endpoint** — `GET /admin/analytics/content` — watch time, completion rate, rating dist per title | L | High | No new tables |
| O-02 | **User analytics endpoint** — `GET /admin/analytics/users` — DAU/MAU, registrations, tier distribution | M | High | No new tables |
| O-03 | **Bulk title import** — `POST /admin/titles/import` accepting JSON array | L | Medium | New endpoint |
| O-04 | **Admin audit log** — `admin_audit_log` table; auto-populate on admin write operations | L | Medium | New table + middleware |
| O-05 | **Seed data for entitlements** — extend seed scripts with packages, title assignments, user entitlements | S | Medium | Depends on E-01 |

### Category 9 — Performance & Reliability

| ID   | Description | Effort | Impact | Notes |
|------|-------------|--------|--------|-------|
| X-01 | **Redis cache for recommendation rails** — 5-min TTL keyed by `profile_id`; invalidate on bookmark/rating | M | High | Redis URL already in settings |
| X-02 | **Redis cache for EPG schedule** — 5-min TTL keyed by `channel_id + date` | S | High | Eliminates repeated DB reads for static schedule |
| X-03 | **Rate limiting middleware** — `slowapi` or Redis-backed, 100 req/min per IP | M | High | Security + availability gap |
| X-04 | **Statement timeout** — `statement_timeout` on DB session to cap runaway vector queries | S | Medium | `connect_args` in `database.py` |
| X-05 | **Async background embedding generation** — `/admin/embeddings/generate` returns immediately; runs in background | M | Medium | `BackgroundTasks` |

### Category 10 — Developer Experience

| ID   | Description | Effort | Impact | Notes |
|------|-------------|--------|--------|-------|
| D-01 | **Request ID tracing middleware** — inject `X-Request-ID` into all requests + structured logs | S | Medium | `main.py` middleware |
| D-02 | **Structured error envelopes** — standardize all `HTTPException` to `{"error": {"code", "message", "field"}}` | M | Medium | Custom exception handler |
| D-03 | **Integration test suite for recommendations** — pytest-asyncio tests for all 5 rails, cold-start, rating exclusion | L | High | No tests exist today |
| D-04 | **OpenAPI enrichment** — add `summary`, `description`, `examples` to all route decorators | M | Low | DX improvement |

---

## Recommended Feature Groupings

### Feature 010 — Recommendations Quality & Watchlist Rail
**~1 week | No new DB tables | No new endpoints**

Fixes the highest-ROI bugs with zero schema risk. All changes are service-layer only.

- R-01 Fix thumbs-down exclusion *(bug fix)*
- R-02 Boost thumbs-up weighting
- R-03 Add Watchlist rail to home
- R-04 Post-play next episode awareness
- R-05 Cold-start fallback for new profiles
- R-06 Trending time-decay
- R-11 Personalized featured titles (hero banner)
- A-06 IVFFlat index on embeddings *(migration only)*
- S-01 Semantic search genre N+1 fix

---

### Feature 011 — Subscription Tiers, Entitlements & TVOD
**~2 weeks | 1 new table (`title_offers`) | ~8 new endpoints**

Activates the subscription model (90% already modeled) and adds full TVOD rent/buy support. A title can simultaneously be SVOD-included, rentable, and purchasable.

- E-01 Package admin management *(SVOD prerequisite)*
- E-02 `TitleOffer` model + migration *(TVOD prerequisite; new table)*
- E-03 Subscription tier enforcement on catalog
- E-04 `access_options` list in catalog responses *(replaces single access_level field)*
- E-05 TVOD purchase/rental endpoint
- E-06 Entitlement expiry enforcement
- E-07 Concurrent stream limits
- E-08 Admin user tier management
- O-05 Seed data for entitlements and offers
- X-03 Rate limiting middleware *(adjacent, low-risk)*

---

### Feature 012 — EPG Live TV Activation & Performance
**~1.5 weeks | 1 optional new table | ~3 new endpoints**

Unblocks the dead EPG click handler and adds meaningful EPG improvements.

- L-01 EPG click-to-play *(unblocks live TV)*
- L-02 Multi-day EPG batch endpoint *(N×1 → 1 request)*
- L-03 EPG now-playing N+1 fix
- L-04 Channel genre filter
- L-05 Entitled channels filter *(depends on 011)*
- X-02 Redis cache for EPG schedule
- X-01 Redis cache for recommendation rails
- D-01 Request ID tracing middleware

---

### Feature 013 — AI Metadata Enrichment + Notifications Foundation
**~2 weeks | 1 new table | ~4 new endpoints**

Populates the AI fields that embeddings and recommendations depend on, and builds the notification infrastructure.

- A-01 Batch AI enrichment admin endpoint
- A-02 Auto-enrich on title creation
- A-03 Mood/theme browse filter
- R-11 Personalized featured titles (extends enriched metadata)
- S-04 Mood-based "just play something"
- N-01 In-app notification store *(foundation)*
- N-02 New-content notification trigger
- O-01 Content analytics endpoint
- O-02 User analytics endpoint

---

## Suggested Execution Order

```
010 (Recommendations) → 011 (Entitlements) → 012 (EPG/Live TV) → 013 (AI + Notifications)
```

010 has zero dependencies and the highest immediate user-visible impact.
011 is a prerequisite for 012 (entitled channel filtering).
013 last due to external LLM dependency and broadest scope.

---

## Critical Files

| Feature | Key Files |
|---------|-----------|
| 010 | `backend/app/services/recommendation_service.py` |
| 011 | `backend/app/models/entitlement.py` (add `TitleOffer`), `backend/app/routers/admin.py`, new `backend/app/routers/offers.py` |
| 012 | `backend/app/routers/epg.py`, `backend/app/services/epg_service.py`, `frontend-client/src/pages/EpgPage.tsx` (L78–80) |
| 013 | `backend/app/routers/admin.py`, new `backend/app/services/enrichment_service.py`, new `backend/app/routers/notifications.py` |
