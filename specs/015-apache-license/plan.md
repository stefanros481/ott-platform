# Implementation Plan: Apache License 2.0

**Branch**: `015-apache-license` | **Date**: 2026-02-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/015-apache-license/spec.md`

## Summary

Add Apache License, Version 2.0 to the project. This involves: (1) creating the `LICENSE` file at the repo root, (2) declaring the license in all package metadata files, (3) prepending SPDX identifier headers to all 129 project-owned source files, (4) adding a License section to the README, and (5) producing a third-party dependency compatibility audit report (pre-completed — all 28 direct dependencies are compatible).

## Technical Context

**Language/Version**: Python 3.12, TypeScript 5.6, Node.js (current LTS)
**Primary Dependencies**: No new dependencies — this is a compliance/metadata feature
**Storage**: N/A — no database changes
**Testing**: Manual verification via grep commands (see quickstart.md); no automated tests required
**Target Platform**: Repository root + backend/app/ + frontend-*/src/
**Project Type**: Web application (backend + two frontends)
**Performance Goals**: N/A
**Constraints**: SPDX short-form only (no copyright per-file, no full boilerplate); migrations excluded; dependency dirs excluded
**Scale/Scope**: 129 source files (64 Python + 45 TS client + 20 TS admin), 3 metadata files, 1 LICENSE, 1 README section

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. PoC-First Quality | ✅ Pass | Compliance task, no production hardening needed |
| II. Monolithic Simplicity | ✅ Pass | No new services or projects |
| III. AI-Native by Default | ✅ N/A | License compliance feature |
| IV. Docker Compose as Truth | ✅ Pass | No Docker changes |
| V. Seed Data as Demo | ✅ N/A | No data changes |
| No `version` in docker-compose | ✅ N/A | No Docker changes |
| Use `uv` for Python deps | ✅ N/A | No new Python deps |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/015-apache-license/
├── plan.md                      # This file
├── research.md                  # Phase 0 — decisions and rationale
├── quickstart.md                # Phase 1 — verification commands
├── third-party-licenses.md      # Phase 0 — audit report (pre-completed)
├── checklists/
│   └── requirements.md
└── tasks.md                     # Phase 2 output (/speckit.tasks)
```

### Source Code (files touched)

```text
LICENSE                          # NEW — Apache 2.0 full text with copyright
README.md                        # MODIFIED — append "## License" section

backend/
└── pyproject.toml               # MODIFIED — add license = "Apache-2.0"
    app/                         # MODIFIED — SPDX header on all 64 .py files
    ├── main.py
    ├── config.py
    ├── database.py
    ├── models/*.py
    ├── schemas/*.py
    ├── routers/*.py
    ├── services/*.py
    └── seed/*.py

frontend-client/
├── package.json                 # MODIFIED — add "license": "Apache-2.0"
└── src/                         # MODIFIED — SPDX header on all 45 .ts/.tsx files

frontend-admin/
├── package.json                 # MODIFIED — add "license": "Apache-2.0"
└── src/                         # MODIFIED — SPDX header on all 20 .ts/.tsx files
```

**Structure Decision**: The feature touches existing files across all three sub-projects. No new directories are created (except the spec artifact `third-party-licenses.md` which is already written). The LICENSE file is new at the repo root.

## Implementation Steps

### Step 1: Create LICENSE file

Fetch the canonical Apache 2.0 text from https://www.apache.org/licenses/LICENSE-2.0.txt and write to `LICENSE` at repo root. The file must begin with the copyright notice, followed by the standard Apache 2.0 text:

```
Copyright 2026 Stefan Rosander

                                 Apache License
                           Version 2.0, January 2004
...
```

### Step 2: Update package metadata

- `backend/pyproject.toml`: add `license = "Apache-2.0"` to `[project]` section
- `frontend-client/package.json`: add `"license": "Apache-2.0"` field
- `frontend-admin/package.json`: add `"license": "Apache-2.0"` field

### Step 3: Add SPDX headers to Python source files

For every `.py` file under `backend/app/`, insert `# SPDX-License-Identifier: Apache-2.0` as the first line. Files that already have a shebang (`#!/...`) or encoding declaration (`# -*- coding: ...`) should have the SPDX line added after those lines.

Scope: 64 files.

### Step 4: Add SPDX headers to TypeScript source files

For every `.ts` and `.tsx` file under `frontend-client/src/` and `frontend-admin/src/`, insert `// SPDX-License-Identifier: Apache-2.0` as the first line.

Scope: 65 files (45 + 20).

### Step 5: Update README.md

Append the following section at the end of `README.md`:

```markdown
## License

Copyright 2026 Stefan Rosander

Licensed under the [Apache License, Version 2.0](LICENSE).
```

### Step 6: Verify

Run the all-in-one check from `quickstart.md` to confirm zero files are missing headers, metadata is correct, and the README has the License section.

## Complexity Tracking

No constitution violations. No complexity tracking required.

## Artifacts

| Artifact | Path | Status |
|----------|------|--------|
| Research | specs/015-apache-license/research.md | ✅ Complete |
| Quickstart | specs/015-apache-license/quickstart.md | ✅ Complete |
| Audit Report | specs/015-apache-license/third-party-licenses.md | ✅ Complete |
| Data Model | N/A (no database changes) | — |
| API Contracts | N/A (no new endpoints) | — |
| Tasks | specs/015-apache-license/tasks.md | Pending `/speckit.tasks` |
