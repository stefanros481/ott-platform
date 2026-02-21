# Tasks: Natural Language Content Analytics Agent

**Input**: Design documents from `/specs/001-content-analytics-agent/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓, quickstart.md ✓

**Tests**: Not requested — spec.md does not require TDD. Tasks cover implementation only.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[US#]**: Maps to user story from spec.md
- Exact file paths included in all descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create new files and skeletons so all team members/phases can work in parallel without merge conflicts.

- [X] T001 Create `backend/app/models/analytics.py` with `AnalyticsEvent` and `QueryJob` SQLAlchemy models using `Mapped` types per data-model.md (UUID PKs, all columns, FK constraints, no relationships to other models yet)
- [X] T002 [P] Create `backend/app/schemas/analytics.py` with all Pydantic models from data-model.md: `AnalyticsEventCreate`, `QueryRequest`, `QueryResult`, `ClarificationResponse`, `QueryResponse` (with `clarification: ClarificationResponse | None = None` field), `JobStatusResponse` — this file must exist before any router can import these types
- [X] T003 [P] Create `backend/app/services/analytics_service.py` with module docstring and empty function stubs: `ingest_event()`, `execute_template_query()`, `get_data_coverage()`
- [X] T004 [P] Create `backend/app/services/query_engine.py` with module docstring, `QueryTemplate` dataclass, `QueryParameters` dataclass (with `regions: list[str] | None` — not `region: str | None`), and empty function stubs: `match_template()`, `extract_parameters()`, `classify_complexity()`, `resolve_query()`
- [X] T005 [P] Verify `jinja2` is present in `backend/pyproject.toml` — run `uv add jinja2` if absent; confirm `jinja2` appears in `pyproject.toml` and `uv.lock` before T018 imports it

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Database schema and router registration — must be complete before any user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T006 Create `backend/alembic/versions/006_analytics_events_and_query_jobs.py` — Alembic migration with `revision="006"`, `down_revision="005"`; `upgrade()` creates `analytics_events` table (all columns + CHECK constraints per data-model.md) and `query_jobs` table (all columns + CHECK constraint), plus all 5 indexes; `downgrade()` drops both tables
- [X] T007 Update `backend/app/models/__init__.py` to import and export `AnalyticsEvent` and `QueryJob` so Alembic picks them up via `target_metadata`
- [X] T008 [P] Create `backend/app/routers/analytics.py` — FastAPI `APIRouter(prefix="/analytics", tags=["analytics"])` with a placeholder `POST /events` route that returns `{"id": str(uuid4())}` with status 201 (to be replaced in T013)
- [X] T009 [P] Create `backend/app/routers/content_analytics.py` — FastAPI `APIRouter(prefix="/content-analytics", tags=["content-analytics"])` with placeholder `POST /query` returning `{}` and `GET /jobs/{job_id}` returning `{}` (to be replaced in T028, T029)
- [X] T010 Register both new routers in `backend/app/main.py` — add `app.include_router(analytics_router, prefix="/api/v1")` and `app.include_router(content_analytics_router, prefix="/api/v1")` in the lifespan/startup section alongside the 9 existing routers

**Checkpoint**: Run `docker compose up` → confirm `/api/v1/analytics/events` and `/api/v1/content-analytics/query` respond (even with placeholder bodies). Run `alembic upgrade head` → confirm migration 006 applies without errors.

---

## Phase 3: User Story 5 — Client Emits Analytics Events (Priority: P1)

**Goal**: Backend accepts analytics events from the client; frontend-client emits play/pause/complete/browse/search events fire-and-forget; seed data provides 500–1000 synthetic events for demo.

**Independent Test**: POST an event via curl (see quickstart.md) → confirm 201 and row in `analytics_events` table. Perform a play action in the client app → confirm event row appears.

- [X] T011 [US5] Implement `ingest_event(db: AsyncSession, user_id: UUID, payload: AnalyticsEventCreate) -> AnalyticsEvent` in `backend/app/services/analytics_service.py` — creates `AnalyticsEvent` ORM instance, `db.add()`, `await db.commit()`, `await db.refresh()`, returns model instance
- [X] T012 [US5] Implement `POST /api/v1/analytics/events` in `backend/app/routers/analytics.py` — requires `CurrentUser` dependency (not AdminUser — any authenticated user can emit events); imports `AnalyticsEventCreate` from `backend/app/schemas/analytics.py`; calls `analytics_service.ingest_event()`; returns `{"id": str(event.id)}` with HTTP 201; wraps any DB error in HTTP 500 (client must handle silently per FR-011)
- [X] T013 [US5] Create `backend/seed/seed_analytics.py` — idempotent seed script: checks `SELECT COUNT(*) FROM analytics_events` and skips if > 0; generates 500–1000 `AnalyticsEvent` records spanning the last 90 days; distributes across all 5 event types (play_start, play_pause, play_complete, browse, search), 3 regions (NO, SE, DK), all 6 service types (Linear, VoD, SVoD, TSTV, Catch_up, Cloud_PVR); seeds realistic patterns: Drama/Thriller → high SVoD completion, Sports → weekend Linear, browse-to-watch ratio higher for SVoD; includes kids profile events for `trending_by_profile_type` template; uses real title IDs and profile IDs from existing seeded data
- [X] T014 [US5] Update `backend/seed/run_seeds.py` to import and call `seed_analytics` after the `seed_users` step (analytics events require user and profile IDs); add log output: `"Seeded N analytics events"`
- [X] T015 [P] [US5] Create `frontend-client/src/api/analytics.ts` — define `AnalyticsEventPayload` interface matching `AnalyticsEventCreate` schema; export `async function emitEvent(event: AnalyticsEventPayload): Promise<void>` that calls `apiFetch<void>('/analytics/events', { method: 'POST', body: JSON.stringify(event) })` inside a `try/catch` block that swallows all errors silently (FR-011)
- [X] T016 [P] [US5] Create `frontend-client/src/hooks/useAnalytics.ts` — custom hook; the `region` field is NOT defaulted on the frontend — instead, omit it from frontend payload and derive it server-side from the authenticated user's profile or account data (set to `"NO"` only as a DB-level default if no region data exists); exports `trackPlay(titleId, serviceType, sessionId)`, `trackPause(titleId, serviceType, sessionId)`, `trackComplete(titleId, serviceType, sessionId, durationSeconds, watchPercentage)`, `trackBrowse(serviceType, extraData?)`, `trackSearch(query, serviceType)` — each constructs the correct `AnalyticsEventPayload` and calls `emitEvent()` without awaiting; the `region` field is populated from the user's account context if available, otherwise omitted and defaulted server-side
- [X] T017 [US5] Integrate `useAnalytics` into `frontend-client/src/pages/PlayerPage.tsx` — call `trackPlay()` after stream session is created (existing `useEffect` on mount), `trackPause()` when stream session ends mid-playback, `trackComplete()` on unmount when `completed` is true with `durationSeconds` from session data and estimated `watchPercentage`
- [X] T018 [US5] Integrate `useAnalytics` into `frontend-client/src/pages/BrowsePage.tsx` — call `trackBrowse()` on initial page load and on every genre/type filter change, passing current filter values in `extraData: { genre_filter, type_filter }` and using the active service type context
- [X] T019 [US5] Integrate `useAnalytics` into `frontend-client/src/pages/SearchPage.tsx` — call `trackSearch()` inside the existing debounced search handler when a search is submitted, passing the search query string in `extraData: { query }`

**Checkpoint**: Re-seed the database (T013–T014). Play a title in the client. Confirm row in `analytics_events`. Browse and search. Confirm additional rows. Confirm that intentionally breaking the analytics endpoint does not cause any error in the player or browse UI.

---

## Phase 4: User Story 1 — Ask a Plain-Language Content Question (Priority: P1) 🎯 MVP

**Goal**: Admin user POSTs a natural language question and receives a structured `QueryResult` with ranked data, a plain-English summary, and confidence score — either synchronously (<2s) or via async job ID (<500ms, result within 30s).

**Independent Test**: `POST /api/v1/content-analytics/query` with `{"question": "Which genres drive SVoD revenue?"}` → response has `status: "complete"` and populated `result` with `summary`, `confidence`, `data`, `data_sources` (see quickstart.md).

- [X] T020 [US1] Implement all 10 `QueryTemplate` definitions in `backend/app/services/query_engine.py` — define as a module-level `TEMPLATES: list[QueryTemplate]` list; each template has `id`, `name`, `description`, parameterized SQL against `analytics_events LEFT JOIN titles ON analytics_events.title_id = titles.id` with optional `:regions`, `:start_date`, `:end_date`, `:service_type` bind parameters, and a `summary_tpl` Jinja2 string; cover all 10 patterns from research.md: genre_revenue, trending_by_profile_type (kids vs adult via profiles.is_kids JOIN — replaces the unimplementable demographic template), pvr_impact, svod_upgrade_drivers, regional_preferences, engagement_by_service, top_titles, revenue_growth, content_browse_behavior, cross_service_comparison
- [X] T021 [US1] Add embedding initialization in `backend/app/services/query_engine.py` — import the shared `get_sentence_transformer()` getter from the existing recommendations service (e.g., `backend/app/services/recommendation_service.py`) to reuse the already-loaded `all-MiniLM-L6-v2` model instance; do NOT instantiate a new `SentenceTransformer(...)` — two copies double container memory; compute 384-dim embeddings for all template descriptions using the shared instance; store as numpy arrays on `QueryTemplate.embedding`; log: `"Query engine: loaded N templates with embeddings"`
- [X] T022 [US1] Implement `extract_parameters(question: str) -> QueryParameters` in `backend/app/services/query_engine.py` — keyword matching on question text: region keywords (Norway→["NO"], Sweden→["SE"], Denmark→["DK"], Nordics→["NO","SE","DK"] — always produces `regions: list[str]`, never a single string); service type keywords (Linear, VoD, SVoD, TSTV, Catch-up, Cloud PVR — case-insensitive); time period keywords (last quarter, this month, last month, last year, YYYY literal); resolve time periods to `start_date`/`end_date` relative to `datetime.utcnow()`
- [X] T023 [US1] Implement `match_template(question: str) -> tuple[QueryTemplate, float]` in `backend/app/services/query_engine.py` — embed question using the shared model; compute cosine similarity against all template embeddings using `numpy`; return `(best_template, similarity_score)` tuple
- [X] T024 [US1] Implement `execute_template_query(db: AsyncSession, template: QueryTemplate, params: QueryParameters) -> QueryResult` in `backend/app/services/analytics_service.py` — build SQLAlchemy `text()` query from template SQL; when `params.regions` is non-null use `WHERE analytics_events.region = ANY(:regions)` with a list bind; apply other non-null params as bind parameters; execute via `await db.execute()`; compute `data_freshness = MAX(occurred_at)` and `coverage_start = MIN(occurred_at)` from `analytics_events`; render `summary` string from template's Jinja2 `summary_tpl` using top result values; set `confidence` from the similarity score passed in (not hardcoded); return `QueryResult`
- [X] T025 [US1] Implement `classify_complexity(template: QueryTemplate, params: QueryParameters) -> bool` in `backend/app/services/query_engine.py` — returns `True` (complex/async) when the template involves GROUP BY on >2 dimensions AND at least 2 non-null parameters are provided; returns `False` (simple/sync) otherwise
- [X] T026 [US1] Implement async job path in `backend/app/services/query_engine.py` — `create_and_schedule_job(db, user_id, question, template, params, similarity_score, background_tasks) -> QueryJob`: insert `QueryJob` row with `status="pending"`; add background task wrapped in `try/except Exception as e` that calls `execute_template_query()` and updates job to `status="complete", result=result_json, completed_at=now()` on success, or `status="failed", error_message=str(e), completed_at=now()` on any exception — job must NEVER remain in `pending` indefinitely
- [X] T027 [US1] Implement `POST /api/v1/content-analytics/query` in `backend/app/routers/content_analytics.py` — requires `AdminUser` dependency; imports `QueryRequest`, `QueryResponse` from `backend/app/schemas/analytics.py`; calls `match_template()` → `extract_parameters()` → `classify_complexity()`; if simple: calls `execute_template_query()`, returns `QueryResponse(status="complete", result=result)` HTTP 200; if complex: calls `create_and_schedule_job()`, returns `QueryResponse(status="pending", job_id=job.id)` HTTP 202
- [X] T028 [US1] Implement `GET /api/v1/content-analytics/jobs/{job_id}` in `backend/app/routers/content_analytics.py` — requires `AdminUser` dependency; imports `JobStatusResponse` from `backend/app/schemas/analytics.py`; queries `query_jobs` WHERE `id = job_id AND user_id = current_user.id`; returns HTTP 404 if not found; returns `JobStatusResponse` with current status, timestamps, `result` (parsed from JSONB when complete), and `error_message` (when failed)

**Checkpoint**: With seeded analytics data, submit "Which genres drive SVoD revenue?" → verify `status: "complete"` with non-empty `data`. Submit a complex cross-join question → verify `status: "pending"` with `job_id`, then poll and get `status: "complete"` within 30s.

---

## Phase 5: User Story 2 — Filter Results by Region or Time Period (Priority: P2)

**Goal**: Questions mentioning a region or time period return data scoped to those filters; multi-filter questions apply both constraints; the response clearly states which filters were applied.

**Independent Test**: `POST /query` with `{"question": "Show me SVoD preferences in Norway last month"}` → verify `applied_filters.region == "NO"`, `applied_filters.time_period == "last_month"`, and result `data` rows are from Norwegian users only.

- [X] T029 [US2] Extend `extract_parameters()` in `backend/app/services/query_engine.py` to handle compound region mentions: "Norway, Sweden, Denmark" and "Nordics" expand to `regions=["NO","SE","DK"]` (always a list, never a scalar — consistent with `QueryParameters.regions: list[str] | None` in data-model.md); single mention "Norway" → `regions=["NO"]`; relative time "last quarter" resolves to most recent calendar quarter boundaries; "2025" resolves to full-year range; both filters can be non-null simultaneously
- [X] T030 [US2] Update `execute_template_query()` in `backend/app/services/analytics_service.py` — when `params.regions` is non-null, add `AND analytics_events.region = ANY(:regions)` to WHERE clause (PostgreSQL array binding); when `params.start_date` is non-null, add `AND analytics_events.occurred_at >= :start_date AND analytics_events.occurred_at < :end_date`; when both filters present, apply both; when filters are null, query is unfiltered (all regions/all time)
- [X] T031 [US2] Populate `applied_filters` correctly in `QueryResult` from `execute_template_query()` — include `regions: list | null`, `time_period: str | null`, `service_type: str | null`; when no region filter was applied, set `regions: null` and include phrase "results for all regions" in the summary string
- [X] T032 [US2] Add empty-result handling in `execute_template_query()` in `backend/app/services/analytics_service.py` — if filtered query returns zero rows, raise a domain exception `NoDataError(filter_description)` caught in the router and returned as `QueryResponse(status="complete", result=QueryResult(summary="No data available for [filter values]", data=[], confidence=similarity_score, data_freshness=..., coverage_start=...))` — confidence comes from the template similarity score, NOT hardcoded to 1.0

**Checkpoint**: Submit "Regional content preferences in Norway" → `data` rows have `region=NO` only. Submit "Trending shows last month" → `data` rows have `occurred_at` within last calendar month. Submit question with no region → `applied_filters.region` is null and summary says "all regions".

---

## Phase 6: User Story 3 — Clarification for Ambiguous Questions (Priority: P2)

**Goal**: Questions below the similarity confidence threshold trigger a single targeted clarifying question; partially ambiguous questions return unfiltered results with a note.

**Independent Test**: `POST /query` with `{"question": "How is content doing?"}` → verify response has `status: "clarification"` and `clarification.clarifying_question` is a non-empty string (not an error).

- [X] T033 [US3] Implement clarification trigger in `backend/app/services/query_engine.py` — in `resolve_query()`, after `match_template()`: if `similarity_score < 0.65`, do not execute SQL; build `ClarificationResponse` with a context-specific `clarifying_question` (e.g., if question contains "content" but no metric keyword: "Which aspect of content performance are you interested in? For example: revenue, engagement rate, completion rate, or viewership numbers?"); multi-part questions (containing "AND" or multiple "?" characters) that produce low confidence should trigger: "Your question has multiple parts — which would you like answered first?"; return special sentinel that signals clarification needed
- [X] T034 [US3] Update `POST /api/v1/content-analytics/query` in `backend/app/routers/content_analytics.py` to handle the clarification sentinel from `resolve_query()` — return HTTP 200 with `QueryResponse(status="clarification", clarification=ClarificationResponse(...), result=None, job_id=None)` (not HTTP 400 or 422); imports `ClarificationResponse` from `backend/app/schemas/analytics.py`
- [X] T035 [US3] Add out-of-domain guard in `backend/app/services/query_engine.py` — if `similarity_score < 0.35` (absolute minimum), the question is entirely outside platform scope (e.g., "social media engagement"); return a distinct `ClarificationResponse` with `clarifying_question` stating: "This metric isn't available in the platform's analytics data. The agent can answer questions about: viewing engagement, completion rates, content preferences, regional trends, and service type comparisons." (FR-006)

**Checkpoint**: Submit "How is content doing?" → `status: "clarification"`. Submit "social media engagement" → `status: "clarification"` with out-of-scope message. Submit "what's popular in Norway" (clear metric, no region ambiguity) → `status: "complete"` with `applied_filters.region: "NO"`.

---

## Phase 7: User Story 4 — Cross-Service Query (Priority: P3)

**Goal**: Questions spanning multiple service types return side-by-side comparison data with separate rows per service type; complex cross-service queries route to the async job path.

**Independent Test**: `POST /query` with `{"question": "What's the engagement rate by content type, Linear vs VoD?"}` → verify response `data` array contains separate rows for "Linear" and "VoD" service types.

- [X] T036 [US4] Verify the `engagement_by_service` and `cross_service_comparison` query templates in `backend/app/services/query_engine.py` include SQL that GROUP BY `analytics_events.service_type` producing one row per service type; confirm `cross_service_comparison` template SQL joins `analytics_events` twice for Linear vs VoD direct comparison; confirm `pvr_impact` template SQL compares `Cloud_PVR` event counts against `Linear` baseline
- [X] T037 [US4] Update `classify_complexity()` in `backend/app/services/query_engine.py` — cross-service templates (`engagement_by_service`, `cross_service_comparison`) are always classified as complex (async) since they aggregate across all service types simultaneously; single-service templates remain simple (sync) unless combined with multiple filters
- [X] T038 [US4] Confirm `QueryResult.data_sources` in `backend/app/services/analytics_service.py` lists both `"analytics_events"` and `"titles"` for all templates that JOIN titles; list only `"analytics_events"` for count-only templates that don't touch titles — ensures FR-007 (which data sources contributed) is met for cross-service results

**Checkpoint**: Submit "Engagement rate by content type Linear vs VoD" → verify async path (job returned), poll → `data` has rows for both "Linear" and "VoD". Submit "PVR impact on viewing" → result includes Cloud_PVR data alongside Linear baseline data.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Edge cases, data quality fields, and final validation across all stories.

- [X] T039 [P] Add `data_freshness` and `coverage_start` computation to `backend/app/services/analytics_service.py` — always query `SELECT MAX(occurred_at), MIN(occurred_at) FROM analytics_events` before executing template SQL; include both timestamps in every `QueryResult` regardless of whether filters were applied (FR-008); use `coverage_start` in summary template to caveat sparse data: "Based on events captured since {coverage_start}"
- [X] T040 Verify the 10 query templates all produce non-empty results against seeded data — add assertions/comments in `backend/seed/seed_analytics.py` confirming seed distribution covers each template's use case (e.g., at least 50 Cloud_PVR events for pvr_impact template, at least 100 SVoD events for genre_revenue template, kids-profile events for trending_by_profile_type template)
- [X] T041 [P] Handle `alembic/env.py` import — confirm `backend/alembic/env.py` imports from `app.models` in a way that includes the new `analytics.py` module; if models are discovered via `app.models.__init__` re-exports, T007 is sufficient; otherwise add explicit import of `AnalyticsEvent, QueryJob` to `env.py`
- [X] T042 Run quickstart.md acceptance checklist — manually verify all 16 acceptance criteria listed in `specs/001-content-analytics-agent/quickstart.md` pass against a freshly seeded database; note any failing items and fix before marking complete
- [X] T043 [P] Update `backend/app/main.py` docstring / router registration comment to document the two new routers (`analytics`, `content_analytics`) consistent with the existing comment style for the 9 existing routers

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately; T002, T003, T004, T005 can run in parallel (T002 depends on T001 indirectly for model types; T003–T005 are independent)
- **Foundational (Phase 2)**: Depends on Phase 1; T008 and T009 can run in parallel; T010 depends on T008 and T009
- **US5 (Phase 3)**: Depends on Phase 2 completion; T015 and T016 (frontend) can run in parallel with T011–T014 (backend)
- **US1 (Phase 4)**: Depends on Phase 2 completion; T020–T023 can run after Phase 2; T024 depends on T020–T023; T027–T028 depend on T024–T026
- **US2 (Phase 5)**: Depends on Phase 4 (extends query engine + execute function); T029–T032 sequentially extend T022 and T024
- **US3 (Phase 6)**: Depends on Phase 4 (extends `resolve_query` / router); T033–T035 run sequentially
- **US4 (Phase 7)**: Depends on Phase 4 (verifies and extends templates + classifier); T036–T038 sequentially
- **Polish (Phase 8)**: Depends on all user story phases; T039, T041, T043 can run in parallel; T040 and T042 run sequentially after seed and implementation are confirmed

### User Story Dependencies

- **US5 (P1)**: Can start after Phase 2 — no dependencies on other user stories
- **US1 (P1)**: Can start after Phase 2 — depends on US5's analytics data only at demo time (seed covers it)
- **US2 (P2)**: Extends US1 — builds on `extract_parameters()` and `execute_template_query()`
- **US3 (P2)**: Extends US1 — adds logic to the `resolve_query()` path in query_engine
- **US4 (P3)**: Extends US1 — verifies/extends template definitions and complexity classifier

### Within Each User Story

- Backend service tasks before router tasks
- Schema file (T002) must exist before any router task imports schema types
- Frontend hook (T016) before page integration tasks (T017–T019)

### Parallel Opportunities

| Parallel Group | Tasks |
|---------------|-------|
| Phase 1 parallel | T002, T003, T004, T005 |
| Phase 2 parallel | T008, T009 |
| Phase 3 frontend ‖ backend | T015, T016 alongside T011–T014 |
| Phase 4 engine foundation | T020, T021, T022 |
| Phase 8 polish | T039, T041, T043 |

---

## Parallel Example: User Story 5

```
# Backend analytics foundation (sequential within stream):
T011 → T012 → T013 → T014

# Frontend emission layer (can run in parallel with T011-T014):
T015 (analytics.ts emitter)
T016 (useAnalytics hook)

# Page integrations (sequential after T016):
T017 → T018 → T019
```

---

## Implementation Strategy

### MVP (User Stories 5 + 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks everything)
3. Complete Phase 3: US5 (Client Emits Analytics Events) + seed data
4. Complete Phase 4: US1 (Plain-Language Query — sync + async path)
5. **STOP and VALIDATE**: Submit 5 test questions, verify results match quickstart.md
6. Demo to stakeholders — agent is queryable against seeded data

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US5 → Analytics data flows in from client; seed covers initial demo
3. US1 → Core query agent works end-to-end *(MVP delivered)*
4. US2 → Regional and time-period filtering adds practical value
5. US3 → Ambiguity handling makes the agent more user-friendly
6. US4 → Cross-service comparisons complete the query pattern coverage
7. Polish → Edge cases hardened; quickstart checklist passes

### Suggested MVP Scope

For the first deployable/demoable increment: **Phase 1 + Phase 2 + Phase 3 + Phase 4** (T001–T028). This delivers:
- Analytics event ingestion (backend + client)
- Synthetic seed data (500–1000 events)
- Natural language query → structured result (sync + async)
- 10 query templates covering all required patterns (FR-004)
- Admin-only access (FR-009)

---

## Notes

- `[P]` tasks = different files, no blocking dependencies — safe to assign to separate developers or run as parallel subagents
- No tests are included — add test tasks explicitly if TDD is required
- Commit after each phase checkpoint
- Verify migration 006 applies cleanly before starting Phase 3
- The `all-MiniLM-L6-v2` model is already pulled into the Docker image by the recommendations feature — no new model download required
- `jinja2` dependency is explicitly handled in T005 (Phase 1 setup)
- Schema file (`backend/app/schemas/analytics.py`) is created in T002 — must precede all router implementation tasks
- `trending_by_profile_type` template replaces the original `trending_by_demographic` — uses `profiles.is_kids` JOIN since no age demographic data exists in the schema
- `QueryParameters.regions` is always a `list[str]` (never a scalar string), consistent with data-model.md and PostgreSQL `ANY(:regions)` binding

**Total Tasks**: 43
**Tasks per user story**: Setup(5) + Foundational(5) + US5(9) + US1(9) + US2(4) + US3(3) + US4(3) + Polish(5) = 43
**Parallel opportunities**: 5 groups identified
