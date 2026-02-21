# Feature Specification: Natural Language Content Analytics Agent

**Feature Branch**: `001-content-analytics-agent`
**Created**: 2026-02-21
**Status**: Draft
**Input**: GitHub Issue #1 — Add Natural Language Query Agent for Content & Product Team Analytics

## Clarifications

### Session 2026-02-21

- Q: What data does this agent query against — existing platform database as-is, or does this feature also include capturing new analytics/telemetry events? → A: Option C — include building a lightweight analytics event capture layer as part of this feature, so real data flows in from day one. This also includes updating the client API to emit events.
- Q: What should happen when a query exceeds the 2-second target — timeout error or async processing? → A: Option B — async processing. Complex queries cannot be optimised (no caching layer, no query rewriting), so returning a job ID immediately and allowing the caller to poll for the result is the correct model.
- Q: Should queries and results be logged for audit purposes? → A: Option C — no logging. This is a PoC with no real user data; queries and results are ephemeral.
- Q: Should the agent be restricted to a new role or reuse existing access control? → A: Option A — admin users only, reusing the existing `is_admin` flag. No new role needed for the PoC.
- Q: Should the seed data script generate synthetic analytics events so the agent is queryable from day one? → A: Option A — yes, seed synthetic analytics events covering realistic viewing patterns across titles, service types, and regions.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Ask a Plain-Language Content Question (Priority: P1)

A content manager types a natural language question about content performance — for example, "Which genres had the highest revenue growth last quarter?" — and receives a structured answer with a plain-English summary and key metrics, without writing any code or SQL.

**Why this priority**: This is the core value proposition of the feature. Everything else builds on this interaction working end-to-end.

**Independent Test**: Can be fully tested by submitting a single natural language question and verifying that the response contains structured data and a human-readable summary.

**Acceptance Scenarios**:

1. **Given** an authenticated content team member, **When** they submit "Which genres drive SVoD revenue?", **Then** the agent returns a ranked list of genres with revenue figures, growth percentages, and a one-paragraph summary of the insight.
2. **Given** a valid question, **When** the agent processes it, **Then** the response arrives within 2 seconds.
3. **Given** a valid question, **When** the agent responds, **Then** the response clearly identifies which service type (Linear, VoD, SVoD, Cloud PVR, etc.) the data relates to.

---

### User Story 2 — Filter Results by Region or Time Period (Priority: P2)

A product owner asks "Show me regional content preferences across Norway, Sweden, Denmark" or "What are trending shows this month?" and receives results scoped to the requested region and/or time window.

**Why this priority**: Regional and temporal filtering is called out as a primary use case and significantly increases the practical value for international OTT operators.

**Independent Test**: Can be tested by submitting a question with an explicit region filter and verifying the response data is scoped to that region only.

**Acceptance Scenarios**:

1. **Given** a question that mentions a specific region, **When** the agent processes it, **Then** results are filtered to that region and the response indicates the applied filter.
2. **Given** a question that mentions a time period ("last quarter", "this month", "2025"), **When** the agent processes it, **Then** results reflect data for that period only.
3. **Given** a question with both a region and a time period, **When** the agent processes it, **Then** both filters are applied correctly.

---

### User Story 3 — Clarification for Ambiguous Questions (Priority: P2)

When a question is too vague to answer with confidence (e.g., "How is content doing?"), the agent asks one targeted clarifying question rather than guessing or returning an error.

**Why this priority**: Ambiguity handling is the difference between a useful tool and a frustrating one. Non-technical users will ask broad questions; the agent must guide them rather than fail silently.

**Independent Test**: Can be tested by submitting a deliberately vague question and verifying the agent responds with a clarifying question rather than data or an error message.

**Acceptance Scenarios**:

1. **Given** an ambiguous question, **When** the agent cannot determine the intent, **Then** it responds with a single clarifying question (not an error).
2. **Given** the agent has asked for clarification, **When** the user resubmits their question with the clarifying information incorporated (e.g., "Which genres drive SVoD revenue?" after being asked about the metric), **Then** the agent uses the combined question to return a result. Note: the API is stateless — the user composes a new, more specific question rather than the agent maintaining session state.
3. **Given** a question that is partially ambiguous (e.g., region not specified but metric is clear), **When** the agent processes it, **Then** it returns results for all regions with a note that the filter was not applied.

---

### User Story 4 — Cross-Service Query (Priority: P3)

A product owner asks a question that spans multiple service types — for example, "What's the engagement rate by content type (Linear vs VoD)?" — and receives a side-by-side comparison across service categories.

**Why this priority**: The issue explicitly lists multi-service context (Linear, TSTV, Catch-up, VoD, SVoD, Cloud PVR) as a requirement. This story validates that cross-service queries work, but is less critical than single-service queries.

**Independent Test**: Can be tested by submitting a question that explicitly compares two service types and verifying the response includes data for both.

**Acceptance Scenarios**:

1. **Given** a question comparing Linear vs VoD engagement, **When** the agent processes it, **Then** results include separate figures for each service type.
2. **Given** a question about Cloud PVR impact on viewing patterns, **When** the agent processes it, **Then** the response contextualises recording data against live/VoD viewing data.

---

### User Story 5 — Client Emits Analytics Events (Priority: P1)

The client app records user interactions (play, pause, completion, content browsing) as structured analytics events, which are stored and made available as the data foundation for the query agent.

**Why this priority**: Without event capture, the agent has no meaningful data to query. This is an enabler for all other user stories.

**Independent Test**: Can be tested by performing a play action in the client and verifying the corresponding event appears in the analytics store within an acceptable time window.

**Acceptance Scenarios**:

1. **Given** a viewer starts playing a title, **When** the play event occurs, **Then** an analytics event is captured with: title ID, service type (Linear/VoD/SVoD), user profile reference, timestamp, and region.
2. **Given** a viewer completes watching a title, **When** the completion event occurs, **Then** a completion event is recorded with watch duration and percentage watched.
3. **Given** the analytics event capture layer is unavailable, **When** a client action occurs, **Then** the client continues to function normally (event capture fails silently, does not block the viewer experience).

---

### Edge Cases

- What happens when no data exists for the requested region or time period? (Agent should respond with "No data available for [filter]" rather than returning zeros or empty tables.)
- What happens when the question references a metric that doesn't exist in the platform (e.g., "social media engagement")? (Agent should clearly state the metric is outside its scope.)
- What happens if the user submits a very long or multi-part question? (Agent should attempt to decompose it or ask which part to answer first.)
- What happens if data is stale or partially available? (Agent should indicate data freshness / last-updated timestamp in the response.)
- What happens when analytics data is sparse (e.g., the event capture layer has only been running for a short time)? (Agent should indicate the data coverage period in its response and caveat insights accordingly.)
- What happens if a caller polls for a job that has already expired or never existed? (Return a clear not-found response, not a server error.)
- What happens if a complex query job fails mid-processing? (Job status must be set to "failed" with a human-readable reason; the caller must not be left in an indefinite pending state.)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The agent MUST accept natural language questions as input from authenticated users with content team or product owner access.
- **FR-001b**: For queries that cannot be resolved within the synchronous response window, the agent MUST return a job ID immediately and provide a polling endpoint so the caller can retrieve the result when ready. The caller MUST be able to check job status (pending / complete / failed) and retrieve the full result upon completion.
- **FR-002**: The agent MUST return structured results that include: ranked/tabular data, a plain-English summary, and a confidence indicator.
- **FR-003**: The agent MUST support filtering by: region/market, time period (relative and absolute), and service type (Linear, TSTV, Catch-up, VoD, SVoD, Cloud PVR). Audience segment filtering is descoped for this PoC iteration — the analytics event schema captures no demographic age data, and the `profiles` table only exposes `is_kids` and `parental_rating` as proxies. Profile-type segmentation (kids vs adult) is addressed via the `content_browse_behavior` query template; a dedicated audience segment filter dimension is deferred to a future iteration when richer subscriber data is available.
- **FR-004**: The agent MUST handle at least 10 distinct query patterns covering the use cases listed in the issue (genre revenue, trending shows by demographic, PVR impact, SVoD upgrade drivers, regional preferences, engagement by content type).
- **FR-005**: The agent MUST ask a clarifying question when a query is ambiguous rather than returning an error or guessing silently.
- **FR-006**: The agent MUST scope its responses to content metadata and performance analytics data available within the OTT platform — it MUST NOT attempt to answer questions outside this domain.
- **FR-007**: The agent MUST indicate which service types and data sources contributed to each response.
- **FR-008**: Results MUST include a data freshness indicator (e.g., "data as of [date]") and a data coverage period (e.g., "based on events captured since [start date]").
- **FR-009**: The agent MUST be accessible only to authenticated admin users (reusing the existing `is_admin` flag); it MUST NOT be accessible to standard subscribers.
- **FR-010**: The client app MUST capture and emit analytics events for key user interactions: play start, play pause, play completion, content browse, and search. Each event MUST include: title ID, service type, user profile reference, timestamp, and region.
- **FR-011**: Analytics event capture MUST be non-blocking — failure to record an event MUST NOT degrade or interrupt the viewer experience.
- **FR-012**: The backend API MUST expose an endpoint for the client to submit analytics events, and this endpoint MUST be included in the existing versioned API surface.

### Key Entities

- **Query**: A natural language question submitted by a user, with optional structured filters (region, time period, service type, audience segment) extracted by the agent.
- **QueryResult**: The structured response to a query — includes tabular data, a plain-English summary, confidence score, applied filters, data freshness timestamp, and data coverage period.
- **ClarificationRequest**: A follow-up question from the agent when the original query is ambiguous — includes context about what information is needed.
- **ContentDimension**: A measurable attribute of content that can be queried (genre, service type, region, audience segment, time period, revenue, engagement rate, etc.).
- **AnalyticsEvent**: A structured record of a user interaction with content. Attributes: event type (play/pause/complete/browse/search), title ID, service type, user profile reference, timestamp, region, and session duration (for completion events).
- **QueryJob**: Represents an in-progress or completed async query. Attributes: job ID, status (pending / complete / failed), submitted timestamp, completed timestamp, and result (once complete). Jobs belonging to one user are not accessible to another.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Simple queries (single service type, no cross-service aggregation) resolve synchronously in under 2 seconds. Complex queries return a job ID within 500ms; the full result is available via polling within 30 seconds.
- **SC-002**: The agent correctly handles at least 10 distinct query patterns without returning errors.
- **SC-003**: Regional and time-period filters are applied correctly in 100% of queries where the filter is explicitly stated.
- **SC-004**: Ambiguous queries result in a clarifying question (not an error) in 100% of cases where the agent cannot determine intent.
- **SC-005**: Content and product team members can answer a business question independently, without engineering support, within a single session.
- **SC-006**: The agent refuses to answer questions outside its defined domain and communicates this clearly to the user.
- **SC-007**: Analytics events are captured for at least the 5 key interaction types (play, pause, complete, browse, search) with zero impact on viewer-facing performance.

## Assumptions

- Access control reuses the existing `is_admin` JWT flag — no new role or permission model is introduced for this PoC.
- Response format will be JSON with a human-readable summary field — no charting or visual output is in scope for this iteration.
- The agent operates as a server-side component; there is no dedicated front-end UI in the first iteration (queries are submitted via API, accessible from admin tooling or developer tools).
- The seed data script will generate synthetic analytics events (realistic viewing patterns across titles, service types, and regions) so the agent is fully queryable from first startup. Re-seeding replaces synthetic events.
- The analytics event store will be part of the existing database; a separate analytics data warehouse is out of scope.
- This is a PoC with no real user data. Query text and results are ephemeral — no query history, audit log, or result persistence is required. GDPR and compliance logging are explicitly out of scope for this iteration.
