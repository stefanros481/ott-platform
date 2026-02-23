# Tasks: Apache License 2.0

**Input**: Design documents from `/specs/015-apache-license/`
**Prerequisites**: plan.md ✅ research.md ✅ quickstart.md ✅ third-party-licenses.md ✅

**Tests**: Not requested — compliance tasks are verified via quickstart.md grep commands.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US4)

---

## Phase 1: Setup

**Purpose**: Fetch the canonical license text that US1 depends on.

- [ ] T001 Fetch Apache License 2.0 plain text from https://www.apache.org/licenses/LICENSE-2.0.txt, save to `/tmp/apache-2.0.txt`, and confirm it matches the expected content (starts with "Apache License", "Version 2.0") — this file is used directly by T002

**Checkpoint**: Canonical license text available — US1 can begin.

---

## Phase 2: User Story 1 — View Project License (Priority: P1) 🎯 MVP

**Goal**: A `LICENSE` file exists at the repo root with the correct copyright notice and the complete Apache 2.0 text, making the project's license immediately discoverable.

**Independent Test**:
```bash
ls LICENSE && head -3 LICENSE && grep "Apache License" LICENSE | head -1
```

### Implementation

- [ ] T002 [US1] Create `LICENSE` at repo root: prepend `Copyright 2026 Stefan Rosander` followed by a blank line, then the full Apache 2.0 text fetched in T001

**Checkpoint**: `LICENSE` exists, copyright line correct, Apache 2.0 text complete. US1 independently testable.

---

## Phase 3: User Story 2 — Package Metadata Reflects License (Priority: P2)

**Goal**: All three package metadata files declare `Apache-2.0` so dependency scanners and registries can auto-detect the license.

**Independent Test**:
```bash
grep "^license" backend/pyproject.toml
node -e "console.log(require('./frontend-client/package.json').license)"
node -e "console.log(require('./frontend-admin/package.json').license)"
```
All three should output `Apache-2.0`.

### Implementation

- [ ] T003 [P] [US2] Add `license = "Apache-2.0"` to the `[project]` section in `backend/pyproject.toml` (after the `description` field)
- [ ] T004 [P] [US2] Add `"license": "Apache-2.0"` field to `frontend-client/package.json` (after the `"version"` field)
- [ ] T005 [P] [US2] Add `"license": "Apache-2.0"` field to `frontend-admin/package.json` (after the `"version"` field)

**Checkpoint**: All three metadata files declare `Apache-2.0`. T003–T005 are fully independent (different files).

---

## Phase 4: User Story 3 — Source Files Carry License Notice (Priority: P3)

**Goal**: Every project-owned source file has `# SPDX-License-Identifier: Apache-2.0` (Python) or `// SPDX-License-Identifier: Apache-2.0` (TypeScript) as its first line.

**Scope**: 64 Python files in `backend/app/`, 45 TypeScript files in `frontend-client/src/`, 20 TypeScript files in `frontend-admin/src/`. Migrations, `.venv/`, `node_modules/`, and build artifacts are excluded.

**Independent Test**:
```bash
find backend/app -name "*.py" | xargs grep -L "SPDX-License-Identifier" | wc -l  # → 0
find frontend-client/src frontend-admin/src \( -name "*.ts" -o -name "*.tsx" \) \
  | xargs grep -L "SPDX-License-Identifier" | wc -l  # → 0
```

### Implementation

- [ ] T006 [P] [US3] Add `# SPDX-License-Identifier: Apache-2.0` to all 64 `.py` files under `backend/app/` — insert as first line, or after any shebang (`#!/`) or encoding declaration (`# -*- coding`), whichever comes first; verify with grep after
- [ ] T007 [P] [US3] Add `// SPDX-License-Identifier: Apache-2.0` as the first line of all 45 `.ts`/`.tsx` files under `frontend-client/src/` (use a single-pass script or loop; verify with grep after)
- [ ] T008 [P] [US3] Add `// SPDX-License-Identifier: Apache-2.0` as the first line of all 20 `.ts`/`.tsx` files under `frontend-admin/src/` (use a single-pass script or loop; verify with grep after)

> **Note on implementation approach**: T006–T008 can be done with a one-liner per directory, e.g.:
> ```bash
> # Python
> for f in $(find backend/app -name "*.py"); do
>   sed -i '' '1s/^/# SPDX-License-Identifier: Apache-2.0\n/' "$f"
> done
> # TypeScript
> for f in $(find frontend-client/src -name "*.ts" -o -name "*.tsx"); do
>   sed -i '' '1s/^/\/\/ SPDX-License-Identifier: Apache-2.0\n/' "$f"
> done
> ```

**Checkpoint**: Zero files missing SPDX header across all three directories. T006–T008 are independent (different directories).

---

## Phase 5: User Story 4 — Third-Party License Compatibility Review (Priority: P2)

**Goal**: Confirm the pre-completed audit report is accurate and satisfies FR-010–FR-012.

**Status**: The audit report was pre-completed during planning. All 28 direct dependencies passed (✅ Compatible). This phase validates the artifact rather than generating it.

**Independent Test**:
```bash
grep "Overall Verdict" specs/015-apache-license/third-party-licenses.md
# → ✅ PASS
grep "Flagged\|Unknown" specs/015-apache-license/third-party-licenses.md | grep -v "^#\|Format\|verdict\|Compatibility"
# → no output
```

### Implementation

- [ ] T009 [US4] Review `specs/015-apache-license/third-party-licenses.md` and confirm: (a) all 15 Python direct deps are listed with SPDX identifiers, (b) all 13 Node.js direct deps are listed, (c) all verdicts are ✅ Compatible, (d) Overall Verdict is ✅ PASS
- [ ] T010 [US4] Cross-check the audit against the installed packages: run `uv pip show <package> | grep License` for any packages where the audit license is uncertain (fastapi, uvicorn, asyncpg, sentence-transformers); update report if any discrepancy found

**Checkpoint**: Audit report confirmed accurate. SC-006 satisfied.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Remaining deliverables that span multiple user stories.

- [ ] T011 Add `## License` section to the end of `README.md` with content:
  ```
  ## License

  Copyright 2026 Stefan Rosander

  Licensed under the [Apache License, Version 2.0](LICENSE).
  ```
- [ ] T012 Run the all-in-one quickstart verification from `specs/015-apache-license/quickstart.md` and confirm: (a) LICENSE exists, (b) all metadata files show `Apache-2.0`, (c) zero Python files missing SPDX header, (d) zero TypeScript files missing SPDX header, (e) README has License section, (f) dependency dirs are clean: `grep -r "SPDX-License-Identifier" backend/.venv 2>/dev/null | wc -l` → 0
- [ ] T013 [P] Update `specs/015-apache-license/checklists/requirements.md` — mark all items complete

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (US1)**: Depends on T001 (needs license text)
- **Phase 3 (US2)**: Independent — can start any time (no dependency on US1)
- **Phase 4 (US3)**: Independent — can start any time (no dependency on US1 or US2)
- **Phase 5 (US4)**: Independent — audit report already exists
- **Phase 6 (Polish)**: Depends on US1 (for README link to LICENSE), US2, US3, US4 complete

### User Story Dependencies

- **US1 (P1)**: Depends on T001 only
- **US2 (P2)**: No dependencies — fully independent
- **US3 (P3)**: No dependencies — fully independent
- **US4 (P2)**: No dependencies — artifact pre-exists

### Parallel Opportunities

- T003, T004, T005 (US2) — fully parallel (different files)
- T006, T007, T008 (US3) — fully parallel (different directories)
- T009, T010 (US4) — T010 depends on T009
- US2, US3, US4 phases can all run in parallel with each other

---

## Implementation Strategy

### MVP First (US1 Only)

1. T001 — Fetch license text
2. T002 — Create LICENSE file
3. **STOP and VALIDATE**: `ls LICENSE && grep "Apache License" LICENSE`
4. Project is now legally licensed — all other tasks are compliance enhancements

### Recommended Execution Order (single developer)

```
T001 → T002 (US1 complete)
     → T003, T004, T005 in parallel (US2 complete)
     → T006, T007, T008 in parallel (US3 complete)
     → T009, T010 (US4 complete)
     → T011, T012, T013
```

### Total Task Count

| Phase | Tasks | Parallel |
|-------|-------|---------|
| Phase 1: Setup | 1 | 0 |
| Phase 2: US1 | 1 | 0 |
| Phase 3: US2 | 3 | 3 |
| Phase 4: US3 | 3 | 3 |
| Phase 5: US4 | 2 | 0 |
| Phase 6: Polish | 3 | 1 |
| **Total** | **13** | **7** |

---

## Notes

- T006–T008 are bulk operations on many files. Use a shell loop or `sed -i` to add headers efficiently rather than editing each file manually.
- After T006–T008, verify with `grep -L "SPDX"` to catch any missed files (output should be empty).
- The audit report (T009–T010) was pre-generated during `/speckit.plan` — only verification is needed.
- Commit after each phase checkpoint to keep progress safe.
