# Implementation Plan: Nordic Currency Alignment (014)

**Branch**: `014-nordic-currencies` | **Date**: 2026-02-21 | **Spec**: [spec.md](spec.md)

## Summary

Replace all USD/EUR/GBP currency references in package and offer seed data with Nordic currencies (NOK/DKK/SEK), update model defaults from "USD" to "NOK", and update the admin UI currency dropdown to show only Nordic options. No database migration required — the existing `String(3)` column accommodates the new values. The seed update logic runs update-in-place on existing records.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5+ / React 18 (frontend-admin)
**Primary Dependencies**: FastAPI 0.115+, SQLAlchemy 2.0+ async, React 18, Tailwind CSS 3+
**Storage**: PostgreSQL 16 — `content_packages` and `title_offers` tables (existing schema, no migration)
**Testing**: pytest (backend unit), manual UI verification
**Target Platform**: Docker Compose local stack
**Performance Goals**: No perf requirements — seed-only and UI change
**Constraints**: Seed must be idempotent (update-in-place, no duplicates); no schema migration
**Scale/Scope**: 3 packages × 1 currency, ~28 TVOD title offers

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. PoC-First Quality | PASS | Data fix only — no over-engineering |
| II. Monolithic Simplicity | PASS | No new services or routers |
| III. AI-Native by Default | N/A | Not an AI feature |
| IV. Docker Compose as Truth | PASS | All changes run within existing stack |
| V. Seed Data as Demo | PASS | Improves seed data realism |

## File Structure

### Files Modified

```
backend/
  app/
    models/
      entitlement.py               # Change default="USD" → "NOK" (2 columns)
    seed/
      seed_entitlements.py         # Update currency constant, prices, add update-in-place logic

frontend-admin/
  src/
    pages/
      PackagesPage.tsx             # Replace USD/EUR/GBP options with NOK/DKK/SEK
```

### Files NOT Changed

- No Alembic migration (no schema change)
- No API routes or schemas (currency is a free-form string field in existing API)
- No `admin.ts` API types (currency typed as `string`, no hardcoded values)
- No `seed_users.py` (packages created without price; seed_entitlements updates them)

## Implementation Details

### 1. `backend/app/models/entitlement.py`

Change model-level defaults on two columns:

```python
# ContentPackage
currency: Mapped[str] = mapped_column(String(3), nullable=False, default="NOK", server_default="NOK")

# TitleOffer
currency: Mapped[str] = mapped_column(String(3), nullable=False, default="NOK", server_default="NOK")
```

### 2. `backend/app/seed/seed_entitlements.py`

**Constants block** — replace USD constants with Nordic pricing:
```python
# Nordic pricing (NOK as primary market currency)
RENT_PRICE_CENTS  = 4900   # 49 NOK
BUY_PRICE_CENTS   = 12900  # 129 NOK
RENT_WINDOW_HOURS = 48
CURRENCY          = "NOK"

# Subscription package pricing (NOK)
PACKAGE_PRICING = {
    "Basic":    9900,   # 99 NOK/mo
    "Standard": 14900,  # 149 NOK/mo
    "Premium":  24900,  # 249 NOK/mo
}
```

**Package update loop** — extend to also set `price_cents` and `currency`:
```python
for pkg_name, attrs in PACKAGE_ATTRS.items():
    pkg = packages.get(pkg_name)
    if pkg is None:
        continue
    # existing tier/max_streams logic...
    if pkg.price_cents != PACKAGE_PRICING.get(pkg_name, 0):
        pkg.price_cents = PACKAGE_PRICING.get(pkg_name, 0)
        changed = True
    if pkg.currency != CURRENCY:
        pkg.currency = CURRENCY
        changed = True
```

**TitleOffer update-in-place** — when offer already exists, update currency if it's non-Nordic:
```python
nordic = {"NOK", "DKK", "SEK"}

# Instead of skip-if-exists, fetch and update:
async def _upsert_offer(title_id, offer_type, price_cents, currency, **kwargs):
    result = await session.execute(
        select(TitleOffer).where(
            and_(TitleOffer.title_id == title_id, TitleOffer.offer_type == offer_type)
        )
    )
    existing = result.scalar_one_or_none()
    if existing is None:
        session.add(TitleOffer(title_id=title_id, offer_type=offer_type,
                               price_cents=price_cents, currency=currency, **kwargs))
        return "created"
    elif existing.currency not in nordic:
        existing.currency = currency
        existing.price_cents = price_cents
        return "updated"
    return "skipped"
```

### 3. `frontend-admin/src/pages/PackagesPage.tsx`

Two `useState` defaults and two `<select>` option blocks:

```tsx
// Default state: 'USD' → 'NOK' (appears twice, once in PackageForm, once in OfferForm)
const [currency, setCurrency] = useState(initial?.currency ?? 'NOK')

// Option lists: replace USD/EUR/GBP with NOK/DKK/SEK (appears twice)
<option value="NOK">NOK</option>
<option value="DKK">DKK</option>
<option value="SEK">SEK</option>
```

## Phases

### Phase 1 — Backend model defaults (no migration)
- Update `entitlement.py` model defaults

### Phase 2 — Seed data
- Update constants and pricing in `seed_entitlements.py`
- Add `PACKAGE_PRICING` dict
- Extend package update loop to set `price_cents` and `currency`
- Replace `_offer_exists` + skip pattern with `_upsert_offer` update-in-place pattern

### Phase 3 — Frontend UI
- Replace currency options and defaults in `PackagesPage.tsx`

### Phase 4 — Verify
- Re-run seeds
- Check zero USD/EUR/GBP rows remain
- Confirm UI shows NOK pricing

## Quickstart Reference

See [quickstart.md](quickstart.md) for step-by-step verification commands.
