# Data Model: Recommendations Quality, Watchlist Rail & Live TV Playback

**No new tables. No schema changes. No migrations.**

This feature exclusively uses existing models. All changes are service-layer logic.

## Existing Models Used

### Rating (`ratings` table)
| Field | Type | Notes |
|-------|------|-------|
| profile_id | UUID (PK, FK→profiles) | Composite PK with title_id |
| title_id | UUID (PK, FK→titles) | |
| rating | SmallInteger | -1 (thumbs down) or 1 (thumbs up) |
| created_at | DateTime(tz) | server_default=now() |

**Used by**: R-01 (exclude -1 from centroid + results), R-02 (2x weight for +1)

### WatchlistItem (`watchlist` table)
| Field | Type | Notes |
|-------|------|-------|
| profile_id | UUID (PK, FK→profiles) | Composite PK with title_id |
| title_id | UUID (PK, FK→titles) | |
| added_at | DateTime(tz) | server_default=now() |

**Used by**: R-03 (My List rail, ordered by added_at DESC)

### Bookmark (`bookmarks` table)
| Field | Type | Notes |
|-------|------|-------|
| id | UUID (PK) | |
| profile_id | UUID (FK→profiles) | |
| content_id | UUID (FK→titles or episodes) | |
| position_seconds | Integer | |
| duration_seconds | Integer | |
| completed | Boolean | |
| updated_at | DateTime(tz) | |

**Used by**: R-01 (bookmark IDs minus thumbs-down), R-06 (time-decay uses updated_at)

### Episode (`episodes` table)
| Field | Type | Notes |
|-------|------|-------|
| id | UUID (PK) | |
| season_id | UUID (FK→seasons) | |
| episode_number | Integer | Unique within season |
| title | String(500) | |
| synopsis | Text (nullable) | |
| duration_minutes | Integer (nullable) | |
| hls_manifest_url | String(500) (nullable) | |

**Used by**: R-04 (next episode lookup by episode_number + 1)

### Season (`seasons` table)
| Field | Type | Notes |
|-------|------|-------|
| id | UUID (PK) | |
| title_id | UUID (FK→titles) | |
| season_number | Integer | Unique within title |
| name | String(200) (nullable) | |
| synopsis | Text (nullable) | |

**Used by**: R-04 (cross-season next episode: season_number + 1, episode 1)

### Title (`titles` table)
| Field | Type | Notes |
|-------|------|-------|
| id | UUID (PK) | |
| title | String(500) | |
| is_featured | Boolean | Default false |
| ... | ... | Many other fields not relevant to this feature |

**Used by**: R-11 (filter by is_featured, personalize order)

### ContentEmbedding (`content_embeddings` table)
| Field | Type | Notes |
|-------|------|-------|
| title_id | UUID (PK, FK→titles) | |
| embedding | Vector(384) | HNSW indexed with vector_cosine_ops |
| model_version | String(50) | Default "all-MiniLM-L6-v2" |

**Used by**: R-01/R-02 (centroid computation), R-11 (featured title similarity), S-01 (semantic search)

### Channel (`channels` table — EPG)
| Field | Type | Notes |
|-------|------|-------|
| id | UUID (PK) | |
| channel_number | Integer | |
| name | String(200) | |
| hls_live_url | String(500) (nullable) | Live stream URL |
| ... | ... | |

**Used by**: L-01 (live TV playback URL)

### ScheduleEntry (`schedule_entries` table — EPG)
| Field | Type | Notes |
|-------|------|-------|
| id | UUID (PK) | |
| channel_id | UUID (FK→channels) | |
| title | String(500) | Program title |
| start_time | DateTime(tz) | |
| end_time | DateTime(tz) | |
| ... | ... | |

**Used by**: L-01 (current program display, Start Over time calculation)

## Key Query Patterns

### Thumbs-Down Exclusion Query (new)
```
Fetch: title_ids WHERE profile_id = :pid AND rating = -1
Purpose: Remove from centroid set + add to exclusion set
```

### Watchlist Rail Query (new)
```
Fetch: titles JOIN watchlist ON title_id
WHERE profile_id = :pid
ORDER BY added_at DESC
LIMIT 20
```

### Next Episode Query (new)
```
Fetch: episode WHERE season_id = :sid AND episode_number = :ep_num + 1
Fallback: first episode of season WHERE title_id = :tid AND season_number = :sn + 1
```

### Time-Decayed Trending Query (replaces existing)
```
Fetch: titles with SUM(EXP(-age_seconds / 604800)) as decay_score
ORDER BY decay_score DESC
```

### Genre Batch Query (replaces N+1)
```
Fetch: title_id, genre.name WHERE title_id IN :ids
Purpose: Single query replacing per-result loop
```
