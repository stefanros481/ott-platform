# Quickstart: TSTV — Start Over & Catch-Up TV

**Feature Branch**: `016-tstv`
**Stack**: Python 3.12 + FastAPI, PostgreSQL 16, React 18, Docker Compose, Shaka Player 4.12

---

## Overview

TSTV requires three new runtime components beyond the existing stack:

1. **SimLive Manager** — FFmpeg subprocesses that loop a source video while writing fMP4 segments to a shared volume
2. **CDN (nginx)** — Serves HLS segments directly from the `hls_data` volume
3. **KMS** — ClearKey key management endpoints in the backend

Everything runs inside the existing Docker Compose setup. No new external services.

---

## Prerequisites

- Docker + Docker Compose installed
- The existing stack (`docker compose up`) has been run at least once before
- `ffmpeg` is already installed in the backend Docker image (see `backend/Dockerfile` line 6)

---

## Step 1: Download Source Videos

SimLive needs `.mp4` source files to loop as simulated live streams. The filenames must match the `cdn_channel_key` values set on channels in the database (`ch1`–`ch5`).

Place them in `backend/hls_sources/` on the host (this directory is bind-mounted read-only into the backend container):

```bash
mkdir -p backend/hls_sources

# Download Big Buck Bunny (~10 min, H.264, small file)
curl -L -o backend/hls_sources/ch1.mp4 \
  "https://download.blender.org/peach/bigbuckbunny_movies/BigBuckBunny_320x180.mp4"

# Reuse for the other channels (or download different videos for variety)
cp backend/hls_sources/ch1.mp4 backend/hls_sources/ch2.mp4
cp backend/hls_sources/ch1.mp4 backend/hls_sources/ch3.mp4
cp backend/hls_sources/ch1.mp4 backend/hls_sources/ch4.mp4
cp backend/hls_sources/ch1.mp4 backend/hls_sources/ch5.mp4
```

Other free test videos (all Blender Foundation, CC-licensed):

| Video | URL | Duration |
|-------|-----|----------|
| Big Buck Bunny | `https://download.blender.org/peach/bigbuckbunny_movies/BigBuckBunny_320x180.mp4` | ~10 min |
| Sintel (trailer) | `https://download.blender.org/durian/trailer/sintel_trailer-480p.mp4` | ~1 min |
| Tears of Steel | `https://download.blender.org/demo/movies/ToS/ToS-4k-1920.mov` | ~12 min |
| Elephant's Dream | `https://download.blender.org/ED/ED_HD.avi` | ~11 min |

Resulting layout:

```
backend/hls_sources/
├── ch1.mp4
├── ch2.mp4
├── ch3.mp4
├── ch4.mp4
└── ch5.mp4
```

Videos must be fMP4-compatible (H.264 baseline for broad compatibility, or H.265).

---

## Step 2: Start the Stack

The Docker Compose file at `docker/docker-compose.yml` already includes all TSTV infrastructure:

- **Backend**: `HLS_SEGMENT_DIR`, `HLS_SOURCES_DIR`, `HLS_SEGMENT_DURATION`, `CDN_BASE_URL`, `DRM_ENABLED` env vars, `hls_data` volume mount, and `hls_sources` bind-mount
- **CDN (nginx)**: Serves segments from the shared `hls_data` volume on port 8081, with CORS headers and proper MIME types (see `nginx/cdn.conf`)
- **FFmpeg**: Already installed in the backend Dockerfile (`backend/Dockerfile` line 6)

Set the required JWT secret and start:

```bash
cd docker
export JWT_SECRET="change-me-to-at-least-32-characters-long"
docker compose up --build -d
```

The backend CMD automatically runs `alembic upgrade head` on startup, which applies migration `007_tstv_schema.py`:

- Adds TSTV columns to `channels` and `schedule_entries`
- Drops `uq_bookmark_profile_content`, adds `uq_bookmark_profile_content_type`
- Creates `tstv_sessions`, `recordings`, `drm_keys` tables

After migrations, the seed script runs automatically (`uv run python -m app.seed.run_seeds`), which includes TSTV seeding (step 9/9):

- Sets `cdn_channel_key` = `ch1`–`ch5` on the 5 seeded channels
- Enables TSTV, start-over, and catch-up on all channels
- Inserts active DRM keys into `drm_keys` for each channel

**If the stack is already running** and you just need to pick up new code:

```bash
cd docker
docker compose up -d
```

The backend has `--reload` enabled and the app source is bind-mounted (`../backend/app:/app/app`), so Python changes are picked up automatically. Frontend source dirs are also bind-mounted, so TSX changes are live via Vite HMR.

**Only rebuild** (`--build`) if:
- Backend Python dependencies changed in `pyproject.toml` / `uv.lock`
- The Dockerfile itself changed
- You want a clean slate

---

## Step 3: Verify the Migration and Seed Data

```bash
# Check TSTV columns on channels
docker compose exec postgres psql -U ott_user -d ott_platform \
  -c "\d channels" | grep tstv
# Should show: tstv_enabled, startover_enabled, catchup_enabled, ...

# Check channel keys and TSTV flags
docker compose exec postgres psql -U ott_user -d ott_platform \
  -c "SELECT name, cdn_channel_key, tstv_enabled FROM channels;"

# Check DRM keys were seeded
docker compose exec postgres psql -U ott_user -d ott_platform \
  -c "SELECT channel_id, active, key_id FROM drm_keys;"
```

---

## Step 4: Start SimLive Streaming

Use the admin panel or call the API directly to start FFmpeg for each channel:

```bash
# Start all channels via the admin API
for key in ch1 ch2 ch3 ch4 ch5; do
  curl -X POST http://localhost:8000/api/v1/admin/simlive/${key}/start \
    -H "Authorization: Bearer <admin_jwt>"
done
```

Or use the Admin UI at `http://localhost:5174` → **Streaming** page → click Start on each channel.

Verify segments are being written:

```bash
docker compose exec backend ls /hls_data/ch1/ | head -5
# ch1-init.mp4
# ch1-20260225143000.m4s
# ch1-20260225143006.m4s
# ...
```

---

## Step 5: Verify TSTV Endpoints

**List TSTV channels:**
```bash
curl http://localhost:8000/api/v1/tstv/channels \
  -H "Authorization: Bearer <viewer_jwt>"
```

**Check start-over availability for a channel:**
```bash
curl "http://localhost:8000/api/v1/tstv/startover/<channel_uuid>" \
  -H "Authorization: Bearer <viewer_jwt>"
```

**Get start-over manifest:**
```bash
curl "http://localhost:8000/api/v1/tstv/startover/<channel_uuid>/manifest?schedule_entry_id=<uuid>" \
  -H "Authorization: Bearer <viewer_jwt>"
```

**List catch-up programs:**
```bash
curl "http://localhost:8000/api/v1/tstv/catchup/<channel_uuid>" \
  -H "Authorization: Bearer <viewer_jwt>"
```

**Browse catch-up by date (cross-channel):**
```bash
curl "http://localhost:8000/api/v1/tstv/catchup?date=2026-02-24" \
  -H "Authorization: Bearer <viewer_jwt>"
```

---

## Step 6: Test Playback in the Browser

1. Open the frontend client: `http://localhost:5173`
2. Navigate to the **EPG** page — past programs should show a **Catch-Up** badge
3. Click a past program → player loads catch-up VOD manifest from the backend
4. Navigate to a live channel that started recently → toast: **"Resuming from 08:42 — Start from beginning?"**
5. Click **Start from beginning** → player loads start-over EVENT manifest
6. Open the **Catch-Up** page from the navbar → browse by channel or by date

---

## Services and Ports

| Service | URL | Purpose |
|---------|-----|---------|
| Backend API | `http://localhost:8000` | FastAPI — all TSTV/DRM/admin endpoints |
| Frontend Client | `http://localhost:5173` | Viewer app (React + Shaka Player) |
| Frontend Admin | `http://localhost:5174` | Admin panel (SimLive controls, TSTV rules) |
| CDN (nginx) | `http://localhost:8081` | Serves HLS segments from `hls_data` volume |
| PostgreSQL | `localhost:5432` | Database (user: `ott_user`, db: `ott_platform`) |
| Redis | `localhost:6379` | Cache/sessions |

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `JWT_SECRET` | *(required)* | JWT signing secret (min 32 chars) |
| `HLS_SEGMENT_DIR` | `/hls_data` | Root dir for all channel segment subdirectories |
| `HLS_SOURCES_DIR` | `/hls_sources` | Location of source `.mp4` files |
| `HLS_SEGMENT_DURATION` | `6` | Target segment duration in seconds |
| `CDN_BASE_URL` | `http://cdn/hls` | Base URL the manifest generator uses for segment URLs |
| `DRM_ENABLED` | `true` | Set to `false` to disable ClearKey encryption (dev only) |

---

## Troubleshooting

### FFmpeg process dies immediately
- Check the backend logs: `docker compose logs backend | grep ffmpeg`
- Ensure the source video exists: `docker compose exec backend ls /hls_sources/`
- Ensure `ffmpeg` is installed: `docker compose exec backend ffmpeg -version`

### No segments appearing in `/hls_data`
- Confirm the `hls_data` volume is mounted: `docker compose exec backend ls /hls_data/`
- Confirm SimLive was started: check admin panel or `GET /api/v1/admin/simlive/status`

### Manifest returns 403 on catch-up
- The CUTV window may have expired: check `channel.cutv_window_hours`
- The program may not be eligible: check `schedule_entry.catchup_eligible`
- The catch-up window expired: response includes `X-Expires-At` header

### Player fails DRM key fetch
- Confirm `drm_keys` table has an active key for the channel
- Check that the `#EXT-X-KEY` URI in the manifest points to the correct `/api/v1/drm/license` URL
- Verify the viewer JWT includes a valid subscription claim

### Admin panel shows no channels in SimLive view
- Confirm `cdn_channel_key` is set on channels: `SELECT cdn_channel_key FROM channels;`
- Confirm the seed data has been applied (check backend startup logs for seed output)

### Backend won't start / import errors
- Check logs: `docker compose logs backend`
- Verify migration ran: `docker compose exec backend uv run alembic current`
- Force rebuild: `docker compose up --build -d backend`

---

## Architecture Quick Reference

```
Browser (Shaka Player)
  |
  +-- Manifest request --> GET /api/v1/tstv/startover/{id}/manifest
  |                          (FastAPI assembles HLS playlist from filesystem)
  |
  +-- Segment fetch    --> GET http://localhost:8081/hls/ch1/ch1-20260225143000.m4s
  |                          (nginx serves directly from hls_data volume)
  |
  +-- DRM license      --> POST /api/v1/drm/license
                             (FastAPI validates JWT + returns ClearKey JSON)

Admin Panel (http://localhost:5174)
  +-- SimLive controls --> POST /api/v1/admin/simlive/{key}/start|stop|restart
  |                          (FastAPI manages FFmpeg subprocess PIDs)
  +-- TSTV rules       --> GET/PUT /api/v1/admin/tstv/rules
                             (Toggle TSTV/start-over/catch-up per channel)

FFmpeg (subprocess inside backend container)
  +-- Writes: /hls_data/ch1/ch1-YYYYMMDDHHmmSS.m4s
              /hls_data/ch1/ch1-init.mp4

Background Tasks (asyncio loops in backend lifespan)
  +-- Hourly: check_expiring_catchup (notify users of expiring bookmarks)
  +-- Hourly: cleanup_all (delete segments older than 168h)
```
