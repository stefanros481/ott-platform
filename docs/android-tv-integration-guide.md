# Android TV Client — Backend Integration Guide

**Backend**: OTT Platform PoC (FastAPI 0.115+, Python 3.12)
**API Version**: v1
**Last Updated**: 2026-02-10

---

## Quick Start

```bash
# 1. Start the backend stack
docker compose -f docker/docker-compose.yml up -d

# 2. Verify backend is running
curl http://localhost:8000/health
# → {"status":"ok"}

# 3. Login with test credentials
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"demo@ott.test","password":"demo123"}'
# → {"access_token":"eyJ...","refresh_token":"...","token_type":"bearer"}

# 4. Use the token
curl http://localhost:8000/api/v1/auth/me \
  -H 'Authorization: Bearer <access_token>'
# → {"id":"...","email":"demo@ott.test","subscription_tier":"premium","is_admin":false}
```

**Interactive API docs**: http://localhost:8000/docs (Swagger UI)

---

## Connection Details

| Setting | Value |
|---------|-------|
| Base URL | `http://<backend-host>:8000/api/v1` |
| Protocol | HTTP (PoC — no TLS) |
| Content-Type | `application/json` |
| Health check | `GET /health` → `{"status": "ok"}` |
| Swagger UI | `http://<backend-host>:8000/docs` |

---

## Authentication

### Overview

| Property | Value |
|----------|-------|
| Scheme | JWT Bearer Token |
| Algorithm | HS256 |
| Access token expiry | 60 minutes |
| Refresh token expiry | 7 days |
| Token rotation | Yes (refresh returns new pair) |

### Test Credentials

| Email | Password | Tier | Admin | Profiles |
|-------|----------|------|-------|----------|
| `admin@ott.test` | `admin123` | premium | Yes | Admin, Kids |
| `demo@ott.test` | `demo123` | premium | No | Demo User |
| `basic@ott.test` | `test123` | basic | No | Basic User |
| `standard@ott.test` | `test123` | standard | No | Standard User, Family |
| `premium@ott.test` | `test123` | premium | No | Premium User, Partner, Kids |

### Auth Flow

```
┌─────────────┐     POST /auth/login          ┌─────────┐
│  Android TV  │ ──── {email, password} ─────→ │ Backend │
│    Client    │ ←── {access_token,            │         │
│              │      refresh_token} ────────  │         │
│              │                                │         │
│  Store tokens│     GET /any-endpoint          │         │
│  securely    │ ──── Authorization: Bearer ──→ │         │
│  (Encrypted  │ ←── 200 OK + data ──────────  │         │
│  SharedPrefs)│                                │         │
│              │     On 401 (token expired):    │         │
│              │     POST /auth/refresh         │         │
│              │ ──── {refresh_token} ────────→ │         │
│              │ ←── {new access_token,         │         │
│              │      new refresh_token} ─────  │         │
└─────────────┘                                └─────────┘
```

### JWT Payload Structure

```json
{
  "sub": "user-uuid-string",
  "is_admin": false,
  "iat": 1707500000,
  "exp": 1707503600
}
```

---

## API Endpoints

All authenticated endpoints require: `Authorization: Bearer <access_token>`

Error responses follow: `{"detail": "Human-readable message"}`

### Auth (`/api/v1/auth`)

#### `POST /register` — Create Account

**Auth**: None

```
Request:
{
  "email": string,          // max 255, validated format
  "password": string        // min 8, max 128
}

Response (201):
{
  "access_token": string,
  "refresh_token": string,
  "token_type": "bearer"
}

Errors:
  409 — "Email already registered"
```

A default profile named "Default" is automatically created on registration.

---

#### `POST /login` — Authenticate

**Auth**: None

```
Request:
{
  "email": string,
  "password": string
}

Response (200):
{
  "access_token": string,
  "refresh_token": string,
  "token_type": "bearer"
}

Errors:
  401 — "Invalid email or password"
```

---

#### `POST /refresh` — Refresh Tokens

**Auth**: None

```
Request:
{
  "refresh_token": string
}

Response (200):
{
  "access_token": string,    // new token
  "refresh_token": string,   // new token (rotation)
  "token_type": "bearer"
}

Errors:
  401 — "Invalid or expired refresh token"
```

Old refresh token is revoked after use. Always store the new pair.

---

#### `GET /me` — Current User

**Auth**: Required

```
Response (200):
{
  "id": "uuid",
  "email": "user@example.com",
  "subscription_tier": "basic" | "standard" | "premium",
  "is_admin": boolean
}
```

---

#### `GET /profiles` — List User Profiles

**Auth**: Required

```
Response (200):
[
  {
    "id": "uuid",
    "name": "Profile Name",
    "avatar_url": string | null,
    "parental_rating": "TV-Y" | "TV-Y7" | "TV-G" | "TV-PG" | "TV-14" | "TV-MA",
    "is_kids": boolean
  }
]
```

---

#### `POST /profiles` — Create Profile

**Auth**: Required

```
Request:
{
  "name": string,                    // min 1, max 100
  "avatar_url": string | null,
  "parental_rating": string,         // default: "TV-MA"
  "is_kids": boolean                 // default: false
}

Response (201): ProfileResponse
```

---

#### `PUT /profiles/{profile_id}/select` — Activate Profile

**Auth**: Required

```
Path: profile_id (UUID)

Response (200): ProfileResponse

Errors:
  404 — "Profile not found"
```

After selecting a profile, pass its `id` as `profile_id` query parameter to catalog, recommendation, viewing, and EPG endpoints.

---

### Catalog (`/api/v1/catalog`)

#### `GET /titles` — Browse & Search Catalog

**Auth**: Required

```
Query params:
  page: int         (default: 1, min: 1)
  page_size: int    (default: 20, min: 1, max: 100)
  genre: string     (optional — genre slug, e.g. "action")
  type: string      (optional — "movie" or "series")
  q: string         (optional — free-text search)
  profile_id: UUID  (optional — for parental filtering)

Response (200):
{
  "items": [TitleListItem],
  "total": int,
  "page": int,
  "page_size": int
}
```

**TitleListItem**:
```json
{
  "id": "uuid",
  "title": "Velocity",
  "title_type": "movie",
  "synopsis_short": "A disgraced F1 driver...",
  "release_year": 2024,
  "duration_minutes": 118,
  "age_rating": "TV-14",
  "poster_url": "https://...",
  "landscape_url": "https://...",
  "is_featured": false,
  "mood_tags": ["intense", "thrilling"],
  "genres": ["Action", "Thriller"]
}
```

---

#### `GET /titles/{title_id}` — Title Detail

**Auth**: Required

```
Path: title_id (UUID)
Query: profile_id (UUID, optional — for parental filtering)

Response (200): TitleDetail

Errors:
  404 — "Title not found"
  403 — "Content not available for this profile"
```

**TitleDetail** (extends TitleListItem):
```json
{
  "id": "uuid",
  "title": "Velocity",
  "title_type": "movie",
  "synopsis_short": "...",
  "synopsis_long": "Full plot description...",
  "release_year": 2024,
  "duration_minutes": 118,
  "age_rating": "TV-14",
  "country_of_origin": "US",
  "language": "en",
  "poster_url": "https://...",
  "landscape_url": "https://...",
  "logo_url": "https://...",
  "hls_manifest_url": "https://test-streams.mux.dev/...",
  "is_featured": true,
  "mood_tags": ["intense"],
  "theme_tags": ["redemption"],
  "ai_description": "AI-generated description...",
  "genres": ["Action", "Thriller"],
  "cast": [
    {
      "person_name": "Ethan Brooks",
      "role": "actor",
      "character_name": "Ben Archer"
    }
  ],
  "seasons": [
    {
      "id": "uuid",
      "season_number": 1,
      "name": "Season 1",
      "synopsis": "...",
      "episodes": [
        {
          "id": "uuid",
          "episode_number": 1,
          "title": "Pilot",
          "synopsis": "...",
          "duration_minutes": 45,
          "hls_manifest_url": "https://..."
        }
      ]
    }
  ]
}
```

For playback: use `hls_manifest_url` (movies) or `episodes[].hls_manifest_url` (series) with ExoPlayer/Media3.

---

#### `GET /genres` — All Genres

**Auth**: Required

```
Response (200):
[
  { "id": "uuid", "name": "Action", "slug": "action" },
  { "id": "uuid", "name": "Comedy", "slug": "comedy" }
]
```

---

#### `GET /featured` — Featured Titles (Hero Banner)

**Auth**: Required

```
Query: profile_id (UUID, optional)

Response (200): [TitleListItem]
```

---

#### `GET /search` — Search Titles

**Auth**: Required

```
Query:
  q: string         (required, min: 1)
  page: int         (default: 1)
  page_size: int    (default: 20, max: 100)
  profile_id: UUID  (optional)

Response (200): PaginatedResponse<TitleListItem>
```

---

### Recommendations (`/api/v1/recommendations`)

#### `GET /home` — Home Screen Rails

**Auth**: Required

```
Query: profile_id (UUID, required)

Response (200):
{
  "rails": [
    {
      "name": "Continue Watching",
      "rail_type": "continue_watching",
      "items": [ContentRailItem]
    },
    {
      "name": "For You",
      "rail_type": "for_you",
      "items": [ContentRailItem]
    },
    {
      "name": "New Releases",
      "rail_type": "new_releases",
      "items": [ContentRailItem]
    },
    {
      "name": "Trending",
      "rail_type": "trending",
      "items": [ContentRailItem]
    },
    {
      "name": "Top in Action",
      "rail_type": "genre",
      "items": [ContentRailItem]
    }
  ]
}
```

**ContentRailItem**:
```json
{
  "id": "uuid",
  "title": "Velocity",
  "title_type": "movie",
  "poster_url": "https://...",
  "landscape_url": "https://...",
  "synopsis_short": "...",
  "release_year": 2024,
  "age_rating": "TV-14",
  "similarity_score": null
}
```

Rails included depend on user viewing history. The genre rail appears when the user has enough history.

---

#### `GET /similar/{title_id}` — More Like This

**Auth**: Required

```
Path: title_id (UUID)
Query:
  limit: int         (default: 12, min: 1, max: 50)
  profile_id: UUID   (optional)

Response (200): [ContentRailItem]
```

Uses AI embedding similarity (pgvector) for content-based recommendations.

---

#### `GET /post-play/{title_id}` — Post-Play Suggestions

**Auth**: Required

```
Path: title_id (UUID)
Query:
  profile_id: UUID   (required)
  limit: int         (default: 8, min: 1, max: 20)

Response (200): [ContentRailItem]
```

---

### Viewing (`/api/v1/viewing`)

#### `GET /continue-watching` — Resume List

**Auth**: Required

```
Query: profile_id (UUID, required)

Response (200):
[
  {
    "id": "uuid",
    "content_type": "movie" | "episode",
    "content_id": "uuid",
    "position_seconds": 1234,
    "duration_seconds": 7080,
    "completed": false,
    "updated_at": "2026-02-10T12:00:00Z",
    "title_info": {
      "title": "Velocity",
      "poster_url": "https://..."
    }
  }
]
```

Returns incomplete bookmarks, most recent first.

---

#### `PUT /bookmarks` — Report Playback Position

**Auth**: Required

```
Query: profile_id (UUID, required)

Request:
{
  "content_type": "movie" | "episode",
  "content_id": "uuid",
  "position_seconds": 1234,
  "duration_seconds": 7080
}

Response (200): BookmarkResponse
```

- Call every 10-30 seconds during playback
- Upsert: creates or updates by `(profile_id, content_id)`
- Auto-marks `completed = true` when `position_seconds >= 95% of duration_seconds`

---

#### `GET /ratings/{title_id}` — Get Rating

**Auth**: Required

```
Path: title_id (UUID)
Query: profile_id (UUID, required)

Response (200):
{
  "title_id": "uuid",
  "rating": 1,              // 1 = thumbs up, -1 = thumbs down
  "created_at": "2026-02-10T12:00:00Z"
}

// Returns null if not yet rated
```

---

#### `POST /ratings` — Rate Title

**Auth**: Required

```
Query: profile_id (UUID, required)

Request:
{
  "title_id": "uuid",
  "rating": 1 | -1           // 1 = thumbs up, -1 = thumbs down
}

Response (200): RatingResponse
```

Upsert — updates existing rating if already rated.

---

#### `GET /watchlist` — Get Watchlist

**Auth**: Required

```
Query: profile_id (UUID, required)

Response (200):
[
  {
    "title_id": "uuid",
    "added_at": "2026-02-10T12:00:00Z",
    "title_info": {
      "id": "uuid",
      "title": "Velocity",
      "poster_url": "https://...",
      "landscape_url": "https://...",
      "title_type": "movie",
      "release_year": 2024,
      "age_rating": "TV-14"
    }
  }
]
```

---

#### `POST /watchlist/{title_id}` — Add to Watchlist

**Auth**: Required

```
Path: title_id (UUID)
Query: profile_id (UUID, required)

Response (201): {"detail": "Added to watchlist"}
```

Idempotent — adding the same title twice returns success.

---

#### `DELETE /watchlist/{title_id}` — Remove from Watchlist

**Auth**: Required

```
Path: title_id (UUID)
Query: profile_id (UUID, required)

Response (204): No Content
```

---

### EPG (`/api/v1/epg`)

#### `GET /channels` — Channel List

**Auth**: Required

```
Query: profile_id (UUID, optional — enables AI ordering + favorites)

Response (200):
[
  {
    "id": "uuid",
    "name": "Channel One",
    "channel_number": 1,
    "logo_url": "https://...",
    "genre": "Entertainment",
    "is_hd": true,
    "is_favorite": false,
    "hls_live_url": "https://..."
  }
]
```

When `profile_id` is provided, channels are sorted with favorites first (AI-personalized ordering).

For live playback: use `hls_live_url` with ExoPlayer.

---

#### `GET /schedule/{channel_id}` — Channel Schedule

**Auth**: Required

```
Path: channel_id (UUID)
Query: date (string, optional — format: YYYY-MM-DD, defaults to today)

Response (200):
[
  {
    "id": "uuid",
    "channel_id": "uuid",
    "title": "Evening News",
    "synopsis": "...",
    "genre": "News",
    "start_time": "2026-02-10T18:00:00Z",
    "end_time": "2026-02-10T19:00:00Z",
    "age_rating": "TV-PG",
    "is_new": true,
    "is_repeat": false,
    "series_title": null,
    "season_number": null,
    "episode_number": null
  }
]
```

---

#### `GET /now` — Now Playing (All Channels)

**Auth**: Required

```
Response (200):
[
  {
    "channel": ChannelResponse,
    "current_program": ScheduleEntryResponse,
    "next_program": ScheduleEntryResponse | null
  }
]
```

---

#### `GET /search` — Search Schedule

**Auth**: Required

```
Query: q (string, required, min: 1)

Response (200): [ScheduleEntryResponse]
```

Case-insensitive title search across all schedule entries.

---

#### `POST /favorites/{channel_id}` — Add Favorite Channel

**Auth**: Required

```
Path: channel_id (UUID)
Query: profile_id (UUID, required)

Response (204): No Content
```

---

#### `DELETE /favorites/{channel_id}` — Remove Favorite Channel

**Auth**: Required

```
Path: channel_id (UUID)
Query: profile_id (UUID, required)

Response (204): No Content
```

---

## Typical Workflows

### 1. App Launch → Home Screen

```
POST /auth/login {email, password}         → Store tokens
GET  /auth/profiles                        → Show profile picker
PUT  /auth/profiles/{id}/select            → Activate profile
GET  /recommendations/home?profile_id=...  → Render home rails
GET  /catalog/featured?profile_id=...      → Render hero banner
```

### 2. Browse → Play Content

```
GET  /catalog/genres                       → Populate genre filter
GET  /catalog/titles?genre=action&page=1   → Browse results
GET  /catalog/titles/{id}?profile_id=...   → Title detail page
     → Extract hls_manifest_url            → Initialize ExoPlayer
PUT  /viewing/bookmarks?profile_id=...     → Report position every 10-30s
GET  /recommendations/similar/{id}         → "More Like This" section
GET  /recommendations/post-play/{id}       → After playback ends
```

### 3. Live TV

```
GET  /epg/channels?profile_id=...          → Channel list (favorites first)
GET  /epg/now                              → Currently airing on all channels
     → Use channel.hls_live_url            → Initialize ExoPlayer for live
GET  /epg/schedule/{channel_id}?date=...   → Full schedule grid
POST /epg/favorites/{channel_id}           → Toggle favorite
```

### 4. Token Refresh

```
On any 401 response:
  POST /auth/refresh {refresh_token}       → New token pair
  Store new tokens
  Retry original request with new access_token

If refresh also returns 401:
  → Token expired or revoked
  → Redirect to login screen
```

---

## Error Handling

| Status | Meaning | When |
|--------|---------|------|
| 200 | Success | Normal response |
| 201 | Created | Registration, new profile, add to watchlist |
| 204 | No Content | Delete operations, favorites |
| 400 | Bad Request | Validation error (malformed request) |
| 401 | Unauthorized | Missing/expired/invalid token |
| 403 | Forbidden | Parental restriction, admin-only endpoint |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Email already registered |

All errors return: `{"detail": "Human-readable message"}`

---

## Android TV Implementation Notes

### ExoPlayer Setup

- Use **Media3 ExoPlayer** with `HlsMediaSource` for both VOD and live
- VOD manifest URLs: `TitleDetail.hls_manifest_url` or `EpisodeResponse.hls_manifest_url`
- Live manifest URLs: `ChannelResponse.hls_live_url`
- Manifest URLs point to public HLS test streams (PoC uses Mux test content)

### Token Storage

- Use `EncryptedSharedPreferences` for token storage
- Store both `access_token` and `refresh_token`
- Implement an OkHttp `Authenticator` for automatic token refresh on 401

### Profile Management

- After login, always fetch profiles and let the user select one
- Store the active `profile_id` — it's required by most endpoints as a query parameter
- `parental_rating` on profiles controls content visibility server-side

### Bookmark Reporting

- Report via `PUT /viewing/bookmarks` every 10-30 seconds during playback
- Include `content_type` ("movie" or "episode") and the content UUID
- Backend auto-marks completion at 95% — no client logic needed
- On next app launch, `GET /continue-watching` returns unfinished content

### Pagination

- Catalog browse returns paginated results: `{items, total, page, page_size}`
- Use `page` and `page_size` query params for Leanback paging
- Default page size is 20, max is 100
