# Feature Specification: Backend Hardening for Production Readiness

**Feature Branch**: `005-backend-hardening`
**Created**: 2026-02-13
**Status**: Draft
**Input**: User description: "We need to address some issues in the backend. Use radiant-sniffing-star.md in the plans folder as input."

## Clarifications

### Session 2026-02-13

- Q: Should the health check be a single endpoint or split into separate liveness and readiness endpoints? → A: Split into two endpoints — a shallow liveness check (process is running) and a deep readiness check (verifies DB connectivity). This prevents unnecessary container restarts during transient database outages.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Secure Authentication Credentials (Priority: P1)

The platform must not ship with default or guessable authentication secrets. An operator deploying the system must be forced to configure a strong secret before the application starts. If the secret is missing or too weak, the system refuses to boot rather than running in an insecure state.

**Why this priority**: A hardcoded secret means anyone who reads the source code can forge authentication tokens and impersonate any user, including admins. This is the single highest-risk vulnerability.

**Independent Test**: Deploy the system without setting the authentication secret environment variable and verify the application fails to start with a clear error message.

**Acceptance Scenarios**:

1. **Given** the authentication secret environment variable is not set, **When** the application starts, **Then** it fails immediately with a clear error message indicating the secret must be configured.
2. **Given** the authentication secret is set but shorter than 32 characters, **When** the application starts, **Then** it fails with an error indicating the minimum required length.
3. **Given** a valid authentication secret is set (>= 32 characters), **When** the application starts, **Then** it boots normally and authentication works as expected.
4. **Given** the application is running, **When** an operator inspects configuration or logs, **Then** the secret value is never exposed in plain text.

---

### User Story 2 - Profile Ownership Enforcement (Priority: P1)

When a logged-in user makes a request that involves a profile (viewing history, bookmarks, watchlist, ratings, recommendations), the system must verify that the specified profile belongs to the authenticated user. Currently, any authenticated user can access or modify any other user's profile data by guessing or enumerating profile identifiers.

**Why this priority**: This is an Insecure Direct Object Reference (IDOR) vulnerability that exposes every user's personal viewing data, bookmarks, ratings, and watchlist to any authenticated attacker. It affects all profile-scoped endpoints across the platform.

**Independent Test**: Log in as User A, attempt to access User B's profile-scoped data (bookmarks, watchlist, ratings), and verify the system denies access.

**Acceptance Scenarios**:

1. **Given** User A is authenticated and owns Profile P1, **When** User A requests bookmarks for Profile P1, **Then** the system returns the bookmarks successfully.
2. **Given** User A is authenticated and does NOT own Profile P2, **When** User A requests bookmarks for Profile P2, **Then** the system returns a 403 Forbidden error.
3. **Given** User A is authenticated and does NOT own Profile P2, **When** User A attempts to update a bookmark for Profile P2, **Then** the system returns a 403 Forbidden error.
4. **Given** a profile identifier that does not exist, **When** any user requests data for that profile, **Then** the system returns a 403 Forbidden error (not 404, to avoid enumeration).
5. **Given** this enforcement is applied, **When** any endpoint accepting a profile parameter is called, **Then** ownership is checked consistently across all endpoints (viewing, recommendations, EPG favorites, catalog browsing with parental filters).

---

### User Story 3 - Elimination of SQL Injection Vectors (Priority: P1)

All database queries must use parameterized queries or ORM-safe constructs. No user-controlled or dynamically constructed values should be interpolated directly into SQL strings. Even when current inputs originate from trusted sources (other database queries), the code must be safe against future changes that could introduce untrusted data into these paths.

**Why this priority**: SQL injection is a critical vulnerability class (OWASP Top 10 #3). String-interpolated SQL `IN` clauses and unescaped ILIKE patterns are present in the recommendation, catalog search, and EPG services.

**Independent Test**: Review all raw SQL constructions and verify that every dynamic value uses bind parameters. Run queries with values containing SQL metacharacters (single quotes, semicolons, percent signs) and verify they are handled safely.

**Acceptance Scenarios**:

1. **Given** a recommendation query that filters by multiple identifiers, **When** the query is executed, **Then** all identifiers are passed as bind parameters (not string-interpolated).
2. **Given** a user searches for a title containing SQL metacharacters (e.g., `'; DROP TABLE titles; --`), **When** the search is executed, **Then** the query runs safely and returns expected results (or no results).
3. **Given** a user searches with ILIKE wildcard characters (e.g., `%` or `_`), **When** the search is executed, **Then** those characters are treated as literal search text, not as SQL wildcards.
4. **Given** any service that constructs SQL dynamically, **When** the codebase is reviewed, **Then** zero instances of f-string or format-string SQL interpolation exist.

---

### User Story 4 - Restricted Cross-Origin Access (Priority: P2)

The platform's cross-origin resource sharing (CORS) policy must only allow the HTTP methods and headers that the API actually uses, rather than permitting all methods and headers. This limits the attack surface for cross-origin requests.

**Why this priority**: Overly permissive CORS can enable cross-site request forgery variants and is a security hygiene issue, though lower risk than the P1 items since CORS is a browser-enforced mechanism.

**Independent Test**: Send a preflight OPTIONS request with an unusual HTTP method (e.g., PATCH or TRACE) and verify the server does not include it in the allowed methods response.

**Acceptance Scenarios**:

1. **Given** a cross-origin request using GET, POST, PUT, or DELETE, **When** the browser sends a preflight request, **Then** the server allows the method.
2. **Given** a cross-origin request using an unsupported method (e.g., TRACE), **When** the browser sends a preflight request, **Then** the server does not include it in the allowed methods.
3. **Given** a cross-origin request with standard headers (Authorization, Content-Type, Accept), **When** the browser sends a preflight request, **Then** the server allows these headers.
4. **Given** a cross-origin request with a non-standard header, **When** the browser sends a preflight request, **Then** the server does not include it in the allowed headers.

---

### User Story 5 - Reliable Health Monitoring (Priority: P2)

The platform must expose separate liveness and readiness health check endpoints. The liveness endpoint confirms the application process is running (used by orchestrators to decide whether to restart). The readiness endpoint verifies the system can actually serve requests, including database connectivity (used by load balancers to decide whether to route traffic). This split prevents unnecessary container restarts during transient database outages.

**Why this priority**: A shallow health check that always returns "healthy" causes orchestrators to route traffic to instances that cannot serve requests, leading to user-facing errors. A single deep-check endpoint used for both liveness and readiness causes unnecessary restarts during brief DB outages.

**Independent Test**: Stop the database, call both health endpoints, and verify: liveness still returns healthy (process is fine), readiness returns unhealthy (DB is down).

**Acceptance Scenarios**:

1. **Given** the application and database are both running normally, **When** the liveness check is called, **Then** it returns a healthy status (200).
2. **Given** the application and database are both running normally, **When** the readiness check is called, **Then** it returns a healthy status (200) with dependency status details.
3. **Given** the database is unreachable, **When** the liveness check is called, **Then** it still returns a healthy status (200) since the process is running.
4. **Given** the database is unreachable, **When** the readiness check is called, **Then** it returns an unhealthy status (503) with a message indicating the database is unreachable.
5. **Given** the application is running but the database is slow, **When** the readiness check is called, **Then** it completes within a reasonable timeout (e.g., 5 seconds) and reports the status accurately.
6. **Given** any monitoring or orchestration tool, **When** it polls the readiness endpoint, **Then** it receives a response that includes status for each critical dependency (database).

---

### User Story 6 - Removal of Confusing Duplicate Entry Point (Priority: P3)

The project contains a duplicate entry point file at the root of the backend directory that only prints a debug message. This creates confusion about which file is the real application entry point and could cause import issues. It must be removed.

**Why this priority**: Low risk but easy to fix. Reduces developer confusion and prevents potential import path issues.

**Independent Test**: Verify the duplicate file no longer exists and the application starts correctly from the intended entry point.

**Acceptance Scenarios**:

1. **Given** the duplicate entry point file exists, **When** it is removed, **Then** the application continues to start and function correctly.
2. **Given** the duplicate is removed, **When** a developer searches for the application entry point, **Then** only one unambiguous entry point exists.

---

### User Story 7 - Database Connection Pool Resilience (Priority: P2)

The database connection pool must be configured to handle the expected concurrent load from multiple clients sending frequent requests (e.g., 30-second bookmark heartbeats from many simultaneous viewers). The default pool size is too small and will be exhausted under moderate load, causing request failures.

**Why this priority**: Under production load with many concurrent users, the default pool of 5 connections will be exhausted, causing cascading request failures. This is a reliability issue that blocks production deployment.

**Independent Test**: Simulate concurrent requests exceeding the default pool size and verify the system handles them without connection errors.

**Acceptance Scenarios**:

1. **Given** 20+ concurrent clients sending bookmark heartbeat requests, **When** all requests are processed, **Then** no connection pool exhaustion errors occur.
2. **Given** a database connection becomes stale or drops, **When** the pool attempts to use it, **Then** the pool detects the dead connection and creates a fresh one automatically.
3. **Given** the pool reaches its maximum size, **When** additional requests arrive, **Then** they queue and wait (with a timeout) rather than failing immediately.
4. **Given** connections have been idle for an extended period, **When** they are recycled, **Then** no connection errors occur due to server-side timeouts.

---

### User Story 8 - Admin Authorization Consistency (Priority: P3)

Admin-only endpoints must enforce authorization through a consistent, centralized mechanism rather than relying on manual checks in each endpoint handler. This prevents accidental omission of authorization checks when new admin endpoints are added.

**Why this priority**: The current manual approach works but is error-prone for future development. A centralized dependency makes it impossible to forget the check.

**Independent Test**: Add a new admin endpoint and verify that the centralized mechanism automatically enforces admin authorization without any manual code in the endpoint handler.

**Acceptance Scenarios**:

1. **Given** a non-admin user, **When** they call any admin endpoint, **Then** the system returns 403 Forbidden before the endpoint handler runs.
2. **Given** an admin user, **When** they call an admin endpoint, **Then** the request proceeds normally.
3. **Given** a developer adds a new admin endpoint using the centralized mechanism, **When** a non-admin user calls it, **Then** authorization is enforced without any additional code in the endpoint handler.

---

### Edge Cases

- What happens when a user's authentication token expires mid-session while health checks pass?
- How does the system behave when the database becomes temporarily unreachable during a request (not just at health check time)?
- What happens when a profile is deleted while another session is actively using it?
- How does the connection pool behave during a database restart (all connections invalidated simultaneously)?
- What happens when CORS preflight requests arrive for the health check endpoint (which should be publicly accessible)?

*These edge cases are documented for awareness and are deferred to future work. They do not have corresponding requirements in this feature.*

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST fail to start if the authentication secret is not configured via environment variable.
- **FR-002**: System MUST fail to start if the configured authentication secret is shorter than 32 characters.
- **FR-003**: System MUST never log or expose the authentication secret value in plain text.
- **FR-004**: System MUST verify that the requesting user owns the specified profile before processing any profile-scoped request.
- **FR-005**: System MUST return 403 Forbidden when a user attempts to access a profile they do not own.
- **FR-006**: System MUST return 403 Forbidden (not 404) when a non-existent profile is specified, to prevent profile enumeration.
- **FR-007**: Profile ownership enforcement MUST apply consistently to all endpoints that accept a profile parameter (viewing, recommendations, EPG favorites, catalog filtering).
- **FR-008**: System MUST use parameterized queries (bind parameters) for all dynamically constructed SQL, with zero instances of string interpolation in SQL.
- **FR-009**: System MUST escape SQL wildcard characters (`%`, `_`) in user-provided search terms before using them in pattern-matching queries.
- **FR-010**: CORS policy MUST restrict allowed methods to only those the API uses (GET, POST, PUT, DELETE, OPTIONS).
- **FR-011**: CORS policy MUST restrict allowed headers to only those the API requires (Authorization, Content-Type, Accept).
- **FR-012**: System MUST expose a liveness endpoint that returns 200 when the application process is running, without checking external dependencies.
- **FR-013**: System MUST expose a readiness endpoint that verifies database connectivity before reporting healthy status.
- **FR-014**: Readiness endpoint MUST return 503 with a descriptive message (including per-dependency status) when any critical dependency is unreachable.
- **FR-021**: Readiness endpoint MUST complete within 5 seconds even when dependencies are slow.
- **FR-015**: The duplicate backend entry point file MUST be removed.
- **FR-016**: Database connection pool MUST be configured with sufficient capacity for expected concurrent load (pool size >= 20, overflow >= 10).
- **FR-017**: Database connection pool MUST automatically detect and replace stale connections (pre-ping enabled).
- **FR-018**: Database connection pool MUST recycle connections periodically to prevent server-side timeout issues.
- **FR-019**: Admin endpoints MUST enforce authorization through a centralized mechanism rather than per-endpoint manual checks.
- **FR-020**: Pool configuration values (size, overflow, recycle interval) MUST be configurable via environment variables.

### Key Entities

- **User**: The authenticated account. Owns one or more profiles. May have admin privileges.
- **Profile**: A viewing profile within a user account. Scoped to a single user. All viewing activity (bookmarks, ratings, watchlist, recommendations) is profile-scoped.
- **Authentication Secret**: A server-side secret used to sign and verify authentication tokens. Must be strong, externally configured, and never exposed.
- **Connection Pool**: The database connection pool managed by the application. Configured with size, overflow, pre-ping, and recycle parameters.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Application refuses to start in 100% of cases where the authentication secret is missing or under 32 characters.
- **SC-002**: Zero profile-scoped endpoints allow cross-user data access -- verified by attempting access to another user's profile on every profile-scoped endpoint.
- **SC-003**: Zero instances of string-interpolated SQL exist in the codebase -- verified by code review or static analysis.
- **SC-004**: CORS preflight responses include only the explicitly allowed methods and headers -- verified by HTTP inspection.
- **SC-005**: Readiness endpoint returns 503 within 5 seconds when the database is unreachable, while the liveness endpoint continues returning 200 -- verified by stopping the database and calling both endpoints.
- **SC-006**: System handles 50 concurrent bookmark heartbeat requests without connection pool exhaustion -- verified by load testing.
- **SC-007**: All admin endpoints return 403 for non-admin users without any per-endpoint authorization code -- verified by code review and testing.
- **SC-008**: Duplicate entry point file no longer exists in the repository.
- **SC-009**: Authentication secret is never visible in log output, repr(), or configuration dumps -- verified by inspecting logs and calling repr() on the settings object.
- **SC-010**: Searches containing `%` or `_` characters return only literal matches, not wildcard expansions -- verified by searching for these characters and confirming result correctness.
- **SC-011**: Connection pool recycles idle connections within the configured interval -- verified by observing pool behavior after the recycle period.
- **SC-012**: Pool size, max overflow, and recycle interval are configurable via environment variables -- verified by setting env vars and confirming the engine uses the overridden values.

## Assumptions

- The platform uses JWT-based authentication with a shared secret (symmetric signing). Migration to asymmetric keys (RS256) is out of scope.
- Profile ownership is determined by a direct user_id foreign key on the profile record. No delegation or sharing model exists.
- The "allowed CORS origins" are already configurable via environment variable; only methods and headers need restriction.
- Health monitoring uses two separate endpoints: liveness (process running) and readiness (dependencies reachable). Only database connectivity is checked in readiness for now; Redis and other dependencies can be added later.
- Pool size of 20 with overflow of 10 is sufficient for the current expected load (up to 500K concurrent platform users, with most traffic distributed across many backend instances).
- The existing admin router is the only location requiring admin authorization enforcement.

## Scope Boundaries

**In scope**:
- Tier 1 items (1.1-1.7) from the backend improvement plan: JWT secret, IDOR fix, SQL injection, CORS, health check, duplicate file removal, DB pool config
- Tier 2 item 2.4: Admin authorization as dependency (closely related to security hardening)

**Out of scope**:
- Test suite creation (Tier 2, item 2.1) -- separate feature
- Structured logging and error middleware (Tier 2, items 2.2-2.3) -- separate feature
- Async embedding generation (Tier 2, item 2.5) -- separate feature
- N+1 query optimization (Tier 2, item 2.6) -- separate feature
- Rate limiting (Tier 2, item 2.7) -- separate feature
- Redis caching (Tier 2, item 2.8) -- separate feature
- All Tier 3 and Tier 4 items -- future features
