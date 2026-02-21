# Quickstart: Admin Analytics UI

**Feature**: `013-admin-analytics-ui`
**Date**: 2026-02-21
**Audience**: Developer implementing or verifying the feature

---

## Prerequisites

- Docker Compose stack running (`docker compose up` from `docker/`)
- Analytics events seeded (auto-seeded on first startup; run `docker compose exec backend uv run python -m app.seed.run_seeds` if needed)
- Admin credentials: `admin@ott.test` / `admin123`

---

## What Gets Built

| Component | Location | Description |
|-----------|----------|-------------|
| Analytics API client | `frontend-admin/src/api/analytics.ts` | `submitQuery()` and `pollJob()` using `apiFetch` |
| Analytics page | `frontend-admin/src/pages/AnalyticsPage.tsx` | Full page: prompt, result, history, examples |
| Route addition | `frontend-admin/src/App.tsx` | `/analytics` route inside `AuthGuard` |
| Sidebar link | `frontend-admin/src/components/Sidebar.tsx` | "Analytics" nav item |

---

## Development Workflow

### 1. Verify the Stack is Running

```bash
curl http://localhost:8000/api/v1/health
# {"status": "ok"}
```

### 2. Access the Admin Dashboard

Open `http://localhost:5174` and log in with `admin@ott.test` / `admin123`.

After implementation, "Analytics" should appear in the sidebar.

### 3. Test — Synchronous Query (Simple)

1. Click "Analytics" in the sidebar
2. Type: `Which genres drive SVoD revenue?`
3. Press Enter or click Submit
4. **Expected**: Result appears within 3 seconds with:
   - Summary text (e.g. "Family content leads with 85 play events...")
   - Confidence badge (e.g. "87% confidence", green)
   - Data table with columns: genre, service_type, event_count, completions, completion_rate_pct
   - Applied filters row (service_type: SVoD, region: null, time_period: null)
   - Data freshness and coverage start dates

### 4. Test — Asynchronous Query (Complex)

1. Type: `How does engagement differ between Linear TV and SVoD?`
2. Press Enter or click Submit
3. **Expected**: "Analysing your question…" loading state appears immediately
4. **Expected**: Result auto-populates within ~5 seconds (no manual refresh)

### 5. Test — Clarification Flow

1. Type: `How is content doing?`
2. Press Enter or click Submit
3. **Expected**: A yellow/amber callout appears with a clarifying question such as:
   > "Which aspect of content performance are you interested in? For example: revenue, engagement rate, completion rate, or viewership numbers?"
4. The original question remains editable in the input field

### 6. Test — New Template Queries

These three templates were added after initial implementation:

1. **Search analytics** — Type: `What are users searching for?`
   - **Expected**: Table with `search_query`, `search_count`, `unique_users`, `service_type` columns

2. **Watch abandonment** — Type: `Which titles do users start but not finish?`
   - **Expected**: Table with `title`, `genre`, `play_starts`, `avg_watch_pct`, `completion_rate_pct` — only titles with < 50% completion rate and ≥ 2 play starts

3. **Time-of-day patterns** — Type: `When do users watch content?`
   - **Expected**: Async result (polling spinner), then table with `hour_of_day`, `service_type`, `play_starts`, `completions`, `avg_watch_pct` rows ordered by hour

### 7. Test — Example Queries Panel

1. On the Analytics page (before or after submitting any query), locate the examples panel on the left
2. Click any example question (e.g. "Show regional content preferences in Norway")
3. **Expected**: The input field is populated with that text; the query is NOT submitted automatically

### 8. Test — Session History

1. Submit two different questions (e.g. Q1: "Which genres drive SVoD revenue?", Q2: "Show me top titles by completion rate")
2. Both appear in the history list (reverse chronological order)
3. Click Q1 in the history
4. **Expected**: Q1's result is displayed instantly (no loading state, no network request)

### 9. Test — Auth Guard

```bash
# Navigate directly without logging in
# (open a new incognito window)
http://localhost:5174/analytics
```
**Expected**: Immediately redirected to `/login`.

### 10. Test — Error State

Stop the backend: `docker compose stop backend`

1. Submit any question
2. **Expected**: Error message "Unable to reach the analytics service. Please try again." with a Retry button
3. Restart backend: `docker compose start backend`

---

## Acceptance Checklist

Before marking this feature complete, verify:

- [ ] "Analytics" link visible in admin sidebar
- [ ] Clicking sidebar link navigates to `/analytics` page
- [ ] Simple query returns result inline within 3 seconds
- [ ] Result includes summary, confidence badge, dynamic data table, applied filters, data freshness
- [ ] Complex async query shows loading indicator then auto-resolves
- [ ] Timeout error shown if query takes >60 seconds (hard to test manually — verify code logic)
- [ ] Ambiguous query shows clarification callout, not an error or empty state
- [ ] Input remains editable after clarification response
- [ ] At least 10 example queries visible in examples panel, grouped by category
- [ ] Clicking example populates input without submitting
- [ ] History list shows all queries submitted in session, newest first
- [ ] Clicking history entry restores result instantly (no spinner)
- [ ] Navigating to another page and back clears history
- [ ] Unauthenticated direct URL access redirects to login
- [ ] Empty input: submit button is disabled
- [ ] While query in progress: submit button is disabled
- [ ] Backend unreachable: friendly error message with Retry option
- [ ] Failed job (`status: failed`): error message from backend is displayed
- [ ] Zero-row result: table shows "No data found" empty state, summary still visible
