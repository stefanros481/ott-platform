# Backend Enhancement Roadmap

## Context

The platform is feature-complete for a Phase 1 PoC: all 9 features (001–009) are merged to main.
The client is fully wired to 38 endpoints with proper error handling, retries, and offline fallback.
This document inventories every meaningful backend enhancement and groups them into 6 shippable features (010–015). Each feature gets a detailed spec via `/speckit.specify` when implementation begins.

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

### Category 11 — Admin Authentication & Separation

**Context:** Currently admins and end users share the same login endpoint, JWT issuer, and password policy. `is_admin` is a single boolean baked into the JWT — if revoked in the DB, access persists until token expiry (up to 60 min). There is no audit trail, no MFA, and no way to restrict admin access by IP or role.

| ID   | Description | Effort | Impact | Notes |
|------|-------------|--------|--------|-------|
| AU-01 | **Separate admin login endpoint** — `POST /api/v1/admin/auth/login`; rejects non-admin users at login time instead of at each route | S | High | Cleaner separation; admin frontend already exists at `frontend-admin/` |
| AU-02 | **Dedicated admin JWT signing** — separate signing key + shorter TTL (15 min vs 60 min); admin tokens cannot be used on user endpoints and vice versa | M | High | Prevents token confusion; limits blast radius of leaked admin token |
| AU-03 | **Real-time admin status check** — verify `is_admin` from DB on every admin request instead of trusting JWT claim alone | S | High | Closes the revocation window; instant admin deactivation |
| AU-04 | **Admin MFA (TOTP)** — optional TOTP enrollment via `POST /admin/auth/mfa/setup`; required on admin login when enrolled | L | High | Industry standard for privileged access; Google Authenticator / Authy compatible |
| AU-05 | **Admin IP allowlist** — configurable CIDR allowlist in settings; reject admin requests from non-allowed IPs before auth check | S | Medium | Defense in depth; optional, disabled by default |
| AU-06 | **Admin audit log** — `admin_audit_log` table auto-populated on every admin write operation (create/update/delete) with user, action, resource, old/new values, timestamp | L | High | Supersedes O-04; regulatory and operational necessity |
| AU-07 | **Admin session management** — separate refresh tokens with shorter lifetime (1 day vs 7 days); `POST /admin/auth/revoke-all` to invalidate all admin sessions | M | Medium | Incident response: one-click lockout of all admin sessions |
| AU-08 | **Role-based admin permissions** — add `admin_role` field (`super_admin`, `catalog_editor`, `user_support`, `viewer`); check role against required permission per endpoint | M | High | Replaces all-or-nothing `is_admin`; prerequisite for multi-team ops |

### Category 12 — Content Operations & Ingest

**Context:** The platform currently has single-item CRUD only. There is no way to bulk-import EPG schedules, VOD metadata, or manage content lifecycle. Every title, episode, and schedule entry must be created one at a time via the admin API. This is a hard blocker for any real content operation.

**EPG Ingest:**

| ID   | Description | Effort | Impact | Notes |
|------|-------------|--------|--------|-------|
| CO-01 | **XMLTV import endpoint** — `POST /admin/epg/import/xmltv` parses standard XMLTV format, maps channels by `channel_number` or `display-name`, creates/updates schedule entries in bulk | L | High | Industry standard; every EPG provider exports XMLTV |
| CO-02 | **Bulk schedule replacement** — `PUT /admin/schedule/bulk` replaces an entire channel's schedule for a date range in one transaction; validates no overlaps | M | High | Needed for daily EPG updates from providers |
| CO-03 | **Schedule conflict detection** — validate overlapping programs on same channel before committing; return detailed error with conflicting entries | S | Medium | Prevents data quality issues from manual or bulk entry |
| CO-04 | **Recurring program templates** — define weekly recurring shows (e.g. "News at 9pm Mon–Fri"); auto-generate schedule entries from template | L | Medium | Reduces manual schedule management for regular programming |

**VOD Metadata Import:**

| ID   | Description | Effort | Impact | Notes |
|------|-------------|--------|--------|-------|
| CO-05 | **Bulk title import (JSON/CSV)** — `POST /admin/titles/import` accepts array of titles with seasons/episodes/cast/genres; upsert logic (create or update by external ID); returns per-item success/error report | L | High | Supersedes O-03; essential for catalog onboarding |
| CO-06 | **External metadata enrichment (TMDB)** — `POST /admin/titles/{id}/enrich/tmdb` fetches poster, synopsis, cast, genres, release year from TMDB API by title search or external ID | M | High | Free API with 95%+ coverage of movies/series |
| CO-07 | **Bulk metadata update** — `PATCH /admin/titles/bulk` updates specific fields across multiple titles (e.g. set `age_rating` for 50 titles at once) | M | Medium | Operational efficiency for editorial corrections |
| CO-08 | **Metadata completeness dashboard** — `GET /admin/titles/completeness` returns titles grouped by missing fields (no poster, no synopsis, no embedding, no mood tags) with counts and IDs | S | Medium | Supersedes A-04; helps editorial prioritize |
| CO-09 | **External ID field on Title** — add `external_id` (nullable, unique) to Title model for TMDB/IMDB/provider IDs; used as upsert key for imports | S | High | Prerequisite for CO-05, CO-06; prevents duplicate imports |

**Content Lifecycle:**

| ID   | Description | Effort | Impact | Notes |
|------|-------------|--------|--------|-------|
| CO-10 | **Content status field** — add `status` enum to Title (`draft`, `published`, `archived`); catalog/search only returns `published` titles; admin sees all | M | High | Currently all titles are implicitly published; no way to stage content |
| CO-11 | **Availability windows** — add `available_from` and `available_until` to Title; catalog automatically filters by current date; admin endpoint to list expiring content | M | High | Licensing compliance; time-limited content rights |
| CO-12 | **Publish scheduling** — set `status=draft` + `available_from` in the future; background task auto-publishes when date arrives | M | Medium | "Content goes live at midnight" use case |

**Asset Validation:**

| ID   | Description | Effort | Impact | Notes |
|------|-------------|--------|--------|-------|
| CO-13 | **HLS manifest health check** — `GET /admin/titles/{id}/validate-stream` fetches the HLS manifest URL, confirms it returns valid M3U8, reports codec/resolution info | M | Medium | Catches broken streams before users see errors |
| CO-14 | **Bulk asset validation** — `POST /admin/titles/validate-assets` checks poster URLs, landscape URLs, and HLS URLs for all titles; returns broken/missing report | M | Medium | Operational health check for asset integrity |

**Data Export:**

| ID   | Description | Effort | Impact | Notes |
|------|-------------|--------|--------|-------|
| CO-15 | **Title catalog export** — `GET /admin/titles/export?format=csv|json` exports full catalog with metadata, genres, cast | M | Medium | BI reporting, backup, migration to other systems |
| CO-16 | **Schedule export** — `GET /admin/schedule/export?format=xmltv|csv&channel_id=...&date_from=...` exports schedule in XMLTV or CSV | M | Medium | Data portability; feed downstream systems |
| CO-17 | **User export** — `GET /admin/users/export?format=csv` exports user list with subscription tiers, profile counts, signup dates (no passwords/hashes) | S | Medium | GDPR compliance, analytics, CRM integration |

### Category 13 — User Administration

**Context:** Admin user management is currently read-only (list users). There is no way to suspend accounts, manage subscriptions, reset PINs, or view user activity.

| ID   | Description | Effort | Impact | Notes |
|------|-------------|--------|--------|-------|
| UA-01 | **User detail endpoint** — `GET /admin/users/{id}` returns full user with profiles, subscription history, entitlements, recent viewing activity | S | High | Basic requirement for any support team |
| UA-02 | **User suspend/activate** — `PATCH /admin/users/{id}/status` sets `is_active=false/true`; suspended users' tokens are immediately invalidated | M | High | Account abuse, payment fraud, GDPR right-to-restrict |
| UA-03 | **Manual entitlement grant** — `POST /admin/users/{id}/entitlements` grants a package or TVOD entitlement with optional expiry (promo, support resolution, press account) | M | High | Depends on E-01; essential for customer support ops |
| UA-04 | **Admin PIN reset** — `DELETE /admin/users/{id}/pin` resets a user's parental control PIN and clears lockout; user must re-create via normal flow | S | Medium | Support scenario: user forgot PIN, locked out |
| UA-05 | **Force logout** — `DELETE /admin/users/{id}/sessions` revokes all refresh tokens for a user, forcing re-login on all devices | S | Medium | Security incident response; stolen device |
| UA-06 | **User search** — `GET /admin/users?email=...&tier=...&created_after=...` with filtering by email, subscription tier, admin status, active status, signup date range | M | Medium | Currently no search/filter on user list |

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

### Feature 014 — Admin Authentication & Separation
**~1.5 weeks | 1 new table (`admin_audit_log`) | ~5 new endpoints**

Fully separates admin auth from end-user auth. Admins get their own login, shorter-lived tokens, optional MFA, audit logging, and role-based permissions.

- AU-01 Separate admin login endpoint
- AU-02 Dedicated admin JWT signing *(separate key + shorter TTL)*
- AU-03 Real-time admin status check *(close revocation window)*
- AU-04 Admin MFA (TOTP) *(optional, high-value)*
- AU-05 Admin IP allowlist *(optional, defense in depth)*
- AU-06 Admin audit log *(supersedes O-04)*
- AU-07 Admin session management *(separate refresh tokens, revoke-all)*
- AU-08 Role-based admin permissions *(replaces boolean `is_admin`)*

### Feature 015 — Content Operations & User Administration
**~2.5 weeks | 1 migration (status + external_id + availability fields) | ~15 new endpoints**

The operational backbone: bulk import, XMLTV ingest, content lifecycle, asset validation, data export, and user management. Without this, every content operation is manual one-at-a-time work.

**Phase A — Foundation (do first):**
- CO-09 External ID field on Title *(prerequisite for imports)*
- CO-10 Content status field *(draft/published/archived)*
- CO-11 Availability windows *(available_from/available_until)*
- UA-01 User detail endpoint
- UA-02 User suspend/activate
- UA-06 User search with filters

**Phase B — Import/Export:**
- CO-01 XMLTV import endpoint *(EPG ingest)*
- CO-02 Bulk schedule replacement
- CO-05 Bulk title import (JSON/CSV)
- CO-06 External metadata enrichment (TMDB)
- CO-15 Title catalog export
- CO-16 Schedule export (XMLTV/CSV)
- CO-17 User export

**Phase C — Operational Quality:**
- CO-03 Schedule conflict detection
- CO-07 Bulk metadata update
- CO-08 Metadata completeness dashboard
- CO-13 HLS manifest health check
- CO-14 Bulk asset validation
- CO-12 Publish scheduling
- UA-03 Manual entitlement grant *(depends on 011)*
- UA-04 Admin PIN reset
- UA-05 Force logout

---

## Suggested Execution Order

```
010 (Recommendations) → 011 (Entitlements) → 015 (Content Ops) → 014 (Admin Auth) → 012 (EPG/Live TV) → 013 (AI + Notifications)
```

010 has zero dependencies and the highest immediate user-visible impact.
011 is a prerequisite for 012 (entitled channel filtering) and 015 (entitlement grants).
015 comes next because content operations are a hard prerequisite for running the platform — you cannot manage a catalog or EPG schedule without bulk import and lifecycle tooling.
014 slots after 015 because audit logging and role checks immediately cover the new content ops endpoints.
012 depends on 011 (entitled channels).
013 last due to external LLM dependency and broadest scope.

---

## Critical Files

| Feature | Key Files |
|---------|-----------|
| 010 | `backend/app/services/recommendation_service.py` |
| 011 | `backend/app/models/entitlement.py` (add `TitleOffer`), `backend/app/routers/admin.py`, new `backend/app/routers/offers.py` |
| 015 | `backend/app/models/catalog.py` (add `status`, `external_id`, `available_from/until`), `backend/app/routers/admin.py` (bulk endpoints), new `backend/app/services/import_service.py`, new `backend/app/services/xmltv_parser.py` |
| 014 | `backend/app/dependencies.py`, `backend/app/services/auth_service.py`, `backend/app/routers/auth.py`, new `backend/app/routers/admin_auth.py`, `frontend-admin/src/context/AuthContext.tsx` |
| 012 | `backend/app/routers/epg.py`, `backend/app/services/epg_service.py`, `frontend-client/src/pages/EpgPage.tsx` (L78–80) |
| 013 | `backend/app/routers/admin.py`, new `backend/app/services/enrichment_service.py`, new `backend/app/routers/notifications.py` |
