# Data Model: Subscription Tiers, Entitlements & TVOD

**Branch**: `012-entitlements-tvod` | **Date**: 2026-02-17

---

## New Tables

### `title_offers`

Transactional access options for individual titles. At most one active offer per type per title (enforced in service layer).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, default uuid4 | Primary key |
| `title_id` | UUID | FK → `titles.id` ON DELETE CASCADE, NOT NULL | The title this offer applies to |
| `offer_type` | VARCHAR(10) | NOT NULL, CHECK IN ('rent','buy','free') | Type of offer |
| `price_cents` | INTEGER | NOT NULL, default 0 | Price in smallest currency unit (0 for free) |
| `currency` | VARCHAR(3) | NOT NULL, default 'USD' | ISO 4217 currency code |
| `rental_window_hours` | INTEGER | NULL (required when offer_type='rent') | Duration of rental access |
| `is_active` | BOOLEAN | NOT NULL, default TRUE | Whether this offer is currently active |
| `created_at` | TIMESTAMPTZ | NOT NULL, server_default now() | Creation timestamp |

**Unique constraint**: `(title_id, offer_type)` WHERE `is_active = TRUE` — enforces one active offer per type per title.

**Index**: `(title_id, is_active)` for catalog access options lookup.

---

### `viewing_sessions`

Tracks active playback sessions for concurrent stream limit enforcement. Sessions are considered abandoned if no heartbeat is received for 5 minutes.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, default uuid4 | Primary key |
| `user_id` | UUID | FK → `users.id` ON DELETE CASCADE, NOT NULL | Owning user |
| `title_id` | UUID | FK → `titles.id` ON DELETE SET NULL | VOD title being played (nullable for live TV) |
| `content_type` | VARCHAR(20) | NOT NULL, default 'vod_title' | 'vod_title' or 'live_channel' |
| `started_at` | TIMESTAMPTZ | NOT NULL, server_default now() | Session start time |
| `last_heartbeat_at` | TIMESTAMPTZ | NOT NULL, server_default now() | Last activity signal received |
| `ended_at` | TIMESTAMPTZ | NULL | Set when session terminates; NULL = active |

**Index**: `(user_id, ended_at)` for counting active sessions per user.

---

## Modified Tables

### `user_entitlements` — Extended for TVOD

Existing table extended to support both SVOD (package-level) and TVOD (title-level) entitlements. The `source_type` discriminator indicates which path granted access.

**Changes from current schema:**
- `package_id` → becomes NULLABLE (was NOT NULL)
- New column `title_id` → nullable FK to `titles.id`
- Service enforces: exactly one of {`package_id`, `title_id`} must be non-null

| Column | Type | Change | Description |
|--------|------|--------|-------------|
| `id` | UUID | unchanged | Primary key |
| `user_id` | UUID | unchanged | FK → `users.id` |
| `package_id` | UUID | **NULLABLE now** | FK → `content_packages.id`; set for SVOD entitlements |
| `title_id` | UUID | **NEW** nullable | FK → `titles.id`; set for TVOD entitlements |
| `source_type` | VARCHAR(20) | unchanged | `'subscription'` (SVOD) or `'tvod'` (rent/buy) |
| `granted_at` | TIMESTAMPTZ | unchanged | When entitlement was created |
| `expires_at` | TIMESTAMPTZ | unchanged | NULL = permanent (buy); set for rentals |

**New index**: `(user_id, title_id, expires_at)` for fast TVOD access checks.

**Access check logic**:
```
User can access title T if ANY of:
  1. SVOD: UserEntitlement(source_type='subscription', package_id IN packages_containing_T, expires_at IS NULL OR > now())
  2. TVOD rental: UserEntitlement(source_type='tvod', title_id=T, expires_at > now())
  3. TVOD purchase: UserEntitlement(source_type='tvod', title_id=T, expires_at IS NULL)
  4. Free offer: TitleOffer(title_id=T, offer_type='free', is_active=TRUE)
```

---

### `content_packages` — Add Tier

| Column | Type | Change | Description |
|--------|------|--------|-------------|
| `id` | UUID | unchanged | Primary key |
| `name` | VARCHAR(100) | unchanged | Display name (e.g., "Basic", "Premium") |
| `description` | TEXT | unchanged | Optional description |
| `tier` | VARCHAR(20) | **NEW** nullable | Tier label for display/grouping (e.g., 'basic', 'premium', 'sports') |

---

## Migration: `005_subscription_entitlements_tvod.py`

**Operations in order:**
1. Add `title_offers` table with unique partial index on `(title_id, offer_type)` WHERE `is_active`
2. Add `viewing_sessions` table with index on `(user_id, ended_at)`
3. `ALTER TABLE user_entitlements ALTER COLUMN package_id DROP NOT NULL`
4. `ALTER TABLE user_entitlements ADD COLUMN title_id UUID REFERENCES titles(id) ON DELETE CASCADE`
5. `CREATE INDEX ON user_entitlements (user_id, title_id, expires_at) WHERE title_id IS NOT NULL`
6. `ALTER TABLE content_packages ADD COLUMN tier VARCHAR(20)`

---

## Entity Relationships

```
users
  └─── user_entitlements ─┬─── content_packages ─── package_contents ─── titles
                          └─── titles (TVOD direct)
  └─── viewing_sessions ──────── titles

titles ─── title_offers
```

---

## Key Entities Summary

| Entity | Table | New/Modified | Key Role |
|--------|-------|-------------|---------|
| Content Package | `content_packages` | Modified (+tier) | Named bundle of SVOD content |
| Package Content | `package_contents` | Unchanged | Join table: package ↔ title |
| User Entitlement | `user_entitlements` | Modified (+title_id, nullable package_id) | Grants access — SVOD or TVOD |
| Title Offer | `title_offers` | **New** | Defines rent/buy/free price for a title |
| Viewing Session | `viewing_sessions` | **New** | Tracks active streams for concurrency limits |
