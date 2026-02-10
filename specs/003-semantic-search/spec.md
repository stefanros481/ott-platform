# Feature Specification: Semantic Search

**Feature Branch**: `003-semantic-search`
**Created**: 2026-02-10
**Status**: Draft
**Input**: Add hybrid semantic search combining keyword matching with vector similarity via Reciprocal Rank Fusion, with match explanations per result

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Natural Language Content Discovery (Priority: P1)

A viewer wants to find content by describing what they're in the mood for, rather than knowing an exact title. They type a natural language phrase like "dark comedy about office life" or "feel-good family adventure" into the search bar, and the system returns semantically relevant titles even when those exact words don't appear in any title or synopsis.

**Why this priority**: This is the core value proposition — the single feature that differentiates semantic search from the existing keyword search. Without this, there is no semantic search.

**Independent Test**: Can be tested by searching for descriptive phrases (mood, theme, style) that don't appear verbatim in any title metadata, and verifying that relevant results appear.

**Acceptance Scenarios**:

1. **Given** a catalog with 70+ titles that have content embeddings, **When** a viewer searches for "dark comedy about office life", **Then** the system returns titles matching that description ranked by relevance, even if none contain those exact words in their metadata.
2. **Given** a viewer searches for "90s thriller", **When** results are returned, **Then** titles from the 1990s in the thriller genre are ranked highest.
3. **Given** a viewer searches for "feel-good family adventure", **When** results are returned, **Then** family-friendly adventure titles appear regardless of whether "feel-good" appears in their metadata.

---

### User Story 2 - Match Explanations (Priority: P1)

A viewer sees search results and wants to understand why each result was returned. Each result displays a brief explanation such as "Title match", "Similar themes", or "Cast match" so the viewer can quickly assess relevance without reading full descriptions.

**Why this priority**: Match explanations are essential for user trust in AI-powered search. Without them, users won't understand why unfamiliar titles appear and may distrust the results.

**Independent Test**: Can be tested by verifying that every search result displays a non-empty match reason, and that reasons accurately reflect why the result was included (keyword field match vs. semantic similarity).

**Acceptance Scenarios**:

1. **Given** a viewer searches for a known title name (e.g., "Severance"), **When** results are displayed, **Then** the matching title shows "Title match" in its explanation.
2. **Given** a viewer searches for an actor's name, **When** results include titles featuring that actor, **Then** those results show "Cast match" in their explanation.
3. **Given** a viewer searches for a descriptive phrase with no keyword matches, **When** results are returned via semantic similarity, **Then** results show "Similar themes", "Strongly related themes", or "Related content" based on similarity strength.
4. **Given** a result that matched both by keyword and semantic similarity, **When** displayed, **Then** the explanation shows both reasons (e.g., "Description match · Similar themes").

---

### User Story 3 - Search Mode Toggle (Priority: P2)

A viewer can switch between "Smart Search" (hybrid keyword + semantic) and "Keyword" (traditional exact matching) modes. The default is Smart Search. An indicator shows when AI-powered search is active.

**Why this priority**: Some viewers may prefer exact keyword matching for specific lookups. The toggle provides user control over search behavior and transparency about when AI is involved.

**Independent Test**: Can be tested by toggling between modes for the same query and verifying that Smart Search returns broader, semantically relevant results while Keyword mode returns only exact text matches.

**Acceptance Scenarios**:

1. **Given** the search page loads, **When** no mode is explicitly selected, **Then** Smart Search (hybrid) mode is active by default and an AI indicator is visible.
2. **Given** a viewer toggles to Keyword mode, **When** they search for "dark comedy", **Then** only results containing the literal text "dark comedy" in their title, synopsis, or cast are returned.
3. **Given** a viewer toggles back to Smart Search mode, **When** they search for "dark comedy", **Then** results include both keyword matches and semantically similar titles.

---

### User Story 4 - Graceful Fallback (Priority: P2)

When the AI search component is unavailable (model loading failure, embedding service error), the system automatically falls back to keyword-only search without any visible error to the viewer. The experience degrades gracefully rather than failing.

**Why this priority**: Reliability is critical for search. Users should never see a broken search page. Fallback ensures the feature is resilient.

**Independent Test**: Can be tested by simulating an embedding service failure and verifying that search still returns keyword-based results.

**Acceptance Scenarios**:

1. **Given** the embedding model fails to load, **When** a viewer searches in hybrid mode, **Then** keyword results are returned and the AI indicator is hidden.
2. **Given** the semantic search endpoint returns an error, **When** the frontend receives the error, **Then** it automatically retries using the existing keyword search endpoint.
3. **Given** a very short query (1-2 characters), **When** submitted in hybrid mode, **Then** the system uses keyword-only search (semantic search requires sufficient text to produce meaningful embeddings).

---

### User Story 5 - Parental Filtering in Semantic Search (Priority: P2)

Search results respect the active profile's parental rating restrictions. Content that exceeds the profile's allowed rating is excluded from both keyword and semantic results.

**Why this priority**: Parental controls are a platform-wide requirement. Semantic search must not bypass existing content restrictions.

**Independent Test**: Can be tested by searching with a child profile active and verifying that age-restricted content never appears in results.

**Acceptance Scenarios**:

1. **Given** a child profile with a TV-G rating limit is active, **When** the viewer searches for any term, **Then** no results with ratings above TV-G are returned (neither keyword nor semantic matches).
2. **Given** an unrestricted adult profile is active, **When** the viewer searches, **Then** all content appears in results regardless of rating.

---

### Edge Cases

- What happens when the search query is empty or whitespace-only? The system requires at least 1 character and the frontend requires 2 characters before triggering a search.
- What happens when no content has embeddings? Semantic search returns empty results; keyword results still appear in hybrid mode.
- What happens when a query is extremely long (500+ characters)? The embedding model truncates input to its token limit; keyword search uses the full query. Results may vary in relevance for very long queries.
- What happens when all results have very low semantic similarity? Results below a minimum similarity threshold (0.2) are excluded to avoid irrelevant noise.
- What happens when keyword and semantic results are completely disjoint? Both sets are included, merged and ranked via Reciprocal Rank Fusion, with match type indicators showing which source contributed each result.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support natural language search queries that return semantically relevant results even when query terms don't appear literally in content metadata.
- **FR-002**: System MUST combine keyword search results and semantic search results into a single ranked list using Reciprocal Rank Fusion.
- **FR-003**: System MUST provide a match explanation for every search result indicating why it was included (e.g., "Title match", "Similar themes", "Cast match").
- **FR-004**: System MUST classify each result's match type as "keyword", "semantic", or "both".
- **FR-005**: System MUST support three search modes: "keyword" (traditional only), "semantic" (vector only), and "hybrid" (both combined). Default mode is "hybrid".
- **FR-006**: System MUST filter search results according to the active profile's parental rating restrictions.
- **FR-007**: System MUST fall back to keyword-only search when the embedding service is unavailable, with no user-visible error.
- **FR-008**: System MUST exclude semantic results with a similarity score below 0.2 to prevent irrelevant noise.
- **FR-009**: System MUST auto-downgrade to keyword-only mode for queries shorter than 3 characters, even when hybrid mode is requested.
- **FR-010**: System MUST display an AI indicator when semantic search is active and contributing to results.
- **FR-011**: System MUST preserve the existing keyword search endpoint unchanged for backwards compatibility.
- **FR-012**: Search results MUST include a similarity score (when available from semantic matching) for transparency.
- **FR-013**: The search interface MUST allow viewers to toggle between Smart Search and Keyword modes.
- **FR-014**: Match explanations MUST distinguish keyword match fields: title matches show "Title match", synopsis matches show "Description match", cast matches show "Cast match".
- **FR-015**: When a result appears in both keyword and semantic results, it MUST receive a ranking boost (inherent in RRF algorithm).

### Key Entities

- **Search Result**: A content title returned from search, enriched with match explanation (reason text, match type, optional similarity score). Extends the existing title representation with search-specific metadata.
- **Search Response**: A collection of search results with metadata about the query and search mode used. Distinct from the existing paginated catalog response to accommodate search-specific fields.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Viewers can discover content by describing what they want in natural language (e.g., "dark comedy about office life") and receive relevant results — at least 3 of the top 10 results should be thematically appropriate for descriptive queries.
- **SC-002**: Every search result displays a human-readable match explanation that accurately reflects why it was returned.
- **SC-003**: Search results appear within 3 seconds of query submission, including semantic processing time.
- **SC-004**: When AI search is unavailable, keyword search results appear with no user-visible error or delay beyond normal keyword search latency.
- **SC-005**: Parental rating filters apply consistently — zero age-restricted results appear for restricted profiles across all search modes.
- **SC-006**: Searching for an exact title name returns that title as the top result in hybrid mode (keyword match + semantic boost).

## Assumptions

- Content embeddings already exist for all titles in the catalog (generated via the admin panel).
- The embedding model (all-MiniLM-L6-v2, 384 dimensions) is sufficient for search quality. No model upgrade is planned in this feature.
- The existing keyword search behavior (ILIKE on title, synopsis, cast) defines the baseline. This feature adds to it without changing it.
- Search results are not paginated in the initial implementation — a single page of up to 30 results is returned. Pagination may be added later.
- No search analytics or query logging is included in this feature scope.

## Scope Boundaries

**In scope:**
- Backend hybrid search service (keyword + semantic + RRF merge)
- New search API endpoint with match explanations
- Frontend search page update with mode toggle and match reasons
- Parental filtering integration
- Graceful fallback on embedding service failure

**Out of scope:**
- Conversational search with session context (Phase 3 per PRD-007)
- Search query logging or analytics
- Elasticsearch integration
- LLM-based intent extraction
- Personalized search ranking based on viewing history
- Search suggestions / autocomplete
