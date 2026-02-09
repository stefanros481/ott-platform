# Feature Specification: Parental Rating Enforcement

**Feature Branch**: `001-parental-rating-enforcement`
**Created**: 2026-02-09
**Status**: Draft
**Input**: User description: "Currently, a Kids profile with parental_rating: TV-Y still sees R-rated and TV-MA content. It's purely cosmetic. Implement parental rating enforcement so that catalog, recommendations, and search results are filtered based on the active profile's parental_rating."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Kids Profile Sees Only Age-Appropriate Content (Priority: P1)

A parent switches to their child's Kids profile (parental rating: TV-Y). Every content surface in the application — browse catalog, home page rails, search results, recommendations — only shows titles rated TV-Y or below. The child cannot discover or access content rated above their profile's parental rating.

**Why this priority**: This is the core safety requirement. Without this, parental profiles are misleading — they suggest protection but provide none. A child on a TV-Y profile should never see TV-MA content anywhere in the app.

**Independent Test**: Switch to a Kids profile (TV-Y), browse the catalog, check all home rails, perform a search, and view a title detail page with "More Like This" — no title with a rating above TV-Y should appear on any surface.

**Acceptance Scenarios**:

1. **Given** a Kids profile with parental_rating TV-Y is active, **When** the user browses the catalog, **Then** only titles rated TV-Y are shown
2. **Given** a Kids profile with parental_rating TV-Y is active, **When** the user views the home page, **Then** all rails (Continue Watching, For You, New Releases, Trending, Top Genre) contain only TV-Y-rated titles
3. **Given** a Kids profile with parental_rating TV-Y is active, **When** the user searches for a title that is rated TV-MA, **Then** the title does not appear in search results
4. **Given** a Kids profile with parental_rating TV-Y is active, **When** the user views "More Like This" on a title detail page, **Then** only titles rated TV-Y or below appear in the suggestions

---

### User Story 2 - Family Profile Sees Content Up to Its Rating Level (Priority: P1)

A user switches to a Family profile with parental_rating TV-PG. They can browse and discover all content rated TV-Y, TV-G, and TV-PG, but not TV-14 or TV-MA content. The filtering applies consistently across all content surfaces.

**Why this priority**: Equally important as the Kids scenario — the system must enforce a clear rating hierarchy, not just an exact-match filter. A TV-PG profile should see TV-Y and TV-G content too.

**Independent Test**: Switch to a Family profile (TV-PG), browse the catalog, and confirm titles rated TV-14 and TV-MA are excluded while TV-Y, TV-G, and TV-PG titles are visible.

**Acceptance Scenarios**:

1. **Given** a profile with parental_rating TV-PG is active, **When** the user browses the catalog, **Then** only titles rated TV-Y, TV-G, or TV-PG are shown
2. **Given** a profile with parental_rating TV-14 is active, **When** the user browses the catalog, **Then** titles rated TV-Y, TV-G, TV-PG, and TV-14 are shown, but TV-MA is excluded

---

### User Story 3 - Unrestricted Profile Sees All Content (Priority: P1)

An adult profile with parental_rating TV-MA (the default) sees all content without any filtering. The filtering system must not degrade the experience for unrestricted users.

**Why this priority**: Must verify that the enforcement does not accidentally restrict adult profiles or introduce performance issues for the default case.

**Independent Test**: Switch to an adult profile (TV-MA), browse the catalog, and confirm all titles are visible and all content surfaces work as before.

**Acceptance Scenarios**:

1. **Given** a profile with parental_rating TV-MA is active, **When** the user browses the catalog, **Then** all titles are shown regardless of age rating
2. **Given** a profile with parental_rating TV-MA is active, **When** the home page loads, **Then** all rails are populated as before with no filtering applied

---

### User Story 4 - Title Detail Page Blocked for Restricted Content (Priority: P2)

When a restricted profile attempts to view the detail page of a title above their rating (e.g., via a direct URL or shared link), the system prevents access and displays a clear message.

**Why this priority**: Important for safety but secondary to surface-level filtering. If catalog/search filtering works correctly, users rarely encounter this, but it's needed as a fallback guard.

**Independent Test**: On a TV-Y profile, navigate directly to the URL of a TV-MA title's detail page and verify the system blocks access or shows an appropriate restriction message.

**Acceptance Scenarios**:

1. **Given** a Kids profile with parental_rating TV-Y, **When** the user navigates directly to the detail page of a TV-MA title, **Then** the system blocks access and shows a "Content not available for this profile" message
2. **Given** a Kids profile with parental_rating TV-Y, **When** the user navigates to the detail page of a TV-Y title, **Then** the detail page loads normally

---

### Edge Cases

- What happens when a title has no age_rating set (NULL)? Titles with no rating are treated as unrestricted (TV-MA equivalent) — hidden from restricted profiles, visible to TV-MA profiles.
- What happens when a profile switches from Kids to Adult mid-session? Content surfaces refresh with the new profile's rating on the next page load or navigation.
- What happens when the "Continue Watching" rail has a bookmark on a title above the current profile's rating? The bookmarked title is excluded from the Continue Watching rail for that profile.
- What happens to the featured/hero banner? Featured titles are also filtered by the active profile's parental rating.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST enforce a rating hierarchy where TV-Y < TV-G < TV-PG < TV-14 < TV-MA, and a profile can only see content at or below its own parental_rating level
- **FR-002**: System MUST filter the catalog browse endpoint results based on the active profile's parental_rating
- **FR-003**: System MUST filter search results based on the active profile's parental_rating
- **FR-004**: System MUST filter all home page recommendation rails (Continue Watching, For You, New Releases, Trending, Top Genre) based on the active profile's parental_rating
- **FR-005**: System MUST filter "More Like This" / similar title recommendations based on the active profile's parental_rating
- **FR-006**: System MUST filter the featured titles (hero banner) based on the active profile's parental_rating
- **FR-007**: System MUST block access to individual title detail pages when the title's age_rating exceeds the active profile's parental_rating
- **FR-008**: System MUST treat titles with a NULL age_rating as unrestricted (equivalent to TV-MA) — only visible to profiles with TV-MA parental_rating
- **FR-009**: System MUST NOT apply any content filtering for profiles with parental_rating TV-MA (the default/highest level)
- **FR-010**: System MUST accept the active profile_id on catalog and search endpoints to enable parental filtering

### Key Entities

- **Profile**: Represents a user profile within a household. Key attribute: `parental_rating` (TV-Y, TV-G, TV-PG, TV-14, TV-MA) and `is_kids` flag
- **Title**: A content item (movie or series) in the catalog. Key attribute: `age_rating` (TV-Y, TV-G, TV-PG, TV-14, TV-MA, or NULL)
- **Rating Hierarchy**: An ordered scale defining which content is visible to which profile level — TV-Y (most restrictive) through TV-MA (unrestricted)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A Kids profile (TV-Y) sees zero titles rated above TV-Y across all content surfaces (catalog, search, home rails, recommendations, featured)
- **SC-002**: A Family profile (TV-PG) sees zero titles rated above TV-PG across all content surfaces
- **SC-003**: An adult profile (TV-MA) sees the complete catalog with no titles filtered out
- **SC-004**: Direct navigation to a restricted title's detail page returns a clear restriction message instead of the content
- **SC-005**: Content surface load times remain unchanged (no perceptible performance difference) after filtering is applied

## Assumptions

- The TV content rating system used is the US TV Parental Guidelines: TV-Y, TV-G, TV-PG, TV-14, TV-MA (in ascending restrictiveness)
- All seed data titles already have an `age_rating` field populated — titles with NULL are treated as TV-MA
- The active profile is already identified via `profile_id` query parameter on viewing/recommendation endpoints; catalog and search endpoints will adopt the same pattern
- No PIN-based override is needed for this PoC — profile switching is sufficient access control
- Admin users are not subject to parental filtering when using the admin dashboard
