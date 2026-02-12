# Feature Specification: Continue Watching & Cross-Device Bookmarks

**Feature Branch**: `004-continue-watching-bookmarks`
**Created**: 2026-02-12
**Status**: Draft
**Input**: User description: "Continue Watching & Cross-Device Bookmarks, User stories US-VOD-017, US-MC-013, US-MC-014."

## Clarifications

### Session 2026-02-12

- Q: Can viewers manually dismiss items from Continue Watching before the 30-day auto-archival? → A: Yes — manual dismiss moves the item to the Paused section with bookmark preserved (recoverable).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cross-Device Bookmark Sync (Priority: P1)

A viewer is watching a movie on their TV. Halfway through, they pause and go to bed. The next morning on their commute, they open the app on their phone. In the "Continue Watching" rail on the home screen, the movie appears with an accurate progress bar showing exactly where they left off. They tap the title and playback resumes from that precise position — no searching, no scrubbing, no guesswork.

**Why this priority**: Without accurate bookmark persistence and cross-device sync, "Continue Watching" has no foundation. Every other feature in this spec (AI sorting, stale archival, context-aware ordering) depends on reliable bookmark data being available across all devices. This is the bedrock capability.

**Independent Test**: Start playing any content on one device, pause at a known position (e.g., 35:12), then open the app on a different device and verify the "Continue Watching" rail shows the title at position 35:12 (within 5-second tolerance). Tap to resume and confirm playback starts at that position.

**Acceptance Scenarios**:

1. **Given** a viewer pauses a movie at 35:12 on their TV, **When** they open the app on their phone within 30 seconds, **Then** the "Continue Watching" rail shows the movie with a progress bar reflecting position 35:12 (within 5-second accuracy)
2. **Given** a viewer taps a title in "Continue Watching" on a second device, **When** playback starts, **Then** it resumes from the last synced bookmark position (not from the beginning)
3. **Given** the player is actively playing, **When** playback progresses, **Then** the bookmark is updated server-side periodically (at least every 30 seconds) so that an unexpected app close still preserves a recent position
4. **Given** two devices send bookmark updates for the same content within a short window, **When** a conflict occurs, **Then** the system resolves using latest-timestamp-wins and the most recent position is reflected on all devices
5. **Given** a viewer completes a movie (watches to the end or within the final 2 minutes), **When** the bookmark is saved, **Then** the content is marked as "completed" and removed from the active "Continue Watching" rail
6. **Given** a viewer completes an episode of a series, **When** the bookmark is saved, **Then** the "Continue Watching" entry advances to the next unwatched episode in the series (if available)

---

### User Story 2 - Continue Watching Rail Display (Priority: P1)

A viewer opens the app and immediately sees the "Continue Watching" rail prominently on the home screen. It shows all their in-progress content — movies, series, catch-up programs — with visual progress bars indicating how far through each title they are. The rail is limited to a manageable number of items so it doesn't become cluttered.

**Why this priority**: The rail is the primary surface where bookmarks become visible and actionable to the user. Without it, bookmarks exist but provide no user value. This is tied with Story 1 because sync without display is invisible to the user.

**Independent Test**: Log in as a profile that has multiple in-progress titles across different content types (movies, series episodes, catch-up). Verify the "Continue Watching" rail appears on the home screen showing each title with an accurate progress indicator. Verify tapping any item resumes playback from the bookmarked position.

**Acceptance Scenarios**:

1. **Given** a viewer has 3 in-progress titles, **When** they open the home screen, **Then** the "Continue Watching" rail appears showing all 3 titles with progress bars reflecting their bookmark positions
2. **Given** a viewer has in-progress content from VOD, catch-up TV, and a Cloud PVR recording, **When** the Continue Watching rail loads, **Then** all content types are aggregated into a single unified rail
3. **Given** a series where the viewer completed episode 3 and hasn't started episode 4, **When** displayed in Continue Watching, **Then** the series card shows episode 4 as "Up Next" with a fresh progress bar at 0%
4. **Given** a viewer has no in-progress content, **When** the home screen loads, **Then** the "Continue Watching" rail is hidden (not shown empty)
5. **Given** the rail display, **When** rendered, **Then** a maximum of 20 items are shown to prevent clutter

---

### User Story 3 - AI-Sorted Continue Watching by Resumption Likelihood (Priority: P2)

A viewer who juggles several shows and movies opens the app. Instead of seeing their in-progress content sorted by "most recently watched" (which might surface a show they've lost interest in), the Continue Watching rail is sorted by AI-predicted likelihood of resumption. The show they watch every Tuesday evening is at the front on Tuesday night. The movie they paused 3 weeks ago and haven't returned to is further back.

**Why this priority**: AI sorting is the key differentiator over a basic recency-sorted list. However, it depends on Stories 1 and 2 being functional first. The system needs bookmark data and a working rail before AI can meaningfully sort it.

**Independent Test**: Create a profile with 5+ in-progress titles with varied viewing patterns (daily series, weekend movie, abandoned title). Open the app at different times of day and on different devices. Verify the rail ordering changes based on context and is not purely recency-based. Verify the AI-predicted top item matches the user's actual next play in at least 60% of test sessions.

**Acceptance Scenarios**:

1. **Given** a viewer has 5 in-progress titles with varied viewing histories, **When** the Continue Watching rail loads, **Then** items are sorted by AI-predicted resumption likelihood, not by recency alone
2. **Given** a series the viewer watches every weekday evening, **When** the viewer opens the app on a weekday evening, **Then** that series appears in the top 2 positions of the rail
3. **Given** the AI prediction model, **When** measured across sessions, **Then** the top-ranked item is the actual next-played content in 60% or more of sessions
4. **Given** the AI recommendation service is unavailable, **When** the Continue Watching rail loads, **Then** it falls back to recency-based ordering (most recently watched first) with no visible error to the user

---

### User Story 4 - Context-Aware Ordering by Device and Time (Priority: P2)

A viewer checks the app on their phone during their morning commute. The Continue Watching rail shows a 22-minute sitcom episode near the top — short content that fits the commute. That evening on their TV at home, the same rail now leads with the 2-hour movie they started last weekend. The system adapts the ordering based on the device type and time of day without the viewer configuring anything.

**Why this priority**: This builds on the AI sorting from Story 3 by adding contextual signals. It enhances the intelligence of the rail but is not essential for basic AI-sorted functionality.

**Independent Test**: Set up a profile with both short-form (< 30 min remaining) and long-form (> 60 min remaining) in-progress content. Open the app on a mobile device in the morning and verify short content is prioritized. Open on a TV device in the evening and verify long content is prioritized.

**Acceptance Scenarios**:

1. **Given** a viewer has both short-form (< 30 min remaining) and long-form (> 60 min remaining) in-progress content, **When** they open the app on a mobile device during morning hours (6 AM–10 AM), **Then** short-form content is prioritized higher in the rail
2. **Given** the same viewer opens the app on a TV device during evening hours (7 PM–11 PM), **Then** long-form content (movies, series) is prioritized higher in the rail
3. **Given** context signals (device type, time of day), **When** sent with the Continue Watching request, **Then** the ordering reflects these signals as factors in the AI model's ranking

---

### User Story 5 - Stale Content Auto-Archival (Priority: P3)

A viewer started a documentary 6 weeks ago and never returned. Instead of this stale title cluttering the Continue Watching rail forever, it is automatically moved to a "Paused" section after 30 days of inactivity. The viewer can access "Paused" content with one tap from the Continue Watching rail if they want to resume it later.

**Why this priority**: This is a housekeeping feature that improves rail quality over time. It depends on all prior stories and adds polish rather than core functionality.

**Independent Test**: Ensure a profile has a bookmark older than 30 days with no playback activity on that title. Open the home screen and verify the stale title does not appear in the active Continue Watching rail. Verify a "Paused" section or link is accessible and contains the archived title. Tap the title in "Paused" and verify playback resumes from the bookmarked position.

**Acceptance Scenarios**:

1. **Given** a title has not been played for 30+ days, **When** the Continue Watching rail loads, **Then** the title is excluded from the active rail and moved to a "Paused" section
2. **Given** stale titles exist, **When** the viewer accesses the "Paused" section (one tap from Continue Watching), **Then** archived titles are displayed with their preserved bookmark positions
3. **Given** a viewer resumes a title from the "Paused" section, **When** they play it, **Then** it returns to the active Continue Watching rail and playback starts from the preserved bookmark position

---

### Edge Cases

- What happens when a viewer watches the same content simultaneously on two devices? The system should allow it (up to concurrent stream limits) and use latest-timestamp-wins to resolve the final bookmark when both sessions end.
- What happens when a title is removed from the catalog while the viewer has an in-progress bookmark? The title should be removed from the Continue Watching rail with no error; if the viewer had a deep-link, they see a "Content no longer available" message.
- What happens when a profile's bookmark storage exceeds the 20-item display limit? Older, lower-ranked items are suppressed from the rail but their bookmarks are preserved. They appear if higher-ranked items are completed or archived.
- What happens if the bookmark service is temporarily unavailable during playback? The player should cache bookmark updates locally and sync them when connectivity is restored, preventing data loss.
- What happens when a series episode is removed but later episodes exist? The Continue Watching entry advances to the next available episode in the series.
- What happens when a viewer wants to remove an item they have no intention of finishing? The viewer can manually dismiss the item, which moves it to the "Paused" section with the bookmark preserved for potential future resumption.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST persist bookmark position (content ID, position in seconds, total duration, completion status) for every piece of content a viewer plays
- **FR-002**: System MUST sync bookmarks across all devices associated with a viewer's profile within 10 seconds of a bookmark update
- **FR-003**: Player MUST send periodic bookmark heartbeats (at minimum every 30 seconds) during active playback
- **FR-004**: System MUST resolve conflicting bookmark updates from multiple devices using latest-timestamp-wins strategy
- **FR-005**: System MUST mark content as "completed" when the viewer reaches the final 2 minutes (or 95% of duration, whichever is less) and remove it from the active Continue Watching rail
- **FR-006**: System MUST advance series entries in Continue Watching to the next unwatched episode when the current episode is completed
- **FR-007**: System MUST display a "Continue Watching" rail on the home screen aggregating in-progress content from all sources (VOD, catch-up TV, Cloud PVR recordings)
- **FR-008**: System MUST limit the Continue Watching rail to a maximum of 20 visible items
- **FR-009**: System MUST hide the Continue Watching rail entirely when a profile has no in-progress content
- **FR-010**: System MUST display a visual progress bar on each Continue Watching item reflecting the bookmark position relative to total duration
- **FR-011**: System MUST sort the Continue Watching rail using AI-predicted resumption likelihood when the recommendation service is available
- **FR-012**: System MUST fall back to recency-based ordering (most recently watched first) when the AI recommendation service is unavailable
- **FR-013**: System MUST incorporate device type and time-of-day as contextual signals in the AI sorting model
- **FR-014**: System MUST automatically archive titles to a "Paused" section after 30 days of inactivity on that title
- **FR-015**: System MUST provide one-tap access from the Continue Watching rail to the "Paused" section
- **FR-016**: System MUST allow viewers to resume archived "Paused" titles, returning them to the active Continue Watching rail
- **FR-017**: System MUST cache bookmark updates locally on the client when the server is unreachable and sync when connectivity is restored
- **FR-018**: System MUST remove titles from Continue Watching when the content is no longer available in the catalog
- **FR-019**: System MUST allow viewers to manually dismiss individual items from the Continue Watching rail, moving them to the "Paused" section with bookmark preserved

### Key Entities

- **Bookmark**: Represents a viewer's progress on a specific piece of content — includes profile reference, content reference, content type (movie/episode/catch-up/recording), position in seconds, total duration, completion status, and timestamp of last update
- **Continue Watching Rail**: An ordered list of in-progress content for a profile, aggregated across content sources, sorted by AI prediction or recency fallback, limited to 20 active items
- **Paused Archive**: A secondary collection of bookmarked titles that have been inactive for 30+ days, accessible from the Continue Watching rail, preserving bookmark positions for future resumption
- **Playback Heartbeat**: A periodic signal sent by the player during active playback containing the current position, used to update the server-side bookmark

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Bookmark position syncs across devices within 10 seconds with accuracy of +/- 5 seconds from the actual pause point
- **SC-002**: The top-ranked item in the AI-sorted Continue Watching rail is the viewer's actual next-played content in 60% or more of sessions
- **SC-003**: 90% of viewers with in-progress content interact with the Continue Watching rail at least once per session (indicating it surfaces relevant content)
- **SC-004**: Continue Watching rail loads and displays within 2 seconds on all supported platforms
- **SC-005**: Zero bookmark data loss during temporary connectivity interruptions (client-side caching ensures all positions are eventually synced)
- **SC-006**: Stale content archival reduces average active Continue Watching rail size by 30% for users with 10+ in-progress titles, improving scannability

## Assumptions

- The existing Bookmark model in the backend already captures the core fields (profile_id, content_id, content_type, position_seconds, duration_seconds, completed, updated_at) and can be extended as needed
- The recommendation service (already partially built for semantic search) can be extended to support resumption-likelihood scoring
- Concurrent stream limits are enforced separately (cross-cutting concern) and are not part of this feature's scope
- Content availability checks are handled by the catalog service — this feature reacts to catalog removal events but does not manage content availability
- The "Paused" section is a UI concept backed by the same bookmark data, filtered by an inactivity threshold — no separate data store is needed
- Parental rating enforcement (already implemented in feature 001) continues to apply to the Continue Watching rail — only age-appropriate content appears
