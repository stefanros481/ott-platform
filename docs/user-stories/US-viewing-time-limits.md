# User Stories: Profile Viewing Time Limits

**Source Feature:** Viewing Time Restrictions per Profile
**Generated:** 2026-02-13
**Total Stories:** 24
**Phase:** 1 (Launch)

**Feature Summary:** Parents can configure daily viewing time limits on child profiles with configurable reset times, weekday/weekend schedules, educational content exemptions, cross-device server-side enforcement, client-side offline tracking, and parent PIN override for granting extra time. The main (adult) profile has unlimited viewing time by default.

---

## Epic 1: Viewing Time Configuration

### US-VTL-001: Configure Viewing Time Limit for Child Profile

**As a** parent
**I want to** set a daily viewing time limit on my child's profile in 15-minute increments
**So that** I can control how much time my child spends watching content each day

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** N/A (new feature)

**Acceptance Criteria:**
- [ ] Given a parent opens Parental Controls for a child profile, when they navigate to Viewing Time Limits, then a slider or stepper allows selecting a limit from 15 minutes to 8 hours in 15-minute increments
- [ ] Given a parent sets a limit (e.g., 2 hours), when they save, then the limit is persisted server-side and enforced immediately across all devices
- [ ] Given the adult/main profile, when viewing time settings are displayed, then it shows "Unlimited" and cannot be changed to a restricted value
- [ ] Given a profile without the child flag, then viewing time limit configuration is not available

**AI Component:** No

**Dependencies:** Profile Service (child flag), Auth/Entitlement Service (PIN verification)

**Technical Notes:**
- Viewing time settings stored in Profile Service as part of parental controls configuration
- Settings API: `PUT /profiles/{profileId}/parental-controls/viewing-time`
- Payload: `{ weekdayLimitMinutes: 120, weekendLimitMinutes: 180, resetTime: "06:00", educationalExempt: true }`

---

### US-VTL-002: Weekday vs Weekend Limit Schedule

**As a** parent
**I want to** set different viewing time limits for weekdays and weekends
**So that** my child can watch more on weekends when there's no school

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** N/A (new feature)

**Acceptance Criteria:**
- [ ] Given the viewing time settings screen, when a parent configures limits, then separate fields are shown for "Monday–Friday" and "Saturday–Sunday"
- [ ] Given weekday limit is 1 hour and weekend limit is 3 hours, when a child watches on Saturday, then the 3-hour weekend limit applies
- [ ] Given it is Friday and the reset time is 6:00 AM, when the clock passes 6:00 AM on Saturday, then the weekend limit applies for the new day
- [ ] Given both limits are set, when the parent clears one, then a validation error requires both to be set or both to be "Unlimited"

**AI Component:** No

**Dependencies:** US-VTL-001

**Technical Notes:**
- Day-of-week determination uses the device/profile timezone combined with the configured reset time
- Weekend definition is locale-aware (default Sat–Sun, configurable for markets where Friday–Saturday is the weekend)

---

### US-VTL-003: Configurable Daily Reset Time

**As a** parent
**I want to** set the time of day when my child's viewing allowance resets
**So that** the reset aligns with our household schedule (e.g., 6 AM rather than midnight)

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** N/A (new feature)

**Acceptance Criteria:**
- [ ] Given the viewing time settings, when configuring reset time, then a time picker allows selecting any hour from 00:00 to 23:00 in 1-hour increments
- [ ] Given the reset time is set to 06:00, when the clock passes 6:00 AM local time, then the child's remaining time resets to the full daily allowance
- [ ] Given a child has 0 minutes remaining at 11 PM, when the reset time is 6:00 AM, then viewing remains locked until 6:00 AM
- [ ] Given no reset time is explicitly configured, then the default reset time is 06:00 AM local time
- [ ] Given the reset time changes from 06:00 to 08:00, when saved mid-day, then the change takes effect at the next reset cycle (not retroactively)

**AI Component:** No

**Dependencies:** US-VTL-001, Profile Service (timezone from profile or device)

**Technical Notes:**
- Reset time stored as `HH:00` in the profile's configured timezone
- Server computes reset boundaries using profile timezone; communicates next reset timestamp (UTC) to clients

---

### US-VTL-004: PIN Protection for Parental Control Settings

**As a** parent
**I want to** protect all parental control settings (including viewing time limits) with a PIN
**So that** my child cannot modify their own viewing restrictions

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** N/A (new feature)

**Acceptance Criteria:**
- [ ] Given a user navigates to Parental Controls in settings, when the section loads, then a PIN entry screen is shown before any settings are visible
- [ ] Given the correct 4-digit PIN is entered, when verified, then the parental controls section unlocks for the current session (no re-prompt until session ends or 15-minute timeout)
- [ ] Given an incorrect PIN is entered 5 times, when the 5th attempt fails, then a 30-minute lockout is enforced with a countdown timer displayed
- [ ] Given no PIN has been set, when a parent first accesses Parental Controls, then they are prompted to create a 4-digit PIN before proceeding
- [ ] Given the user is on the adult/main profile, then PIN is required only for accessing Parental Controls settings — not for switching to the profile

**AI Component:** No

**Dependencies:** Auth Service (PIN storage — hashed, not plaintext)

**Technical Notes:**
- PIN stored as bcrypt hash in the Auth Service, scoped to the account (not per-profile)
- PIN verification endpoint: `POST /accounts/{accountId}/pin/verify`
- Rate limiting: 5 attempts per 30-minute window per device

---

## Epic 2: Time Tracking & Enforcement

### US-VTL-005: Server-Side Viewing Time Tracking

**As a** platform operator
**I want to** track viewing time per child profile on the server in real-time
**So that** the limit is enforced consistently regardless of which device the child uses

**Priority:** P0
**Phase:** 1
**Story Points:** XL
**PRD Reference:** N/A (new feature)

**Acceptance Criteria:**
- [ ] Given a child starts playback on any device, when the Playback Session Service creates a session, then the Viewing Time Service begins tracking elapsed time for that profile
- [ ] Given a child watches 45 minutes on the TV and then switches to a tablet, when the tablet starts playback, then the remaining time reflects 45 minutes already consumed
- [ ] Given two devices attempt simultaneous playback for the same child profile, then only one active stream is permitted (concurrent stream limit per child profile = 1)
- [ ] Given the server receives heartbeats from the client every 30 seconds, when a heartbeat is missed for 5+ minutes, then the session is considered paused/ended and the clock stops
- [ ] Performance: Viewing time balance query responds in < 100ms (p95)

**AI Component:** No

**Dependencies:** Playback Session Service, Profile Service, Redis (real-time counters)

**Technical Notes:**
- Viewing Time Service maintains a Redis counter per `{profileId}:{resetDate}` with TTL of 48 hours
- Client sends heartbeat every 30 seconds: `POST /viewing-time/heartbeat { sessionId, profileId, timestamp }`
- Balance query: `GET /viewing-time/balance/{profileId}` returns `{ usedMinutes, limitMinutes, remainingMinutes, nextResetTimestamp }`
- Counter incremented on each heartbeat (30-second granularity)

---

### US-VTL-006: Playback Blocking When Limit Reached

**As a** platform operator
**I want to** prevent a child profile from starting new playback when the daily limit is exhausted
**So that** viewing time limits are enforced even before the warning flow triggers

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** N/A (new feature)

**Acceptance Criteria:**
- [ ] Given a child profile has 0 minutes remaining, when they attempt to start any content, then playback is denied and the lock screen is shown
- [ ] Given a child profile has 0 minutes remaining, when they browse the catalog, then browsing remains fully functional (only playback is blocked)
- [ ] Given a parent grants extra time via PIN override, when the child attempts playback again, then playback starts normally
- [ ] Given the daily reset time passes, when the child attempts playback, then the full allowance is available and playback succeeds

**AI Component:** No

**Dependencies:** US-VTL-005, Playback Session Service (entitlement check integration)

**Technical Notes:**
- Viewing time check added to the playback session creation flow as an additional entitlement gate
- BFF includes `viewingTimeRemaining` in the playback eligibility response so clients can show appropriate UI before attempting playback

---

### US-VTL-007: Pause Stops the Viewing Clock

**As a** child viewer
**I want** paused content to not count against my viewing time
**So that** I'm not penalized for taking a break

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** N/A (new feature)

**Acceptance Criteria:**
- [ ] Given a child pauses playback, when 5 minutes of pause elapse with no interaction, then the viewing time clock stops
- [ ] Given the clock has stopped due to pause, when the child resumes playback, then the clock resumes immediately
- [ ] Given a child pauses for 3 minutes and then resumes, then the 3-minute pause is counted as viewing time (under the 5-minute threshold)
- [ ] Given a child pauses for 15 minutes, then only the first 5 minutes count as viewing time; the remaining 10 are not counted
- [ ] Given a child closes the app without explicitly pausing, when no heartbeat is received for 5 minutes, then the clock stops

**AI Component:** No

**Dependencies:** US-VTL-005

**Technical Notes:**
- Client sends explicit pause/resume events to the Viewing Time Service
- Server-side: if no heartbeat received for 5 minutes, mark session as paused
- Clock granularity is 30 seconds (heartbeat interval), so pause detection has ±30s accuracy

---

## Epic 3: Child-Facing Experience

### US-VTL-008: Remaining Time Indicator for Child

**As a** child viewer
**I want to** see how much viewing time I have left today
**So that** I can plan what to watch and avoid a surprise cutoff

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** N/A (new feature)

**Acceptance Criteria:**
- [ ] Given a child profile is active, when viewing the profile menu or settings, then remaining viewing time is displayed (e.g., "1h 15m left today")
- [ ] Given remaining time drops below 30 minutes, then the indicator changes color to amber/yellow as a subtle visual cue
- [ ] Given remaining time drops below 15 minutes, then the indicator changes color to red
- [ ] Given the child has unlimited time (adult profile), then no time indicator is shown
- [ ] Given the child is offline, then the locally tracked remaining time is displayed

**AI Component:** No

**Dependencies:** US-VTL-005, BFF (viewing time balance in profile response)

**Technical Notes:**
- BFF includes `viewingTimeBalance` in the profile context response, refreshed every 60 seconds
- Client caches balance and decrements locally between server refreshes for smooth countdown

---

### US-VTL-009: Pre-Limit Warning During Playback

**As a** child viewer
**I want to** be warned before my viewing time runs out
**So that** I'm not surprised by an abrupt stop in the middle of something I'm watching

**Priority:** P0
**Phase:** 1
**Story Points:** M
**PRD Reference:** N/A (new feature)

**Acceptance Criteria:**
- [ ] Given a child is watching content, when 15 minutes of viewing time remain, then a non-intrusive toast notification appears: "15 minutes of viewing time left today"
- [ ] Given the warning has been shown, when 5 minutes remain, then a second, more prominent notification appears: "5 minutes left — ask a parent for more time"
- [ ] Given the warnings are on screen, when the child dismisses them, then they disappear and do not reappear for that threshold
- [ ] Given the child is watching a short piece of content (< 15 min), when remaining time is less than the content duration, then the warning appears at playback start

**AI Component:** No

**Dependencies:** US-VTL-005, US-VTL-008

**Technical Notes:**
- Warning thresholds configurable server-side (default: 15 min and 5 min)
- Overlay rendered by the client player UI layer, not a system notification
- Client-driven based on locally tracked remaining time (server-synced)

---

### US-VTL-010: Friendly Lock Screen When Time Expires

**As a** child viewer
**I want to** see a friendly, non-punitive screen when my viewing time is used up
**So that** the experience feels positive rather than abruptly cut off

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** N/A (new feature)

**Acceptance Criteria:**
- [ ] Given a child's viewing time reaches zero during playback, when playback stops, then a kid-friendly lock screen appears with a cheerful message (e.g., "Great watching today! Time for something else.")
- [ ] Given the lock screen is displayed, then it includes suggested offline activities (e.g., "Read a book", "Play outside", "Draw something") as a rotating set
- [ ] Given the lock screen is displayed, then a "Need more time? Ask a parent" button is visible, leading to the parent PIN override prompt
- [ ] Given the lock screen is displayed, then the child can still navigate to the profile menu to see their profile but cannot start any playback
- [ ] Given the lock screen is displayed on a TV (big screen), then the activities are rendered with child-appropriate illustrations/icons

**AI Component:** No

**Dependencies:** US-VTL-006, US-VTL-009

**Technical Notes:**
- Lock screen is a full-screen overlay managed by the client app (not a system screen)
- Activity suggestions are a static list shipped with the client, rotated randomly per session
- Design must follow platform-specific accessibility guidelines (large text, high contrast, screen reader support)

---

## Epic 4: Parent Override & Extra Time

### US-VTL-011: Parent PIN Override for Extra Time

**As a** parent
**I want to** enter my PIN on the lock screen to grant my child extra viewing time
**So that** I can make exceptions without going into settings (e.g., during a road trip)

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** N/A (new feature)

**Acceptance Criteria:**
- [ ] Given the child lock screen is displayed, when a parent taps "Need more time? Ask a parent", then a PIN entry screen is shown
- [ ] Given the correct PIN is entered, then a quick-add menu appears with preset options: "+15 min", "+30 min", "+1 hour", "Unlimited for today"
- [ ] Given "+30 min" is selected, then 30 minutes are added to the child's remaining balance and playback resumes automatically
- [ ] Given "Unlimited for today" is selected, then viewing time tracking is suspended for the current day (until the next reset)
- [ ] Given an incorrect PIN is entered, then the same lockout policy applies as US-VTL-004 (5 attempts, 30-minute lockout)
- [ ] Given extra time is granted, then a server-side audit log records: timestamp, profileId, grantedMinutes, grantedBy (account)

**AI Component:** No

**Dependencies:** US-VTL-004 (PIN), US-VTL-005 (time tracking), US-VTL-010 (lock screen)

**Technical Notes:**
- API: `POST /viewing-time/override { profileId, additionalMinutes: 30 | -1 (unlimited), pin }` — PIN verified in the same request
- The override adjusts the Redis counter balance, not the configured limit
- "Unlimited for today" sets a flag that bypasses time checks until the next reset

---

### US-VTL-012: Extra Time Grant from Parent's Own Device

**As a** parent
**I want to** grant extra viewing time from my own phone without physically going to the TV
**So that** I can manage my child's time remotely if I'm in another room

**Priority:** P1
**Phase:** 1
**Story Points:** M
**PRD Reference:** N/A (new feature)

**Acceptance Criteria:**
- [ ] Given the parent is on their own profile on a mobile device, when they navigate to Parental Controls > [Child's name] > Viewing Time, then current remaining time is shown with a "Grant Extra Time" button
- [ ] Given the parent taps "Grant Extra Time", when they select a preset (+15 min, +30 min, +1 hour, Unlimited today), then the child's balance updates within 5 seconds on the child's device
- [ ] Given the child is currently on the lock screen, when extra time is granted remotely, then the lock screen dismisses automatically and the child can resume browsing/playback
- [ ] Given the grant is made, then no PIN re-entry is needed (parent is already authenticated in their profile session)

**AI Component:** No

**Dependencies:** US-VTL-011, WebSocket/push notification for real-time client update

**Technical Notes:**
- Real-time update to child's device via push notification or WebSocket event: `viewing_time_updated`
- Client on child's device listens for balance change events and refreshes UI accordingly

---

## Epic 5: Reporting & History

### US-VTL-013: Child Viewing History for Parents

**As a** parent
**I want to** see a detailed log of what my child watched and for how long
**So that** I can understand my child's viewing habits and have informed conversations about screen time

**Priority:** P1
**Phase:** 1
**Story Points:** L
**PRD Reference:** N/A (new feature)

**Acceptance Criteria:**
- [ ] Given a parent navigates to Parental Controls > [Child's name] > Viewing History, then a chronological log is shown grouped by day
- [ ] Given the history view, then each entry shows: title, date/time, duration watched, and device used
- [ ] Given the history view, then each day shows a total viewing time summary (e.g., "Tuesday Feb 11 — 1h 45m total")
- [ ] Given the history view, then educational content entries are visually tagged (e.g., a small badge) and shown separately in the daily total (e.g., "1h 45m counted + 30m educational")
- [ ] Given the history view, then at least 30 days of history is available
- [ ] Performance: History loads within 2 seconds for a 30-day view

**AI Component:** No

**Dependencies:** Viewing Time Service (event log), Analytics Service

**Technical Notes:**
- Viewing history sourced from the analytics event pipeline (not real-time counters)
- API: `GET /viewing-time/history/{profileId}?from=2026-01-14&to=2026-02-13`
- Response includes aggregated daily totals and per-session detail records

---

### US-VTL-014: Weekly Viewing Time Report for Parents

**As a** parent
**I want to** receive a weekly summary of my child's viewing time
**So that** I can monitor trends without checking the app every day

**Priority:** P1
**Phase:** 1
**Story Points:** M
**PRD Reference:** N/A (new feature)

**Acceptance Criteria:**
- [ ] Given a parent has viewing time limits configured for at least one child profile, when a week completes (based on reset time), then a weekly report is generated
- [ ] Given the report is generated, then it is available as an in-app notification in the parent's profile (not push notification by default)
- [ ] Given the report content, then it includes: daily viewing totals for the week, average daily viewing, comparison to limit (e.g., "used 80% of limit on average"), most-watched content, and educational content breakdown
- [ ] Given the parent's notification preferences, when they opt in to push notifications, then the weekly report is also sent as a push notification
- [ ] Given the parent has multiple child profiles, then the report covers all children in a single summary

**AI Component:** No

**Dependencies:** US-VTL-013, Notification Service

**Technical Notes:**
- Weekly report generated by a batch job (e.g., Sunday at reset time) from the analytics pipeline
- Report stored as a notification object; clients render it natively
- Future enhancement (Phase 2): AI-generated insights ("Emma watched 30% more this week — mostly cartoons")

---

## Epic 6: Offline & Multi-Device Enforcement

### US-VTL-015: Client-Side Offline Viewing Time Enforcement

**As a** platform operator
**I want to** enforce viewing time limits even when the child's device is offline
**So that** children cannot bypass limits by enabling airplane mode

**Priority:** P0
**Phase:** 1
**Story Points:** XL
**PRD Reference:** N/A (new feature)

**Acceptance Criteria:**
- [ ] Given a child's device goes offline (no network), when the child plays downloaded content, then the client tracks elapsed viewing time locally using a secure on-device counter
- [ ] Given the local counter reaches the configured limit, then playback is blocked and the lock screen is shown (offline variant without remote override option)
- [ ] Given the device reconnects to the network, then the locally tracked time syncs with the server within 60 seconds and the authoritative server-side balance is reconciled
- [ ] Given a discrepancy between client and server balances (e.g., time was granted remotely while offline), then the server balance takes precedence and the client adjusts accordingly
- [ ] Given the device clock is manually changed (attempted tamper), then the client detects clock drift using the last-known server timestamp and falls back to the most restrictive interpretation

**AI Component:** No

**Dependencies:** US-VTL-005, client-side secure storage

**Technical Notes:**
- Offline balance stored in platform-secure storage (Keychain on iOS, EncryptedSharedPreferences on Android, encrypted IndexedDB on web)
- Clock tampering detection: client compares device clock with last server-synced timestamp; if drift > 5 minutes, assume tamper and lock
- Offline lock screen omits the "Ask a parent" override (no network to verify PIN) — shows "Connect to the internet for a parent to grant more time"

---

### US-VTL-016: Cross-Device Session Handoff Accuracy

**As a** child viewer
**I want to** switch devices and have my remaining time be accurate on the new device
**So that** I don't lose viewing time or get extra time by switching devices

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** N/A (new feature)

**Acceptance Criteria:**
- [ ] Given a child watches 45 minutes on device A, when they start playback on device B, then device B shows approximately 45 minutes consumed (±1 minute accuracy)
- [ ] Given a child has an active session on device A, when they start playback on device B, then device A's session is terminated (single concurrent stream per child profile)
- [ ] Given device A was offline and had local tracking, when device A reconnects after device B has been used, then the server reconciles both devices' tracked time correctly
- [ ] Performance: Balance sync between devices completes within 5 seconds of session start on the new device

**AI Component:** No

**Dependencies:** US-VTL-005, US-VTL-015, Playback Session Service (concurrent stream enforcement)

**Technical Notes:**
- New session creation on device B triggers an immediate balance fetch from the Viewing Time Service
- Previous session on device A receives a termination event and flushes its local counter to the server

---

## Epic 7: Educational Content Exemption

### US-VTL-017: Educational Content Does Not Count Toward Limit

**As a** parent
**I want** educational content to not count against my child's viewing time
**So that** my child is encouraged to watch learning content without it reducing their entertainment time

**Priority:** P1
**Phase:** 1
**Story Points:** L
**PRD Reference:** N/A (new feature)

**Acceptance Criteria:**
- [ ] Given content is tagged as "educational" in the content provider's metadata, when a child watches it, then viewing time is tracked but NOT deducted from the daily limit
- [ ] Given educational content is playing, then the remaining time indicator does not decrease
- [ ] Given a child watches 30 minutes of educational content and 1 hour of regular content, when the limit is 2 hours, then 1 hour remains (not 30 minutes)
- [ ] Given the parent can see the history (US-VTL-013), then educational viewing time is shown separately (e.g., "Counted: 1h 00m | Educational (exempt): 30m")
- [ ] Given the educational exemption toggle in Parental Controls, when a parent disables it, then all content counts toward the limit equally

**AI Component:** No

**Dependencies:** Catalog Service / Metadata Service (educational tag), US-VTL-005

**Technical Notes:**
- Educational classification sourced from content provider metadata field `genre` or `tags` containing "educational", "kids-learning", or equivalent mapped values
- Viewing Time Service checks content classification on each heartbeat via a cached lookup from the Catalog Service
- The exemption is a per-profile toggle (default: enabled for child profiles)

---

### US-VTL-018: Educational Content Indicator in UI

**As a** child viewer (and parent)
**I want to** see which content is classified as educational
**So that** I (or my parent) know which content is exempt from the viewing limit

**Priority:** P1
**Phase:** 1
**Story Points:** S
**PRD Reference:** N/A (new feature)

**Acceptance Criteria:**
- [ ] Given content is classified as educational, when displayed in browse, search, or detail screens, then a small "Educational" badge is visible on the content card/tile
- [ ] Given a child profile is active with viewing time limits, when an educational title is playing, then a subtle on-screen indicator shows "This doesn't count toward your daily limit"
- [ ] Given the badge design, then it is consistent across all client platforms and meets accessibility contrast requirements

**AI Component:** No

**Dependencies:** Catalog Service (educational tag), US-VTL-017

**Technical Notes:**
- Badge rendered client-side based on `isEducational` boolean from the Catalog API content response
- Indicator during playback is shown once at playback start and dismisses after 5 seconds

---

## Epic 8: Settings Integration

### US-VTL-019: Unified Parental Controls Settings Screen

**As a** parent
**I want to** manage viewing time limits alongside content rating restrictions in one place
**So that** all parental controls are easy to find and configure

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** N/A (new feature)

**Acceptance Criteria:**
- [ ] Given a parent accesses Parental Controls (PIN-protected), then the screen shows sections for: Content Ratings, Viewing Time Limits, and Profile Management
- [ ] Given the Viewing Time Limits section, then each child profile is listed with its current weekday limit, weekend limit, and reset time
- [ ] Given a parent taps on a child profile's viewing time entry, then they can edit weekday limit, weekend limit, reset time, and educational exemption toggle
- [ ] Given the settings are saved, then changes take effect within 5 seconds on all active sessions for that profile
- [ ] Given the screen layout, then it is consistent with the existing parental rating enforcement UI (PRD-001)

**AI Component:** No

**Dependencies:** US-VTL-001, US-VTL-002, US-VTL-003, US-VTL-004, existing parental controls UI

**Technical Notes:**
- Extends the existing Parental Controls settings screen rather than creating a new navigation path
- Real-time enforcement: settings change triggers a push event to all active clients for the affected profile

---

### US-VTL-020: Default Configuration for New Child Profiles

**As a** parent
**I want** new child profiles to have sensible default viewing time limits
**So that** children are protected by default without requiring manual configuration

**Priority:** P1
**Phase:** 1
**Story Points:** S
**PRD Reference:** N/A (new feature)

**Acceptance Criteria:**
- [ ] Given a new child profile is created, then default viewing time limits are applied: 2 hours weekday, 3 hours weekend, 06:00 reset time, educational exemption enabled
- [ ] Given the defaults are applied, when the parent opens Parental Controls, then a banner says "Default viewing limits have been set — review and customize"
- [ ] Given the parent wants no viewing time limit on a child profile, then they can set both weekday and weekend to "Unlimited"

**AI Component:** No

**Dependencies:** Profile Service (profile creation flow)

**Technical Notes:**
- Defaults are configurable per deployment/market via server-side configuration
- Banner is shown once and dismissed after the parent views the settings (tracked via a `viewingTimeLimitsReviewed` flag)

---

## Epic 9: Non-Functional & Technical Enablers

### US-VTL-021: Viewing Time Service Infrastructure

**As a** platform engineer
**I want to** deploy a Viewing Time Service that handles real-time tracking at scale
**So that** viewing limits are enforced reliably across the platform

**Priority:** P0
**Phase:** 1
**Story Points:** XL
**PRD Reference:** N/A (new feature)

**Acceptance Criteria:**
- [ ] Given the Viewing Time Service is deployed, then it supports 500K concurrent child profile sessions with < 100ms (p95) latency on balance queries
- [ ] Given Redis is used for real-time counters, then data is replicated across availability zones with automatic failover (< 5 second recovery)
- [ ] Given the service receives heartbeats every 30 seconds per active session, then it sustains up to 16K heartbeats/second at peak (500K sessions / 30s)
- [ ] Given a Redis failure, then the service gracefully degrades: clients continue tracking locally and sync when the service recovers (no viewing time lost or duplicated)
- [ ] Given the service is deployed, then Prometheus metrics are emitted: active sessions, heartbeat rate, balance queries, overrides granted, enforcement blocks

**AI Component:** No

**Dependencies:** Kubernetes cluster, Redis cluster, Kafka (for event logging)

**Technical Notes:**
- Service written in Go for low-latency, high-throughput heartbeat handling
- Redis data structure: `HASH viewing_time:{profileId}:{resetDate}` with fields: `usedSeconds`, `limitSeconds`, `isUnlimited`, `lastHeartbeat`
- All state changes published to Kafka topic `viewing-time-events` for analytics and audit

---

### US-VTL-022: GDPR/COPPA Compliance for Viewing Time Data

**As a** platform operator
**I want to** ensure viewing time data collection complies with children's privacy regulations
**So that** the platform meets GDPR and COPPA requirements

**Priority:** P0
**Phase:** 1
**Story Points:** L
**PRD Reference:** N/A (new feature)

**Acceptance Criteria:**
- [ ] Given viewing time data is collected for a child profile, then it is classified as children's personal data under GDPR Article 8 and COPPA
- [ ] Given a parent requests data deletion for a child profile, then all viewing time history, counters, and audit logs are deleted within 30 days
- [ ] Given viewing time data, then it is used exclusively for enforcement and parental reporting — never for advertising, third-party sharing, or profiling beyond the stated purpose
- [ ] Given the platform's privacy policy, then viewing time tracking for children is explicitly disclosed with purpose limitation
- [ ] Given data retention, then detailed per-session viewing logs are retained for a maximum of 90 days; aggregated daily totals retained for 1 year

**AI Component:** No

**Dependencies:** Data Privacy Service, Profile Service (deletion cascade)

**Technical Notes:**
- Viewing time data tagged with `data_category: children_personal` in the data catalog
- Data deletion implemented via the existing GDPR right-to-erasure pipeline
- No cross-profile data sharing: a child's viewing time data is never used to train models that serve other users

---

### US-VTL-023: Viewing Time Observability & Alerting

**As a** platform operator
**I want to** monitor viewing time enforcement health and detect anomalies
**So that** limit enforcement failures are caught and resolved before they impact families

**Priority:** P1
**Phase:** 1
**Story Points:** M
**PRD Reference:** N/A (new feature)

**Acceptance Criteria:**
- [ ] Given the Viewing Time Service, then a Grafana dashboard shows: active tracked sessions, enforcement blocks (limit reached), overrides granted, heartbeat error rate, and sync conflicts
- [ ] Given the enforcement block rate drops to zero unexpectedly, then an alert fires (possible enforcement failure)
- [ ] Given heartbeat processing latency exceeds 500ms (p99), then an alert fires
- [ ] Given Redis replication lag exceeds 2 seconds, then an alert fires
- [ ] Given the service, then distributed tracing covers the full flow: heartbeat → counter update → balance query → enforcement decision

**AI Component:** No

**Dependencies:** US-VTL-021, Prometheus, Grafana, PagerDuty

**Technical Notes:**
- SLO: 99.9% of enforcement decisions are correct (no false permits, no false blocks)
- Key metric: `viewing_time_enforcement_accuracy` measured via reconciliation between client-reported and server-tracked totals

---

### US-VTL-024: Viewing Time E2E Integration Tests

**As a** platform engineer
**I want to** have automated end-to-end tests covering all viewing time scenarios
**So that** regressions in time tracking or enforcement are caught before deployment

**Priority:** P1
**Phase:** 1
**Story Points:** L
**PRD Reference:** N/A (new feature)

**Acceptance Criteria:**
- [ ] Given the test suite, then it covers: limit configuration, time tracking (online and offline), pause behavior, limit reached + lock screen, PIN override + extra time, cross-device sync, educational exemption, weekday/weekend transition, and reset time behavior
- [ ] Given the test suite runs in CI/CD, then all scenarios pass in the staging environment before production deployment
- [ ] Given the test suite, then at least one test simulates clock tampering (device clock set forward) and verifies the client falls back to restrictive mode
- [ ] Given the test suite, then cross-device scenarios use at least two simulated client types (e.g., Android TV + mobile)

**AI Component:** No

**Dependencies:** All US-VTL stories, CI/CD pipeline, staging environment

**Technical Notes:**
- E2E tests implemented using the platform's integration test framework
- Clock manipulation tests use mock time providers on both client and server
- Target: full suite runs in < 10 minutes in CI

---

## Dependency Map

```
US-VTL-001 (Configure Limit)
├── US-VTL-002 (Weekday/Weekend)
├── US-VTL-003 (Reset Time)
├── US-VTL-004 (PIN Protection)
│   └── US-VTL-011 (PIN Override)
│       └── US-VTL-012 (Remote Override)
├── US-VTL-005 (Server-Side Tracking) ★ Critical Path
│   ├── US-VTL-006 (Playback Blocking)
│   │   └── US-VTL-010 (Lock Screen)
│   │       └── US-VTL-011 (PIN Override)
│   ├── US-VTL-007 (Pause Stops Clock)
│   ├── US-VTL-008 (Remaining Time Indicator)
│   │   └── US-VTL-009 (Pre-Limit Warning)
│   ├── US-VTL-013 (Viewing History)
│   │   └── US-VTL-014 (Weekly Report)
│   ├── US-VTL-015 (Offline Enforcement)
│   │   └── US-VTL-016 (Cross-Device Sync)
│   └── US-VTL-017 (Educational Exemption)
│       └── US-VTL-018 (Educational Badge)
├── US-VTL-019 (Settings Screen)
├── US-VTL-020 (Default Config)
├── US-VTL-021 (Service Infrastructure) ★ Technical Enabler
├── US-VTL-022 (GDPR/COPPA Compliance)
├── US-VTL-023 (Observability)
└── US-VTL-024 (E2E Tests)
```

## Summary of Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Time window | Configurable reset time (default 6 AM) | Aligns with household schedules; avoids midnight edge cases |
| Limit reached behavior | Warning at 15m/5m + parent PIN override | Avoids abrupt cutoffs; empowers parents to make exceptions |
| Content scope | Educational content exempt (provider metadata) | Encourages learning without penalizing screen time |
| PIN scope | Settings access only (not profile switch) | Balances security with convenience for adult profile usage |
| Time granularity | 15-minute increments | Flexible enough for parents, simple enough for UI |
| Multi-device | Shared server-side tracking | Prevents circumvention by device switching |
| Day schedules | Weekday / Weekend split | Covers the most common parenting pattern with minimal complexity |
| Time visibility | Visible to child | Teaches self-regulation and avoids surprise |
| Extra time UX | Quick-add presets (+15m, +30m, +1h, Unlimited today) | Fast for parents in the moment; no complex forms |
| Parent notifications | Weekly report only | Non-intrusive; gives trends rather than real-time alerts |
| Pause behavior | Clock stops after 5 min idle | Fair to children; prevents gaming by pausing indefinitely |
| Lock screen | Friendly message + activity suggestions | Positive experience; avoids punitive messaging |
| Offline enforcement | Client-side tracking with server sync | Closes airplane-mode loophole; reconciles on reconnect |
| Educational tagging | Content provider metadata | Low implementation cost; leverages existing data pipeline |
| Settings UX | Unified parental controls section | Single destination for all child restrictions |
| Phase | Phase 1 (Launch) | Must-have for family-oriented platform positioning |
