# Feature Specification: Nordic Currency Alignment for Packages & Offers

**Feature Branch**: `014-nordic-currencies`
**Created**: 2026-02-21
**Status**: Draft
**GitHub Issue**: #3

## Clarifications

### Session 2026-02-21

- Q: When re-seeding, should existing packages with old currencies be skipped, updated in place, or deleted and re-created? → A: Update existing packages in place, replacing USD/EUR/GBP currency values with the correct Nordic currency.

## Overview

The platform serves three Nordic markets — Norway (NO), Denmark (DK), and Sweden (SE) — but the Packages & Offers data currently uses non-Nordic currencies (USD, EUR, GBP). This creates a data inconsistency between the analytics layer (correctly scoped to Nordic regions) and the commercial/pricing layer. This feature corrects all currency references to use the local currency for each Nordic market.

## User Scenarios & Testing

### User Story 1 — Admin views packages with correct Nordic currencies (Priority: P1)

An admin navigating to the Packages & Offers section of the dashboard sees pricing displayed in the correct local currency for each market: NOK for Norway, DKK for Denmark, and SEK for Sweden. No USD, EUR, or GBP values appear anywhere in the packages list or detail views.

**Why this priority**: The admin dashboard is the primary surface where currency data is shown. Correctness here directly affects trust in the commercial data and any downstream reporting.

**Independent Test**: Open the Packages & Offers admin page and verify that every package displays a Nordic currency (NOK, DKK, or SEK) and that price values are realistic for each currency.

**Acceptance Scenarios**:

1. **Given** the admin is logged in, **When** they navigate to Packages & Offers, **Then** all packages show prices in NOK, DKK, or SEK — no USD, EUR, or GBP appear.
2. **Given** a package priced at "99 NOK", **When** displayed in the UI, **Then** the price is shown as a value consistent with Norwegian kroner (e.g. 99 NOK or kr 99), not as a dollar/euro/pound amount.
3. **Given** packages across all three markets, **When** sorted or filtered, **Then** the currency order presented follows: NO (NOK) first, DK (DKK) second, SE (SEK) third.

---

### User Story 2 — Seed data produces realistic Nordic pricing (Priority: P2)

When the platform is freshly seeded (e.g. on first startup or after a reset), all generated packages use realistic price points in local currencies. A basic streaming subscription in Norway costs roughly what a real market player would charge in NOK, not a USD amount incorrectly labelled as NOK.

**Why this priority**: Realistic seed data ensures that demos, analytics queries, and admin reviews convey credible pricing information for the target markets.

**Independent Test**: Re-seed the platform and inspect the packages table. Verify price values match typical market rates for each currency (e.g. 99–299 NOK, 79–249 DKK, 99–349 SEK for streaming tiers).

**Acceptance Scenarios**:

1. **Given** a fresh seed run, **When** the packages table is inspected, **Then** all currency fields contain only NOK, DKK, or SEK.
2. **Given** a package for the Norwegian market, **When** its price is examined, **Then** `price_cents` reflects the NOK amount × 100 (e.g. 99 NOK = 9900 price_cents).
3. **Given** packages for all three markets, **When** prices are compared, **Then** each market's prices fall within a realistic local range — not a 1:1 conversion from USD/EUR/GBP.

---

### User Story 3 — No residual foreign currency references exist (Priority: P3)

After the fix, a thorough review of the system finds zero references to USD, EUR, or GBP in package-related data, configuration, or display labels. The platform is consistent end-to-end.

**Why this priority**: Residual references undermine trust and could resurface in future features (e.g. invoicing, reporting, entitlement exports).

**Independent Test**: Search the package seed data and any currency-related UI labels for USD, EUR, GBP — expect zero results.

**Acceptance Scenarios**:

1. **Given** the full package dataset after seeding, **When** searched for "USD", "EUR", or "GBP", **Then** zero results are found.
2. **Given** the admin UI for Packages & Offers, **When** all pages are reviewed, **Then** no foreign currency symbols ($, €, £) appear in package pricing contexts.

---

### Edge Cases

- What happens if a package has no region assigned — which currency applies? (Assumption: default to NOK as the primary market.)
- How should price display behave if a currency code is missing or null? Show a clear placeholder rather than silently displaying "0" or crashing.
- Are there packages that intentionally span multiple markets with a single price? If so, each market variant should carry its own currency.

## Requirements

### Functional Requirements

- **FR-001**: All content packages in seed data MUST use NOK, DKK, or SEK as the currency field — no other currencies are permitted.
- **FR-002**: The currency order for display and seed generation MUST follow: NO → NOK, DK → DKK, SE → SEK.
- **FR-003**: `price_cents` values MUST represent the local currency amount multiplied by 100 (e.g. 149 NOK = 14900 price_cents).
- **FR-004**: Price values MUST reflect realistic local market rates, not 1:1 conversions from USD, EUR, or GBP.
- **FR-005**: The Packages & Offers admin page MUST display the currency code (NOK/DKK/SEK) alongside each price.
- **FR-006**: The system MUST contain zero references to USD, EUR, or GBP in package seed data after the fix is applied.
- **FR-007**: Seed data MUST be idempotent — re-running the seed MUST update existing packages in place (replacing any USD/EUR/GBP currency values with the correct Nordic currency and recalculating `price_cents`), never creating duplicates.

### Key Entities

- **ContentPackage**: A subscription or transactional offering with a price, currency, and associated region. Key attributes: `price_cents` (integer, currency-unit × 100), `currency` (ISO 4217 code: NOK, DKK, or SEK).
- **Region mapping**: The logical link between a market identifier (NO, DK, SE) and its ISO 4217 currency code (NOK, DKK, SEK).

## Success Criteria

### Measurable Outcomes

- **SC-001**: 100% of seeded packages use NOK, DKK, or SEK — zero packages with USD, EUR, or GBP currency codes remain after seeding.
- **SC-002**: All displayed prices on the Packages & Offers admin page show a Nordic currency code with no foreign currency symbols.
- **SC-003**: Seeded subscription package prices fall within a realistic NOK range (Basic: 99 NOK, Standard: 149 NOK, Premium: 249 NOK). DKK and SEK apply only to manually-created offers via the admin UI currency dropdown, which lists all three Nordic currencies.
- **SC-004**: Re-seeding on a clean database produces the same correct results every time (100% idempotent).

## Assumptions

- The platform's only supported markets are NO, DK, and SE — no other currencies need to be introduced.
- "Realistic pricing" is defined as typical Nordic streaming subscription rates (approximately NOK 99–299 / DKK 79–249 / SEK 99–349 per month for standard tiers).
- The fix is data and display only — no payment gateway integration or live transaction processing is in scope.
- Existing package schema supports the `currency` field as a string; no schema migration is required beyond updating seed values.

## Out of Scope

- Payment processing or live currency conversion.
- Adding support for additional currencies or markets beyond NO, DK, SE.
- Localisation of the UI into Norwegian, Danish, or Swedish languages.
- Historical data migration for analytics events (analytics layer already uses correct region codes).
