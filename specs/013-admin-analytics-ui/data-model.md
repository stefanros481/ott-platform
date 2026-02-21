# Data Model: Admin Analytics UI

**Feature**: 013-admin-analytics-ui
**Date**: 2026-02-21
**Scope**: Client-side only — no database schema changes. This document describes the TypeScript types used in the frontend.

---

## Overview

This feature introduces no backend data model changes. All data is fetched from the existing Content Analytics API (feature 001) and held in React component state for the lifetime of the page session.

---

## Client-Side Types

### QueryRequest
```typescript
// Sent to POST /api/v1/content-analytics/query
interface QueryRequest {
  question: string  // 3–1000 characters
}
```

### QueryResult
```typescript
// The result payload for a completed query
interface QueryResult {
  summary: string
  confidence: number           // 0.0–1.0
  data: Record<string, unknown>[]  // dynamic columns, varies per template
  applied_filters: {
    region: string | null
    time_period: string | null
    service_type: string | null
  }
  data_sources: string[]
  data_freshness: string       // ISO 8601 datetime
  coverage_start: string       // ISO 8601 datetime
}
```

### ClarificationPayload
```typescript
interface ClarificationPayload {
  type: 'clarification'
  clarifying_question: string
  context: string
}
```

### QueryResponse
```typescript
// Response from POST /api/v1/content-analytics/query
interface QueryResponse {
  status: 'complete' | 'pending' | 'clarification'
  result: QueryResult | null         // populated when status === 'complete'
  job_id: string | null              // UUID, populated when status === 'pending'
  clarification: ClarificationPayload | null  // populated when status === 'clarification'
}
```

### JobStatusResponse
```typescript
// Response from GET /api/v1/content-analytics/jobs/{job_id}
interface JobStatusResponse {
  job_id: string
  status: 'pending' | 'complete' | 'failed'
  submitted_at: string         // ISO 8601
  completed_at: string | null
  result: QueryResult | null
  error_message: string | null
}
```

### HistoryEntry
```typescript
// Session-scoped query history (in-memory, cleared on navigation)
interface HistoryEntry {
  id: string                   // uuid generated client-side for React key
  question: string
  submittedAt: Date
  status: 'complete' | 'clarification' | 'failed'
  result: QueryResult | null
  clarification: ClarificationPayload | null
  errorMessage: string | null
}
```

### ActiveQueryState
```typescript
// Tracks the currently in-progress query lifecycle
type ActiveQueryState =
  | { phase: 'idle' }
  | { phase: 'submitting' }                       // POST in flight
  | { phase: 'polling'; jobId: string }            // async job polling
  | { phase: 'complete'; result: QueryResult }
  | { phase: 'clarification'; payload: ClarificationPayload }
  | { phase: 'failed'; errorMessage: string }
  | { phase: 'timeout' }
```

---

## State Transitions

```
idle
  → submitting       (admin submits question)
  → complete         (sync result returned)
  → polling          (pending job_id returned)
  → clarification    (clarification response returned)
  → failed           (API error or network error)

polling
  → complete         (job finishes with status: complete)
  → failed           (job finishes with status: failed)
  → timeout          (60s elapsed without terminal state)

complete / clarification / failed / timeout
  → submitting       (admin submits a new question)
  → idle             (admin navigates away — component unmounts)
```

---

## API Endpoints Used

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/v1/content-analytics/query` | Submit natural language question |
| `GET` | `/api/v1/content-analytics/jobs/{job_id}` | Poll async job status |

Both endpoints require `Authorization: Bearer <JWT>` header, provided automatically by the existing `apiFetch` client.

---

## Files Introduced

| File | Purpose |
|------|---------|
| `frontend-admin/src/api/analytics.ts` | `submitQuery()` and `pollJob()` API functions |
| `frontend-admin/src/pages/AnalyticsPage.tsx` | Full page component with all state logic |

## Files Modified

| File | Change |
|------|--------|
| `frontend-admin/src/App.tsx` | Add `<Route path="/analytics" element={<AnalyticsPage />} />` inside `AuthGuard` |
| `frontend-admin/src/components/Sidebar.tsx` | Add Analytics nav item to `navItems` array |
