# Research: Content Metadata MCP Server

**Branch**: `017-content-mcp` | **Date**: 2026-02-27

## R1: MCP Python SDK — Server Implementation Pattern

**Decision**: Use `FastMCP` from the official `mcp` Python SDK (`mcp[cli]>=1.0`).

**Rationale**: FastMCP provides a high-level decorator-based API (`@mcp.tool()`, `@mcp.resource()`) with built-in lifespan management, automatic JSON schema generation from type hints, and stdio transport. This is the officially recommended approach for Python MCP servers.

**Alternatives considered**:
- Low-level `mcp.server.lowlevel.Server` — more control but requires manual schema definitions and handler registration. Unnecessary for our straightforward read-only tools.
- Custom stdio protocol implementation — no reason to reinvent what the SDK provides.

**Key patterns**:
```python
mcp = FastMCP("OTT Content Metadata", json_response=True)

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    yield AppContext(session_factory=async_session_factory)

@mcp.tool()
async def search_titles(query: str, ctx: Context) -> dict: ...

@mcp.resource("content://schema")
def get_schema() -> str: ...
```

Entry point: `mcp.run(transport="stdio")`

## R2: Model Import Strategy — Shared ORM, Separate Engine

**Decision**: Import SQLAlchemy model classes from `backend/app/models/` by adding the backend directory to `sys.path`. Create an independent async engine in `mcp-server/src/ott_mcp/db.py`.

**Rationale**: The ORM models (Title, Genre, Channel, etc.) are the source of truth for database table mappings. Duplicating them would create maintenance burden. However, importing `app.database` triggers `app.config.Settings` which requires `JWT_SECRET` — so we set a dummy env var at import time.

**Alternatives considered**:
- Duplicate models in MCP server — rejected: high maintenance cost, divergence risk.
- Use raw SQL queries — rejected: loses type safety and relationship loading from ORM.
- Make `app.config.Settings` optional — rejected: would require modifying the backend for a tooling concern.

**Implementation**:
```python
import os, sys
os.environ.setdefault("JWT_SECRET", "mcp-server-dummy")
backend_path = os.environ.get("OTT_BACKEND_PATH", ...)
sys.path.insert(0, os.path.abspath(backend_path))
# Now: from app.models.catalog import Title, Genre, ...
```

## R3: Service Function Reuse

**Decision**: Call existing service functions from `catalog_service.py` and `epg_service.py` directly, passing the MCP server's own `AsyncSession`.

**Rationale**: 9 of 10 tools map directly to existing service functions. These functions accept `AsyncSession` as their first parameter — they don't depend on FastAPI request context, Redis, or JWT.

**Service function mapping**:

| MCP Tool | Service Function | File |
|----------|-----------------|------|
| `search_titles` | `catalog_service.get_titles(db, search_query=...)` | `backend/app/services/catalog_service.py` |
| `get_title` | `catalog_service.get_title_detail(db, title_id)` | same |
| `list_titles` | `catalog_service.get_titles(db, page=..., ...)` | same |
| `list_genres` | `catalog_service.get_genres(db)` | same |
| `get_featured_titles` | `catalog_service.get_featured_titles(db)` | same |
| `list_channels` | `epg_service.get_channels(db)` | `backend/app/services/epg_service.py` |
| `get_schedule` | `epg_service.get_schedule(db, channel_id, day)` | same |
| `get_now_playing` | `epg_service.get_now_playing(db)` | same |
| `get_title_offers` | New query (simple SELECT on TitleOffer) | MCP server |
| `get_catalog_stats` | New aggregate queries (COUNT + GROUP BY) | MCP server |

## R4: Transport — stdio Only

**Decision**: Use stdio transport exclusively for v1.

**Rationale**: Claude Code invokes MCP servers as stdio subprocesses. This is the simplest deployment model — no port binding, no auth, no CORS. Networked transport (streamable-http) deferred per clarification session.

**Registration** in `.claude/settings.local.json`:
```json
{
  "mcpServers": {
    "ott-content": {
      "command": "uv",
      "args": ["run", "--directory", "mcp-server", "ott-mcp"],
      "env": {
        "DATABASE_URL": "postgresql+asyncpg://ott_user:ott_password@localhost:5432/ott_platform",
        "OTT_BACKEND_PATH": "./backend"
      }
    }
  }
}
```

## R5: Serialization

**Decision**: Use `json_response=True` on `FastMCP` so tools can return dicts/lists that get auto-serialized. Provide a custom JSON encoder for UUID and datetime objects.

**Rationale**: SQLAlchemy model attributes include `uuid.UUID` and `datetime` types that aren't JSON-serializable by default. A simple custom encoder handles this universally.

## R6: Database Connection Pool

**Decision**: Pool size of 5, pool_pre_ping enabled.

**Rationale**: MCP server is single-user (one Claude Code session). A small pool avoids wasting connections. `pool_pre_ping` ensures stale connections are detected after the database restarts.
