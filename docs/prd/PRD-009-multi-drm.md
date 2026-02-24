# PRD: MultiDRM Content Protection & Entitlement Management

**Document ID:** PRD-POC-003
**Author:** TV Engineering
**Date:** February 2026
**Status:** Draft
**Scope:** OTT Platform PoC
**Dependencies:** TSTV Implementation Plan (SimLive streaming infrastructure, CDN, TSTV manifest generator)

---

## 1. Problem Statement

The OTT Platform PoC currently serves all content in the clear — any HTTP client that can reach the CDN can play any channel or catch-up program without authentication or authorization. This makes it impossible to demonstrate three capabilities that are fundamental to every commercial streaming platform.

**Content cannot be monetized without access control.** A real OTT platform gates content behind subscriptions, channel packages, rentals, and purchases. Without an entitlement model and enforcement mechanism, the PoC cannot demonstrate the business logic that determines who can watch what — the core value proposition of a pay-TV platform.

**Content protection is not just a checkbox — it's an architecture.** DRM is deeply integrated into the streaming pipeline: it affects how segments are packaged, how manifests are constructed, how players initialize, and how license decisions are made at playback time. A PoC that skips DRM entirely leaves a significant architectural gap — the team cannot validate that TSTV, catch-up, PVR, and live streaming all work correctly when encryption is in the path.

**The entitlement-to-playback chain is invisible.** In production, a viewer's ability to watch content passes through multiple systems: subscription management → entitlement resolution → license server → key delivery → decryption → playback. Each step can fail, and each failure requires a different UX response (upsell prompt, subscription renewal, error message). Without this chain in the PoC, the team cannot design, test, or demonstrate these critical user journeys.

---

## 2. Objective

Add standards-based content encryption and entitlement-gated key delivery to the OTT Platform PoC, demonstrating the full subscription → entitlement → license → playback chain using ClearKey DRM. ClearKey is architecturally identical to production Widevine/FairPlay — same CENC encryption, same EME browser API, same license request/response flow — but requires no commercial licenses.

The PoC will demonstrate:

1. **Content encryption** — all live and time-shifted streams are encrypted using CENC (Common Encryption) on fMP4 segments, making content unplayable without a valid decryption key.
2. **Entitlement-gated key delivery** — a license server that authenticates the viewer, checks their subscription/entitlements, and returns decryption keys only to authorized users.
3. **Subscription and product model** — a data model supporting base subscriptions, channel packages, à la carte channels, SVOD catalogs, and TVOD rent/buy, with enforcement at the license level.
4. **Denial and upsell flows** — when a viewer attempts to play content they're not entitled to, the system returns actionable information (which product would grant access) enabling the frontend to show an upsell prompt.
5. **Per-channel key management** — encryption keys managed per channel with rotation support, demonstrating that key lifecycle does not disrupt catch-up or PVR playback of previously encrypted content.

---

## 3. Success Criteria

| Criteria | Measurement |
|----------|-------------|
| All live and TSTV streams are encrypted | Segments are not playable when accessed directly via CDN URL without a license |
| Entitled viewers can play content seamlessly | Login as a user with the correct subscription → channel plays without interruption |
| Non-entitled viewers are blocked with actionable feedback | Login as a user without the correct subscription → 403 response with product suggestion → frontend shows upsell |
| Key rotation does not break existing content | Rotate a channel key → new live content uses new key → catch-up content from before rotation still plays |
| Entitlement changes take effect immediately | Admin adds a subscription to a user → user can immediately play previously blocked content |
| All acquisition types are demonstrable | Base, channel package, à la carte, SVOD, TVOD rent, and TVOD buy all correctly gate content access |

---

## 4. Scope

### 4.1 In Scope

- ClearKey DRM encryption of all HLS fMP4 segments (live, start-over, catch-up)
- Key management service: per-channel key generation, storage, and rotation
- ClearKey license endpoint implementing the W3C EME ClearKey JSON protocol
- Entitlement model: products, subscriptions, and entitlement resolution
- Subscription types: base subscription, channel packages, à la carte channels, SVOD, TVOD rent, TVOD buy
- Entitlement enforcement at the license server (definitive block) and at the API level (early rejection)
- Player integration: hls.js EME configuration with ClearKey, auth token injection, upsell handling on denial
- Admin dashboard: DRM key management (view keys, rotate), subscription management (assign/remove subscriptions per user), product management
- Segment format migration from MPEG-TS to fMP4 (required for CENC)
- Seed data: products, entitlements, and test users with varied subscription levels

### 4.2 Out of Scope

- **Production DRM (Widevine, FairPlay, PlayReady).** These require commercial license agreements with Google, Apple, and Microsoft respectively. ClearKey demonstrates the identical architecture without the licensing overhead. The migration path from ClearKey to production DRM is documented but not implemented.
- **Hardware-level content protection.** ClearKey does not use a hardware-backed CDM — the decryption key is visible in browser dev tools. This is accepted for a PoC. Production would use Widevine L1/L3 and FairPlay for secure key handling.
- **HDCP enforcement.** Output protection is not available with ClearKey and is out of scope.
- **Multi-key encryption within a single stream.** The PoC uses one key per channel. Production might use per-program or per-quality-tier keys. The key management service supports this data model but it is not demonstrated.
- **Offline download DRM.** Persistent license sessions for offline playback are not implemented.
- **Payment processing.** Subscriptions are assigned via admin dashboard, not purchased through a payment flow. The product/pricing model is present for demonstration, not commerce.

---

## 5. User Segments & Scenarios

### 5.1 Viewer Scenarios

The PoC uses four test users to demonstrate the entitlement model across different subscription levels:

**Charlie — Full Access Subscriber**
- Subscriptions: "All Channels" package
- Can access: All 5 channels (live, start-over, catch-up)
- Demonstrates: Premium subscriber experience — everything works, no friction

**Alice — Partial Subscriber (Sports)**
- Subscriptions: Basic + Sports Package
- Can access: ch1 (NRK1), ch4 (Eurosport), ch5 (NatGeo)
- Cannot access: ch2 (TV 2), ch3 (Discovery)
- Demonstrates: Entitlement boundaries — plays some channels, gets upsell prompt on Entertainment channels

**Bob — Partial Subscriber (Entertainment)**
- Subscriptions: Basic + Entertainment Package
- Can access: ch1 (NRK1), ch2 (TV 2), ch3 (Discovery), ch5 (NatGeo)
- Cannot access: ch4 (Eurosport)
- Demonstrates: Complementary entitlements to Alice — different package, different access

**Diana — Minimal Subscriber**
- Subscriptions: Basic only
- Can access: ch1 (NRK1), ch5 (NatGeo)
- Cannot access: ch2 (TV 2), ch3 (Discovery), ch4 (Eurosport)
- Demonstrates: Upsell-heavy experience — most channels trigger product suggestions

### 5.2 Admin Scenarios

**Subscription management:** Admin assigns Sports Package to Diana → Diana immediately gains access to ch4 without re-login.

**Key rotation:** Admin rotates encryption key for ch1 → SimLive restarts with new key → live viewers experience brief rebuffer → catch-up content from before rotation still plays using the old key (resolved by KID in segment headers).

**Product management:** Admin creates a new "Movie Night" TVOD rental product for a specific program → assigns to Alice → Alice can play the program for 48h.

---

## 6. Functional Requirements

### 6.1 Content Encryption

**FR-1:** All HLS segments produced by SimLive shall be encrypted using CENC AES-128-CTR (Common Encryption, Counter Mode). Segments shall be in fMP4 (fragmented MP4) format, replacing the current MPEG-TS format.

**FR-2:** Each channel shall have a dedicated encryption key. The key ID (KID) shall be embedded in the fMP4 init segment's PSSH box and referenced in the HLS manifest via `#EXT-X-KEY`.

**FR-3:** The HLS manifest shall include encryption signaling compatible with the ClearKey EME key system, including the license server URL and appropriate KEYFORMAT identifier.

**FR-4:** Encrypted segments shall be indistinguishable from random data when accessed without the decryption key. Direct CDN access to segment URLs shall not yield playable content.

### 6.2 Key Management

**FR-5:** The key management service shall generate cryptographically random 128-bit AES keys using a secure random source (`os.urandom` or equivalent).

**FR-6:** Each key shall be identified by a UUID (Key ID / KID). The KID is public (embedded in manifests and segments). The key value is secret (returned only via the license endpoint after entitlement verification).

**FR-7:** The key management service shall support key rotation per channel: deactivating the current key and generating a new one. The old key shall remain in the database for license requests referencing content encrypted with it (catch-up, PVR).

**FR-8:** SimLive shall request the active encryption key for each channel from the key management service at startup and whenever a key rotation is triggered.

**FR-9:** Key provisioning endpoints (used by SimLive) shall be restricted to internal Docker network access only — not exposed to end users.

### 6.3 License Server (ClearKey Protocol)

**FR-10:** The license endpoint shall implement the W3C EME ClearKey JSON license exchange: accept a JSON request containing `kids` (array of base64url-encoded Key IDs) and return a JSON response containing `keys` (array of base64url-encoded key ID/value pairs).

**FR-11:** Every license request shall be authenticated via the user's JWT bearer token (the same auth mechanism used throughout the PoC).

**FR-12:** Before returning any key, the license server shall verify the requesting user's entitlement to the channel (or content) associated with the requested KID. The entitlement check shall query `user_subscriptions` → `product_entitlements` for an active subscription covering the relevant channel or content.

**FR-13:** If the user is entitled, the license server shall return HTTP 200 with the requested keys in ClearKey JSON format.

**FR-14:** If the user is not entitled, the license server shall return HTTP 403 with a structured error response including: the error type (`not_entitled`), the channel or content that was requested, and a list of products that would grant access (enabling the frontend to display an upsell prompt).

### 6.4 Entitlement Model

**FR-15:** The system shall support the following product/acquisition types:

| Type | Description | Duration | Entitlement scope |
|------|-------------|----------|-------------------|
| `base` | Included with platform access | Ongoing while subscribed | Specified channels |
| `channel_package` | Premium channel bundle | Monthly recurring | Specified channels |
| `channel` | Single premium channel | Monthly recurring | One channel |
| `svod` | Streaming catalog subscription | Monthly recurring | Specified content library |
| `tvod_rent` | Time-limited single title | N hours from first play | One content item |
| `tvod_buy` | Permanent single title | Account lifetime | One content item |

**FR-16:** A user's effective entitlements shall be the union of all entitlements granted by their active subscriptions. If a user has both "Basic" (granting ch1, ch5) and "Sports Package" (granting ch4), their effective entitlements include ch1, ch4, and ch5.

**FR-17:** For TVOD rentals, the rental countdown shall begin on first playback (`first_played_at`), not on purchase. A rental that has not been played does not expire. Once played, it expires after the product's `rental_hours`.

**FR-18:** Entitlement changes (new subscription, cancellation, expiry) shall take effect immediately — no cache delay. The next license request after a subscription change shall reflect the updated entitlements.

### 6.5 Entitlement Enforcement Points

**FR-19:** Entitlements shall be enforced at multiple points in the playback chain:

| Enforcement point | Behavior on denial | Purpose |
|-------------------|-------------------|---------|
| DRM license request | 403 + product suggestions | Definitive block — content cannot be decrypted |
| TSTV manifest request | 403 + product suggestions | Early rejection — prevents loading player |
| Channel list API | Channel marked as locked | UI indication — shows subscription needed |
| EPG catch-up click | Redirect to upsell | UX guard — prevents futile playback attempt |

The DRM license check is the authoritative enforcement point. API-level checks are convenience optimizations that improve UX by failing fast, but cannot be relied upon as the sole protection.

### 6.6 Player Integration

**FR-20:** The player (Shaka Player 4.12) shall be configured with EME support for the ClearKey key system, including the license server URL and automatic injection of the user's auth token on license requests. Shaka's DRM configuration shall use the `drm.servers` and `drm.advanced` config keys for the `org.w3.clearkey` key system.

**FR-21:** On successful license acquisition, playback shall proceed seamlessly — the viewer should not be aware that decryption is occurring.

**FR-22:** On license denial (HTTP 403), the player shall intercept the error and display a contextual upsell prompt showing: which channel or content was denied, which product(s) would grant access, and a call-to-action (e.g., "Subscribe to Sports Package — 299 kr/mo").

**FR-23:** The upsell prompt shall be a reusable component used across all denial scenarios (live, catch-up, start-over, VOD).

### 6.7 Admin Dashboard

**FR-24:** The admin dashboard shall include a DRM management panel showing: all encryption keys (channel, KID, active/rotated status, creation date), with a "Rotate Key" action per channel.

**FR-25:** The admin dashboard shall include a subscription management panel showing: all users with their active subscriptions and effective channel entitlements, with actions to add/remove subscriptions.

**FR-26:** The admin dashboard shall include a product management panel showing: all products with their type, pricing, and channel/content entitlements, with editing capability.

**FR-27:** The admin dashboard shall include a license request log showing: recent license requests with outcome (granted/denied), user, channel, and timestamp — for debugging and demonstration.

---

## 7. Non-Functional Requirements

### 7.1 Performance

**NFR-1:** License requests shall complete within 100ms (p99) under PoC load conditions. License latency directly impacts time-to-first-frame — the player cannot render video until the key is received.

**NFR-2:** Key rotation shall complete within 5 seconds (key generation + SimLive restart for affected channel). Other channels shall not be impacted during rotation.

### 7.2 Security

**NFR-3:** Encryption key values shall never appear in API responses other than the license endpoint (and only after entitlement verification). Key values shall not be logged, included in error messages, or exposed in admin dashboard UI.

**NFR-4:** Key provisioning endpoints (used by SimLive) shall be network-restricted to the Docker internal network. They shall not be accessible from the frontend or external clients.

**NFR-5:** The license endpoint shall validate JWT tokens using the same authentication middleware as the rest of the backend. Expired, malformed, or missing tokens shall result in HTTP 401 before any entitlement check occurs.

### 7.3 Reliability

**NFR-6:** If the key management service is temporarily unavailable, SimLive shall retry key fetching with exponential backoff rather than starting unencrypted. Content shall never be served in the clear due to a transient key service failure.

**NFR-7:** Old encryption keys shall remain in the database indefinitely (or until explicitly purged by admin). This ensures catch-up and PVR content encrypted with rotated keys remains playable.

### 7.4 Observability

**NFR-8:** License request outcomes (granted, denied by reason) shall be logged with structured fields: user_id, channel_id, kid, outcome, denial_reason, latency_ms.

**NFR-9:** Key rotation events shall be logged: channel_id, old_kid, new_kid, timestamp.

---

## 8. Data Model

### 8.1 New Tables

```sql
CREATE TABLE drm_keys (
    id              SERIAL PRIMARY KEY,
    key_id          UUID NOT NULL UNIQUE,
    key_value       BYTEA NOT NULL,
    channel_id      INTEGER REFERENCES channels(id),
    content_id      INTEGER,
    active          BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    rotated_at      TIMESTAMPTZ,
    expires_at      TIMESTAMPTZ
);
```

### 8.2 Entitlement Tables (defined in TSTV plan, referenced here)

The following tables are created as part of the TSTV implementation and are consumed by the DRM license server:

- `products` — available subscription/purchase products
- `product_entitlements` — maps products to channels/content
- `user_subscriptions` — tracks what each user has subscribed to or purchased

### 8.3 Seed Data

**Products:**

| Product | Type | Monthly price | Channels |
|---------|------|---------------|----------|
| Basic | base | Included | ch1 (NRK1), ch5 (NatGeo) |
| Sports Package | channel_package | 299 kr | ch4 (Eurosport) |
| Entertainment Package | channel_package | 199 kr | ch2 (TV 2), ch3 (Discovery) |
| All Channels | channel_package | 449 kr | ch1–ch5 |

**Test user subscriptions:**

| User | Subscriptions | Entitled channels |
|------|--------------|-------------------|
| Charlie | All Channels | ch1, ch2, ch3, ch4, ch5 |
| Alice | Basic + Sports | ch1, ch4, ch5 |
| Bob | Basic + Entertainment | ch1, ch2, ch3, ch5 |
| Diana | Basic | ch1, ch5 |

---

## 9. Infrastructure Changes

### 9.1 Segment Format Migration

SimLive output changes from MPEG-TS (`.ts`) to fMP4 (`.m4s`) with CENC encryption. This affects:

- SimLive FFmpeg command: adds `-hls_segment_type fmp4`, `-encryption_scheme`, `-encryption_key`, `-encryption_kid`
- CDN nginx config: `.m4s` and `.mp4` file extensions in cache rules
- Cleanup cron: `.m4s` instead of `.ts`
- TSTV manifest generator: `.m4s` extension and init segment (`#EXT-X-MAP`) reference in generated manifests

### 9.2 SimLive Startup Flow Change

SimLive must obtain encryption keys before launching FFmpeg processes:

1. Container starts
2. For each channel: `GET /drm/keys/channel/{id}/active` → receives `key_id_hex` and `key_hex`
3. Launch FFmpeg with encryption parameters
4. On key rotation signal: stop FFmpeg for affected channel → fetch new key → restart FFmpeg

---

## 10. Dependencies

| Dependency | Source | Status | Notes |
|------------|--------|--------|-------|
| SimLive streaming infrastructure | TSTV Plan | Planned | SimLive must be operational before encryption can be added |
| CDN serving layer | TSTV Plan | Planned | fMP4 segments served from shared volume |
| TSTV manifest generator | TSTV Plan | Planned | Must be updated for `.m4s` extension and `#EXT-X-MAP` |
| Entitlement tables | TSTV Plan | Planned | `products`, `product_entitlements`, `user_subscriptions` created in TSTV migration |
| User authentication (JWT) | Existing | Exists | Auth middleware already in the backend |
| Shaka Player | Existing | Exists (v4.12) | Supports ClearKey EME, Widevine, and FairPlay natively — no version change required |

---

## 11. Production Migration Path

The ClearKey PoC is designed for minimal-friction migration to production MultiDRM:

| Component | ClearKey (PoC) | Production | Change required |
|-----------|---------------|------------|-----------------|
| Segment encryption | CENC AES-128-CTR | CENC AES-128-CTR | None — identical |
| Segment format | fMP4 | fMP4 | None — identical |
| Key management | Self-hosted (FastAPI) | DRM vendor (Axinom, BuyDRM, PallyCon) or self-hosted with Widevine SDK | Integration work |
| License server | ClearKey JSON protocol | Widevine license proxy + FairPlay KSM | Protocol swap |
| License auth + entitlement | JWT + entitlement check | Same logic, called from vendor license proxy | Reusable |
| Player | Shaka Player EME (ClearKey) | Shaka Player (Widevine/FairPlay CDM) | DRM config change only — same player |
| Manifest signaling | `#EXT-X-KEY` (ClearKey) | `#EXT-X-KEY` (Widevine/FairPlay KEYFORMAT) | Manifest template change |
| Key storage | PostgreSQL | HSM-backed key storage or vendor-managed | Security upgrade |
| Entitlement model | Same | Same | Reusable as-is |

The entitlement model, product/subscription data model, and business logic are fully reusable. The migration is primarily a license protocol and key security upgrade.

---

## 12. Implementation Sequence

| # | Task | Scope |
|---|------|-------|
| 1 | Alembic migration: `drm_keys` table | DB |
| 2 | Key management service: generation, storage, rotation endpoints | Backend |
| 3 | SimLive update: fMP4 output + CENC encryption, key fetching at startup | Infra |
| 4 | CDN config update: `.m4s` / `.mp4` extensions | Infra |
| 5 | Verify encrypted segments (curl + ffplay) | Test |
| 6 | License endpoint: ClearKey protocol + entitlement enforcement | Backend |
| 7 | TSTV manifest generator: `.m4s` extension, init segment reference | Backend |
| 8 | Player: hls.js EME configuration, auth token injection | Frontend |
| 9 | Player: upsell prompt on license denial | Frontend |
| 10 | Admin: DRM key management panel | Frontend |
| 11 | Admin: subscription management panel | Frontend |
| 12 | Admin: license request log | Frontend |

---

## 13. Open Questions

1. **Encrypt all channels or allow some in the clear?** The PoC could keep ch1 (NRK1) unencrypted to demonstrate the difference and simplify debugging. However, this would mean the entitlement model doesn't protect "Basic" tier content. Recommendation: encrypt all channels — consistency is more valuable than the debugging convenience.

2. **Key rotation frequency for PoC demo?** Production systems rotate keys on a schedule (hourly, daily, or per content window). For the PoC, manual rotation via admin dashboard is sufficient. Automatic rotation is a future enhancement.

3. **TVOD demonstration scope.** The entitlement model supports TVOD rent/buy, but without a payment flow or content catalog beyond live channels, demonstrating TVOD requires additional seed data (e.g., a "Movie Night" VOD title). Should this be included in the initial implementation or deferred? Recommendation: include one TVOD rental in seed data to demonstrate the time-limited rental countdown.

4. **License caching in the player.** hls.js may cache the ClearKey license for the session duration, meaning a subscription change (admin adds/removes a package) won't take effect until the player reloads. Is this acceptable for the PoC? Recommendation: yes — document the behavior and note that production implementations would use shorter license durations or server-side revocation.

---

*This PRD should be read alongside the TSTV Implementation Plan (streaming infrastructure, entitlement data model) and the DRM Implementation Plan (detailed technical specifications) for full context.*
