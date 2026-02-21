# Implementation Plan: Admin Analytics UI

**Branch**: `013-admin-analytics-ui` | **Date**: 2026-02-21 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/013-admin-analytics-ui/spec.md`

## Summary

Add an Analytics page to the admin frontend (`frontend-admin`) that exposes the natural language content analytics query engine via a prompt-style UI. The backend API is fully implemented (feature 001). This feature is **frontend-only** — two new files and two small modifications to existing files.

## Technical Context

**Language/Version**: TypeScript 5+ / React 18
**Primary Dependencies**: React (hooks), Tailwind CSS 3+ — no new packages required
**Storage**: In-memory React state only (session-scoped history); no localStorage, no DB
**Testing**: Manual via Vite dev server (`http://localhost:5174`)
**Target Platform**: Admin dashboard (desktop browser, Vite dev server)
**Performance Goals**: Sync queries <3s (SC-001), async <60s (SC-002), history restore <100ms (SC-005)
**Constraints**: No new npm dependencies; consistent with existing admin code patterns
**Scale/Scope**: Single admin user at a time; no concurrency concerns

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. PoC-First Quality | ✅ PASS | Session-only history; no persistence; no rate limiting |
| II. Monolithic Simplicity | ✅ PASS | Frontend-only change; no new backend services or routes |
| III. AI-Native by Default | ✅ PASS | The entire feature IS the AI query UI |
| IV. Docker Compose as Truth | ✅ PASS | No Docker/compose config changes needed |
| V. Seed Data as Demo | ✅ PASS | Uses existing analytics seed data (feature 001) |
| Tech Stack | ✅ PASS | React 18 + TypeScript 5 + Tailwind CSS 3 — already in use |

**Gate result: PASS. No violations.**

## Project Structure

### Documentation (this feature)

```text
specs/013-admin-analytics-ui/
├── plan.md              ← this file
├── research.md          ← Phase 0 output
├── data-model.md        ← Phase 1 output (client-side types)
├── quickstart.md        ← Phase 1 output
└── tasks.md             ← Phase 2 output (/speckit.tasks — not yet created)
```

### Source Code Changes

```text
frontend-admin/src/
├── api/
│   └── analytics.ts          NEW — submitQuery() and pollJob() API functions
├── pages/
│   └── AnalyticsPage.tsx     NEW — Full page component
├── App.tsx                   MODIFY — add /analytics route inside AuthGuard
└── components/
    └── Sidebar.tsx            MODIFY — add Analytics nav item
```

**No backend changes. No new npm packages. No migration.**

## Architecture

### Component Architecture

```
AnalyticsPage
├── Left panel (w-72, fixed)
│   ├── ExamplesPanel         — 10 hardcoded example queries, grouped
│   └── QueryHistory          — session history list, clickable entries
└── Right panel (flex-1)
    ├── QueryInput             — textarea + submit button (disabled when empty/loading)
    └── ResultPanel            — switches based on ActiveQueryState:
        ├── idle               — prompt to ask a question
        ├── submitting         — spinner
        ├── polling            — spinner + "Analysing your question…"
        ├── complete           → ResultCard (summary, confidence, DataTable, filters, meta)
        ├── clarification      → ClarificationCallout (amber callout + question text)
        ├── failed             → ErrorCard (error message + Retry button)
        └── timeout            → TimeoutCard ("Query timed out" + Retry button)
```

### API Client (`analytics.ts`)

```typescript
// Two functions wrapping apiFetch:
submitQuery(question: string): Promise<QueryResponse>
pollJob(jobId: string): Promise<JobStatusResponse>
```

### State Machine in AnalyticsPage

```
idle → submitting → complete         (sync result)
                 → polling → complete  (async job done)
                           → failed    (async job failed)
                           → timeout   (60s elapsed)
                 → clarification      (ambiguous question)
                 → failed             (network error)
```

History entries are appended when a query reaches a terminal state (complete/clarification/failed/timeout).

### Polling Implementation

```typescript
// useEffect reacts to pendingJobId
// setInterval every 2s polls GET /jobs/{jobId}
// Cleared on: unmount | terminal state | timeout
// Timeout: setTimeout(60000) cancels interval and sets phase: 'timeout'
```

### Dynamic Table

```typescript
// Derive columns from first data row:
const columns = data.length > 0 ? Object.keys(data[0]) : []
// Render header + rows dynamically
// Column label: snake_case → "Title Case" transformation
```

### Confidence Badge

```typescript
// Colour coding:
// confidence >= 0.80 → green badge
// confidence >= 0.65 → amber badge
// confidence < 0.65  → red badge (shouldn't occur per backend threshold, but defensive)
// Display: "91% confidence"
```

## Example Queries (Hardcoded)

```typescript
const EXAMPLE_QUERIES = [
  {
    category: 'Revenue & Engagement',
    questions: [
      'Which genres drive SVoD revenue?',
      'What are the top titles by completion rate?',
      'Show me revenue growth by genre over time',
    ],
  },
  {
    category: 'Regional & Audience',
    questions: [
      'Show regional content preferences in Norway',
      'Which content trends with kids profiles?',
      'Compare viewing patterns across NO, SE, DK',
    ],
  },
  {
    category: 'Service & Behaviour',
    questions: [
      'How does engagement differ between Linear TV and SVoD?',
      'What is the Cloud PVR impact on viewing?',
      'Show me browse-without-watch patterns',
      'What are the SVoD upgrade signals?',
    ],
  },
]
```

## Implementation Phases

### Phase 1: API Client + Route Wiring (foundation)
- Create `analytics.ts` with `submitQuery` and `pollJob`
- Add `/analytics` route to `App.tsx`
- Add Analytics nav item to `Sidebar.tsx`

### Phase 2: Core Query Flow — User Story 1 (sync result)
- `AnalyticsPage` skeleton with `QueryInput` and basic `ResultPanel`
- Handle `status: complete` — render `ResultCard` with summary, confidence badge, dynamic `DataTable`, filters, and metadata footer

### Phase 3: Async Polling — User Story 2
- Extend state machine with `polling` phase
- `useEffect` + `setInterval` polling every 2s
- 60s `setTimeout` for timeout error (FR-017)
- `TimeoutCard` and polling spinner

### Phase 4: Clarification Flow — User Story 3
- `ClarificationCallout` component (amber callout)
- Ensure input remains populated after clarification response

### Phase 5: Examples Panel — User Story 4
- `ExamplesPanel` component with grouped example questions
- Click-to-populate (no auto-submit)

### Phase 6: Session History — User Story 5
- `QueryHistory` component
- Append to history on terminal state
- Click-to-restore result from state (no network)

### Phase 7: Edge Cases & Polish
- Empty input: disable submit button
- Backend unreachable: `ErrorCard` with Retry
- Failed job: show `error_message` from API
- Zero-row result: empty state in `DataTable`
- Loading state during submission (before response)

## Key API Contracts (reference)

From `specs/001-content-analytics-agent/contracts/content-analytics.yaml`:

| Endpoint | Method | Auth | Returns |
|----------|--------|------|---------|
| `/api/v1/content-analytics/query` | POST | Bearer JWT | `QueryResponse` (status: complete/pending/clarification) |
| `/api/v1/content-analytics/jobs/{job_id}` | GET | Bearer JWT | `JobStatusResponse` (status: pending/complete/failed) |

The existing `apiFetch` client in `frontend-admin/src/api/client.ts` handles JWT injection and 401 refresh automatically.
