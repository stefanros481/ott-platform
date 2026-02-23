# Feature Specification: Apache License 2.0

**Feature Branch**: `015-apache-license`
**Created**: 2026-02-23
**Status**: Draft
**Input**: User description: "We need to make sure add 'Apache License, Version 2.0' (https://www.apache.org/licenses/LICENSE-2.0) to the project."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Project License (Priority: P1)

A developer or third party visits the project repository and needs to understand the terms under which the software is distributed. They look for the LICENSE file at the project root, read the Apache 2.0 terms, and can clearly determine what they are permitted to do with the code.

**Why this priority**: This is the core deliverable — without a LICENSE file, the project has no clear open-source license. All other stories build on this foundation.

**Independent Test**: Can be fully tested by navigating to the project root directory and confirming the presence and correctness of the LICENSE file.

**Acceptance Scenarios**:

1. **Given** a user visits the repository root, **When** they look for the license, **Then** a file named `LICENSE` exists at the root containing the complete, unmodified Apache License, Version 2.0 text.
2. **Given** the LICENSE file exists, **When** a user reads it, **Then** the copyright holder/year line is filled in correctly (not a placeholder).
3. **Given** the LICENSE file exists, **When** a license checker tool scans the repository root, **Then** the project is identified as "Apache-2.0".

---

### User Story 2 - Package Metadata Reflects License (Priority: P2)

A developer consuming the project through its package metadata (Python package metadata, Node.js package.json) can see the license identifier without having to inspect the LICENSE file manually.

**Why this priority**: Package registries, dependency scanners, and tooling rely on metadata fields to identify licenses. Missing metadata means tooling cannot auto-detect the license.

**Independent Test**: Can be tested by inspecting each package's metadata file to confirm the license field is present and correct.

**Acceptance Scenarios**:

1. **Given** the backend Python package metadata (`pyproject.toml`), **When** a user reads the `[project]` section, **Then** a `license` field is present with value `"Apache-2.0"`.
2. **Given** the frontend client `package.json`, **When** a user reads it, **Then** a `"license": "Apache-2.0"` field is present.
3. **Given** the frontend admin `package.json`, **When** a user reads it, **Then** a `"license": "Apache-2.0"` field is present.

---

### User Story 3 - Source Files Carry License Notice (Priority: P3)

A developer viewing an individual source file can see a brief copyright and license notice at the top, directing them to the full LICENSE for the complete terms. This is the standard Apache 2.0 recommended notice practice.

**Why this priority**: Per Apache 2.0 guidelines (Appendix), attaching notices to source files is recommended but optional. It provides clear attribution at the file level, which matters most in a shared/open-source context.

**Independent Test**: Can be tested by checking a representative set of source files across backend (Python) and frontend (TypeScript) to confirm the notice header is present.

**Acceptance Scenarios**:

1. **Given** a Python source file in `backend/app/`, **When** a user views the file header, **Then** a standard Apache 2.0 SPDX short-form notice appears at the top (e.g., `# SPDX-License-Identifier: Apache-2.0`).
2. **Given** a TypeScript/TSX source file in `frontend-client/src/` or `frontend-admin/src/`, **When** a user views the file header, **Then** a standard Apache 2.0 SPDX short-form notice appears at the top (e.g., `// SPDX-License-Identifier: Apache-2.0`).
3. **Given** auto-generated files or vendor/dependency files, **When** checked, **Then** they do NOT have the project license header applied (only project-owned source files are licensed).

---

### User Story 4 - Third-Party License Compatibility Review (Priority: P2)

The project maintainer audits all direct third-party dependencies (Python packages and Node.js packages) to confirm their licenses are compatible with Apache 2.0. Any dependency with an incompatible or unknown license is identified and flagged for resolution before the project is distributed under Apache 2.0.

**Why this priority**: Adopting Apache 2.0 as the project license creates an obligation to ensure bundled or linked dependencies don't impose incompatible license terms. GPL-3.0 or AGPL dependencies in particular can conflict with Apache 2.0 distribution. This must be resolved before the license is published.

**Independent Test**: Can be tested by running a dependency license audit tool against `backend/pyproject.toml` and both `package.json` files and reviewing the output report.

**Acceptance Scenarios**:

1. **Given** the list of direct Python dependencies in `backend/pyproject.toml`, **When** a license audit is run, **Then** every dependency's license is identified (no "Unknown" entries) and none are GPL-3.0, AGPL-3.0, or other copyleft licenses incompatible with Apache 2.0 distribution.
2. **Given** the list of direct Node.js dependencies in `frontend-client/package.json` and `frontend-admin/package.json`, **When** a license audit is run, **Then** every dependency's license is identified and none are incompatible with Apache 2.0.
3. **Given** an audit report is produced, **When** the maintainer reviews it, **Then** the report lists each direct dependency with its SPDX license identifier and a pass/flag status.
4. **Given** a flagged dependency is found, **When** the maintainer reviews it, **Then** a documented decision exists: either confirm compatibility, replace the dependency, or explicitly accept the risk.

---

### Edge Cases

- What happens to files in `.venv/`, `node_modules/`, or other dependency directories? — License headers must NOT be applied to these; they remain under their own respective licenses.
- What about generated migration files (e.g., Alembic migrations)? — These are excluded. SPDX headers apply to `backend/app/` only; migration files in `backend/alembic/` are auto-generated scaffolding and out of scope.
- What if the copyright holder is an organization rather than an individual? — Resolved: copyright holder is Stefan Rosander (see Assumptions).
- What if a direct dependency has an incompatible license (e.g., GPL-3.0)? — The dependency must be replaced, or a written risk-acceptance decision documented, before the project is published under Apache 2.0.
- What about transitive dependencies (dependencies of dependencies)? — Out of scope for this audit; only direct dependencies listed in `pyproject.toml` and `package.json` are reviewed. Transitive dependency audit can be added as a follow-up.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The project MUST include a `LICENSE` file at the repository root containing the full, unmodified text of the Apache License, Version 2.0.
- **FR-002**: The `LICENSE` file MUST include a correctly filled-in copyright line (year and copyright holder name — not a placeholder).
- **FR-003**: The backend package metadata (`backend/pyproject.toml`) MUST declare `license = "Apache-2.0"` in the `[project]` section.
- **FR-004**: The frontend client package metadata (`frontend-client/package.json`) MUST declare `"license": "Apache-2.0"`.
- **FR-005**: The frontend admin package metadata (`frontend-admin/package.json`) MUST declare `"license": "Apache-2.0"`.
- **FR-006**: All project-owned Python source files under `backend/app/` MUST include exactly one line at the top of each file: `# SPDX-License-Identifier: Apache-2.0`.
- **FR-007**: All project-owned TypeScript/TSX source files under `frontend-client/src/` and `frontend-admin/src/` MUST include exactly one line at the top of each file: `// SPDX-License-Identifier: Apache-2.0`.
- **FR-008**: Dependency directories (`.venv/`, `node_modules/`, `dist/`, build artifacts) MUST be excluded from license header application.
- **FR-009**: The `README.md` MUST include a "License" section at the end with the following content:
  ```
  ## License

  Copyright 2026 Stefan Rosander

  Licensed under the [Apache License, Version 2.0](LICENSE).
  ```
- **FR-010**: A license compatibility audit MUST be performed against all direct Python dependencies (from `backend/pyproject.toml`) and all direct Node.js dependencies (from `frontend-client/package.json` and `frontend-admin/package.json`).
- **FR-011**: The audit MUST produce a report listing each direct dependency with its SPDX license identifier and a compatibility verdict (Compatible / Flagged / Unknown).
- **FR-012**: Any dependency flagged as incompatible or Unknown MUST have a documented resolution before this feature is considered complete (replace dependency, confirm compatibility, or record explicit risk acceptance).

### Key Entities

- **LICENSE file**: The canonical legal document at the project root. Contains complete Apache 2.0 text with copyright notice.
- **SPDX identifier**: A short machine-readable comment (`SPDX-License-Identifier: Apache-2.0`) added to source file headers for tooling compatibility.
- **Package metadata**: The `pyproject.toml` and `package.json` files that declare the license identifier for package registries and dependency scanners.
- **License audit report**: A document listing each direct dependency, its SPDX license identifier, and a compatibility verdict (Compatible / Flagged / Unknown). Produced as part of this feature; stored as `specs/015-apache-license/third-party-licenses.md`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of project-owned source files (Python and TypeScript) include the SPDX license identifier header.
- **SC-002**: A license compliance scanner (e.g., `licensee`, `reuse`, or equivalent) run against the repository root reports the project license as "Apache-2.0" with zero missing or ambiguous files.
- **SC-003**: All three package metadata files (`pyproject.toml`, `frontend-client/package.json`, `frontend-admin/package.json`) declare the correct SPDX identifier, verifiable in under 1 minute by inspection.
- **SC-004**: The LICENSE file is present at the repository root. The Apache 2.0 body text it contains (excluding the copyright preamble) matches the canonical text from https://www.apache.org/licenses/LICENSE-2.0.txt.
- **SC-005**: The README.md contains a visible "License" section that a first-time visitor can find without scrolling more than once.
- **SC-006**: A third-party license audit report exists covering 100% of direct Python and Node.js dependencies, with zero Flagged or Unknown entries remaining unresolved.

## Clarifications

### Session 2026-02-23

- Q: Should source file headers include a copyright line alongside the SPDX identifier, or just the SPDX identifier alone? → A: SPDX identifier only (one line per file, no copyright comment, no boilerplate).
- Q: Should Alembic migration files in `backend/alembic/versions/` be included in SPDX header coverage? → A: Excluded — SPDX headers apply to `backend/app/` and `frontend-*/src/` only.

## Assumptions

- Copyright holder: **Stefan Rosander**, year **2026**. The LICENSE file copyright line will read: `Copyright 2026 Stefan Rosander`.
- Source file headers use SPDX identifier only (one line, no copyright comment): `# SPDX-License-Identifier: Apache-2.0` for Python, `// SPDX-License-Identifier: Apache-2.0` for TypeScript. No copyright line per file, no full boilerplate.
- Auto-generated files (Alembic migrations in `backend/alembic/`, compiled assets, build output) are excluded from SPDX header coverage. Only hand-authored source files in `backend/app/` and `frontend-*/src/` are in scope.
- No `NOTICE` file is required unless the project redistributes third-party Apache-2.0-licensed code that mandates attribution in a NOTICE file. This can be added in a follow-up if needed.
