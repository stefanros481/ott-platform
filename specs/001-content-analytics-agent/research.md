# Research: Natural Language Content Analytics Agent

**Feature**: `001-content-analytics-agent`
**Date**: 2026-02-21
**Phase**: 0 — Research & Decision Resolution

---

## 1. NLP Query Resolution Approach

**Question**: How does the agent convert a natural language question into a SQL query without cloud AI services?

### Options Evaluated

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| A — Embedding similarity (pgvector) | Embed query with all-MiniLM-L6-v2; find closest predefined query template via cosine similarity | Uses existing infrastructure; no new deps; handles natural language variation | Bounded to predefined templates; can't handle truly novel queries |
| B — Regex/keyword matching | Pattern match on keywords (genre, revenue, region, etc.) | Simple to implement | Brittle; fails on paraphrase; hard to extend |
| C — Local LLM (Ollama) | Run a local LLM to generate SQL | Flexible, handles novel queries | Violates Docker Compose constraint (GPU/memory); new service needed |
| D — Cloud LLM (Anthropic/OpenAI) | Call external API | Best NL understanding | Violates no-cloud-deps constraint |

**Decision**: **Option A — Embedding similarity with predefined query templates**

**Rationale**: The existing `sentence-transformers` `all-MiniLM-L6-v2` model is already loaded in the backend for content recommendations. pgvector with HNSW index is already running. Reusing this infrastructure for query resolution requires zero new dependencies and zero new Docker services. The spec requires "at least 10 distinct query patterns" — these are well-bounded and can be fully covered by predefined templates. A cosine similarity threshold controls the clarification boundary: similarity < 0.65 triggers a clarification request rather than a guess.

**Model sharing**: The recommendations service loads `all-MiniLM-L6-v2` into a module-level singleton. The query engine must reuse this instance (import and call the same getter) rather than loading a second copy. Loading two copies doubles peak memory usage inside the backend container.

**Alternatives Rejected**:
- Option C (Ollama): Requires a new Docker service with significant GPU/CPU overhead; violates Principle II (Monolithic Simplicity) and IV (Docker Compose as Truth).
- Option D (Cloud LLM): Violates Principle IV (no cloud dependencies) explicitly.
- Option B (Regex): Insufficient for the natural language variation described in user stories; fails on paraphrases like "which service type earns most?" vs. "show me revenue by service".

### Template Design

Query templates are seeded at startup into an in-memory list (loaded once by the query engine service). Each template has:
- A human-readable name and description
- A parameterized SQL query against `analytics_events` + `titles`
- Accepted parameters: `region` (optional), `time_period` (optional), `service_type` (optional)
- A pre-computed embedding (384-dimensional, all-MiniLM-L6-v2)

**10 required query patterns covered by templates**:

| # | Template Name | Example Question |
|---|--------------|-----------------|
| 1 | genre_revenue | "Which genres drive SVoD revenue?" |
| 2 | trending_by_profile_type | "What are trending shows for kids vs adults?" |
| 3 | pvr_impact | "How does Cloud PVR impact viewing?" |
| 4 | svod_upgrade_drivers | "What content drives SVoD upgrades?" |
| 5 | regional_preferences | "Regional content preferences in Nordics?" |
| 6 | engagement_by_service | "Engagement rate by content type Linear vs VoD?" |
| 7 | top_titles | "Which titles have the highest completion rate?" |
| 8 | revenue_growth | "Which genres had highest revenue growth last quarter?" |
| 9 | content_browse_behavior | "What content do users browse but not watch?" |
| 10 | cross_service_comparison | "Compare viewing time across Linear and SVoD" |

---

## 2. Async Job Processing Design

**Question**: How should complex queries be processed asynchronously without an external queue?

### Options Evaluated

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| A — FastAPI BackgroundTasks | Process job in FastAPI background task after returning 202 | Zero new deps; runs in same process | No retry; dies if process restarts mid-job |
| B — Redis + RQ/Celery | Dedicated worker queue | Production-grade; retry support | New service (violates Docker Compose simplicity for PoC) |
| C — PostgreSQL LISTEN/NOTIFY | DB-driven job dispatch | Persistent | Complex; harder than BackgroundTasks |

**Decision**: **Option A — FastAPI `BackgroundTasks`**

**Rationale**: This is a PoC with a single admin user running queries. `BackgroundTasks` is built into FastAPI — no new dependencies. The job record is persisted in PostgreSQL (`query_jobs` table), so the caller can poll. If the background task fails, the job status is set to `failed` with a human-readable error. For the PoC scale, process restart during a query is an acceptable edge case (documented in quickstart).

**Complexity boundary**: Query is classified as "complex" if the nearest template similarity score is high but the query contains multiple dimension cross-joins (detected via parameter extraction). Simple queries (single aggregation, one filter) execute synchronously. All async jobs resolve within 30s per spec SC-001.

**Alternatives Rejected**:
- Option B: Adds Celery/Redis worker — violates PoC-First Quality (Principle I) and Monolithic Simplicity (Principle II). Redis is already in Docker Compose but adding a Celery worker container is out of scope.

---

## 3. Analytics Event Schema

**Question**: What is the minimal event schema that satisfies FR-010 while fitting the existing PostgreSQL schema patterns?

### Decision: Single `analytics_events` table (migration 006)

**Fields**:

| Field | Type | Notes |
|-------|------|-------|
| id | UUID PK | Standard, consistent with all models |
| event_type | VARCHAR(20) | Enum: play_start, play_pause, play_complete, browse, search |
| title_id | UUID (nullable) | References titles.id; null for browse/search without specific title |
| service_type | VARCHAR(20) | Linear, VoD, SVoD, TSTV, Catch_up, Cloud_PVR |
| user_id | UUID FK → users.id | Ties event to user account |
| profile_id | UUID (nullable) | References profiles.id; null if no profile selected |
| region | VARCHAR(10) | ISO country code (e.g., "NO", "SE", "DK") |
| occurred_at | TIMESTAMPTZ | When the event happened (client-provided, not server receipt time) |
| created_at | TIMESTAMPTZ | Server receipt time (server_default=func.now()) |
| session_id | UUID (nullable) | Groups play_start → play_pause → play_complete events |
| duration_seconds | INTEGER (nullable) | Populated for play_complete events |
| watch_percentage | SMALLINT (nullable) | 0-100, populated for play_complete events |
| extra_data | JSONB (nullable) | Future extensibility (search query text, genre filter, etc.) |

**Indexes**: `(user_id, occurred_at)`, `(service_type, occurred_at)`, `(region, occurred_at)`, `(title_id)` — supports the 10 query patterns.

**Rationale**: Single table keeps migration simple (consistent with 001-005 pattern). Nullable fields handle events that don't carry all attributes (browse without title, search without title). `extra_data` JSONB preserves extensibility without schema churn.

---

## 4. Query Result Schema

**Question**: What does a `QueryResult` look like in JSON to satisfy FR-002?

### Decision: Structured JSON with summary + tabular data + metadata

```json
{
  "summary": "SVoD content drove 64% of total revenue last quarter, with Drama and Thriller genres leading...",
  "confidence": 0.87,
  "data": [
    {"genre": "Drama", "service_type": "SVoD", "event_count": 1240, "completion_rate": 0.78},
    {"genre": "Thriller", "service_type": "SVoD", "event_count": 890, "completion_rate": 0.71}
  ],
  "applied_filters": {
    "region": null,
    "time_period": "last_quarter",
    "service_type": "SVoD"
  },
  "data_sources": ["analytics_events", "titles"],
  "data_freshness": "2026-02-21T10:30:00Z",
  "coverage_start": "2026-01-01T00:00:00Z"
}
```

**Summary generation**: Constructed from a Jinja2 template string per query pattern, populated with the top results from the SQL query. No LLM required — the PoC uses deterministic summary templates (e.g., "{{top_genre}} content drove {{top_pct}}% of {{service_type}} engagement last {{time_period}}").

---

## 5. Client Event Emission Design

**Question**: How should the frontend-client emit events without blocking the viewer experience (FR-011)?

### Decision: Fire-and-forget `apiFetch` wrapper with silent failure

```typescript
// analytics.ts
export async function emitEvent(event: AnalyticsEventPayload): Promise<void> {
  try {
    await apiFetch<void>('/analytics/events', {
      method: 'POST',
      body: JSON.stringify(event),
    });
  } catch {
    // Silent failure — never propagate analytics errors to the UI
  }
}
```

**Integration points** (existing files to modify):
- `PlayerPage.tsx`: Call `emitEvent` on play start, pause, and completion (already has stream session lifecycle hooks)
- `BrowsePage.tsx`: Call `emitEvent` on genre/type filter change and page load
- `SearchPage.tsx`: Call `emitEvent` on debounced search submit

**Rationale**: The `try/catch` wrapper at the emission layer ensures analytics failures are invisible to users. The `apiFetch` client already handles auth (Bearer token from localStorage). No new auth plumbing needed.

---

## 6. Seed Data Strategy

**Question**: How should synthetic analytics events be generated to make the agent queryable from first startup?

### Decision: Dedicated seed script `seed_analytics.py` added to existing seed orchestrator

**Strategy**:
- Generate 500–1000 events spanning the last 90 days
- Cover all 5 event types: play_start, play_pause, play_complete, browse, search
- Distribute across: 3 regions (NO, SE, DK), all 5 service types, realistic genre/title mix
- Skew distribution to simulate realistic patterns (Drama more popular in evenings, Sports peaks weekends, SVoD has higher completion rates than Linear)
- Idempotent: check if analytics_events table already has rows before seeding (consistent with other seed scripts)
- Added to `run_seeds.py` after `seed_users` (requires user IDs and profile IDs)

**Synthetic patterns seeded**:
1. Drama and Thriller → highest SVoD completion rates
2. Sports → spike on weekends, mostly Linear service type
3. Nordic regions → different genre preferences (Crime drama strong in DK, Sports in NO)
4. Browse → high browse-to-watch ratio for new subscribers (SVoD upgrade signal)
5. Cloud PVR recordings → concentrated on prime-time Linear content
