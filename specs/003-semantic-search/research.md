# Research: Semantic Search

## R1: Hybrid Search Merging Strategy

**Decision**: Reciprocal Rank Fusion (RRF) with K=60
**Rationale**: RRF is a well-established, parameter-light algorithm for merging ranked lists from different retrieval systems. K=60 is the standard constant from the original Cormack et al. paper. It requires no score normalization (unlike weighted sum) and naturally boosts results that appear in both lists.
**Alternatives considered**:
- Weighted linear combination (requires normalizing keyword and semantic scores to same scale — fragile)
- Interleaving (alternating results — doesn't account for relevance strength)
- Re-ranking via LLM (overkill for PoC, adds latency and dependency)

## R2: Semantic Similarity Threshold

**Decision**: Minimum similarity score of 0.2 for inclusion
**Rationale**: all-MiniLM-L6-v2 with cosine similarity produces scores roughly in the 0.1–0.8 range for typical queries. Below 0.2, results are effectively noise. Thresholds: >0.6 "Strongly related", >0.4 "Similar themes", >0.2 "Related content".
**Alternatives considered**:
- No threshold (includes irrelevant noise in results)
- Higher threshold 0.3+ (too aggressive, misses loosely related but valid results)
- Dynamic threshold based on result distribution (complexity not justified for PoC)

## R3: Query Embedding Approach

**Decision**: Reuse `embedding_service.generate_embedding()` with the user's raw query text
**Rationale**: The same model (all-MiniLM-L6-v2) that generates content embeddings should embed queries for consistent vector space. No query preprocessing or expansion needed — the model handles natural language well at 384 dimensions.
**Alternatives considered**:
- Query expansion via LLM before embedding (adds latency, Bedrock dependency — out of scope)
- Separate query-tuned model (asymmetric retrieval models like ms-marco — unnecessary for 70 titles)

## R4: Keyword Match Field Detection

**Decision**: Run separate ILIKE checks per field and track which fields matched via Python-side post-processing
**Rationale**: SQLAlchemy's `or_()` pattern doesn't natively report which branch matched. Running the pattern check per field in the result processing loop (after fetching matching rows) is simpler than SQL CASE expressions and sufficient for 70 titles.
**Alternatives considered**:
- SQL CASE expressions per field (works but verbose, harder to maintain)
- Full-text search with ts_rank (requires GIN index setup, migration — overkill for PoC)

## R5: Frontend Fallback Strategy

**Decision**: TanStack Query `onError` triggers a fallback query to the existing `/catalog/search` endpoint
**Rationale**: The existing keyword search endpoint remains unchanged (FR-011). If the semantic endpoint fails, the frontend can seamlessly fall back by re-issuing the query to the old endpoint. The user sees results either way.
**Alternatives considered**:
- Backend-only fallback (already implemented — backend falls back to keyword on embedding failure)
- Frontend retry with exponential backoff (unnecessary — keyword fallback is instant)

## R6: New Endpoint vs Extending Existing

**Decision**: New endpoint at `/catalog/search/semantic` rather than modifying `/catalog/search`
**Rationale**: The existing `/search` returns `PaginatedResponse[TitleListItem]` which lacks `match_reason`, `match_type`, and `similarity_score` fields. Changing its return type would break the API contract. A new sub-path keeps the old endpoint intact (FR-011) and makes the new one opt-in.
**Alternatives considered**:
- Add `mode` parameter to existing `/search` (breaks response schema contract)
- Version the API `/v2/search` (premature, no other v2 endpoints)
