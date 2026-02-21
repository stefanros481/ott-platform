# Research: Admin Analytics UI

**Feature**: 013-admin-analytics-ui
**Date**: 2026-02-21

---

## Decision 1: API Client Strategy

**Decision**: Reuse the existing `apiFetch<T>` utility in `frontend-admin/src/api/client.ts`.

**Rationale**: The client already handles JWT auth headers, automatic 401 token refresh, and error normalisation. Creating a new `src/api/analytics.ts` module that calls `apiFetch` is perfectly consistent with how `src/api/admin.ts` works. No new HTTP library needed.

**Alternatives considered**:
- TanStack Query (React Query): Not used anywhere in the admin frontend. Adding it for a single page would be inconsistent and add unnecessary dependency.
- Axios: Not in use in admin frontend; no reason to introduce it.

---

## Decision 2: Async Job Polling Pattern

**Decision**: `setInterval` inside a `useEffect`, cleared on component unmount or when the job reaches a terminal state (`complete` or `failed`).

**Rationale**: The admin frontend uses plain React hooks, no data-fetching library. A `useRef`-held interval ID is the idiomatic React pattern for polling without React Query. Cleanup on unmount prevents memory leaks and avoids state updates on an unmounted component.

**Implementation sketch**:
```typescript
useEffect(() => {
  if (!pendingJobId) return
  const intervalId = setInterval(async () => {
    const job = await pollJob(pendingJobId)
    if (job.status === 'complete' || job.status === 'failed') {
      clearInterval(intervalId)
      // update state
    }
  }, 2000)
  return () => clearInterval(intervalId) // cleanup on unmount / job change
}, [pendingJobId])
```

**Timeout**: An additional `setTimeout` for 60 seconds cancels the interval and sets an error state if no terminal state has been reached, satisfying FR-017.

**Alternatives considered**:
- Recursive `setTimeout`: Slightly more complex to cancel, no meaningful advantage here.
- WebSocket/SSE: Backend doesn't expose a push channel; polling is correct per the API contract.

---

## Decision 3: Dynamic Table Columns

**Decision**: Derive column headers from `Object.keys(data[0])` and render rows by iterating keys. Apply a simple `formatColumnHeader` transform (snake_case → Title Case).

**Rationale**: The API returns varying column schemas per query template (e.g. `genre, service_type, event_count` for one template vs `region, play_starts, avg_duration_min` for another). Hardcoding columns would break for any template mismatch. Dynamic derivation satisfies FR-009 with zero maintenance burden.

**Column ordering**: Keys are returned in insertion order from the Python dict, which is the natural SQL `SELECT` column order — correct for display.

**Alternatives considered**:
- Column config per template ID: Over-engineered for a PoC; requires frontend to track all 10 template schemas.
- Generic key-value list: Less readable than a table for tabular analytics data.

---

## Decision 4: Session History State

**Decision**: `useState<HistoryEntry[]>` in the `AnalyticsPage` component. History lives in component state, cleared automatically on unmount (navigation away), consistent with FR-015.

**Rationale**: No persistence needed (per spec Assumptions). React component state is the simplest correct solution. No context, no store, no localStorage.

**HistoryEntry shape**:
```typescript
type HistoryEntry = {
  id: string           // uuid for key prop
  question: string
  submittedAt: Date
  response: QueryResponse | JobResult  // the final resolved result
}
```

Clicking a history entry sets `activeResult` to the stored response — zero network calls (SC-005: <100ms).

**Alternatives considered**:
- SessionStorage: Adds complexity, survives page refresh which the spec explicitly excludes.
- React Context: Unnecessary indirection for single-page state.

---

## Decision 5: Page Layout

**Decision**: Two-column layout within the existing `main` area (Sidebar is already fixed at `w-64`).
- **Left column** (narrow, `w-72`): Examples panel (top) + Query history (bottom, scrollable)
- **Right column** (flex-1): Query input bar (top) + Result panel (scrollable)

**Rationale**: This mirrors common analytics tool layouts (Metabase, Redash). The history and examples are secondary — keeping them in a sidebar prevents them from dominating the view. On smaller screens the left column can collapse, but the spec doesn't require responsive design (admin tool, desktop-first).

**Alternatives considered**:
- Single-column (stacked): History below result becomes unwieldy once several queries accumulate.
- Modal for results: Breaks the session workflow; admin can't see history and result simultaneously.

---

## Decision 6: Confidence Score Display

**Decision**: Colour-coded badge (green ≥ 0.80, amber 0.65–0.79, red < 0.65) showing the percentage, e.g. "91% confidence". Rendered inline with the result summary.

**Rationale**: Threshold of 0.65 is the backend's clarification cutoff — any result returned is ≥ 0.65. The three-band colouring gives admins instant quality signal without needing to interpret a raw float. Satisfies FR-010.

**Alternatives considered**:
- Progress bar: More visual space than needed for a single data point.
- Raw float only: Non-intuitive for non-technical admins.

---

## Decision 7: Example Queries Content

**Decision**: Hardcode 10 example questions in `AnalyticsPage.tsx`, drawn from the 10 backend query templates, grouped into three categories: **Revenue & Engagement**, **Regional & Audience**, **Service & Behaviour**.

**Rationale**: The 10 backend templates are stable (PoC; no admin UI for template management). Hardcoding avoids a `/templates` API endpoint that doesn't exist. The examples panel satisfies FR-011 (≥5 examples) comfortably.

| Category | Examples |
|----------|---------|
| Revenue & Engagement | "Which genres drive SVoD revenue?", "What are the top titles by completion rate?", "Show me revenue growth by genre over time" |
| Regional & Audience | "Show regional content preferences in Norway", "Which content trends with kids profiles?", "Compare viewing patterns across NO, SE, DK" |
| Service & Behaviour | "How does engagement differ between Linear TV and SVoD?", "What is the Cloud PVR impact on viewing?", "Show me browse-without-watch patterns", "What are SVoD upgrade signals?" |

---

## No Backend Changes Required

The backend API (feature 001) is complete and stable. This feature is entirely frontend-only. No new migrations, no new routes, no seed changes.
