# Feature Specification: Backend Performance Optimization

**Feature Branch**: `009-backend-performance`
**Created**: 2026-02-13
**Status**: Draft
**Input**: User description: "Implement the 009 backend performance plan — fix async event loop blocking, reduce DB round-trips in heartbeat hot path, add missing indexes, cache config lookups, optimize N+1 queries in weekly reports"

## Clarifications

### Session 2026-02-13

- Q: Should the system expose production metrics (cache hit rate, queries per heartbeat, p95 latency) for ongoing monitoring, or only verify during testing? → A: Add observability — expose key metrics for production monitoring.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Concurrent Viewing Without Stalls (Priority: P1)

Multiple viewers are actively watching content simultaneously, each sending periodic heartbeat signals to track viewing time. Today, a slow operation in the PIN verification path blocks all other requests from being processed, causing heartbeat failures and degraded experience for all viewers — not just the one verifying a PIN.

**Why this priority**: This is a correctness and availability issue. A single user's PIN check can stall the entire server, causing all concurrent viewers to experience failed heartbeats, lost viewing time tracking, and potentially premature lock-outs. Fixing this unblocks the system's ability to serve concurrent users at all.

**Independent Test**: Can be tested by having one user verify a PIN while another user's heartbeat is in-flight. The heartbeat should complete without delay.

**Acceptance Scenarios**:

1. **Given** 100 concurrent viewers are sending heartbeats, **When** one viewer performs a PIN verification, **Then** all other heartbeats continue to be processed without additional delay (no queuing behind the PIN operation).
2. **Given** a parent resets their parental control PIN, **When** the new PIN is being hashed, **Then** all concurrent heartbeat and playback requests continue to be served with normal latency.
3. **Given** the PIN service is under load (multiple PIN verifications at once), **When** heartbeats arrive simultaneously, **Then** heartbeat processing latency remains unaffected by PIN operations.

---

### User Story 2 - Fast Heartbeat Processing at Scale (Priority: P1)

Each active viewer sends a heartbeat every 30 seconds to track their viewing time. Today, each heartbeat requires 4-6 separate database lookups, which creates excessive load at scale and increases response times. The system should process each heartbeat with minimal database overhead.

**Why this priority**: The heartbeat is the single hottest code path in the system. At target scale (thousands of concurrent viewers), the current 4-6 queries per heartbeat create unsustainable database load and risk timeouts. This directly impacts viewing time accuracy and lock screen enforcement.

**Independent Test**: Can be tested by sending heartbeats and measuring database query count per heartbeat call. Verify viewing time tracking remains accurate after optimization.

**Acceptance Scenarios**:

1. **Given** a viewer is watching content and sends a heartbeat, **When** the system processes the heartbeat, **Then** it completes with no more than 3 database operations (down from 4-6).
2. **Given** a viewer's heartbeat includes viewing time tracking and balance updates, **When** the balance is updated, **Then** the updated balance values are returned in the same operation without requiring a separate read.
3. **Given** 1,000 concurrent viewers are sending heartbeats simultaneously, **When** the system processes all heartbeats, **Then** the 95th percentile response time remains under 200ms.

---

### User Story 3 - Efficient History and Report Queries (Priority: P2)

Parents view weekly viewing time reports for their children. Operators query viewing history for specific date ranges. Today, these queries do not efficiently use database indexes because of how date filtering is implemented, and the weekly report issues separate queries for each child profile (N+1 pattern).

**Why this priority**: While reports are less frequent than heartbeats, they can be expensive and cause load spikes. The N+1 query pattern means report generation time grows linearly with the number of child profiles, and the index issue causes full table scans on history queries.

**Independent Test**: Can be tested by generating a weekly report for a parent with multiple children and verifying the report is accurate and fast.

**Acceptance Scenarios**:

1. **Given** a parent has 5 child profiles, **When** they request the weekly viewing time report, **Then** the system generates the report using a fixed number of database queries (not scaling with the number of children).
2. **Given** a user requests viewing history for a specific date range, **When** the query executes, **Then** it uses the database index efficiently (no full table scans).
3. **Given** a parent has 10 child profiles with extensive viewing history, **When** the weekly report is generated, **Then** it completes within 2 seconds.

---

### User Story 4 - Cached Configuration for Repeat Requests (Priority: P2)

Viewing time configuration (daily limits, schedules, educational content rules) rarely changes — only when a parent explicitly updates settings. Despite this, the system re-fetches the configuration from the database on every single heartbeat, adding unnecessary load.

**Why this priority**: Configuration caching is a low-risk, high-reward optimization. Config changes are infrequent (a few times per day at most), while reads happen every 30 seconds per viewer. Caching eliminates a database query from every heartbeat without complex logic.

**Independent Test**: Can be tested by sending multiple heartbeats for the same profile and verifying the config is only fetched from the database once within the cache window.

**Acceptance Scenarios**:

1. **Given** a profile's viewing time configuration has not changed, **When** multiple heartbeats arrive for that profile within 60 seconds, **Then** only the first heartbeat triggers a database lookup for the configuration.
2. **Given** a parent updates their child's viewing time limits, **When** the next heartbeat arrives for that child, **Then** the updated configuration is used (cache is invalidated on update).
3. **Given** the configuration cache is active, **When** heartbeats arrive for different profiles, **Then** each profile's configuration is cached independently.

---

### User Story 5 - Database Index Coverage for Common Queries (Priority: P2)

The system queries viewing sessions by profile and date frequently (for heartbeats, history, and reports). Today, these queries lack proper composite database indexes, causing the database to scan more data than necessary.

**Why this priority**: Adding proper indexes is a foundational optimization that improves all query paths. Without it, the query optimizations from other stories won't reach their full performance potential.

**Independent Test**: Can be tested by running viewing session queries and confirming the database uses index scans rather than sequential scans.

**Acceptance Scenarios**:

1. **Given** the system queries viewing sessions for a specific profile and date range, **When** the query executes, **Then** the database uses an index scan (not a sequential scan).
2. **Given** the index is in place, **When** the viewing history endpoint is called for a profile with thousands of sessions, **Then** the query response time is consistently under 100ms.
3. **Given** a new index migration is applied, **When** existing data is present, **Then** the migration completes without data loss and existing functionality remains unaffected.

---

### User Story 6 - Lightweight Data Loading for History (Priority: P3)

When users browse their viewing history, the system loads complete content records from the database even though the history view only needs the content title. This wastes memory and bandwidth.

**Why this priority**: Lower impact than the other optimizations but contributes to overall system efficiency, especially when history lists are long. This is a refinement that reduces unnecessary data transfer.

**Independent Test**: Can be tested by loading viewing history and confirming that only the needed fields are fetched from related content records.

**Acceptance Scenarios**:

1. **Given** a user requests their viewing history, **When** the system loads associated content information, **Then** only the minimum required fields (identifier and display name) are loaded from content records.
2. **Given** a viewing history contains 100 entries, **When** the history is loaded, **Then** only 2 columns (identifier and display name) are fetched from content records instead of the full row.

---

### User Story 7 - Connection and Configuration Efficiency (Priority: P3)

Several small system-level inefficiencies exist: configuration values are re-parsed on every request, database connections aren't pre-warmed on startup, and prepared statement caching isn't configured. Individually minor, collectively they add latency to every request.

**Why this priority**: These are low-effort improvements that provide marginal gains per request but compound across thousands of concurrent requests. They represent good operational hygiene.

**Independent Test**: Can be tested by measuring cold-start response times and steady-state latency before and after changes.

**Acceptance Scenarios**:

1. **Given** the system starts up, **When** the first requests arrive, **Then** database connections are already established (no cold-start connection delay).
2. **Given** the system is handling requests, **When** configuration values are accessed, **Then** they are read from a cached value rather than re-parsed each time.
3. **Given** the system processes repeated similar queries, **When** prepared statement caching is enabled, **Then** query preparation overhead is eliminated for cached statements.

---

### User Story 8 - Production Performance Observability (Priority: P2)

The operations team needs visibility into backend performance after optimization changes are deployed. Without metrics, there is no way to confirm that optimizations are working as expected or to detect regressions.

**Why this priority**: Observability validates all other stories' success criteria in production. Without it, performance improvements are unverifiable beyond initial testing.

**Independent Test**: Deploy the optimized backend, send heartbeats, then query the metrics endpoint to confirm counters are populated.

**Acceptance Scenarios**:

1. **Given** the optimized backend is running and processing heartbeats, **When** an admin queries the metrics endpoint, **Then** the response includes heartbeat count, average DB operations per heartbeat, p95 duration, cache hit rate, and uptime.
2. **Given** a cache invalidation event occurs, **When** the application logs are inspected, **Then** a structured log line with the profile ID and event type is present.

---

### Edge Cases

- What happens when the config cache contains stale data because the invalidation failed? The system should fall back to a fresh database read after the TTL expires (maximum 60 seconds of stale data).
- How does the system behave if the composite index migration is applied while the system is under load? The migration should be non-blocking to avoid locking the table.
- What happens if heartbeat processing is optimized but a query returns unexpected NULL values from the joined lookup? The system should handle missing related records gracefully (e.g., missing config defaults to system defaults).
- What happens if the cache grows unbounded for profiles? The cache should have a maximum size limit to prevent memory exhaustion, evicting least-recently-used entries.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST process PIN verification and PIN hashing operations without blocking concurrent request processing.
- **FR-002**: The system MUST process each heartbeat using no more than 3 database operations (combined lookups and upsert with return).
- **FR-003**: The system MUST return updated balance values as part of the balance update operation, eliminating the need for a separate read.
- **FR-004**: The system MUST cache viewing time configuration per profile with a configurable time-to-live (default 60 seconds).
- **FR-005**: The system MUST invalidate the cached configuration for a profile when a parent updates that profile's viewing time settings.
- **FR-006**: The system MUST maintain a composite database index on viewing sessions by profile and start time to support efficient range queries.
- **FR-007**: The system MUST generate weekly viewing reports using a fixed number of database queries regardless of the number of child profiles.
- **FR-008**: The system MUST use date range comparisons (not function-wrapped date extraction) for filtering viewing sessions by date to enable index usage.
- **FR-009**: The system MUST load only the minimum necessary fields from related content records when building viewing history responses.
- **FR-010**: The system MUST pre-warm database connections on application startup.
- **FR-011**: The system MUST cache parsed configuration values rather than re-parsing them on each request.
- **FR-012**: The configuration cache MUST have a bounded maximum size to prevent unbounded memory growth.
- **FR-013**: All optimizations MUST preserve existing API response formats and behavior — no user-visible changes to responses.
- **FR-014**: The system MUST pass the already-loaded profile to balance lookups when available, avoiding redundant database queries.
- **FR-015**: The system MUST expose production metrics for key performance indicators: heartbeat database operation count, heartbeat response latency (p95), configuration cache hit rate, and weekly report query count.
- **FR-016**: The system MUST emit structured log lines for cache invalidation events and heartbeat processing duration to support operational debugging.

### Key Entities

- **Heartbeat**: A periodic signal from an active viewer that updates their viewing session duration and balance. The most frequent operation in the system.
- **Viewing Time Configuration**: Per-profile settings (daily limits, schedules, educational rules) set by parents. Changes infrequently, read on every heartbeat.
- **Viewing Time Balance**: Per-profile, per-day record of consumed viewing time. Updated on every heartbeat.
- **Viewing Session**: A record of a single continuous viewing period for a profile, including start time, duration, and associated content.
- **Weekly Report**: An aggregation of viewing sessions and balances across all child profiles for a parent, generated on demand.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A PIN verification or PIN change operation does not increase the response time of any concurrent request by more than 10ms.
- **SC-002**: Heartbeat processing uses no more than 3 database round-trips per call (down from 4-6).
- **SC-003**: 95th percentile heartbeat response time remains under 200ms with 1,000 concurrent viewers.
- **SC-004**: Weekly report generation completes in under 2 seconds for a parent with up to 10 child profiles, using a fixed number of queries (not proportional to profile count).
- **SC-005**: Viewing history queries for specific date ranges use index scans (verified by query plan analysis).
- **SC-006**: Configuration is fetched from the database at most once per 60 seconds per profile under continuous heartbeat load.
- **SC-007**: All existing API endpoints return identical response structures and data after optimization — zero breaking changes.
- **SC-008**: Database connection establishment delay on the first request after startup is eliminated (connections are pre-established).
- **SC-009**: Key performance metrics (heartbeat latency, cache hit rate, DB operations per heartbeat) are visible in production monitoring within 5 minutes of deployment.

## Assumptions

- The heartbeat interval remains at 30 seconds per active viewer.
- Viewing time configuration changes are infrequent (a few times per day per profile at most), making a 60-second cache TTL acceptable.
- The system runs as a single application instance (in-process caching is sufficient; distributed caching is not required for this phase).
- The database migration for adding indexes can be performed non-destructively on a live system.
- Existing functional test coverage is sufficient to verify that optimizations don't change API behavior.

## Dependencies

- Depends on the existing viewing time limits feature (006) being complete and stable.
- Requires database migration capabilities for adding indexes.
- PIN service changes depend on the existing parental controls service being in place.

## Scope Boundaries

**In scope:**
- All items marked CRITICAL in the performance plan (C-01, C-02, C-03)
- All items marked HIGH in the performance plan (H-01 through H-05)
- Selected MEDIUM items that are low-effort (M-01, M-06)
- Selected LOW items that are trivially bundled (L-05)
- Database migration for composite index

**Out of scope:**
- Distributed caching — in-process cache is sufficient for now
- Load testing infrastructure setup — performance targets verified via focused benchmarks
- Application-level rate limiting — separate feature
- Items with negligible impact (M-02, M-04, M-08, L-01, L-03, L-04)
