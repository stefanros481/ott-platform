# Research: Continue Watching & Cross-Device Bookmarks

**Feature**: 004-continue-watching-bookmarks
**Date**: 2026-02-12

## R1: Bookmark Model Extension Strategy

**Decision**: Extend existing `Bookmark` model with a `dismissed_at` nullable timestamp field rather than a separate status enum.

**Rationale**: The existing Bookmark model already has `completed` (bool) and `updated_at` (timestamp). Adding `dismissed_at` (nullable datetime) is the simplest extension:
- `dismissed_at IS NULL AND completed = false` → active (show in Continue Watching)
- `dismissed_at IS NOT NULL` → manually dismissed (show in Paused)
- `completed = true` → finished (excluded from both rails)
- `updated_at < now() - 30 days AND dismissed_at IS NULL AND completed = false` → stale (auto-archive to Paused)

No need for a state machine or status enum — the combination of existing fields plus one new field covers all states.

**Alternatives considered**:
- Status enum (`active`, `paused`, `completed`, `dismissed`): More explicit but requires migrating existing boolean `completed` field. Over-engineered for PoC.
- Separate `PausedBookmark` table: Unnecessary data duplication. The "Paused" concept is a query filter, not a separate entity.

## R2: Heartbeat Interval and Client-Side Caching

**Decision**: Increase heartbeat from current 10s to 30s interval (spec minimum). Use `localStorage` for client-side bookmark cache with sync-on-reconnect.

**Rationale**: The current VideoPlayer sends position updates every 10 seconds via `onPositionUpdate`. The spec requires "at minimum every 30 seconds." 30s reduces backend load while still limiting worst-case data loss to 30 seconds of position. For the PoC, `localStorage` is sufficient for client-side caching (no IndexedDB complexity needed).

**Alternatives considered**:
- Keep 10s interval: Works but is more aggressive than needed for a PoC.
- IndexedDB for caching: Overkill — localStorage handles small JSON payloads fine.
- Service Worker for background sync: Out of scope for PoC.

## R3: Series Episode Advancement Logic

**Decision**: On episode completion, query the same series for the next episode by `(season_number, episode_number)` ordering. Use the existing `Season` → `Episode` hierarchy in the catalog model.

**Rationale**: The catalog model already has `Season.season_number` and `Episode.episode_number` with proper FK relationships. A SQL query joining `bookmarks → episodes → seasons → titles` can find the next unwatched episode. The existing `PlayerPage.tsx` already computes `nextEpisodeId` client-side — the backend service will mirror this for the Continue Watching rail display.

**Alternatives considered**:
- Client-side only advancement: Already partially done in PlayerPage, but the backend needs this for the Continue Watching rail to show "Up Next: S2E3" without the player being active.

## R4: AI Resumption Scoring Approach

**Decision**: Implement a simple scoring function in the recommendation service that combines recency, completion percentage, time-of-day affinity, and remaining duration. No ML model training for the PoC — use a weighted heuristic.

**Rationale**: The spec mentions "XGBoost model" in the user story reference, but for a PoC this is overengineered. A weighted scoring formula achieves the same demonstrable behavior:
- `recency_score`: Exponential decay based on days since last watch (weight: 0.3)
- `completion_score`: Higher score for titles with 20-80% completion (weight: 0.2)
- `time_affinity_score`: Short content boosted on mobile/morning, long on TV/evening (weight: 0.25)
- `series_momentum_score`: Bonus for series with recent consecutive episode watches (weight: 0.25)

This produces visibly different ordering than pure recency, satisfying the spec's behavioral requirements.

**Alternatives considered**:
- XGBoost model: Production-grade but requires training data pipeline, model serving. Deferred to production.
- Pure recency fallback only: Doesn't demonstrate AI-native capability (violates Constitution Principle III).

## R5: Context Signal Passing

**Decision**: Pass `device_type` and `hour_of_day` as query parameters on the Continue Watching API call. The BFF/client determines its own device type.

**Rationale**: The simplest approach — the frontend knows its own device type and local time. No need for user-agent parsing on the backend. The scoring function uses these directly.

**Alternatives considered**:
- User-agent parsing on backend: Fragile, doesn't work for all platforms.
- Separate context service: Over-engineered for PoC.

## R6: Continue Watching Rail Integration with Home Page

**Decision**: Create a dedicated `ContinueWatchingCard` component (distinct from `TitleCard`) that shows a progress bar overlay. Fetch Continue Watching data from a separate API call (not embedded in the recommendations home response).

**Rationale**: The existing `TitleCard` component doesn't support progress bars. The Continue Watching rail has unique UX (progress bar, dismiss action, "Up Next" for series) that warrants a dedicated card component. Separating the API call from `/recommendations/home` allows independent refresh (e.g., after dismissing an item) without reloading all home rails.

**Alternatives considered**:
- Extend TitleCard with optional progress bar: Adds complexity to a widely-used component for a single rail's needs.
- Keep Continue Watching embedded in home recommendations response: The existing `_continue_watching_rail` in recommendation_service already does this, but the response format lacks progress data. Separating gives more control.

## R7: Unique Constraint on Bookmarks

**Decision**: Add a unique constraint on `(profile_id, content_id)` to the Bookmark model. The existing model has a comment placeholder for this but no actual constraint.

**Rationale**: The existing code in `viewing.py` already upserts by `(profile_id, content_id)`, but without a DB constraint, concurrent requests could create duplicates. Adding the constraint ensures data integrity and enables `ON CONFLICT` upsert patterns.

**Alternatives considered**:
- Application-level dedup only: Current approach, but fragile under concurrent requests.
