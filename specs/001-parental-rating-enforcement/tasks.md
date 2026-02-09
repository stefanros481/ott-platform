# Tasks: Parental Rating Enforcement

**Input**: Design documents from `/specs/001-parental-rating-enforcement/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the rating hierarchy utility used by all subsequent tasks

- [x] T001 Create rating hierarchy helper module in backend/app/services/rating_utils.py — define `RATING_HIERARCHY = ["TV-Y", "TV-G", "TV-PG", "TV-14", "TV-MA"]`, implement `get_allowed_ratings(parental_rating: str) -> list[str] | None` that returns None for TV-MA (no filtering) or the list of allowed ratings for any other level, and `async resolve_profile_rating(db: AsyncSession, profile_id: UUID) -> list[str] | None` that fetches the profile's parental_rating from the profiles table and calls get_allowed_ratings

**Checkpoint**: rating_utils.py exists with both functions. Can be verified by importing and calling `get_allowed_ratings("TV-PG")` → `["TV-Y", "TV-G", "TV-PG"]` and `get_allowed_ratings("TV-MA")` → `None`.

---

## Phase 2: User Story 1 — Kids Profile Sees Only Age-Appropriate Content (Priority: P1) — MVP

**Goal**: A Kids profile (TV-Y) only sees TV-Y content across all content surfaces — catalog browse, search, featured, home rails, and similar titles.

**Independent Test**: Log in as admin@example.com, switch to "Kids" profile (TV-Y), browse catalog (should see only 4 titles), search for a TV-MA title (no results), check home rails (only TV-Y content), view a title detail "More Like This" (only TV-Y suggestions).

### Backend — Catalog Service

- [x] T002 [US1] Add `allowed_ratings: list[str] | None = None` parameter to `get_titles()` in backend/app/services/catalog_service.py — when not None, add `.where(Title.age_rating.in_(allowed_ratings))` to both the base query and count query
- [x] T003 [US1] Add `allowed_ratings: list[str] | None = None` parameter to `get_featured_titles()` in backend/app/services/catalog_service.py — when not None, add `.where(Title.age_rating.in_(allowed_ratings))` to the query

### Backend — Recommendation Service

- [x] T004 [US1] Add `allowed_ratings: list[str] | None = None` parameter to `get_similar_titles()` in backend/app/services/recommendation_service.py — when not None, add `AND t.age_rating IN :allowed` to the raw SQL WHERE clause; pass allowed_ratings as a tuple bindparam
- [x] T005 [US1] Add `allowed_ratings: list[str] | None = None` parameter to `get_for_you_rail()` in backend/app/services/recommendation_service.py — when not None, add `AND t.age_rating IN :allowed` to the raw SQL WHERE clause
- [x] T006 [US1] Add `allowed_ratings: list[str] | None = None` parameter to `_continue_watching_rail()` in backend/app/services/recommendation_service.py — when not None, add `AND t.age_rating IN :allowed` to the raw SQL WHERE clause
- [x] T007 [US1] Add `allowed_ratings: list[str] | None = None` parameter to `_new_releases_rail()` in backend/app/services/recommendation_service.py — when not None, add `.where(Title.age_rating.in_(allowed_ratings))` to the ORM query
- [x] T008 [US1] Add `allowed_ratings: list[str] | None = None` parameter to `_trending_rail()` in backend/app/services/recommendation_service.py — when not None, add `AND t.age_rating IN :allowed` to the raw SQL WHERE clause
- [x] T009 [US1] Add `allowed_ratings: list[str] | None = None` parameter to `_top_genre_rail()` in backend/app/services/recommendation_service.py — when not None, add `AND t.age_rating IN :allowed` to the titles fetch raw SQL
- [x] T010 [US1] Update `get_home_rails()` in backend/app/services/recommendation_service.py — add `allowed_ratings: list[str] | None = None` parameter and pass it through to all rail functions (_continue_watching_rail, get_for_you_rail, _new_releases_rail, _trending_rail, _top_genre_rail)
- [x] T011 [US1] Update `get_post_play()` in backend/app/services/recommendation_service.py — add `allowed_ratings: list[str] | None = None` parameter and pass it through to get_similar_titles

### Backend — Catalog Router

- [x] T012 [US1] Update `list_titles()` endpoint in backend/app/routers/catalog.py — add `profile_id: uuid.UUID = Query(..., description="Active profile")` parameter, call `resolve_profile_rating(db, profile_id)` to get allowed_ratings, pass to `catalog_service.get_titles()`
- [x] T013 [US1] Update `search_titles()` endpoint in backend/app/routers/catalog.py — add `profile_id` parameter, resolve allowed_ratings, pass to `catalog_service.get_titles()`
- [x] T014 [US1] Update `featured_titles()` endpoint in backend/app/routers/catalog.py — add `profile_id` parameter, resolve allowed_ratings, pass to `catalog_service.get_featured_titles()`

### Backend — Recommendations Router

- [x] T015 [US1] Update `home_rails()` endpoint in backend/app/routers/recommendations.py — call `resolve_profile_rating(db, profile_id)` and pass allowed_ratings to `recommendation_service.get_home_rails()`
- [x] T016 [US1] Update `similar_titles()` endpoint in backend/app/routers/recommendations.py — add `profile_id: uuid.UUID = Query(..., description="Active profile")` parameter, resolve allowed_ratings, pass to `recommendation_service.get_similar_titles()`
- [x] T017 [US1] Update `post_play()` endpoint in backend/app/routers/recommendations.py — make profile_id required (remove Optional/None default), resolve allowed_ratings, pass to `recommendation_service.get_post_play()`

### Frontend — API Layer

- [x] T018 [P] [US1] Update `getTitles()` in frontend-client/src/api/catalog.ts — add `profile_id` to CatalogParams interface and append it as query parameter
- [x] T019 [P] [US1] Update `getFeatured()` in frontend-client/src/api/catalog.ts — add `profileId: string` parameter and append `?profile_id={profileId}` to the URL
- [x] T020 [P] [US1] Update `getSimilarTitles()` in frontend-client/src/api/recommendations.ts — add `profileId: string` parameter and append `?profile_id={profileId}` to the URL

### Frontend — Pages

- [x] T021 [US1] Update BrowsePage in frontend-client/src/pages/BrowsePage.tsx — get profile from useAuth(), add profile_id to CatalogParams in the query function, add profile?.id to queryKey, redirect to /profiles if no profile
- [x] T022 [US1] Update HomePage in frontend-client/src/pages/HomePage.tsx — pass profile!.id to getFeatured() call, add profile?.id to featured queryKey
- [x] T023 [US1] Update SearchPage in frontend-client/src/pages/SearchPage.tsx — get profile from useAuth(), add profile_id to search params, add profile?.id to queryKey
- [x] T024 [US1] Update TitleDetailPage in frontend-client/src/pages/TitleDetailPage.tsx — pass profile!.id to getSimilarTitles() call, add profile?.id to similar titles queryKey

**Checkpoint**: Kids profile (TV-Y) sees only 4 titles in catalog browse. Search for "TV-MA title name" returns nothing. All home rails show only TV-Y content. "More Like This" on a TV-Y title shows only TV-Y suggestions. Adult profile (TV-MA) sees all 70 titles unchanged.

---

## Phase 3: User Story 2 — Family Profile Sees Content Up to Its Rating Level (Priority: P1)

**Goal**: A Family profile (TV-PG) sees TV-Y + TV-G + TV-PG content (28 titles). A TV-14 profile sees everything except TV-MA. The rating hierarchy is enforced as a "less than or equal to" comparison, not exact match.

**Independent Test**: Log in as standard@example.com, switch to "Family" profile (TV-PG), browse catalog — should see 28 titles. TV-14 and TV-MA titles should not appear.

> **Note**: This story requires NO additional code changes. It is automatically satisfied by the rating hierarchy implemented in T001 (`get_allowed_ratings("TV-PG")` returns `["TV-Y", "TV-G", "TV-PG"]`). This phase is a validation-only checkpoint.

- [ ] T025 [US2] Verify Family profile (TV-PG) filtering by browsing catalog as standard@example.com / Family profile — confirm 28 titles visible (TV-Y: 4, TV-G: 7, TV-PG: 17), confirm TV-14 and TV-MA titles excluded

**Checkpoint**: Family profile sees exactly TV-Y + TV-G + TV-PG content across all surfaces.

---

## Phase 4: User Story 3 — Unrestricted Profile Sees All Content (Priority: P1)

**Goal**: Adult profiles (TV-MA) see the complete catalog with zero filtering overhead. The `get_allowed_ratings("TV-MA")` returns None, which means no WHERE clause is added to queries.

**Independent Test**: Log in as admin@example.com, select "Admin" profile (TV-MA), browse catalog — should see all 70 titles. Verify all home rails work as before.

> **Note**: This story requires NO additional code changes. It is automatically satisfied by the TV-MA bypass in T001 (`get_allowed_ratings("TV-MA")` returns `None`). This phase is a validation-only checkpoint.

- [ ] T026 [US3] Verify Adult profile (TV-MA) sees all content by browsing catalog as admin@example.com / Admin profile — confirm all 70 titles visible, all home rails populated, search returns full results

**Checkpoint**: Adult profile experience is identical to pre-feature behavior.

---

## Phase 5: User Story 4 — Title Detail Page Blocked for Restricted Content (Priority: P2)

**Goal**: When a restricted profile navigates directly to a title detail page above their rating, the system returns a 403 and the frontend shows a restriction message.

**Independent Test**: On Kids profile (TV-Y), navigate directly to `/title/{tv-ma-title-id}` — should see "Content not available for this profile" instead of the title detail.

### Backend

- [x] T027 [US4] Update `get_title()` endpoint in backend/app/routers/catalog.py — add `profile_id` parameter, call `resolve_profile_rating()`, if allowed_ratings is not None and title.age_rating not in allowed_ratings, raise HTTPException(status_code=403, detail="Content not available for this profile")

### Frontend

- [x] T028 [US4] Update `getTitleById()` in frontend-client/src/api/catalog.ts — add `profileId: string` parameter and append `?profile_id={profileId}` to the URL
- [x] T029 [US4] Update TitleDetailPage in frontend-client/src/pages/TitleDetailPage.tsx — pass profile!.id to getTitleById(), handle 403 error response by showing a "Content not available for this profile" message with a back button instead of the title detail content

**Checkpoint**: Kids profile navigating to a TV-MA title URL sees restriction message. Kids profile navigating to a TV-Y title URL sees normal detail page.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and edge case verification

- [ ] T030 Verify NULL age_rating handling — confirm that titles with NULL age_rating are hidden from restricted profiles (TV-Y, TV-PG) but visible to TV-MA profiles
- [ ] T031 Verify profile switch refreshes content — switch from Adult to Kids profile mid-session, confirm catalog and home rails update on next navigation without requiring a browser refresh
- [ ] T032 Run full quickstart.md validation — execute all test scenarios from specs/001-parental-rating-enforcement/quickstart.md end to end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — creates rating_utils.py
- **Phase 2 (US1)**: Depends on Phase 1 — implements all backend and frontend changes
- **Phase 3 (US2)**: Depends on Phase 2 — validation only, no code changes
- **Phase 4 (US3)**: Depends on Phase 2 — validation only, no code changes
- **Phase 5 (US4)**: Depends on Phase 2 — adds 403 blocking on title detail
- **Phase 6 (Polish)**: Depends on all previous phases

### Within Phase 2 (US1) — Task Dependencies

```
T001 (rating_utils.py)
  ├── T002, T003 (catalog_service.py) ─── T012, T013, T014 (catalog router)
  ├── T004-T011 (recommendation_service.py) ─── T015, T016, T017 (recommendations router)
  └── T018, T019, T020 (frontend API) ─── T021, T022, T023, T024 (frontend pages)
```

- Backend service tasks (T002-T011) can run in parallel across catalog_service and recommendation_service
- Backend router tasks (T012-T017) depend on their respective service tasks
- Frontend API tasks (T018-T020) are parallel with each other and with backend tasks
- Frontend page tasks (T021-T024) depend on their corresponding API tasks

### Parallel Opportunities

Within Phase 2:
- T002+T003 (catalog_service) can run parallel with T004-T011 (recommendation_service)
- T018, T019, T020 (frontend API files) can run in parallel with each other
- Backend and frontend work can proceed in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Create rating_utils.py
2. Complete Phase 2: All backend + frontend changes for US1
3. **STOP and VALIDATE**: Test Kids profile (TV-Y) across all surfaces
4. This delivers the core safety feature

### Full Delivery

1. Phase 1 → Phase 2 → Validate US1/US2/US3 (no extra code for US2/US3)
2. Phase 5 → Validate US4 (title detail blocking)
3. Phase 6 → Final validation

### Estimated Scope

- **New files**: 1 (rating_utils.py)
- **Modified backend files**: 4 (catalog_service.py, recommendation_service.py, catalog.py, recommendations.py)
- **Modified frontend files**: 6 (catalog.ts, recommendations.ts, BrowsePage.tsx, HomePage.tsx, SearchPage.tsx, TitleDetailPage.tsx)
- **Total tasks**: 32 (1 setup + 23 US1 + 1 US2 validation + 1 US3 validation + 3 US4 + 3 polish)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US2 and US3 are validation-only phases (the rating hierarchy in T001 handles both automatically)
- The TV-MA bypass (`None` return) ensures zero performance impact for adult profiles
- All raw SQL queries in recommendation_service use tuple bindparams for the IN clause to prevent SQL injection
- Commit after each phase for clean rollback points
