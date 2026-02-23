# Research: Apache License 2.0

**Feature**: 015-apache-license
**Date**: 2026-02-23

---

## Decision 1: License File Source

**Decision**: Fetch the canonical Apache 2.0 text from https://www.apache.org/licenses/LICENSE-2.0.txt and write it verbatim to `LICENSE` at the repo root, with the copyright notice prepended as required by Apache 2.0 Section 4(a).

**Rationale**: The Apache Software Foundation publishes the definitive plain-text version at this URL. The spec requires a byte-for-byte match (SC-004), so no reformatting is permitted.

**Copyright line format**:
```
Copyright 2026 Stefan Rosander
```

---

## Decision 2: SPDX Identifier Format

**Decision**: Use a single-line SPDX short-form identifier per file. No copyright comment, no full boilerplate.

- Python: `# SPDX-License-Identifier: Apache-2.0`
- TypeScript/TSX: `// SPDX-License-Identifier: Apache-2.0`

**Rationale**: Chosen in clarification session. SPDX short-form is machine-readable, minimal, and sufficient for open-source compliance tooling.

**Alternatives considered**:
- Full Apache 2.0 boilerplate per file — rejected (verbose, adds noise to 129 files)
- Copyright comment + SPDX — rejected (clarification Q1: SPDX only)

---

## Decision 3: File Scope for SPDX Headers

**Decision**:
- Include: `backend/app/**/*.py` (64 files), `frontend-client/src/**/*.{ts,tsx}` (45 files), `frontend-admin/src/**/*.{ts,tsx}` (20 files)
- Exclude: `backend/alembic/`, `.venv/`, `node_modules/`, `dist/`, build artifacts

**File count**: 129 project-owned source files total.

**Rationale**: Clarified in session (Q2). Migration files are auto-generated and excluded. Dependency directories retain their own upstream licenses.

---

## Decision 4: Package Metadata Format

**pyproject.toml** — PEP 621 format:
```toml
license = "Apache-2.0"
```
Added to `[project]` table. The SPDX expression string is the modern PEP 621 standard (not the legacy `{text = "..."}` table form).

**package.json** — standard npm field:
```json
"license": "Apache-2.0"
```

---

## Decision 5: Third-Party License Compatibility

All direct dependencies are Apache-2.0 compatible. Full audit results in `third-party-licenses.md`.

**Summary**: 15 Python direct dependencies, 13 Node.js direct dependencies (shared between both frontends). All are MIT, BSD-2, BSD-3, or Apache-2.0 licensed — all permissive and fully compatible with Apache 2.0.

**No incompatible or unknown licenses found.**

---

## Decision 6: Audit Report Location

**Decision**: Store at `specs/015-apache-license/third-party-licenses.md`.

**Rationale**: Keeps the compliance artifact alongside the feature spec that required it. Not committed to the project root to avoid cluttering the main repo structure.

---

## Unknowns Resolved

| Was Unknown | Resolution |
|-------------|------------|
| Copyright holder name/year | Stefan Rosander, 2026 |
| SPDX vs full boilerplate | SPDX only (clarification Q1) |
| Migration files in scope? | Excluded (clarification Q2) |
| Any incompatible dependencies? | None found (see third-party-licenses.md) |
