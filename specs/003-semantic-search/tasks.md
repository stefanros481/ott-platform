# Tasks: Semantic Search

**Input**: Design documents from `/specs/003-semantic-search/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Not requested — manual validation via Swagger UI and browser per quickstart.md.

**Organization**: Tasks grouped by user story. Backend search service is foundational (serves all stories). Frontend tasks map to individual stories.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1–US5) this task belongs to
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Schemas)

**Purpose**: Add response schemas used by all subsequent tasks

- [x] T001 Add `SearchResultItem` and `SemanticSearchResponse` schemas after `PaginatedResponse` in `backend/app/schemas/catalog.py`. SearchResultItem has all TitleListItem fields plus `match_reason: str`, `match_type: str`, `similarity_score: float | None`. SemanticSearchResponse wraps `items: list[SearchResultItem]`, `total: int`, `query: str`, `mode: str`.

---

## Phase 2: Foundation (Backend Search Service + Endpoint)

**Purpose**: Core search infrastructure that ALL user stories depend on. Implements keyword search with field-level match detection, semantic search via pgvector, hybrid merge via RRF, match reason generation, parental filtering, and graceful fallback. This phase covers the backend portions of US1, US2, US4, and US5 in a single coherent service.

**⚠️ CRITICAL**: No frontend work can begin until this phase is complete.

- [x] T002 Create `backend/app/services/search_service.py` with `keyword_search(db, query, allowed_ratings, limit)`. Use ILIKE pattern from `backend/app/services/catalog_service.py:50-65`. Query `titles` joined with `title_genres`→`genres` for genre names. For each result, determine which fields matched (title, synopsis_short, synopsis_long, cast) by checking `pattern in field.lower()` post-query. Include `mood_tags` and `genres` in results. Return list of dicts with title metadata + `match_fields: list[str]`.
- [x] T003 Add `semantic_search(db, query_text, allowed_ratings, limit)` to `backend/app/services/search_service.py`. Call `embedding_service.generate_embedding(query_text)` to get 384-dim vector. Use pgvector cosine query pattern from `backend/app/services/recommendation_service.py:66-87` but WITHOUT the `WHERE title_id != :source_id` exclusion. Apply `allowed_ratings` filter via `AND t.age_rating IN :allowed`. Filter out results with similarity < 0.2. Return list of dicts with title metadata + `similarity_score: float`.
- [x] T004 Add `_reciprocal_rank_fusion(keyword_hits, semantic_hits, k=60)` to `backend/app/services/search_service.py`. For each list, compute RRF score per item: `score += 1/(k + rank)` where rank is 1-indexed position. Merge into single dict keyed by title ID, summing scores for items in both lists. Return sorted by descending RRF score.
- [x] T005 Add `_build_match_reason(keyword_hit, semantic_hit)` to `backend/app/services/search_service.py`. If keyword_hit: map match_fields to labels — "title"→"Title match", "synopsis_short"/"synopsis_long"→"Description match", "cast"→"Cast match". If semantic_hit: score > 0.6→"Strongly related themes", > 0.4→"Similar themes", > 0.2→"Related content". Join multiple reasons with " · ". Also determine `match_type`: "both" if both hits, "keyword" or "semantic" if only one.
- [x] T006 Add `hybrid_search(db, query_text, mode, allowed_ratings, limit)` to `backend/app/services/search_service.py`. If mode=="keyword": call keyword_search only. If mode=="semantic": call semantic_search only. If mode=="hybrid": call both and merge with `_reciprocal_rank_fusion`. For queries < 3 chars, auto-downgrade to keyword. Wrap `semantic_search` call in try/except — on failure, log warning and return keyword results only. Build final list of `SearchResultItem`-compatible dicts using `_build_match_reason`.
- [x] T007 Add `GET /search/semantic` endpoint after line 185 in `backend/app/routers/catalog.py`. Import `SemanticSearchResponse` from schemas and `search_service` from services. Parameters: `q: str = Query(..., min_length=1)`, `mode: str = Query("hybrid", pattern="^(keyword|semantic|hybrid)$")`, `page_size: int = Query(20, ge=1, le=100)`, `profile_id: uuid.UUID | None = Query(None)`. Use `resolve_profile_rating(db, profile_id)` for parental filtering. Call `search_service.hybrid_search()`. Return `SemanticSearchResponse`.

**Checkpoint**: Backend is fully functional. Test via Swagger at `http://localhost:8000/docs`:
- `GET /catalog/search/semantic?q=dark+comedy+about+office+life` — returns results with match_reason
- `GET /catalog/search/semantic?q=comedy&mode=keyword` — keyword-only results
- `GET /catalog/search/semantic?q=feel-good+family+adventure&mode=semantic` — semantic-only results
- Existing `GET /catalog/search?q=comedy` still works unchanged

---

## Phase 3: User Story 1+2 — Natural Language Discovery + Match Explanations (Priority: P1) 🎯 MVP

**Goal**: Viewers can search using natural language and see match explanations for each result.

**Independent Test**: Search for "dark comedy about office life" → results appear with explanations like "Similar themes". Search for a known title → shows "Title match".

- [x] T008 [P] [US1] Add `SearchResultItem` interface, `SemanticSearchResponse` interface, `SemanticSearchParams` interface, and `semanticSearch()` function to `frontend-client/src/api/catalog.ts`. SearchResultItem extends TitleListItem with `match_reason: string`, `match_type: 'keyword' | 'semantic' | 'both'`, `similarity_score: number | null`. Use the `apiFetch` + `URLSearchParams` pattern from existing `getTitles()`. Endpoint: `/catalog/search/semantic`.
- [x] T009 [US1] Update `frontend-client/src/pages/SearchPage.tsx` to use `semanticSearch()` instead of `getTitles()` for the search query. Import `semanticSearch` from API. Change TanStack Query to call `semanticSearch({ q: debouncedQuery, page_size: 30, profile_id: profile!.id })`. Update `queryKey` to `['semantic-search', ...]`.
- [x] T010 [US2] Add match reason display below each TitleCard in `frontend-client/src/pages/SearchPage.tsx`. Wrap each result in a div. Below TitleCard, add a `<p>` with `text-xs text-gray-500 truncate` showing `item.match_reason`. Add left border color based on `match_type`: `border-l-2 border-primary-500` for "both", `border-l-2 border-teal-500` for "semantic", no border for "keyword".
- [x] T011 [US2] Update placeholder text in SearchPage to `"Try: dark comedy about office life, 90s thriller..."`. Update the empty-state "Type to search" section with subtitle: `"Describe what you're in the mood for"`.

**Checkpoint**: Search works with natural language. Results show match reasons. Old keyword search still works.

---

## Phase 4: User Story 3 — Search Mode Toggle (Priority: P2)

**Goal**: Viewers can switch between "Smart Search" and "Keyword" modes with an AI indicator.

**Independent Test**: Toggle to Keyword, search "dark comedy" — only exact matches. Toggle to Smart Search — semantic results appear too.

- [x] T012 [US3] Add `mode` state (`'hybrid' | 'keyword'`, default `'hybrid'`) to `frontend-client/src/pages/SearchPage.tsx`. Pass `mode` to `semanticSearch()` params. Update queryKey to include `mode`.
- [x] T013 [US3] Add mode toggle segmented control below the search input in `frontend-client/src/pages/SearchPage.tsx`. Two buttons: "Smart Search" (mode='hybrid') and "Keyword" (mode='keyword'). Active button uses `bg-primary-500 text-white`, inactive uses `bg-surface-overlay text-gray-400`. Wrap in a `flex gap-2` container with `mt-3`.
- [x] T014 [US3] Add AI sparkle badge next to result count in `frontend-client/src/pages/SearchPage.tsx`. When `mode !== 'keyword'`, show a `<span>` with sparkle SVG icon + "AI" text using `text-xs text-primary-400 bg-primary-500/10 px-2 py-0.5 rounded-full inline-flex items-center gap-1`.

**Checkpoint**: Mode toggle works. Keyword mode returns only exact matches. AI badge shows/hides correctly.

---

## Phase 5: User Story 4 — Graceful Fallback (Priority: P2)

**Goal**: Search never breaks — if semantic search fails, keyword results appear seamlessly.

**Independent Test**: Verify search still works when semantic endpoint errors. Short queries (1-2 chars) use keyword only.

- [x] T015 [US4] Add fallback query to `frontend-client/src/pages/SearchPage.tsx`. Use TanStack Query's `isError` state from the semantic search query. Add a second `useQuery` that calls `getTitles({ q: debouncedQuery, page_size: 30, profile_id: profile!.id })` with `enabled: isError && debouncedQuery.length >= 2`. Use semantic results when available, fallback results otherwise. When using fallback, map results to add `match_reason: 'Keyword match'`, `match_type: 'keyword'`, `similarity_score: null`.
- [x] T016 [US4] Hide AI badge when fallback is active in `frontend-client/src/pages/SearchPage.tsx`. Check if using fallback results (`isError` or mode is 'keyword') and conditionally hide the sparkle badge and set mode display to keyword.

**Checkpoint**: Deliberately break semantic endpoint (e.g., bad URL) — verify search still returns keyword results with no error visible to user.

---

## Phase 6: Polish & Validation

**Purpose**: End-to-end validation and cleanup

- [x] T017 Run full validation per `specs/003-semantic-search/quickstart.md` — test all 3 modes (hybrid, keyword, semantic) via Swagger and frontend browser
- [x] T018 Verify parental filtering: search with a child profile active and confirm no age-restricted results appear (covers US5 — parental filtering is handled entirely by backend T007 via `resolve_profile_rating`)
- [x] T019 Verify backwards compatibility: confirm `GET /catalog/search?q=comedy` returns identical results to before this feature

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundation (Phase 2)**: Depends on Phase 1 — BLOCKS all frontend work
- **US1+US2 (Phase 3)**: Depends on Phase 2 — T008 can start immediately after Phase 2; T009-T011 are sequential
- **US3 (Phase 4)**: Depends on Phase 3 (needs working SearchPage with semantic search)
- **US4 (Phase 5)**: Depends on Phase 4 (needs mode toggle to properly hide AI badge)
- **Polish (Phase 6)**: Depends on all previous phases

### User Story Dependencies

- **US1+US2 (P1)**: Backend foundation (Phase 2) → API client (T008) → SearchPage (T009-T011)
- **US3 (P2)**: Depends on US1+US2 complete (builds on SearchPage changes)
- **US4 (P2)**: Depends on US3 (needs mode toggle for badge hiding logic)
- **US5 (P2)**: No dedicated frontend tasks — fully implemented by backend T007 (`resolve_profile_rating` integration). Validated in T018.

### Within Phase 2 (Backend)

Tasks T002→T003→T004→T005→T006 are sequential (each builds on the previous function). T007 depends on T006.

### Parallel Opportunities

- T008 (frontend API client) can be written immediately after Phase 2 without waiting for other frontend tasks
- Phase 6 validation tasks (T017, T018, T019) can run in parallel

---

## Implementation Strategy

### MVP First (US1+US2)

1. Complete Phase 1: Schemas (T001)
2. Complete Phase 2: Backend service + endpoint (T002–T007)
3. Complete Phase 3: Frontend search + match reasons (T008–T011)
4. **STOP and VALIDATE**: Test semantic search end-to-end
5. This delivers the core value: natural language search with explanations

### Full Feature

6. Phase 4: Mode toggle (T012–T014)
7. Phase 5: Fallback handling (T015–T016)
8. Phase 6: Polish and validation (T017–T019)

---

## Notes

- No database migrations needed — all queries are read-only against existing tables
- Backend search_service.py is the only new file; all others are modifications
- US5 (Parental Filtering) has no dedicated tasks — it's inherently handled by the `allowed_ratings` parameter threaded through T002, T003, T006, and T007, using the same `resolve_profile_rating()` pattern as existing endpoints
- The embedding model loads lazily on first semantic search query (~2-3 seconds cold start); subsequent queries are fast
