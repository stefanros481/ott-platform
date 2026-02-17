# Feature Specification: Recommendations Quality, Watchlist Rail & Live TV Playback

**Feature Branch**: `011-recs-watchlist-livetv`
**Created**: 2026-02-17
**Status**: Draft
**Input**: Feature 010 from Backend Enhancement Roadmap — fixes highest-ROI recommendation bugs, surfaces the watchlist, improves content discovery performance, and unblocks live TV playback from the EPG.

## Clarifications

### Session 2026-02-17

- Q: When a viewer clicks a currently-airing program in the EPG, where does playback begin? → A: Navigate to the existing player page (same as VOD). Reuse the existing player with Start Over button. Pass EPG program data so the player shows current program info and Start Over seeks to the program's scheduled start time.
- Q: What powers the cold-start fallback rail for new profiles with no viewing history? → A: "Popular Now" — recently popular content (reuse trending signal), not "Top Rated" based on ratings.
- Q: Where does the "My List" rail appear relative to other home screen rails? → A: After Continue Watching, before For You (standard Netflix/Disney+ convention).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Accurate Personalized Recommendations (Priority: P1)

A returning viewer opens the home screen and sees a "For You" rail of titles matched to their taste. Titles they have explicitly disliked (thumbs down) never appear in this rail. Titles they have explicitly liked (thumbs up) carry stronger influence on what is recommended than titles they merely started watching. The result is a "For You" rail that visibly improves the more the viewer uses ratings.

**Why this priority**: The "For You" rail is the primary discovery surface. Including disliked content and treating all signals equally undermines user trust and reduces engagement. This is the single highest-impact quality fix.

**Independent Test**: Create a profile that has bookmarked 10 titles across 3 genres, thumbs-up rated 3 titles in Genre A, and thumbs-down rated 2 titles in Genre B. Verify the "For You" rail contains zero Genre B titles that were thumbs-downed, and that Genre A titles dominate the top positions.

**Acceptance Scenarios**:

1. **Given** a profile has thumbs-down rated Title X, **When** the home screen loads, **Then** Title X does not appear in the "For You" rail
2. **Given** a profile has thumbs-down rated 3 titles in Genre B and thumbs-up rated 3 titles in Genre A, **When** the "For You" rail is generated, **Then** Genre A titles appear with higher similarity scores than Genre B titles
3. **Given** a profile has thumbs-up rated Title Y, **When** the "For You" rail is generated, **Then** Title Y's characteristics have stronger influence on recommendations than a merely bookmarked title
4. **Given** a profile has only bookmarks and no ratings, **When** the "For You" rail is generated, **Then** recommendations still appear based on bookmark signals (backward compatible)

---

### User Story 2 - My List Rail on Home Screen (Priority: P1)

A viewer who has added titles to their watchlist sees a "My List" rail on the home screen, positioned after "Continue Watching" and before "For You", showing their saved titles most recently added first. This gives viewers quick access to content they intend to watch without needing to navigate to a separate watchlist page.

**Why this priority**: Watchlist data is already being collected but never surfaced on the home screen. This is a zero-risk, high-value addition that immediately rewards users for engaging with the watchlist feature.

**Independent Test**: Add 5 titles to a profile's watchlist. Load the home screen and verify a "My List" rail appears with those 5 titles in reverse chronological order (newest first).

**Acceptance Scenarios**:

1. **Given** a profile has 3 titles on their watchlist, **When** the home screen loads, **Then** a "My List" rail appears after "Continue Watching" and before "For You", containing those 3 titles sorted by most recently added first
2. **Given** a profile has no titles on their watchlist, **When** the home screen loads, **Then** no "My List" rail appears (the rail is omitted entirely, not shown empty)
3. **Given** a profile adds a new title to their watchlist, **When** they return to the home screen, **Then** the newly added title appears first in the "My List" rail
4. **Given** parental controls are active for a child profile, **When** the home screen loads, **Then** the "My List" rail only shows titles within the allowed age ratings

---

### User Story 3 - Post-Play Next Episode (Priority: P1)

A viewer finishes watching Episode 3 of a series. Instead of seeing random similar titles, the post-play suggestions show Episode 4 of the same series as the first recommendation, followed by similar content. If the viewer has finished the final episode of a season, the first episode of the next season is suggested. This keeps binge-watchers engaged in their current series.

**Why this priority**: Episode-to-episode continuity is a fundamental expectation of any streaming platform. Showing unrelated titles after an episode ends breaks the binge-watching flow and increases drop-off.

**Independent Test**: Bookmark Episode 3 of a series as completed. Request post-play suggestions for Episode 3 and verify Episode 4 appears as the first result.

**Acceptance Scenarios**:

1. **Given** a viewer finishes Episode 3 of Season 1 (and Episode 4 exists), **When** post-play suggestions load, **Then** Episode 4 of Season 1 appears as the first suggestion
2. **Given** a viewer finishes the last episode of Season 1 (and Season 2 exists), **When** post-play suggestions load, **Then** Season 2 Episode 1 appears as the first suggestion
3. **Given** a viewer finishes the last episode of the final season, **When** post-play suggestions load, **Then** similar titles are shown (no next episode available)
4. **Given** a viewer finishes a standalone movie, **When** post-play suggestions load, **Then** similar titles are shown (current behavior, unchanged)
5. **Given** a child profile with parental controls finishes an episode, **When** post-play suggestions load, **Then** the next episode only appears if it is within the allowed age ratings

---

### User Story 4 - New Profile Welcome Experience (Priority: P2)

A new viewer creates a profile and opens the home screen for the first time. Instead of seeing an empty "For You" rail (or no "For You" rail at all), they see a "Popular Now" rail featuring recently popular content on the platform — titles that other viewers have been watching in the last 7 days. This gives new users an engaging starting point until they build up enough viewing history for personalized recommendations.

**Why this priority**: First impressions matter. An empty or missing recommendation rail for new profiles signals a broken product. A curated fallback ensures every profile has a compelling home screen from day one.

**Independent Test**: Create a new profile with zero viewing history, zero bookmarks, and zero ratings. Load the home screen and verify a "Popular Now" rail appears with recently popular content.

**Acceptance Scenarios**:

1. **Given** a brand-new profile with no viewing history, **When** the home screen loads, **Then** a "Popular Now" rail appears in place of the "For You" rail, containing the recently popular titles
2. **Given** a new profile with parental controls, **When** the home screen loads, **Then** the "Popular Now" rail only includes titles within the allowed age ratings
3. **Given** a profile that subsequently bookmarks their first title, **When** the home screen loads next time, **Then** the "For You" rail replaces the "Popular Now" rail (personalization kicks in)
4. **Given** the platform has no recent viewing activity at all, **When** a new profile's home screen loads, **Then** the fallback rail is omitted gracefully (no error, no empty rail)

---

### User Story 5 - Live TV Playback from EPG (Priority: P2)

A viewer browsing the electronic program guide (EPG) clicks on a currently-airing program and is taken to the existing player page — the same player used for VOD. The player shows the live channel stream along with the current EPG program's information (title, time slot). The player's existing Start Over button lets the viewer jump back to the program's scheduled start time. Today, clicking a program in the EPG does nothing. This fix unblocks the entire live TV experience — channels already have playback URLs configured, but the user interface does not use them.

**Why this priority**: Live TV is a core platform capability. The EPG exists, channel data exists, and playback URLs are populated — but users cannot actually watch live TV because the click action is not wired. This is the single most visible gap in the platform.

**Independent Test**: Navigate to the EPG, click on a currently-airing program, and verify the existing player page opens with the live stream and current program info displayed.

**Acceptance Scenarios**:

1. **Given** a viewer is browsing the EPG grid, **When** they click on a currently-airing program, **Then** the existing player page opens with the live stream for that channel playing
2. **Given** a viewer is watching a live channel, **When** they look at the player UI, **Then** the current EPG program's title and time slot are displayed
3. **Given** a viewer is watching a live channel mid-program, **When** they press the Start Over button, **Then** playback seeks to the program's scheduled start time from the EPG
4. **Given** a live program ends and the next program begins, **When** the viewer continues watching, **Then** the displayed program information updates to reflect the new program
5. **Given** a viewer clicks on a future program in the EPG, **When** the click occurs, **Then** the system shows program details (not playback, since the program hasn't started)
6. **Given** a viewer clicks on a past program in the EPG, **When** the click occurs, **Then** the system shows program details (playback may be available via catch-up in a future feature)
7. **Given** a channel's playback URL is unavailable or broken, **When** the viewer clicks to play, **Then** a clear error message is shown ("Channel temporarily unavailable")
8. **Given** a child profile with parental controls, **When** they click on a channel rated above their allowed rating, **Then** playback is blocked with an appropriate message

---

### User Story 6 - Trending Content Reflects Recent Popularity (Priority: P2)

A viewer browsing the home screen sees a "Trending" rail that reflects what is popular right now, not what has been popular since the platform launched. Content that was heavily watched in the last 7 days ranks higher than content that accumulated views months ago. This makes the trending rail feel fresh and timely.

**Why this priority**: A stale trending rail that never changes (because all-time counts dominate) reduces trust in the platform's intelligence. Time-decayed trending creates a dynamic, "living" home screen.

**Independent Test**: Simulate 50 bookmarks on Title A in the last 2 days and 100 bookmarks on Title B spread over the last 90 days. Verify Title A ranks higher than Title B in the trending rail.

**Acceptance Scenarios**:

1. **Given** Title A received 50 views in the last 7 days and Title B received 100 views over 90 days, **When** the trending rail loads, **Then** Title A ranks higher than Title B
2. **Given** no bookmarks exist in the last 7 days, **When** the trending rail loads, **Then** all-time popular titles are shown as a fallback (the rail is never empty)
3. **Given** parental controls are active, **When** the trending rail loads, **Then** only titles within the allowed age ratings appear

---

### User Story 7 - Personalized Featured Content (Priority: P3)

A viewer sees the featured/hero content area on the home screen showing titles that are both editorially featured AND relevant to their personal taste. Instead of every user seeing the same featured titles in the same order, the platform ranks featured titles by how well they match each viewer's preferences. This increases the likelihood that the hero banner catches the viewer's attention.

**Why this priority**: Featured titles are high-value editorial placements. Personalizing their order per viewer maximizes the conversion rate of the most prominent real estate on the home screen without changing what is featured — only the ranking.

**Independent Test**: Mark 5 titles as featured. Create a profile with strong affinity for Action genre. Verify the featured titles list returns Action titles ranked higher than Romance titles for that profile.

**Acceptance Scenarios**:

1. **Given** 5 titles are marked as featured and a profile has strong Action genre affinity, **When** featured titles are requested, **Then** Action-genre featured titles appear before other genres
2. **Given** a new profile with no viewing history, **When** featured titles are requested, **Then** all featured titles are returned in their default order (no personalization applied)
3. **Given** parental controls are active, **When** featured titles are requested, **Then** only featured titles within the allowed age ratings appear

---

### User Story 8 - Faster Content Discovery (Priority: P3)

A viewer searching for content or browsing recommendations receives results noticeably faster. Content similarity searches that power "For You", "More Like This", and semantic search all return results more quickly. Additionally, search results include genre information without the system making redundant per-title lookups.

**Why this priority**: Performance directly impacts engagement. Slow recommendations and search results increase abandonment. These are infrastructure improvements that benefit every user on every interaction.

**Independent Test**: Measure the response time of the "For You" rail and semantic search endpoints before and after the improvement. Verify a measurable reduction in response time.

**Acceptance Scenarios**:

1. **Given** a catalog of 500+ titles with embeddings, **When** a user requests their "For You" rail, **Then** results return within 500 milliseconds (p95)
2. **Given** a user performs a semantic search, **When** results are returned, **Then** each result includes genre names without additional per-title lookups
3. **Given** a catalog of 500+ titles, **When** a semantic search is performed, **Then** results return within 500 milliseconds (p95)

---

### Edge Cases

- What happens when a profile has only thumbs-down ratings and no thumbs-up or bookmarks? The "For You" rail should not appear (no positive signals to build recommendations from).
- What happens when a viewer's entire watchlist consists of titles that have been removed from the catalog? The "My List" rail should gracefully skip deleted titles and show remaining valid ones, or be omitted if all are gone.
- What happens when a series has episodes that are out of order or missing (e.g., Season 1 has Episodes 1, 2, 5)? Post-play should use the next available episode by episode number, skipping gaps.
- What happens when all featured titles are outside a child profile's allowed ratings? The featured rail should be omitted for that profile rather than showing an empty section.
- What happens when the EPG contains channels with no playback URL configured? The UI should indicate the channel is not available for live viewing and not offer a play action.
- What happens when a viewer rapidly switches between EPG channels? The system should cancel the previous playback request before initiating a new one (no stacking of player instances).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST exclude titles with a negative rating from the "For You" recommendation computation — negatively rated titles must not influence the recommendation profile in any way
- **FR-002**: System MUST weight positively rated titles at 2x compared to merely bookmarked titles when computing the recommendation profile
- **FR-003**: System MUST include a "My List" rail on the home screen, positioned after "Continue Watching" and before "For You", containing the active profile's watchlist titles sorted by most recently added first
- **FR-004**: System MUST return the next sequential episode as the first post-play suggestion when the completed content is a series episode and a next episode exists
- **FR-005**: System MUST display a "Popular Now" rail for profiles with no viewing history, bookmarks, or ratings, in place of the "For You" rail — showing recently popular content based on viewing activity in the last 7 days
- **FR-006**: System MUST weight recent viewing activity (last 7 days) more heavily than older activity when calculating the trending rail
- **FR-007**: System MUST rank editorially featured titles by relevance to the active profile's viewing preferences
- **FR-008**: System MUST navigate to the existing player page (same as VOD) when a viewer clicks on a currently-airing program in the EPG, playing the live channel stream
- **FR-009**: The player MUST display the current EPG program's title and time slot while playing a live channel, and update this information when the on-air program changes
- **FR-010**: The player's existing Start Over button MUST seek to the current program's scheduled start time (from the EPG schedule) when pressed during live TV playback
- **FR-011**: System MUST show program details (not playback) when a viewer clicks on a future or past program in the EPG
- **FR-012**: System MUST display a clear error message when live TV playback fails (broken URL, channel unavailable)
- **FR-013**: System MUST load semantic search results without making per-title supplementary lookups (genre information must be retrieved in a single operation alongside the search results)
- **FR-014**: System MUST ensure content discovery queries (recommendations, similar titles, semantic search) perform efficiently on catalogs of 500+ titles with sub-second response times
- **FR-015**: All home screen rails (My List, For You, Popular Now, Trending, Featured) MUST respect the active profile's parental control age rating restrictions
- **FR-016**: The "My List" rail MUST be omitted from the home screen when the profile's watchlist is empty (no empty state shown)
- **FR-017**: The "Popular Now" fallback rail MUST transition to a personalized "For You" rail once the profile accumulates sufficient viewing history (at least one bookmark or rating)

### Key Entities

- **Rating**: A profile's explicit sentiment for a title — thumbs up (+1) or thumbs down (-1). Used to refine recommendation quality. Key attributes: profile, title, rating value, timestamp.
- **Watchlist Item**: A title saved by a profile for future viewing. Key attributes: profile, title, date added. Ordered by recency.
- **Episode**: A single installment within a season of a series. Key attributes: title (parent series), season, episode number, ordering. Used for next-episode logic.
- **Season**: A grouping of episodes within a series. Key attributes: title (parent series), season number, episode count.
- **Bookmark**: A record of viewing progress on a specific piece of content. Used as an implicit interest signal for recommendations and for the "Continue Watching" rail.
- **Content Embedding**: A vector representation of a title's characteristics, used for similarity-based recommendations and semantic search.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Titles that a user has explicitly disliked (thumbs down) never appear in their personalized recommendation rail — 100% exclusion rate
- **SC-002**: The home screen displays a "My List" rail for any profile that has at least one watchlist item, appearing within the standard home screen load time
- **SC-003**: When a viewer finishes a series episode, the next episode appears as the first post-play suggestion in 100% of cases where a next episode exists
- **SC-004**: New profiles with no viewing history see a populated "Popular Now" rail (based on recent viewing activity) on their first home screen visit instead of an empty or missing recommendation section
- **SC-005**: The trending rail shows different results compared to all-time popularity — titles popular in the last 7 days rank higher than titles with more total but older engagement
- **SC-006**: Viewers can start watching a live TV channel by clicking on a currently-airing program in the EPG, which navigates to the existing player page with playback beginning within 3 seconds; the player displays the current program info and Start Over seeks to the program's start time
- **SC-007**: Content discovery queries (home rails, search, post-play) return results within 500 milliseconds at the 95th percentile for a catalog of 500+ titles
- **SC-008**: Search results include complete metadata (including genre information) without the system making per-result supplementary lookups
- **SC-009**: All home screen rails respect parental control restrictions — 0% of titles shown exceed the active profile's allowed age rating
- **SC-010**: Featured titles displayed to a profile with established viewing history are ranked by personal relevance, with the most relevant featured title appearing first

## Assumptions

- The existing `WatchlistItem` model and associated endpoints (add/remove/list) are working correctly. This feature only surfaces the data on the home screen.
- The `Episode` and `Season` models already contain episode number and season number fields sufficient for determining next-episode ordering.
- The `is_featured` flag on titles is already being set by administrators and contains meaningful data.
- The `hls_live_url` field on channels is populated with valid playback URLs for the majority of channels.
- The current 384-dimension embeddings are sufficient for recommendation quality; no re-embedding is needed.
- The existing parental control system (allowed age ratings per profile) is already enforced on other home screen rails and the same mechanism can be extended to new rails.

## Scope Boundaries

**In scope:**
- Service-layer fixes to recommendation quality (rating exclusion, weighting, cold-start)
- New "My List" rail on the home screen
- Next-episode awareness in post-play suggestions
- Time-decayed trending computation
- Personalized ordering of featured titles
- Search performance fix (genre N+1 query elimination)
- Content discovery performance improvement (recommendation and search response times)
- Frontend wiring of EPG click-to-play for live channels

**Out of scope:**
- New database tables (this feature uses only existing models)
- New user-facing endpoints (all changes are to existing endpoints)
- AI metadata enrichment (covered in Feature 013)
- Subscription/entitlement enforcement (covered in Feature 011)
- Redis caching (covered in Feature 012)
- Recommendation explanation strings (deferred to a future feature)
- "Not Interested" suppression (deferred — requires a new table)
