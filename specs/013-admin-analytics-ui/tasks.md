# Tasks: Admin Analytics UI — Natural Language Query Interface

**Input**: Design documents from `/specs/013-admin-analytics-ui/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, quickstart.md ✓

**Organization**: Tasks are grouped by user story. Each story is independently testable.
**Tests**: Not requested — no test tasks included.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no shared dependencies)
- **[Story]**: Which user story this task belongs to (US1–US5)
- All paths relative to repository root

---

## Phase 1: Setup (Route Wiring)

**Purpose**: Register the new page in the router and sidebar so it is reachable. These two tasks touch different files and can be done in parallel.

- [X] T001 [P] Add `/analytics` route inside the `AuthGuard` block in `frontend-admin/src/App.tsx` — import `AnalyticsPage` and add `<Route path="/analytics" element={<AnalyticsPage />} />`
- [X] T002 [P] Add Analytics nav item to the `navItems` array in `frontend-admin/src/components/Sidebar.tsx` — entry `{ to: '/analytics', label: 'Analytics', icon: AnalyticsIcon }` and add an inline `AnalyticsIcon` SVG (bar-chart style, matching the existing icon style: `h-5 w-5`, `strokeWidth={1.5}`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: TypeScript types, API client functions, and the AnalyticsPage skeleton. Every user story depends on these.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T003 Create `frontend-admin/src/api/analytics.ts` — define all TypeScript interfaces: `QueryRequest`, `QueryResult`, `ClarificationPayload`, `QueryResponse`, `JobStatusResponse`, `HistoryEntry`, `ActiveQueryState` (discriminated union with phases: `idle | submitting | polling | complete | clarification | failed | timeout`) — copy types verbatim from `specs/013-admin-analytics-ui/data-model.md`
- [X] T004 Add `submitQuery(question: string): Promise<QueryResponse>` to `frontend-admin/src/api/analytics.ts` — calls `apiFetch<QueryResponse>('/content-analytics/query', { method: 'POST', body: JSON.stringify({ question }) })` importing `apiFetch` from `@/api/client`
- [X] T005 Add `pollJob(jobId: string): Promise<JobStatusResponse>` to `frontend-admin/src/api/analytics.ts` — calls `apiFetch<JobStatusResponse>(\`/content-analytics/jobs/${jobId}\`)`
- [X] T006 Create `frontend-admin/src/pages/AnalyticsPage.tsx` — scaffold the page with: (a) a two-column layout (`flex gap-6`): left column `w-72 shrink-0` and right column `flex-1`; (b) `question` state (`useState<string>('')`); (c) `activeQueryState` state (`useState<ActiveQueryState>({ phase: 'idle' })`); (d) `QueryInput` section in right column: `<textarea>` bound to `question` and a Submit `<button>`; (e) empty placeholders for left and right panel content; (f) page title "Analytics" with a subheading "Ask a question about your content performance"

**Checkpoint**: Stack running, navigate to `http://localhost:5174/analytics` — page loads with empty two-column layout, sidebar shows "Analytics" link.

---

## Phase 3: User Story 1 — Ask a Question and See Results (Priority: P1) 🎯 MVP

**Goal**: Admin submits a simple question and sees a complete result with summary, confidence badge, dynamic data table, applied filters, and data metadata.

**Independent Test**: Submit "Which genres drive SVoD revenue?" — result card appears within 3 seconds with summary text, a green/amber confidence badge, a table with genre/metrics columns, and a data freshness footer.

- [X] T007 [US1] Add `onSubmit` handler in `frontend-admin/src/pages/AnalyticsPage.tsx` — async function that: (1) sets `activeQueryState` to `{ phase: 'submitting' }`, (2) calls `submitQuery(question)`, (3) on `status: 'complete'` sets `{ phase: 'complete', result }`, (4) on `status: 'clarification'` sets `{ phase: 'clarification', payload: response.clarification }` — do NOT reset `question` state here so the textarea retains the original text for editing, (5) on `status: 'pending'` sets `{ phase: 'polling', jobId: response.job_id }`, (6) on thrown error sets `{ phase: 'failed', errorMessage: err.message }`; wire Submit button `onClick` to `onSubmit`
- [X] T008 [US1] Add `ResultCard` section in the right column of `frontend-admin/src/pages/AnalyticsPage.tsx` — rendered when `activeQueryState.phase === 'complete'`: (a) summary paragraph in a white card with shadow; (b) confidence badge — compute percentage as `Math.round(confidence * 100)`, colour: ≥80 → `bg-green-100 text-green-800`, 65–79 → `bg-amber-100 text-amber-800`, <65 → `bg-red-100 text-red-800`; display as `"87% confidence"` inline chip next to the summary
- [X] T009 [US1] Add dynamic `DataTable` section inside `ResultCard` in `frontend-admin/src/pages/AnalyticsPage.tsx` — derive column headers from `Object.keys(result.data[0] ?? {})`, apply a `formatColumnHeader` helper (replace underscores with spaces, title-case each word); render `<table>` with `<thead>` and `<tbody>`; when `result.data.length === 0` render `<p className="text-gray-500 text-sm">No data found for this query.</p>` instead of the table
- [X] T010 [US1] Add result metadata footer inside `ResultCard` in `frontend-admin/src/pages/AnalyticsPage.tsx` — three rows beneath the data table: (a) **Applied filters**: display `region`, `time_period`, `service_type` values or "–" if null; (b) **Data sources**: join `data_sources` array with ", "; (c) **Coverage**: format `coverage_start` and `data_freshness` as local date strings using `new Date(x).toLocaleDateString()`

**Checkpoint**: US1 complete — sync query returns and displays a full result card.

---

## Phase 4: User Story 2 — Async Query with Progress Indicator (Priority: P2)

**Goal**: Admin submits a complex question; UI shows a loading indicator immediately and auto-resolves when the job completes — no manual refresh needed.

**Independent Test**: Submit "How does engagement differ between Linear TV and SVoD?" — spinner appears with "Analysing your question…", then result auto-populates within ~5 seconds.

- [X] T011 [US2] Add polling `useEffect` in `frontend-admin/src/pages/AnalyticsPage.tsx` — triggered when `activeQueryState.phase === 'polling'`: (a) stores `jobId` from state; (b) starts `setInterval` (2000ms) that calls `pollJob(jobId)` and on `status: 'complete'` clears interval and sets `{ phase: 'complete', result: job.result }`; on `status: 'failed'` clears interval and sets `{ phase: 'failed', errorMessage: job.error_message ?? 'Query failed' }`; (c) returns cleanup function `() => clearInterval(intervalId)` to stop polling on unmount or state change
- [X] T012 [US2] Add 60-second polling timeout in `frontend-admin/src/pages/AnalyticsPage.tsx` — inside the same `useEffect` as T011, add `setTimeout(() => { clearInterval(intervalId); setActiveQueryState({ phase: 'timeout' }) }, 60000)`, cleared in the cleanup function; store both IDs in refs or variables local to the effect
- [X] T013 [US2] Add loading and timeout UI states in the right column of `frontend-admin/src/pages/AnalyticsPage.tsx` — (a) when `phase === 'submitting'`: render a centered spinner SVG with text "Submitting…"; (b) when `phase === 'polling'`: render spinner with "Analysing your question…" and a subtle elapsed-time hint; (c) when `phase === 'timeout'`: render a card with message "The query is taking longer than expected." and a **Retry** button that resets state to `{ phase: 'idle' }` with the question preserved in the input

**Checkpoint**: US2 complete — async queries show loading state and auto-resolve.

---

## Phase 5: User Story 3 — Clarification Flow (Priority: P3)

**Goal**: Ambiguous questions display a clarifying question in a distinct callout; the admin can refine and resubmit without losing their original text.

**Independent Test**: Submit "How is content doing?" — amber callout appears with clarifying question text; input field still contains the original question.

- [X] T014 [US3] Add `ClarificationCallout` UI state in the right column of `frontend-admin/src/pages/AnalyticsPage.tsx` — when `phase === 'clarification'`: render an amber callout box (`bg-amber-50 border border-amber-200 rounded-lg p-4`) containing: (a) a header "Could you be more specific?" with an info icon; (b) the `clarifying_question` text in `text-sm text-amber-900`; (c) the `context` text in `text-xs text-amber-700 mt-1`

**Checkpoint**: US3 complete — ambiguous queries prompt clarification; input remains editable.

---

## Phase 6: User Story 4 — Example Queries Panel (Priority: P4)

**Goal**: A curated panel of 10 example questions (grouped by category) sits in the left column; clicking any example populates the input without submitting.

**Independent Test**: Locate the examples panel, click "Which genres drive SVoD revenue?" — input field is populated with that text; no query is submitted.

- [X] T015 [US4] Add `EXAMPLE_QUERIES` constant at the top of `frontend-admin/src/pages/AnalyticsPage.tsx` — array of 3 category objects, each with `category: string` and `questions: string[]`, totalling 10 questions: **Revenue & Engagement** → ["Which genres drive SVoD revenue?", "What are the top titles by completion rate?", "Show me revenue growth by genre over time"], **Regional & Audience** → ["Show regional content preferences in Norway", "Which content trends with kids profiles?", "Compare viewing patterns across NO, SE, DK"], **Service & Behaviour** → ["How does engagement differ between Linear TV and SVoD?", "What is the Cloud PVR impact on viewing?", "Show me browse-without-watch patterns", "What are the SVoD upgrade signals?"]
- [X] T016 [US4] Add `ExamplesPanel` section in the left column of `frontend-admin/src/pages/AnalyticsPage.tsx` — render each category as a heading (`text-xs font-semibold text-gray-400 uppercase tracking-wider`) followed by a list of question buttons (`<button>` with `text-sm text-left text-gray-700 hover:text-indigo-600 hover:bg-indigo-50 rounded px-2 py-1 w-full`); clicking calls `setQuestion(q)` and focuses the textarea — does NOT call `onSubmit`

**Checkpoint**: US4 complete — examples panel visible and populates input on click.

---

## Phase 7: User Story 5 — Session Query History (Priority: P5)

**Goal**: All submitted questions and their results are listed in reverse chronological order in the left column; clicking an entry instantly restores the result.

**Independent Test**: Submit two questions; both appear in history; click the first — result restores instantly without a loading state.

- [X] T017 [US5] Add `history` state in `frontend-admin/src/pages/AnalyticsPage.tsx` — `const [history, setHistory] = useState<HistoryEntry[]>([])` (import `HistoryEntry` from `@/api/analytics`); after `activeQueryState` reaches a terminal state (complete/clarification/failed/timeout), append a new `HistoryEntry` — generate `id` with `crypto.randomUUID()`, set `question`, `submittedAt: new Date()`, and populate `status`/`result`/`clarification`/`errorMessage` from the resolved state
- [X] T018 [US5] Add `QueryHistory` section in the left column of `frontend-admin/src/pages/AnalyticsPage.tsx`, below `ExamplesPanel` — render when `history.length > 0`: heading "Recent queries", then a scrollable list of entries in reverse order (newest first); each entry is a `<button>` showing the question text (truncated to 1 line with `truncate`) and the submission time using `new Date(entry.submittedAt).toLocaleTimeString()`; clicking an entry calls `setActiveQueryState` to restore the stored result/clarification/failed state and sets `setQuestion(entry.question)` — no API call made

**Checkpoint**: US5 complete — history panel shows queries; clicking restores result instantly.

---

## Phase 8: Polish & Edge Cases

**Purpose**: Harden all error and edge case states across all user stories.

- [X] T019 Disable the Submit button in `frontend-admin/src/pages/AnalyticsPage.tsx` when `question.trim() === ''` OR `activeQueryState.phase === 'submitting'` OR `activeQueryState.phase === 'polling'` — add `disabled` prop and `disabled:opacity-50 disabled:cursor-not-allowed` Tailwind classes
- [X] T020 Add failed-job error UI in `frontend-admin/src/pages/AnalyticsPage.tsx` — when `phase === 'failed'`: render a red error card (`bg-red-50 border border-red-200`) showing `errorMessage` text and a **Retry** button that resets state to `{ phase: 'idle' }` with the question preserved in the input (does not resubmit automatically)
- [X] T021 Wrap `submitQuery()` call in `frontend-admin/src/pages/AnalyticsPage.tsx` in a `try/catch` — catch `ApiError` (import from `@/api/client`) and generic `Error`; for network failures set `{ phase: 'failed', errorMessage: 'Unable to reach the analytics service. Please try again.' }`; the Retry button in the failed card resets state to `{ phase: 'idle' }` with the question preserved in the input
- [X] T022 Add idle state prompt in the right column of `frontend-admin/src/pages/AnalyticsPage.tsx` — when `phase === 'idle'`: render a centered placeholder (`text-gray-400 text-sm`) with a search icon and text "Type a question above to get started — or pick an example from the left."

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately; T001 and T002 are parallel
- **Phase 2 (Foundational)**: Depends on Phase 1 — blocks all user stories; T003 → T004 → T005 (sequential, same file), T006 can start after T003
- **Phase 3–7 (User Stories)**: Depend on Phase 2 completion; each story builds on the existing `AnalyticsPage.tsx` and adds new state/UI — execute sequentially P1 → P2 → P3 → P4 → P5
- **Phase 8 (Polish)**: Execute after all user story phases are complete

### Story Dependencies

- **US1 (P1)**: Requires Phase 2 complete — the core sync result flow
- **US2 (P2)**: Requires US1 complete — extends the state machine with polling
- **US3 (P3)**: Requires US1 complete — extends onSubmit with clarification branch (parallel with US2)
- **US4 (P4)**: Requires Phase 2 complete — adds left-panel examples, independent of US1–US3
- **US5 (P5)**: Requires US1+US2+US3 complete — history needs terminal states from all flows

### Parallel Opportunities

- T001 ↔ T002 — different files (App.tsx vs Sidebar.tsx)
- After Phase 2: US2 (T011–T013) ↔ US3 (T014) — both extend same file but different state branches; best done sequentially to avoid merge conflicts
- US4 (T015–T016) — can start immediately after Phase 2, independent of US1–US3

---

## Parallel Example: Phase 1

```
T001: Add /analytics route in App.tsx
T002: Add Analytics sidebar item in Sidebar.tsx
  → Both in parallel (different files)
```

---

## Implementation Strategy

### MVP (User Story 1 Only — ~6 tasks)

1. Complete Phase 1: T001, T002
2. Complete Phase 2: T003 → T004 → T005 → T006
3. Complete Phase 3: T007 → T008 → T009 → T010
4. **STOP and VALIDATE**: Submit "Which genres drive SVoD revenue?" — full result card visible
5. Demo-able at this point

### Incremental Delivery

1. Phase 1 + 2 → Analytics page reachable (empty)
2. + Phase 3 (US1) → Sync query results working (MVP!)
3. + Phase 4 (US2) → Async jobs handled
4. + Phase 5 (US3) → Clarification flow works
5. + Phase 6 (US4) → Example queries panel
6. + Phase 7 (US5) → Session history
7. + Phase 8 → All edge cases hardened

---

## Notes

- All changes are in `frontend-admin/src/` — no backend changes, no new npm packages
- `apiFetch` from `@/api/client` handles JWT auth and 401 token refresh automatically
- Dynamic table columns are derived at render time from `Object.keys(result.data[0] ?? {})` — no hardcoding
- History is React `useState` — clears automatically on navigation (component unmount)
- Polling `useEffect` cleanup function stops the interval on navigation — no memory leaks
