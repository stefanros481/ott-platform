# PRD-006: Multi-Client Platform Support

**Document ID:** PRD-006
**Version:** 1.0
**Date:** 2026-02-08
**Status:** Draft
**Author:** PRD Writer B Agent
**References:** VIS-001 (Project Vision & Design), ARCH-001 (Platform Architecture)
**Audience:** Product Management, Engineering (Client, Backend, QA), UX Design

---

## Table of Contents

1. [Overview](#1-overview)
2. [Goals & Non-Goals](#2-goals--non-goals)
3. [User Scenarios](#3-user-scenarios)
4. [Functional Requirements](#4-functional-requirements)
5. [AI-Specific Features](#5-ai-specific-features)
6. [Non-Functional Requirements](#6-non-functional-requirements)
7. [Technical Considerations](#7-technical-considerations)
8. [Dependencies](#8-dependencies)
9. [Success Metrics](#9-success-metrics)
10. [Open Questions & Risks](#10-open-questions--risks)

---

## 1. Overview

### Service Description

The Multi-Client Platform provides a consistent, high-quality streaming experience across all target devices -- living room TVs, mobile phones, tablets, web browsers, and operator set-top boxes. Rather than building a single responsive application, the platform follows a **native-first, BFF-optimized** strategy: each client family runs a native application built with platform-appropriate technologies, backed by a dedicated Backend-for-Frontend (BFF) that tailors API responses for that client's capabilities, input model, and constraints.

The platform targets 9 client platforms across 4 client families (TV, Mobile, Web, Smart TV/STB), with each client delivering the full feature set while respecting platform-specific capabilities, design guidelines, and performance constraints.

### Business Context

Multi-client support is a competitive necessity. The average streaming household uses 3.2 different devices for viewing. 78% of subscribers report that availability on their preferred device is a key factor in subscription retention. A platform that launches on only 2-3 devices leaves significant market coverage gaps.

However, multi-client also represents the largest engineering investment in the platform. Client engineering typically consumes 40-50% of total engineering effort. The BFF architecture, shared design system, and shared API contracts described in this PRD are designed to maximize code reuse and minimize per-platform effort while still delivering native-quality experiences.

### Scope

**In Scope:**
- Target platform matrix definition (9 platforms, 4 client families)
- BFF architecture pattern (TV, Mobile, Web BFFs)
- Per-platform player integration and DRM configuration
- Cross-device experience (profile sync, continue watching, device management)
- Per-platform input model support (remote, touch, mouse/keyboard, voice)
- Platform-specific features (PiP, notifications, widgets, deep links)
- Feature flag infrastructure for per-platform rollout
- Device certification requirements and testing strategy
- Cast/AirPlay protocol support
- On-device AI capabilities
- Second screen / companion app features
- Concurrent stream limit enforcement

**Out of Scope:**
- Platform-specific UI design (handled by design team with design system)
- Detailed playback engine internals (player selection is defined here; detailed playback behavior is in PRD-001 through PRD-004)
- App store listing, marketing, and distribution strategy
- Operator-specific STB customization (handled per-operator)

---

## 2. Goals & Non-Goals

### Goals

1. **Launch on 5 platforms by Phase 1** (Android TV, Apple TV, Web, iOS, Android) with full feature parity for core functionality (Live TV, VOD, EPG, basic TSTV)
2. **Expand to 9 platforms by Phase 2** (add Samsung Tizen, LG webOS, operator STBs, Chromecast/AirPlay)
3. **Achieve native-quality experience** on every platform -- each client follows platform design guidelines, uses native components, and feels like a first-class app for that ecosystem
4. **Maintain feature parity** across platforms with < 2 week delay between platform releases for new features
5. **Enable seamless cross-device experience** -- viewers can start watching on one device and continue on another with < 5 second bookmark accuracy
6. **Maximize engineering efficiency** through shared BFF layer, design system tokens, API contracts, and automated per-platform testing
7. **Support on-device AI** for latency-sensitive personalization, pre-fetching, and local quality optimization

### Non-Goals

- Building a single cross-platform application (e.g., React Native for all) -- native-first is the chosen strategy for TV and mobile, web-based approach for Smart TVs
- Supporting legacy devices (e.g., Android TV < Android 8, iOS < 16, Tizen < 6.0)
- Building a gaming console app (PlayStation, Xbox) in the initial roadmap
- Supporting 4K/HDR on all platforms from launch -- resolution support is tiered by platform capability

---

## 3. User Scenarios

### Scenario 1: Living Room TV Experience (Android TV)

**Persona:** The Okafor Family
**Context:** Friday evening, living room 55" Android TV, remote control

David picks up the remote and presses the home button on the Android TV launcher. The app tile shows a preview of the personalized hero banner. He selects the app, which launches in < 3 seconds. The home screen is composed for 10-foot viewing: large thumbnails, bold text, personalized rails navigable with the D-pad. He scrolls to "Continue Watching" and resumes a drama series. The player starts within 1.5 seconds, in 4K HDR with Dolby Digital audio. During playback, he presses the info button to see a mini EPG overlay. Later, he uses the Google Assistant button: "Show me nature documentaries" -- the voice search returns results displayed as a navigable grid.

### Scenario 2: Commute Viewing on Mobile (iOS)

**Persona:** Maria (The Busy Professional)
**Context:** 8:15 AM, iPhone 15, cellular connection on train

Maria opens the app with Face ID authentication. The home screen loads in < 2 seconds, optimized for portrait mode on a small screen. "Continue Watching" shows her drama series with the remaining episode duration prominently displayed (22 min left -- perfect for her commute). She taps to play. The player detects cellular connectivity and starts at 540p to conserve data, stepping up to 720p as bandwidth allows. She receives a notification: "New episode of Severance available." She swipes down to dismiss -- she'll watch it on TV tonight. When she exits the train and loses connectivity for 30 seconds, playback continues from the downloaded buffer without interruption.

### Scenario 3: Web Browser Discovery

**Persona:** Priya (The Binge Watcher)
**Context:** Saturday afternoon, MacBook Pro, Chrome browser

Priya opens the platform in her browser. The web app loads via server-side rendering for fast first-contentful-paint (< 1.5 seconds). She uses the conversational search: "dark sci-fi series like Severance" -- results appear as a grid with keyboard-navigable focus management. She reads AI-generated summaries and adds two series to her watchlist. She starts watching one; the Shaka Player handles HLS with Widevine DRM. She resizes the browser window, and the player adapts seamlessly. She right-clicks the player for quality settings and selects "1080p." The web app works as a PWA -- she can install it to her dock for quick access.

### Scenario 4: Cross-Device Handoff (Mobile to TV)

**Persona:** Maria (The Busy Professional)
**Context:** Tuesday evening, transitioning from iPhone to Apple TV

Maria watched 35 minutes of a movie on her iPhone during lunch. At 8 PM, she opens the app on her Apple TV. "Continue Watching" shows the same movie with her exact position (35:12). She selects it, and the player resumes from 35:12 on the big screen -- now in 4K with surround sound. The cross-device sync happened within 3 seconds of her stopping playback on the phone. The viewing context also shifted: the Apple TV BFF serves a living-room-optimized experience with larger UI elements and different content suggestions than her phone showed earlier.

### Scenario 5: Samsung Tizen Smart TV

**Persona:** Thomas (The Casual Viewer)
**Context:** Evening, 65" Samsung QLED TV, Tizen OS

Thomas navigates to the app from the Samsung Smart Hub. The app is built with the web-based framework (TypeScript + React) but styled to feel native on Tizen. It launches in < 4 seconds (slower than native platforms but within target). The UI is optimized for the Samsung remote: D-pad navigation with focus indicators, back button integration, and Samsung-specific volume control overlay. DRM uses Widevine L1 via the Tizen native DRM module. Thomas sees a simplified home screen -- the BFF returns fewer rails and larger thumbnails, tuned for the Tizen performance profile. He watches a documentary in 4K HDR.

### Scenario 6: Chromecast from Mobile

**Persona:** Erik (The Sports Fan)
**Context:** Saturday afternoon, casting from Android phone to living room Chromecast

Erik is watching F1 qualifying on his Android phone. His friends arrive, and he taps the Cast button in the player. The Chromecast icon indicates his living room device. He selects it, and playback transfers to the TV within 3 seconds. His phone becomes a remote control -- he can pause, seek, and see the mini EPG. The cast session uses the Chromecast receiver application, which handles DRM and ABR independently. When he taps "stop casting," playback returns to his phone at the current position.

### Scenario 7: Offline Download (iOS)

**Persona:** Maria (The Busy Professional)
**Context:** Sunday evening, preparing content for a flight

Maria opens the "Downloads" section on her iPhone. She selects a 3-episode run of her current series and taps "Download" at Medium quality (720p). The app estimates 1.8 GB for all three episodes. Downloads proceed in the background -- she can close the app. Each episode acquires an offline DRM license (valid for 48 hours). On the plane, she opens the app in airplane mode and plays the downloaded episodes. When she lands and gets connectivity, her viewing progress syncs to the server, and her "Continue Watching" on other devices updates.

### Scenario 8: Picture-in-Picture on iPad

**Persona:** Priya (The Binge Watcher)
**Context:** Saturday evening, iPad Pro, browsing while watching

Priya is watching a series on her iPad. She swipes up to go home -- the video shrinks to a PiP window in the corner. She opens the platform app to browse for something to watch next. The PiP window continues playing the current episode while she browses VOD content. She taps a new title to start watching, and the PiP window is replaced by the new content.

### Scenario 9: Operator STB (Android-Based)

**Persona:** The Okafor Family
**Context:** Operator-provided set-top box (Android STB variant)

The family receives an Android-based STB from their operator. The platform app comes pre-installed and integrates with the operator's channel lineup and billing. The STB app uses the same Android TV codebase but with operator-specific configuration: custom branding, operator channel numbers, and billing integration via the operator's subscriber management system. The experience is identical to the standalone Android TV app, with the addition of operator-specific EPG channel mappings and entitlement integration.

### Scenario 10: Device Management and Concurrent Streams

**Persona:** Maria (The Busy Professional)
**Context:** Reaching concurrent stream limit

Maria is watching on her Apple TV. She forgot to stop a stream on her iPad that her partner was using. She tries to start a new stream on her iPhone -- the app shows: "You've reached your stream limit (2 simultaneous). Currently watching on: Apple TV (Living Room), iPad (Bedroom). Stop a stream to continue." She can tap "Stop iPad stream" directly from the message to free up a slot.

---

## 4. Functional Requirements

### Target Platform Matrix

| ID | Requirement | Priority | Phase | Acceptance Criteria |
|----|-------------|----------|-------|---------------------|
| MC-FR-001 | Platform shall support Android TV / Google TV (Android 8+) with Kotlin + Jetpack Compose and ExoPlayer/Media3 | P0 | 1 | App passes Google TV certification, renders at 4K HDR, channel tune < 1.5s, Widevine L1 DRM functional |
| MC-FR-002 | Platform shall support Apple TV (tvOS 16+) with Swift + SwiftUI and AVPlayer | P0 | 1 | App passes Apple TV App Review, renders at 4K HDR with Dolby Vision, FairPlay DRM functional, Siri integration |
| MC-FR-003 | Platform shall support Web browsers (Chrome, Safari, Firefox, Edge, latest 2 versions) with TypeScript + React and Shaka Player | P0 | 1 | App loads in < 3 seconds (first contentful paint), supports Widevine (Chrome/Firefox/Edge) and FairPlay (Safari), responsive from 320px to 4K |
| MC-FR-004 | Platform shall support iOS (iPhone/iPad, iOS 16+) with Swift + SwiftUI and AVPlayer | P1 | 1 | App passes App Store Review, supports FairPlay DRM, offline downloads functional, PiP supported on iPad |
| MC-FR-005 | Platform shall support Android Mobile (Android 8+) with Kotlin + Jetpack Compose and ExoPlayer/Media3 | P1 | 1 | App passes Google Play certification, Widevine L1/L3 DRM functional, offline downloads functional |
| MC-FR-006 | Platform shall support Samsung Tizen (Tizen 6.0+) with TypeScript + React and Shaka Player | P1 | 2 | App passes Samsung TV app certification, renders at 4K HDR, Widevine L1 via Tizen native module |
| MC-FR-007 | Platform shall support LG webOS (webOS 6.0+) with TypeScript + React and Shaka Player | P1 | 2 | App passes LG Content Store certification, renders at 4K HDR, Widevine L1 via webOS native module |
| MC-FR-008 | Platform shall support operator STBs (RDK-based and Android-based) with platform-appropriate technology | P2 | 2 | App runs on reference RDK and Android STB hardware, integrates with operator entitlements and channel maps |
| MC-FR-009 | Platform shall support Chromecast (Google Cast) and AirPlay protocol for casting from mobile and web | P2 | 2 | Cast/AirPlay session transfers playback within 3 seconds, remote control functions (play/pause/seek) work from sender, DRM maintained during cast session |

### Shared Architecture

| ID | Requirement | Priority | Phase | AI Enhancement | Acceptance Criteria |
|----|-------------|----------|-------|----------------|---------------------|
| MC-FR-010 | Platform shall implement a BFF (Backend-for-Frontend) pattern with dedicated BFFs for TV, Mobile, and Web client families | P0 | 1 | No | Each BFF returns responses tailored to its client family: TV BFF includes focus management metadata, Mobile BFF includes compact payloads, Web BFF includes SEO data |
| MC-FR-011 | All clients shall consume versioned REST APIs from their respective BFF, with API contracts defined in OpenAPI 3.1 | P0 | 1 | No | API contracts are published, versioned (v1/v2), and used for client code generation; breaking changes require version increment |
| MC-FR-012 | Platform shall implement a shared design system with cross-platform design tokens (colors, typography, spacing, component specifications) | P0 | 1 | No | Design tokens are consumed by all client platforms; a design token change propagates to all clients within one release cycle |
| MC-FR-013 | Feature flags (Unleash) shall support targeting by: device type, platform, OS version, app version, user ID, subscription tier, market/region, percentage rollout | P0 | 1 | No | A feature flag targeting "Android TV, app version > 2.0, market=DE, 10% rollout" correctly gates the feature for matching users only |
| MC-FR-014 | Remote configuration shall enable server-driven UI changes (rail order, layout parameters, content limits) without app updates | P1 | 1 | No | A configuration change to home screen rail order is reflected on all clients within 60 seconds without requiring an app update |

### Cross-Device Experience

| ID | Requirement | Priority | Phase | AI Enhancement | Acceptance Criteria |
|----|-------------|----------|-------|----------------|---------------------|
| MC-FR-020 | Viewing progress (bookmarks) shall sync across all devices within 5 seconds of a playback stop/pause event | P0 | 1 | No | Given a user pauses at 35:12 on device A, when they open the app on device B within 10 seconds, then "Continue Watching" shows 35:12 (± 5 seconds) |
| MC-FR-021 | User profile settings, preferences, and favorites shall sync across all devices for the same profile | P0 | 1 | No | Given a user adds a channel to favorites on iOS, when they open the EPG on Android TV, then the same channel appears in favorites within 5 seconds |
| MC-FR-022 | "Continue Watching" rail shall be consistent across all devices, AI-prioritized per context (device type, time-of-day) | P0 | 1 | Yes -- AI-prioritized per device context | Given a user has 5 in-progress titles, when they open on mobile at 8 AM, then short-form content is prioritized; when they open on TV at 9 PM, then long-form content is prioritized |
| MC-FR-023 | Users shall be able to view and manage authorized devices from any client | P1 | 1 | No | Given a user opens Device Management, then all registered devices are listed with: device name, type, last active time; user can rename or remove devices |
| MC-FR-024 | Concurrent stream limits shall be enforced per subscription tier across all devices | P0 | 1 | No | Given a Basic subscriber with a 2-stream limit, when 2 streams are active and a 3rd is attempted, then the 3rd stream is denied with a clear message showing active devices and an option to stop one |
| MC-FR-025 | A grace period of 60 seconds shall apply between stopping a stream and the slot becoming available for a new device | P1 | 1 | No | Given a user stops playback on device A, when they start on device B within 60 seconds, then the system allows the new stream without counting against the limit |

### Per-Platform Input Models

| ID | Requirement | Priority | Phase | AI Enhancement | Acceptance Criteria |
|----|-------------|----------|-------|----------------|---------------------|
| MC-FR-030 | TV clients (Android TV, Apple TV, Tizen, webOS, STB) shall support full D-pad remote control navigation with visible focus indicators | P0 | 1/2 | No | Every interactive element is reachable via D-pad; focus state is clearly visible; focus moves in predictable directions |
| MC-FR-031 | Mobile clients (iOS, Android) shall support touch gesture navigation (swipe, tap, pinch-to-zoom on player, pull-to-refresh) | P0 | 1 | No | All navigation is gesture-based; player supports swipe-to-seek, pinch-to-zoom (letterbox fill); pull-to-refresh on content rails |
| MC-FR-032 | Web client shall support mouse, keyboard, and trackpad navigation | P0 | 1 | No | All elements are clickable; keyboard navigation (Tab, Enter, Escape, Arrow keys) works throughout; keyboard shortcuts for player (Space=play/pause, F=fullscreen, M=mute) |
| MC-FR-033 | TV clients shall integrate with platform voice assistants (Google Assistant on Android TV, Siri on Apple TV, Bixby on Samsung, LG ThinQ) | P1 | 1/2 | Yes -- AI-powered search backing voice queries | Voice query "show me action movies" returns relevant results; voice command "play [title]" initiates playback directly |
| MC-FR-034 | All clients shall support platform-specific deep linking (Android App Links, iOS Universal Links, Web URLs, Smart TV deep links) | P1 | 1/2 | No | A deep link to a specific title (e.g., from a notification or external referral) opens the title detail page directly in the app within 2 seconds |

### Platform-Specific Features

| ID | Requirement | Priority | Phase | AI Enhancement | Acceptance Criteria |
|----|-------------|----------|-------|----------------|---------------------|
| MC-FR-040 | iOS and iPadOS shall support Picture-in-Picture (PiP) playback | P1 | 1 | No | When the user navigates away from the player, video continues in a PiP window; PiP can be resized and repositioned |
| MC-FR-041 | Android TV shall integrate with the Google TV home screen (Watch Next, Continue Watching, recommendations) | P1 | 1 | Yes -- AI recommendations surfaced on TV home screen | The platform publishes "Continue Watching" and "Recommended" content to the Google TV home screen via the Watch Next API |
| MC-FR-042 | Mobile clients (iOS, Android) shall support push notifications for smart reminders, new content alerts, and engagement re-activation | P0 | 1 | Yes -- AI-triggered notifications | Push notifications are delivered within 30 seconds of trigger; tap opens relevant deep link; notification preferences are configurable |
| MC-FR-043 | Mobile clients shall support background download for offline viewing (VOD titles with offline rights) | P1 | 1 | No | Downloads proceed in background; progress visible in Downloads section; downloaded content plays in airplane mode; offline DRM license valid for 48 hours |
| MC-FR-044 | Web client shall support Progressive Web App (PWA) installation | P2 | 2 | No | User can "Install" the web app to desktop; installed PWA launches in standalone window; PWA receives push notifications (where browser supports) |
| MC-FR-045 | Samsung Tizen shall integrate with Samsung Smart Hub preview and recommendations | P2 | 2 | No | App tile in Smart Hub shows a content preview; Samsung recommendation API receives personalized content suggestions |
| MC-FR-046 | LG webOS shall integrate with LG Content Store and Magic Remote pointer input | P2 | 2 | No | App appears in LG Content Store; Magic Remote pointer navigation works alongside D-pad; voice button triggers voice search |

### Second Screen / Companion Features

| ID | Requirement | Priority | Phase | AI Enhancement | Acceptance Criteria |
|----|-------------|----------|-------|----------------|---------------------|
| MC-FR-050 | Mobile clients shall function as a remote control for TV clients on the same network (play/pause, seek, volume) | P2 | 3 | No | Phone discovers TV on local network; remote control functions have < 300ms latency; works across Android phone → Android TV and iPhone → Apple TV |
| MC-FR-051 | Mobile clients shall support "second screen" mode during live sports: synchronized stats, lineup, and commentary | P2 | 3 | Yes -- AI-curated real-time stats | During a live football match on TV, the phone shows synchronized match stats, lineup, and key events; data is synced to broadcast position ± 5 seconds |
| MC-FR-052 | Mobile clients shall allow browsing content and adding to watchlist while content plays on TV (via Cast/AirPlay) | P2 | 2 | No | While casting to TV, the mobile app shows a mini player bar and allows full browse, search, and watchlist functionality |

---

## 5. AI-Specific Features

### 5.1 Context-Aware Content Personalization

**Description:** The BFF layer incorporates device context into AI personalization requests. The Recommendation Service adjusts its output based on which device the user is on, what time it is, and historical context-specific viewing patterns.

**Context Signals:**
- **Device type:** TV (long-form, immersive), Mobile (short-form, commute), Tablet (mixed), Web (browse-heavy)
- **Time of day:** Morning (news, short content), Evening (movies, series), Late night (binge-watching)
- **Network:** Wi-Fi (high quality, large files) vs Cellular (bandwidth-conscious)
- **Session history:** If the user just finished an episode, prioritize "Next Episode" over discovery

**Requirements:**

| ID | Requirement | Priority | Phase | Acceptance Criteria |
|----|-------------|----------|-------|---------------------|
| MC-AI-001 | BFF shall include device type, screen size, network type, and time-of-day in all Recommendation Service requests | P0 | 1 | Given a request from Mobile BFF at 8 AM on cellular, then recommendation response prioritizes short-form content (< 30 min) and reduces image payload sizes |
| MC-AI-002 | Home screen content rails shall be ordered differently based on device context | P1 | 1 | Given the same user on TV at 9 PM, then "Movies for Tonight" is the top rail; on phone at 8 AM, then "Quick Catch-Up" (short episodes) is the top rail |
| MC-AI-003 | AI model shall learn per-user per-device viewing patterns and adapt recommendations per context | P1 | 2 | Given a user who watches sports on TV and drama on mobile, then after 14 days of data, TV recommendations emphasize sports and mobile recommendations emphasize drama |

### 5.2 On-Device AI

**Description:** Select AI capabilities run on-device for latency-sensitive operations or to reduce server load, where device hardware supports it.

**On-Device Capabilities:**
- **Pre-fetching:** Client predicts next content likely to be played (based on viewing patterns) and pre-buffers initial segments
- **UI personalization caching:** Client caches personalized UI state (rail positions, content order) for instant app launch
- **Local quality optimization:** Client-side ML model learns the user's network pattern and adjusts ABR aggressiveness (e.g., on known-flaky networks, start at lower quality to avoid rebuffer)
- **Voice preprocessing:** On-device voice activity detection and keyword spotting before sending to cloud

**Requirements:**

| ID | Requirement | Priority | Phase | Acceptance Criteria |
|----|-------------|----------|-------|---------------------|
| MC-AI-010 | Mobile and TV clients shall implement predictive pre-fetching of likely-next content based on viewing patterns | P2 | 2 | Given a user is 80% through an episode, then the client pre-fetches the first 10 seconds of the next episode; when auto-play triggers, playback starts in < 500ms |
| MC-AI-011 | All clients shall cache the most recent personalized home screen for instant display on app launch | P1 | 1 | Given a user reopens the app within 4 hours, then the cached home screen displays within 500ms while fresh data loads in the background |
| MC-AI-012 | Mobile clients shall implement adaptive ABR initialization based on learned network patterns | P2 | 3 | Given a user is on a known-slow cellular network, then the player starts at a lower initial bitrate to avoid early rebuffer; given a known-fast Wi-Fi network, then the player starts at a higher bitrate |
| MC-AI-013 | Clients shall send engagement telemetry (focus dwell time, scroll velocity, rail scroll depth) to feed recommendation models | P0 | 1 | Given a user scrolls past a recommendation rail without interacting, then a "rail_scroll_through" event with dwell times per item is sent to the Analytics Collector within 5 seconds |

### 5.3 AI-Powered Cast/AirPlay Selection

**Description:** When multiple cast-compatible devices are available on the network, the AI suggests the most likely target device based on time-of-day and historical cast behavior.

| ID | Requirement | Priority | Phase | Acceptance Criteria |
|----|-------------|----------|-------|---------------------|
| MC-AI-020 | When multiple cast targets are available, the most likely device shall be pre-selected based on usage patterns | P2 | 3 | Given a user always casts to "Living Room TV" in the evening, when they tap the Cast button at 8 PM, then "Living Room TV" is pre-selected (top of list) |

---

## 6. Non-Functional Requirements

### Performance Targets (Per Platform)

| ID | Metric | Android TV | Apple TV | Web | iOS | Android | Tizen | webOS | STB |
|----|--------|-----------|----------|-----|-----|---------|-------|-------|-----|
| MC-NFR-001 | App cold launch time | < 3s | < 3s | < 3s (FCP) | < 2s | < 2s | < 4s | < 4s | < 5s |
| MC-NFR-002 | Home screen render | < 2s | < 2s | < 2s | < 1.5s | < 1.5s | < 3s | < 3s | < 3s |
| MC-NFR-003 | Playback start time | < 1.5s | < 1.5s | < 2s | < 1.5s | < 1.5s | < 2s | < 2s | < 2.5s |
| MC-NFR-004 | Channel change time | < 1.5s | < 1.5s | < 2s | N/A | N/A | < 2s | < 2s | < 2s |
| MC-NFR-005 | Memory usage (peak) | < 300MB | < 256MB | < 400MB | < 200MB | < 250MB | < 256MB | < 256MB | < 200MB |
| MC-NFR-006 | App size (installed) | < 50MB | < 40MB | N/A | < 80MB | < 60MB | < 30MB | < 30MB | < 40MB |

### Battery and Resource Usage (Mobile)

| ID | Requirement | Target | Measurement |
|----|-------------|--------|-------------|
| MC-NFR-010 | Battery consumption during 1-hour playback (Wi-Fi, screen at 50%) | < 15% battery drain | Lab measurement on reference device (iPhone 14, Pixel 7) |
| MC-NFR-011 | Battery consumption during background download | < 5% per hour of downloading | Lab measurement |
| MC-NFR-012 | Cellular data usage for 1 hour of medium-quality streaming (720p) | < 1.5 GB | Network traffic measurement at player level |

### Availability and Reliability

| ID | Requirement | Target | Measurement |
|----|-------------|--------|-------------|
| MC-NFR-020 | BFF availability (per BFF) | 99.95% monthly uptime | Server-side uptime monitoring |
| MC-NFR-021 | Client crash rate | < 0.5% of sessions | Crash reporting (Firebase Crashlytics / Sentry) |
| MC-NFR-022 | Client ANR rate (Android) / hang rate | < 0.2% of sessions | Platform-specific hang detection |
| MC-NFR-023 | Graceful degradation | App remains functional when BFF returns partial data (missing AI scores, missing images) | Integration test: BFF returns degraded response; client renders without crash |

### Scale

| ID | Requirement | Target | Measurement |
|----|-------------|--------|-------------|
| MC-NFR-030 | TV BFF throughput | 4,000 RPS (Phase 1), 20,000 RPS (Phase 4) | Load test with simulated TV client traffic patterns |
| MC-NFR-031 | Mobile BFF throughput | 3,000 RPS (Phase 1), 15,000 RPS (Phase 4) | Load test with simulated mobile client traffic patterns |
| MC-NFR-032 | Web BFF throughput | 2,000 RPS (Phase 1), 10,000 RPS (Phase 4) | Load test with simulated web client traffic patterns |
| MC-NFR-033 | BFF response latency | p99 < 200ms for all BFF endpoints | Server-side latency measurement under load |

### Accessibility

| ID | Requirement | Target | Measurement |
|----|-------------|--------|-------------|
| MC-NFR-040 | All platforms shall meet WCAG 2.1 AA compliance | 100% AA compliance at launch | Automated accessibility audit + manual testing |
| MC-NFR-041 | Android and iOS clients shall support TalkBack / VoiceOver screen readers for all screens | Full screen reader support | Manual testing with screen readers on all screens |
| MC-NFR-042 | TV clients shall support audio description tracks where available | Audio description selectable in player settings | Functional test with audio description content |
| MC-NFR-043 | All clients shall support closed captions / subtitles with configurable presentation (size, color, background) | Subtitle customization across all platforms | Manual testing on each platform |

---

## 7. Technical Considerations

### BFF Architecture

The BFF layer is the primary API surface for all clients. Three BFF services run as Go microservices on Kubernetes, each optimized for its client family.

**TV BFF (Go):**
- Serves: Android TV, Apple TV, Samsung Tizen, LG webOS, STBs
- Responsibilities: Aggregate data from backend services (Catalog, EPG, Recommendation, Profile, Bookmark, Entitlement), compose pre-laid-out screen payloads, include D-pad focus management metadata, pre-size image URLs for TV resolutions (1920x1080, 3840x2160)
- Response format: JSON with screen layout structure (sections, rails, tiles with position data)
- Payload size: < 50KB for home screen initial load
- Caching: Redis cache for per-profile composed screens (TTL: 5 minutes)

**Mobile BFF (Go):**
- Serves: iOS, Android
- Responsibilities: Same aggregation as TV BFF but with compact payloads, mobile-DPI image URLs, offline manifest generation, touch layout hints
- Additional: Push notification registration endpoints, download management APIs, offline sync endpoints
- Payload size: < 30KB for home screen initial load
- Caching: Redis cache for per-profile composed screens (TTL: 5 minutes)

**Web BFF (Go):**
- Serves: Web browsers
- Responsibilities: Same aggregation with SEO-friendly metadata (Open Graph tags, JSON-LD structured data), responsive layout hints, SSR data endpoints, service worker cache hints
- Additional: Server-side rendering data endpoint for initial page load (hydration data)
- Payload size: < 40KB for home screen initial load
- Caching: CDN cache for anonymous pages (TTL: 5 minutes), Redis for per-profile data

### Per-Platform Player Integration

| Platform | Player | DRM | Codecs | Offline | Notes |
|----------|--------|-----|--------|---------|-------|
| Android TV | ExoPlayer/Media3 3.3+ | Widevine L1 (certified devices) | HEVC, H.264, AV1 (device-dependent) | Optional (OEM-dependent) | Use Media3 for latest features; hardware HEVC decoding required for 4K |
| Apple TV | AVPlayer/AVKit | FairPlay | HEVC, H.264, Dolby Vision | No | AVKit provides native player chrome; use custom overlay for branded UI |
| Web (Chrome/Firefox/Edge) | Shaka Player 4.x | Widevine (L1 via EME on hardware-secured machines, L3 otherwise) | H.264, VP9, AV1 (browser-dependent) | No | L1 requires hardware security; L3 is software-only (max 720p for premium content) |
| Web (Safari) | Shaka Player 4.x | FairPlay (via EME) | HEVC, H.264 | No | FairPlay via EME in Safari 14.1+; HLS-specific handling |
| iOS | AVPlayer/AVKit | FairPlay | HEVC, H.264 | Yes (AVAssetDownloadTask) | Use AVAssetDownloadTask for background downloads; FairPlay offline license |
| Android Mobile | ExoPlayer/Media3 3.3+ | Widevine L1/L3 | HEVC, H.264 | Yes (ExoPlayer download helper) | L1 for certified devices (full resolution); L3 for others (max 540p premium) |
| Samsung Tizen | Shaka Player 4.x + Tizen native DRM | Widevine L1 (Tizen native module) | HEVC, H.264 | No | Use Tizen AVPlay for DRM interaction; Shaka for manifest parsing |
| LG webOS | Shaka Player 4.x + webOS native DRM | Widevine L1 (webOS native module) | HEVC, H.264 | No | Similar to Tizen: webOS media pipeline for DRM, Shaka for ABR/manifest |
| Chromecast | Cast Application Framework | Widevine L1 | HEVC, H.264 | No | Custom receiver app; DRM handled by Chromecast firmware |

### Client Telemetry Schema

All clients emit standardized telemetry events via a shared schema. Events are sent to the Analytics Collector service (Go) via HTTPS (batched every 5 seconds or 20 events, whichever comes first).

**Core Event Schema:**
```
{
  "event_type": "playback.started | browse.rail_scrolled | search.query | ...",
  "timestamp": "ISO 8601",
  "session_id": "uuid",
  "user_id": "uuid",
  "profile_id": "uuid",
  "device_type": "android_tv | apple_tv | web | ios | android | tizen | webos | stb",
  "app_version": "2.1.3",
  "os_version": "Android 14",
  "connection_type": "wifi | cellular | ethernet",
  "attributes": { ... event-specific payload ... }
}
```

**Event Categories:**
- **Playback:** start, stop, pause, seek, error, heartbeat (every 30 seconds), quality change
- **Browse:** screen_view, rail_scroll, tile_click, search_query, search_result_click
- **EPG:** grid_open, channel_select, program_select, reminder_set, record_action
- **User:** login, logout, profile_switch, preference_change, device_register
- **System:** app_launch, app_background, crash, ANR

### Automated Testing Strategy

| Test Type | Tool | Platforms | Frequency | Coverage Target |
|-----------|------|-----------|-----------|-----------------|
| Unit tests | JUnit/XCTest/Jest | All | Every commit | > 80% line coverage |
| UI tests | Espresso/XCUITest/Playwright | Android TV, Apple TV, Web, iOS, Android | Every PR merge | Critical user journeys (20 scenarios) |
| Integration tests | Custom + BFF test suite | BFF layer | Every PR merge | All BFF endpoints |
| Performance tests | Custom profiling | All | Weekly (nightly on CI) | Launch time, memory, frame rate benchmarks |
| DRM validation | Custom + DRM provider tools | All | Per release | DRM playback functional on all target security levels |
| Accessibility | Accessibility Scanner / axe-core | Android, iOS, Web | Per release | WCAG 2.1 AA compliance |
| Smart TV certification | Samsung/LG lab tools | Tizen, webOS | Per release | Passes manufacturer certification test suites |

### Certification Requirements

| Platform | Certification | Lead Time | Key Requirements |
|----------|--------------|-----------|-----------------|
| Google TV | Google TV App Quality Requirements | 2-4 weeks | Watch Next API integration, leanback UI guidelines, 4K/HDR support, TalkBack support |
| Apple TV | App Store Review | 1-2 weeks | Apple HIG compliance, universal purchase support, tvOS UI guidelines |
| Samsung Tizen | Samsung TV App Certification | 4-8 weeks | Samsung UX guidelines, Smart Hub integration, memory/performance limits, IP control |
| LG webOS | LG Content Store Certification | 4-8 weeks | webOS UX guidelines, Magic Remote support, LG Account integration |
| Google Play | Google Play Console Review | 1-3 days | Material Design, target SDK compliance, 64-bit support |
| Apple App Store | App Store Review | 1-2 weeks | Apple HIG, App Tracking Transparency, privacy labels |

---

## 8. Dependencies

### Upstream Dependencies

| Dependency | Service/PRD | Nature | Impact if Unavailable |
|------------|------------|--------|----------------------|
| TV BFF | ARCH-001 | API layer for TV clients | TV clients cannot load data; show cached content or error |
| Mobile BFF | ARCH-001 | API layer for mobile clients | Mobile clients cannot load data; show cached content or error |
| Web BFF | ARCH-001 | API layer for web client | Web client cannot load data; show cached/SSR content |
| Recommendation Service | PRD-007 (AI UX) | Personalized content for home screen, rails, AI-curated EPG | Fallback to popularity-based content; reduced personalization |
| Entitlement Service | ARCH-001 | Content access verification | Cannot verify what user can play; deny playback or show generic catalog |
| Bookmark Service | ARCH-001 | Cross-device playback sync | "Continue Watching" unavailable; user must manually navigate to content |
| Profile Service | ARCH-001 | Multi-profile support | Single profile experience; no per-user personalization |
| Token Service (CAT) | ARCH-001 | CDN access authorization | Cannot start playback; CDN denies segment requests |
| CDN Routing Service | PRD-008 (AI Ops) | Optimal CDN selection per session | Fallback to default CDN; suboptimal quality possible |
| Feature Flag Service (Unleash) | ARCH-001 | Per-platform feature gating | All features enabled/disabled globally; no granular rollout |

### Downstream Dependencies (services depend on multi-client)

| Dependent | Nature | Integration |
|-----------|--------|-------------|
| All PRDs (001-005, 007-008) | Multi-client is the delivery vehicle for all user-facing features | Every user-facing requirement in other PRDs is rendered by a client app |
| Analytics / Telemetry | Client telemetry feeds the entire analytics and ML pipeline | Client events → Analytics Collector → Kafka → Data Lake → ML Training |
| QoE Service | Client-side QoE SDK provides playback quality measurements | Conviva SDK integrated in all players; QoE metrics flow to QoE Service |

### Cross-PRD Integration Points

- **PRD-001 (Live TV):** Live playback is rendered by each client's player. Channel change speed is a client-level metric. Mini-EPG overlay is client-rendered.
- **PRD-002 (TSTV):** Start Over and Catch-Up playback use the same player pipeline. TSTV-specific UI (catch-up-to-live button, "started X minutes ago" overlay) is client-implemented.
- **PRD-003 (Cloud PVR):** Recording management UI is client-rendered. "Record" actions from EPG trigger Recording Service calls via BFF.
- **PRD-004 (VOD/SVOD):** Browse, search, and playback are core client features. Offline downloads are mobile-client specific.
- **PRD-005 (EPG):** EPG grid and "Your Schedule" rendering is client-implemented with per-platform optimization (virtualized grid on TV, compact list on mobile).
- **PRD-007 (AI UX):** All AI-powered UX features (recommendations, conversational search, personalized thumbnails) are surfaced through client apps. On-device AI runs in client context.
- **PRD-008 (AI Ops):** Client telemetry feeds AIOps models. CDN routing decisions are consumed by client players for CDN selection/switching.

---

## 9. Success Metrics

| Metric | Description | Baseline | Phase 1 Target | Phase 2 Target | Phase 4 Target | Measurement Method |
|--------|-------------|----------|---------------|---------------|---------------|-------------------|
| Platform Coverage | Number of supported client platforms | 0 | 5 | 8 | 9 | Platform count |
| Cross-Device Resume Accuracy | % of cross-device sessions resuming within 5 seconds of stop position | 70% (industry) | 90% | 95% | 97% | Client telemetry: bookmark delta between devices |
| Feature Parity Gap | Max delay (days) between first-platform and last-platform feature release | N/A | < 14 days | < 10 days | < 7 days | Release tracking system |
| App Store Rating | Average user rating across app stores | N/A | > 4.2 | > 4.4 | > 4.5 | App store analytics |
| Client Crash Rate | % of sessions experiencing a crash | 1.2% (industry) | < 0.5% | < 0.3% | < 0.2% | Crash reporting (Crashlytics/Sentry) |
| Playback Start Time (p95) | Time from play press to first video frame | 3-5s (industry) | < 2s | < 1.8s | < 1.5s | Client telemetry per platform |
| App Launch Time (p95) | Cold launch to interactive home screen | 4-6s (industry) | < 3s (native), < 4s (Smart TV) | < 2.5s / < 3.5s | < 2s / < 3s | Client telemetry per platform |
| Concurrent Stream Enforcement Accuracy | % of limit violations correctly detected | N/A | > 99% | > 99.5% | > 99.9% | Server-side session tracking |
| Offline Download Completion Rate | % of initiated downloads that complete successfully | N/A | > 95% | > 97% | > 98% | Client telemetry: download started vs completed |
| Cast/AirPlay Session Success Rate | % of cast attempts that successfully transfer playback | N/A | N/A | > 90% | > 95% | Client telemetry: cast initiated vs playing on target |

---

## 10. Open Questions & Risks

### Open Questions

| ID | Question | Owner | Impact | Target Decision Date |
|----|----------|-------|--------|---------------------|
| MC-OQ-001 | Should the Smart TV apps (Tizen, webOS) use a web-based framework or a native approach? Current recommendation is web-based (React) for cost efficiency, but native may offer better performance. | Engineering / Product | Affects Smart TV development timeline and performance | Month 3 |
| MC-OQ-002 | Should we build a custom Chromecast receiver or use the Default Media Receiver? Custom gives more control over UI and DRM but adds development cost. | Engineering | Affects cast experience and DRM support | Month 6 |
| MC-OQ-003 | What is the minimum Android version for Android TV support? Android 8 covers ~95% of devices but limits access to newer Media3 features. | Product / Engineering | Affects feature set and testing matrix | Month 1 |
| MC-OQ-004 | Should operator STBs use the Android TV codebase (for Android STBs) or a separate lightweight build? | Engineering / Business | Affects operator integration timeline and maintenance cost | Month 6 |
| MC-OQ-005 | How should we handle Widevine L3 (software DRM) on web and older Android devices? Some premium content owners require L1 (hardware DRM). | Product / Content Ops | Affects content availability on L3 devices | Month 2 |

### Risks

| ID | Risk | Severity | Likelihood | Mitigation |
|----|------|----------|------------|------------|
| MC-R-001 | **Smart TV performance constraints** -- Tizen and webOS devices have limited CPU/RAM (often < 2GB RAM, ARM SoCs) and may struggle with the React-based app, leading to poor UX and certification failure | High | High | Profile aggressively on lowest-tier target devices from day 1; move all heavy computation to BFF (server-side composition); implement tiered feature sets (basic EPG, fewer rails on low-end devices); budget 40% more development time for Smart TV optimization |
| MC-R-002 | **Smart TV certification delays** -- Samsung and LG certification processes take 4-8 weeks and rejections are common for performance, UX guideline violations, or DRM issues | High | High | Submit early pre-certification builds; engage Samsung/LG developer relations early; allocate dedicated QA resources for Smart TV testing; build certification compliance checks into CI/CD |
| MC-R-003 | **Cross-device bookmark inconsistency** -- Network latency, device clock drift, or race conditions cause bookmark mismatches across devices, frustrating users | Medium | Medium | Use server-authoritative bookmarks (Bookmark Service is source of truth); client sends heartbeats every 30 seconds; implement conflict resolution (latest-write-wins with client timestamp and server validation); alert on sync drift > 10 seconds |
| MC-R-004 | **Per-platform DRM complexity** -- Supporting Widevine, FairPlay, and PlayReady across 9 platforms creates a massive testing matrix and potential for DRM-specific playback failures | High | High | Use CPIX multi-DRM workflow with single encryption; automate DRM functional testing in CI/CD per platform; partner with DRM provider for managed key server; maintain a DRM compatibility matrix with known issues |
| MC-R-005 | **BFF as a bottleneck** -- BFF layer becomes a performance bottleneck or single point of failure since all client traffic flows through it | High | Medium | Auto-scale BFFs independently (HPA based on RPS and latency); implement circuit breakers per backend dependency; cache aggressively (Redis for per-profile, CDN for anonymous); implement graceful degradation (return partial response if one backend is slow) |
| MC-R-006 | **Feature parity drift** -- Different development timelines per platform cause feature parity to diverge, with some platforms lagging behind by weeks or months | Medium | High | Maintain a shared feature backlog with per-platform tracking; prioritize feature parity in sprint planning; use feature flags to dark-ship features that are waiting for all platforms; track feature parity gap as a team metric |
| MC-R-007 | **Offline DRM license management** -- Offline DRM licenses (48-hour validity) create edge cases: expired licenses during flights, license renewal failures, storage corruption | Medium | Medium | Implement pre-flight check: warn user if licenses expire within the next 24 hours; attempt background license renewal when online; graceful error messaging when license expires offline; allow re-download of expired content |

---

*This PRD defines the multi-client platform strategy, per-platform requirements, and cross-device experience specifications. It serves as the reference for client engineering teams, BFF development, and platform QA. All user-facing features defined in PRDs 001-005 and 007 are delivered through the client apps specified here.*
