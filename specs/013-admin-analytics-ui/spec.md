# Feature Specification: Admin Analytics UI — Natural Language Query Interface

**Feature Branch**: `013-admin-analytics-ui`
**Created**: 2026-02-21
**Status**: Draft
**Input**: GitHub Issue #2 — Admin Analytics UI: Natural Language Query Interface

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Ask a Question and See Results (Priority: P1)

An admin opens the Analytics page, types a natural language question about content performance (e.g. "Which genres drive SVoD revenue?"), submits it, and sees a formatted result with a summary, data table, confidence score, and metadata — all without leaving the page.

**Why this priority**: This is the core value proposition of the feature. Without it, the page has no function. All other stories build on top of this.

**Independent Test**: Can be tested end-to-end by navigating to the Analytics page, submitting a simple question, and verifying a result is displayed with summary text, a data table, and a confidence indicator.

**Acceptance Scenarios**:

1. **Given** an admin is on the Analytics page, **When** they type "Which genres drive SVoD revenue?" and submit, **Then** the result appears within 3 seconds with a summary sentence, a data table showing genres and metrics, a confidence score, and data freshness information.
2. **Given** a result is displayed, **When** the admin inspects it, **Then** the applied filters (region, time period, service type) are shown even if they are "none".
3. **Given** a result is displayed, **When** the admin reads the footer of the result, **Then** the data sources list and coverage start date are visible.

---

### User Story 2 — Async Query with Progress Indicator (Priority: P2)

An admin submits a complex multi-dimensional question. The system acknowledges the query immediately, shows a loading/polling state, and automatically updates the display once the result is ready — without requiring the admin to manually refresh.

**Why this priority**: Complex queries are a key use case for analytics power users. Without proper async handling the UI appears broken (indefinitely spinning or returning an empty response).

**Independent Test**: Can be tested by submitting "How does engagement differ between Linear TV and SVoD?" and verifying a loading indicator appears followed by a populated result within 30 seconds.

**Acceptance Scenarios**:

1. **Given** an admin submits a complex question, **When** the backend responds with `status: pending`, **Then** a loading indicator with a progress message is shown immediately.
2. **Given** a query is pending, **When** the job completes on the backend, **Then** the result automatically replaces the loading indicator without requiring any user action.
3. **Given** a query has been pending for more than 60 seconds without resolution, **When** the polling timeout is reached, **Then** a friendly error message is displayed with an option to retry.

---

### User Story 3 — Clarification Flow (Priority: P3)

An admin submits a vague or ambiguous question. The system responds with a clarifying question rather than an empty or confusing result. The admin can read the clarification, refine their question, and re-submit.

**Why this priority**: Without this, ambiguous queries silently fail, confusing the admin. The clarification flow makes the system feel intelligent rather than broken.

**Independent Test**: Can be tested by submitting "How is content doing?" and verifying a clarifying question is displayed in a distinct visual style with the original input still editable for refinement.

**Acceptance Scenarios**:

1. **Given** an admin submits "How is content doing?", **When** the backend returns `status: clarification`, **Then** the clarifying question text is displayed in a visually distinct callout (not in the result table area).
2. **Given** a clarification response is shown, **When** the admin reads it, **Then** the original question is still present in the input field so they can edit and resubmit.
3. **Given** a clarification is shown, **When** the admin refines the question and resubmits, **Then** the new query is processed normally.

---

### User Story 4 — Example Queries Panel (Priority: P4)

An admin who is unsure what to ask can browse a curated panel of example questions. Clicking an example populates the input field, which the admin can then submit or adjust before submitting.

**Why this priority**: Discoverability. Without examples, new admins don't know what kinds of questions are supported and are unlikely to get useful results on their first attempt.

**Independent Test**: Can be tested by locating the examples panel on the Analytics page, clicking one example, and verifying it populates the input field without submitting.

**Acceptance Scenarios**:

1. **Given** an admin opens the Analytics page, **When** they look at the examples panel, **Then** at least 5 distinct example questions are shown grouped by category (e.g. Revenue, Engagement, Regional).
2. **Given** an admin clicks an example question, **When** the click is registered, **Then** the input field is populated with that question text and focus moves to the input — but the query is NOT automatically submitted.

---

### User Story 5 — Session Query History (Priority: P5)

While the admin stays on the Analytics page, their previous questions and results are listed in a history panel. Clicking a past question restores that result instantly without re-querying.

**Why this priority**: Allows admins to compare results across multiple questions in a single session without losing earlier findings.

**Independent Test**: Can be tested by submitting two different questions and verifying both appear in a history list, and clicking the first restores its result.

**Acceptance Scenarios**:

1. **Given** an admin has submitted at least two questions in a session, **When** they look at the history panel, **Then** each submitted question appears as a clickable entry in reverse chronological order.
2. **Given** a history entry exists, **When** the admin clicks it, **Then** the corresponding result is instantly displayed without triggering a new API call.
3. **Given** the admin navigates away from the Analytics page and returns, **When** the page loads again, **Then** the history is empty (history is session-scoped, not persisted).

---

### Edge Cases

- What happens when the backend API is unavailable? The UI must show a clear error message and allow retry without refreshing the page.
- What happens when a result contains zero data rows? The summary is shown but the table displays an empty state message ("No data found for this query").
- What happens if a non-admin user navigates directly to the Analytics URL? They must be redirected to the login page.
- What happens if the admin submits an empty question? The submit button is disabled and no API call is made.
- What happens if a pending job reaches `status: failed`? The polling detects the failure and displays the error message from the response.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Admins MUST be able to access the Analytics page via a sidebar navigation link visible in the admin dashboard.
- **FR-002**: The Analytics page MUST be restricted to authenticated admin users; unauthenticated or non-admin access MUST redirect to login.
- **FR-003**: Admins MUST be able to type a natural language question into a text input and submit it using a button.
- **FR-004**: The submit button MUST be disabled when the input is empty or when a query is already in progress.
- **FR-005**: The system MUST display a complete result for synchronous responses containing: summary text, confidence score, data table, applied filters, data freshness, and data sources.
- **FR-006**: The system MUST display a loading indicator for asynchronous responses and automatically poll until the job reaches a terminal state (`complete` or `failed`).
- **FR-007**: The system MUST display the clarifying question text in a distinct callout for clarification responses, leaving the input editable for refinement.
- **FR-008**: The system MUST display an error state when a job reaches `failed` status, showing the error message returned by the backend.
- **FR-009**: The data table MUST render dynamic columns derived from the keys of the result data rows, without requiring hardcoded column definitions.
- **FR-010**: The confidence score MUST be displayed as a visual indicator (percentage label and/or colour-coded badge) alongside the raw value.
- **FR-011**: An example queries panel MUST be displayed on the Analytics page with at least 5 curated example questions grouped by category.
- **FR-012**: Clicking an example question MUST populate the input field without auto-submitting the query.
- **FR-013**: All questions submitted during a session MUST be preserved in a visible query history list in reverse chronological order.
- **FR-014**: Clicking a history entry MUST restore the associated result instantly without making a new API call.
- **FR-015**: The query history MUST be cleared when the admin navigates away from the Analytics page or reloads it.
- **FR-016**: The system MUST display a user-friendly error message when the backend is unreachable, with an option to retry.
- **FR-017**: Polling for async jobs MUST stop and show a timeout error if the job has not completed within 60 seconds.

### Key Entities

- **Query**: A natural language question submitted by an admin, with its associated response state, result payload, and submission timestamp.
- **Result**: The structured response for a completed query — including summary, confidence score, data rows, applied filters, data freshness, and data sources.
- **Job**: A server-side async processing unit identified by a job identifier, polled at regular intervals until it reaches a terminal state.
- **History Entry**: A session-scoped record pairing a submitted query with its final result, enabling instant restoration without re-querying.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An admin can submit a simple question and see a complete result within 3 seconds.
- **SC-002**: An admin can submit a complex question and see the result appear automatically within 60 seconds without manual intervention.
- **SC-003**: 100% of clarification responses display readable clarifying question text — no blank or broken states.
- **SC-004**: Admins can discover and use at least 5 example queries from the page without consulting any documentation.
- **SC-005**: An admin can restore any previous session query result by clicking a history entry in under 100 milliseconds with no network request.
- **SC-006**: The Analytics page is inaccessible to non-admin users — any direct URL access redirects to login within 1 second.

## Assumptions

- The backend query API is already implemented and stable (feature 001); no backend changes are required for this feature.
- The existing JWT-based admin authentication mechanism is reused without modification.
- The admin frontend already has a sidebar component and client-side routing infrastructure that the new page plugs into.
- Query history is session-scoped and in-memory only; no server-side persistence of query history is required.
- The example queries panel content is hardcoded, drawn from the 10 supported query templates in the backend; no admin-configurable example management is needed.
- Polling interval for async jobs is 2 seconds; this is acceptable for a background analytics operation.
