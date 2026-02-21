# Tasks: Nordic Currency Alignment (014)

**Input**: Design documents from `/specs/014-nordic-currencies/`
**Branch**: `014-nordic-currencies`
**Spec**: 3 user stories (P1 Admin UI, P2 Seed data, P3 Zero residual references)
**No tests requested** — verification via quickstart.md CLI commands

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to
- No Phase 1 Setup or Phase 2 Foundational needed — this is a targeted fix across 3 existing files

---

## Phase 1: Setup (No New Infrastructure)

**Purpose**: This feature modifies 3 existing files only. No project setup, migrations, or new dependencies required.

- [X] T001 Read and understand current currency references: `backend/app/models/entitlement.py`, `backend/app/seed/seed_entitlements.py`, `frontend-admin/src/pages/PackagesPage.tsx`

---

## Phase 2: Foundational — Model Defaults

**Purpose**: Update model-level defaults so any new records created outside the seed also default to NOK. Must complete before seed changes to avoid default-value conflicts.

- [X] T002Update `ContentPackage.currency` default from `"USD"` to `"NOK"` and `server_default` from `"USD"` to `"NOK"` in `backend/app/models/entitlement.py`
- [X] T003Update `TitleOffer.currency` default from `"USD"` to `"NOK"` and `server_default` from `"USD"` to `"NOK"` in `backend/app/models/entitlement.py`

**Checkpoint**: Model defaults changed — no migration needed (String(3) column accepts NOK/DKK/SEK)

---

## Phase 3: User Story 2 — Seed Data with Realistic Nordic Pricing (Priority: P2)

> **Note on phase ordering**: US2 (seed/P2) is implemented before US1 (UI/P1) because the admin UI verification in Phase 4 depends on correct seed data already being present. The spec priority (P1 = highest) reflects business importance, not implementation sequence.

**Goal**: Re-running the seed updates all existing packages and title offers to Nordic currencies with realistic price points.

**Independent Test**: Run `docker compose exec backend uv run python -m app.seed.run_seeds` then verify all `content_packages` rows show NOK currency and realistic price_cents (9900/14900/24900), and all `title_offers` rows show NOK with 0/4900/12900.

### Implementation for User Story 2

- [X] T004 [US2] Replace `CURRENCY = "USD"`, `RENT_PRICE_CENTS = 399`, `BUY_PRICE_CENTS = 999` constants with `CURRENCY = "NOK"`, `RENT_PRICE_CENTS = 4900` (49 NOK), `BUY_PRICE_CENTS = 12900` (129 NOK), and add `PACKAGE_PRICING = {"Basic": 9900, "Standard": 14900, "Premium": 24900}` in `backend/app/seed/seed_entitlements.py`

- [X] T005 [US2] Extend the package update loop (lines ~97–109) to also update `pkg.price_cents` from `PACKAGE_PRICING` and `pkg.currency` to `CURRENCY` when they differ from the target values in `backend/app/seed/seed_entitlements.py`

- [X] T006 [US2] Replace the `_offer_exists` helper and skip-if-exists pattern with an `_upsert_offer` helper that: (a) inserts the offer if it doesn't exist, (b) updates `currency` and `price_cents` on the existing offer if `currency` is not in `{"NOK", "DKK", "SEK"}`, (c) skips if already correct — in `backend/app/seed/seed_entitlements.py`

- [X] T007 [US2] Update all three `session.add(TitleOffer(...))` call sites for free, rent, and buy offers to use the new `_upsert_offer` helper, and update the print statement to report updated offers separately from created offers in `backend/app/seed/seed_entitlements.py`

**Checkpoint**: Run seed — all packages show NOK pricing, all title offers show NOK; re-running seed is a no-op (no duplicates, no unnecessary updates)

---

## Phase 4: User Story 1 — Admin UI Shows Nordic Currencies (Priority: P1)

**Goal**: The Packages & Offers admin page currency dropdown lists NOK/DKK/SEK only (order: NO→DK→SE), and defaults to NOK.

**Independent Test**: Open `http://localhost:5174/packages` — all displayed package prices show NOK amounts; the "Add Package" and "Add Offer" currency dropdowns show NOK/DKK/SEK with NOK pre-selected.

### Implementation for User Story 1

- [X] T008 [US1] Replace the two `useState('USD')` defaults (one in the package form, one in the offer form) with `useState(initial?.currency ?? 'NOK')` and `useState('NOK')` respectively in `frontend-admin/src/pages/PackagesPage.tsx`

- [X] T009 [US1] Replace both sets of `<option value="USD">USD</option> / EUR / GBP` with `<option value="NOK">NOK</option> / <option value="DKK">DKK</option> / <option value="SEK">SEK</option>` (two separate `<select>` blocks at lines ~139–141 and ~436–438) in `frontend-admin/src/pages/PackagesPage.tsx`

**Checkpoint**: Admin UI shows only Nordic currencies; existing packages display NOK prices; no USD/EUR/GBP options appear in any form

---

## Phase 5: User Story 3 — Zero Residual Foreign Currency References (Priority: P3)

**Goal**: After implementing US1 and US2, confirm zero USD/EUR/GBP references survive in package data or UI.

**Independent Test**: Run the verification commands from `quickstart.md` — both SQL queries return count = 0; grep for "USD"/"EUR"/"GBP" in the three modified files returns no currency-value matches.

### Implementation for User Story 3

- [X] T010 [US3] Verify `backend/app/seed/seed_entitlements.py` contains no remaining `"USD"`, `"EUR"`, or `"GBP"` string literals used as currency values (comments referencing old prices like `# $3.99` should be updated to reflect NOK amounts)

- [X] T011 [US3] Update inline comments in `backend/app/seed/seed_entitlements.py` that reference dollar amounts (e.g. `# $3.99`, `# $9.99`) to reflect the new NOK amounts (e.g. `# 49 NOK`, `# 129 NOK`)

**Checkpoint**: grep for USD/EUR/GBP in seed file finds zero currency-value literals; database verification confirms zero non-Nordic rows

---

## Phase 6: Polish & Verification

**Purpose**: Run end-to-end verification per quickstart.md and commit.

- [X] T012 Re-run seeds against the running stack: `docker compose exec backend uv run python -m app.seed.run_seeds` and confirm output reports NOK updates
- [X] T013 [P] Run DB verification queries from `quickstart.md` step 3 and step 5 — confirm all packages show correct NOK price_cents and zero non-Nordic currency rows remain
- [X] T014 [P] Manually verify admin UI at `http://localhost:5174/packages` — prices display in NOK, dropdown shows NOK/DKK/SEK only

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Read)**: No dependencies — start immediately
- **Phase 2 (Model defaults)**: After Phase 1 — blocks nothing else but should be done first
- **Phase 3 (Seed)**: After Phase 2 — depends on model defaults being correct
- **Phase 4 (UI)**: Independent of Phases 2–3 — can run in parallel with Phase 3
- **Phase 5 (Verification)**: After Phases 3 and 4 — confirms no residuals
- **Phase 6 (Polish)**: After all implementation phases complete

### Parallel Opportunities

- T008 and T009 (UI changes) can run in parallel with T004–T007 (seed changes) — different files
- T013 and T014 (verification) can run in parallel — independent checks

### Within Seed Phase (Phase 3)

- T004 must complete before T005, T006, T007 (constants must exist before use)
- T005, T006 can run in parallel (different functions in same file)
- T007 depends on T006 (uses the new helper)

---

## Implementation Strategy

### MVP: All 3 stories are tightly coupled — implement in sequence

1. **Phase 1**: Read the 3 files
2. **Phase 2**: Update model defaults (2 lines changed)
3. **Phase 3**: Update seed (constants + package loop + offer upsert)
4. **Phase 4**: Update UI (2 useState + 2 select blocks)
5. **Phase 5**: Remove residual comments
6. **Phase 6**: Run verification — confirm 0/10 checklist items fail

Total: ~50 lines changed across 3 files. No migration, no new files.
