# Android TV Client — Backend Integration Guide

## Context

A separate Android TV client needs to connect to the existing OTT backend. This plan produces an API integration guide covering authentication flow and all available endpoints. No code changes are needed — the backend already supports external clients (CORS allows `localhost:5174`, and native Android apps using OkHttp/Retrofit are not subject to browser CORS at all).

## Deliverable

Create `docs/android-tv-integration-guide.md` — a standalone reference for the Android TV team.

## Files to Create

| File | Purpose |
|------|---------|
| `docs/android-tv-integration-guide.md` | Complete API reference with auth flow, all endpoints, schemas, and workflows |

## Content Outline

### 1. Connection Details

- **Base URL**: `http://<backend-host>:8000/api/v1`
- **Swagger UI**: `http://<backend-host>:8000/docs` (auto-generated, interactive)
- **Health check**: `GET /health` → `{"status": "ok"}`

### 2. Authentication

**JWT Bearer tokens** — HS256, 60-min access / 7-day refresh, token rotation on refresh.

**Flow**:
1. `POST /api/v1/auth/login` with `{email, password}` → `{access_token, refresh_token}`
2. All subsequent requests: `Authorization: Bearer <access_token>`
3. On 401: `POST /api/v1/auth/refresh` with `{refresh_token}` → new token pair
4. Store tokens in `EncryptedSharedPreferences` on Android

**Test credentials**: `admin@ott.test / admin123` (premium+admin), `demo@ott.test / demo123` (premium), `basic@ott.test / test123`, `standard@ott.test / test123`

### 3. All Endpoints (43 total)

**Auth** (prefix: `/auth`) — 6 endpoints
- `POST /register` — Create account (public)
- `POST /login` — Authenticate (public)
- `POST /refresh` — Refresh tokens (public)
- `GET /me` — Current user info
- `GET /profiles` — List profiles
- `POST /profiles` — Create profile
- `PUT /profiles/{id}/select` — Activate profile

**Catalog** (prefix: `/catalog`) — 5 endpoints
- `GET /titles` — Browse/search with pagination, genre/type filters, parental filtering
- `GET /titles/{id}` — Full detail (cast, seasons, episodes, HLS manifest URL)
- `GET /genres` — All genres
- `GET /featured` — Hero banner titles
- `GET /search?q=` — Search titles

**Recommendations** (prefix: `/recommendations`) — 3 endpoints
- `GET /home?profile_id=` — Home screen rails (Continue Watching, For You, New, Trending, genre)
- `GET /similar/{title_id}` — "More like this" (embedding similarity)
- `GET /post-play/{title_id}` — Post-play suggestions

**Viewing** (prefix: `/viewing`) — 7 endpoints
- `GET /continue-watching?profile_id=` — Resume list
- `PUT /bookmarks?profile_id=` — Report playback position (upsert, marks complete at 95%)
- `GET /ratings/{title_id}?profile_id=` — Get user rating
- `POST /ratings?profile_id=` — Rate title (thumbs up=1, down=-1)
- `GET /watchlist?profile_id=` — Watchlist with title info
- `POST /watchlist/{title_id}?profile_id=` — Add to watchlist
- `DELETE /watchlist/{title_id}?profile_id=` — Remove from watchlist

**EPG** (prefix: `/epg`) — 6 endpoints
- `GET /channels?profile_id=` — Channel list (AI-ordered with favorites)
- `GET /schedule/{channel_id}?date=` — Day schedule
- `GET /now` — Now playing on all channels
- `GET /search?q=` — Search schedule entries
- `POST /favorites/{channel_id}?profile_id=` — Add favorite channel
- `DELETE /favorites/{channel_id}?profile_id=` — Remove favorite channel

**Admin** (prefix: `/admin`) — 17 endpoints (requires `is_admin=true`)
- Stats, Titles CRUD, Users list, Channels CRUD, Schedule CRUD, Embedding generation

### 4. Key Schemas

Document all request/response Pydantic models:
- `TokenResponse`, `UserResponse`, `ProfileResponse`
- `TitleListItem`, `TitleDetail` (with cast, seasons, episodes)
- `ContentRail`, `ContentRailItem`, `HomeResponse`
- `BookmarkResponse`, `BookmarkUpdate`
- `ChannelResponse`, `ScheduleEntryResponse`, `NowPlayingResponse`
- `RatingResponse`, `WatchlistItemResponse`
- `PaginatedResponse<T>` (items, total, page, page_size)

### 5. Android TV Workflows

Document the typical user journeys:
1. **App launch** → Login → Profile select → Home screen rails
2. **Browse** → Catalog search/filter → Title detail → Play
3. **Playback** → Get manifest URL → ExoPlayer → Report bookmarks every 10s
4. **Live TV** → Channel list → Now playing → Schedule grid
5. **Token lifecycle** → Access token expires → Refresh → Retry

### 6. Error Handling

Standard HTTP codes with `{"detail": "message"}` body:
- 400 (validation), 401 (auth), 403 (forbidden/parental), 404 (not found), 409 (conflict)

### 7. Notes for Android TV

- **Player**: Use ExoPlayer/Media3 with HLS manifest URLs from `TitleDetail.hls_manifest_url` or `ChannelResponse.hls_live_url`
- **Profile ID**: Most endpoints require `profile_id` as a query parameter — persist the active profile after selection
- **Parental filtering**: Pass `profile_id` to catalog/recommendation endpoints; backend enforces rating limits
- **Bookmarks**: Report position via `PUT /viewing/bookmarks` every 10-30 seconds during playback; completion auto-detected at 95%
- **Pagination**: Catalog endpoints return `PaginatedResponse` — use `page` and `page_size` params

## Verification

1. Run `docker compose -f docker/docker-compose.yml up -d` to start the stack
2. Open `http://localhost:8000/docs` to verify Swagger UI loads with all endpoints
3. Test login: `curl -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{"email":"demo@ott.test","password":"demo123"}'`
4. Test authenticated request: `curl http://localhost:8000/api/v1/auth/me -H 'Authorization: Bearer <token>'`
5. Verify the generated guide covers all endpoints listed in Swagger
