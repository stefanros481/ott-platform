# Tasks: Content Metadata MCP Server

**Input**: Design documents from `/specs/017-content-mcp/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/mcp-tools.md, quickstart.md

**Tests**: Not explicitly requested in spec. Test tasks omitted. Validation via Claude Code tool calls per quickstart.md.

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **MCP Server**: `mcp-server/src/ott_mcp/` (new standalone package)
- **Backend models/services**: `backend/app/models/`, `backend/app/services/` (existing, read-only reference)
- **Config**: `.claude/settings.local.json`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the MCP server package structure and install dependencies

- [x] T001 Create `mcp-server/pyproject.toml` with dependencies: `mcp[cli]>=1.0`, `sqlalchemy[asyncio]>=2.0`, `asyncpg>=0.30`, `pgvector>=0.3`, `pydantic>=2.10`, `pydantic-settings>=2.7`. Define entry point `ott-mcp = "ott_mcp.server:main"`. Use hatchling build backend.
- [x] T002 Create `mcp-server/src/ott_mcp/__init__.py` (empty package init)
- [x] T003 Run `cd mcp-server && uv sync` to install dependencies and verify resolution succeeds

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Database connection and serialization utilities that ALL tools depend on

**CRITICAL**: No tool implementation can begin until this phase is complete

- [x] T004 Create `mcp-server/src/ott_mcp/db.py` — standalone async SQLAlchemy engine. Read `DATABASE_URL` from env (default: `postgresql+asyncpg://ott_user:ott_password@localhost:5432/ott_platform`). Pool size 5, pool_pre_ping enabled. Export `engine` and `async_session_factory`.
- [x] T005 [P] Create `mcp-server/src/ott_mcp/serializers.py` — JSON encoder handling `uuid.UUID` (→ str) and `datetime` (→ ISO format). Export `to_json(data) -> str` helper function.
- [x] T006 Create `mcp-server/src/ott_mcp/server.py` — scaffold with FastMCP instance (`json_response=True`), lifespan that creates `AppContext(session_factory)` and disposes engine on shutdown, `sys.path` setup for backend model imports (set dummy `JWT_SECRET` env var), and `main()` entry point calling `mcp.run(transport="stdio")`. Per FR-010: register only read-only tools — no write/mutation tools.
- [x] T006a [P] Add `content://schema` resource in `mcp-server/src/ott_mcp/server.py` — static string documenting all table schemas (titles, genres, title_genres, title_cast, seasons, episodes, channels, schedule_entries, content_packages, title_offers) with columns and types.
- [x] T006b [P] Add `content://tools-guide` resource in `mcp-server/src/ott_mcp/server.py` — static string with usage guide explaining how to effectively use the tools (search workflow, filtering with genre slugs, ID passing between tools).

**Checkpoint**: `cd mcp-server && uv run ott-mcp` should start without errors (waiting for stdio input)

---

## Phase 3: User Story 1 — Search and Browse Content Catalog (Priority: P1) MVP

**Goal**: Agent can search, browse, and inspect VoD catalog titles via MCP tools

**Independent Test**: Call `list_genres`, `search_titles(query="action")`, `list_titles(page=1)`, and `get_title(title_id="<uuid>")` from Claude Code

### Implementation for User Story 1

- [x] T007 [US1] Implement `list_genres` tool in `mcp-server/src/ott_mcp/server.py` — call `catalog_service.get_genres(db)`, return list of `{name, slug}`. Import `Genre` from `app.models.catalog`.
- [x] T008 [US1] Implement `search_titles` tool in `mcp-server/src/ott_mcp/server.py` — params: `query` (str, required), `title_type` (str, optional), `genre` (str, optional), `limit` (int, default 20). Call `catalog_service.get_titles(db, search_query=query, title_type=..., genre_slug=...)`. Serialize results with id, title, title_type, synopsis_short, release_year, duration_minutes, age_rating, genres, poster_url, is_featured. Return `{titles: [...], total: N}`.
- [x] T009 [US1] Implement `list_titles` tool in `mcp-server/src/ott_mcp/server.py` — params: `page` (int, default 1), `page_size` (int, default 20), `title_type` (optional), `genre` (optional). Call `catalog_service.get_titles(db, page=..., page_size=..., ...)`. Return `{titles: [...], total, page, page_size}`.
- [x] T010 [US1] Implement `get_title` tool in `mcp-server/src/ott_mcp/server.py` — param: `title_id` (str, required). Parse UUID, call `catalog_service.get_title_detail(db, title_id)`. Return full detail: id, title, title_type, all synopsis fields, ai_description, release_year, duration, age_rating, country, language, URLs, mood/theme tags, is_featured, is_educational, genres (with is_primary), cast (name, role, character, sort_order), seasons with episodes. Return error message if title not found.
- [x] T011 [US1] Implement `get_featured_titles` tool in `mcp-server/src/ott_mcp/server.py` — no params. Call `catalog_service.get_featured_titles(db)`. Return list of title summaries.

**Checkpoint**: US1 complete — agent can search catalog, browse with filters, and get full title details

---

## Phase 4: User Story 2 — Browse EPG and Channel Information (Priority: P2)

**Goal**: Agent can query channels, EPG schedules, and currently airing programs

**Independent Test**: Call `list_channels`, `get_schedule(channel_id="<uuid>", date="today")`, and `get_now_playing` from Claude Code

### Implementation for User Story 2

- [x] T012 [US2] Implement `list_channels` tool in `mcp-server/src/ott_mcp/server.py` — no params. Call `epg_service.get_channels(db)`. Note: `_channel_dict()` omits TSTV fields — serialize tstv_enabled, startover_enabled, catchup_enabled, catchup_window_hours directly from the Channel ORM objects returned by the service. Return list with id, name, channel_number, logo_url, genre, is_hd, tstv_enabled, startover_enabled, catchup_enabled, catchup_window_hours.
- [x] T013 [US2] Implement `get_schedule` tool in `mcp-server/src/ott_mcp/server.py` — params: `channel_id` (str, required), `date` (str, default "today"). Parse UUID and date (support "today" and YYYY-MM-DD). Call `epg_service.get_schedule(db, channel_id, day)`. Return list of schedule entries with id, title, synopsis, genre, start_time, end_time, age_rating, is_new, is_repeat, catchup_eligible, startover_eligible. Return validation error for invalid date format.
- [x] T014 [US2] Implement `get_now_playing` tool in `mcp-server/src/ott_mcp/server.py` — no params. Call `epg_service.get_now_playing(db)`. Serialize channel info and current/next program for each channel.

**Checkpoint**: US2 complete — agent can browse channels and query EPG data

---

## Phase 5: User Story 3 — Catalog Statistics (Priority: P3)

**Goal**: Agent can get aggregate catalog overview in a single tool call

**Independent Test**: Call `get_catalog_stats` from Claude Code and verify counts, genre distribution, and package info

### Implementation for User Story 3

- [x] T015 [US3] Implement `get_catalog_stats` tool in `mcp-server/src/ott_mcp/server.py` — no params. Run aggregate queries: COUNT titles (total, movies, series), GROUP BY genre (with slug and count), GROUP BY age_rating, COUNT channels, SELECT all content packages (name, tier, price_cents, currency). Return `{titles: {total, movies, series}, genres: [...], age_ratings: {...}, channels: {total}, packages: [...]}`.

**Checkpoint**: US3 complete — agent can get full catalog overview

---

## Phase 6: User Story 4 — Title Pricing and Offers (Priority: P3)

**Goal**: Agent can query pricing and SVOD package inclusion for any title

**Independent Test**: Call `get_title_offers(title_id="<uuid>")` from Claude Code

### Implementation for User Story 4

- [x] T016 [US4] Implement `get_title_offers` tool in `mcp-server/src/ott_mcp/server.py` — param: `title_id` (str, required). Query `TitleOffer` WHERE title_id AND is_active. Query `PackageContent` + `ContentPackage` WHERE content_id = title_id AND content_type = 'vod_title'. Return `{title_id, offers: [{offer_type, price_cents, currency, rental_window_hours}], included_in_packages: [{name, tier}]}`.

**Checkpoint**: US4 complete — agent can check title availability and pricing

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Resources, registration, and final validation

- [x] T017 (moved to T006a in Phase 2)
- [x] T018 (moved to T006b in Phase 2)
- [x] T019 Add error handling wrappers to all tools in `mcp-server/src/ott_mcp/server.py` — catch invalid UUIDs (return descriptive message), database connection errors (return "Database unreachable" message), and unexpected exceptions (return error string, don't crash).
- [x] T020 Register MCP server in `.mcp.json` (project scope) — add `ott-content` entry under `mcpServers` with command `uv`, args `["run", "--directory", "mcp-server", "ott-mcp"]`, and env vars `DATABASE_URL` and `OTT_BACKEND_PATH`.
- [x] T021 Run quickstart.md validation — start postgres, run `uv run ott-mcp` standalone, then restart Claude Code and verify tools appear and respond correctly.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phases 3-6)**: All depend on Foundational phase completion
  - US1 (Phase 3): No story dependencies
  - US2 (Phase 4): No story dependencies (can run parallel with US1)
  - US3 (Phase 5): No story dependencies (can run parallel with US1/US2)
  - US4 (Phase 6): No story dependencies (can run parallel with US1/US2/US3)
- **Polish (Phase 7)**: Depends on all user stories being complete

### Within Each User Story

- All tools write to the same file (`server.py`), so tasks within a story are sequential
- However, different stories can be interleaved since each tool is a self-contained function

### Parallel Opportunities

- T004 and T005 can run in parallel (different files: `db.py` and `serializers.py`)
- T017 and T018 can run in parallel (both are static resource strings)
- All 4 user story phases could theoretically run in parallel, but since all tools live in `server.py`, sequential execution is more practical

---

## Parallel Example: Foundational Phase

```bash
# These can run in parallel (different files):
Task: "Create db.py with async engine" (T004)
Task: "Create serializers.py with JSON encoder" (T005)

# Then sequential:
Task: "Scaffold server.py with FastMCP lifespan" (T006) — depends on T004, T005
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T006)
3. Complete Phase 3: User Story 1 (T007-T011)
4. **STOP and VALIDATE**: Register in settings (T020), test via Claude Code
5. Agent can now search and browse the catalog — functional MVP

### Incremental Delivery

1. Setup + Foundational → Server scaffold running
2. Add US1 (catalog search/browse) → MVP
3. Add US2 (EPG/channels) → Full content coverage
4. Add US3 (statistics) → Catalog overview
5. Add US4 (pricing) → Commercial data
6. Polish → Resources, error handling, registration

---

## Notes

- All tool implementations go in a single file: `mcp-server/src/ott_mcp/server.py`
- 9 of 10 tools reuse existing service functions from `backend/app/services/catalog_service.py` and `backend/app/services/epg_service.py`
- Only `get_catalog_stats` (T015) and `get_title_offers` (T016) require new SQL queries
- Total: 21 tasks across 7 phases
