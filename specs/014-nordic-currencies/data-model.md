# Data Model: Nordic Currency Alignment (014)

## Affected Entities

### ContentPackage (existing — `content_packages` table)

No schema changes. Python model default updated only.

| Field | Type | Current Default | New Default | Notes |
|-------|------|----------------|-------------|-------|
| `currency` | `String(3)` | `"USD"` | `"NOK"` | ISO 4217 code |
| `price_cents` | `Integer` | `0` | `0` (unchanged) | Set by seed |

**Seed values updated:**

| Package | price_cents | currency |
|---------|------------|---------|
| Basic | 9900 | NOK |
| Standard | 14900 | NOK |
| Premium | 24900 | NOK |

---

### TitleOffer (existing — `title_offers` table)

No schema changes. Python model default updated only.

| Field | Type | Current Default | New Default | Notes |
|-------|------|----------------|-------------|-------|
| `currency` | `String(3)` | `"USD"` | `"NOK"` | ISO 4217 code |

**Seed values updated:**

| Offer type | price_cents | currency |
|-----------|------------|---------|
| free | 0 | NOK |
| rent | 4900 | NOK |
| buy | 12900 | NOK |

---

## Currency → Region Mapping

| Market | Region code | ISO 4217 currency | UI display order |
|--------|-------------|-------------------|-----------------|
| Norway | NO | NOK | 1st |
| Denmark | DK | DKK | 2nd |
| Sweden | SE | SEK | 3rd |

This mapping is used in the frontend currency dropdown and documents the canonical order per FR-002.

---

## No New Tables or Migrations

All changes are to seed data values and Python model defaults. The existing `String(3)` column type accommodates NOK, DKK, and SEK without any schema change.
