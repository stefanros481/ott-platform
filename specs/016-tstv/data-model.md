# Data Model: TSTV — Start Over & Catch-Up TV

**Feature Branch**: `016-tstv`
**Phase**: 1 — Design
**Date**: 2026-02-24

---

## Overview

TSTV extends four existing tables and adds three new tables. All changes are delivered via a single Alembic migration.

---

## Existing Tables — Column Additions

### `channels` (extend)

New columns added to the existing `channels` table:

| Column | Type | Default | Nullable | Purpose |
|--------|------|---------|----------|---------|
| `cdn_channel_key` | `VARCHAR(20)` | — | YES | Maps channel to segment directory (`ch1`, `ch2`, ..., `ch5`). NULL = not a TSTV channel. |
| `tstv_enabled` | `BOOLEAN` | `TRUE` | NO | Master switch. When FALSE, no start-over or catch-up is offered for this channel. |
| `startover_enabled` | `BOOLEAN` | `TRUE` | NO | Whether Start Over is available for this channel. |
| `catchup_enabled` | `BOOLEAN` | `TRUE` | NO | Whether Catch-Up is available for this channel. |
| `catchup_window_hours` | `INTEGER` | `168` | NO | Infrastructure retention — how long segments are kept on disk. Cleanup cron uses this value. Default: 7 days. |
| `cutv_window_hours` | `INTEGER` | `168` | NO | Viewer entitlement window — how long after broadcast a viewer may access catch-up. Enforced by the manifest endpoint. Options: 2, 6, 12, 24, 48, 72, 168. |

**Important distinction**: `catchup_window_hours` is infrastructure (when to delete segments); `cutv_window_hours` is the business rule (when to deny viewer access). Infrastructure always retains segments for the maximum window; the API enforces the viewer's entitlement window at request time.

**SQLAlchemy model addition** (`backend/app/models/epg.py`):
```python
cdn_channel_key: Mapped[str | None] = mapped_column(String(20), nullable=True)
tstv_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
startover_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
catchup_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
catchup_window_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=168)
cutv_window_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=168)
```

---

### `schedule_entries` (extend)

New columns added to the existing `schedule_entries` table:

| Column | Type | Default | Nullable | Purpose |
|--------|------|---------|----------|---------|
| `catchup_eligible` | `BOOLEAN` | `TRUE` | NO | Per-program catch-up eligibility. Overrides channel default when explicitly set to FALSE. |
| `startover_eligible` | `BOOLEAN` | `TRUE` | NO | Per-program start-over eligibility. Overrides channel default when explicitly set to FALSE. |
| `series_id` | `VARCHAR(100)` | NULL | YES | Links episodes of the same series for auto-play next episode. Matches on series_title + season_number if absent. |

**SQLAlchemy model addition** (`backend/app/models/epg.py`):
```python
catchup_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
startover_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
series_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
```

---

### `bookmarks` (modify constraint)

The unique constraint changes from `(profile_id, content_id)` to `(profile_id, content_id, content_type)`. This allows the same UUID to exist as both a VOD bookmark and a TSTV bookmark without collision.

New `content_type` values added (in addition to existing `'movie'`, `'episode'`):
- `'tstv_catchup'` — catch-up viewing bookmark; `content_id` = `schedule_entry.id`
- `'tstv_startover'` — start-over viewing bookmark; `content_id` = `schedule_entry.id`

**Conflict resolution**: For TSTV content types, `upsert_bookmark` uses `GREATEST(existing_position, new_position)` to implement furthest-position-wins semantics.

**Alembic migration change**:
```sql
-- Drop old constraint
ALTER TABLE bookmarks DROP CONSTRAINT uq_bookmark_profile_content;

-- Add new constraint including content_type
ALTER TABLE bookmarks ADD CONSTRAINT uq_bookmark_profile_content_type
    UNIQUE (profile_id, content_id, content_type);
```

---

## New Tables

### `tstv_sessions`

Tracks TSTV viewing sessions for analytics (maps to the `service_type = 'TSTV'` / `'Catch_up'` values already defined in `analytics_events`).

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| `id` | `SERIAL` | PK | — |
| `user_id` | `INTEGER` | FK → `users.id`, nullable | User who initiated the session |
| `profile_id` | `INTEGER` | FK → `profiles.id`, nullable | Active profile |
| `channel_id` | `VARCHAR(20)` | — | CDN channel key (e.g., `ch1`) |
| `schedule_entry_id` | `UUID` | FK → `schedule_entries.id` | Which program is being watched |
| `session_type` | `VARCHAR(20)` | CHECK IN ('startover', 'catchup') | Session mode |
| `started_at` | `TIMESTAMPTZ` | DEFAULT NOW() | Session start wall-clock time |
| `last_position_s` | `FLOAT` | DEFAULT 0 | Last known playback position in seconds |
| `completed` | `BOOLEAN` | DEFAULT FALSE | Whether viewer watched to the end |

**Indexes**: `(user_id, started_at)`, `(schedule_entry_id)` for analytics queries.

**SQLAlchemy model** (new file `backend/app/models/tstv.py`):
```python
class TSTVSession(Base):
    __tablename__ = "tstv_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    profile_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("profiles.id"), nullable=True)
    channel_id: Mapped[str] = mapped_column(String(20), nullable=False)
    schedule_entry_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("schedule_entries.id"), nullable=False)
    session_type: Mapped[str] = mapped_column(String(20), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_position_s: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
```

---

### `recordings` (PVR stub)

Metadata-only stub for Cloud PVR. No new storage or infrastructure required — segments already exist in the TSTV archive. A recording is a pointer to a time range; playback reuses the catch-up manifest generator.

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| `id` | `SERIAL` | PK | — |
| `user_id` | `UUID` | FK → `users.id` | Owner of the recording |
| `schedule_entry_id` | `UUID` | FK → `schedule_entries.id` | What was recorded |
| `channel_id` | `VARCHAR(20)` | — | CDN channel key |
| `requested_at` | `TIMESTAMPTZ` | DEFAULT NOW() | When the recording was requested |
| `status` | `VARCHAR(20)` | DEFAULT 'completed' | Recording status (stub: always 'completed') |

---

### `drm_keys`

Stores AES-128 encryption keys per channel for the ClearKey KMS.

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| `id` | `SERIAL` | PK | — |
| `key_id` | `UUID` | UNIQUE, NOT NULL | ClearKey KID (base64url in license response) |
| `key_value` | `BYTEA` | NOT NULL | 16-byte AES-128 key |
| `channel_id` | `UUID` | FK → `channels.id` | Which channel uses this key |
| `active` | `BOOLEAN` | DEFAULT TRUE | Active key for new segments; old keys remain for catch-up |
| `created_at` | `TIMESTAMPTZ` | DEFAULT NOW() | — |
| `rotated_at` | `TIMESTAMPTZ` | nullable | When this key was superseded |
| `expires_at` | `TIMESTAMPTZ` | nullable | Optional TTL for key validity |

**Key rotation**: When a key is rotated, the old key remains in the table (marked `active=FALSE`). The license server resolves keys by KID lookup — old catch-up content encrypted with the old key remains playable.

---

## Entity Relationships (summary)

```
channels (1) ──────────────── (N) schedule_entries
    │                                   │
    │ cdn_channel_key                    │ (defines program time window)
    │ tstv_enabled                       │
    │ cutv_window_hours                  │
    │                                    │
channels (1) ──── (N) drm_keys          │
                                         │
profiles (1) ─── (N) bookmarks ─────────┘
                  content_type ∈ {       (content_id = schedule_entry.id
                    'tstv_catchup',       for TSTV types)
                    'tstv_startover',
                    'movie', 'episode'}

users (1) ──── (N) tstv_sessions ──── (1) schedule_entries
users (1) ──── (N) recordings ──── (1) schedule_entries
```

---

## Migration: `007_tstv_schema.py`

Single Alembic migration covering all changes above:

1. Add columns to `channels`: `cdn_channel_key`, `tstv_enabled`, `startover_enabled`, `catchup_enabled`, `catchup_window_hours`, `cutv_window_hours`
2. Add columns to `schedule_entries`: `catchup_eligible`, `startover_eligible`, `series_id`
3. Drop constraint `uq_bookmark_profile_content`; add `uq_bookmark_profile_content_type` on `(profile_id, content_id, content_type)`
4. Create `tstv_sessions` table
5. Create `recordings` table
6. Create `drm_keys` table
7. Create indexes: `tstv_sessions(user_id, started_at)`, `tstv_sessions(schedule_entry_id)`, `drm_keys(channel_id, active)`, `channels(cdn_channel_key)`

---

## Seed Data Changes (`backend/app/seed_data.py`)

1. Assign `cdn_channel_key` to the 5 seeded channels: `ch1`–`ch5`
2. Set `tstv_enabled=True`, `startover_enabled=True`, `catchup_enabled=True` for all 5 channels
3. Set `cutv_window_hours` per channel based on PoC rights config (e.g., `168` for most, `48` for one sports channel)
4. Generate repeating schedule entries for the past 7 days + next 7 days, cycling program names aligned to each channel's video loop duration:
   - ch1 (Big Buck Bunny, 10 min): entries every 10 minutes
   - ch2 (10 min), ch3 (12 min), ch4 (11 min), ch5 (12 min): same pattern
5. Set `catchup_eligible=True` for all seeded schedule entries
6. Generate DRM keys for each channel via the KMS (or insert static test keys for seeding)
