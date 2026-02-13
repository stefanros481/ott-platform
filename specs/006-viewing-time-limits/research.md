# Research: Profile Viewing Time Limits

**Feature**: 006-viewing-time-limits
**Date**: 2026-02-13

## R1: Real-Time Tracking Without Redis (PoC Constraint)

**Decision**: Use an in-memory Python dict for real-time balance tracking with periodic DB flush, rather than Redis.

**Rationale**: Constitution constraint IV (Docker Compose as Truth) and the PoC principle mandate no new external services. Redis would add a container and operational complexity. For the PoC scale (demo scenarios, not 500K concurrent sessions), an in-memory dict keyed by `{profile_id}:{reset_date}` is sufficient. The dict is initialized from the DB on first access and flushed to DB on each heartbeat (every 30 seconds). On process restart, balances are recovered from the DB.

**Alternatives considered**:
- Redis container: Rejected — violates PoC simplicity; adds container, config, health check
- DB-only (write every heartbeat): Acceptable for PoC scale. Chosen as the fallback if in-memory dict adds complexity. A heartbeat every 30s per active child session is ~2 writes/min, well within PoC PostgreSQL capacity
- SQLite sidecar: Rejected — adds complexity, no benefit over PostgreSQL for this use case

**Final approach**: Direct DB writes on each heartbeat. At PoC scale this is fine. The `viewing_time_balances` table uses an UPSERT pattern to atomically increment `used_seconds`. No in-memory caching needed.

## R2: PIN Storage and Verification

**Decision**: Store PIN as bcrypt hash on the `users` table. Reuse existing bcrypt dependency (already used for password hashing).

**Rationale**: PIN is account-scoped (not per-profile), so a single `pin_hash` column on `users` is appropriate. bcrypt provides adequate security for a 4-digit PIN combined with the 5-attempt lockout. No new dependencies needed.

**Alternatives considered**:
- Separate `account_pins` table: Rejected — over-normalized for a single value per account
- SHA-256 hash: Rejected — too fast for brute force without the lockout
- Argon2: Rejected — would require new dependency (`argon2-cffi`), bcrypt is already present

**Implementation details**:
- `users.pin_hash` (nullable String(255)) — NULL means no PIN set yet
- `users.pin_lockout_until` (nullable DateTime(tz)) — NULL means not locked out
- `users.pin_failed_attempts` (Integer, default 0) — reset on success or lockout expiry
- PIN verification: bcrypt.checkpw() with constant-time comparison
- Lockout: 5 failed attempts → set `pin_lockout_until = now + 30 minutes`

## R3: Daily Reset Mechanism

**Decision**: Compute reset boundaries on-demand (not via background scheduler).

**Rationale**: PoC has no background task infrastructure (no Celery, no APScheduler). Instead, compute the current "viewing day" boundary at query time. When a balance query arrives, calculate whether the current time is past the reset boundary; if so, return a fresh balance (0 used). The stale balance row remains in the DB for history purposes.

**Alternatives considered**:
- Background cron job: Rejected — requires scheduler infrastructure not in PoC
- DB trigger: Rejected — adds complexity, harder to test
- Client-side reset: Rejected — clients can't be trusted for enforcement

**Implementation**:
- `ViewingTimeBalance` has `reset_date` (Date) representing which "viewing day" the balance covers
- `reset_date` is computed from: `current_time - reset_hour` (e.g., if reset is 6 AM and it's 5 AM, the reset_date is still yesterday)
- On balance query, if no row exists for today's `reset_date`, a fresh balance (0 used) is returned
- Old balance rows are kept for reporting (retained 90 days per GDPR policy)

## R4: Concurrent Stream Enforcement for Child Profiles

**Decision**: Check-and-block at playback session creation time, with heartbeat-based session expiry.

**Rationale**: When a child profile starts playback, the system checks for an existing active session. If one exists on another device, the new session takes over (old session is marked expired). This is simpler than real-time WebSocket-based session killing for the PoC.

**Alternatives considered**:
- WebSocket push to terminate old device: Rejected for PoC — too complex. Old device will discover termination on its next heartbeat (within 30s)
- Prevent new session entirely: Rejected — bad UX when switching devices legitimately

**Implementation**:
- `viewing_sessions` table tracks active sessions with `device_id`, `started_at`, `last_heartbeat_at`, `ended_at`
- On new session creation: find active session for same profile where `ended_at IS NULL` and `last_heartbeat_at > now - 5min`; if found, set `ended_at = now` (terminate it)
- Session is considered expired if `last_heartbeat_at < now - 5min` (no heartbeat = inactive)

## R5: Educational Content Classification

**Decision**: Use existing `Title.age_rating` field pattern — add a boolean `is_educational` column to the `titles` table.

**Rationale**: The spec says educational classification comes from content provider metadata. In the PoC, we model this as a simple boolean on the title. Seed data sets `is_educational = True` on 5-10 titles (documentaries, kids learning content). The viewing time service checks this flag during heartbeat processing.

**Alternatives considered**:
- Tag-based system (many-to-many): Rejected — over-engineered for PoC; a boolean is sufficient
- Separate metadata table: Rejected — unnecessary indirection

## R6: Offline Enforcement Strategy (PoC Scope)

**Decision**: Defer full offline enforcement to post-PoC. Document the design but implement online-only enforcement.

**Rationale**: Offline enforcement requires platform-specific secure storage (Keychain, EncryptedSharedPreferences, encrypted IndexedDB), clock tampering detection, and sync reconciliation. The PoC frontend is a web app (Shaka Player in browser) — there is no offline/download capability in the current stack. Implementing offline enforcement would require building download support first, which is out of scope.

**What we implement**: Server-side tracking, cross-device balance sync, fail-closed when server unreachable.
**What we defer**: Client-side secure storage, clock tamper detection, offline lock screen variant, sync reconciliation.

## R7: Remote Extra Time Grant (Real-Time Push)

**Decision**: Use polling (not WebSocket) for the PoC.

**Rationale**: The frontend already uses polling for bookmark sync and balance queries. Adding WebSocket infrastructure for a single push event is disproportionate for the PoC. When a parent grants time remotely, the child's device picks it up on its next balance poll (every 60 seconds). For the PoC demo, this latency is acceptable. The 5-second propagation target from the spec is a production requirement.

**Alternatives considered**:
- WebSocket connection per child session: Rejected — requires WebSocket infrastructure (not in PoC stack)
- Server-Sent Events (SSE): Simpler than WebSocket but still requires connection management
- Reduce poll interval to 10s during lock screen: Acceptable enhancement — when lock screen is active, poll every 10s instead of 60s to catch remote grants faster

**Implementation**: Balance poll every 60s during normal playback, every 10s when lock screen is active.

## R8: Weekly Report Generation

**Decision**: Generate reports on-demand when the parent views the report screen, not via batch job.

**Rationale**: No background scheduler in the PoC. Instead, when the parent navigates to Viewing History, the weekly summary is computed on-the-fly by aggregating `viewing_sessions` data. This avoids batch infrastructure while still demonstrating the feature.

**Alternatives considered**:
- Scheduled batch job: Rejected — requires scheduler not in PoC
- Materialized view: Over-engineered for PoC
- Pre-computed on each session end: Adds write overhead to every heartbeat

## Unknowns Resolution Summary

| Unknown | Resolution | Impact |
|---------|-----------|--------|
| Real-time tracking without Redis | Direct DB writes per heartbeat | Low — PoC scale handles it |
| PIN storage | bcrypt hash on users table | None — reuses existing dependency |
| Daily reset without scheduler | Compute reset boundaries on-demand | None — query-time logic |
| Concurrent stream enforcement | Check-and-block at session creation | Low — 30s detection latency acceptable for PoC |
| Educational content tagging | Boolean column on titles table | None — simple seed data |
| Offline enforcement | Deferred to post-PoC | Medium — documented in plan, not implemented |
| Real-time push for remote grants | Polling with 10s interval on lock screen | Low — acceptable for demo |
| Weekly report generation | On-demand aggregation | None — computed at query time |
