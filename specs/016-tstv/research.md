# Research: TSTV — Start Over & Catch-Up TV

**Feature Branch**: `001-tstv`
**Phase**: 0 — Research & Architecture Decisions
**Date**: 2026-02-24

---

## Decision 1: HLS Segment Storage & Time Indexing

**Decision**: Encode wall-clock start time directly in segment filenames using `strftime` (`ch1-YYYYMMDDHHmmSS.ts`). Derive time ranges by listing the filesystem and parsing filenames.

**Rationale**: Eliminates the need for a separate `hls_segments` database table and a segment-indexer sidecar process. A directory listing + filename parse is sub-50ms on SSD for the PoC segment volume (~100K files per channel at 7 days of 6-second segments). Segment timestamps are self-describing — no sync between DB and filesystem.

**Alternatives considered**:
- *PostgreSQL segment index table* — adds a write per segment (every 6 seconds × N channels), requires a sidecar process, and creates a dependency that can desync from the actual filesystem. Rejected.
- *Redis time-series index* — fast lookups but adds operational complexity and another data store to keep in sync. Rejected for PoC.

**Format**: `ch1-20260224143000.ts` (channel key + YYYYMMDDHHmmSS)
**Init segment**: `ch1-init.mp4` (one per channel — written once; reused across restarts)

---

## Decision 2: Segment Format — fMP4 vs MPEG-TS

**Decision**: Use fMP4 (`.m4s`) segments with CENC AES-128-CTR encryption (ClearKey for PoC).

**Rationale**: PRD-002 Section 7.6 explicitly specifies fMP4 + CENC as the PoC format, with a documented production migration path to Widevine/FairPlay (same encryption scheme, different license server only). The spec assumption states DRM is already handled by the existing SimLive setup. Shaka Player 4.12 supports ClearKey natively — no player changes needed. Using fMP4 now avoids a format migration when DRM is hardened in production.

**FFmpeg flags**:
- `-hls_segment_type fmp4` — fMP4 output
- `-hls_fmp4_init_filename 'ch1-init.mp4'` — PSSH box + codec config in init segment
- `-encryption_scheme cenc-aes-ctr` — CENC (same scheme as Widevine/FairPlay)
- Segment extension: `.m4s`

**Alternatives considered**:
- *Plain MPEG-TS (`.ts`)* — simpler, no encryption, but requires a format change when DRM is added. Also contradicts the PRD-002 v1.2 architecture. Rejected.
- *fMP4 without encryption* — would require re-encryption later. Rejected.

**Key impact**: The SimLive manager must fetch encryption keys from the Key Management Service (KMS) at startup. The KMS is the backend's `/drm/keys` endpoint.

---

## Decision 3: FFmpeg Process Management — Where It Runs

**Decision**: FFmpeg processes run as subprocesses of the FastAPI backend container (not in a separate playbox container). The backend's `SimLiveManager` service manages per-channel FFmpeg processes and exposes admin control endpoints.

**Rationale**: The spec (FR-050, FR-051) requires start/stop/restart of FFmpeg from the admin panel. If FFmpeg runs in a separate container, controlling it requires a cross-container API or Docker socket access. Running FFmpeg as subprocesses of the backend is architecturally simpler: the backend can directly `subprocess.Popen`, kill PIDs, and read process status. The `hls_data` Docker volume is shared, so segments end up in the same place.

**Alternatives considered**:
- *Separate playbox container with HTTP control API* — adds a new service, increases inter-service communication, complicates startup ordering. Rejected for PoC.
- *Docker socket-based control* — requires mounting `/var/run/docker.sock` into the backend, a significant security concern even for PoC. Rejected.

**Implementation note**: The backend container must have `ffmpeg` installed (add to `Dockerfile`). The `hls_data` volume is mounted read-write on the backend (for FFmpeg to write segments) and read-only on the CDN (nginx for segment serving). Wait — actually the CDN needs RW for cleanup cron. Both get RW access.

---

## Decision 4: TSTV Bookmark Strategy

**Decision**: Extend the existing `Bookmark` table with two new `content_type` values: `'tstv_catchup'` and `'tstv_startover'`. Change the unique constraint from `(profile_id, content_id)` to `(profile_id, content_id, content_type)`. Store `schedule_entry_id` as `content_id`. The bookmark service's `upsert_bookmark` is extended to apply "furthest position wins" semantics for TSTV content types.

**Rationale**: The existing `Bookmark` model has no FK on `content_id` — it's just a UUID. Adding TSTV as content types avoids a new table and reuses the existing Continue Watching API (`/api/v1/viewing/continue-watching`) and bookmark service. The unique constraint change is needed to prevent collisions between VOD title UUIDs and schedule entry UUIDs.

**Furthest-position-wins**: When upserting a TSTV bookmark, the SQL uses `ON CONFLICT DO UPDATE SET position_seconds = GREATEST(EXCLUDED.position_seconds, bookmarks.position_seconds)`. This ensures concurrent writes from two devices always preserve the higher position.

**Alternatives considered**:
- *Separate `tstv_bookmarks` table* — cleaner schema isolation but duplicates bookmark CRUD logic and doesn't appear in the existing Continue Watching rail without changes to that query. Rejected.
- *VOD bookmark table reuse without constraint change* — risks UUID collision between title IDs and schedule_entry IDs (low probability but not zero). Rejected.

---

## Decision 5: Catch-Up Window Enforcement Point

**Decision**: The TSTV manifest endpoint enforces the CUTV window. When a catch-up manifest is requested, the backend checks: `NOW() < schedule_entry.end_time + channel.cutv_window_hours`. If the window has expired, the endpoint returns 403. No filesystem cleanup is required for enforcement — expired segments remain on disk until the infrastructure `catchup_window_hours` cron runs.

**Rationale**: Enforcement at the manifest level means the viewer can never get a playable URL for expired content, regardless of how they obtained the `schedule_entry_id`. This matches the "rights enforced at the playback level" requirement (FR-032). The CDN serves segments directly without rights checks — so the manifest is the enforcement point.

**Alternatives considered**:
- *Client-side enforcement only* — insufficient; clients could construct manifest URLs manually. Rejected.
- *CDN token-based enforcement* — production approach (Common Access Token), out of scope for PoC. Deferred.

---

## Decision 6: Admin SimLive & TSTV Rules — Single New Admin Page

**Decision**: Add a new "Streaming" section to the admin frontend with two panels: (1) SimLive channel control (start/stop/restart/status per channel) and (2) TSTV Rules editor (per-channel toggles and CUTV window dropdown). These are served by new admin endpoints added to the existing `admin.py` router.

**Rationale**: The admin app already has a `ChannelListPage` for channel CRUD. Streaming controls and TSTV rules are operational concerns separate from channel metadata editing. A dedicated `StreamingPage` in the admin app keeps operational controls separate from content management.

---

## Decision 7: Catch-Up Browse as New Dedicated Page

**Decision**: Add a dedicated `CatchUpPage.tsx` in the client frontend (route: `/catchup`). The existing `EpgPage.tsx` is extended to show catch-up badges on past programs, linking to this page. The `HomePage.tsx` gets a "Catch-Up TV" rail showing the top 10 eligible programs across all channels.

**Rationale**: Catch-Up browsing (by channel + date, filterable by genre) is distinct enough from the live EPG to warrant its own page. The EPG page is optimized for the forward-looking schedule; catch-up browse is optimized for the past 7 days. This avoids cluttering the EPG with a backwards-scrolling view.

---

## Decision 8: Schedule Entry Seeding Strategy

**Decision**: Seed schedule entries as repeating program loops aligned to the FFmpeg video loop duration. Each channel's video (10–12 minutes) defines the program duration. Schedule entries are generated for the past 7 days and next 7 days, cycling through a small set of program names. The seed script generates entries programmatically based on the channel's loop duration.

**Rationale**: Since FFmpeg loops the same video indefinitely, programs repeat every video duration. Schedule entries should reflect this so the "elapsed time" displayed in the Start Over prompt is meaningful. A 10-minute video means a new "program" starts every 10 minutes.

**Example** (ch1, Big Buck Bunny, 10-min loop):
- Programs: "Big Buck Bunny", "Nature Documentary", "Short Film" etc. cycling
- Entry duration: 10 minutes
- Start times: every 10 minutes from (NOW - 7 days)

---

## Decision 9: Key Management Service (KMS) for ClearKey

**Decision**: Add a `/drm` router to the backend implementing a minimal ClearKey KMS. The KMS stores AES-128 keys per channel in a `drm_keys` table. SimLive fetches the key at startup via `GET /drm/keys/channel/{channel_key}` and passes it to FFmpeg's `-encryption_key` and `-encryption_kid` flags. The license endpoint `POST /drm/license` validates JWT and entitlement before returning the key in ClearKey JSON format.

**Rationale**: PRD-002 Section 7.8 specifies the full DRM architecture. The spec assumption says DRM is already handled — but since we're choosing fMP4+CENC, the KMS must be built as part of this feature. It is a contained service within the existing backend (two new endpoints) with one new table (`drm_keys`).

**License flow**:
```
Player loads manifest → sees #EXT-X-KEY → EME license request →
POST /drm/license (Bearer JWT) →
Validate JWT + check subscription entitlement →
Return ClearKey JSON { "keys": [{"kty":"oct","kid":"...","k":"..."}] }
```

---

## Resolved: All NEEDS CLARIFICATION Items

All unknowns from the spec are resolved by these decisions:
- ✅ Schedule entry source → Decision 8 (seeded static loops)
- ✅ Bookmark service state → Decision 4 (extend existing table)
- ✅ Resume interaction → clarified in spec (auto-resume + toast)
- ✅ Search scope → deferred (out of scope)
- ✅ Concurrent bookmark conflict → Decision 4 (`GREATEST()` upsert)
- ✅ Segment format → Decision 2 (fMP4 + CENC)
- ✅ FFmpeg management → Decision 3 (backend subprocess)
- ✅ Window enforcement → Decision 5 (manifest endpoint)
