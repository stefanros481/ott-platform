# Implementation Plan: Recommendations Quality, Watchlist Rail & Live TV Playback

**Branch**: `011-recs-watchlist-livetv` | **Date**: 2026-02-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/011-recs-watchlist-livetv/spec.md`

## Summary

Fix the highest-ROI recommendation quality bugs (thumbs-down exclusion, thumbs-up weighting), surface the existing watchlist as a home screen rail, add next-episode awareness to post-play, implement cold-start and time-decayed trending, personalize featured titles, fix the semantic search N+1 bug, and wire EPG click-to-play using the existing player with EPG program context and Start Over.

All changes are to existing services, routers, and frontend components. No new database tables. One migration (skip — HNSW vector index already exists).

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5+ (frontend)
**Primary Dependencies**: FastAPI 0.115+, SQLAlchemy 2.0+ (async), React 18, TanStack Query, Shaka Player 4+
**Storage**: PostgreSQL 16 + pgvector 0.7+ (existing schema, no new tables)
**Testing**: pytest + pytest-asyncio (backend), manual verification (frontend PoC)
**Target Platform**: Docker Compose (local development)
**Project Type**: Web application (backend + 2 frontends)
**Performance Goals**: Home rails < 500ms p95, semantic search < 500ms p95, live TV playback start < 3s
**Constraints**: No new tables, no new user-facing endpoints, PoC-quality frontend
**Scale/Scope**: 500+ titles, 50-100 channels, single FastAPI process

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. PoC-First Quality | PASS | All changes are functional correctness fixes to existing code |
| II. Monolithic Simplicity | PASS | All changes within existing FastAPI app, no new services |
| III. AI-Native by Default | PASS | Improves recommendation quality, adds personalized featured, adds EPG-aware playback |
| IV. Docker Compose as Truth | PASS | No new containers or external services |
| V. Seed Data as Demo | PASS | Existing seed data sufficient; watchlist/ratings already seeded |

**No violations. No complexity tracking needed.**

## Project Structure

### Documentation (this feature)

```text
specs/011-recs-watchlist-livetv/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (existing models, no changes)
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (API contract changes)
│   └── home-rails.yaml  # Updated home rails response
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── services/
│   │   ├── recommendation_service.py  # R-01, R-02, R-03, R-04, R-05, R-06, R-11
│   │   ├── search_service.py          # S-01 (N+1 fix)
│   │   └── catalog_service.py         # R-11 (personalized featured)
│   └── routers/
│       └── catalog.py                 # Featured endpoint update (R-11)
└── tests/

frontend-client/
├── src/
│   ├── pages/
│   │   ├── EpgPage.tsx                # L-01 (wire click handler)
│   │   ├── PlayerPage.tsx             # L-01 (live TV type handler)
│   │   └── HomePage.tsx               # Verify new rails render
│   └── api/
│       └── epg.ts                     # L-01 (channel playback data)
```

**Structure Decision**: Web application — backend/ + frontend-client/. All changes to existing files. No new source files needed.

## Design Decisions

### DD-01: Thumbs-Down Exclusion (R-01)

**Current state**: `get_for_you_rail` (recommendation_service.py:111-195) fetches thumbs-up rated IDs (line 132: `Rating.rating == 1`) and all bookmark IDs. It computes a centroid from the union of both sets. Thumbs-down titles are not explicitly in the centroid, but if a user bookmarked a title AND thumbs-downed it, the bookmark embedding still pollutes the centroid.

**Change**: After collecting `bookmarked_ids` and `rated_ids`:
1. Fetch thumbs-down title IDs: `SELECT title_id FROM ratings WHERE profile_id = :pid AND rating = -1`
2. Subtract thumbs-down IDs from `interacted_ids` before computing the centroid
3. Add thumbs-down IDs to the `excluded_ids` in the similarity query (so they never appear in results)

### DD-02: Thumbs-Up 2x Weighting (R-02)

**Current state**: All embeddings weighted equally via `np.mean(vectors)`.

**Change**: When fetching embeddings for the centroid, duplicate the vectors for thumbs-up rated titles. Concretely: build a weighted vector list where each thumbs-up title's embedding appears twice, bookmark-only titles appear once. Then compute `np.mean(weighted_vectors)`.

### DD-03: Watchlist Rail (R-03)

**Current state**: `WatchlistItem` model exists (viewing.py:39-44). `get_home_rails` does not include a watchlist rail.

**Change**: Add `_watchlist_rail(db, profile_id, allowed_ratings)` function that queries:
```sql
SELECT t.* FROM watchlist w
JOIN titles t ON t.id = w.title_id
WHERE w.profile_id = :pid [AND t.age_rating IN :allowed]
ORDER BY w.added_at DESC
LIMIT 20
```
Insert into `get_home_rails` after Continue Watching, before For You (rail_type: `"watchlist"`, name: `"My List"`).

### DD-04: Post-Play Next Episode (R-04)

**Current state**: `get_post_play` (recommendation_service.py:536-544) just calls `get_similar_titles`. Frontend PlayerPage.tsx already has next-episode logic (lines 54-82) for auto-play, but the API doesn't return it.

**Change**: In `get_post_play`, check if the given `title_id` is an episode:
1. Query: `SELECT e.*, s.title_id AS series_id, s.season_number FROM episodes e JOIN seasons s ON s.id = e.season_id WHERE e.id = :title_id`
2. If it's an episode, find next: same season + episode_number + 1, or first episode of next season
3. Prepend the next episode to the similar titles list (converting to the same dict format)
4. If not an episode (movie), current behavior unchanged

### DD-05: Cold-Start "Popular Now" (R-05)

**Current state**: `get_for_you_rail` returns `[]` when no interactions exist. No fallback rail shown.

**Change**: In `get_home_rails`, when `get_for_you_rail` returns empty:
1. Call the updated `_trending_rail` (which now uses time-decay from DD-06)
2. Return it as `{"name": "Popular Now", "rail_type": "popular_now", "items": items}`
3. This replaces the For You position in the rail order

### DD-06: Time-Decayed Trending (R-06)

**Current state**: `_trending_rail` uses `COUNT(b.id)` — no time weighting.

**Change**: Replace the simple count with a time-weighted sum using exponential decay:
```sql
SELECT t.*, SUM(EXP(-EXTRACT(EPOCH FROM (NOW() - b.updated_at)) / (7 * 86400))) AS decay_score
FROM titles t
LEFT JOIN bookmarks b ON b.content_id = t.id
[WHERE t.age_rating IN :allowed]
GROUP BY t.id
HAVING COUNT(b.id) > 0
ORDER BY decay_score DESC
LIMIT :lim
```
The decay constant (7 days) means a bookmark from 7 days ago contributes ~37% of a fresh bookmark's weight. Falls back to all-time if no recent bookmarks exist (HAVING clause prevents empty results — if all decay to near-zero, the highest still wins).

### DD-07: Personalized Featured (R-11)

**Current state**: `get_featured_titles` (catalog_service.py:101-116) returns featured titles ordered by `created_at DESC`. No personalization.

**Change**: Add `get_personalized_featured_titles(db, profile_id, allowed_ratings)` in `recommendation_service.py`:
1. Compute profile centroid (reuse logic from `get_for_you_rail`)
2. If centroid exists: fetch featured titles with their embeddings, compute cosine similarity, sort by similarity DESC
3. If no centroid (new profile): fall back to default order (`created_at DESC`)
4. Update the catalog router's `/featured` endpoint to call the personalized version when `profile_id` is provided

### DD-08: Search N+1 Fix (S-01)

**Current state**: `semantic_search` (search_service.py:144-151) executes one genre query per result in a loop.

**Change**: After the main similarity query returns results, batch-fetch genres for all result IDs in a single query:
```sql
SELECT tg.title_id, g.name
FROM title_genres tg
JOIN genres g ON g.id = tg.genre_id
WHERE tg.title_id IN :title_ids
```
Build a `{title_id: [genre_names]}` mapping, then populate each result's `genres` field from the mapping.

### DD-09: EPG Click-to-Play (L-01)

**Current state**: `handleProgramClick` in EpgPage.tsx (line 78) is an empty stub. PlayerPage route exists at `/play/:type/:id` and already passes `isLive={type === 'live'}` to VideoPlayer.

**Change — Frontend (3 parts)**:

1. **EpgPage.tsx** — Implement `handleProgramClick`:
   - If program is currently airing: `navigate('/play/live/{channelId}', { state: { channel, currentProgram: entry } })`
   - If program is in the past or future: show a program detail modal/toast (simple info display)

2. **PlayerPage.tsx** — Add live TV type handler:
   - When `type === 'live'`: read channel/program from route state (or fetch via channel ID)
   - Set `manifestUrl` to `channel.hls_live_url`
   - Set `displayTitle` to current program's title + time slot
   - For Start Over: set `startPosition` to the offset from stream start corresponding to the program's EPG start time (requires knowing the DVR window start or using the program's `start_time` as a relative offset)
   - Track current time and update `displayTitle` when the on-air program changes (poll EPG or use program end_time as a timer)

3. **Start Over for live**: The existing "Start from beginning" button sets `startPosition = 0`. For live TV, Start Over needs to seek to the program's scheduled start time. The simplest approach: calculate the seconds elapsed since program start, seek backward by that amount from the live edge. This uses the existing Shaka Player `seekTo()` capability with a negative offset from live edge.

### DD-10: HNSW Index (A-06) — SKIP

**Research finding**: Migration 001 already creates an HNSW index on `content_embeddings.embedding` with `vector_cosine_ops` (m=16, ef_construction=64). The `<=>` cosine distance operator used in all recommendation queries matches this index. **No additional work needed.**

## Complexity Tracking

No constitution violations. No complexity tracking needed.
