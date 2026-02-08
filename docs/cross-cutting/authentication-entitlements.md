# Authentication & Entitlements
## Cross-Cutting Concerns — AI-Native OTT Streaming Platform

**Document ID:** XC-001
**Version:** 1.0
**Date:** 2026-02-08
**Status:** Draft
**Author:** Integration Analyst Agent
**References:** ARCH-001, VIS-001, PRD-001 through PRD-008
**Audience:** Backend Engineers, Security Engineers, Client Engineers, Product Managers

---

## Table of Contents

1. [Overview](#1-overview)
2. [User Authentication](#2-user-authentication)
3. [Device Activation & Management](#3-device-activation--management)
4. [Session Management](#4-session-management)
5. [Entitlement Model](#5-entitlement-model)
6. [Per-Service Entitlement Checks](#6-per-service-entitlement-checks)
7. [Parental Controls & PIN Management](#7-parental-controls--pin-management)
8. [Guest & Trial Access](#8-guest--trial-access)
9. [Single Sign-On (SSO)](#9-single-sign-on-sso)
10. [Token Lifecycle](#10-token-lifecycle)
11. [Error Handling & Edge Cases](#11-error-handling--edge-cases)
12. [AI Integration](#12-ai-integration)

---

## 1. Overview

Authentication and entitlements form the security and access-control backbone of the platform. Every user interaction — from browsing the EPG to starting live TV playback, scheduling a recording, or purchasing a TVOD title — requires identity verification and entitlement validation. These concerns span all eight PRDs and touch every microservice in the architecture.

### Design Principles

- **Stateless token validation at the edge.** Access tokens (JWT, RS256) are validated by the BFF layer without calling back to the Auth Service. This keeps the critical playback path fast (< 200ms end-to-end).
- **Centralized entitlement source of truth.** The Entitlement Service owns all access decisions. Other services query it but never maintain their own entitlement logic.
- **Cache-first for hot paths.** Entitlement lookups are cached in Redis with a 60-second TTL. The cache is invalidated on subscription change, package upgrade, or TVOD purchase events via Kafka.
- **Graceful degradation.** If the Auth Service or Entitlement Service is temporarily unavailable, cached tokens and entitlements allow continued access for the duration of the cache TTL. New sessions cannot be created during an outage.
- **Audit everything.** Every authentication event, entitlement check, and access denial is logged with structured fields for security investigation and compliance.

### Key Services

| Service | Role | SLO |
|---------|------|-----|
| **Auth Service** (Go) | Handles login, token issuance, token refresh, device activation | p99 < 100ms, 99.99% availability |
| **Entitlement Service** (Go) | Evaluates access rights per user per content/channel | p99 < 30ms, 99.99% availability |
| **User Service** (Go) | Manages user accounts, credentials, profile associations | p99 < 50ms, 99.99% availability |
| **Profile Service** (Go) | Manages per-user profiles (up to 6 per account) | p99 < 50ms, 99.95% availability |
| **Subscription Service** (Go) | Manages subscription lifecycle, packages, add-ons | p99 < 100ms, 99.95% availability |

---

## 2. User Authentication

### 2.1 Authentication Methods

The platform supports multiple authentication methods to cover all client platforms and user preferences:

| Method | Flow | Platforms | Phase |
|--------|------|-----------|-------|
| Email + Password | Direct credential entry | Web, Mobile | 1 |
| Social Login (Google) | OAuth 2.0 Authorization Code + PKCE | Web, Mobile | 1 |
| Social Login (Apple) | Sign in with Apple (OAuth 2.0) | iOS, Apple TV, Web | 1 |
| Device Activation Code | 6-character code displayed on TV, authenticated on phone/web | Android TV, Apple TV, Smart TVs, STBs | 1 |
| Operator SSO (SAML/OIDC) | Federated identity via operator's IdP | All (operator-branded deployments) | 2 |
| Biometric (Face ID / Fingerprint) | Local biometric for re-authentication | iOS, Android | 2 |

### 2.2 OAuth 2.0 Token Flow

The platform uses OAuth 2.0 with JWT access tokens and opaque refresh tokens.

**Login Flow (Email + Password):**

```
Client                    BFF                     Auth Service              User Service
  │                        │                          │                         │
  │  POST /auth/login      │                          │                         │
  │  {email, password}     │                          │                         │
  │───────────────────────>│                          │                         │
  │                        │  gRPC: ValidateCredentials                         │
  │                        │─────────────────────────>│                         │
  │                        │                          │  gRPC: GetUser(email)   │
  │                        │                          │────────────────────────>│
  │                        │                          │  {user_id, password_hash}│
  │                        │                          │<────────────────────────│
  │                        │                          │                         │
  │                        │                          │  bcrypt.Compare(...)    │
  │                        │                          │                         │
  │                        │  {access_token, refresh_token, expires_in}         │
  │                        │<─────────────────────────│                         │
  │                        │                          │                         │
  │  {access_token,        │                          │                         │
  │   refresh_token,       │                          │                         │
  │   expires_in: 900}     │                          │                         │
  │<───────────────────────│                          │                         │
```

**Access Token (JWT) Structure:**

```json
{
  "header": {
    "alg": "RS256",
    "typ": "JWT",
    "kid": "key-2026-02"
  },
  "payload": {
    "sub": "usr_a1b2c3d4",
    "iss": "https://auth.platform.example.com",
    "aud": "platform-api",
    "iat": 1707400800,
    "exp": 1707401700,
    "jti": "tok_unique_id",
    "profile_id": "prf_x1y2z3",
    "subscription_tier": "premium",
    "device_id": "dev_m1n2o3",
    "device_type": "android_tv",
    "entitlements_hash": "sha256:abcdef12",
    "max_streams": 4,
    "parental_rating": "TV-14",
    "market": "GB"
  }
}
```

Key design decisions:
- **15-minute expiry** for access tokens balances security with user experience. Shorter expiry means less damage from token theft; 15 minutes avoids excessive refresh traffic.
- **`entitlements_hash`** is a compact hash of the user's entitlement set. The BFF uses it as a cache key for entitlement lookups. When the hash changes (subscription change), cached entitlements are invalidated.
- **`parental_rating`** is included so the BFF can filter content without querying the Profile Service on every request.

**Refresh Token:**

Refresh tokens are opaque (not JWT). They are stored server-side in the Auth Service database (PostgreSQL) with the following record:

| Field | Type | Description |
|-------|------|-------------|
| `token_id` | UUID | Unique token identifier |
| `user_id` | UUID | Associated user |
| `device_id` | UUID | Associated device |
| `token_hash` | VARCHAR(64) | SHA-256 hash of the token value (never store raw) |
| `expires_at` | TIMESTAMP | 30-day expiry from issuance |
| `created_at` | TIMESTAMP | Issuance time |
| `revoked_at` | TIMESTAMP | Null unless explicitly revoked |
| `last_used_at` | TIMESTAMP | Updated on each refresh |

**Refresh flow:**
1. Client detects access token nearing expiry (< 2 minutes remaining).
2. Client sends `POST /auth/refresh` with refresh token.
3. Auth Service validates refresh token: exists, not expired, not revoked, device matches.
4. Auth Service issues new access token + new refresh token (rotation).
5. Old refresh token is invalidated (one-time use).
6. If refresh token is expired or invalid, client must re-authenticate (login screen).

**Refresh token rotation** prevents replay attacks: if a refresh token is used twice, both the original and the new token are revoked, forcing re-authentication.

### 2.3 Password Security

- **Storage:** bcrypt with cost factor 12 (adaptive — increases as hardware improves).
- **Requirements:** Minimum 10 characters, checked against Have I Been Pwned (HIBP) k-anonymity API during registration and password change.
- **Rate limiting:** 5 failed attempts per email per 15 minutes. After 5 failures, account is locked for 30 minutes. CAPTCHA challenge after 3 failures.
- **Recovery:** Email-based password reset with 1-hour expiry token. Rate limited to 3 reset requests per email per hour.

### 2.4 Kafka Events

All authentication events are published to `user.events` (Avro schema):

| Event | Trigger | Key Fields |
|-------|---------|------------|
| `auth.login.success` | Successful authentication | user_id, device_id, method (email/social/device_code), client_ip, user_agent |
| `auth.login.failed` | Failed authentication attempt | email (hashed), reason (invalid_password, account_locked, unknown_email), client_ip |
| `auth.token.refreshed` | Token refresh | user_id, device_id, old_token_id, new_token_id |
| `auth.logout` | Explicit logout | user_id, device_id, session_id |
| `auth.device.activated` | Device activation completed | user_id, device_id, device_type, activation_code_hash |
| `auth.password.changed` | Password updated | user_id, method (user_initiated, admin_reset) |
| `auth.account.locked` | Account locked due to failed attempts | email (hashed), failed_count, lock_duration |

---

## 3. Device Activation & Management

### 3.1 TV / STB Activation Flow

TV and STB devices use a code-based activation flow because they lack convenient text input.

```
TV App                  Auth Service            User's Phone/Web
  │                         │                         │
  │  POST /auth/device/code │                         │
  │  {device_id, device_type}                         │
  │────────────────────────>│                         │
  │                         │                         │
  │  {code: "AB3X7K",       │                         │
  │   verify_url: "https://activate.example.com",     │
  │   expires_in: 600,      │                         │
  │   poll_interval: 5}     │                         │
  │<────────────────────────│                         │
  │                         │                         │
  │  Display code + URL     │                         │
  │  on TV screen           │                         │
  │                         │                         │
  │                         │   GET /activate?code=AB3X7K
  │                         │<────────────────────────│
  │                         │                         │
  │                         │   Login form (if not    │
  │                         │   already authenticated)│
  │                         │────────────────────────>│
  │                         │                         │
  │                         │   POST /activate        │
  │                         │   {code, user_session}  │
  │                         │<────────────────────────│
  │                         │                         │
  │                         │   "Device activated!"   │
  │                         │────────────────────────>│
  │                         │                         │
  │  GET /auth/device/poll  │                         │
  │  {code}                 │                         │
  │────────────────────────>│                         │
  │                         │                         │
  │  {access_token,         │                         │
  │   refresh_token}        │                         │
  │<────────────────────────│                         │
```

**Activation code properties:**
- 6 alphanumeric characters (uppercase, excluding ambiguous characters: 0/O, 1/I/L).
- Effective character set: `ABCDEFGHJKMNPQRSTUVWXYZ23456789` (29 characters) = ~24.5 bits of entropy per code.
- 10-minute expiry. Not reusable.
- Rate limited: 1 code request per device per 2 minutes.

### 3.2 Device Management

Users can manage their registered devices through the account settings:

| Capability | Description |
|------------|-------------|
| **View devices** | List all registered devices with: name, type, last active date, location (approximate, from IP) |
| **Rename device** | Custom name for easier identification ("Living Room TV") |
| **Remove device** | Deregister a device, revoking all its tokens immediately |
| **Device limit** | Per-subscription tier (Basic: 3 devices, Standard: 5, Premium: 10) |
| **Device cooldown** | After removing a device, its slot is available after 24 hours (prevents rapid device swapping for account sharing abuse) |

**Device registration Kafka event:** `auth.device.registered` with fields: user_id, device_id, device_type, device_name, registration_method.

### 3.3 Concurrent Stream Enforcement

The Playback Session Service enforces concurrent stream limits:

| Subscription Tier | Max Concurrent Streams |
|-------------------|----------------------|
| Basic | 1 |
| Standard | 2 |
| Premium | 4 |
| Family | 6 |

**Enforcement flow:**
1. Client requests playback start → Playback Session Service creates session.
2. Service counts active sessions for this user (sessions with a heartbeat in the last 60 seconds).
3. If count >= limit: return `HTTP 409 Conflict` with body listing active devices and streams.
4. Client displays: "You are already watching on [device_name]. Stop that session to watch here, or upgrade your plan."
5. User can remotely stop another session (force-stop sends a push notification to the affected device).

**Grace period:** 60 seconds between session stop and new session start, to handle natural device switching (e.g., moving from phone to TV) without hitting the limit.

**Heartbeat:** Clients send playback heartbeats every 30 seconds. A session without a heartbeat for 90 seconds is considered inactive and does not count toward the concurrent limit.

---

## 4. Session Management

### 4.1 Session Lifecycle

```
                    ┌──────────┐
                    │  Login   │
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │  Active  │─── Token Refresh (every ~14 min)
                    └────┬─────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
         ┌────▼────┐ ┌──▼───┐ ┌───▼────┐
         │ Logout  │ │Expired│ │Revoked │
         │(explicit)│ │(30-day│ │(admin/ │
         │         │ │ idle) │ │ user)  │
         └─────────┘ └──────┘ └────────┘
```

### 4.2 Session Types

| Session Type | Duration | Refresh | Use Case |
|-------------|----------|---------|----------|
| **Interactive session** | Access token: 15 min, Refresh token: 30 days | Automatic by client | Normal user sessions on all devices |
| **Playback session** | Tied to interactive session | Heartbeat every 30s | Active media playback |
| **Device session** | Refresh token: 90 days | Automatic | TV/STB devices where re-login is inconvenient |
| **Remember me session** | Refresh token: 90 days | Automatic | Web/mobile with "keep me logged in" enabled |

### 4.3 Session Revocation

Sessions can be revoked through multiple paths:

| Trigger | Scope | Mechanism |
|---------|-------|-----------|
| User explicit logout | Single device | Refresh token revoked in Auth Service DB |
| User removes device | Single device | All refresh tokens for that device revoked |
| User changes password | All devices | All refresh tokens for user revoked, Kafka event triggers BFF cache invalidation |
| Admin suspends account | All devices | User flagged as suspended in User Service; BFF rejects all tokens for this user |
| Subscription expired | None (session stays, entitlements restricted) | Entitlement cache invalidated; user can browse but not play premium content |
| Security incident | All devices for affected users | Bulk revocation via Auth Service admin API |

### 4.4 Session Storage

Active sessions are tracked in Redis (Auth Service cluster):

```
Key:    session:{user_id}:{device_id}
Value:  {
          "session_id": "sess_abc123",
          "refresh_token_id": "rtok_def456",
          "device_type": "android_tv",
          "created_at": "2026-02-08T10:00:00Z",
          "last_active": "2026-02-08T14:30:00Z",
          "ip_address": "203.0.113.42"
        }
TTL:    90 days (matches max refresh token lifetime)
```

---

## 5. Entitlement Model

### 5.1 Entitlement Hierarchy

The entitlement model uses a package-based system where content is grouped into packages, and subscription tiers include one or more packages:

```
Subscription Tier
  └── Content Package(s)
        └── Content Item(s) — channels, VOD titles, recording rights
```

**Example:**

```
Premium Tier
  ├── Base Package (channels 1-150, SVOD catalog)
  ├── Sports Package (sports channels, sports VOD)
  ├── Movies Package (premium movie channels, movie SVOD)
  └── Cloud PVR (100 hours recording quota)

Standard Tier
  ├── Base Package (channels 1-100, limited SVOD catalog)
  └── Cloud PVR (50 hours recording quota)

Basic Tier
  └── Base Package (channels 1-50, basic SVOD catalog)
```

### 5.2 Entitlement Types

| Entitlement Type | Scope | Duration | Source |
|-----------------|-------|----------|--------|
| **SVOD** | Package of VOD titles | Subscription lifetime | Subscription Service |
| **TVOD Rental** | Single title | 48 hours from first play (30-day purchase window) | Transaction Service |
| **TVOD Purchase (EST)** | Single title | Indefinite (account lifetime) | Transaction Service |
| **Live Channel** | Single channel or channel package | Subscription lifetime | Subscription Service |
| **Start Over** | Per-channel right | Subscription lifetime (if channel package includes it) | Subscription Service + content rights |
| **Catch-Up** | Per-channel right | Subscription lifetime (7-day content window) | Subscription Service + content rights |
| **Cloud PVR** | Recording quota (hours) | Subscription lifetime | Subscription Service |
| **Download (Offline)** | Per-title right (subset of SVOD) | 48-hour offline license | Content rights flag |
| **Add-On Package** | Bundle of channels/content | Monthly (auto-renewing) | Subscription Service |
| **Promotional** | Any content set | Fixed period (e.g., 7-day trial, 30-day promo) | Promotion Service |

### 5.3 Entitlement Data Model

**Entitlement Service (PostgreSQL):**

```sql
-- Core entitlement record
CREATE TABLE user_entitlements (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id),
    package_id      UUID NOT NULL REFERENCES content_packages(id),
    source_type     VARCHAR(20) NOT NULL,  -- 'subscription', 'tvod', 'promotion', 'addon'
    source_id       UUID NOT NULL,         -- references subscription, transaction, or promotion
    granted_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at      TIMESTAMPTZ,           -- NULL = indefinite
    revoked_at      TIMESTAMPTZ,           -- NULL = active
    market          VARCHAR(5) NOT NULL,   -- ISO 3166-1 (e.g., 'GB')
    metadata        JSONB                  -- additional per-source metadata
);

-- Content package membership
CREATE TABLE package_contents (
    package_id      UUID NOT NULL REFERENCES content_packages(id),
    content_type    VARCHAR(20) NOT NULL,  -- 'channel', 'vod_title', 'vod_collection', 'pvr_quota'
    content_id      UUID NOT NULL,         -- references channel, catalog title, etc.
    start_at        TIMESTAMPTZ,           -- availability window start
    end_at          TIMESTAMPTZ,           -- availability window end
    territory       VARCHAR(5),            -- NULL = all territories
    PRIMARY KEY (package_id, content_type, content_id)
);

-- TVOD transactions
CREATE TABLE tvod_transactions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id),
    content_id      UUID NOT NULL,
    transaction_type VARCHAR(10) NOT NULL, -- 'rental', 'purchase'
    price_amount    DECIMAL(10,2) NOT NULL,
    price_currency  VARCHAR(3) NOT NULL,
    purchased_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    first_played_at TIMESTAMPTZ,          -- rental window starts on first play
    expires_at      TIMESTAMPTZ,          -- rental expiry; NULL for purchases
    payment_ref     VARCHAR(255) NOT NULL, -- external payment provider reference
    status          VARCHAR(20) NOT NULL DEFAULT 'active'  -- active, expired, refunded
);
```

### 5.4 Entitlement Check Flow

The Entitlement Service exposes a single gRPC endpoint used by all services:

```protobuf
service EntitlementService {
  rpc CheckAccess(CheckAccessRequest) returns (CheckAccessResponse);
  rpc ListEntitlements(ListEntitlementsRequest) returns (ListEntitlementsResponse);
}

message CheckAccessRequest {
  string user_id = 1;
  string content_type = 2;    // "channel", "vod_title", "recording", "catchup"
  string content_id = 3;
  string market = 4;
  string device_type = 5;     // for platform-specific rights
}

message CheckAccessResponse {
  bool allowed = 1;
  string denial_reason = 2;   // empty if allowed
  string monetization = 3;    // "svod", "tvod_rental", "tvod_purchase", "avod", "free"
  string package_id = 4;      // which package grants access
  int32 max_quality = 5;      // max resolution tier (e.g., 1080, 2160)
  bool offline_allowed = 6;   // can this be downloaded
  bool startover_allowed = 7; // for channel content
  bool catchup_allowed = 8;   // for channel content
  bool pvr_allowed = 9;       // can be recorded
}
```

**Caching strategy:**

```
                     ┌───────────┐
  Request ──────────>│ Redis     │── Hit ──> Return cached result
                     │ Cache     │
                     │ TTL: 60s  │
                     └─────┬─────┘
                           │ Miss
                     ┌─────▼─────┐
                     │ PostgreSQL│── Query entitlements
                     │           │
                     └─────┬─────┘
                           │
                     ┌─────▼─────┐
                     │ Cache     │── Store result (TTL: 60s)
                     │ Write     │
                     └─────┬─────┘
                           │
                     Return result
```

**Cache invalidation:** The Entitlement Service consumes `subscription.changed`, `tvod.purchased`, `promotion.activated`, and `promotion.expired` events from Kafka. On receiving these events, it invalidates the relevant Redis cache entries for the affected user. This ensures that entitlement changes propagate within seconds (Kafka + cache invalidation) rather than waiting for TTL expiry.

### 5.5 Entitlement Kafka Events

| Event | Trigger | Key Fields |
|-------|---------|------------|
| `entitlement.granted` | New subscription, TVOD purchase, promotion activation | user_id, package_id, source_type, source_id, market |
| `entitlement.revoked` | Subscription cancelled, TVOD expired, promotion ended | user_id, package_id, source_type, reason |
| `entitlement.checked` | Every entitlement check (for analytics) | user_id, content_type, content_id, result (allowed/denied), denial_reason, latency_ms |

---

## 6. Per-Service Entitlement Checks

Every service that controls access to content must verify entitlements. The checks are tailored to each service's specific requirements:

### 6.1 Live TV (PRD-001)

| Check Point | What is Verified | Denial Behavior |
|-------------|-----------------|-----------------|
| Channel tune | User has the channel in an active package | "This channel is not included in your subscription. Upgrade to [tier]." |
| HD/UHD access | User's tier supports the requested quality level | Downgrade to SD automatically, show "Upgrade for HD" prompt |
| Multi-audio | No additional check (included with channel) | N/A |
| Concurrent stream | Active session count vs limit | "You are already watching on [n] devices" |

### 6.2 TSTV — Start Over (PRD-002)

| Check Point | What is Verified | Denial Behavior |
|-------------|-----------------|-----------------|
| Start Over initiation | Channel package includes start-over rights + content has start-over flag | "Start Over is not available for this program" |
| Content rights | Per-program start-over eligibility (content provider restriction) | Same as above |

### 6.3 TSTV — Catch-Up (PRD-002)

| Check Point | What is Verified | Denial Behavior |
|-------------|-----------------|-----------------|
| Catch-up browse | Channel package includes catch-up rights | Programs without catch-up rights are hidden from the catch-up listing |
| Catch-up playback | Per-program catch-up eligibility + within 7-day window | "This program is not available for catch-up" or "This program has expired" |

### 6.4 Cloud PVR (PRD-003)

| Check Point | What is Verified | Denial Behavior |
|-------------|-----------------|-----------------|
| Schedule recording | User has PVR entitlement + channel is in an active package + quota available | "Cloud PVR is not included in your plan" or "Not enough storage. Delete recordings or upgrade." |
| Playback of recording | Recording exists + user owns it + content rights still valid | "This recording is no longer available" (if rights have lapsed) |
| Series link | Same as schedule recording, applied per episode | Same as above |

### 6.5 VOD / SVOD (PRD-004)

| Check Point | What is Verified | Denial Behavior |
|-------------|-----------------|-----------------|
| Browse/catalog | Content visibility filtered by territory + platform | Invisible content is simply not returned in API responses |
| SVOD playback | Title's packages intersect with user's packages | "Subscribe to [package] to watch this title" |
| TVOD playback | Valid rental (within 48h of first play) or purchase exists | "Rent for [price] or Buy for [price]" |
| AVOD playback | User is on AVOD tier or title is free-with-ads | Insert SSAI ad markers; no denial |
| Download | Title has offline rights flag + user's tier supports download | "Download is not available for this title" |

### 6.6 EPG (PRD-005)

| Check Point | What is Verified | Denial Behavior |
|-------------|-----------------|-----------------|
| EPG grid | Channels filtered by user's active packages | Channels outside user's subscription are either hidden or shown dimmed with "Upgrade" badge |
| Quick actions (Record, Start Over) | Same as respective service checks | Action button disabled with tooltip explaining why |

### 6.7 AI Services (PRD-007, PRD-008)

| Check Point | What is Verified | Denial Behavior |
|-------------|-----------------|-----------------|
| Recommendations | Only recommend content the user can access (or upsell) | Entitled content shown normally; non-entitled content shown with monetization label ("Available with Premium" or "Rent for $3.99") |
| Personalized EPG | Channel scoring limited to entitled channels (with optional preview of upgradeable channels) | Non-entitled channels scored lower and shown with upgrade indicator |
| AI PVR suggestions | Only suggest recording on entitled channels with PVR rights | Non-entitled suggestions filtered out before presentation |

---

## 7. Parental Controls & PIN Management

### 7.1 Parental Control Model

Parental controls operate at the profile level. Each profile has a content maturity rating that restricts what content is visible and playable.

**Rating system (UK-centric, adaptable per market):**

| Rating Level | Label | Allowed Content | Typical Age |
|-------------|-------|-----------------|-------------|
| 0 | Kids | U, PG rated content only | 0-7 |
| 1 | Older Kids | U, PG, 12 rated content | 8-12 |
| 2 | Teen | U, PG, 12, 15 rated content | 13-15 |
| 3 | Adult (default) | All content including 18-rated | 16+ |

### 7.2 PIN Protection

A 4-digit PIN protects access to restricted content and profile switching:

| Action | PIN Required | Configurable |
|--------|-------------|--------------|
| Switch to an adult profile from a kids profile | Always | No |
| Watch content above the active profile's rating | Always | No |
| Purchase TVOD content | Default: Yes | Yes (can disable per profile) |
| Modify parental control settings | Always | No |
| Delete recordings | Default: No | Yes |
| Access account settings | Always (on TV devices) | No |

**PIN flow:**
1. User attempts restricted action.
2. Client presents PIN entry overlay (4-digit numeric).
3. PIN is validated by the Profile Service (hashed comparison, bcrypt).
4. On success: action proceeds. A "PIN session" is created with a 30-minute TTL, so the user is not repeatedly prompted within a short period.
5. On failure: 3 attempts allowed. After 3 failures, PIN entry is locked for 15 minutes on that device.

**PIN storage:** PIN is hashed (bcrypt, cost factor 10) and stored in the Profile Service database. Each account has a single master PIN. Individual profiles do not have separate PINs.

### 7.3 Kids Profile

Kids profiles have additional restrictions beyond content rating:

- **Search restricted:** Conversational search and free-text search are limited to the kids catalog only.
- **Autoplay disabled:** No automatic next-episode or continuous play.
- **Recommendations scoped:** AI recommendations only draw from the kids catalog.
- **EPG filtered:** Only kid-appropriate channels are visible.
- **No purchases:** TVOD purchase buttons are hidden entirely.
- **Watch time limits (Phase 3):** Configurable daily watch time limit with gentle "time's up" messaging.
- **No data collection for ad targeting:** Kids profile viewing data is excluded from ad personalization (COPPA/GDPR compliance).

### 7.4 Content Rating Mapping

The platform normalizes content ratings from multiple sources into the internal rating system:

| Source | Ratings | Maps To Internal Level |
|--------|---------|----------------------|
| BBFC (UK) | U, PG, 12A, 12, 15, 18 | 0, 0, 1, 1, 2, 3 |
| FSK (DE) | 0, 6, 12, 16, 18 | 0, 0, 1, 2, 3 |
| MPAA (US) | G, PG, PG-13, R, NC-17 | 0, 0, 1, 2, 3 |
| TV Parental Guidelines (US) | TV-Y, TV-Y7, TV-G, TV-PG, TV-14, TV-MA | 0, 0, 0, 0, 2, 3 |

---

## 8. Guest & Trial Access

### 8.1 Guest Access (Unauthenticated)

Unauthenticated users can access a limited set of features:

| Feature | Access Level |
|---------|-------------|
| Browse catalog (limited) | Top-level categories, trending, editorial picks — no personalization |
| View EPG grid | Full grid visible, but no playback or recording actions |
| Search | Basic keyword search — no conversational search |
| View content details | Title metadata, trailers (free-to-air trailers only) |
| Playback | None — all play actions prompt "Sign up or log in" |
| Recommendations | Popularity-based only — no personalization |
| Download | None |

Guest sessions use a device-specific anonymous session token (JWT with `sub: anonymous`, 24-hour expiry). Browsing behavior is tracked with a device fingerprint for basic analytics but is not linked to any user account.

### 8.2 Trial Access

Free trials allow new users to experience the full platform:

| Trial Type | Duration | Access Level | Restrictions |
|-----------|----------|--------------|--------------|
| Standard Trial | 7 days | Standard tier (full) | Payment method required upfront; auto-converts to paid |
| Promotional Trial | 14-30 days | Varies per promotion | May not require payment upfront; marketing-driven |
| Day Pass | 24 hours | Premium tier | One-time payment; no recurring subscription |

**Trial rules:**
- One trial per payment method (prevents trial abuse).
- One trial per device (checked via device ID hash).
- Trial users are flagged in entitlements with `source_type: 'trial'`. When the trial expires, entitlements revert to free-tier.
- Kafka event `subscription.trial.started` and `subscription.trial.expired` trigger appropriate entitlement cache invalidation.

### 8.3 Promotional Entitlements

Promotions can grant temporary entitlements:

```json
{
  "promotion_id": "promo_weekend_movies",
  "name": "Free Movie Weekend",
  "packages": ["pkg_movies_premium"],
  "start_at": "2026-02-14T00:00:00Z",
  "end_at": "2026-02-16T23:59:59Z",
  "target_audience": "all_active_subscribers",
  "auto_activate": true
}
```

When `auto_activate` is true, the Promotion Service publishes `promotion.activated` events for all eligible users, and the Entitlement Service grants temporary access. When the promotion expires, `promotion.expired` events trigger entitlement revocation.

---

## 9. Single Sign-On (SSO)

### 9.1 Operator SSO (Phase 2)

For operator-branded (white-label) deployments, the platform supports federated authentication via the operator's identity provider (IdP).

**Supported protocols:**
- SAML 2.0 (for enterprise operators with existing SAML infrastructure)
- OpenID Connect (OIDC) (preferred for modern integrations)

**SSO flow (OIDC):**

1. User accesses the operator-branded app/website.
2. Client redirects to the operator's IdP authorization endpoint.
3. User authenticates with operator credentials.
4. IdP redirects back with authorization code.
5. Platform Auth Service exchanges code for ID token + access token from IdP.
6. Auth Service validates the ID token, extracts user identity claims.
7. Auth Service creates or links a platform user account (just-in-time provisioning).
8. Auth Service issues platform-specific access + refresh tokens.
9. Client proceeds with platform tokens (all subsequent API calls use platform tokens, not IdP tokens).

**Account linking:** If a user already has a platform account (email match), the SSO identity is linked to the existing account. If no account exists, one is created automatically with the subscriber's entitlements provisioned from the operator's subscriber management system.

### 9.2 Operator Entitlement Mapping

Operators manage their own subscription tiers and packages. The platform maps operator entitlements to internal packages:

```json
{
  "operator_id": "op_telecom_uk",
  "entitlement_mapping": [
    {
      "operator_package": "TV_BASIC",
      "platform_packages": ["pkg_base_channels", "pkg_basic_svod"]
    },
    {
      "operator_package": "TV_PREMIUM",
      "platform_packages": ["pkg_base_channels", "pkg_sports", "pkg_movies", "pkg_premium_svod", "pkg_pvr_100h"]
    },
    {
      "operator_package": "PVR_ADDON",
      "platform_packages": ["pkg_pvr_50h"]
    }
  ]
}
```

The operator subscriber management system pushes entitlement changes to the platform via a webhook API (`POST /operator/entitlements/update`). The platform translates these into internal entitlement grants/revocations.

---

## 10. Token Lifecycle

### 10.1 Token Types Summary

| Token | Format | Lifetime | Issued By | Validated By | Purpose |
|-------|--------|----------|-----------|-------------|---------|
| Access Token | JWT (RS256) | 15 minutes | Auth Service | BFF (stateless) | API authentication |
| Refresh Token | Opaque | 30-90 days | Auth Service | Auth Service (stateful) | Token renewal |
| CAT Token | JWT-like (ES256) | 5 minutes | Token Service | CDN edge | CDN media access |
| DRM License Token | DRM-specific | Session-based (streaming), 48h (offline) | DRM License Server | Player DRM module | Content decryption |
| Device Activation Code | 6-char alphanumeric | 10 minutes | Auth Service | Auth Service | TV device onboarding |
| PIN Session Token | Opaque | 30 minutes | Profile Service | Profile Service | Parental control bypass |

### 10.2 Key Rotation

| Key Type | Rotation Frequency | Overlap Period | Storage |
|----------|-------------------|----------------|---------|
| JWT signing key (RS256) | Monthly | 48 hours (both keys valid) | Vault |
| CAT signing key (ES256) | Weekly | 24 hours (both keys valid) | Vault + CDN edge cache |
| DRM content keys (live) | Daily per channel | 1 hour overlap | Vault + DRM backend |
| DRM content keys (VOD) | Per title (no rotation) | N/A | Vault + DRM backend |

### 10.3 Token Revocation

**Access tokens** cannot be revoked before expiry (they are stateless JWTs). The 15-minute lifetime is the mitigation. For immediate revocation (account compromise), the BFF maintains a short-lived deny list in Redis (user IDs whose tokens should be rejected regardless of signature validity). This list is populated by `auth.emergency.revoke` Kafka events.

**Refresh tokens** are revoked by marking them in the Auth Service database (`revoked_at` timestamp). Revoked tokens are rejected on the next refresh attempt.

---

## 11. Error Handling & Edge Cases

### 11.1 Error Responses

All authentication and entitlement errors follow a consistent response format:

```json
{
  "error": {
    "code": "ENTITLEMENT_DENIED",
    "message": "This content requires a Premium subscription.",
    "details": {
      "content_id": "vod_12345",
      "required_package": "pkg_premium_svod",
      "upgrade_options": [
        {
          "tier": "Premium",
          "price": "14.99",
          "currency": "GBP",
          "period": "monthly"
        }
      ]
    },
    "actions": [
      {
        "type": "upgrade",
        "label": "Upgrade to Premium",
        "url": "/account/upgrade?tier=premium"
      },
      {
        "type": "tvod",
        "label": "Rent for £3.99",
        "url": "/purchase/vod_12345?type=rental"
      }
    ]
  }
}
```

### 11.2 Error Codes

| Code | HTTP Status | Description | Client Action |
|------|-------------|-------------|---------------|
| `AUTH_INVALID_CREDENTIALS` | 401 | Wrong email/password | Show error, allow retry |
| `AUTH_ACCOUNT_LOCKED` | 423 | Too many failed attempts | Show lockout timer |
| `AUTH_TOKEN_EXPIRED` | 401 | Access token expired | Attempt refresh |
| `AUTH_REFRESH_EXPIRED` | 401 | Refresh token expired | Redirect to login |
| `AUTH_DEVICE_LIMIT` | 403 | Too many registered devices | Show device management |
| `ENTITLEMENT_DENIED` | 403 | Content not in user's packages | Show upgrade/purchase options |
| `STREAM_LIMIT_EXCEEDED` | 409 | Too many concurrent streams | Show active sessions, offer to stop one |
| `PARENTAL_PIN_REQUIRED` | 403 | Content above profile rating | Show PIN entry overlay |
| `PARENTAL_PIN_LOCKED` | 423 | Too many failed PIN attempts | Show lockout message with timer |
| `GEO_BLOCKED` | 403 | Content not available in user's region | Show "Not available in your region" |
| `CONTENT_EXPIRED` | 410 | TVOD rental expired or catch-up window passed | Show "Content no longer available" |

### 11.3 Edge Cases

**Subscription downgrade during playback:**
- User is watching Premium content when their subscription is downgraded to Basic.
- Behavior: Current playback session continues until natural end. New playback requests for Premium content are denied.
- The Entitlement Service processes `subscription.changed` events, invalidates cache, and subsequent entitlement checks reflect the new tier.

**TVOD rental window:**
- User rents a title but does not start watching within 30 days.
- Behavior: Rental expires. User is notified via push notification 48 hours before expiry: "Your rental of [title] expires in 2 days."

**Device offline during subscription change:**
- A TV device is offline when the user upgrades their subscription.
- Behavior: The device's cached entitlements (from the JWT `entitlements_hash`) will be stale until the access token is refreshed. Worst case: 15 minutes until the next token refresh brings the new entitlements. This is acceptable.

**Multi-market accounts:**
- A user moves from GB to DE.
- Behavior: The user's `market` field in the User Service is updated (manual process or admin override). Entitlements are re-evaluated against DE content rights. Some content may become unavailable while other content becomes available. A grace period of 30 days allows the user to finish watching content that is only available in GB.

---

## 12. AI Integration

### 12.1 AI-Enhanced Authentication

**Login anomaly detection (Phase 2):**
- An ML model trained on login patterns (time, device, location, IP) scores each login attempt with a risk score (0.0 to 1.0).
- Low risk (< 0.3): Normal authentication.
- Medium risk (0.3-0.7): Step-up authentication required (email verification code).
- High risk (> 0.7): Account flagged, session created but entitlements restricted until user verifies identity.
- The model learns from confirmed fraud cases and legitimate usage patterns.

**Account sharing detection (Phase 3):**
- The platform monitors viewing patterns for indicators of credential sharing beyond the household:
  - Simultaneous sessions from geographically distant locations.
  - Unusually high number of unique IP addresses per account per month.
  - Viewing patterns inconsistent with a single household (e.g., different language preferences from different locations).
- Detection is informational initially (dashboard metric). Phase 4 may introduce enforcement (e.g., requiring extra authentication from new locations, or prompting users to add extra members).

### 12.2 AI-Enhanced Entitlements

**Churn-risk entitlement boost (Phase 3):**
- When the churn prediction model (PRD-008) identifies a user as high-risk, the platform can automatically grant temporary promotional entitlements (e.g., 7-day access to a premium package) to re-engage the user.
- This is controlled by the retention team via a campaign management system that sets rules: which segments, which packages, what duration, what cap.

**Upsell personalization:**
- When a user hits an entitlement wall (denied access to premium content), the AI selects the most relevant upgrade message based on the user's viewing history and genre preferences.
- Example: A user who primarily watches sports sees "Upgrade to Premium for all live sports channels" rather than a generic "Upgrade to Premium."

---

*This document defines the authentication and entitlement architecture that underpins all platform services. All PRDs should reference this document for auth flows, entitlement checks, and access control patterns. Changes to the entitlement model require coordination across the Entitlement Service, Subscription Service, and all consuming services (Playback, Recording, Catalog, EPG, Recommendation).*
