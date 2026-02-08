# Content Security
## Cross-Cutting Concerns — AI-Native OTT Streaming Platform

**Document ID:** XC-003
**Version:** 1.0
**Date:** 2026-02-08
**Status:** Draft
**Author:** Integration Analyst Agent
**References:** ARCH-001, VIS-001, PRD-001 through PRD-008
**Audience:** Security Engineers, Backend Engineers, Client Engineers, Content Operations, Legal/Compliance

---

## Table of Contents

1. [Overview](#1-overview)
2. [Multi-DRM Architecture](#2-multi-drm-architecture)
3. [DRM Per-Platform Implementation](#3-drm-per-platform-implementation)
4. [HDCP Enforcement](#4-hdcp-enforcement)
5. [Content Encryption (CBCS)](#5-content-encryption-cbcs)
6. [Key Management](#6-key-management)
7. [Forensic Watermarking](#7-forensic-watermarking)
8. [Anti-Piracy Monitoring](#8-anti-piracy-monitoring)
9. [Geo-Blocking & Territory Enforcement](#9-geo-blocking--territory-enforcement)
10. [CDN Token Security (CAT)](#10-cdn-token-security-cat)
11. [Content Rights Across Services](#11-content-rights-across-services)
12. [Security Incident Response](#12-security-incident-response)

---

## 1. Overview

Content security is the foundation of every content licensing agreement. Failure to protect premium content results in license revocations, financial penalties, and loss of content partnerships. This document defines the layered security strategy that protects content from ingest to playback across all platform services and client devices.

### Security Layers

```
Layer 1: Access Control (Authentication + Entitlement)
    └── Who is allowed to watch this content?

Layer 2: Encryption (CBCS + Multi-DRM)
    └── Content is encrypted at rest and in transit

Layer 3: Device Security (Widevine/FairPlay/PlayReady levels)
    └── Content decryption in hardware-secured environments

Layer 4: Output Protection (HDCP)
    └── Encrypted link between device and display

Layer 5: Transport Security (CAT + TLS)
    └── Authorized CDN access with short-lived tokens

Layer 6: Forensic Watermarking
    └── Trace leaked content back to the source session

Layer 7: Monitoring & Response (Anti-piracy)
    └── Detect and respond to unauthorized distribution
```

### Design Principles

- **Defense in depth.** No single layer is considered sufficient. A breach of one layer (e.g., CDN token compromise) does not expose content because encryption and DRM still protect it.
- **Standards-based.** Use industry-standard protocols (CPIX, CBCS, CENC, CAT) rather than proprietary solutions.
- **Content-tiered security.** Not all content requires the same protection level. Premium content (early-window movies, live sports) gets the highest protection (L1 only, HDCP required, watermarked). Older catalog content can be served with lower security levels.
- **Transparent to the user.** Security should be invisible. Users should never see DRM errors, HDCP failures, or token issues under normal operation. Graceful degradation (resolution reduction) is preferred over playback failure.

---

## 2. Multi-DRM Architecture

### 2.1 DRM Systems

The platform uses three DRM systems to cover all target client platforms:

| DRM System | Vendor | Platforms | License Server |
|-----------|--------|-----------|----------------|
| **Widevine** | Google | Android TV, Android Mobile, Web (Chrome/Firefox/Edge), Samsung Tizen, LG webOS, Chromecast | Widevine Cloud or self-hosted Widevine Proxy |
| **FairPlay** | Apple | Apple TV (tvOS), iOS, Web (Safari) | Self-hosted FairPlay Key Server Module (KSM) |
| **PlayReady** | Microsoft | Xbox (future), Windows apps (future), some STBs | PlayReady License Server (Azure-hosted or self-hosted) |

### 2.2 CPIX Workflow

The Content Protection Information Exchange (CPIX) standard enables a single encryption workflow that serves all three DRM systems.

```
                    ┌─────────────────────────┐
                    │   Key Management Service │
                    │   (Platform-owned)        │
                    └──────────┬──────────────┘
                               │
                    ┌──────────▼──────────────┐
                    │   CPIX Document          │
                    │   - Content Key ID       │
                    │   - Content Key (encrypted│
                    │     per DRM system)       │
                    │   - DRM System configs    │
                    │   - Usage rules           │
                    └──────────┬──────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
     ┌────────▼───────┐┌──────▼──────┐┌────────▼───────┐
     │  Widevine      ││  FairPlay    ││  PlayReady     │
     │  Cloud API     ││  KSM         ││  License Server│
     │                ││              ││                │
     │  Registers     ││  Registers   ││  Registers     │
     │  content key   ││  content key ││  content key   │
     └────────────────┘└──────────────┘└────────────────┘
```

**CPIX Document Generation Flow:**

1. Content Ingest Service triggers key generation for new content.
2. Key Management Service (KMS) generates a random AES-128 content key.
3. KMS creates a CPIX 2.3 document containing:
   - `ContentKey`: The encryption key (encrypted to each DRM system's public key).
   - `DRMSystem` entries: Widevine PSSH data, FairPlay key delivery data, PlayReady PSSH data.
   - `UsageRule`: Output protection requirements (HDCP level), license duration, offline permissions.
4. CPIX document is sent to the encoding pipeline, which uses the content key for encryption.
5. CPIX document is cached (TTL: 24h for VOD, 1h for live) and used by the manifest proxy to inject PSSH boxes into manifests.

### 2.3 License Acquisition Flow

```
Client Player                    BFF                  DRM License Server
     │                            │                          │
     │  1. Parse manifest, extract│                          │
     │     PSSH / key ID          │                          │
     │                            │                          │
     │  2. Generate license       │                          │
     │     request (challenge)    │                          │
     │                            │                          │
     │  POST /drm/license         │                          │
     │  {challenge, key_id,       │                          │
     │   drm_type, session_token} │                          │
     │───────────────────────────>│                          │
     │                            │                          │
     │                            │  3. Validate session     │
     │                            │     token, check         │
     │                            │     entitlements         │
     │                            │                          │
     │                            │  4. Forward challenge     │
     │                            │     + usage rules        │
     │                            │────────────────────────>│
     │                            │                          │
     │                            │  5. License response     │
     │                            │     (encrypted to        │
     │                            │      device)             │
     │                            │<────────────────────────│
     │                            │                          │
     │  6. License response       │                          │
     │<───────────────────────────│                          │
     │                            │                          │
     │  7. Decrypt content key    │                          │
     │     in secure environment  │                          │
     │     (TEE / CDM)            │                          │
     │                            │                          │
     │  8. Begin decryption and   │                          │
     │     playback               │                          │
```

The BFF acts as a DRM proxy. This provides:
- **Entitlement verification** before license issuance (the BFF checks entitlements, not the DRM server).
- **Usage rule injection** — the BFF applies platform-specific rules (max resolution, offline duration, HDCP requirements) based on the content tier and the user's subscription.
- **Logging** — every license request is logged for audit and anti-piracy purposes.

---

## 3. DRM Per-Platform Implementation

### 3.1 Widevine (Google)

**Platforms:** Android TV, Android Mobile, Web (Chrome/Firefox/Edge), Samsung Tizen, LG webOS, Chromecast.

**Security Levels:**

| Level | Environment | Max Resolution (Premium) | Max Resolution (Standard) | Platforms |
|-------|-----------|------------------------|--------------------------|-----------|
| **L1** | Hardware TEE (Trusted Execution Environment). Key processing and content decryption occur in hardware-secured memory. | 4K HDR | 4K HDR | Android TV (certified), Samsung Tizen, LG webOS, Chromecast, Android Mobile (certified devices) |
| **L2** | Hardware key processing, software decryption. | 1080p | 1080p | Some Android devices, some STBs |
| **L3** | Software-only. No hardware security. | 480p (premium) / 720p (standard) | 720p | Web (Chrome/Firefox/Edge without hardware security), older Android devices |

**Implementation:**
- Android: Widevine CDM is built into the OS. ExoPlayer/Media3 handles license acquisition via `DefaultDrmSessionManager`.
- Web: EME (Encrypted Media Extensions) API in the browser provides access to the Widevine CDM. Shaka Player handles EME integration.
- Smart TVs: Tizen and webOS use their native Widevine modules. The Shaka Player web layer communicates with the native DRM module via platform-specific bridge APIs.

**L1 vs L3 content policy:**
- Content owners may restrict premium content (early-window movies, 4K HDR, live sports premium) to L1 devices only.
- The platform maintains a `content_security_tier` field per title: `premium` (L1 required), `standard` (L1 or L3).
- When a L3 device requests premium content, the license server issues a license with max resolution 480p, and the BFF returns a manifest with only sub-HD profiles.

### 3.2 FairPlay (Apple)

**Platforms:** Apple TV (tvOS), iOS (iPhone/iPad), Web (Safari).

**Security characteristics:**
- All Apple devices use hardware-based content protection (Secure Enclave).
- FairPlay does not have the L1/L2/L3 distinction — all Apple devices are considered hardware-secured.
- FairPlay uses a different key delivery mechanism: the FairPlay Streaming Key Server Module (KSM) rather than PSSH boxes.

**Implementation:**
- Apple TV / iOS: AVPlayer and AVContentKeySession handle FairPlay license acquisition natively.
- Safari: EME API with the `com.apple.fps` key system. Shaka Player handles the FairPlay-specific certificate and license exchange.

**FairPlay-specific flow:**
1. Player requests the FairPlay server certificate from the platform (cached locally after first fetch).
2. Player generates a Server Playback Context (SPC) using the certificate and content key ID.
3. SPC is sent to the platform's FairPlay license endpoint (via BFF).
4. BFF validates entitlements, forwards SPC to the FairPlay KSM.
5. KSM returns a Content Key Context (CKC) containing the encrypted content key.
6. Player uses CKC to decrypt content.

### 3.3 PlayReady (Microsoft)

**Platforms:** Xbox (future Phase 3), Windows native apps (future), some operator STBs.

**Security levels:**
- **SL3000:** Hardware-protected. Required for premium content.
- **SL2000:** Software-based. Standard content only.

**Current scope:** PlayReady is included in the CPIX workflow for future compatibility and for operator STBs that use PlayReady. Phase 1 focuses on Widevine and FairPlay. PlayReady license server is provisioned but low-traffic.

---

## 4. HDCP Enforcement

High-bandwidth Digital Content Protection (HDCP) protects the link between the playback device and the display (TV/monitor).

### 4.1 HDCP Requirements Per Content Tier

| Content Tier | HDCP Requirement | Enforcement Point |
|-------------|-----------------|-------------------|
| **Premium 4K HDR** | HDCP 2.2 mandatory | DRM license usage rules (output restriction) |
| **Premium HD (1080p)** | HDCP 1.4 mandatory | DRM license usage rules |
| **Standard HD (1080p)** | HDCP 1.4 preferred (fail open to 720p) | DRM license usage rules with fallback |
| **Standard SD (≤720p)** | No HDCP required | N/A |
| **Mobile (phone/tablet)** | N/A (no external output) | Screen capture protection (OS-level) |

### 4.2 HDCP Failure Handling

When a device cannot establish the required HDCP level:

1. **Widevine L1:** The CDM reports HDCP unavailable. The DRM proxy issues a license with reduced max resolution (1080p → 720p, or 4K → 1080p).
2. **FairPlay:** AVPlayer automatically handles HDCP negotiation. If HDCP 2.2 is unavailable, the system falls back to HDCP 1.4. If neither is available, resolution is capped.
3. **User messaging:** "This content requires a secure display connection. Playback quality has been reduced. Check your HDMI cable connection."
4. **No playback block:** The platform prefers resolution downgrade over playback refusal. Content owners who mandate HDCP with no fallback are accommodated as a per-title policy exception.

### 4.3 Screen Capture Protection

- **iOS:** `isExternalPlaybackActive` and `preventsDisplaySleepDuringVideoPlayback` flags. AirPlay Mirroring is blocked for protected content (FairPlay handles this natively).
- **Android:** `FLAG_SECURE` on the player surface prevents screenshots and screen recording. MediaDRM `SECURITY_LEVEL_HW_SECURE_ALL` ensures hardware decryption.
- **Web:** The CDM (Widevine/FairPlay) prevents screen capture of the video layer in supported browsers. There is no reliable way to block screen capture on all web configurations — this is a known limitation accepted by content owners.

---

## 5. Content Encryption (CBCS)

### 5.1 Encryption Mode

The platform uses **CBCS** (Common Encryption — CBC mode with Subsample pattern encryption) as defined in ISO 23001-7:2016.

**Why CBCS over CTR (CENC):**
- CBCS is required by FairPlay (Apple). Using CBCS for all platforms eliminates the need for dual encryption.
- CBCS encrypts only a subset of each sample (1:9 pattern — 1 encrypted block for every 9 clear blocks). This reduces decryption CPU load by ~10x compared to CTR, which is important for lower-powered devices (Smart TVs, STBs).
- All modern DRM CDMs (Widevine, FairPlay, PlayReady) support CBCS.

### 5.2 Encryption Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| Mode | CBCS | Subsample pattern encryption |
| Algorithm | AES-128 CBC | Per CBCS specification |
| Key length | 128 bits | Industry standard for video content |
| IV (Initialization Vector) | Constant per sample (derived from sample number) | Per CBCS specification |
| Pattern | 1:9 (crypt:skip) | 1 block encrypted, 9 blocks clear, repeating |
| Key scope (VOD) | Per-title (all segments of a title share one content key) | Simplifies key management; acceptable for VOD |
| Key scope (Live) | Per-channel per 24-hour period | Key rotation for live security |

### 5.3 Encryption in the Pipeline

**VOD:**
1. Content Ingest Service requests content key from Key Management Service.
2. Encoding Pipeline encodes mezzanine to ABR ladder (unencrypted).
3. Packaging step (Shaka Packager) encrypts CMAF segments using the content key (CBCS mode).
4. Encrypted segments are stored on S3 (origin).
5. Manifests (HLS .m3u8 / DASH .mpd) include DRM signaling (PSSH boxes for Widevine/PlayReady, `EXT-X-KEY` with `skd://` URI for FairPlay).

**Live:**
1. Key Management Service pre-generates content keys for each channel for the next 48 hours (key per 24-hour period with 1-hour overlap).
2. Live encoder produces unencrypted CMAF segments.
3. USP (Unified Streaming Platform) encrypts segments in real-time using the active content key.
4. Manifests are generated with current-period DRM signaling.
5. At key rotation boundary: new segments use the new key, manifests reference both keys for the overlap period. Clients acquire the new license seamlessly during the overlap.

---

## 6. Key Management

### 6.1 Architecture

```
                    ┌───────────────────────┐
                    │  HashiCorp Vault       │
                    │  (Key Encryption Keys) │
                    │  KEK stored in Vault   │
                    │  Auto-unseal via KMS   │
                    └──────────┬────────────┘
                               │
                    ┌──────────▼────────────┐
                    │  Key Management Service│
                    │  (Platform-owned)       │
                    │  - Generates content   │
                    │    keys (AES-128)      │
                    │  - Creates CPIX docs   │
                    │  - Registers with DRM  │
                    │    backends             │
                    │  - Caches active keys   │
                    └──────────┬────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
     ┌────────▼───────┐┌──────▼──────┐┌────────▼───────┐
     │  Widevine      ││  FairPlay    ││  PlayReady     │
     │  Cloud         ││  KSM         ││  License Server│
     └────────────────┘└──────────────┘└────────────────┘
```

### 6.2 Key Hierarchy

| Key Type | Purpose | Storage | Rotation |
|----------|---------|---------|----------|
| **Key Encryption Key (KEK)** | Encrypts content keys at rest | HashiCorp Vault (hardware-backed via KMS auto-unseal) | Annually |
| **Content Key (CEK)** | Encrypts media segments (AES-128 CBCS) | Vault (encrypted by KEK), registered with DRM backends | Per-title (VOD), daily (live) |
| **JWT Signing Key** | Signs access tokens (RS256) | Vault | Monthly |
| **CAT Signing Key** | Signs CDN access tokens (ES256) | Vault + CDN edge cache | Weekly |
| **DRM Transport Key** | Encrypts content keys in transit to DRM backends | Per DRM system (system-managed) | Per DRM system schedule |

### 6.3 Key Storage Security

- Content keys are **never** stored in application databases, configuration files, or environment variables.
- Content keys are stored in Vault's transit engine. The Key Management Service requests decryption of the content key only when needed (CPIX document generation, live packaging).
- Vault access is authenticated via Kubernetes service account tokens (Vault Agent sidecar). Only the Key Management Service and the live packaging service have policies permitting access to content keys.
- All key access is audit-logged in Vault's audit backend (shipped to the security SIEM).

### 6.4 Key Lifecycle

**VOD content key lifecycle:**
1. **Generation:** On content ingest, Key Management Service generates a random AES-128 key.
2. **Registration:** Key is registered with Widevine Cloud, FairPlay KSM, and PlayReady License Server via CPIX.
3. **Usage:** Shaka Packager uses the key during encoding. DRM license servers use the key for license issuance.
4. **Retention:** Key is retained for the lifetime of the content in the catalog. Archived to cold storage (Vault) when content is removed.
5. **Deletion:** Key is permanently deleted 90 days after content removal from all territories.

**Live content key lifecycle:**
1. **Pre-generation:** Keys for the next 48 hours are generated and registered daily.
2. **Activation:** The current-period key is used by USP for real-time encryption.
3. **Rotation:** At the 24-hour boundary, the new key becomes active. The old key remains valid for 1 hour (overlap) to allow client license refresh.
4. **Expiry:** Old live keys are retained for 8 days (covers the 7-day catch-up window + 1 day buffer).
5. **Deletion:** Expired live keys are purged from active storage but retained in cold storage for forensic purposes (1 year).

---

## 7. Forensic Watermarking

### 7.1 Strategy

Forensic watermarking embeds an invisible, unique identifier into the video stream that traces leaked content back to the specific session (and therefore the specific user) that captured it.

### 7.2 A/B Watermarking (CDN-Level)

**How it works:**

1. Two slightly different encodes of the same content are created during encoding: Variant A and Variant B. The visual difference is imperceptible to viewers (sub-pixel luminance shifts, micro-timing adjustments in frame presentation).
2. Both variants are stored as separate segment files on the origin.
3. When a user starts playback, the CDN Routing Service assigns a watermark pattern — a sequence of A/B selections for each segment (e.g., AABBABBA...).
4. The pattern is derived from a hash of the session ID, creating a unique per-session watermark.
5. The CDN uses the CAT token's session ID to select the correct variant for each segment.

```
Segment 1: A    Segment 2: A    Segment 3: B    Segment 4: B
Segment 5: A    Segment 6: B    Segment 7: B    Segment 8: A

Pattern: AABBAABA → maps to session sess_x1y2z3 → maps to user usr_a1b2c3
```

### 7.3 Watermark Detection

When pirated content is discovered:

1. The anti-piracy team obtains a sample of the leaked content.
2. The sample is analyzed to extract the A/B pattern from each segment.
3. The pattern is looked up in the watermark database (session ID → user ID).
4. The identified user account is flagged for investigation.

**Detection accuracy:** A minimum of 30 seconds of contiguous content is needed for reliable pattern extraction (>99% confidence with 60 segments at 0.5-second granularity).

### 7.4 Watermarking Scope

| Content Category | Watermarked | Phase | Storage Overhead |
|-----------------|-------------|-------|-----------------|
| Premium VOD (early window, TVOD) | Yes | 2 | ~2x segment storage |
| Live sports (premium events) | Yes | 2 | ~2x segment storage |
| Standard SVOD catalog | No (Phase 2), Yes (Phase 3) | 3 | ~2x segment storage |
| Catch-up / TSTV | No (uses live watermark if live was watermarked) | 2 | Minimal |
| Cloud PVR recordings | No (recording points to live/catch-up segments) | N/A | None |
| Free/AVOD content | No | N/A | None |

**Storage impact:** A/B watermarking doubles the segment storage for watermarked content. For Phase 1 (no watermarking), this is zero. At full watermarking (Phase 3), storage increases by ~80% (not all content is watermarked; audio-only segments and lower-resolution profiles may share a single variant).

### 7.5 Alternative: Server-Side Watermarking (Phase 4)

For Phase 4, the platform may transition from A/B segment-based watermarking to real-time server-side watermarking, where the watermark is applied per-session in the packaging/manifest layer. This eliminates the 2x storage overhead but requires integration with a third-party watermarking solution (e.g., Irdeto, NexGuard, or Nagra). This is captured as a future architecture decision.

---

## 8. Anti-Piracy Monitoring

### 8.1 Detection Channels

| Channel | Method | Coverage | Phase |
|---------|--------|----------|-------|
| **Automated web crawling** | Bots scan known piracy sites, torrent trackers, IPTV aggregators for platform content | Public internet | 2 |
| **Fingerprint matching** | Audio/video fingerprinting of content found online compared against the platform catalog | Public internet, social media | 2 |
| **Watermark extraction** | When pirated content is found, extract the A/B watermark pattern to identify the source session | Leaked content samples | 2 |
| **CDN token abuse detection** | Monitor for patterns indicating token sharing: same token used from multiple IPs, tokens used after expiry attempts | CDN logs | 1 |
| **Account sharing detection** | ML model detects unusual account usage patterns (geographic spread, concurrent pattern) | Internal analytics | 3 |
| **DMCA/takedown response** | Automated DMCA takedown notices for content found on hosting platforms, social media | Public internet | 2 |

### 8.2 Response Actions

| Detection | Automated Response | Manual Response |
|-----------|-------------------|-----------------|
| CDN token abuse | Token revoked, session terminated, alert to security team | Account investigation |
| Account sharing (high confidence) | Warning notification to user, step-up authentication on next login | Subscription review, potential enforcement |
| Pirated content found (no watermark) | Automated DMCA takedown notice | Investigation to identify source |
| Pirated content found (watermark extracted) | Automated DMCA takedown, source account flagged | Account suspension, legal review, content owner notification |
| Credential stuffing detected | Rate limiting, CAPTCHA, account lock | Affected accounts forced password reset |

### 8.3 Piracy Metrics

| Metric | Measurement | Target | Reporting |
|--------|------------|--------|-----------|
| Time to detect pirated content | From upload to detection | < 24 hours | Weekly security report |
| Time to takedown | From detection to content removal | < 48 hours (US), < 72 hours (EU) | Weekly security report |
| Watermark extraction success rate | % of detected piracy samples where watermark is successfully extracted | > 90% | Monthly security report |
| CDN token abuse incidents | Number of detected token abuse events per month | < 100 | Monthly security report |

---

## 9. Geo-Blocking & Territory Enforcement

### 9.1 Content Territorial Rights

Content availability is defined per territory (ISO 3166-1 country codes). The Catalog Service manages availability windows per content per territory:

```json
{
  "content_id": "vod_12345",
  "title": "Northern Lights",
  "availability": [
    {
      "territory": "GB",
      "start_at": "2026-01-15T00:00:00Z",
      "end_at": "2027-01-14T23:59:59Z",
      "monetization": ["svod"],
      "platforms": ["all"]
    },
    {
      "territory": "DE",
      "start_at": "2026-03-01T00:00:00Z",
      "end_at": "2027-02-28T23:59:59Z",
      "monetization": ["tvod_rental", "tvod_purchase"],
      "platforms": ["all"]
    },
    {
      "territory": "FR",
      "start_at": null,
      "end_at": null,
      "monetization": [],
      "platforms": [],
      "note": "No rights — content invisible in FR"
    }
  ]
}
```

### 9.2 Enforcement Points

| Enforcement Point | Mechanism | Accuracy |
|-------------------|-----------|----------|
| **User account registration** | Market is set based on billing address and IP geolocation at registration | High (billing address) |
| **Catalog API (BFF)** | BFF filters catalog responses by user's market. Content without rights in the user's market is excluded from API responses entirely. | High (prevents discovery) |
| **Entitlement Service** | Entitlement check includes market parameter. Even if a client bypasses BFF filtering, the entitlement check will deny access. | High (prevents playback) |
| **CDN token (CAT)** | CAT token includes an optional IP restriction claim. CDN edge validates the requesting IP against the token. | Medium (IP can be spoofed/VPN) |
| **DRM license server** | License server can enforce geo-restriction as a usage rule (IP check at license issuance). | Medium |

### 9.3 VPN Detection

VPN usage is a common method to circumvent geo-blocking:

| Detection Method | Mechanism | Accuracy | Action |
|-----------------|-----------|----------|--------|
| **IP reputation database** | MaxMind GeoIP2 includes VPN/proxy/datacenter classification | Good (~85% of commercial VPNs detected) | Block or warn |
| **IP-to-ASN mismatch** | IP geolocates to one country but ASN is registered in another | Medium | Flag for secondary check |
| **DNS leak detection** | Compare DNS resolver IP location with client IP location | Low (client cooperation needed) | Informational |
| **Behavioral analysis** | User's IP rapidly changes between countries (unlikely for legitimate use) | Medium | Flag for investigation |

**VPN enforcement policy:**
- Phase 1: Best-effort VPN detection via IP reputation. Known VPN IPs result in a warning: "We detected you may be using a VPN. Some content may not be available."
- Phase 2: Strict enforcement for premium content (live sports with exclusive territorial rights). Known VPN IPs are denied access to geo-restricted premium content.
- No blanket VPN block (some users have legitimate reasons). Detection accuracy is tracked and false positive rate monitored.

### 9.4 Traveling Users

When a user travels to a different country:

- **EU Portability Regulation (EU 2017/1128):** EU subscribers traveling within the EU must retain access to their home-market content for up to 90 days. The platform detects temporary travel (IP in a different EU country, but market is still home market) and maintains home-market entitlements.
- **Non-EU travel:** Content availability switches to the visited country's catalog. Some content may become unavailable. A user-friendly message is shown: "Some content is not available in your current location."
- **Market override:** The user's registered market (billing address) is the primary determinant. Temporary IP-based location changes do not change the user's market.

---

## 10. CDN Token Security (CAT)

### 10.1 Common Access Token (CAT) Overview

CAT provides CDN-agnostic, token-based authorization for media segment and manifest requests. It replaces CDN-specific token mechanisms with a standardized approach.

### 10.2 Token Structure

```json
{
  "header": {
    "alg": "ES256",
    "typ": "CATv1",
    "kid": "cat-key-2026-02-w1"
  },
  "payload": {
    "sub": "sess_a1b2c3d4",
    "iss": "token.platform.example.com",
    "iat": 1707400800,
    "exp": 1707401100,
    "cdnid": "akamai",
    "paths": [
      "/live/ch-*/",
      "/vod/title_12345/"
    ],
    "ip": "203.0.113.0/24",
    "ua": "sha256:user_agent_hash"
  }
}
```

| Claim | Purpose | Validation |
|-------|---------|------------|
| `sub` | Session ID — links token to a playback session | Logged for audit; not validated at CDN edge (opaque to CDN) |
| `iss` | Token issuer | CDN validates against configured issuer |
| `iat` | Issued-at timestamp | CDN rejects tokens with `iat` in the future |
| `exp` | Expiry timestamp | CDN rejects expired tokens |
| `cdnid` | Target CDN identifier | CDN validates that the token is for itself |
| `paths` | Allowed path patterns (regex) | CDN validates request path matches one of the patterns |
| `ip` | Client IP prefix restriction (optional) | CDN validates requesting IP falls within the range |
| `ua` | User-Agent hash (optional) | CDN validates hash matches the requesting client's UA |

### 10.3 Token Lifecycle

```
Client                Token Service          CDN Edge
  │                       │                     │
  │  1. Playback start    │                     │
  │  Request CAT token    │                     │
  │──────────────────────>│                     │
  │                       │                     │
  │  2. Token issued      │                     │
  │  (5-min lifetime)     │                     │
  │<──────────────────────│                     │
  │                       │                     │
  │  3. Request segment   │                     │
  │  with CAT token       │                     │
  │─────────────────────────────────────────── >│
  │                       │                     │
  │                       │  4. Validate token  │
  │                       │     (local, no      │
  │                       │      callback)      │
  │                       │                     │
  │  5. Segment response  │                     │
  │< ───────────────────────────────────────────│
  │                       │                     │
  │  ... (every 4 min)    │                     │
  │                       │                     │
  │  6. Refresh token     │                     │
  │──────────────────────>│                     │
  │                       │                     │
  │  7. New token issued  │                     │
  │<──────────────────────│                     │
```

### 10.4 Security Properties

- **Short-lived:** 5-minute lifetime limits the window of token theft exploitation.
- **Path-restricted:** Token is valid only for specific content paths. A token for `/vod/title_12345/` cannot access `/live/ch-001/`.
- **CDN-restricted:** Token is valid only for the designated CDN. Cannot be replayed against a different CDN.
- **IP-restricted (optional):** For fixed-line connections, the token includes an IP prefix restriction. Disabled for mobile (IP changes frequently on cellular).
- **No origin callback:** CDN validates tokens locally using cached signing keys. No performance penalty from token validation.
- **Key rotation:** Signing keys are rotated weekly. CDN edge caches both current and previous key for seamless rotation. The overlap period is 24 hours.

### 10.5 Token Abuse Detection

The Token Service monitors for abuse patterns:

| Pattern | Detection | Response |
|---------|-----------|----------|
| Same token used from multiple IPs | CDN access logs analyzed (batch, every 5 min) | Token revoked (via CDN-specific invalidation API), session flagged |
| Token reuse after expiry attempts | CDN 403 response logs | Alert (may indicate a scraping bot) |
| Abnormal token request rate | Token Service rate limiting (> 2 requests/min per session) | Rate limited; session flagged if persistent |
| Token used from VPN/proxy IP | IP reputation check at Token Service | Optional: deny token issuance for restricted content |

---

## 11. Content Rights Across Services

### 11.1 Rights Matrix

Content rights determine which platform services can use a piece of content. These rights are defined per-title (or per-channel) and come from content licensing agreements:

| Right | Description | Services Affected | Controlled By |
|-------|-------------|-------------------|---------------|
| **Linear broadcast** | Channel can be broadcast live | Live TV (PRD-001) | Channel licensing agreement |
| **Start-over** | Currently airing program can be restarted | TSTV Start Over (PRD-002) | Per-channel or per-program flag |
| **Catch-up** | Previously aired program available for 7 days | TSTV Catch-Up (PRD-002) | Per-channel or per-program flag + duration |
| **Network PVR** | Program can be recorded to Cloud PVR | Cloud PVR (PRD-003) | Per-channel flag (some channels restrict PVR) |
| **VOD (SVOD)** | Title included in subscription catalog | VOD (PRD-004) | Per-title licensing window |
| **VOD (TVOD)** | Title available for rent/purchase | VOD (PRD-004) | Per-title licensing window |
| **Download (offline)** | Title can be downloaded for offline viewing | Multi-Client (PRD-006) | Per-title flag (subset of SVOD) |
| **Ad-supported (AVOD)** | Title available with ads at reduced/free price | VOD (PRD-004) | Per-title flag |
| **Territorial** | Content available in specific territories | All services | Per-territory licensing window |
| **Platform** | Content available on specific device types | Multi-Client (PRD-006) | Per-platform restriction (rare) |
| **Quality tier** | Maximum resolution/codec for content | All playback services | Per-license or per-device DRM enforcement |

### 11.2 Rights Data Flow

```
Content Provider (license agreement)
        │
        ▼
Content Operations (manual entry + automated ingest)
        │
        ▼
Catalog Service (content_rights table)
        │
        ├──── Entitlement Service (runtime check)
        │        └── Per-request: "Can user X access content Y via service Z?"
        │
        ├──── EPG Service (schedule enrichment)
        │        └── Per-program: start_over_allowed, catchup_allowed, pvr_allowed
        │
        ├──── Recording Service (schedule validation)
        │        └── Per-schedule: Is PVR allowed for this channel/program?
        │
        ├──── Recommendation Service (filter)
        │        └── Only recommend content the user can access (or upsell)
        │
        └──── BFF (catalog filtering)
                 └── Content without rights is excluded from API responses
```

### 11.3 Rights Change Propagation

When content rights change (e.g., a catch-up window expires, a VOD title is removed):

1. Content Operations updates the Catalog Service (or an automated rights management system triggers the update).
2. Catalog Service publishes `catalog.availability.changed` event to Kafka.
3. Consumers:
   - **Entitlement Service:** Invalidates cached entitlements for affected content.
   - **EPG Service:** Updates program flags (start-over, catch-up indicators).
   - **Recording Service:** For PVR rights revocation: existing recordings remain playable (typically under the original license) but new recordings cannot be scheduled.
   - **Search/Recommendation:** Affected content is removed from search index and recommendation candidate pool.
   - **BFF cache:** Invalidated so next API response reflects the change.

**Propagation latency target:** < 5 minutes from rights change to all services reflecting the update.

---

## 12. Security Incident Response

### 12.1 Content Security Incident Categories

| Category | Severity | Example | Response SLA |
|----------|----------|---------|-------------|
| **P1 — Active content leak** | Critical | Platform content found on piracy sites with active distribution | 1 hour (begin takedown), 24 hours (identify source) |
| **P2 — DRM compromise** | Critical | Evidence of DRM key extraction or CDM bypass | 1 hour (assess scope), 4 hours (mitigation) |
| **P3 — Token/auth abuse** | High | CAT token sharing at scale, credential stuffing attack | 4 hours (begin mitigation) |
| **P4 — Geo-blocking bypass** | Medium | Systematic VPN usage for restricted content | 24 hours (assess), 1 week (policy update) |
| **P5 — Credential theft** | High | User credentials exposed in a third-party breach | 4 hours (force password reset for affected accounts) |

### 12.2 Incident Response Playbook

**For P1 (Active Content Leak):**

1. **Detect:** Anti-piracy monitoring identifies platform content on unauthorized sites.
2. **Assess:** Determine content scope (single title or catalog-wide), distribution channel (torrent, IPTV, direct download), and whether watermark is present.
3. **Contain:**
   - Submit DMCA/NTD (Notice and Takedown) to hosting platform.
   - If watermark extracted: identify source session and user account.
   - If source identified: suspend account, revoke all tokens.
4. **Investigate:** Analyze how content was captured (screen recording, DRM bypass, insider leak).
5. **Remediate:** Based on root cause — may involve DRM policy tightening, HDCP enforcement changes, or process changes.
6. **Report:** Notify affected content owners within 48 hours with incident details and remediation actions.

### 12.3 Security Audit & Compliance

| Audit | Frequency | Scope | Owner |
|-------|-----------|-------|-------|
| DRM compliance audit | Quarterly | DRM implementation correctness, license policy enforcement, HDCP compliance | Security Engineering |
| Penetration test (content path) | Semi-annually | Attempt to access content without valid entitlement, bypass DRM, extract content keys | External security firm |
| Token security review | Quarterly | CAT token implementation, signing key management, token abuse metrics | Security Engineering |
| Content rights audit | Monthly | Verify catalog rights match licensing agreements, catch-up windows are correct, expired content is removed | Content Operations + Engineering |
| Watermark integrity test | Quarterly | Verify watermark survives transcoding, resolution changes, and common piracy techniques | Security Engineering |

---

*This document defines the content security architecture for the AI-native OTT streaming platform. All content handling — from ingest through encoding, packaging, storage, CDN delivery, and client playback — must adhere to these security requirements. Content security is non-negotiable: it is the foundation of content licensing relationships and a prerequisite for carrying premium content. Changes to security policies require review by the Security Engineering team and may require content owner approval.*
