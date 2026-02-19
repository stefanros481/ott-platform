# Feature Specification: Subscription Tiers, Entitlements & TVOD

**Feature Branch**: `012-entitlements-tvod`
**Created**: 2026-02-17
**Status**: Draft
**Input**: User description: "011 — Subscription Tiers, Entitlements & TVOD"

## Overview

This feature activates the platform's monetization model. The subscription and entitlement data structures are already in place but have never been enforced — content is currently accessible to all users regardless of their subscription tier. This feature:

1. Enforces subscription-based access to content packages (SVOD)
2. Introduces transactional video-on-demand (TVOD) — renting and buying individual titles
3. Surfaces all available access options to users in the catalog
4. Gives administrators tools to manage packages, assign content, and update user subscriptions
5. Protects against abuse via concurrent stream limits and rate limiting

**Key design principle:** A single title can simultaneously be free with a subscription, available to rent, and available to buy. These access paths are not mutually exclusive.

---

## Clarifications

### Session 2026-02-17

- Q: If the entitlement check fails (service unavailable), should the system fail-open or fail-closed? → A: Fail-closed with cache — deny new playback sessions if the entitlement check is unavailable; in-progress sessions may continue for up to 5 minutes using the last known cached entitlement result.
- Q: Can unauthenticated (guest) users browse the catalog and see offer pricing? → A: Yes — unauthenticated users may browse the catalog and see all available access options and pricing. Any playback attempt or TVOD transaction redirects to login.
- Q: Can a title have multiple active offers of the same type (e.g., two different rental durations)? → A: No — at most one active offer per type per title (one rent offer, one buy offer). Admins must deactivate the existing offer before creating a new one of the same type.
- Q: What scope should rate limiting cover? → A: All authenticated API requests per user (e.g., 100 requests/minute); TVOD transaction endpoints get an additional stricter per-user limit to prevent transaction abuse.
- Q: When two devices simultaneously attempt to claim the last available stream slot, how is the conflict resolved? → A: First write wins — whichever session request is processed first claims the slot; the second receives the over-limit error immediately.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Subscription Content Access Enforcement (Priority: P1)

A subscriber wants to watch content included in their subscription package. Today, all content is freely accessible regardless of subscription status. After this feature, the system verifies that the user's active subscription includes the requested title before allowing playback. Users without a matching subscription see a clear paywall with upgrade options.

**Why this priority**: Subscription enforcement is the foundation of the entire monetization model. Without it, all content is free to all users — the platform has no revenue protection. Every other entitlement story depends on this working correctly.

**Independent Test**: Create a subscription package, assign a title to it, create a subscriber and a non-subscriber, attempt playback as both. Subscriber plays successfully; non-subscriber sees an upgrade prompt.

**Acceptance Scenarios**:

1. **Given** a user with an active subscription that includes a content package, **When** they attempt to play a title in that package, **Then** playback is permitted without interruption.
2. **Given** a user with no subscription, **When** they attempt to play a title that requires a subscription, **Then** they are presented with a clear message explaining the access restriction and an option to subscribe or explore other access paths (rent/buy if available).
3. **Given** a user whose subscription has expired, **When** they attempt playback, **Then** access is denied and they are prompted to renew.
4. **Given** a title that is available to rent or buy in addition to being in a subscription package, **When** a non-subscriber views the title detail page, **Then** they see all available access options (subscription required, or rent for X, or buy for Y).

---

### User Story 2 - View Access Options in Catalog (Priority: P2)

A user browsing the catalog sees exactly how they can access each title: whether it's included in their subscription, available to rent, available to buy, or a combination. The catalog no longer shows a single generic "access level" — it shows a structured list of options with pricing so users can make informed decisions.

**Why this priority**: Users cannot make a purchase decision without knowing their options. This is the informational layer that enables TVOD (Stories 3 & 4) to work effectively. It also makes the subscription's value visible.

**Independent Test**: Set up a title with SVOD inclusion + rent offer + buy offer. Verify the catalog response returns all three options with correct pricing for a subscriber (subscription shown as "included") and a non-subscriber (subscription shown as an upgrade option).

**Acceptance Scenarios**:

1. **Given** a title that is included in a subscription package and also has rent and buy offers, **When** a subscribed user views the title, **Then** the catalog shows the title as "Included with your subscription" plus the rent and buy options.
2. **Given** a title with only a buy offer (no subscription, no rental), **When** any user views it, **Then** only the buy option is shown with its price.
3. **Given** a title available only through subscription, **When** a non-subscriber views it, **Then** the title is shown as locked with a subscription upgrade prompt and no rent/buy options.
4. **Given** a title with no offers and no package assignment, **When** any user views it, **Then** it is not accessible and is not shown in public catalog browse results.

---

### User Story 3 - Rent a Title (TVOD) (Priority: P3)

A user who is not a subscriber — or who wants to access a title outside their subscription package — can rent it for a fixed price. The rental grants time-limited access (e.g., 48 hours from purchase). After the rental window closes, the title is no longer playable.

**Why this priority**: Rental is a direct revenue path for users who don't want a full subscription. It also converts non-subscribers into paying customers. Technically simpler than purchase (a time-limited version of the same entitlement flow).

**Independent Test**: Create a rental offer for a title, complete a rental transaction as a non-subscriber, verify playback works during the rental window, verify playback fails after expiry.

**Acceptance Scenarios**:

1. **Given** a title with an active rental offer, **When** a user selects "Rent" and confirms the price, **Then** a rental entitlement is created for the rental window duration and playback begins immediately.
2. **Given** an active rental, **When** the rental window expires, **Then** the user can no longer play the title and the title is shown as "Rental expired" in their history.
3. **Given** a user who already owns (purchased) a title, **When** they view the title, **Then** the "Rent" option is not shown — only "Owned" is displayed.
4. **Given** a user who already has an active rental, **When** they view the title, **Then** the remaining time on their rental is displayed and they are not prompted to rent again.

---

### User Story 4 - Buy a Title (TVOD) (Priority: P4)

A user can permanently purchase a title for ongoing unlimited access. Unlike a rental, a purchase does not expire. The title appears in their library indefinitely, even if they cancel their subscription.

**Why this priority**: Purchasing represents a higher transaction value than renting and builds a user's permanent library — increasing long-term retention. Technically nearly identical to rental but without an expiry, making it straightforward to implement after rental.

**Independent Test**: Complete a purchase transaction, verify the title shows as "Owned" in the user's library, verify access persists after the rental window would have expired, verify access persists regardless of subscription status.

**Acceptance Scenarios**:

1. **Given** a title with a buy offer, **When** a user selects "Buy" and confirms the price, **Then** a permanent entitlement is created and the title is added to their library with no expiry.
2. **Given** a purchased title, **When** the user accesses the platform after their subscription lapses, **Then** purchased titles remain fully accessible.
3. **Given** a user who has both rented and subsequently purchased a title, **When** they view it, **Then** it shows as "Owned" and the rental period is irrelevant.

---

### User Story 5 - Admin Manages Subscription Packages (Priority: P5)

An administrator creates subscription packages (e.g., "Basic", "Premium", "Sports Add-on"), assigns titles to those packages, and manages which users are on which tier. This is the operational backbone that makes SVOD work.

**Why this priority**: Packages must exist before subscription enforcement (Story 1) and TVOD (Stories 3 & 4) can be demonstrated end-to-end. However, it's P5 here because for testing purposes, packages can be seeded while earlier stories are validated independently.

**Independent Test**: Log in as an admin, create a new package, assign 3 titles to it, set a test user to that package tier, verify the user can play those titles and not others.

**Acceptance Scenarios**:

1. **Given** an admin user, **When** they create a new content package with a name and tier level, **Then** the package is available for title assignment and user entitlement.
2. **Given** an existing package, **When** an admin assigns a title to it, **Then** all subscribers of that package immediately gain access to that title.
3. **Given** an admin, **When** they update a user's subscription tier, **Then** the user's access changes immediately — gaining access to new package content or losing access to content outside the new tier.
4. **Given** an admin, **When** they remove a title from a package, **Then** users who had SVOD-only access to that title immediately lose access (titles they separately purchased or rented are unaffected).

---

### User Story 6 - Concurrent Stream Limit Enforcement (Priority: P6)

A subscription tier defines how many devices can stream simultaneously. A Basic plan might allow 1 stream; Premium allows 3. When a user exceeds their plan's stream limit by starting a new playback session, the system blocks the new session or prompts the user to stop another active one.

**Why this priority**: This closes a significant abuse vector (credential sharing beyond plan limits) and is a standard subscription service expectation. Lower priority than core access control because it requires active viewing sessions to test end-to-end.

**Independent Test**: Configure a plan with a 1-stream limit, start playback on device A, then attempt to start playback on device B, verify device B is blocked or device A is interrupted.

**Acceptance Scenarios**:

1. **Given** a user on a 1-stream plan with an active session on device A, **When** they start playback on device B, **Then** they receive a message explaining the limit is reached and are offered the option to stop the existing session.
2. **Given** a user on a 2-stream plan, **When** they have 2 active sessions and attempt a 3rd, **Then** the 3rd session is blocked with a clear message.
3. **Given** a user whose session on device A was abandoned (no activity for 5 minutes), **When** they start playback on device B, **Then** the abandoned session is treated as ended and playback on device B is permitted.

---

### Edge Cases

- What happens when the entitlement service is unavailable at playback start? (New sessions are denied — fail-closed. A cached entitlement result may be used for up to 5 minutes for in-progress sessions; after that, the session ends gracefully. The failure is logged for operational visibility.)
- What happens when a user's subscription expires mid-playback? (Active session continues to completion; the next playback attempt is denied.)
- What happens when a title is removed from a package — do existing rentals continue? (Yes — TVOD entitlements are independent of package membership.)
- What happens when a rental offer is removed from a title — do existing rentals continue? (Yes — existing entitlements persist until their expiry date.)
- What happens when a user tries to rent a title they already have via subscription? (Allowed, but the UI should make clear they can already access it for free through their plan.)
- What happens to purchased titles if the user's account is suspended? (Access is suspended along with the account; entitlements are restored upon reactivation.)
- What happens when concurrent stream limit is reduced by a plan downgrade mid-session? (Active sessions over the new limit are allowed to complete; new sessions apply the new limit.)
- What happens when two devices simultaneously attempt to claim the last available stream slot? (First write wins — the session request processed first claims the slot; the second receives the over-limit error. No retry or queuing.)
- What happens when a title has a free offer (price = 0)? (Any user, including non-subscribers, can access it without a subscription or payment — entitlement is still created for tracking.)

---

## Requirements *(mandatory)*

### Functional Requirements

**Package Management**

- **FR-001**: Administrators MUST be able to create, update, and delete subscription packages, each with a name and tier designation.
- **FR-002**: Administrators MUST be able to assign and remove individual titles from subscription packages.
- **FR-003**: Administrators MUST be able to set and update a user's subscription tier.

**Offer Management**

- **FR-004**: The system MUST support defining transactional offers per title — each offer has a type (rent, buy, or free), a price, and a currency.
- **FR-005**: Rental offers MUST include a rental window duration (in hours) that starts at the time of purchase.
- **FR-006**: A title MUST be able to carry multiple simultaneous offer types: SVOD package inclusion, rental, and purchase — all independently configurable and non-exclusive.
- **FR-023**: A title MUST have at most one active offer per type (one active rent offer, one active buy offer, one active free offer) at any given time. Creating a new offer of the same type MUST require the existing offer of that type to be deactivated first.

**Access Control**

- **FR-007**: The system MUST enforce subscription tier access on both catalog browsing and playback — users without a valid entitlement covering a title MUST NOT be able to play it.
- **FR-008**: The system MUST check entitlement expiry; expired rental entitlements MUST NOT grant playback access.
- **FR-009**: The access check MUST evaluate the union of all valid access paths: active subscription package membership, non-expired TVOD rental, TVOD purchase, and free offers.
- **FR-021**: When the entitlement check service is unavailable, the system MUST deny new playback sessions (fail-closed). In-progress sessions MAY continue using a cached entitlement result for up to 5 minutes, after which the session ends gracefully. All entitlement check failures MUST be logged.

**Catalog Presentation**

- **FR-010**: Every title in catalog responses MUST include a structured list of available access options tailored to the requesting user — for example: "Included in your subscription", "Rent for $3.99 / 48 hours", "Buy for $9.99".
- **FR-011**: For a subscribed user whose plan includes a title, the response MUST indicate the title is accessible through their current subscription.
- **FR-012**: For a user without the relevant subscription, available rent and buy offers MUST be shown alongside a subscription upgrade prompt when applicable.
- **FR-022**: Unauthenticated (guest) users MUST be able to browse the catalog and view all available access options and pricing without logging in. Any attempt to initiate playback or complete a TVOD transaction MUST redirect the user to the login or registration flow.

**TVOD Transactions**

- **FR-013**: Users MUST be able to rent a title by selecting a rental offer, resulting in a time-limited access entitlement created immediately upon confirmation.
- **FR-014**: Users MUST be able to purchase a title by selecting a buy offer, resulting in a permanent access entitlement with no expiry.
- **FR-015**: The system MUST prevent redundant rental prompts — users with an active rental or purchase MUST NOT be offered the same transaction type again.
- **FR-016**: Rental and purchase entitlements MUST be device-independent — accessible from any of the user's authorized devices.

**Stream Limits**

- **FR-017**: Each subscription tier MUST have a configurable maximum number of concurrent active playback sessions.
- **FR-018**: When a user attempts to start a playback session that would exceed their plan's limit, the system MUST block the new session and present the user with an explanation and the option to stop an existing session.
- **FR-019**: Playback sessions with no activity heartbeat for 5 minutes MUST be automatically released from the concurrent stream count.

**Rate Limiting**

- **FR-024**: All authenticated API requests MUST be rate-limited per user, with a general threshold (e.g., 100 requests per minute). Requests exceeding the limit MUST be rejected with a clear error response indicating the limit and when requests may resume.
- **FR-025**: TVOD transaction endpoints (rent and buy) MUST enforce an additional, stricter per-user rate limit to prevent transaction abuse. Clients that exceed this limit MUST receive the same rejection response.

**Seed Data**

- **FR-020**: The platform MUST ship with seed data covering at least two subscription packages, sample title-to-package assignments, sample rental and buy offers, and at least one user account per subscription tier to support testing without manual setup.

### Key Entities

- **Subscription Package**: A named bundle of content accessible to subscribers on a matching tier. A package has a name and a tier designation; titles are assigned to it individually.
- **Title Offer**: An access option for a specific title — type (rent / buy / free), price, currency, and for rentals, a window duration in hours.
- **User Entitlement**: A record granting a specific user access to content. Sourced from either a subscription package (SVOD) or a TVOD transaction. Rental entitlements have an expiry timestamp; purchases do not.
- **Active Viewing Session**: A record of an in-progress playback, used to enforce concurrent stream limits. Considered abandoned and released if no heartbeat is received for 5 minutes.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of titles require a valid entitlement to play — no title is accessible to any user without a subscription, rental, purchase, or free offer covering it.
- **SC-002**: A user's access to a title is updated within 10 seconds of a package assignment change or TVOD transaction completing.
- **SC-003**: A rental entitlement becomes inaccessible within 60 seconds of its expiry time — users cannot continue playback on an expired rental.
- **SC-004**: The catalog access options list accurately reflects each requesting user's entitlements for 100% of titles — no false "included" or missing offer entries.
- **SC-005**: Concurrent stream limits are enforced in 100% of tested cases — users on a 1-stream plan cannot simultaneously stream on 2 devices.
- **SC-006**: An administrator can create a new subscription package, assign content, and update a user's tier in under 3 minutes using the admin interface.
- **SC-007**: A TVOD transaction (rent or buy) completes and grants playback access within 5 seconds of user confirmation.
- **SC-008**: The platform handles at least 500 concurrent entitlement checks with catalog list response times remaining ≤ 500ms at p95 under that load. *(PoC-scale acceptance: validated against local Docker Compose stack, not a distributed load test.)*

---

## Dependencies & Assumptions

### Dependencies

- **Feature 010 (Recommendations Quality & Live TV)**: Must be merged to main; this feature builds on the same platform baseline.
- **Existing data models**: `UserEntitlement`, `ContentPackage`, `PackageContent`, and `subscription_tier` on User are already modeled but unenforced — this feature activates and extends them. `ViewingSession` does **not** yet exist in the codebase and will be created as a new model in this feature. One additional new table (`title_offers`) is also introduced for transactional access pricing.
- **Admin panel**: An existing admin interface is in place for package and user management endpoints.

### Assumptions

- **Payment processing is out of scope**: TVOD transactions in this feature create entitlements directly without a real payment gateway. Confirmation is treated as successful payment. A future payment integration feature will add real money movement.
- **Subscription sign-up and cancellation flows are out of scope**: Subscription tier changes are handled manually via the admin panel in this feature.
- **Heartbeat mechanism**: Client applications send a playback heartbeat signal at regular intervals during active viewing; the backend tracks these to manage stream session state.
- **Prices are stored in the smallest currency unit** (e.g., cents for USD); client applications handle display formatting and currency symbols.
- **A "free" offer type** grants access to any user regardless of subscription tier — no transaction or payment required. Access is granted via direct `TitleOffer` lookup; no `UserEntitlement` record is created for free offers.
- **At least one admin account** already exists in the platform with access to the admin panel.
