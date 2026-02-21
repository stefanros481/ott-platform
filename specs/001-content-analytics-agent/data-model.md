# Data Model: Natural Language Content Analytics Agent

**Feature**: `001-content-analytics-agent`
**Date**: 2026-02-21
**Phase**: 1 — Design

---

## New Tables

### `analytics_events`

Records user interactions with content. Core data source for all agent queries.

```sql
CREATE TABLE analytics_events (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type      VARCHAR(20) NOT NULL,       -- play_start | play_pause | play_complete | browse | search
    title_id        UUID        REFERENCES titles(id) ON DELETE SET NULL,  -- null for browse/search
    service_type    VARCHAR(20) NOT NULL,       -- Linear | VoD | SVoD | TSTV | Catch_up | Cloud_PVR
    user_id         UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    profile_id      UUID        REFERENCES profiles(id) ON DELETE SET NULL,  -- null if no profile active
    region          VARCHAR(10) NOT NULL,       -- ISO country code: NO | SE | DK | etc.
    occurred_at     TIMESTAMPTZ NOT NULL,       -- client event time
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),  -- server receipt time
    session_id      UUID,                       -- groups play_start → pause → complete for one viewing
    duration_seconds INTEGER,                  -- populated for play_complete
    watch_percentage SMALLINT,                 -- 0–100, populated for play_complete
    extra_data      JSONB                       -- search query text, genre filter, etc.
);

-- Supporting indexes for the 10 query templates
CREATE INDEX idx_analytics_events_user_time    ON analytics_events (user_id, occurred_at DESC);
CREATE INDEX idx_analytics_events_service_time ON analytics_events (service_type, occurred_at DESC);
CREATE INDEX idx_analytics_events_region_time  ON analytics_events (region, occurred_at DESC);
CREATE INDEX idx_analytics_events_title        ON analytics_events (title_id) WHERE title_id IS NOT NULL;
CREATE INDEX idx_analytics_events_type_time    ON analytics_events (event_type, occurred_at DESC);
```

**Constraints**:
- `event_type` CHECK IN ('play_start', 'play_pause', 'play_complete', 'browse', 'search')
- `service_type` CHECK IN ('Linear', 'VoD', 'SVoD', 'TSTV', 'Catch_up', 'Cloud_PVR')
- `watch_percentage` CHECK BETWEEN 0 AND 100
- `duration_seconds` CHECK >= 0

**Key relationships**:
- `user_id → users.id` (CASCADE delete — events removed if user deleted)
- `title_id → titles.id` (SET NULL on delete — preserve event record if title removed)
- `profile_id → profiles.id` (SET NULL on delete)

---

### `query_jobs`

Tracks async query processing for complex queries that exceed the 2-second synchronous window.

```sql
CREATE TABLE query_jobs (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    question        TEXT        NOT NULL,       -- original natural language question
    status          VARCHAR(10) NOT NULL DEFAULT 'pending',  -- pending | complete | failed
    submitted_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,               -- set when status transitions to complete or failed
    result          JSONB,                     -- QueryResult JSON when status = complete
    error_message   TEXT                       -- human-readable reason when status = failed
);

CREATE INDEX idx_query_jobs_user_submitted ON query_jobs (user_id, submitted_at DESC);
```

**Constraints**:
- `status` CHECK IN ('pending', 'complete', 'failed')
- Row-level access: a user can only retrieve their own jobs (enforced in router, not DB)

---

## Entity Definitions

### AnalyticsEvent (Python Model)

```python
# backend/app/models/analytics.py

class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id:               Mapped[uuid.UUID]       # PK
    event_type:       Mapped[str]             # play_start | play_pause | play_complete | browse | search
    title_id:         Mapped[uuid.UUID | None]  # nullable
    service_type:     Mapped[str]
    user_id:          Mapped[uuid.UUID]       # FK → users.id
    profile_id:       Mapped[uuid.UUID | None]  # nullable FK → profiles.id
    region:           Mapped[str]
    occurred_at:      Mapped[datetime]
    created_at:       Mapped[datetime]        # server_default=func.now()
    session_id:       Mapped[uuid.UUID | None]  # nullable
    duration_seconds: Mapped[int | None]
    watch_percentage: Mapped[int | None]
    extra_data:       Mapped[dict | None]     # JSONB
```

### QueryJob (Python Model)

```python
# backend/app/models/analytics.py (same file)

class QueryJob(Base):
    __tablename__ = "query_jobs"

    id:            Mapped[uuid.UUID]
    user_id:       Mapped[uuid.UUID]           # FK → users.id, admin only
    question:      Mapped[str]
    status:        Mapped[str]                 # pending | complete | failed
    submitted_at:  Mapped[datetime]            # server_default=func.now()
    completed_at:  Mapped[datetime | None]
    result:        Mapped[dict | None]         # JSONB — QueryResult
    error_message: Mapped[str | None]
```

---

## Pydantic Schemas (Request / Response)

### AnalyticsEventCreate (request body for POST /analytics/events)

```python
class AnalyticsEventCreate(BaseModel):
    event_type:       Literal["play_start", "play_pause", "play_complete", "browse", "search"]
    title_id:         uuid.UUID | None = None
    service_type:     Literal["Linear", "VoD", "SVoD", "TSTV", "Catch_up", "Cloud_PVR"]
    profile_id:       uuid.UUID | None = None
    region:           str                       # e.g., "NO"
    occurred_at:      datetime
    session_id:       uuid.UUID | None = None
    duration_seconds: int | None = None
    watch_percentage: int | None = Field(None, ge=0, le=100)
    extra_data:       dict | None = None
```

### QueryRequest (request body for POST /content-analytics/query)

```python
class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
```

### QueryResult (synchronous response body OR stored in query_jobs.result)

```python
class QueryResult(BaseModel):
    summary:         str                        # plain-English insight paragraph
    confidence:      float = Field(ge=0.0, le=1.0)
    data:            list[dict]                 # tabular rows — schema varies per query
    applied_filters: dict                       # regions (list|null), time_period, service_type used
    data_sources:    list[str]                  # tables/entities contributing to result
    data_freshness:  datetime                   # most recent event timestamp in result set
    coverage_start:  datetime                   # earliest event in analytics_events table
```

### ClarificationResponse (when query is ambiguous)

```python
class ClarificationResponse(BaseModel):
    type:              Literal["clarification"] = "clarification"
    clarifying_question: str                    # single question to narrow the query
    context:           str                      # what aspect is ambiguous
```

### QueryResponse (union response for POST /content-analytics/query)

```python
class QueryResponse(BaseModel):
    status:        Literal["complete", "pending", "clarification"]
    # Synchronous path: result included, no job_id
    result:        QueryResult | None = None
    # Asynchronous path: job_id included, no result
    job_id:        uuid.UUID | None = None
    # Clarification path: clarification included, no result or job_id
    clarification: ClarificationResponse | None = None
```

### JobStatusResponse (GET /content-analytics/jobs/{job_id})

```python
class JobStatusResponse(BaseModel):
    job_id:        uuid.UUID
    status:        Literal["pending", "complete", "failed"]
    submitted_at:  datetime
    completed_at:  datetime | None = None
    result:        QueryResult | None = None    # populated when complete
    error_message: str | None = None           # populated when failed
```

---

## Alembic Migration: 006

**File**: `backend/alembic/versions/006_analytics_events_and_query_jobs.py`
**Revision ID**: `006`
**Revises**: `005`

```python
"""analytics events and query jobs

Revision ID: 006
Revises: 005

Adds:
  - analytics_events table (client interaction events)
  - query_jobs table (async NL query processing)
  - Indexes supporting the 10 query patterns and job polling
"""
```

**Downgrade**: `DROP TABLE query_jobs; DROP TABLE analytics_events;` (fully reversible)

---

## Existing Tables Used (Read-Only)

The query engine reads these existing tables to join against analytics events:

| Table | Usage |
|-------|-------|
| `titles` | Join on title_id to get genre, service_type metadata for aggregation |
| `users` | Verify admin status for query endpoints |
| `profiles` | Optional join for demographic segment (parental_rating, is_kids) |

No schema changes to existing tables are required.

---

## Query Engine Internal Representation

### QueryTemplate (in-memory, not persisted to DB)

```python
@dataclass
class QueryTemplate:
    id:          str                # e.g., "genre_revenue"
    name:        str                # human-readable
    description: str                # used for embedding + display
    sql:         str                # parameterized SQL with :region, :start_date, :end_date, :service_type
    parameters:  list[str]          # which params this template accepts
    summary_tpl: str                # Jinja2 template for generating the summary string
    embedding:   list[float] | None = None  # computed at startup via all-MiniLM-L6-v2
```

### QueryParameters (extracted from natural language by the engine)

```python
@dataclass
class QueryParameters:
    regions:      list[str] | None  # e.g., ["NO"] or ["NO", "SE", "DK"] for "Nordics"
    service_type: str | None        # e.g., "SVoD"
    time_period:  str | None        # e.g., "last_quarter"
    start_date:   datetime | None   # resolved from time_period
    end_date:     datetime | None
```

Parameter extraction uses keyword matching after template selection. A single region mention ("Norway") produces `regions=["NO"]`; compound mentions ("Norway, Sweden" or "Nordics") produce `regions=["NO", "SE", "DK"]`. A null value means no region filter — query returns all regions. SQL uses `WHERE region IN :regions` with a bind parameter list.
