# Data Model: Profile Viewing Time Limits

**Feature**: 006-viewing-time-limits
**Date**: 2026-02-13

## Entity Changes

### User (EXTEND existing `users` table)

**Current fields** (no changes to existing):
| Field | Type | Nullable | Notes |
|-------|------|----------|-------|
| id | UUID | No | Primary key |
| email | String(255) | No | Unique |
| password_hash | String(255) | No | bcrypt |
| subscription_tier | String(20) | No | Default "basic" |
| is_admin | Boolean | No | Default false |
| is_active | Boolean | No | Default true |
| created_at | DateTime(tz) | No | server_default now() |

**New fields**:
| Field | Type | Nullable | Default | Notes |
|-------|------|----------|---------|-------|
| pin_hash | String(255) | Yes | NULL | bcrypt hash of 4-digit PIN. NULL = no PIN set. |
| pin_failed_attempts | Integer | No | 0 | Reset on successful verify or lockout expiry |
| pin_lockout_until | DateTime(tz) | Yes | NULL | NULL = not locked out. Set to now+30min after 5 failures. |

### Title (EXTEND existing `titles` table)

**New fields**:
| Field | Type | Nullable | Default | Notes |
|-------|------|----------|---------|-------|
| is_educational | Boolean | No | false | Set by content provider metadata. Used for viewing time exemption. |

### ViewingTimeConfig (NEW table: `viewing_time_configs`)

Per-child-profile viewing time limit configuration. One row per child profile (created when limits are first configured or when a child profile is created with defaults).

| Field | Type | Nullable | Default | Notes |
|-------|------|----------|---------|-------|
| id | UUID | No | uuid4 | Primary key |
| profile_id | UUID FK→profiles.id | No | | CASCADE on delete. Unique (one config per profile). |
| weekday_limit_minutes | Integer | Yes | 120 | NULL = Unlimited. Range: 15–480 (15min to 8h) in 15-min increments. |
| weekend_limit_minutes | Integer | Yes | 180 | NULL = Unlimited. Same range. |
| reset_hour | Integer | No | 6 | 0–23. Hour of day (in profile timezone) when allowance resets. |
| educational_exempt | Boolean | No | true | If true, educational content doesn't count toward limit. |
| timezone | String(50) | No | "UTC" | IANA timezone for reset calculation (e.g., "Europe/Berlin"). |
| created_at | DateTime(tz) | No | now() | |
| updated_at | DateTime(tz) | No | now() | Auto-updated on change. |

**Constraints**:
| Constraint | Type | Columns | Notes |
|------------|------|---------|-------|
| uq_vtc_profile | UNIQUE | (profile_id) | One config per profile |
| ck_vtc_weekday_range | CHECK | weekday_limit_minutes | NULL OR (15 <= val <= 480 AND val % 15 = 0) |
| ck_vtc_weekend_range | CHECK | weekend_limit_minutes | NULL OR (15 <= val <= 480 AND val % 15 = 0) |
| ck_vtc_reset_hour | CHECK | reset_hour | 0 <= val <= 23 |

### ViewingTimeBalance (NEW table: `viewing_time_balances`)

Daily balance tracking. One row per profile per "viewing day" (defined by reset_hour). Upserted on each heartbeat.

| Field | Type | Nullable | Default | Notes |
|-------|------|----------|---------|-------|
| id | UUID | No | uuid4 | Primary key |
| profile_id | UUID FK→profiles.id | No | | CASCADE on delete |
| reset_date | Date | No | | The "viewing day" this balance covers (date when the day started at reset_hour) |
| used_seconds | Integer | No | 0 | Total seconds consumed today. Incremented by heartbeat. |
| educational_seconds | Integer | No | 0 | Total educational seconds (tracked but not counted toward limit). |
| is_unlimited_override | Boolean | No | false | Set to true when parent grants "Unlimited for today". Reset on next day. |
| updated_at | DateTime(tz) | No | now() | Last heartbeat time |

**Constraints**:
| Constraint | Type | Columns | Notes |
|------------|------|---------|-------|
| uq_vtb_profile_date | UNIQUE | (profile_id, reset_date) | One balance per profile per day |

**Indexes**:
| Index | Columns | Type | Notes |
|-------|---------|------|-------|
| ix_vtb_profile_date | (profile_id, reset_date) | UNIQUE B-tree | Primary lookup pattern |

### ViewingSession (NEW table: `viewing_sessions`)

Active and historical viewing sessions. Used for concurrent stream enforcement, pause detection, and viewing history.

| Field | Type | Nullable | Default | Notes |
|-------|------|----------|---------|-------|
| id | UUID | No | uuid4 | Primary key |
| profile_id | UUID FK→profiles.id | No | | CASCADE on delete |
| title_id | UUID FK→titles.id | No | | What is being watched |
| device_id | String(100) | No | | Client-generated device identifier |
| device_type | String(20) | Yes | | "tv", "mobile", "tablet", "web" |
| is_educational | Boolean | No | false | Cached from title at session start |
| started_at | DateTime(tz) | No | now() | |
| last_heartbeat_at | DateTime(tz) | No | now() | Updated on each heartbeat |
| ended_at | DateTime(tz) | Yes | NULL | NULL = active session. Set when terminated. |
| total_seconds | Integer | No | 0 | Accumulated viewing seconds for this session |
| paused_at | DateTime(tz) | Yes | NULL | Set when pause detected. Cleared on resume. |

**Indexes**:
| Index | Columns | Type | Notes |
|-------|---------|------|-------|
| ix_vs_profile_active | (profile_id) WHERE ended_at IS NULL | Partial B-tree | Find active session for concurrent stream check |
| ix_vs_profile_started | (profile_id, started_at DESC) | B-tree | Viewing history queries |

### TimeGrant (NEW table: `time_grants`)

Audit log of parent extra time grants. Append-only.

| Field | Type | Nullable | Default | Notes |
|-------|------|----------|---------|-------|
| id | UUID | No | uuid4 | Primary key |
| profile_id | UUID FK→profiles.id | No | | Child profile that received extra time |
| granted_by_user_id | UUID FK→users.id | No | | Parent account that authorized it |
| granted_minutes | Integer | Yes | | Minutes added. NULL = Unlimited for today. |
| is_remote | Boolean | No | false | True if granted from parent's own device |
| granted_at | DateTime(tz) | No | now() | |

## Relationships

```
User (1) ──→ (N) Profile (1) ──→ (0..1) ViewingTimeConfig
                          │
                          ├──→ (N) ViewingTimeBalance (one per day)
                          ├──→ (N) ViewingSession
                          └──→ (N) TimeGrant (as recipient)

User (1) ──→ (N) TimeGrant (as grantor, via granted_by_user_id)

Title (1) ──→ (N) ViewingSession (via title_id)
```

## State Derivation

### Viewing Day Calculation

```python
def get_viewing_day(now: datetime, reset_hour: int, timezone: str) -> date:
    """Compute which 'viewing day' the current moment belongs to."""
    local_now = now.astimezone(ZoneInfo(timezone))
    if local_now.hour < reset_hour:
        return (local_now - timedelta(days=1)).date()
    return local_now.date()
```

### Balance State

```
Has time:     used_seconds < limit_seconds AND NOT is_unlimited_override
Exhausted:    used_seconds >= limit_seconds AND NOT is_unlimited_override
Unlimited:    is_unlimited_override = true OR config limit is NULL
```

Where `limit_seconds` is computed from config:
- If today is Saturday or Sunday → `weekend_limit_minutes * 60`
- If today is Monday–Friday → `weekday_limit_minutes * 60`
- If limit is NULL → Unlimited

### Session State

```
Active:    ended_at IS NULL AND last_heartbeat_at >= (now - 5min)
Stale:     ended_at IS NULL AND last_heartbeat_at < (now - 5min)
Ended:     ended_at IS NOT NULL
Paused:    paused_at IS NOT NULL AND ended_at IS NULL
```

## Alembic Migration

Migration name: `003_add_viewing_time_limits`

Operations:
1. `ADD COLUMN users.pin_hash VARCHAR(255) DEFAULT NULL`
2. `ADD COLUMN users.pin_failed_attempts INTEGER NOT NULL DEFAULT 0`
3. `ADD COLUMN users.pin_lockout_until TIMESTAMP WITH TIME ZONE DEFAULT NULL`
4. `ADD COLUMN titles.is_educational BOOLEAN NOT NULL DEFAULT FALSE`
5. `CREATE TABLE viewing_time_configs` (with constraints and unique index)
6. `CREATE TABLE viewing_time_balances` (with unique index)
7. `CREATE TABLE viewing_sessions` (with partial index and composite index)
8. `CREATE TABLE time_grants`
