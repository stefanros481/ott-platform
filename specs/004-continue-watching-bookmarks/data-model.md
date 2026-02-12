# Data Model: Continue Watching & Cross-Device Bookmarks

**Feature**: 004-continue-watching-bookmarks
**Date**: 2026-02-12

## Entity Changes

### Bookmark (EXTEND existing `bookmarks` table)

**Current fields** (no changes):
| Field | Type | Nullable | Notes |
|-------|------|----------|-------|
| id | UUID | No | Primary key |
| profile_id | UUID FK→profiles.id | No | CASCADE on delete |
| content_type | String(20) | No | 'movie' or 'episode' |
| content_id | UUID | No | References titles.id or episodes.id |
| position_seconds | Integer | No | Default 0 |
| duration_seconds | Integer | No | Total content duration |
| completed | Boolean | No | Default false |
| updated_at | DateTime(tz) | No | Auto-updated on change |

**New fields**:
| Field | Type | Nullable | Default | Notes |
|-------|------|----------|---------|-------|
| dismissed_at | DateTime(tz) | Yes | NULL | Set when manually dismissed; NULL = active |

**New constraint**:
| Constraint | Type | Columns | Notes |
|------------|------|---------|-------|
| uq_bookmark_profile_content | UNIQUE | (profile_id, content_id) | Prevents duplicate bookmarks; enables upsert |

### State Derivation (no new table — computed from existing fields)

```
Active:     completed = false AND dismissed_at IS NULL AND updated_at >= (now - 30 days)
Stale:      completed = false AND dismissed_at IS NULL AND updated_at < (now - 30 days)
Dismissed:  completed = false AND dismissed_at IS NOT NULL
Completed:  completed = true
```

- **Active** → shown in Continue Watching rail
- **Stale** → shown in Paused section (auto-archived)
- **Dismissed** → shown in Paused section (manually archived)
- **Completed** → excluded from both rails

### Alembic Migration

Migration name: `add_bookmark_dismissed_at_and_unique_constraint`

Operations:
1. `ADD COLUMN dismissed_at TIMESTAMP WITH TIME ZONE DEFAULT NULL`
2. `ADD CONSTRAINT uq_bookmark_profile_content UNIQUE (profile_id, content_id)`
   - Note: must first deduplicate any existing duplicate bookmarks before adding constraint

## Relationships

```
User (1) ──→ (N) Profile (1) ──→ (N) Bookmark
                                       │
                                       ├── content_type = 'movie' → Title
                                       └── content_type = 'episode' → Episode ──→ Season ──→ Title
```

No new relationships. Bookmark already references Profile via FK. Content resolution (movie vs episode) remains application-level via `content_type` discriminator.

## Series Episode Resolution

For series advancement (FR-006), the Continue Watching service resolves the "next episode" by:

1. From `content_id` (episode), join to `episodes.season_id` → `seasons.title_id`
2. Query all episodes for that title ordered by `(season_number, episode_number)`
3. Find the first episode after the completed one that has no completed bookmark for this profile

This is a read-time computation, not stored. The Continue Watching response includes `next_episode` metadata when applicable.

## Seed Data Requirements

New seed script `seed_bookmarks.py` creates demo bookmarks:

| Profile | Content | Position | State | Purpose |
|---------|---------|----------|-------|---------|
| Adult profile | Movie A | 45 min / 120 min | Active (recent) | Shows progress bar at 37% |
| Adult profile | Series B, S1E3 | 18 min / 22 min | Active (recent) | Shows near-completion, next-ep advance |
| Adult profile | Movie C | 30 min / 90 min | Active (2 days ago) | Mid-progress, lower recency |
| Adult profile | Documentary D | 10 min / 60 min | Stale (35 days ago) | Appears in Paused section |
| Adult profile | Movie E | 5 min / 100 min | Dismissed | Appears in Paused section |
| Adult profile | Movie F | 95 min / 100 min | Completed | Excluded from both rails |
| Kids profile | Kids Movie G | 20 min / 75 min | Active | Shows parental filtering works |
