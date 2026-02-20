# Quickstart: Continue Watching & Cross-Device Bookmarks Validation

## Prerequisites

```bash
cd docker
docker compose up --build
```

Wait for all services to be healthy (~1-2 minutes). Seed data includes pre-created bookmarks across multiple profiles and states.

## 1. Backend API Validation

### Get auth token
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"demo@ott.test","password":"demo123"}' | jq -r .access_token)

PROFILE_ID=$(curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/users/me/profiles | jq -r '.[0].id')
```

### Continue Watching rail (AI-sorted)
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/viewing/continue-watching?profile_id=$PROFILE_ID&device_type=web&hour_of_day=20" \
  | jq '.[] | {id, content_type, progress_percent, resumption_score, title: .title_info.title, next_episode}'
```

Expected: Active bookmarks sorted by `resumption_score` (not purely by recency). Items with `completed=true`, `dismissed_at` set, or `updated_at` older than 30 days are excluded. Each item has `progress_percent` reflecting position/duration.

### Context-aware ordering (mobile vs TV)
```bash
# Mobile morning — short content should rank higher
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/viewing/continue-watching?profile_id=$PROFILE_ID&device_type=mobile&hour_of_day=8" \
  | jq '.[0:3] | .[] | {title: .title_info.title, resumption_score}'

# TV evening — long content should rank higher
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/viewing/continue-watching?profile_id=$PROFILE_ID&device_type=tv&hour_of_day=21" \
  | jq '.[0:3] | .[] | {title: .title_info.title, resumption_score}'
```

Expected: Different ordering between the two requests. Short-form content ranks higher on mobile/morning; long-form ranks higher on TV/evening.

### Bookmark heartbeat (upsert)
```bash
CONTENT_ID=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/viewing/continue-watching?profile_id=$PROFILE_ID" \
  | jq -r '.[0].content_id')

curl -s -X PUT -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  "http://localhost:8000/api/v1/viewing/bookmarks?profile_id=$PROFILE_ID" \
  -d "{\"content_type\":\"movie\",\"content_id\":\"$CONTENT_ID\",\"position_seconds\":2700,\"duration_seconds\":7200}" \
  | jq '{id, position_seconds, duration_seconds, completed, updated_at}'
```

Expected: Bookmark updated (upserted by profile_id + content_id). `completed` is false (2700/7200 = 37.5%, below 95% threshold).

### Auto-completion at 95%
```bash
curl -s -X PUT -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  "http://localhost:8000/api/v1/viewing/bookmarks?profile_id=$PROFILE_ID" \
  -d "{\"content_type\":\"movie\",\"content_id\":\"$CONTENT_ID\",\"position_seconds\":6900,\"duration_seconds\":7200}" \
  | jq '{id, position_seconds, completed}'
```

Expected: `completed: true` because 6900/7200 = 95.8% (exceeds 95% threshold). This bookmark disappears from the Continue Watching rail.

### Dismiss a bookmark
```bash
BOOKMARK_ID=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/viewing/continue-watching?profile_id=$PROFILE_ID" \
  | jq -r '.[0].id')

curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/viewing/bookmarks/$BOOKMARK_ID/dismiss?profile_id=$PROFILE_ID" \
  | jq '{id, dismissed_at, position_seconds}'
```

Expected: `dismissed_at` is set. Bookmark no longer appears in Continue Watching rail. Position is preserved.

### Paused section (dismissed + stale)
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/viewing/continue-watching/paused?profile_id=$PROFILE_ID" \
  | jq '.[] | {id, title: .title_info.title, dismissed_at, progress_percent}'
```

Expected: Shows both manually dismissed bookmarks (dismissed_at set) and stale bookmarks (updated_at > 30 days ago). Ordered by most recently dismissed/stale first.

### Restore a bookmark from Paused
```bash
PAUSED_ID=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/viewing/continue-watching/paused?profile_id=$PROFILE_ID" \
  | jq -r '.[0].id')

curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/viewing/bookmarks/$PAUSED_ID/restore?profile_id=$PROFILE_ID" \
  | jq '{id, dismissed_at, updated_at}'
```

Expected: `dismissed_at` is null, `updated_at` is now. Bookmark reappears in the active Continue Watching rail.

### Series next-episode metadata
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/viewing/continue-watching?profile_id=$PROFILE_ID" \
  | jq '.[] | select(.next_episode != null) | {title: .title_info.title, season: .title_info.season_number, episode: .title_info.episode_number, next: .next_episode}'
```

Expected: Series entries with a completed episode show `next_episode` with the next unwatched episode's season_number, episode_number, and episode_title.

## 2. Frontend Validation

1. Open http://localhost:5173 and log in as `demo@ott.test` / `demo123`
2. **Home screen** — verify Continue Watching rail appears with progress bars on each card
3. **Progress accuracy** — compare visible progress bars to known seed data positions
4. **Resume playback** — tap a Continue Watching item, verify playback starts from bookmarked position (not from beginning)
5. **Dismiss** — swipe or click dismiss on a Continue Watching card, verify it disappears from the rail
6. **Paused section** — tap "Paused" link from Continue Watching rail, verify dismissed and stale items appear
7. **Restore** — tap a Paused item to restore it, verify it reappears in Continue Watching
8. **Empty state** — if all items are dismissed/completed, verify the Continue Watching rail is hidden (not shown empty)
9. **Series next-episode** — for a series with a completed episode, verify the card shows "Up Next: S_E_"

## 3. Cross-Device Sync Validation

1. Open the app in two browser tabs (simulating two devices)
2. In Tab 1, play content and let the player run for 30+ seconds (one heartbeat cycle)
3. In Tab 2, refresh the home screen — verify the Continue Watching rail reflects the updated position from Tab 1
4. Position accuracy should be within 30 seconds (one heartbeat interval)

## 4. Fallback Validation

1. Continue Watching rail loads with AI-sorted ordering when recommendation service is available
2. If the AI scoring function fails or returns null scores, rail falls back to recency ordering (most recently watched first)
3. Frontend shows no error — items still display with progress bars, just in recency order
