# Data Model: Backend Performance Optimization

**Feature Branch**: `009-backend-performance`
**Date**: 2026-02-13

## Overview

This feature does **not** add new tables or entities. It optimizes how existing entities are queried and cached. The changes are:

1. **New index** on existing table (via Alembic migration)
2. **In-process cache** for ViewingTimeConfig (application-level, not persisted)
3. **Query pattern changes** (joined queries, RETURNING clause, range comparisons)

## Existing Entities (No Schema Changes)

### ViewingTimeConfig
- **Table**: `viewing_time_configs`
- **Purpose**: Per-profile viewing time limits and schedule settings
- **Key fields**: profile_id (unique), weekday_limit_minutes, weekend_limit_minutes, reset_hour, timezone
- **Change**: Cached in-process with 60s TTL; no schema changes

### ViewingTimeBalance
- **Table**: `viewing_time_balances`
- **Purpose**: Per-profile, per-day usage tracking
- **Key fields**: profile_id, reset_date, used_seconds, educational_seconds, is_unlimited_override
- **Constraint**: `uq_vtb_profile_date` (profile_id, reset_date) — used for upsert
- **Change**: Upsert query updated to use RETURNING clause; no schema changes

### ViewingSession
- **Table**: `viewing_sessions`
- **Purpose**: Individual viewing periods with timing and content metadata
- **Key fields**: profile_id, title_id, started_at, ended_at, total_seconds
- **Existing indexes**:
  - `ix_vs_profile_active`: `(profile_id) WHERE ended_at IS NULL`
  - `ix_vs_profile_started`: `(profile_id, started_at)`
- **Change**: Query patterns updated to use range comparisons instead of `func.date()` so existing `ix_vs_profile_started` index is utilized

### Title (read-only reference)
- **Table**: `titles`
- **Purpose**: Content catalog entries
- **Change**: Loaded with `load_only(Title.id, Title.title)` in history/report queries instead of full object

## New: Alembic Migration

### Migration: `004_add_performance_indexes.py`

**Purpose**: Ensure composite index exists and is optimal for the query patterns used.

The existing index `ix_vs_profile_started` on `(profile_id, started_at)` already covers the primary query pattern. The migration verifies it exists and adds `DESC` ordering on `started_at` if needed for descending date queries (history sorted newest-first).

```sql
-- Verify existing index or create if missing
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_vs_profile_started
ON viewing_sessions (profile_id, started_at DESC);
```

**Rollback**: `DROP INDEX IF EXISTS ix_vs_profile_started;`

## New: In-Process Cache Structure

### ConfigCache

**Not a database entity** — exists only in application memory.

| Field | Type | Description |
|-------|------|-------------|
| key | UUID (profile_id) | Cache lookup key |
| value | ViewingTimeConfig | Cached ORM object (detached from session) |
| cached_at | float (monotonic) | Time when entry was cached |

**Behavior**:
- **TTL**: 60 seconds (configurable via constant)
- **Max size**: 10,000 entries
- **Eviction**: LRU when max size exceeded
- **Invalidation**: Explicit eviction on config update via `PUT /viewing-time` endpoint
- **Fallback**: On cache miss or after TTL expiry, fetches from database

## New: Performance Metrics Structure

### PerformanceMetrics (in-process counters)

**Not a database entity** — exists only in application memory, reset on restart.

| Metric | Type | Description |
|--------|------|-------------|
| heartbeat_total | int | Total heartbeats processed since startup |
| heartbeat_db_ops_total | int | Total DB operations across all heartbeats |
| heartbeat_duration_ms_sum | float | Sum of heartbeat durations (for averaging) |
| heartbeat_duration_ms_max | float | Maximum heartbeat duration observed |
| config_cache_hits | int | Config cache hit count |
| config_cache_misses | int | Config cache miss count |
| config_cache_invalidations | int | Explicit cache invalidation count |

**Derived metrics** (computed on read):
- `avg_db_ops_per_heartbeat` = heartbeat_db_ops_total / heartbeat_total
- `avg_heartbeat_duration_ms` = heartbeat_duration_ms_sum / heartbeat_total
- `cache_hit_rate` = config_cache_hits / (config_cache_hits + config_cache_misses)

**Exposed via**: `GET /api/v1/admin/metrics` (AdminUser auth required)

## Query Pattern Changes Summary

| Operation | Before | After |
|-----------|--------|-------|
| Heartbeat lookups | 3 separate SELECTs (profile, config, title) | 1 joined SELECT |
| Balance upsert | INSERT ON CONFLICT + separate SELECT | INSERT ON CONFLICT RETURNING |
| Config fetch (heartbeat) | DB SELECT every time | In-process cache (60s TTL) |
| History date filter | `func.date(started_at) >= date` | `started_at >= datetime` (index-friendly) |
| Weekly report sessions | N separate SELECTs (per profile) | 1 SELECT with `IN(...)` clause |
| Weekly report configs | N separate SELECTs (per profile) | 1 SELECT with `IN(...)` clause |
| Title loading (history) | Full object via `selectinload` | `joinedload` with `load_only(id, title)` |
| PIN hashing | Synchronous on event loop | `asyncio.to_thread()` |
