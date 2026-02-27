# AI-Native OTT Streaming Platform

## Project Dependencies
- Use uv for dependency management as specified in the design
- Never add version to the top of any docker-compose

## Stack
- **Backend:** Python 3.12 + FastAPI, PostgreSQL 16 + pgvector
- **Frontend:** React 18 + TypeScript, Shaka Player 4.12
- **Infrastructure:** Kubernetes, Kafka, Go + Python microservices
- **AI/ML:** Hybrid cloud (Bedrock/SageMaker) + self-hosted (KServe)
- **Streaming:** CMAF with HLS/DASH, LL-HLS for live, Widevine + FairPlay + PlayReady DRM

## Feature Workflow
Features are tracked in `.specify/` workflow. Use `/speckit.specify` to start a new feature.

## Documentation Generation
The full 12-agent prompt suite for generating PRDs, user stories, and architecture docs is in [docs/agent-prompts.md](docs/agent-prompts.md). Read that file when running the doc generation workflow.

## Active Technologies & Recent Changes

See [.claude/agent-context.md](.claude/agent-context.md) — updated automatically by `update-agent-context.sh` after each feature implementation.
