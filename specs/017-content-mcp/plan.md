# Implementation Plan: Content Metadata MCP Server

**Branch**: `017-content-mcp` | **Date**: 2026-02-27 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/017-content-mcp/spec.md`

## Summary

Create a read-only MCP (Model Context Protocol) server that exposes the OTT platform's content metadata database to AI agents via stdio transport. The server provides 10 tools for catalog search/browse, EPG/channel queries, statistics, and pricing — reusing existing SQLAlchemy service functions from the backend. Packaged as a standalone Python project at `mcp-server/` that imports the backend's ORM models but manages its own database connection.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: `mcp[cli]` (MCP Python SDK with FastMCP), SQLAlchemy 2.0+ (async), asyncpg, pgvector
**Storage**: PostgreSQL 16 + pgvector (existing database, read-only access)
**Testing**: Manual validation via Claude Code tool calls; pytest for unit tests of serializers
**Target Platform**: macOS/Linux (local developer machine, stdio subprocess)
**Project Type**: Single project (standalone MCP server package)
**Performance Goals**: <2s response time per tool call (SC-002)
**Constraints**: Read-only (no mutations), stdio transport only (no HTTP/SSE), no sentence-transformers dependency
**Scale/Scope**: Single-user (one Claude Code session), ~50-100 titles, ~20-30 channels in seed data

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. PoC-First Quality | PASS | MCP server is a developer tool, not production-facing. Functional correctness prioritized. |
| II. Monolithic Simplicity | PASS with justification | MCP server is a separate package but not a microservice — it's a developer tooling process that imports models from the monolith. See Complexity Tracking. |
| III. AI-Native by Default | PASS | The entire feature is AI-native — enabling AI agents to query content metadata. |
| IV. Docker Compose as Truth | PASS | MCP server uses the same PostgreSQL from docker-compose. No new services needed. |
| V. Seed Data as Demo | PASS | MCP server reads existing seed data. No new seed data required. |
| Constraints: uv | PASS | Uses uv for dependency management. |
| Constraints: No cloud deps | PASS | Runs entirely locally. |

## Project Structure

### Documentation (this feature)

```text
specs/017-content-mcp/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (MCP tool schemas)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
mcp-server/
├── pyproject.toml           # Package config (uv-managed, hatchling build)
└── src/
    └── ott_mcp/
        ├── __init__.py
        ├── server.py        # FastMCP server: lifespan, 10 tools, 2 resources, main()
        ├── db.py            # Standalone async engine from DATABASE_URL
        └── serializers.py   # UUID/datetime JSON encoder
```

**Structure Decision**: Separate `mcp-server/` directory at repo root. This is a standalone Python package that imports ORM models from `backend/app/models/` via `sys.path` manipulation. It does NOT depend on the FastAPI app runtime (no JWT, Redis, CORS). The MCP server creates its own lightweight SQLAlchemy engine from `DATABASE_URL`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Separate `mcp-server/` package (not inside `backend/`) | MCP servers run as stdio subprocesses with their own entry point. Embedding in FastAPI would couple lifecycle, require JWT_SECRET/Redis at startup, and pull in 800MB+ of sentence-transformers. | Adding MCP as a FastAPI endpoint would require the web server to be running, defeating the purpose of a lightweight developer tool. |
