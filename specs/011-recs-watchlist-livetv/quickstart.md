# Quickstart: Recommendations Quality, Watchlist Rail & Live TV Playback

## Prerequisites

```bash
docker compose up -d          # Start PostgreSQL, Redis, backend, frontends
docker compose exec backend alembic upgrade head   # Apply migrations (no new ones)
docker compose exec backend python -m app.seed     # Seed data (ratings, watchlist, EPG)
```

## What to Verify After Implementation

### 1. Thumbs-Down Exclusion (R-01)

```bash
# Create a profile with bookmarks + thumbs-down
# Via the client app: browse titles, start watching 5+, thumbs-down 2 of them
# Go to home screen → "For You" rail should NOT contain thumbs-downed titles
```

### 2. Thumbs-Up Weighting (R-02)

```bash
# Thumbs-up 3 Action titles, bookmark 3 Comedy titles (no rating)
# Home screen "For You" rail should lean toward Action over Comedy
```

### 3. My List Rail (R-03)

```bash
# Add 3+ titles to watchlist via title detail page
# Home screen should show "My List" rail after "Continue Watching", before "For You"
# Rail shows most recently added first
# Remove all watchlist items → "My List" rail disappears
```

### 4. Post-Play Next Episode (R-04)

```bash
# Start watching any episode (e.g., S1E3 of a series)
# Let it finish (or seek to near end)
# Post-play suggestions: first item should be S1E4
# If it's the last episode of a season: first item should be S2E1
```

### 5. Cold-Start "Popular Now" (R-05)

```bash
# Create a new profile (no viewing history)
# Home screen should show "Popular Now" rail (not empty "For You")
# Bookmark one title → next home load shows "For You" instead of "Popular Now"
```

### 6. Time-Decayed Trending (R-06)

```bash
# Check Trending rail — should reflect recently-watched titles
# Titles with many old bookmarks but no recent activity should rank lower
```

### 7. Personalized Featured (R-11)

```bash
# As a profile with Action viewing history:
#   GET /api/v1/catalog/featured?profile_id=<id>
#   Action featured titles should appear first
# As a new profile: featured titles in default order
```

### 8. Search N+1 Fix (S-01)

```bash
# Semantic search should return results with genres included
# Check backend logs: should see 2 queries (search + genre batch), not N+1
```

### 9. Live TV Playback (L-01)

```bash
# Navigate to EPG page
# Click on a currently-airing program → player page opens with live stream
# Player shows program title and time slot
# Click "Start Over" → playback seeks to program's scheduled start time
# Wait for program to end → displayed program info updates to next program
# Click a future program → shows program details (no playback)
```

## Key Files Modified

| File | Changes |
|------|---------|
| `backend/app/services/recommendation_service.py` | R-01, R-02, R-03, R-04, R-05, R-06, R-11 |
| `backend/app/services/search_service.py` | S-01 (N+1 fix) |
| `backend/app/services/catalog_service.py` | R-11 (personalized featured) |
| `backend/app/routers/catalog.py` | R-11 (featured endpoint update) |
| `frontend-client/src/pages/EpgPage.tsx` | L-01 (wire click handler) |
| `frontend-client/src/pages/PlayerPage.tsx` | L-01 (live TV type handler) |

## Testing

```bash
# Backend tests (when added)
docker compose exec backend python -m pytest tests/ -v

# Manual testing via client app at http://localhost:5173
```
