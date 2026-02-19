# Quickstart: Subscription Tiers, Entitlements & TVOD

**Branch**: `012-entitlements-tvod` | **Date**: 2026-02-17

---

## Prerequisites

- Docker Compose stack running (`docker compose up`)
- Migration 004 already applied (current baseline)

---

## Setup

### 1. Add `slowapi` dependency

```bash
cd backend
uv add slowapi
```

### 2. Apply migration

```bash
cd backend
alembic upgrade head
```

This applies migration `005_subscription_entitlements_tvod.py`, which:
- Creates `title_offers` and `viewing_sessions` tables
- Makes `user_entitlements.package_id` nullable
- Adds `user_entitlements.title_id` column
- Adds `content_packages.tier` column

### 3. Run seed data

```bash
cd backend
python -m app.seed.run_seeds
```

Seed data includes:
- 2 packages: "Basic" (tier=basic) and "Premium" (tier=premium)
- 30 titles assigned to Basic, 80 titles assigned to Premium
- Sample rental offer ($3.99 / 48h) and buy offer ($9.99) on 20 titles
- Test users: `basic@test.com` (Basic plan), `premium@test.com` (Premium plan), `noplan@test.com` (no subscription)

---

## Manual Test Flows

### Test SVOD enforcement

```bash
# Login as basic user
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"basic@test.com","password":"test1234"}' | jq -r '.access_token')

# Get a title — should show access_options + user_access
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/catalog/titles | jq '.[0].access_options'

# Try to play a Premium-only title as Basic user — expect 403
PREMIUM_TITLE_ID="<UUID of a premium-only title from catalog>"
curl -H "Authorization: Bearer $TOKEN" \
  -X POST http://localhost:8000/api/v1/viewing/sessions \
  -H "Content-Type: application/json" \
  -d "{\"title_id\": \"$PREMIUM_TITLE_ID\", \"content_type\": \"vod_title\"}"
# Expected: 403 with access_options showing rent/buy alternatives
```

### Test TVOD rental

```bash
# Login as user with no subscription
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"noplan@test.com","password":"test1234"}' | jq -r '.access_token')

# Find a title with a rent offer
TITLE_ID="<UUID of a title with rental offer>"

# Rent it
curl -H "Authorization: Bearer $TOKEN" \
  -X POST "http://localhost:8000/api/v1/catalog/titles/$TITLE_ID/purchase" \
  -H "Content-Type: application/json" \
  -d '{"offer_type": "rent"}'
# Expected: 201 with expires_at ~48h from now

# Start playback — should succeed now
curl -H "Authorization: Bearer $TOKEN" \
  -X POST http://localhost:8000/api/v1/viewing/sessions \
  -H "Content-Type: application/json" \
  -d "{\"title_id\": \"$TITLE_ID\", \"content_type\": \"vod_title\"}"
# Expected: 201 with session_id
```

### Test concurrent stream limits

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"basic@test.com","password":"test1234"}' | jq -r '.access_token')

TITLE_ID="<UUID of a Basic-plan title>"

# Start first session — OK
SESSION1=$(curl -s -H "Authorization: Bearer $TOKEN" \
  -X POST http://localhost:8000/api/v1/viewing/sessions \
  -H "Content-Type: application/json" \
  -d "{\"title_id\": \"$TITLE_ID\", \"content_type\": \"vod_title\"}" | jq -r '.session_id')

# Start second session from same account — should fail (Basic = 1 stream)
curl -H "Authorization: Bearer $TOKEN" \
  -X POST http://localhost:8000/api/v1/viewing/sessions \
  -H "Content-Type: application/json" \
  -d "{\"title_id\": \"$TITLE_ID\", \"content_type\": \"vod_title\"}"
# Expected: 429 with active_sessions list

# Stop first session
curl -H "Authorization: Bearer $TOKEN" \
  -X DELETE "http://localhost:8000/api/v1/viewing/sessions/$SESSION1"

# Now second session succeeds
curl -H "Authorization: Bearer $TOKEN" \
  -X POST http://localhost:8000/api/v1/viewing/sessions \
  -H "Content-Type: application/json" \
  -d "{\"title_id\": \"$TITLE_ID\", \"content_type\": \"vod_title\"}"
# Expected: 201
```

### Test guest catalog access

```bash
# No auth header — should see catalog with offers but no user_access
curl http://localhost:8000/api/v1/catalog/titles | jq '.[0] | {title, access_options}'
# Expected: access_options present, no user_access field

# Try to play without auth — expect redirect to login (401)
curl -X POST http://localhost:8000/api/v1/viewing/sessions \
  -H "Content-Type: application/json" \
  -d '{"title_id": "uuid", "content_type": "vod_title"}'
# Expected: 401 Unauthorized
```

### Test admin package management

```bash
ADMIN_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"admin1234"}' | jq -r '.access_token')

# Create a new package
PACKAGE=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  -X POST http://localhost:8000/api/v1/admin/packages \
  -H "Content-Type: application/json" \
  -d '{"name": "Sports Pack", "tier": "sports"}' | jq -r '.id')

# Assign a title
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  -X POST "http://localhost:8000/api/v1/admin/packages/$PACKAGE/titles" \
  -H "Content-Type: application/json" \
  -d "{\"title_id\": \"$TITLE_ID\"}"

# Update a user's subscription to this package
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  -X PATCH "http://localhost:8000/api/v1/admin/users/$USER_ID/subscription" \
  -H "Content-Type: application/json" \
  -d "{\"package_id\": \"$PACKAGE\"}"
```

---

## Verifying Rate Limits

```bash
# Hit the catalog 101 times as same user — 101st should return 429
for i in {1..101}; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $TOKEN" \
    http://localhost:8000/api/v1/catalog/titles)
  echo "Request $i: $STATUS"
done

# Verify Retry-After header on 429
curl -v -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/catalog/titles 2>&1 | grep -i retry-after
```
