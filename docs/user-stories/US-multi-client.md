# User Stories: PRD-006 — Multi-Client Platform Support

**Source PRD:** PRD-006-multi-client.md
**Generated:** 2026-02-08
**Total Stories:** 30

---

## Epic 1: Platform Launch — Phase 1 Clients

### US-MC-001: Android TV Application

**As a** viewer
**I want to** use a native Android TV application with full D-pad remote navigation and 4K HDR playback
**So that** I can enjoy the complete streaming experience on my living room TV

**Priority:** P0
**Phase:** 1
**Story Points:** XL
**PRD Reference:** MC-FR-001, MC-FR-030

**Acceptance Criteria:**
- [ ] Given the app is installed on Android TV 8+, when it launches cold, then the home screen is interactive within 3 seconds
- [ ] Given the user navigates with D-pad, then every interactive element is reachable with visible focus indicators
- [ ] Given a 4K HDR title is played, then ExoPlayer/Media3 renders in 4K HDR with Widevine L1 DRM
- [ ] Performance: Channel tune < 1.5s, playback start < 1.5s, peak memory < 300MB

**AI Component:** No

**Dependencies:** TV BFF, Entitlement Service, CDN, ExoPlayer/Media3

**Technical Notes:**
- Built with Kotlin + Jetpack Compose for TV; must pass Google TV certification
- ExoPlayer/Media3 3.3+ for latest features; hardware HEVC decoding required for 4K

---

### US-MC-002: Apple TV Application

**As a** viewer
**I want to** use a native Apple TV application with Siri integration and Dolby Vision support
**So that** I can watch content on my Apple TV with the best possible quality and Apple ecosystem integration

**Priority:** P0
**Phase:** 1
**Story Points:** XL
**PRD Reference:** MC-FR-002, MC-FR-030

**Acceptance Criteria:**
- [ ] Given the app is installed on tvOS 16+, when it launches cold, then the home screen is interactive within 3 seconds
- [ ] Given Dolby Vision content is available, then AVPlayer renders in Dolby Vision on supported hardware
- [ ] Given the user presses the Siri button and says "show me action movies," then relevant results are displayed
- [ ] Performance: Playback start < 1.5s, FairPlay DRM functional, peak memory < 256MB

**AI Component:** No

**Dependencies:** TV BFF, Entitlement Service, CDN, FairPlay license server

**Technical Notes:**
- Built with Swift + SwiftUI; AVKit provides native player chrome with custom overlay for branding
- Must pass Apple TV App Review

---

### US-MC-003: Web Browser Application

**As a** viewer
**I want to** access the streaming platform in my web browser with responsive design
**So that** I can watch content on my computer without installing an app

**Priority:** P0
**Phase:** 1
**Story Points:** XL
**PRD Reference:** MC-FR-003, MC-FR-032

**Acceptance Criteria:**
- [ ] Given the user opens the web app in Chrome/Safari/Firefox/Edge (latest 2 versions), then first contentful paint occurs within 3 seconds
- [ ] Given the user navigates with keyboard, then Tab, Enter, Escape, and Arrow keys work throughout the app
- [ ] Given the player is active, then keyboard shortcuts work (Space=play/pause, F=fullscreen, M=mute)
- [ ] Given the browser supports Widevine (Chrome/Firefox/Edge) or FairPlay (Safari), then DRM playback is functional

**AI Component:** No

**Dependencies:** Web BFF, Shaka Player, CDN, Widevine/FairPlay license servers

**Technical Notes:**
- Built with TypeScript + React; SSR for fast first-contentful-paint and SEO
- Responsive from 320px to 4K; Shaka Player 4.x handles HLS/DASH

---

### US-MC-004: iOS Application

**As a** viewer
**I want to** use a native iOS app on my iPhone and iPad with touch gestures and Face ID login
**So that** I can watch content on the go with a native mobile experience

**Priority:** P1
**Phase:** 1
**Story Points:** XL
**PRD Reference:** MC-FR-004, MC-FR-031

**Acceptance Criteria:**
- [ ] Given the app is installed on iOS 16+, when it launches cold, then the home screen is interactive within 2 seconds
- [ ] Given the user swipes, taps, and pinch-to-zooms in the player, then all gestures respond correctly
- [ ] Given FairPlay DRM content, then playback works with offline download support via AVAssetDownloadTask
- [ ] Performance: Playback start < 1.5s, peak memory < 200MB, installed size < 80MB

**AI Component:** No

**Dependencies:** Mobile BFF, FairPlay license server, CDN

**Technical Notes:**
- Built with Swift + SwiftUI; must pass App Store Review
- iPad supports PiP (see US-MC-015)

---

### US-MC-005: Android Mobile Application

**As a** viewer
**I want to** use a native Android app on my phone with Material Design and offline downloads
**So that** I can watch content on my Android device anywhere

**Priority:** P1
**Phase:** 1
**Story Points:** XL
**PRD Reference:** MC-FR-005, MC-FR-031

**Acceptance Criteria:**
- [ ] Given the app is installed on Android 8+, when it launches cold, then the home screen is interactive within 2 seconds
- [ ] Given the user swipes, taps, and uses pull-to-refresh, then all gestures respond correctly
- [ ] Given Widevine L1/L3 certified device, then DRM playback works at the appropriate security level
- [ ] Performance: Playback start < 1.5s, peak memory < 250MB, installed size < 60MB

**AI Component:** No

**Dependencies:** Mobile BFF, Widevine license server, CDN

**Technical Notes:**
- Built with Kotlin + Jetpack Compose; ExoPlayer/Media3 for playback
- L1 for certified devices (full resolution); L3 for others (max 540p for premium content)

---

## Epic 2: Platform Expansion — Phase 2 Clients

### US-MC-006: Samsung Tizen Smart TV Application

**As a** viewer
**I want to** use the streaming app on my Samsung Smart TV with native-feeling performance
**So that** I can watch content directly on my TV without an external device

**Priority:** P1
**Phase:** 2
**Story Points:** XL
**PRD Reference:** MC-FR-006

**Acceptance Criteria:**
- [ ] Given the app is installed on Tizen 6.0+, when it launches cold, then the home screen is interactive within 4 seconds
- [ ] Given the user navigates with Samsung remote, then D-pad navigation works with visible focus indicators
- [ ] Given 4K HDR content, then Widevine L1 via Tizen native module renders at full quality
- [ ] Performance: Peak memory < 256MB, app size < 30MB

**AI Component:** No

**Dependencies:** TV BFF, Tizen native DRM module, CDN

**Technical Notes:**
- Built with TypeScript + React; Shaka Player + Tizen AVPlay for DRM
- Must pass Samsung TV app certification (4-8 weeks lead time)

---

### US-MC-007: LG webOS Smart TV Application

**As a** viewer
**I want to** use the streaming app on my LG TV with Magic Remote pointer support
**So that** I can access the platform on my LG TV with its native input method

**Priority:** P1
**Phase:** 2
**Story Points:** XL
**PRD Reference:** MC-FR-007, MC-FR-046

**Acceptance Criteria:**
- [ ] Given the app is installed on webOS 6.0+, when it launches cold, then the home screen is interactive within 4 seconds
- [ ] Given the user uses the Magic Remote pointer, then pointer navigation works alongside D-pad
- [ ] Given 4K HDR content, then Widevine L1 via webOS native module renders at full quality
- [ ] Performance: Peak memory < 256MB, app size < 30MB

**AI Component:** No

**Dependencies:** TV BFF, webOS native DRM module, CDN

**Technical Notes:**
- Built with TypeScript + React; similar architecture to Tizen app
- Must pass LG Content Store certification (4-8 weeks lead time)

---

### US-MC-008: Chromecast and AirPlay Support

**As a** viewer
**I want to** cast content from my phone or tablet to my TV via Chromecast or AirPlay
**So that** I can watch on the big screen using my mobile device as a remote

**Priority:** P2
**Phase:** 2
**Story Points:** L
**PRD Reference:** MC-FR-009

**Acceptance Criteria:**
- [ ] Given the user taps the Cast button and selects a Chromecast device, then playback transfers to the TV within 3 seconds
- [ ] Given casting is active, then remote control functions (play/pause/seek) work from the sender device
- [ ] Given the user stops casting, then playback returns to the mobile device at the current position
- [ ] Given AirPlay is available, then the same transfer behavior works for Apple devices

**AI Component:** No

**Dependencies:** Chromecast receiver application, AirPlay integration, DRM (maintained during cast)

**Technical Notes:**
- Custom Chromecast receiver app for branded UI and DRM; AirPlay uses native protocol

---

## Epic 3: BFF Architecture & Shared Infrastructure

### US-MC-009: Backend-for-Frontend Layer

**As a** developer
**I want to** deploy dedicated BFF services (TV, Mobile, Web) that aggregate backend data into client-optimized responses
**So that** each client family receives pre-composed payloads tailored to its capabilities

**Priority:** P0
**Phase:** 1
**Story Points:** XL
**PRD Reference:** MC-FR-010, MC-FR-011

**Acceptance Criteria:**
- [ ] Given a request from the TV BFF, then the response includes focus management metadata and TV-resolution image URLs
- [ ] Given a request from the Mobile BFF, then the response uses compact payloads < 30KB for home screen
- [ ] Given a request from the Web BFF, then the response includes SEO metadata and SSR hydration data
- [ ] Performance: All BFF endpoints respond with p99 < 200ms

**AI Component:** No

**Dependencies:** All backend microservices (Catalog, EPG, Recommendation, Profile, Bookmark, Entitlement)

**Technical Notes:**
- BFFs built in Go running on Kubernetes; Redis cache for per-profile composed screens (TTL: 5 minutes)
- API contracts defined in OpenAPI 3.1; used for client code generation

---

### US-MC-010: Shared Design System with Cross-Platform Tokens

**As a** developer
**I want to** use a shared design system with platform-specific design tokens
**So that** all clients maintain visual consistency while respecting platform guidelines

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** MC-FR-012

**Acceptance Criteria:**
- [ ] Given a design token change (e.g., primary color), then it propagates to all client platforms within one release cycle
- [ ] Given tokens are defined, then they cover colors, typography, spacing, and component specifications
- [ ] Given platform-specific guidelines exist, then tokens include per-platform overrides (e.g., Apple TV focus effects)

**AI Component:** No

**Dependencies:** Design team

**Technical Notes:**
- Design tokens defined in a central system (e.g., Style Dictionary); exported to platform-specific formats

---

### US-MC-011: Feature Flag Infrastructure

**As a** developer
**I want to** gate features per device type, platform, OS version, app version, user segment, and percentage rollout
**So that** I can safely roll out features incrementally per platform

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** MC-FR-013

**Acceptance Criteria:**
- [ ] Given a flag targeting "Android TV, app version > 2.0, market=DE, 10% rollout," then only matching users see the feature
- [ ] Given a flag is toggled, then the change takes effect on clients within 60 seconds
- [ ] Given Unleash is unavailable, then clients fall back to a cached flag configuration

**AI Component:** No

**Dependencies:** Unleash (feature flag service)

**Technical Notes:**
- Unleash client SDK integrated in all client apps and BFFs; cached locally for resilience

---

### US-MC-012: Remote Configuration for Server-Driven UI

**As an** operator
**I want to** change home screen rail order, layout parameters, and content limits without requiring an app update
**So that** I can adjust the user experience dynamically based on business needs

**Priority:** P1
**Phase:** 1
**Story Points:** M
**PRD Reference:** MC-FR-014

**Acceptance Criteria:**
- [ ] Given a configuration change to home screen rail order, then it is reflected on all clients within 60 seconds
- [ ] Given a configuration is invalid, then clients fall back to the previous valid configuration
- [ ] Given no network connectivity, then clients use the last cached configuration

**AI Component:** No

**Dependencies:** Remote config service, BFF layer

**Technical Notes:**
- Remote configuration served by BFF; clients poll at configurable intervals or receive push updates

---

## Epic 4: Cross-Device Experience

### US-MC-013: Cross-Device Bookmark Sync

**As a** viewer
**I want to** stop watching on one device and continue from the exact position on another device
**So that** I can seamlessly transition between my phone, tablet, and TV

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** MC-FR-020

**Acceptance Criteria:**
- [ ] Given a user pauses at 35:12 on device A, when they open "Continue Watching" on device B within 10 seconds, then the position shows 35:12 (+/- 5 seconds)
- [ ] Given playback heartbeats are sent every 30 seconds, then the bookmark is updated server-side within 5 seconds of each heartbeat
- [ ] Given two devices send conflicting bookmarks, then latest-write-wins with server validation resolves the conflict

**AI Component:** No

**Dependencies:** Bookmark Service

**Technical Notes:**
- Bookmark Service is source of truth; clients send heartbeats every 30 seconds; server uses latest-write-wins conflict resolution

---

### US-MC-014: AI Context-Aware Continue Watching

**As a** viewer
**I want to** see my "Continue Watching" rail prioritized differently based on my current device and time of day
**So that** short content appears first on my phone during commute and long content appears first on my TV at night

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** MC-FR-022, MC-AI-001, MC-AI-002

**Acceptance Criteria:**
- [ ] Given a user has 5 in-progress titles and opens the app on mobile at 8 AM, then short-form content (< 30 min remaining) is prioritized
- [ ] Given the same user opens on TV at 9 PM, then long-form content (movies, series) is prioritized
- [ ] Given the Recommendation Service is unavailable, then "Continue Watching" falls back to recency-based ordering

**AI Component:** Yes -- BFF includes device type, time-of-day, and network type in Recommendation Service requests; model adapts content prioritization per context

**Dependencies:** Recommendation Service, Bookmark Service, BFF

**Technical Notes:**
- Context signals (device type, time, network) sent by BFF to Recommendation Service with every home screen request

---

### US-MC-015: Picture-in-Picture on iOS/iPadOS

**As a** binge watcher
**I want to** continue watching in a PiP window while browsing for my next title
**So that** I can multitask without interrupting the current playback

**Priority:** P1
**Phase:** 1
**Story Points:** M
**PRD Reference:** MC-FR-040

**Acceptance Criteria:**
- [ ] Given the user navigates away from the player on iPad, then video continues in a PiP window
- [ ] Given PiP is active, then the window can be resized and repositioned
- [ ] Given the user starts a new title, then PiP is replaced by the new content

**AI Component:** No

**Dependencies:** AVKit PiP support (iOS/iPadOS)

**Technical Notes:**
- Use AVPictureInPictureController; requires background audio entitlement

---

### US-MC-016: Device Management

**As a** viewer
**I want to** view and manage all my authorized devices from any client
**So that** I can control which devices have access to my account

**Priority:** P1
**Phase:** 1
**Story Points:** M
**PRD Reference:** MC-FR-023

**Acceptance Criteria:**
- [ ] Given a user opens Device Management, then all registered devices are listed with device name, type, and last active time
- [ ] Given a user renames a device, then the new name appears across all clients within 5 seconds
- [ ] Given a user removes a device, then that device loses access and must re-authenticate on next app launch

**AI Component:** No

**Dependencies:** Device Service, Auth Service

**Technical Notes:**
- Devices registered on first authentication; device metadata (type, OS, app version) sent during registration

---

### US-MC-017: Concurrent Stream Limit Enforcement

**As an** operator
**I want to** enforce concurrent stream limits per subscription tier across all devices
**So that** account sharing is within acceptable bounds

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** MC-FR-024, MC-FR-025

**Acceptance Criteria:**
- [ ] Given a Basic subscriber with 2-stream limit has 2 active streams, when a 3rd is attempted, then the stream is denied with a message showing active devices and an option to stop one
- [ ] Given a user stops a stream, then the slot becomes available after a 60-second grace period
- [ ] Given enforcement accuracy, then > 99% of limit violations are correctly detected

**AI Component:** No

**Dependencies:** Playback Session Service, Entitlement Service

**Technical Notes:**
- Session tracking in Playback Session Service with heartbeats; grace period prevents race conditions during device handoffs

---

## Epic 5: Platform-Specific Features

### US-MC-018: Google TV Home Screen Integration

**As a** viewer
**I want to** see my Continue Watching and recommended content on the Google TV home screen
**So that** I can discover and resume content without opening the app

**Priority:** P1
**Phase:** 1
**Story Points:** M
**PRD Reference:** MC-FR-041

**Acceptance Criteria:**
- [ ] Given the app is installed on Google TV, then "Continue Watching" entries appear on the Google TV home screen via Watch Next API
- [ ] Given the AI recommends content, then "Recommended" entries are published to the Google TV home screen
- [ ] Given a user selects a Watch Next entry on the home screen, then the app opens and begins playback directly

**AI Component:** Yes -- AI recommendations surfaced on TV home screen via Watch Next API

**Dependencies:** Google TV Watch Next API, Recommendation Service

**Technical Notes:**
- Use Engagement API (Watch Next) for Continue Watching; Recommendation API for personalized content

---

### US-MC-019: Mobile Push Notifications

**As a** viewer
**I want to** receive push notifications for smart reminders, new content, and engagement prompts
**So that** I stay informed about content I care about without manually checking

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** MC-FR-042

**Acceptance Criteria:**
- [ ] Given a smart reminder is triggered, then a push notification is delivered to the mobile device within 30 seconds
- [ ] Given the user taps the notification, then the app opens at the relevant deep link
- [ ] Given the user configures notification preferences, then only enabled notification types are delivered

**AI Component:** Yes -- AI-triggered notifications based on viewing patterns and relevance scoring

**Dependencies:** Notification Service, APNs (iOS), FCM (Android)

**Technical Notes:**
- FCM for Android; APNs for iOS; notification payload includes deep link parameters

---

### US-MC-020: Offline Download for Mobile

**As a** viewer
**I want to** download VOD content for offline viewing on my mobile device
**So that** I can watch during flights or when I have no connectivity

**Priority:** P1
**Phase:** 1
**Story Points:** L
**PRD Reference:** MC-FR-043

**Acceptance Criteria:**
- [ ] Given a user selects "Download" on an eligible title, then downloads proceed in background with progress visible in the Downloads section
- [ ] Given a downloaded title has an offline DRM license (48-hour validity), then it plays in airplane mode
- [ ] Given the user regains connectivity, then viewing progress syncs to the server and "Continue Watching" updates on other devices
- [ ] Given a license expires while offline, then a clear error message explains the issue and offers to re-download when online

**AI Component:** No

**Dependencies:** DRM license server (offline license), Bookmark Service (progress sync)

**Technical Notes:**
- iOS: AVAssetDownloadTask; Android: ExoPlayer download helper; DRM offline license acquired during download

---

### US-MC-021: PWA Installation for Web

**As a** viewer
**I want to** install the web app as a Progressive Web App on my desktop
**So that** I can launch the streaming platform quickly without opening a browser tab

**Priority:** P2
**Phase:** 2
**Story Points:** M
**PRD Reference:** MC-FR-044

**Acceptance Criteria:**
- [ ] Given the user is on Chrome/Edge, when they click "Install," then the PWA installs and launches in a standalone window
- [ ] Given the PWA is installed, then it appears in the OS application launcher
- [ ] Given the browser supports push notifications for PWAs, then smart notifications are delivered

**AI Component:** No

**Dependencies:** Service worker, Web BFF

**Technical Notes:**
- Manifest.json configured for standalone mode; service worker for caching and offline shell

---

### US-MC-022: Voice Assistant Integration on TV

**As a** casual viewer
**I want to** use voice commands on my TV remote to search and play content
**So that** I can find what I want without typing or browsing

**Priority:** P1
**Phase:** 1 (Android TV, Apple TV) / Phase 2 (Samsung, LG)
**Story Points:** L
**PRD Reference:** MC-FR-033

**Acceptance Criteria:**
- [ ] Given the user presses the voice button and says "show me nature documentaries," then relevant search results are displayed
- [ ] Given the user says "play The Bear," then playback of the title begins directly
- [ ] Given voice search returns no results, then a helpful message with suggestions is displayed

**AI Component:** Yes -- AI-powered search backing voice queries for semantic understanding

**Dependencies:** Platform voice SDKs (Google Assistant, Siri, Bixby, LG ThinQ), Search Service

**Technical Notes:**
- Each platform has its own voice integration SDK; queries routed to Search Service via BFF

---

### US-MC-023: Deep Linking Support

**As a** viewer
**I want to** open a shared link or notification and land directly on the relevant content in the app
**So that** I can access specific titles without navigating through the app

**Priority:** P1
**Phase:** 1 (native) / Phase 2 (Smart TV)
**Story Points:** M
**PRD Reference:** MC-FR-034

**Acceptance Criteria:**
- [ ] Given a deep link to a title, when the user taps it, then the title detail page opens within 2 seconds
- [ ] Given the app is not installed, then the deep link redirects to the web app or app store
- [ ] Given Android App Links and iOS Universal Links are configured, then links open in the native app directly (no disambiguation)

**AI Component:** No

**Dependencies:** App link configuration per platform

**Technical Notes:**
- Android App Links (verified), iOS Universal Links, web fallback URL

---

## Epic 6: On-Device AI

### US-MC-024: Predictive Pre-Fetching of Next Content

**As a** binge watcher
**I want to** have the next episode pre-loaded when I am near the end of the current one
**So that** playback of the next episode starts instantly

**Priority:** P2
**Phase:** 2
**Story Points:** L
**PRD Reference:** MC-AI-010

**Acceptance Criteria:**
- [ ] Given a user is 80% through an episode, then the client pre-fetches the first 10 seconds of the next episode
- [ ] Given auto-play triggers, then the next episode starts within 500ms
- [ ] Given the user exits before auto-play, then pre-fetched data is discarded without wasting storage

**AI Component:** Yes -- On-device ML predicts next content based on viewing patterns and triggers pre-fetch

**Dependencies:** Player, CDN

**Technical Notes:**
- Pre-fetch initiated by client-side logic; initial segments of next episode cached locally

---

### US-MC-025: Cached Home Screen for Instant Launch

**As a** viewer
**I want to** see a personalized home screen instantly when I reopen the app
**So that** I do not wait for network requests before I can start browsing

**Priority:** P1
**Phase:** 1
**Story Points:** M
**PRD Reference:** MC-AI-011

**Acceptance Criteria:**
- [ ] Given a user reopens the app within 4 hours, then the cached home screen displays within 500ms
- [ ] Given fresh data is available, then the home screen updates in the background after the cached version is shown
- [ ] Given the cache is older than 4 hours, then a loading state is shown while fresh data loads

**AI Component:** Yes -- Caches the most recent AI-personalized home screen for instant display

**Dependencies:** BFF, local storage

**Technical Notes:**
- Cached response stored in local storage/DB; background refresh on every app open

---

### US-MC-026: Client Engagement Telemetry

**As a** developer
**I want to** send detailed engagement telemetry from all clients to feed recommendation and QoE models
**So that** AI models continuously improve based on real user behavior

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** MC-AI-013

**Acceptance Criteria:**
- [ ] Given a user scrolls past a rail without interacting, then a "rail_scroll_through" event with per-item dwell times is sent within 5 seconds
- [ ] Given events are batched, then they are sent every 5 seconds or 20 events (whichever comes first)
- [ ] Given the event schema is followed, then every event includes session_id, user_id, profile_id, device_type, app_version, os_version, and connection_type

**AI Component:** Yes -- Telemetry feeds recommendation models, QoE models, and AIOps

**Dependencies:** Analytics Collector service

**Technical Notes:**
- Standardized event schema across all platforms; sent via HTTPS to Analytics Collector; categories: playback, browse, EPG, user, system

---

### US-MC-027: Per-Device Viewing Pattern Learning

**As a** viewer
**I want to** receive device-specific recommendations that reflect how I use each device
**So that** my phone suggests commute content and my TV suggests evening viewing

**Priority:** P1
**Phase:** 2
**Story Points:** L
**PRD Reference:** MC-AI-003

**Acceptance Criteria:**
- [ ] Given a user watches sports on TV and drama on mobile for 14+ days, then TV recommendations emphasize sports and mobile recommendations emphasize drama
- [ ] Given insufficient per-device data (< 14 days), then cross-device general recommendations are used
- [ ] Given the model is unavailable, then the fallback is cross-device general recommendations

**AI Component:** Yes -- ML model learns per-user per-device viewing patterns from telemetry data

**Dependencies:** Recommendation Service, Feature Store, Analytics pipeline

**Technical Notes:**
- Device type included in all telemetry events; Feature Store maintains per-user per-device features

---

## Epic 7: Second Screen & Companion

### US-MC-028: Mobile as Remote Control for TV

**As a** viewer
**I want to** use my phone as a remote control for the TV app on my local network
**So that** I can control playback without the TV remote

**Priority:** P2
**Phase:** 3
**Story Points:** L
**PRD Reference:** MC-FR-050

**Acceptance Criteria:**
- [ ] Given the phone and TV are on the same network, then the phone discovers the TV client
- [ ] Given the phone is connected, then play/pause, seek, and volume controls have < 300ms latency
- [ ] Given the scenario works cross-platform, then Android phone -> Android TV and iPhone -> Apple TV are both supported

**AI Component:** No

**Dependencies:** Local network discovery protocol, TV client receiver

**Technical Notes:**
- Use mDNS/SSDP for discovery; WebSocket or platform-specific protocol for control commands

---

### US-MC-029: Browse While Casting

**As a** viewer
**I want to** browse content and manage my watchlist on my phone while casting to my TV
**So that** I can multitask without interrupting what is playing on the TV

**Priority:** P2
**Phase:** 2
**Story Points:** M
**PRD Reference:** MC-FR-052

**Acceptance Criteria:**
- [ ] Given the user is casting to TV, then the mobile app shows a mini player bar with cast status
- [ ] Given the mini player is visible, then the user can browse, search, and add to watchlist
- [ ] Given the user selects new content to play, then the cast session switches to the new content on the TV

**AI Component:** No

**Dependencies:** Cast SDK (Chromecast), AirPlay, Mobile app

**Technical Notes:**
- Mini player bar persists at bottom of screen during active cast; sender app retains full browse functionality

---

## Epic 8: Non-Functional & Quality Assurance

### US-MC-030: Accessibility Compliance Across Platforms

**As a** viewer with accessibility needs
**I want to** use screen readers, high-contrast mode, and subtitle customization on every platform
**So that** I can access the full streaming experience regardless of my abilities

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** MC-NFR-040, MC-NFR-041, MC-NFR-042, MC-NFR-043

**Acceptance Criteria:**
- [ ] Given all platforms at launch, then 100% WCAG 2.1 AA compliance is verified by automated audit and manual testing
- [ ] Given TalkBack (Android) or VoiceOver (iOS/tvOS) is active, then all screens are fully navigable by screen reader
- [ ] Given a title has audio description tracks, then they are selectable in player settings on TV clients
- [ ] Given subtitle customization is available, then the user can adjust size, color, and background on all platforms

**AI Component:** No

**Dependencies:** Per-platform accessibility frameworks, design system

**Technical Notes:**
- Automated accessibility testing (Accessibility Scanner, axe-core) in CI/CD; manual testing per release

---

### US-MC-031: BFF Scalability and Resilience

**As a** developer
**I want to** ensure BFF services auto-scale and degrade gracefully under load
**So that** client applications remain functional even during traffic spikes or backend failures

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** MC-NFR-020, MC-NFR-030, MC-NFR-031, MC-NFR-032, MC-NFR-033

**Acceptance Criteria:**
- [ ] Given TV BFF target throughput of 4,000 RPS (Phase 1), then load tests pass with p99 < 200ms
- [ ] Given a backend service is unavailable, then the BFF returns a partial response with degraded data (no crash, no 500 error)
- [ ] Given BFF availability target of 99.95%, then monthly uptime meets or exceeds this target

**AI Component:** No

**Dependencies:** Kubernetes HPA, Redis, circuit breaker libraries

**Technical Notes:**
- Auto-scale BFFs independently per client family; circuit breakers per backend dependency; cache aggressively

---

### US-MC-032: Client Crash Rate Monitoring

**As a** developer
**I want to** monitor crash rates across all client platforms in real-time
**So that** regressions are detected and fixed quickly before impacting users

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** MC-NFR-021, MC-NFR-022

**Acceptance Criteria:**
- [ ] Given a crash occurs on any client, then it is reported to crash analytics (Crashlytics/Sentry) within 60 seconds
- [ ] Given the crash rate exceeds 0.5% of sessions for any platform, then an alert is triggered
- [ ] Given an Android ANR rate exceeds 0.2%, then an alert is triggered

**AI Component:** No

**Dependencies:** Firebase Crashlytics (mobile/TV), Sentry (web/Smart TV)

**Technical Notes:**
- Crash reporting SDKs integrated in all clients; dashboards per platform; alerts configured in monitoring system

---

*End of user stories for PRD-006 (Multi-Client). Total: 30 stories covering Phase 1 clients (5), Phase 2 clients (3), shared infrastructure (4), cross-device (5), platform-specific features (6), on-device AI (4), second screen (2), and non-functional (3).*
