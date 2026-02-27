# Feature Specification: Content Metadata MCP Server

**Feature Branch**: `017-content-mcp`
**Created**: 2026-02-27
**Status**: Draft
**Input**: User description: "Create an MCP server so AI agents can interact with the content metadata database"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Search and Browse Content Catalog (Priority: P1)

An AI agent (such as Claude in Claude Code) needs to search and browse the OTT platform's content catalog to answer questions about available titles, find specific movies or series, and understand the catalog composition.

The agent connects to the MCP server (registered in Claude Code settings) and uses tools like `search_titles`, `list_titles`, and `get_title` to query the database directly. The agent can filter by genre, type (movie/series), and keyword, and retrieve full details including cast, seasons, episodes, and metadata tags.

**Why this priority**: Catalog search is the most fundamental operation. Without it, the MCP server has no core value. This enables content operations teams and developers to query the catalog conversationally.

**Independent Test**: Can be fully tested by starting the MCP server, connecting via Claude Code, and running `search_titles(query="action")` — returns matching titles from the database.

**Acceptance Scenarios**:

1. **Given** the MCP server is running and connected to the database, **When** an agent calls `search_titles` with a keyword, **Then** matching titles are returned with id, title, type, synopsis, genres, and year.
2. **Given** the catalog contains both movies and series, **When** an agent calls `list_titles` with `title_type="series"`, **Then** only series are returned with pagination info.
3. **Given** a valid title UUID, **When** an agent calls `get_title`, **Then** full details are returned including cast members, genres, mood/theme tags, and seasons/episodes for series.
4. **Given** a search query that matches cast member names, **When** an agent calls `search_titles`, **Then** titles featuring that cast member are included in results.

---

### User Story 2 - Browse EPG and Channel Information (Priority: P2)

An AI agent needs to query the Electronic Program Guide (EPG) to understand what channels are available, what is currently airing, and what programs are scheduled for a specific channel and date.

The agent uses `list_channels`, `get_schedule`, and `get_now_playing` to access linear TV metadata.

**Why this priority**: EPG data is the second major content domain after VoD catalog. Together with Story 1, this covers the full content metadata surface.

**Independent Test**: Can be tested by calling `list_channels` to see all channels, then `get_schedule(channel_id="<uuid>", date="2026-02-27")` to see that day's schedule.

**Acceptance Scenarios**:

1. **Given** the database has channel data, **When** an agent calls `list_channels`, **Then** all channels are returned with name, number, genre, HD status, and TSTV capabilities.
2. **Given** a valid channel UUID and date, **When** an agent calls `get_schedule`, **Then** schedule entries for that day are returned in chronological order with title, times, synopsis, and age rating.
3. **Given** programs are currently airing, **When** an agent calls `get_now_playing`, **Then** the current and next program for each channel are returned.

---

### User Story 3 - Understand Catalog Composition and Statistics (Priority: P3)

An AI agent needs to get a high-level overview of the content library — total counts, genre distribution, content package pricing — to answer business questions or generate reports about catalog health.

The agent calls `get_catalog_stats` and `list_genres` to understand the shape of the catalog without browsing individual titles.

**Why this priority**: Statistics and overview tools add value for content operations but are not required for core browsing functionality.

**Independent Test**: Can be tested by calling `get_catalog_stats` and verifying it returns total title count, movie/series breakdown, genre distribution, and channel count.

**Acceptance Scenarios**:

1. **Given** the catalog contains titles across multiple genres, **When** an agent calls `get_catalog_stats`, **Then** aggregate counts are returned: total titles, movies, series, genre distribution, total channels, and age rating distribution.
2. **Given** content packages exist, **When** an agent calls `get_catalog_stats`, **Then** package information (name, tier, price) is included in the statistics.
3. **Given** any catalog state, **When** an agent calls `list_genres`, **Then** all genres are returned with name and slug for use as filters.

---

### User Story 4 - Query Title Pricing and Offers (Priority: P3)

An AI agent needs to understand the commercial availability of a specific title — whether it's included in an SVOD package, available for rent or purchase, and at what price.

**Why this priority**: Pricing data is useful but secondary to content discovery. Builds on Story 1 by enriching title details.

**Independent Test**: Can be tested by calling `get_title_offers(title_id="<uuid>")` for a title with active offers and verifying pricing data is returned.

**Acceptance Scenarios**:

1. **Given** a title with active TVOD offers, **When** an agent calls `get_title_offers`, **Then** offer type (rent/buy/free), price, currency, and rental window are returned.
2. **Given** a title with no active offers, **When** an agent calls `get_title_offers`, **Then** an empty offers list is returned.

---

### Edge Cases

- What happens when the database is unreachable? The MCP server returns a clear error message rather than crashing.
- What happens when a tool receives an invalid UUID? The server returns a descriptive validation error, not a stack trace.
- What happens when search returns zero results? An empty list with a count of 0, not an error.
- What happens when pagination exceeds available results? The last page is returned with correct total count.
- What happens when the `date` parameter for `get_schedule` is in an invalid format? A clear validation error is returned.

## Clarifications

### Session 2026-02-27

- Q: Should the MCP server support only local stdio transport or also networked access? → A: Local stdio only (for Claude Code on the same machine). Networked transport (HTTP/SSE) deferred to a future iteration.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST expose content catalog search via keyword matching across title, synopsis, and cast member names.
- **FR-002**: System MUST support paginated browsing of the catalog with optional filters for genre and content type (movie/series).
- **FR-003**: System MUST return full title details including cast, genres, seasons/episodes, mood/theme tags, and AI description when queried by ID.
- **FR-004**: System MUST expose all TV channels with their metadata and TSTV capability flags.
- **FR-005**: System MUST return EPG schedule data for a specific channel and date, ordered chronologically.
- **FR-006**: System MUST provide a "now playing" view showing current and next program across all channels.
- **FR-007**: System MUST provide aggregate catalog statistics (counts, distributions) in a single query.
- **FR-008**: System MUST return pricing/offer information for individual titles.
- **FR-009**: System MUST provide schema documentation and a usage guide as readable resources for the agent.
- **FR-010**: System MUST be strictly read-only — no database mutations are permitted.
- **FR-011**: System MUST handle errors gracefully, returning descriptive error messages rather than raw exceptions.
- **FR-012**: System MUST be registerable in Claude Code's MCP server configuration for stdio-based communication. Networked transport (HTTP/SSE) is out of scope for this iteration.

### Key Entities

- **Title**: A movie or series in the catalog, with associated genres, cast, and metadata tags.
- **Genre**: A content category (e.g., Action, Drama) used for filtering and classification.
- **Channel**: A linear TV channel with schedule, TSTV capabilities, and live stream URL.
- **Schedule Entry**: A single program slot in the EPG grid, tied to a channel and time window.
- **Content Package**: An SVOD subscription tier with pricing and included content.
- **Title Offer**: A per-title commercial offer (rent, buy, or free) with pricing details.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An AI agent can discover and use all content tools within a single Claude Code session without manual configuration beyond initial registration.
- **SC-002**: Catalog search returns results in under 2 seconds for any keyword query.
- **SC-003**: An agent can retrieve full details for any title (including cast, seasons, episodes) in a single tool call.
- **SC-004**: The EPG schedule for any channel and date is returned in a single tool call with all program details.
- **SC-005**: Catalog statistics (counts, genre distribution) are available in a single tool call without the agent needing to aggregate manually.
- **SC-006**: All tools return structured, parseable responses that the agent can reason over without additional transformation.
- **SC-007**: The server handles 100% of invalid inputs (bad UUIDs, missing parameters, unreachable database) with descriptive errors rather than crashes.
