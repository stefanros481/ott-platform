# Feature Specification: Profile Viewing Time Limits

**Feature Branch**: `006-viewing-time-limits`
**Created**: 2026-02-13
**Status**: Draft
**Input**: User description: "Restrict daily viewing time per child profile with configurable reset, weekday/weekend schedules, educational content exemptions, cross-device enforcement, and parent PIN override"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Parent Configures Daily Viewing Limits (Priority: P1)

A parent opens the Parental Controls section (protected by their account PIN) and sets a daily viewing time limit for their child's profile. They choose separate limits for weekdays and weekends using 15-minute increments (e.g., 1h 30m on school days, 3h on weekends). They also set the time their child's allowance resets each day (e.g., 6:00 AM to match their household wake-up routine). New child profiles receive sensible defaults (2 hours weekday, 3 hours weekend, 6:00 AM reset) that the parent can customize. The adult/main profile always has unlimited viewing time and cannot be restricted.

**Why this priority**: Without the ability to configure limits, no other part of this feature functions. This is the foundational capability that all enforcement, tracking, and reporting depends on.

**Independent Test**: Can be fully tested by creating a child profile, navigating to Parental Controls, setting weekday/weekend limits with a reset time, saving, and verifying the configuration persists across app restarts and devices.

**Acceptance Scenarios**:

1. **Given** a parent opens Parental Controls for a child profile, **When** they navigate to Viewing Time Limits, **Then** they can select a limit from 15 minutes to 8 hours in 15-minute increments for weekdays and weekends separately
2. **Given** a parent sets a weekday limit of 2 hours and weekend limit of 3 hours, **When** they save, **Then** the limits are persisted and enforced across all devices within 5 seconds
3. **Given** the viewing time settings screen, **When** a parent configures the reset time, **Then** they can select any hour from 00:00 to 23:00 in 1-hour increments (default: 06:00)
4. **Given** no PIN has been set, **When** a parent first accesses Parental Controls, **Then** they are prompted to create a 4-digit PIN before any settings are visible
5. **Given** a new child profile is created, **Then** default viewing time limits are applied automatically and a banner prompts the parent to review and customize them
6. **Given** the adult/main profile, **When** viewing time settings are displayed, **Then** it shows "Unlimited" and cannot be changed to a restricted value
7. **Given** an incorrect PIN is entered 5 times, **Then** a 30-minute lockout is enforced with a countdown timer displayed
8. **Given** a parent has forgotten their PIN, **When** they select "Forgot PIN" on the PIN entry screen, **Then** they can reset the PIN by entering their full account password, and the new PIN takes effect immediately

---

### User Story 2 - Child Watches Content With Time Tracking (Priority: P1)

A child logs into their profile and starts watching a show. The system tracks their viewing time in real time, shared across all devices. A subtle remaining-time indicator is visible in the profile menu (e.g., "1h 15m left today"). When they pause for more than 5 minutes, the clock stops — they are not penalized for breaks. When they resume, the clock resumes. If they switch from the TV to a tablet, their remaining time is accurate on the new device (±1 minute). Only one stream is allowed per child profile at a time to prevent circumvention.

**Why this priority**: Time tracking is the core enforcement mechanism. Without accurate, cross-device, pause-aware tracking, limits cannot be enforced meaningfully.

**Independent Test**: Can be fully tested by starting playback on a child profile, verifying the remaining time decreases, pausing for over 5 minutes and confirming the clock stops, then switching devices and confirming the balance is accurate.

**Acceptance Scenarios**:

1. **Given** a child starts playback on any device, **When** the session begins, **Then** the system begins tracking elapsed viewing time for that profile in real time
2. **Given** a child watches 45 minutes on the TV, **When** they start playback on a tablet, **Then** the tablet shows approximately 45 minutes consumed (±1 minute accuracy) and remaining time is correct
3. **Given** a child pauses playback, **When** 5 minutes of pause elapse with no interaction, **Then** the viewing time clock stops and does not count idle time
4. **Given** a child pauses for 3 minutes and resumes, **Then** the 3-minute pause is counted as viewing time (under the 5-minute threshold)
5. **Given** a child has an active session on device A, **When** they start playback on device B, **Then** device A's session is terminated (single concurrent stream per child profile)
6. **Given** remaining time drops below 30 minutes, **Then** the indicator changes to amber; below 15 minutes, it changes to red
7. **Given** the child closes the app without pausing, **When** no activity is detected for 5 minutes, **Then** the clock stops automatically

---

### User Story 3 - Child Receives Warnings and Friendly Lock Screen (Priority: P1)

As a child approaches their daily limit, they receive gentle, non-intrusive warnings during playback — first at 15 minutes remaining, then at 5 minutes remaining. When their time runs out, playback stops and a kid-friendly lock screen appears with a cheerful message ("Great watching today! Time for something else."), suggestions for offline activities, and a "Need more time? Ask a parent" button. The child can still navigate the app and see their profile but cannot start any new playback until their allowance resets or a parent grants extra time.

**Why this priority**: The child-facing experience is critical to the feature's usability and family acceptance. Abrupt cutoffs without warning would create a negative experience and undermine parent trust.

**Independent Test**: Can be fully tested by setting a short limit (e.g., 15 minutes), watching content until warnings appear, confirming warning timing and dismissal, then waiting for the limit to expire and verifying the lock screen appears with all expected elements.

**Acceptance Scenarios**:

1. **Given** a child is watching content, **When** 15 minutes of viewing time remain, **Then** a non-intrusive toast notification appears: "15 minutes of viewing time left today"
2. **Given** the first warning has been shown, **When** 5 minutes remain, **Then** a second, more prominent notification appears: "5 minutes left — ask a parent for more time"
3. **Given** warnings are on screen, **When** the child dismisses them, **Then** they disappear and do not reappear for that threshold
4. **Given** a child's viewing time reaches zero during playback, **Then** a kid-friendly lock screen appears with a cheerful message, suggested offline activities, and a parent override button
5. **Given** the lock screen is displayed, **Then** the child can navigate to the profile menu but cannot start any playback
6. **Given** a child profile has 0 minutes remaining, **When** they attempt to start any content, **Then** playback is denied and the lock screen is shown immediately
7. **Given** the daily reset time passes, **When** the child attempts playback, **Then** the full allowance is available and playback succeeds

---

### User Story 4 - Parent Grants Extra Time via PIN Override (Priority: P1)

When the lock screen appears on the child's device, a parent can tap the "Need more time?" button, enter their PIN, and choose from quick-add presets: +15 min, +30 min, +1 hour, or Unlimited for today. The extra time is granted immediately and playback resumes. Alternatively, the parent can grant extra time remotely from their own device (phone or tablet) without physically going to the child's screen — no PIN re-entry needed since the parent is already in their authenticated profile session. When extra time is granted remotely, the child's lock screen dismisses automatically within 5 seconds.

**Why this priority**: Without an override mechanism, the limit system is too rigid for real-world parenting (road trips, rainy days, special occasions). This is essential for parent acceptance of the feature.

**Independent Test**: Can be fully tested by letting a child's time expire, entering the parent PIN on the lock screen, selecting a time preset, and confirming playback resumes. For remote grant: accessing Parental Controls on a separate device, granting time, and confirming the child's device updates.

**Acceptance Scenarios**:

1. **Given** the child lock screen is displayed, **When** a parent taps "Need more time? Ask a parent" and enters the correct PIN, **Then** a quick-add menu appears with presets: "+15 min", "+30 min", "+1 hour", "Unlimited for today"
2. **Given** "+30 min" is selected, **Then** 30 minutes are added to the child's remaining balance and playback resumes automatically
3. **Given** "Unlimited for today" is selected, **Then** viewing time enforcement is suspended until the next daily reset
4. **Given** the parent is on their own device, **When** they navigate to Parental Controls > [Child's name] > Viewing Time and tap "Grant Extra Time", **Then** the child's balance updates within 5 seconds on the child's device
5. **Given** the child is on the lock screen, **When** extra time is granted remotely, **Then** the lock screen dismisses automatically and the child can resume browsing/playback
6. **Given** extra time is granted (locally or remotely), **Then** an audit log records the timestamp, the child profile, the amount granted, and the granting account

---

### User Story 5 - Educational Content Is Exempt From Limits (Priority: P2)

When a child watches content that is tagged as "educational" by the content provider, the viewing time is tracked for reporting purposes but does not count against their daily limit. The remaining time indicator does not decrease during educational content. In the parental viewing history, educational time is shown separately from counted time (e.g., "Counted: 1h 00m | Educational: 30m"). Parents can disable this exemption per child profile if they want all content to count equally. Content classified as educational displays a small badge in browse, search, and detail screens. During playback of educational content, a brief indicator confirms "This doesn't count toward your daily limit."

**Why this priority**: Educational exemption is a strong value-add for parents but not essential for the core limit enforcement to function. The feature works without it; this enhances the parenting experience.

**Independent Test**: Can be fully tested by having a child watch educational content, confirming the remaining time does not decrease, then watching regular content and confirming it does. Verify the history shows both separately.

**Acceptance Scenarios**:

1. **Given** content is tagged as "educational" in the content provider's metadata, **When** a child watches it, **Then** viewing time is tracked but NOT deducted from the daily limit
2. **Given** a child watches 30 minutes of educational content and 1 hour of regular content with a 2-hour limit, **Then** 1 hour remains (not 30 minutes)
3. **Given** the educational exemption toggle in Parental Controls, **When** a parent disables it, **Then** all content counts toward the limit equally
4. **Given** content is classified as educational, **When** displayed in browse or search screens, **Then** a small "Educational" badge is visible on the content card
5. **Given** educational content is playing on a child profile with viewing limits, **Then** a brief on-screen indicator confirms the content is exempt from the daily limit

---

### User Story 6 - Viewing Time Works Offline (Priority: P2)

When a child's device goes offline (airplane mode, no Wi-Fi), the device continues to track viewing time locally for downloaded content. When the configured limit is reached, playback is blocked and an offline variant of the lock screen appears (without the remote override option, since PIN verification requires a network connection). When the device reconnects, the locally tracked time syncs with the server within 60 seconds. If there is a discrepancy (e.g., extra time was granted remotely while the device was offline), the server balance takes precedence and the client adjusts accordingly. If the device clock is manually tampered with, the system detects the drift and falls back to the most restrictive interpretation.

**Why this priority**: Offline enforcement closes an obvious circumvention loophole (airplane mode). It is important for the feature's integrity but is technically complex and not part of the core online experience.

**Independent Test**: Can be fully tested by setting a limit, going offline, playing downloaded content until the limit triggers, confirming the offline lock screen appears, reconnecting, and verifying the server balance reconciles correctly.

**Acceptance Scenarios**:

1. **Given** a child's device goes offline, **When** the child plays downloaded content, **Then** the device tracks elapsed viewing time locally using a secure on-device counter
2. **Given** the local counter reaches the configured limit, **Then** playback is blocked and an offline lock screen appears showing "Connect to the internet for a parent to grant more time"
3. **Given** the device reconnects, **Then** the locally tracked time syncs with the server within 60 seconds and the server balance takes precedence
4. **Given** the device clock is manually changed, **Then** the system detects clock drift and falls back to the most restrictive interpretation
5. **Given** extra time was granted remotely while the device was offline, **When** the device reconnects, **Then** the updated balance is reflected and the child can resume watching

---

### User Story 7 - Parent Reviews Viewing History and Weekly Reports (Priority: P2)

A parent navigates to Parental Controls > [Child's name] > Viewing History and sees a chronological log grouped by day. Each entry shows the title watched, date/time, duration, and device used. Each day displays a total viewing time summary with educational time shown separately. At least 30 days of history is available. Additionally, at the end of each week, a summary report is generated and delivered as an in-app notification (with optional push notification). The report includes daily totals, average daily viewing, comparison to the configured limit, most-watched content, and educational content breakdown. If the parent has multiple children, the report covers all children in a single summary.

**Why this priority**: Reporting is valuable for parental oversight and trend monitoring, but the core feature (limits, tracking, enforcement) works without it. This is an important companion but not a launch blocker for the enforcement system itself.

**Independent Test**: Can be fully tested by having a child watch content over several days, then accessing the history screen and verifying all entries, daily totals, and educational breakdowns are accurate. Weekly report can be tested by triggering the batch report and verifying its contents.

**Acceptance Scenarios**:

1. **Given** a parent navigates to Viewing History for a child profile, **Then** a chronological log is shown grouped by day with title, date/time, duration, and device for each entry
2. **Given** the history view, **Then** each day shows a total viewing time summary (e.g., "Tuesday Feb 11 — 1h 45m total") with educational content shown separately
3. **Given** the history view, **Then** at least 30 days of history is available and loads within 2 seconds
4. **Given** a week completes, **Then** a weekly summary report is generated and available as an in-app notification in the parent's profile
5. **Given** the weekly report, **Then** it includes daily totals, average daily viewing, comparison to limits, most-watched content, and educational breakdown

---

### User Story 8 - Unified Parental Controls Experience (Priority: P2)

Viewing time limits are managed within the existing Parental Controls settings screen, alongside content rating restrictions. After entering their PIN, the parent sees organized sections for Content Ratings, Viewing Time Limits, and Profile Management. The Viewing Time section lists each child profile with its current weekday limit, weekend limit, and reset time. Tapping a child profile opens an editor for all viewing time settings including the educational exemption toggle. Changes take effect within 5 seconds on all active sessions for the affected profile. The visual design is consistent with the existing parental rating enforcement UI.

**Why this priority**: A unified settings experience prevents confusion and ensures parents can find all child restrictions in one place. This is important for usability but depends on the configuration and tracking stories being implemented first.

**Independent Test**: Can be fully tested by accessing Parental Controls, verifying all sections are visible, editing a child's viewing time settings, saving, and confirming the changes propagate to active sessions on other devices.

**Acceptance Scenarios**:

1. **Given** a parent accesses Parental Controls (PIN-protected), **Then** the screen shows sections for Content Ratings, Viewing Time Limits, and Profile Management
2. **Given** the Viewing Time Limits section, **Then** each child profile is listed with its current weekday limit, weekend limit, and reset time
3. **Given** a parent edits a child's viewing time settings and saves, **Then** changes take effect within 5 seconds on all active sessions for that profile
4. **Given** the settings screen layout, **Then** it is visually consistent with the existing parental rating enforcement UI

---

### Edge Cases

- What happens when the reset time crosses a weekday/weekend boundary (e.g., Friday night to Saturday morning with a 6 AM reset)? The system applies the new day type's limit at reset time — so the Saturday limit kicks in at 6 AM Saturday.
- What happens when a parent changes the reset time mid-day after the child has already used some time? The change takes effect at the next reset cycle, not retroactively. Current day's balance is unchanged.
- What happens when a child's device and the server have different clocks (NTP drift)? The server is authoritative. Clients sync their balance from the server; offline clients detect clock tampering by comparing against last-known server timestamp.
- What happens when the parent changes the limit mid-day to a value lower than what the child has already watched? The child is immediately over-limit and cannot start new playback until the next reset or a parent grants extra time.
- What happens when the parent sets both weekday and weekend to "Unlimited"? Viewing time enforcement is fully disabled for that child profile; tracking continues for reporting purposes only.
- What happens when the content provider metadata doesn't clearly indicate educational content? Only content explicitly tagged as educational by the provider is exempt. Ambiguous or untagged content counts toward the limit by default.
- What happens when a child is watching a short piece of content (e.g., 5 minutes) and has less time remaining than the content duration? The child can start the content but will hit the warning/lock screen during playback; they are not prevented from starting content that exceeds their remaining balance.
- What happens when the viewing time enforcement service is unavailable (outage)? The system fails closed — playback is blocked for child profiles until enforcement can be verified. The client uses its last-known local balance as a fallback if available; otherwise playback is denied with a message indicating temporary unavailability.
- What happens when the educational content classification lookup fails during playback? The content is treated as regular and counted toward the daily limit. Consistent with the fail-closed principle — parent-configured limits are protected when classification is uncertain.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow parents to set daily viewing time limits on child profiles in 15-minute increments from 15 minutes to 8 hours, or Unlimited
- **FR-002**: System MUST support separate limits for weekdays (Monday–Friday) and weekends (Saturday–Sunday)
- **FR-003**: System MUST allow parents to configure a daily reset time in 1-hour increments (default: 06:00 local time) that determines when the child's daily allowance refreshes
- **FR-004**: System MUST protect all parental control settings with a 4-digit account PIN, with lockout after 5 failed attempts for 30 minutes
- **FR-005**: System MUST track viewing time per child profile in real time, shared across all devices, with the server as the authoritative source of truth
- **FR-006**: System MUST stop the viewing time clock when a child pauses for more than 5 minutes with no interaction
- **FR-007**: System MUST limit child profiles to one concurrent active stream to prevent circumvention of time limits
- **FR-008**: System MUST display the remaining viewing time to the child in the profile menu, with color changes at 30-minute (amber) and 15-minute (red) thresholds
- **FR-009**: System MUST show non-intrusive playback warnings at 15 minutes and 5 minutes before the limit is reached
- **FR-010**: System MUST display a kid-friendly lock screen with cheerful messaging, suggested offline activities, and a parent override button when the limit is reached
- **FR-011**: System MUST allow a parent to grant extra time (+15 min, +30 min, +1 hour, Unlimited for today) via PIN entry on the child's lock screen
- **FR-012**: System MUST allow a parent to grant extra time remotely from their own device without PIN re-entry, with the child's device updating within 10 seconds when on the lock screen or 60 seconds during normal playback (production target: 5 seconds via push)
- **FR-013**: System MUST exempt content tagged as "educational" by the content provider from counting toward the daily limit, with a per-profile toggle to disable this exemption. If the educational classification cannot be determined (lookup failure), the content MUST be treated as regular and counted toward the limit
- **FR-014**: System MUST display an "Educational" badge on exempt content in browse, search, and detail screens
- **FR-015**: ~~DEFERRED — Post-PoC~~ System MUST enforce viewing time limits on offline/downloaded content via secure on-device tracking, with server reconciliation when connectivity returns. *PoC is web-only with no download capability; see research.md R6. Fail-closed enforcement (FR-024) covers the online case.*
- **FR-016**: ~~DEFERRED — Post-PoC~~ System MUST detect device clock tampering and fall back to the most restrictive interpretation of the viewing balance. *Requires platform-specific secure storage not available in web PoC; see research.md R6.*
- **FR-017**: System MUST provide a detailed viewing history per child profile showing title, date/time, duration, and device for each session, grouped by day with totals, for at least 30 days
- **FR-018**: System MUST generate a weekly summary report per account (covering all child profiles), available on-demand in Parental Controls. *PoC: computed on-the-fly when parent views the report screen (see research.md R8). Production: delivered as in-app notification with optional push at the weekly boundary.*
- **FR-019**: System MUST apply sensible default limits (2h weekday, 3h weekend, 06:00 reset, educational exemption enabled) to newly created child profiles
- **FR-020**: System MUST present viewing time settings within the existing Parental Controls section alongside content rating restrictions
- **FR-021**: System MUST ensure the adult/main profile always has unlimited viewing time that cannot be restricted
- **FR-022**: System MUST log all extra time grants as auditable events (timestamp, child profile, amount, granting account)
- **FR-023**: System MUST comply with GDPR and COPPA for children's viewing time data — purpose-limited to enforcement and parental reporting only, with deletion within 30 days upon request
- **FR-024**: System MUST fail-closed for child profiles — if the viewing time enforcement service is unavailable or the enforcement status cannot be verified, playback MUST be blocked until enforcement is restored or the device can verify the balance locally
- **FR-025**: System MUST allow a parent who has forgotten their PIN to reset it by verifying their full account password, with the new PIN taking effect immediately

### Key Entities

- **Viewing Time Configuration**: Per child profile settings including weekday limit (minutes), weekend limit (minutes), daily reset time (hour), educational exemption toggle, and unlimited flag. Belongs to a child profile within an account.
- **Viewing Time Balance**: The real-time state of a child's daily allowance including minutes used, minutes remaining, current limit, whether unlimited override is active, and next reset timestamp. Resets daily at the configured reset time.
- **Viewing Session Record**: An individual viewing event including child profile, content title, start time, end time, duration, device identifier, and whether the content was educational. Used for history and reporting.
- **Extra Time Grant**: An auditable record of a parent granting additional time including timestamp, child profile, minutes granted (or unlimited flag), and the parent account that authorized it.
- **Account PIN**: A single shared secure credential scoped to the account (not per-profile, not per-caregiver) used to protect parental control settings and on-device time overrides. All caregivers in the household share the same PIN. Subject to rate limiting (5 attempts per 30-minute window per device). Can be reset by verifying the full account password.
- **Weekly Report**: An aggregated summary per account covering all child profiles, including daily totals, averages, limit comparison, most-watched content, and educational breakdown for the preceding week.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Parents can configure viewing time limits for a child profile in under 2 minutes, including first-time PIN setup
- **SC-002**: Viewing time balance is accurate across devices within ±1 minute after a device switch
- **SC-003**: 95% of parents with child profiles activate viewing time limits within the first 30 days (aided by default configuration and banner prompt)
- **SC-004**: Time limit enforcement blocks playback within 30 seconds of the balance reaching zero
- **SC-005**: Parent override (PIN entry to extra time granted) completes in under 15 seconds on the child's device
- **SC-006**: Remote extra time grant from a parent's device propagates to the child's device within 10 seconds when lock screen is active (PoC polling; production target: 5 seconds via push)
- **SC-007**: Viewing time data for deleted child profiles is fully purged within 30 days of the deletion request
- **SC-008**: Weekly reports are available on-demand with results computed in under 2 seconds (PoC). Production target: delivered within 1 hour of the weekly boundary for 99% of eligible accounts.
- **SC-009**: The viewing time feature supports 500 concurrent tracked child sessions without degradation in the PoC (production target: 500,000)
- **SC-010**: ~~DEFERRED — Post-PoC~~ Offline enforcement prevents 100% of playback attempts that exceed the configured limit when the device is disconnected. *PoC has no offline/download capability.*
- **SC-011**: Fewer than 5% of parents contact support about viewing time limits within the first 90 days (indicating self-service clarity)
- **SC-012**: Child profiles spend at least 15% of their viewing time on educational content when exemptions are enabled (measuring the incentive effect)

## Clarifications

### Session 2026-02-13

- Q: When the viewing time enforcement service is unavailable, should the system fail-open (allow viewing) or fail-closed (block playback)? → A: Fail-closed — block playback when enforcement status cannot be verified.
- Q: How does a parent recover a forgotten PIN? → A: Account password verification — parent enters their full account password to reset the PIN immediately, no external dependency.
- Q: Can multiple caregivers manage viewing time, or is it single-account only? → A: Single shared PIN per account. All caregivers in the household share the same PIN. Matches industry standard (Netflix, Disney+).
- Q: When the educational content tag lookup fails, should content be treated as educational (exempt) or regular (counted)? → A: Treat as regular (counted toward the limit). Consistent with fail-closed philosophy — protects parent intent when classification is uncertain.

## Assumptions

- The platform already has a profile system with a child/kids profile flag that distinguishes child profiles from adult profiles.
- The existing Parental Controls UI from PRD-001 (parental rating enforcement) provides a foundation to extend with viewing time settings.
- Content providers supply reliable "educational" metadata tags; the platform does not need to independently classify content as educational for Phase 1.
- The platform supports downloaded/offline content playback on mobile devices, with secure local storage capabilities available on all target platforms.
- Push notifications infrastructure exists and can deliver real-time events to specific devices within a profile.
- Weekend is defined as Saturday–Sunday by default; locale-specific weekend definitions (e.g., Friday–Saturday) will be handled via market configuration.
- The account PIN system is either already in place (from existing parental controls) or will be implemented as part of this feature.
- Multi-caregiver PIN support (per-person PINs, delegated access) is out of scope for this feature. A single shared PIN per account is sufficient for Phase 1.

## Dependencies

- **Existing Parental Controls (PRD-001)**: The viewing time settings UI extends the existing parental controls screen and PIN system.
- **Profile Service**: Provides child profile flag, profile timezone, and profile management hooks for default configuration.
- **Playback Session Service**: Viewing time enforcement is an additional gate in the playback session creation flow.
- **Catalog/Metadata Service**: Provides educational content classification from content provider metadata.
- **Notification Service**: Delivers weekly reports and real-time events for remote extra time grants.
- **Analytics Pipeline**: Powers the viewing history and weekly report aggregation.
- **Multi-Client Platform (PRD-006)**: Offline enforcement and secure local storage must be implemented per client platform.
