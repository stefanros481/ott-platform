# OTT Content Metadata MCP Server

Read-only [MCP](https://modelcontextprotocol.io/) server that exposes the OTT platform's content catalog, EPG, entitlements, and analytics to AI agents. Supports two transports:

- **stdio** (default) — for local use with Claude Code and Claude Desktop
- **HTTP + SSE** — for deployment in Docker or remote agent platforms (e.g. AgentHub)

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- PostgreSQL 16 running with the `ott_platform` database seeded

## Quick Start

```bash
# Install dependencies
cd mcp-server
uv sync

# Configure environment (copy and edit as needed)
cp .env.example .env
```

Edit `.env` with your local database credentials and transport preference:

```env
# Async PostgreSQL connection string (asyncpg driver required)
DATABASE_URL=postgresql+asyncpg://ott_user:ott_password@localhost:5432/ott_platform

# Path to the backend package (needed for SQLAlchemy model imports)
OTT_BACKEND_PATH=../backend

# Transport: "stdio" (default) or "sse" (HTTP server)
MCP_TRANSPORT=stdio
MCP_HOST=0.0.0.0
MCP_PORT=8080
```

## Transport Modes

### stdio (default — Claude Code / Claude Desktop)

No configuration needed. The server is launched as a subprocess and communicates over stdin/stdout:

```bash
uv run ott-mcp
```

`MCP_TRANSPORT` defaults to `stdio` so you don't need to set it explicitly for local use.

### HTTP + SSE (Docker / remote agents)

Set `MCP_TRANSPORT=sse` to run as an HTTP server. The server will listen on `MCP_HOST:MCP_PORT` and expose the standard MCP SSE endpoint at `/sse`:

```bash
MCP_TRANSPORT=sse MCP_PORT=8080 uv run ott-mcp
```

Or via `.env`:

```env
MCP_TRANSPORT=sse
MCP_HOST=0.0.0.0
MCP_PORT=8080
```

To connect a remote client, point it at `http://<host>:8080/sse`.

## Usage with Claude Code

The server is registered in the project's `.mcp.json`:

```json
{
  "mcpServers": {
    "ott-content": {
      "command": "uv",
      "args": ["run", "--directory", "mcp-server", "ott-mcp"]
    }
  }
}
```

Once registered, Claude Code automatically starts the server and exposes its tools. Ask natural language questions like:

- "Show me all French movies"
- "What's on TV right now?"
- "Find titles with a gritty mood"
- "How many subscribers does the premium package have?"

## Available Tools

See [TOOLS.md](TOOLS.md) for the full tool reference. Key tool groups:

| Group | Tools |
|-------|-------|
| Catalog | `search_titles`, `list_titles`, `browse_titles`, `get_title`, `get_featured_titles` |
| Genres & Tags | `list_genres`, `list_mood_tags`, `list_theme_tags` |
| Cast & Crew | `search_cast`, `get_person_titles` |
| EPG | `list_channels`, `get_schedule`, `get_now_playing`, `search_schedule`, `get_catchup_available` |
| Packages | `get_packages`, `get_package_contents`, `get_title_offers` |
| Analytics | `get_title_popularity`, `get_service_type_stats`, `get_title_ratings`, `get_most_wishlisted` |
| Operations | `get_catalog_stats`, `get_embedding_status`, `get_tstv_stats`, `get_recording_stats` |
