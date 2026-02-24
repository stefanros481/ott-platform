# User Stories: MultiDRM Content Protection & Entitlement Management (PRD-009)

**Source PRD:** PRD-009-multi-drm.md (PRD-POC-003)
**Generated:** 2026-02-24
**Total Stories:** 34

---

## Epic 1: Content Encryption

### US-DRM-001: Encrypted Segment Delivery

**As a** platform operator
**I want to** serve all HLS fMP4 segments encrypted with CENC AES-128-CTR
**So that** content cannot be played back by anyone who fetches segments directly from the CDN

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** FR-1, FR-4

**Acceptance Criteria:**
- [ ] Given SimLive is running, when a segment is written to the shared CDN volume, then the segment file is CENC-encrypted and is not playable by `ffplay` without a key
- [ ] Given a direct CDN URL for a `.m4s` segment, when fetched without a license, then the bytes are indistinguishable from random data and no video/audio is recoverable
- [ ] Given any of the 5 channels, when segments are inspected, then all use AES-128-CTR (CTR mode, not CBC)
- [ ] Given the init segment (`.mp4`), when parsed, then a PSSH box is present containing the KID for that channel

**AI Component:** No

**Dependencies:** SimLive infrastructure, FFmpeg CENC encryption flags, CDN shared volume

**Technical Notes:**
- FFmpeg flags required: `-hls_segment_type fmp4 -encryption_scheme cenc-aes-ctr -encryption_key <hex> -encryption_kid <hex>`
- Segment format changes from `.ts` to `.m4s`; init segment is a separate `.mp4` file

---

### US-DRM-002: fMP4 Segment Format Migration

**As a** platform operator
**I want to** migrate SimLive output from MPEG-TS to fMP4 segments
**So that** CENC encryption (which requires fMP4) is possible and HLS manifests include `#EXT-X-MAP`

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** FR-1, Section 9.1

**Acceptance Criteria:**
- [ ] Given SimLive is running, when it produces HLS output, then segments use the `.m4s` extension and an init segment uses the `.mp4` extension
- [ ] Given a generated manifest, when inspected, then an `#EXT-X-MAP` tag points to the correct init segment
- [ ] Given the CDN nginx config, when serving content, then `.m4s` and `.mp4` extensions are included in cache rules
- [ ] Given the cleanup cron job, when it runs, then it removes `.m4s` files (not `.ts` files)
- [ ] Given the TSTV manifest generator, when producing catch-up manifests, then it references `.m4s` segments and includes `#EXT-X-MAP`

**AI Component:** No

**Dependencies:** SimLive FFmpeg config, CDN nginx config, TSTV manifest generator

**Technical Notes:**
- TSTV manifest generator must be updated alongside SimLive — both must reference `.m4s` extension consistently

---

### US-DRM-003: Per-Channel Encryption Key Assignment

**As a** platform operator
**I want to** assign a dedicated encryption key per channel
**So that** compromising one channel's key does not expose other channels

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** FR-2, FR-3

**Acceptance Criteria:**
- [ ] Given 5 channels, when DRM keys are seeded, then each channel has a distinct KID and key value
- [ ] Given an HLS manifest for any channel, when inspected, then the `#EXT-X-KEY` tag includes the license server URL and the correct KEYFORMAT for ClearKey
- [ ] Given the init segment for channel A, when the KID is extracted, then it does not match the KID in channel B's init segment
- [ ] Given the manifest `#EXT-X-KEY`, when the KEYFORMAT attribute is checked, then it is `com.apple.streamingkeydelivery` or the W3C ClearKey KEYFORMAT as appropriate for hls.js EME

**AI Component:** No

**Dependencies:** Key management service (US-DRM-007), SimLive startup flow

---

## Epic 2: Key Management Service

### US-DRM-004: Secure Key Generation

**As a** platform operator
**I want to** generate cryptographically random 128-bit AES keys via the key management service
**So that** encryption keys meet security requirements and cannot be predicted

**Priority:** P0
**Phase:** 1
**Story Points:** S
**PRD Reference:** FR-5, FR-6

**Acceptance Criteria:**
- [ ] Given a key generation request, when the service creates a key, then it uses `os.urandom(16)` (or equivalent CSPRNG) to produce 128 bits of entropy
- [ ] Given a new key, when stored in `drm_keys`, then `key_id` is a UUID and `key_value` is stored as `BYTEA`
- [ ] Given any API response other than the license endpoint, when inspected for key values, then no `key_value` bytes appear in the response body or logs

**AI Component:** No

**Dependencies:** `drm_keys` database table (US-DRM-006)

**Technical Notes:**
- Key value must never appear in structured logs, error messages, or admin UI responses

---

### US-DRM-005: SimLive Key Provisioning at Startup

**As a** SimLive service
**I want to** fetch the active encryption key for each channel at container startup
**So that** FFmpeg is launched with the correct encryption parameters without manual intervention

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** FR-8, FR-9, NFR-6

**Acceptance Criteria:**
- [ ] Given SimLive starts, when it initializes, then it calls `GET /drm/keys/channel/{id}/active` for each channel before launching FFmpeg
- [ ] Given the key provisioning endpoint responds, when SimLive receives the key, then it passes `key_id_hex` and `key_hex` to the corresponding FFmpeg process
- [ ] Given the key management service is temporarily unavailable, when SimLive retries, then it uses exponential backoff and does not start FFmpeg unencrypted
- [ ] Given all key fetches succeed, when SimLive launches FFmpeg, then content is encrypted from the first segment

**AI Component:** No

**Dependencies:** Key management service, internal Docker network (endpoint not exposed externally)

**Technical Notes:**
- Provisioning endpoint must be network-restricted to Docker internal network only (NFR-4)
- Retry strategy: exponential backoff with jitter, max 5 retries before fatal exit

---

### US-DRM-006: `drm_keys` Database Migration

**As a** platform engineer
**I want to** create the `drm_keys` table via an Alembic migration
**So that** encryption keys, their KIDs, channel associations, and rotation history are persisted

**Priority:** P0
**Phase:** 1
**Story Points:** S
**PRD Reference:** Section 8.1

**Acceptance Criteria:**
- [ ] Given the migration is run, when `drm_keys` is inspected, then it has columns: `id`, `key_id` (UUID, unique), `key_value` (BYTEA), `channel_id` (FK), `content_id`, `active` (bool), `created_at`, `rotated_at`, `expires_at`
- [ ] Given a channel_id FK, when an invalid channel_id is inserted, then a foreign key violation is raised
- [ ] Given the migration, when run on a clean database, then it applies without error and is reversible with `alembic downgrade`

**AI Component:** No

**Dependencies:** Existing `channels` table, Alembic migration tooling

---

### US-DRM-007: Key Rotation per Channel

**As a** platform admin
**I want to** rotate the encryption key for a specific channel
**So that** new live content uses a new key while catch-up content encrypted with the old key remains playable

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** FR-7, NFR-9

**Acceptance Criteria:**
- [ ] Given a rotation is triggered for channel X, when the rotation completes, then the old key has `active = false` and `rotated_at` set, and a new key is active for channel X
- [ ] Given the new key is active, when SimLive restarts for channel X, then it fetches the new key and FFmpeg uses it for all new segments
- [ ] Given content encrypted with the old KID, when a license request arrives for that KID, then the license server still returns the old key (it is retained in `drm_keys`)
- [ ] Given key rotation, when measured end-to-end, then new live content uses the new key within 5 seconds (NFR-2)
- [ ] Given rotation of channel X, when channel Y is inspected, then channel Y's encryption is unaffected
- [ ] Rotation event is logged with: `channel_id`, `old_kid`, `new_kid`, `timestamp` (NFR-9)

**AI Component:** No

**Dependencies:** Key management service, SimLive key-rotation signal handler, admin dashboard trigger (US-DRM-026)

---

## Epic 3: ClearKey License Server

### US-DRM-008: ClearKey License Protocol Implementation

**As a** ClearKey-compatible player (hls.js EME)
**I want to** send a license request with `kids` and receive decryption keys in the W3C ClearKey JSON format
**So that** the player can decrypt and play back encrypted content

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** FR-10, FR-13

**Acceptance Criteria:**
- [ ] Given an authenticated license request with a valid `kids` array (base64url-encoded KIDs), when the user is entitled, then the response is HTTP 200 with `{"keys": [{"kty": "oct", "k": "<base64url key>", "kid": "<base64url kid>"}], "type": "temporary"}`
- [ ] Given the response, when measured, then it completes within 100ms (p99) under PoC load (NFR-1)
- [ ] Given an unknown KID in the request, when the user is entitled for the channel, then the response includes only the KIDs the server can resolve; unknown KIDs are omitted
- [ ] Given multiple KIDs in a single request, when all are for entitled channels, then all are returned in one response

**AI Component:** No

**Dependencies:** `drm_keys` table, entitlement engine (US-DRM-011), JWT auth middleware

---

### US-DRM-009: License Request Authentication

**As a** license server
**I want to** authenticate every license request using the user's JWT bearer token
**So that** only logged-in users can receive decryption keys

**Priority:** P0
**Phase:** 1
**Story Points:** S
**PRD Reference:** FR-11, NFR-5

**Acceptance Criteria:**
- [ ] Given a license request with a valid JWT, when processed, then authentication passes and entitlement check proceeds
- [ ] Given a license request with an expired JWT, when processed, then the response is HTTP 401 before any entitlement check occurs
- [ ] Given a license request with a malformed or missing JWT, when processed, then the response is HTTP 401
- [ ] Given authentication, when the existing auth middleware is reused, then no new authentication logic is written for the license endpoint

**AI Component:** No

**Dependencies:** Existing JWT auth middleware (backend)

---

### US-DRM-010: License Denial with Upsell Payload

**As a** viewer who is not entitled to a channel
**I want to** receive a structured denial response when my license request fails
**So that** the player can display a meaningful upsell prompt instead of a generic error

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** FR-14

**Acceptance Criteria:**
- [ ] Given an authenticated request for a KID the user is not entitled to, when the license server responds, then it returns HTTP 403 with `{"error": "not_entitled", "channel_id": <id>, "products": [{"id": <id>, "name": "<name>", "price_label": "<price>"}]}`
- [ ] Given the 403 response, when the `products` array is checked, then it contains at least one product that would grant access to the requested channel
- [ ] Given a user with no subscriptions requesting any premium channel, when denied, then all relevant products appear in the response
- [ ] Given an invalid or unknown KID (no channel association), when the request is made, then HTTP 403 is returned with `{"error": "unknown_content"}`

**AI Component:** No

**Dependencies:** Entitlement engine, `product_entitlements` table, `products` table

---

## Epic 4: Entitlement Model

### US-DRM-011: Entitlement Resolution at License Time

**As a** license server
**I want to** verify a user's subscription entitlements before returning any decryption key
**So that** only authorized users can decrypt and play content

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** FR-12, FR-16, FR-18

**Acceptance Criteria:**
- [ ] Given user Alice (Basic + Sports) requests a key for ch4 (Eurosport), when the entitlement check runs, then it returns entitled (Sports Package covers ch4)
- [ ] Given user Diana (Basic only) requests a key for ch2 (TV 2), when the entitlement check runs, then it returns not-entitled
- [ ] Given a user has overlapping subscriptions (e.g., Basic grants ch1, All Channels also grants ch1), when the entitlement check runs, then the union of entitlements is used (ch1 is accessible)
- [ ] Given an admin adds Sports Package to Diana's account, when Diana makes the next license request for ch4, then entitlement is granted without requiring re-login
- [ ] Given the entitlement query, when measured, then it contributes < 20ms to the total license response time (target NFR-1)

**AI Component:** No

**Dependencies:** `user_subscriptions`, `product_entitlements`, `products` tables (from TSTV plan)

---

### US-DRM-012: Product and Subscription Seed Data

**As a** QA engineer or demo presenter
**I want to** have seed data with four test users, four products, and correct entitlement mappings
**So that** all entitlement scenarios (full access, partial access, no access) can be demonstrated immediately

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** Section 8.3

**Acceptance Criteria:**
- [ ] Given the seed migration runs, when the `products` table is queried, then Basic, Sports Package, Entertainment Package, and All Channels products exist with correct `type`, `price_label`, and channel entitlements
- [ ] Given the seed data, when Charlie attempts to play any of ch1–ch5, then all license requests succeed
- [ ] Given the seed data, when Alice attempts ch4, then the license succeeds; when Alice attempts ch2 or ch3, then the license is denied with a suggestion for Entertainment Package
- [ ] Given the seed data, when Bob attempts ch4, then the license is denied with a suggestion for Sports Package
- [ ] Given the seed data, when Diana attempts ch2, ch3, or ch4, then the license is denied with appropriate product suggestions

**AI Component:** No

**Dependencies:** `products`, `product_entitlements`, `user_subscriptions` tables, test users (Charlie, Alice, Bob, Diana)

---

### US-DRM-013: Subscription Acquisition Types

**As a** product manager
**I want to** support all six product/acquisition types in the entitlement model
**So that** base subscriptions, channel packages, à la carte channels, SVOD, TVOD rent, and TVOD buy can all be demonstrated

**Priority:** P1
**Phase:** 1
**Story Points:** M
**PRD Reference:** FR-15, FR-17

**Acceptance Criteria:**
- [ ] Given a product of type `base`, when a user has an active subscription, then entitled channels are accessible for the subscription duration
- [ ] Given a product of type `channel_package`, when a user subscribes, then all channels in the package become accessible on the next license request
- [ ] Given a product of type `tvod_rent` with `rental_hours = 48`, when a user plays the content for the first time (`first_played_at` is set), then the rental expires 48 hours after first play
- [ ] Given a TVOD rental that has never been played, when checked for expiry, then it does not expire (countdown starts on first play only)
- [ ] Given a product of type `tvod_buy`, when a user purchases it, then the content is accessible for the account lifetime
- [ ] Given all 6 product types, when seeded in the demo environment, then at least one product of each type exists

**AI Component:** No

**Dependencies:** Entitlement model, `products` schema with `product_type` and `rental_hours` fields

---

## Epic 5: Entitlement Enforcement Points

### US-DRM-014: TSTV Manifest Entitlement Check

**As a** viewer without a subscription
**I want to** receive an early rejection when requesting a TSTV manifest I'm not entitled to
**So that** the player does not waste time loading before hitting a license wall

**Priority:** P1
**Phase:** 1
**Story Points:** M
**PRD Reference:** FR-19

**Acceptance Criteria:**
- [ ] Given Diana requests a TSTV manifest for ch2 (not entitled), when the API responds, then HTTP 403 is returned with the same structured denial payload as the license endpoint
- [ ] Given Alice requests a TSTV manifest for ch4 (entitled), when the API responds, then HTTP 200 is returned with the manifest
- [ ] Given an unauthenticated TSTV manifest request, when the API responds, then HTTP 401 is returned (auth check precedes entitlement check)
- [ ] Given the TSTV entitlement check, when implemented, then it reuses the same entitlement resolution logic as the license server (no duplicate code)

**AI Component:** No

**Dependencies:** TSTV manifest generator, entitlement engine, JWT auth middleware

---

### US-DRM-015: Channel List Locked State

**As a** viewer browsing the channel list
**I want to** see locked channels clearly marked when I don't have the required subscription
**So that** I understand which channels require an upgrade before attempting to play

**Priority:** P1
**Phase:** 1
**Story Points:** S
**PRD Reference:** FR-19

**Acceptance Criteria:**
- [ ] Given the channel list API response for Diana, when channels are returned, then ch2, ch3, and ch4 include `"locked": true` and a `required_product` hint
- [ ] Given a locked channel in the UI, when rendered, then a lock icon or visual indicator is displayed
- [ ] Given Charlie's channel list, when returned, then no channels are marked locked
- [ ] Given the channel list API, when measured, then it returns within 200ms including the entitlement check

**AI Component:** No

**Dependencies:** Channel list API, entitlement engine, frontend channel list component

---

## Epic 6: Player Integration

### US-DRM-016: hls.js EME ClearKey Configuration

**As a** viewer
**I want to** have hls.js automatically negotiate ClearKey DRM and request licenses on my behalf
**So that** encrypted streams play without any manual intervention

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** FR-20, FR-21

**Acceptance Criteria:**
- [ ] Given an encrypted HLS stream, when hls.js initializes, then it detects the `#EXT-X-KEY` tag with ClearKey KEYFORMAT and initiates EME key session setup
- [ ] Given EME key session setup, when the license request is sent, then it includes the user's JWT as a `Bearer` token in the `Authorization` header
- [ ] Given a successful license response, when playback starts, then video renders within the normal playback start time target with no visible interruption
- [ ] Given hls.js version, when checked, then it is 1.4 or higher (minimum for ClearKey EME support)

**AI Component:** No

**Dependencies:** hls.js ≥ 1.4, license endpoint (US-DRM-008), user auth token available in player context

---

### US-DRM-017: Upsell Prompt on License Denial

**As a** viewer who attempts to play a channel I'm not subscribed to
**I want to** see a contextual upsell prompt with the product required to unlock the content
**So that** I understand my options and can upgrade my subscription

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** FR-22, FR-23

**Acceptance Criteria:**
- [ ] Given the player receives a 403 response from the license server, when the error is intercepted, then playback stops and the upsell modal is displayed within 500ms
- [ ] Given the upsell modal, when displayed, then it shows: the channel name that was denied, the product(s) that would grant access, and the price label for each product
- [ ] Given the upsell modal, when a "Subscribe" CTA is tapped, then the user is navigated to the subscription/upgrade flow
- [ ] Given the upsell modal, when closed without acting, then the user is returned to the previous screen without an error state
- [ ] Given any denial scenario (live, catch-up, start-over), when the upsell modal triggers, then the same reusable component is used across all surfaces

**AI Component:** No

**Dependencies:** License denial payload (US-DRM-010), upsell modal component, subscription/upgrade navigation

---

## Epic 7: Admin Dashboard

### US-DRM-018: DRM Key Management Panel

**As a** platform admin
**I want to** view all encryption keys and their status in the admin dashboard
**So that** I can audit which channels have active keys and identify rotation history

**Priority:** P1
**Phase:** 1
**Story Points:** M
**PRD Reference:** FR-24

**Acceptance Criteria:**
- [ ] Given the admin navigates to the DRM management panel, when the page loads, then all channels are listed with their KID (truncated UUID), active/rotated status, and creation date
- [ ] Given a rotated key, when displayed, then it shows `rotated_at` timestamp alongside the replacement key
- [ ] Given any row in the key list, when inspected, then the `key_value` (secret bytes) is never displayed — only the KID is shown
- [ ] Given the key list, when it loads, then it appears within 2 seconds

**AI Component:** No

**Dependencies:** Key management service API, admin dashboard frontend

**Technical Notes:**
- Key values must never appear in the admin UI (NFR-3)

---

### US-DRM-019: Key Rotation via Admin Dashboard

**As a** platform admin
**I want to** trigger key rotation for a specific channel from the admin dashboard
**So that** I can demonstrate key rotation and verify that catch-up content still plays after rotation

**Priority:** P1
**Phase:** 1
**Story Points:** M
**PRD Reference:** FR-24, FR-7

**Acceptance Criteria:**
- [ ] Given the DRM key management panel, when the admin clicks "Rotate Key" for a channel, then a confirmation dialog appears
- [ ] Given confirmation, when rotation proceeds, then the new key appears as active and the old key shows `rotated_at` within 5 seconds
- [ ] Given rotation completes, when a live viewer on that channel is observed, then they experience a brief rebuffer as SimLive restarts with the new key
- [ ] Given a catch-up viewer watching content from before the rotation, when they request a license for the old KID, then it is still granted (old key retained)

**AI Component:** No

**Dependencies:** Key rotation API endpoint, SimLive restart signal, admin dashboard key management panel (US-DRM-018)

---

### US-DRM-020: Subscription Management Panel

**As a** platform admin
**I want to** view all users with their active subscriptions and effective channel entitlements in the admin dashboard
**So that** I can add or remove subscriptions per user to demonstrate entitlement changes

**Priority:** P1
**Phase:** 1
**Story Points:** M
**PRD Reference:** FR-25

**Acceptance Criteria:**
- [ ] Given the admin navigates to the subscription management panel, when the page loads, then all users are listed with their subscriptions and the resulting effective channel access (e.g., "ch1, ch4, ch5")
- [ ] Given the admin adds Sports Package to Diana, when the change is saved, then Diana's entitlement row updates immediately in the UI
- [ ] Given the entitlement change, when Diana makes the next license request for ch4, then it succeeds without re-login (FR-18)
- [ ] Given the admin removes a subscription, when saved, then the user loses access on their next license request

**AI Component:** No

**Dependencies:** Subscription management API, entitlement engine, admin dashboard frontend

---

### US-DRM-021: Product Management Panel

**As a** platform admin
**I want to** view and edit all products (type, pricing, channel entitlements) in the admin dashboard
**So that** I can demonstrate the product model and make adjustments for demo scenarios

**Priority:** P1
**Phase:** 1
**Story Points:** M
**PRD Reference:** FR-26

**Acceptance Criteria:**
- [ ] Given the admin navigates to the product management panel, when the page loads, then all products are listed with type, price label, and entitled channels/content
- [ ] Given the admin edits a product's channel entitlements, when saved, then the change is reflected in subsequent entitlement checks
- [ ] Given a product of type `tvod_rent`, when displayed, then the `rental_hours` field is shown and editable

**AI Component:** No

**Dependencies:** Products API, product_entitlements table, admin dashboard frontend

---

### US-DRM-022: License Request Log

**As a** platform admin or developer
**I want to** view a log of recent license requests with their outcomes in the admin dashboard
**So that** I can debug entitlement issues and demonstrate the DRM flow during a PoC presentation

**Priority:** P1
**Phase:** 1
**Story Points:** M
**PRD Reference:** FR-27, NFR-8

**Acceptance Criteria:**
- [ ] Given the admin navigates to the license request log, when the page loads, then recent requests are shown with: timestamp, username, channel name, KID (truncated), and outcome (granted/denied)
- [ ] Given a denied request, when displayed, then the denial reason is shown (e.g., `not_entitled`)
- [ ] Given the log, when a new license request occurs, then it appears in the log within 5 seconds (near-real-time)
- [ ] Given the log, when rendered, then no key values appear — only KIDs are shown
- [ ] License request log entries are written with structured fields: `user_id`, `channel_id`, `kid`, `outcome`, `denial_reason`, `latency_ms` (NFR-8)

**AI Component:** No

**Dependencies:** License server structured logging, admin dashboard log view component

---

## Epic 8: Non-Functional & Observability

### US-DRM-023: License Latency Under 100ms

**As a** viewer starting playback
**I want to** receive a license response within 100ms
**So that** DRM key acquisition does not meaningfully delay time-to-first-frame

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** NFR-1

**Acceptance Criteria:**
- [ ] Given load testing with PoC-level concurrent users (up to 50), when license requests are sent, then p99 response time is ≤ 100ms
- [ ] Given the license endpoint, when a request arrives, then the entitlement query uses indexed lookups (no full-table scans on `user_subscriptions` or `product_entitlements`)
- [ ] Given the latency breakdown, when instrumented, then the entitlement DB query contributes < 20ms

**AI Component:** No

**Dependencies:** Database indexes on `user_subscriptions.user_id`, `product_entitlements.product_id`, structured latency logging

---

### US-DRM-024: Key Provisioning Endpoint Network Restriction

**As a** security engineer
**I want to** ensure the SimLive key provisioning endpoint is only reachable within the Docker internal network
**So that** no external client can request raw encryption keys

**Priority:** P0
**Phase:** 1
**Story Points:** S
**PRD Reference:** NFR-4, FR-9

**Acceptance Criteria:**
- [ ] Given a request to the provisioning endpoint from a browser or external HTTP client, when attempted, then the connection is refused or returns a network error (not HTTP 403 — the port must not be reachable)
- [ ] Given a SimLive container on the Docker internal network, when it calls the provisioning endpoint, then it receives the key successfully
- [ ] Given the Docker Compose configuration, when inspected, then the provisioning port is not listed under `ports` (not published to the host)

**AI Component:** No

**Dependencies:** Docker Compose network configuration, backend service routing

---

### US-DRM-025: Encrypted Stream Verification Test

**As a** platform engineer
**I want to** run a post-deployment smoke test that verifies segments are encrypted and playable only with a valid key
**So that** I can confirm the full encryption pipeline is working correctly

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** Section 12, Task 5

**Acceptance Criteria:**
- [ ] Given a running SimLive instance, when a `.m4s` segment is fetched via curl and piped to ffplay without a key, then ffplay reports an error or produces no playable output
- [ ] Given the same segment URL, when ffplay is provided the correct key and KID, then it plays back correctly
- [ ] Given the test script, when run against all 5 channels, then all pass the encryption check
- [ ] Test script is committed to the repository and documented in the README

**AI Component:** No

**Dependencies:** Running SimLive, CDN, key management service

---

### US-DRM-026: Structured License Outcome Logging

**As a** platform operator
**I want to** have all license request outcomes written to structured logs
**So that** I can monitor entitlement patterns, debug denials, and audit key usage

**Priority:** P1
**Phase:** 1
**Story Points:** S
**PRD Reference:** NFR-8

**Acceptance Criteria:**
- [ ] Given a granted license request, when the response is sent, then a log entry is written with: `user_id`, `channel_id`, `kid`, `outcome=granted`, `latency_ms`
- [ ] Given a denied license request, when the response is sent, then a log entry is written with: `user_id`, `channel_id`, `kid`, `outcome=denied`, `denial_reason`, `latency_ms`
- [ ] Given a 401 (unauthenticated) request, when logged, then `user_id` is null and `outcome=unauthenticated`
- [ ] Given the log format, when inspected, then no `key_value` bytes appear in any log field

**AI Component:** No

**Dependencies:** License endpoint, structured logging middleware

---

## Epic 9: TVOD Demonstration

### US-DRM-027: TVOD Rental Countdown from First Play

**As a** viewer with a TVOD rental
**I want to** have my rental countdown begin only when I first play the content
**So that** I don't lose rental time before I've had a chance to watch

**Priority:** P1
**Phase:** 1
**Story Points:** M
**PRD Reference:** FR-17

**Acceptance Criteria:**
- [ ] Given a user with a TVOD rental that has never been played, when the license is checked before first play, then it is not expired regardless of purchase date
- [ ] Given a user who plays TVOD content for the first time, when the first playback event occurs, then `first_played_at` is set in `user_subscriptions`
- [ ] Given `first_played_at` is set and `rental_hours = 48`, when 49 hours have passed since first play, then the next license request is denied with `{"error": "rental_expired"}`
- [ ] Given the "Movie Night" TVOD seed data, when used in a demo, then the rental countdown behavior is demonstrable end-to-end

**AI Component:** No

**Dependencies:** `user_subscriptions` table with `first_played_at` field, entitlement engine rental logic, TVOD seed data

---

### US-DRM-028: TVOD Seed Data for Demo

**As a** demo presenter
**I want to** have one TVOD rental in the seed data assigned to Alice
**So that** the time-limited rental countdown behavior can be demonstrated

**Priority:** P1
**Phase:** 1
**Story Points:** S
**PRD Reference:** Section 8.3 Open Question 3

**Acceptance Criteria:**
- [ ] Given the seed data, when Alice's subscriptions are queried, then a "Movie Night" TVOD rental product exists assigned to Alice
- [ ] Given the TVOD product, when inspected, then `rental_hours = 48` and `first_played_at` is null (not yet played)
- [ ] Given Alice plays the TVOD content, when the license is requested, then it succeeds and `first_played_at` is recorded

**AI Component:** No

**Dependencies:** TVOD product seed data, `user_subscriptions` with TVOD support, Alice test user

---

## Epic 10: Production Migration Path

### US-DRM-029: Production DRM Migration Documentation

**As a** platform architect
**I want to** have the ClearKey-to-production-DRM migration path documented alongside the implementation
**So that** the team understands the upgrade path to Widevine/FairPlay without re-architecting

**Priority:** P2
**Phase:** 2
**Story Points:** S
**PRD Reference:** Section 11

**Acceptance Criteria:**
- [ ] Given the implementation, when a migration document is reviewed, then it covers every component in the production migration table (Section 11) with change required vs reusable assessment
- [ ] Given the document, when the entitlement model is referenced, then it is explicitly noted as fully reusable without changes
- [ ] Given the license server implementation, when reviewed, then the entitlement logic is cleanly separated from the ClearKey protocol handling (enabling a future protocol swap)

**AI Component:** No

**Dependencies:** License server implementation (US-DRM-008), key management service

---

## Epic 11: Technical Enablers

### US-DRM-030: Entitlement Engine Shared Module

**As a** backend developer
**I want to** have a single shared entitlement resolution module used by both the license server and the TSTV manifest endpoint
**So that** entitlement logic is consistent and maintained in one place

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** FR-12, FR-19

**Acceptance Criteria:**
- [ ] Given the entitlement module, when called with `(user_id, channel_id)`, then it returns `{entitled: bool, products: [...]}` from the union of the user's active subscriptions
- [ ] Given the license server and the TSTV manifest endpoint, when both perform entitlement checks, then both call the same module function
- [ ] Given the module, when tested in isolation, then unit tests cover: entitled user, not-entitled user, multiple overlapping subscriptions, expired subscription, TVOD rental not-yet-played, TVOD rental expired

**AI Component:** No

**Dependencies:** `user_subscriptions`, `product_entitlements`, `products` tables

---

### US-DRM-031: hls.js Version Audit and Upgrade

**As a** platform engineer
**I want to** verify and if necessary upgrade hls.js to version 1.4 or higher
**So that** ClearKey EME support is available in the player

**Priority:** P0
**Phase:** 1
**Story Points:** S
**PRD Reference:** Section 10 (Dependencies)

**Acceptance Criteria:**
- [ ] Given the frontend package.json, when inspected, then hls.js version is ≥ 1.4.0
- [ ] Given any hls.js upgrade, when existing player tests run, then no regressions in non-DRM playback are introduced
- [ ] Given the upgrade, when the changelog is reviewed, then any breaking changes are documented and addressed

**AI Component:** No

**Dependencies:** Frontend package.json, existing player integration tests

---

### US-DRM-032: CDN Configuration for fMP4 Extensions

**As a** platform engineer
**I want to** update the CDN nginx configuration to serve `.m4s` and `.mp4` files correctly
**So that** fMP4 init segments and media segments are cached and served with appropriate MIME types and headers

**Priority:** P0
**Phase:** 1
**Story Points:** S
**PRD Reference:** Section 9.1

**Acceptance Criteria:**
- [ ] Given the nginx config, when inspected, then `.m4s` has MIME type `video/iso.segment` and `.mp4` (init) has `video/mp4`
- [ ] Given the CDN cache rules, when `.m4s` and `.mp4` files are requested, then they are served with appropriate `Cache-Control` headers consistent with the HLS segment duration
- [ ] Given the previous `.ts` extension rules, when the config is updated, then `.ts` rules are removed or set to no-cache (no longer produced)

**AI Component:** No

**Dependencies:** CDN nginx configuration, fMP4 migration (US-DRM-002)

---

### US-DRM-033: End-to-End DRM Demo Runbook

**As a** demo presenter
**I want to** have a step-by-step runbook for demonstrating the full DRM entitlement chain
**So that** I can reliably walk through all key scenarios without improvisation

**Priority:** P2
**Phase:** 1
**Story Points:** S
**PRD Reference:** Section 5 (User Segments & Scenarios)

**Acceptance Criteria:**
- [ ] Given the runbook, when followed, then it covers: (1) Charlie playing all channels, (2) Diana being blocked with upsell, (3) admin granting Diana Sports Package → Diana immediately gaining access, (4) key rotation with catch-up still playing
- [ ] Given the runbook, when referenced for TVOD, then it includes Alice's Movie Night rental countdown demo
- [ ] Runbook is committed to `docs/` alongside the PRD

**AI Component:** No

**Dependencies:** All DRM epics implemented, seed data, admin dashboard

---

### US-DRM-034: Observability Dashboard for DRM

**As a** platform operator
**I want to** have a basic Grafana or admin dashboard view showing license request volume, grant/denial ratio, and latency
**So that** DRM health is visible during the PoC and any issues are quickly identifiable

**Priority:** P2
**Phase:** 1
**Story Points:** M
**PRD Reference:** NFR-8, FR-27

**Acceptance Criteria:**
- [ ] Given the dashboard, when viewed, then it shows license requests per minute grouped by outcome (granted/denied/unauthenticated)
- [ ] Given the dashboard, when viewed, then p50 and p99 license response latency are plotted over time
- [ ] Given the dashboard, when a spike in denials occurs, then it is visually prominent
- [ ] Dashboard can be the admin license request log (US-DRM-022) or a Grafana panel — either satisfies this story

**AI Component:** No

**Dependencies:** Structured license logging (US-DRM-026), admin dashboard or Grafana

---

*This user story document traces to PRD-009-multi-drm.md (PRD-POC-003). All stories should be read alongside the TSTV Implementation Plan for entitlement table dependencies.*
