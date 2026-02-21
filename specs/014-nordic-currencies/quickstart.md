# Quickstart: Nordic Currency Alignment (014)

**Feature**: `014-nordic-currencies`
**Date**: 2026-02-21
**Audience**: Developer implementing or verifying the feature

---

## Prerequisites

- Docker Compose stack running (`docker compose up` from `docker/`)
- Database migrated to latest (`docker compose exec backend uv run alembic upgrade head`)
- Admin credentials: `admin@ott.test` / `admin123`

---

## What Gets Changed

| File | Change |
|------|--------|
| `backend/app/models/entitlement.py` | Change `default="USD"` → `"NOK"` on `ContentPackage.currency` and `TitleOffer.currency` |
| `backend/app/seed/seed_entitlements.py` | Update `CURRENCY`, `RENT_PRICE_CENTS`, `BUY_PRICE_CENTS`; add package pricing; add update-in-place for existing TitleOffers |
| `frontend-admin/src/pages/PackagesPage.tsx` | Replace USD/EUR/GBP options with NOK/DKK/SEK; change default from `'USD'` to `'NOK'` |

---

## Development Workflow

### 1. Verify current (broken) state

```bash
docker compose exec backend uv run python -c "
import asyncio
from app.database import async_session_maker
from sqlalchemy import select, text
async def check():
    async with async_session_maker() as s:
        rows = await s.execute(text(\"SELECT name, price_cents, currency FROM content_packages\"))
        for r in rows: print(r)
asyncio.run(check())
"
```
Expected before fix: currency = `USD`, price_cents = `0` for all packages.

### 2. Re-run seeds after implementation

```bash
docker compose exec backend uv run python -m app.seed.run_seeds
```

Expected output includes:
```
[seed_entitlements] Updated N package(s) with NOK pricing.
[seed_entitlements] Updated N title offer(s) to NOK currency.
```

### 3. Verify seed result

```bash
docker compose exec backend uv run python -c "
import asyncio
from app.database import async_session_maker
from sqlalchemy import text
async def check():
    async with async_session_maker() as s:
        pkgs = await s.execute(text(\"SELECT name, price_cents, currency FROM content_packages ORDER BY name\"))
        print('=== Packages ===')
        for r in pkgs: print(f'  {r.name}: {r.price_cents/100:.0f} {r.currency}')
        offers = await s.execute(text(\"SELECT offer_type, price_cents, currency FROM title_offers GROUP BY offer_type, price_cents, currency\"))
        print('=== Offers ===')
        for r in offers: print(f'  {r.offer_type}: {r.price_cents/100:.0f} {r.currency}')
asyncio.run(check())
"
```

Expected:
```
=== Packages ===
  Basic: 99 NOK
  Premium: 249 NOK
  Standard: 149 NOK
=== Offers ===
  buy: 129 NOK
  free: 0 NOK
  rent: 49 NOK
```

### 4. Verify admin UI

Open `http://localhost:5174/packages` and confirm:
- All package prices show in NOK (e.g. "NOK 99.00")
- Currency dropdown in "Add Package" and "Add Offer" forms shows: NOK / DKK / SEK (no USD/EUR/GBP)
- Default currency is NOK

### 5. Verify zero foreign currency references

```bash
docker compose exec backend uv run python -c "
import asyncio
from app.database import async_session_maker
from sqlalchemy import text
async def check():
    async with async_session_maker() as s:
        r = await s.execute(text(\"SELECT COUNT(*) FROM content_packages WHERE currency NOT IN ('NOK','DKK','SEK')\"))
        print('Non-Nordic packages:', r.scalar())
        r = await s.execute(text(\"SELECT COUNT(*) FROM title_offers WHERE currency NOT IN ('NOK','DKK','SEK')\"))
        print('Non-Nordic offers:', r.scalar())
asyncio.run(check())
"
```
Expected: both counts = **0**

---

## Acceptance Checklist

- [ ] `content_packages` table: all rows have `currency` in (NOK, DKK, SEK)
- [ ] `content_packages`: Basic = 9900, Standard = 14900, Premium = 24900 price_cents in NOK
- [ ] `title_offers` table: all rows have `currency` in (NOK, DKK, SEK)
- [ ] `title_offers`: rent = 4900 NOK, buy = 12900 NOK, free = 0 NOK
- [ ] Re-running seeds does not create duplicate packages or offers
- [ ] Admin Packages UI shows NOK prices, not USD/EUR/GBP
- [ ] Currency dropdown in admin forms lists: NOK, DKK, SEK only
- [ ] Default currency in forms is NOK
- [ ] Zero rows with USD/EUR/GBP remain in either table
