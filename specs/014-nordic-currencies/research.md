# Research: Nordic Currency Alignment (014)

## Finding 1: Scope of currency references

**Decision**: Three files need changes — `seed_entitlements.py` (seed logic), `entitlement.py` (model defaults), and `PackagesPage.tsx` (frontend UI).

**Rationale**: A grep across the codebase found currency values in exactly these locations:
- `backend/app/seed/seed_entitlements.py` — `CURRENCY = "USD"`, `RENT_PRICE_CENTS = 399`, `BUY_PRICE_CENTS = 999`
- `backend/app/models/entitlement.py` — `default="USD", server_default="USD"` on both `ContentPackage.currency` and `TitleOffer.currency`
- `frontend-admin/src/pages/PackagesPage.tsx` — three `<option>` elements (USD/EUR/GBP) and two `useState('USD')` defaults

**Alternatives considered**: `admin.ts` API types also reference `currency: string` but as a generic type — no currency-specific value is hardcoded there, so no change needed.

---

## Finding 2: ContentPackage has no region field

**Decision**: Since `ContentPackage` (Basic/Standard/Premium) is market-wide with no per-region pricing, assign NOK as the single currency for subscription packages. The currency dropdown in the admin UI should offer NOK/DKK/SEK to allow manual entry of market-specific offers.

**Rationale**: The model has no `region` column. Introducing per-region package variants is out of scope. NOK is the primary market (Norway) per spec assumptions.

**Alternatives considered**: Creating three variants of each package (one per currency) would require schema changes and is out of scope.

---

## Finding 3: Realistic Nordic TVOD pricing

**Decision**:
- Rent: **49 NOK** (4900 price_cents) — equivalent to a typical Nordic VOD rental
- Buy: **129 NOK** (12900 price_cents) — equivalent to a typical Nordic digital purchase
- Subscription pricing for packages:
  - Basic: **99 NOK/mo** (9900 price_cents)
  - Standard: **149 NOK/mo** (14900 price_cents)
  - Premium: **249 NOK/mo** (24900 price_cents)

**Rationale**: Nordic streaming market benchmarks (Viaplay, Netflix NO, Max NO) as of 2026: basic tiers ~79–129 NOK, standard ~149–179 NOK, premium ~199–299 NOK. TVOD rentals ~39–59 NOK, purchases ~99–149 NOK.

---

## Finding 4: Idempotency for TitleOffers (update-in-place)

**Decision**: The existing TitleOffer seed skips insertion if the offer already exists (`_offer_exists` check). It must be extended to also **update the `currency` field** on existing offers when currency is not already a Nordic code.

**Rationale**: Per clarification (FR-007), existing records must be updated in place rather than skipped. The update-in-place pattern is already used for `ContentPackage` tier/max_streams in the same seed file.

---

## Finding 5: No Alembic migration needed

**Decision**: No database migration required.

**Rationale**: The `currency` column is `String(3)` with no CHECK constraint limiting values to specific codes. Changing the Python-level default and the `server_default` (from `"USD"` to `"NOK"`) only affects new records created outside the seed flow. Existing data is updated via the seed update-in-place logic.
