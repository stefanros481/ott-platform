# Quickstart: Natural Language Content Analytics Agent

**Feature**: `001-content-analytics-agent`
**Date**: 2026-02-21
**Audience**: Developer implementing the feature

---

## Prerequisites

- Docker Compose stack running (`docker compose up` from `docker/`)
- Database migrated to latest (`docker exec backend alembic upgrade head`)
- Seed data loaded (`docker exec backend python seed/run_seeds.py`)
- Admin user exists (seeded as `admin@ott.test` / `admin123`)

---

## What Gets Built

| Component | Location | Description |
|-----------|----------|-------------|
| DB migration 006 | `backend/alembic/versions/006_analytics_events_and_query_jobs.py` | Creates `analytics_events` and `query_jobs` tables |
| SQLAlchemy models | `backend/app/models/analytics.py` | `AnalyticsEvent`, `QueryJob` |
| Analytics router | `backend/app/routers/analytics.py` | `POST /api/v1/analytics/events` |
| Content analytics router | `backend/app/routers/content_analytics.py` | `POST /api/v1/content-analytics/query`, `GET /api/v1/content-analytics/jobs/{job_id}` |
| Analytics service | `backend/app/services/analytics_service.py` | Event ingestion + aggregate query helpers |
| Query engine | `backend/app/services/query_engine.py` | NLP → template match → SQL → QueryResult pipeline |
| Analytics seed | `backend/seed/seed_analytics.py` | Generates 500–1000 synthetic events |
| Client event emitter | `frontend-client/src/api/analytics.ts` | Fire-and-forget `emitEvent()` |
| Client analytics hook | `frontend-client/src/hooks/useAnalytics.ts` | `trackPlay`, `trackPause`, `trackComplete`, `trackBrowse`, `trackSearch` |
| Client integrations | `PlayerPage.tsx`, `BrowsePage.tsx`, `SearchPage.tsx` | Call analytics hook at interaction points |

---

## Development Workflow

### 1. Run Migration

```bash
# Inside running backend container
docker exec -it backend alembic upgrade head
# Confirms: "Running upgrade 005 -> 006, analytics events and query jobs"
```

### 2. Load Seed Data (includes analytics events)

```bash
docker exec -it backend python seed/run_seeds.py
# Output includes: "Seeded 847 analytics events across NO/SE/DK regions"
```

### 3. Test the Query Endpoint

Get an admin token first:

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@ott.test", "password": "admin123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

Submit a simple query (synchronous):

```bash
curl -X POST http://localhost:8000/api/v1/content-analytics/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Which genres drive SVoD revenue?"}'
```

Expected response (status: "complete", result populated):

```json
{
  "status": "complete",
  "result": {
    "summary": "Drama and Thriller genres drive the highest SVoD engagement...",
    "confidence": 0.91,
    "data": [...]
  },
  "job_id": null
}
```

Submit a complex query (async):

```bash
curl -X POST http://localhost:8000/api/v1/content-analytics/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Compare viewing time across Linear and SVoD for each region last quarter"}'

# Returns: { "status": "pending", "job_id": "abc-123...", "result": null }
```

Poll for the result:

```bash
curl http://localhost:8000/api/v1/content-analytics/jobs/abc-123... \
  -H "Authorization: Bearer $TOKEN"

# Returns: { "status": "complete", "result": {...} } after processing
```

Test an ambiguous query:

```bash
curl -X POST http://localhost:8000/api/v1/content-analytics/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "How is content doing?"}'

# Returns: { "status": "clarification", "clarification": { "clarifying_question": "..." } }
```

### 4. Test the Analytics Event Endpoint

```bash
curl -X POST http://localhost:8000/api/v1/analytics/events \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "play_start",
    "title_id": "<any-title-uuid-from-catalog>",
    "service_type": "SVoD",
    "region": "NO",
    "occurred_at": "2026-02-21T20:00:00Z"
  }'

# Returns 201 Created: { "id": "<new-event-uuid>" }
```

---

## Key Implementation Notes

### Query Engine Flow

```
question (string)
  ↓ embed with all-MiniLM-L6-v2 (384-dim vector)
  ↓ cosine similarity vs. pre-loaded template embeddings (pgvector)
  ↓ best match template selected
  ├── similarity < 0.65 → return ClarificationResponse (FR-005)
  ├── similarity ≥ 0.65, simple query → execute SQL, return QueryResult (sync)
  └── similarity ≥ 0.65, complex query → create QueryJob, BackgroundTask, return job_id (async)
  ↓ parameter extraction from question text (region, time_period, service_type keywords)
  ↓ run parameterized SQL against analytics_events + titles
  ↓ render summary from Jinja2 template string
  ↓ return QueryResult
```

### Complexity Classification

A query is classified as **complex** (async) when:
- It uses a cross-dimension template that always runs async: `engagement_by_service`, `cross_service_comparison`, `viewing_by_time_of_day`
- Or it uses a multi-dimension template (`genre_revenue`, `revenue_growth`, `regional_preferences`) with two or more active filters (region + time, region + service, etc.)

Simple queries (one or two aggregate dimensions, no multi-filter overlap) return synchronously.

### Template Embeddings

On backend startup, the query engine service:
1. Loads the 13 predefined `QueryTemplate` objects (hardcoded in `query_engine.py`)
2. Generates embeddings for each template description using the existing `sentence-transformers` model
3. Stores embeddings in memory for the lifetime of the process

No DB storage for templates — consistent with PoC-first principle.

### Analytics Emission (Frontend)

The `useAnalytics` hook wraps `emitEvent()` and is called at three integration points:

```typescript
// PlayerPage.tsx — on stream start
const { trackPlay } = useAnalytics();
// call trackPlay({ titleId, serviceType, region, sessionId }) after stream session created

// PlayerPage.tsx — on unmount/stop
const { trackComplete } = useAnalytics();
// call trackComplete({ ..., durationSeconds, watchPercentage })

// BrowsePage.tsx — on filter change / initial load
const { trackBrowse } = useAnalytics();
// call trackBrowse({ serviceType, region, extraData: { genre_filter } })

// SearchPage.tsx — on debounced search submit
const { trackSearch } = useAnalytics();
// call trackSearch({ serviceType, region, extraData: { query: searchQuery } })
```

All calls are fire-and-forget with silent failure catch — the UI is never blocked.

---

## Known Limitations (PoC)

| Limitation | Reason | Impact |
|-----------|--------|--------|
| BackgroundTask job lost on process restart | No persistent queue | Extremely unlikely in dev; document in error response |
| Template list is hardcoded | PoC — no admin UI for template management | Add new patterns by editing `query_engine.py` |
| No query history | Spec explicitly excludes audit log | Results are ephemeral; re-run query for fresh result |
| Summary uses deterministic templates | No LLM in PoC | Summary quality bounded by template richness |
| Seed data only | No real viewer events in PoC | Agent answers are illustrative, not production-grade |

---

## Running Tests

```bash
# Backend unit tests for query engine and analytics service
docker exec -it backend pytest tests/unit/test_query_engine.py tests/unit/test_analytics_service.py -v

# Integration test: full query flow (requires seeded DB)
docker exec -it backend pytest tests/integration/test_content_analytics.py -v

# Frontend: test analytics hook and emitter
cd frontend-client && npx vitest run src/hooks/useAnalytics.test.ts
```

---

## Acceptance Checklist

Before marking this feature complete, verify:

- [ ] `POST /api/v1/analytics/events` accepts all 5 event types and returns 201
- [ ] Querying with a non-admin token returns 403
- [ ] Simple query ("Which genres drive SVoD revenue?") returns synchronously with `status: "complete"`
- [ ] Complex query returns `status: "pending"` with a `job_id` within 500ms
- [ ] Polling the job ID returns `status: "complete"` with a result within 30 seconds
- [ ] Ambiguous query ("How is content doing?") returns `status: "clarification"` with a question
- [ ] Non-existent or other user's job ID returns 404
- [ ] Failed job has `status: "failed"` with a non-empty `error_message`
- [ ] Regional filter ("Norway only") applied correctly in result data
- [ ] Time-period filter ("last quarter") applied correctly
- [ ] `data_freshness` and `coverage_start` fields populated in all results
- [ ] `data_sources` field lists contributing tables
- [ ] Client play/pause/complete events visible in `analytics_events` table
- [ ] Browse and search events captured with `extra_data`
- [ ] Analytics emission failure does NOT block or error the player/browse/search UI
- [ ] Seed script generates ≥ 500 events covering all regions, service types, and event types
