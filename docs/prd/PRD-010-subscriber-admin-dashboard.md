# PRD-010: Subscriber Admin Dashboard

**Product:** OTT Platform PoC — Admin Portal
**Author:** Stefan
**Date:** February 2026
**Status:** Draft
**Dependencies:** TSTV Implementation Plan, DRM Implementation Plan (ClearKey + CENC)

---

## 1. Overview

### 1.1 Problem Statement

The OTT Platform PoC introduces several subscriber-facing systems — entitlements, subscriptions, TSTV, DRM-protected content, and (future) PVR — but provides no unified admin view of a subscriber's state. Without this, demonstrating the platform requires querying individual API endpoints or the database directly to answer basic operational questions: What can this subscriber watch? Why can't they access a channel? What have they been watching?

### 1.2 Purpose

The Subscriber Admin Dashboard provides a single pane of glass for managing and inspecting any subscriber in the system. It ties together the entitlement model, subscription management, viewing activity, and DRM license history into a coherent admin interface — demonstrating the kind of operational tooling a real OTT platform requires.

### 1.3 Success Criteria

| Metric | Target |
|--------|--------|
| Subscriber lookup to full overview | < 3 seconds |
| "Why can't subscriber X watch channel Y?" answerable from dashboard | Yes, in Phase 2 |
| All subscription CRUD operations available without touching the database | Yes, in Phase 1 |
| DRM license grant/denial history visible per subscriber | Yes, in Phase 2 |

---

## 2. Scope

### 2.1 In Scope

- Subscriber lookup, search, and overview
- Subscription and entitlement management (CRUD)
- Visual channel entitlement matrix per subscriber
- Viewing activity history (TSTV sessions)
- DRM license request log per subscriber
- Entitlement diagnostic tool ("Why can't I watch X?")
- PVR recording management (when PVR is implemented)
- Viewing analytics and usage patterns

### 2.2 Out of Scope

- Self-service subscriber portal (this is admin-only)
- Billing integration or payment processing
- Real-time notification to subscribers about subscription changes
- Multi-tenancy or role-based access control within the admin portal (single admin role for PoC)
- GDPR data export/deletion tooling (user IDs are not traceable to real persons in the PoC)

---

## 3. Phased Delivery

The dashboard is delivered in three phases, aligned with the platform's feature rollout.

### Phase 1 — Core (delivered with TSTV + DRM)

The foundation: subscriber identity, subscriptions, and entitlements. This phase makes the entitlement model tangible and testable through the admin UI.

### Phase 2 — Activity & Diagnostics (delivered after TSTV is running)

Adds operational insight: what subscribers are watching, why access is granted or denied, and diagnostic tools for support scenarios.

### Phase 3 — Advanced (delivered with PVR)

Adds PVR management, deeper analytics, and conversion tracking.

---

## 4. Functional Requirements — Phase 1: Core

### 4.1 Subscriber Lookup & Overview

**FR-1:** The admin dashboard shall provide a subscriber search function that searches by name, email, or user ID. Search shall return results within 500ms and support partial matching.

**FR-2:** The subscriber overview page shall display:
- Account details: name, email, user ID, account creation date, account status (active/suspended)
- Active subscriptions: product name, type, price, start date, status
- Total monthly spend (sum of active subscription prices)
- Quick-access links to all dashboard sub-sections for this subscriber

**FR-3:** The subscriber overview shall display an account status badge (active, suspended, cancelled) prominently. Status changes shall be logged with timestamp and admin user.

### 4.2 Subscription Management

**FR-4:** The admin shall be able to view all subscriptions for a subscriber: active, cancelled, and expired. Each subscription entry shows product name, product type (base, channel_package, channel, svod, tvod_rent, tvod_buy), price, start date, expiry date, and current status.

**FR-5:** The admin shall be able to add a subscription to a subscriber by selecting from available products. The subscription becomes active immediately upon creation.

**FR-6:** The admin shall be able to cancel or suspend an active subscription. Cancellation sets the status to 'cancelled' and records the cancellation timestamp. Suspension sets status to 'suspended' and can be reversed.

**FR-7:** For TVOD rental subscriptions, the dashboard shall display the rental countdown: hours remaining from first play, or "not yet started" if `first_played_at` is null.

**FR-8:** Subscription changes shall be reflected immediately in the entitlement matrix (FR-9) without requiring a page refresh.

### 4.3 Channel Entitlement Matrix

**FR-9:** The subscriber overview shall include a visual channel entitlement matrix displaying all channels in the system. For each channel:
- Green indicator if the subscriber is entitled (has an active subscription with a product that includes this channel)
- Red indicator if the subscriber is not entitled
- The product name(s) granting access (e.g., "via Sports Package")

**FR-10:** For channels the subscriber is not entitled to, the matrix shall show which product(s) would grant access and their price. This is the admin-facing equivalent of the subscriber upsell prompt.

**FR-11:** The entitlement matrix shall update in real-time when subscriptions are added or removed (FR-5, FR-6).

### 4.4 Product & Entitlement Admin

**FR-12:** The admin shall be able to view all products in the system with their entitlement mappings (which channels/content each product grants access to).

**FR-13:** The admin shall be able to create, modify, and deactivate products. Product modifications include: name, price, active status, and channel/content entitlement mappings.

**FR-14:** The admin shall be able to modify which channels a product grants access to. Changes take effect on the next entitlement check for all subscribers holding that product.

### 4.5 API Endpoints (Phase 1)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/subscribers` | GET | Search/list subscribers (query: name, email, user_id) |
| `/admin/subscribers/{id}` | GET | Full subscriber overview |
| `/admin/subscribers/{id}/subscriptions` | GET | List subscriber's subscriptions |
| `/admin/subscribers/{id}/subscriptions` | POST | Add subscription |
| `/admin/subscribers/{id}/subscriptions/{sub_id}` | PUT | Modify subscription (cancel, suspend, reactivate) |
| `/admin/subscribers/{id}/entitlements` | GET | Resolved entitlement matrix for subscriber |
| `/admin/products` | GET | List all products |
| `/admin/products` | POST | Create product |
| `/admin/products/{id}` | PUT | Modify product |
| `/admin/products/{id}/entitlements` | GET | List product's entitlement mappings |
| `/admin/products/{id}/entitlements` | PUT | Update product's entitlement mappings |

---

## 5. Functional Requirements — Phase 2: Activity & Diagnostics

### 5.1 Viewing Activity

**FR-15:** The subscriber detail page shall include a viewing activity section showing TSTV session history: channel, program name, session type (live, startover, catchup), start time, duration, and completion status.

**FR-16:** Viewing activity shall be sortable by date (most recent first) and filterable by session type and channel.

**FR-17:** The viewing activity section shall display a channel usage summary: number of sessions per channel over the last 7/30 days, visualized as a simple bar chart or ranked list.

### 5.2 DRM License Log

**FR-18:** The subscriber detail page shall include a DRM section showing recent license requests: timestamp, channel, result (granted/denied), and denial reason if applicable.

**FR-19:** The DRM section shall display summary statistics: total license requests, grant rate, denial rate, and most common denial reason.

**FR-20:** Denied license requests shall include the specific reason: 'not_entitled', 'subscription_expired', 'rental_expired', 'key_not_found', or 'auth_failed'.

### 5.3 Entitlement Diagnostic Tool

**FR-21:** The admin dashboard shall provide a "Why can't subscriber X watch channel Y?" diagnostic tool. The admin selects a subscriber and a channel, and the tool walks through the entitlement resolution chain step by step:

1. Is the subscriber account active? → Yes/No
2. Does the subscriber have any active subscriptions? → List them
3. Do any of those subscriptions include a product with this channel? → Yes (product name) / No
4. If no: which products would grant access? → List with prices
5. Are there channel-level TSTV restrictions? → startover_enabled, catchup_enabled, cutv_window

**FR-22:** The diagnostic result shall include a clear recommended action: "Add [Product Name] to grant access" or "Subscription [X] is suspended — reactivate to restore access."

**FR-23:** The diagnostic tool shall be accessible both as a standalone page and as a quick action from the entitlement matrix (clicking a red channel indicator).

### 5.4 API Endpoints (Phase 2)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/subscribers/{id}/viewing-activity` | GET | TSTV session history (query: days, type, channel) |
| `/admin/subscribers/{id}/viewing-summary` | GET | Channel usage summary |
| `/admin/subscribers/{id}/drm-log` | GET | DRM license request history |
| `/admin/subscribers/{id}/drm-summary` | GET | DRM grant/denial statistics |
| `/admin/subscribers/{id}/diagnose` | POST | Entitlement diagnostic (body: channel_id) |

---

## 6. Functional Requirements — Phase 3: Advanced

### 6.1 PVR Management

**FR-24:** When PVR is implemented, the subscriber detail page shall include a PVR section showing: scheduled recordings (pending), active recordings (recording), completed recordings, and series links.

**FR-25:** The admin shall be able to view recording details: program name, channel, scheduled time, status, recorded time range, expiry date, and storage impact (segment count / estimated size).

**FR-26:** The admin shall be able to delete a subscriber's recording or deactivate a series link on their behalf.

**FR-27:** The PVR section shall display aggregate storage impact: total recordings, total hours retained, and estimated disk usage locked by this subscriber's retention requirements.

### 6.2 Viewing Analytics

**FR-28:** The subscriber detail page shall include a viewing heatmap showing viewing patterns by day-of-week and time-of-day over the last 30 days. This provides a quick visual read of the subscriber's habits.

**FR-29:** The analytics section shall show TSTV usage patterns: ratio of live vs. start-over vs. catch-up viewing, average catch-up delay (hours between broadcast and catch-up play), and most-used catch-up channels.

### 6.3 Conversion Tracking

**FR-30:** The dashboard shall track denial-to-subscription conversion: when a subscriber encounters a DRM denial (or upsell prompt) and subsequently subscribes to a product that resolves the denial, this event is recorded and visible in the subscriber's history.

**FR-31:** The admin shall be able to view aggregate conversion data: across all subscribers, what percentage of DRM denials lead to a subscription within 24h / 7d / 30d. This is displayed as a summary card on the main admin dashboard.

### 6.4 API Endpoints (Phase 3)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/subscribers/{id}/recordings` | GET | PVR recordings and series links |
| `/admin/subscribers/{id}/recordings/{rec_id}` | DELETE | Delete recording |
| `/admin/subscribers/{id}/series-links/{link_id}` | DELETE | Deactivate series link |
| `/admin/subscribers/{id}/viewing-heatmap` | GET | Viewing pattern heatmap data |
| `/admin/subscribers/{id}/tstv-analytics` | GET | TSTV usage pattern analytics |
| `/admin/subscribers/{id}/conversions` | GET | Denial-to-subscription conversion events |
| `/admin/conversions/summary` | GET | Aggregate conversion statistics |

---

## 7. UI Design

### 7.1 Navigation Structure

The Subscriber Dashboard is a new top-level section in the existing Admin Portal, accessible from the main navigation alongside the existing Streaming (SimLive + TSTV Rules) section.

```
Admin Portal
├── Streaming                    (existing)
│   ├── Channel Control          (SimLive management)
│   └── TSTV Rules               (per-channel business rules)
├── Subscriber Dashboard         (new — this PRD)
│   ├── Subscriber Search        (Phase 1)
│   ├── Subscriber Detail        (Phase 1, extended in Phase 2 & 3)
│   └── Products & Entitlements  (Phase 1)
│   └── Diagnostic Tool          (Phase 2)
├── DRM                          (from DRM plan)
│   ├── Key Management
│   └── License Statistics
└── Platform Analytics           (Phase 3)
    └── Conversion Dashboard
```

### 7.2 Subscriber Detail Page Layout

The subscriber detail page is the primary workspace. It uses a tabbed or sectioned layout:

**Header:** Subscriber name, email, status badge, account age, total monthly spend

**Section: Subscriptions** (Phase 1)
- Active subscriptions table with inline actions (cancel, suspend)
- "Add Subscription" button — product picker
- Subscription history (collapsed by default)

**Section: Channel Entitlements** (Phase 1)
- Visual grid: all channels as tiles, green/red, with product attribution
- Clickable red tiles — diagnostic (Phase 2) or "Add subscription" shortcut (Phase 1)

**Section: Viewing Activity** (Phase 2)
- Session table: sortable, filterable
- Channel usage summary chart
- TSTV pattern breakdown

**Section: DRM** (Phase 2)
- Recent license requests table
- Grant/denial summary stats
- Link to diagnostic tool

**Section: PVR** (Phase 3)
- Recordings table with status, expiry, storage impact
- Series links list
- Storage summary

**Section: Analytics** (Phase 3)
- Viewing heatmap
- Conversion events

---

## 8. Non-Functional Requirements

### 8.1 Performance

| Requirement | Target | Rationale |
|---|---|---|
| Subscriber search response | < 500ms | Admin must find subscribers quickly |
| Subscriber detail page load (Phase 1 data) | < 1 second | Core overview must be fast |
| Subscriber detail page load (all phases) | < 3 seconds | Acceptable for full data load with activity history |
| Entitlement matrix computation | < 200ms | Must feel instant when subscriptions change |
| Diagnostic tool result | < 1 second | Step-by-step resolution should feel real-time |

### 8.2 Data Integrity

**NFR-1:** Subscription changes made through the admin dashboard shall take effect immediately for all downstream systems (entitlement checks, DRM license decisions, TSTV manifest access). No cache invalidation delay.

**NFR-2:** The entitlement matrix shall always reflect the current state of subscriptions and product mappings. Stale data is not acceptable — if a subscription was just cancelled, the matrix must show the channel as red on the next render.

### 8.3 Audit Trail

**NFR-3:** All admin actions that modify subscriber state (add/cancel/suspend subscription, delete recording, deactivate series link) shall be logged with: action type, target subscriber, admin user, timestamp, and before/after state.

**NFR-4:** The audit log shall be viewable per subscriber as a chronological event list.

---

## 9. Dependencies

### 9.1 Phase 1 Dependencies

| Dependency | Source | Status |
|------------|--------|--------|
| Entitlement model (products, product_entitlements, user_subscriptions) | TSTV Implementation Plan | Planned |
| User authentication and admin role | Existing platform | Exists |
| Admin portal framework (AdminPage.tsx) | Existing platform | Exists |
| Channel and schedule data | Existing platform | Exists |

### 9.2 Phase 2 Dependencies

| Dependency | Source | Status |
|------------|--------|--------|
| TSTV sessions table and recording | TSTV Implementation Plan | Planned |
| DRM key management and license logging | DRM Implementation Plan | Planned |
| SimLive streaming infrastructure running | TSTV Implementation Plan | Planned |

### 9.3 Phase 3 Dependencies

| Dependency | Source | Status |
|------------|--------|--------|
| PVR recordings and series links | TSTV Plan (Future: PVR Extension) | Deferred |
| Viewing analytics aggregation | New (built in this phase) | Not started |

---

## 10. Implementation

### 10.1 Files to Create / Modify

**Phase 1:**

| File | Action |
|------|--------|
| `backend/app/routers/admin_subscribers.py` | Create — subscriber search, detail, subscription CRUD |
| `backend/app/routers/admin_products.py` | Create — product and entitlement mapping CRUD |
| `backend/app/services/entitlement_service.py` | Create — entitlement resolution logic (shared with DRM, TSTV) |
| `backend/app/schemas.py` | Modify — add subscriber dashboard schemas |
| `frontend-client/src/pages/admin/SubscriberSearchPage.tsx` | Create |
| `frontend-client/src/pages/admin/SubscriberDetailPage.tsx` | Create |
| `frontend-client/src/pages/admin/ProductsPage.tsx` | Create |
| `frontend-client/src/components/admin/EntitlementMatrix.tsx` | Create |
| `frontend-client/src/components/admin/SubscriptionManager.tsx` | Create |

**Phase 2:**

| File | Action |
|------|--------|
| `backend/app/routers/admin_subscribers.py` | Modify — add viewing activity, DRM log, diagnostic endpoints |
| `backend/app/services/diagnostic_service.py` | Create — entitlement diagnostic logic |
| `frontend-client/src/pages/admin/DiagnosticToolPage.tsx` | Create |
| `frontend-client/src/components/admin/ViewingActivity.tsx` | Create |
| `frontend-client/src/components/admin/DrmLog.tsx` | Create |
| `frontend-client/src/components/admin/ChannelUsageChart.tsx` | Create |

**Phase 3:**

| File | Action |
|------|--------|
| `backend/app/routers/admin_subscribers.py` | Modify — add PVR, analytics, conversion endpoints |
| `backend/app/services/analytics_service.py` | Create — viewing heatmap, TSTV patterns, conversion tracking |
| `frontend-client/src/components/admin/PvrManager.tsx` | Create |
| `frontend-client/src/components/admin/ViewingHeatmap.tsx` | Create |
| `frontend-client/src/components/admin/ConversionDashboard.tsx` | Create |

### 10.2 Implementation Steps

| # | Task | Phase | Scope |
|---|------|-------|-------|
| 1 | Entitlement service: shared resolution logic | Phase 1 | Backend |
| 2 | Subscriber search and detail API endpoints | Phase 1 | Backend |
| 3 | Subscription CRUD API endpoints | Phase 1 | Backend |
| 4 | Product and entitlement mapping API endpoints | Phase 1 | Backend |
| 5 | Subscriber search page | Phase 1 | Frontend |
| 6 | Subscriber detail page with subscription management | Phase 1 | Frontend |
| 7 | Channel entitlement matrix component | Phase 1 | Frontend |
| 8 | Products and entitlements admin page | Phase 1 | Frontend |
| 9 | Viewing activity API and session history component | Phase 2 | Full stack |
| 10 | DRM license log API and component | Phase 2 | Full stack |
| 11 | Entitlement diagnostic tool (API + UI) | Phase 2 | Full stack |
| 12 | Channel usage summary chart | Phase 2 | Frontend |
| 13 | PVR management API and component | Phase 3 | Full stack |
| 14 | Viewing heatmap and TSTV analytics | Phase 3 | Full stack |
| 15 | Denial-to-subscription conversion tracking | Phase 3 | Full stack |

---

## 11. Verification

### Phase 1

1. Admin searches for "Alice" — subscriber found, overview loads with account details
2. Alice has Basic + Sports — entitlement matrix shows ch1, ch4, ch5 green; ch2, ch3 red
3. Red channels show "Available via Entertainment Package (199 kr/mo)"
4. Admin adds Entertainment Package to Alice — ch2, ch3 turn green immediately
5. Admin cancels Sports Package — ch4 turns red, subscription shows as cancelled with timestamp
6. Admin creates new product — product appears in product list with correct entitlement mappings

### Phase 2

7. Subscriber detail shows Alice's last 20 TSTV sessions with correct metadata
8. DRM section shows 15 license grants and 3 denials (for ch2 before Entertainment was added)
9. Admin runs diagnostic: Alice + ch3 — "Access granted via Entertainment Package"
10. Admin runs diagnostic: Diana + ch4 — "Not entitled. Available via: Sports Package (299 kr/mo), All Channels (449 kr/mo). Recommended action: Add Sports Package."
11. Channel usage chart shows Alice watches ch1 most frequently

### Phase 3

12. Alice's PVR section shows 3 scheduled recordings, 12 completed, 1 series link
13. Storage impact: "47 hours retained, ~14 GB estimated"
14. Viewing heatmap shows Alice watches primarily 19:00–22:00 on weekdays
15. Conversion dashboard: "23% of DRM denials led to subscription within 7 days"

---

*This PRD should be read alongside PRD-002 (TSTV) and PRD-009 (Multi-DRM) for full technical context on the entitlement model, TSTV sessions, and DRM license flow.*
