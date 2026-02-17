# Research: Recommendations Quality, Watchlist Rail & Live TV Playback

## R-01: Thumbs-Down Exclusion Bug

**Decision**: Exclude thumbs-down rated title IDs from both the centroid computation and the final results.

**Rationale**: The current code (`get_for_you_rail` lines 126-139) fetches thumbs-up rated IDs (`Rating.rating == 1`) and ALL bookmark IDs. While thumbs-down ratings are not directly included in `rated_ids`, a title that was bookmarked (user started watching) AND later thumbs-downed still has its embedding in the centroid via the `bookmarked_ids` set. The fix must:
1. Query thumbs-down IDs separately
2. Remove them from `interacted_ids` (so their embeddings don't enter the centroid)
3. Add them to `excluded_ids` in the similarity query (so they never appear in results)

**Alternatives considered**:
- Only remove from centroid, not from results → Rejected: user explicitly disliked, should never see
- Use negative embeddings (subtract instead of ignore) → Rejected: over-engineering for PoC, unpredictable centroid shifts

## R-02: Thumbs-Up 2x Weighting

**Decision**: Duplicate thumbs-up embedding vectors in the centroid calculation (effectively 2x weight vs 1x for bookmarks).

**Rationale**: A thumbs-up is an explicit positive signal; a bookmark is merely "started watching." Doubling the embedding contribution for rated titles biases the centroid toward explicitly preferred content. `np.mean()` over a list where rated embeddings appear twice naturally gives them 2x weight.

**Alternatives considered**:
- Weighted average with explicit float weights → Rejected: more complex, same result for 2x
- 3x weighting → Rejected: too aggressive, could narrow recommendations excessively
- Configurable weight → Rejected: over-engineering for PoC

## R-03: Watchlist Rail Position

**Decision**: Insert "My List" rail after "Continue Watching" and before "For You" in `get_home_rails`.

**Rationale**: This matches Netflix/Disney+ convention. The user's explicit saves are more actionable than algorithmic recommendations. The rail uses `watchlist` table joined to `titles`, ordered by `added_at DESC`, limited to 20 items.

**Alternatives considered**: N/A — position was clarified by user.

## R-04: Post-Play Next Episode — Backend vs Frontend

**Decision**: Add next-episode logic to the backend `get_post_play` service function, prepending the next episode to the similar titles list.

**Rationale**: The frontend PlayerPage.tsx (lines 54-82) already computes `nextEpisodeId` for auto-play navigation. However, the backend `get_post_play` API is consumed by any client and should be self-contained. Adding next-episode awareness to the API makes it correct for all consumers, not just the current React frontend.

**Implementation**: Query `episodes` → `seasons` to find the next episode by `episode_number + 1` (same season) or first episode of `season_number + 1`. The Episode model has `episode_number` and Season has `season_number` (both confirmed in catalog.py:72-96 with unique constraints from migration 001).

**Alternatives considered**:
- Leave backend as-is, rely on frontend → Rejected: API should be complete for any client
- Return next episode as a separate field instead of prepending to list → Rejected: changes response schema, adds complexity

## R-05: Cold-Start Fallback

**Decision**: When `get_for_you_rail` returns empty (no interactions), substitute a "Popular Now" rail using the time-decayed trending logic (R-06).

**Rationale**: This reuses the improved trending computation rather than inventing a new "top rated" metric. Since the platform uses binary ratings with potentially sparse data, recent popularity (bookmarks) is a more reliable signal than ratings for new users.

**Alternatives considered**:
- Use ratings-based "Top Rated" → Rejected by user: "Popular Now" preferred
- Show nothing (rely on other rails) → Rejected: For You slot is prominent real estate
- Editor's Picks (featured titles) → Rejected: featured titles already have their own slot

## R-06: Time-Decay Function

**Decision**: Use exponential decay with 7-day half-life: `EXP(-seconds_since_bookmark / (7 * 86400))`.

**Rationale**: PostgreSQL supports `EXP()` and `EXTRACT(EPOCH FROM ...)` natively. A 7-day window matches the spec requirement. Exponential decay is smooth and well-understood — a bookmark from 7 days ago contributes ~37% of a fresh bookmark.

**Fallback**: If no bookmarks exist in recent history, the decay function still returns values (just very small), so all-time popular titles still appear — they just rank lower than freshly popular ones. The rail is never empty.

**Alternatives considered**:
- Linear decay → Rejected: creates a hard cutoff at the window boundary
- Step function (last 7 days only) → Rejected: abrupt, no graceful fallback
- Configurable decay constant → Rejected: over-engineering for PoC

## R-11: Personalized Featured Titles

**Decision**: Compute profile centroid (reuse For You logic), then sort featured titles by cosine similarity to centroid. Fall back to `created_at DESC` for new profiles.

**Rationale**: Featured titles are already filtered by `is_featured=True` (catalog_service.py:107). The personalization layer just reorders them per profile. Using the same centroid as For You ensures consistency. The change is in catalog_service.py or a new recommendation_service function — the router just needs to pass `profile_id`.

**Alternatives considered**:
- Fetch embeddings for featured titles and compare → This IS the approach (via pgvector)
- Use genre overlap instead of embeddings → Rejected: embeddings capture richer similarity
- Move featured to recommendations router → Rejected: keep catalog ownership, just add personalization call

## S-01: Semantic Search N+1 Fix

**Decision**: Replace the per-result genre query loop with a single batch query after the main similarity search.

**Rationale**: Current code (search_service.py:144-151) executes N+1 queries (1 per result + the main query). For 30 results, that's 31 queries. A single batch query with `WHERE tg.title_id IN :ids` reduces this to 2 queries total. The genre names are then mapped to results by title_id.

**Alternatives considered**:
- JOIN genres in the main similarity query → Rejected: complicates the raw SQL vector query with GROUP_CONCAT/array_agg
- Use SQLAlchemy selectinload → Rejected: main query uses raw text() SQL for pgvector compatibility

## A-06: Vector Index — SKIP

**Decision**: No work needed. HNSW index already exists.

**Rationale**: Migration 001 (lines 231-235) creates: `CREATE INDEX idx_content_embedding_hnsw ON content_embeddings USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)`. All recommendation queries use the `<=>` operator which matches `vector_cosine_ops`. The index is already active.

**Alternatives considered**: N/A — the work is already done.

## L-01: EPG Click-to-Play Architecture

**Decision**: Navigate to existing PlayerPage at `/play/live/{channelId}` with channel and program data passed via React Router state. PlayerPage handles the `live` type by using `channel.hls_live_url` and displaying EPG program info.

**Rationale**: The route `/play/:type/:id` already exists and the player already passes `isLive={type === 'live'}` to VideoPlayer (PlayerPage.tsx:294). The minimal change is:
1. EpgPage: navigate with channel/program state
2. PlayerPage: add a `live` branch in the `playbackInfo` useMemo that reads from route state
3. Start Over: calculate seconds since program start, seek to that offset from stream start

**EPG program updates while watching**: Use the program's `end_time` to set a timer. When the timer fires, fetch the new current program for the channel and update the display. This avoids polling.

**Start Over implementation**: The existing "Start from beginning" sets `startPosition = 0`. For live, we calculate `programStartOffset = (now - program.start_time).seconds` and seek to `liveEdge - programStartOffset`. Shaka Player supports seeking within the DVR window via `player.seekTo(targetTime)`.

**Alternatives considered**:
- Create a separate LivePlayerPage → Rejected: violates reuse requirement, duplicates player logic
- Fetch channel data via API instead of route state → Could be a fallback if route state is missing (e.g., deep link to `/play/live/123`), but route state is the primary path from EPG
- Use WebSocket for live EPG updates → Rejected: over-engineering for PoC; timer-based is sufficient
