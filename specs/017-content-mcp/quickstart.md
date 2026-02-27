# Quickstart: Content Metadata MCP Server

**Branch**: `017-content-mcp` | **Date**: 2026-02-27

## Prerequisites

1. PostgreSQL running with seed data:
   ```bash
   docker compose -f docker/docker-compose.yml up -d postgres
   ```

2. Backend migrations and seed applied (if not already):
   ```bash
   cd backend && uv run alembic upgrade head
   ```

## Install & Run

```bash
# Install MCP server dependencies
cd mcp-server
uv sync

# Run standalone (stdio mode — will wait for MCP protocol messages on stdin)
DATABASE_URL="postgresql+asyncpg://ott_user:ott_password@localhost:5432/ott_platform" \
OTT_BACKEND_PATH="../backend" \
uv run ott-mcp
```

## Register in Claude Code

Add to `.claude/settings.local.json`:

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

Then restart Claude Code. The `ott-content` tools will be available in your session.

## Verify

In a Claude Code conversation:
1. Ask Claude to call `list_genres` — should return all genres
2. Ask Claude to call `search_titles(query="action")` — should return matching titles
3. Ask Claude to call `get_catalog_stats` — should return aggregate counts

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | yes | `postgresql+asyncpg://ott_user:ott_password@localhost:5432/ott_platform` | Async PostgreSQL connection string |
| `OTT_BACKEND_PATH` | yes | `../backend` (relative to mcp-server/) | Path to backend directory for model imports |
