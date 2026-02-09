# API Contract Changes: Parental Rating Enforcement

## Overview

All changes are additive — existing parameters remain, new `profile_id` query parameter is added to catalog endpoints that previously did not require it. Recommendation endpoints already accept `profile_id`.

## Changed Endpoints

### GET /catalog/titles

**Added parameter**: `profile_id` (UUID, required)

```
GET /catalog/titles?page=1&page_size=20&genre=action&profile_id={uuid}
```

**Behavior change**: Results are filtered to only include titles whose `age_rating` is at or below the profile's `parental_rating`. If the profile has `parental_rating: TV-MA`, no filtering is applied.

**Response**: Unchanged schema. `total` count reflects filtered results.

---

### GET /catalog/search

**Added parameter**: `profile_id` (UUID, required)

```
GET /catalog/search?q=thriller&profile_id={uuid}
```

**Behavior change**: Same filtering as /catalog/titles.

---

### GET /catalog/featured

**Added parameter**: `profile_id` (UUID, required)

```
GET /catalog/featured?profile_id={uuid}
```

**Behavior change**: Featured titles filtered by profile's parental_rating.

---

### GET /catalog/titles/{title_id}

**Added parameter**: `profile_id` (UUID, required)

```
GET /catalog/titles/{title_id}?profile_id={uuid}
```

**Behavior change**: Returns 403 Forbidden with body `{"detail": "Content not available for this profile"}` if the title's `age_rating` exceeds the profile's `parental_rating`.

**New error response**:
```json
{
  "detail": "Content not available for this profile"
}
```

---

### GET /recommendations/similar/{title_id}

**Added parameter**: `profile_id` (UUID, required — was not present)

```
GET /recommendations/similar/{title_id}?profile_id={uuid}
```

**Behavior change**: Similar titles filtered by profile's parental_rating.

---

### GET /recommendations/post-play/{title_id}

**Changed parameter**: `profile_id` (UUID, now required — was optional)

```
GET /recommendations/post-play/{title_id}?profile_id={uuid}
```

**Behavior change**: Post-play titles filtered by profile's parental_rating.

---

### GET /recommendations/home

**No parameter change** — already requires `profile_id`.

**Behavior change**: All rails (Continue Watching, For You, New Releases, Trending, Top Genre) are filtered by the profile's parental_rating.

## Unchanged Endpoints

- `GET /catalog/genres` — no filtering needed (genres don't have age ratings)
- `GET /auth/*` — no changes
- `GET /viewing/*` — no changes (bookmarks, ratings, watchlist are per-profile already)
- `POST /admin/*` — admin endpoints are exempt from parental filtering
