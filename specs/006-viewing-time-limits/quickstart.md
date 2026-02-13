# Quickstart: Profile Viewing Time Limits

**Feature**: 006-viewing-time-limits
**Date**: 2026-02-13

## Prerequisites

- Docker Compose stack running (`docker compose up`)
- Existing user account with at least one child profile (`is_kids = true`)
- Seed data loaded (includes educational content tags)

## Verification Scenarios

### 1. Set Up PIN and Configure Limits

```bash
# 1a. Create a PIN (first time)
curl -X POST http://localhost:8000/api/v1/parental-controls/pin \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"new_pin": "1234"}'
# Expected: 200 {"detail": "PIN set successfully"}

# 1b. Verify PIN
curl -X POST http://localhost:8000/api/v1/parental-controls/pin/verify \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pin": "1234"}'
# Expected: 200 {"verified": true, "pin_token": null}

# 1c. Configure viewing time for child profile
curl -X PUT http://localhost:8000/api/v1/parental-controls/profiles/$CHILD_PROFILE_ID/viewing-time \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "weekday_limit_minutes": 120,
    "weekend_limit_minutes": 180,
    "reset_hour": 6,
    "educational_exempt": true,
    "timezone": "Europe/Berlin"
  }'
# Expected: 200 with full config object
```

### 2. Simulate Playback and Time Tracking

```bash
# 2a. Check playback eligibility
curl http://localhost:8000/api/v1/viewing-time/playback-eligible/$CHILD_PROFILE_ID \
  -H "Authorization: Bearer $TOKEN"
# Expected: 200 {"eligible": true, "remaining_minutes": 120, ...}

# 2b. Send first heartbeat (creates session)
curl -X POST http://localhost:8000/api/v1/viewing-time/heartbeat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "profile_id": "'$CHILD_PROFILE_ID'",
    "title_id": "'$TITLE_ID'",
    "device_id": "demo-tv-001",
    "device_type": "tv"
  }'
# Expected: 200 {"session_id": "...", "enforcement": "allowed", "remaining_minutes": 119.5, ...}

# 2c. Check balance after some heartbeats
curl http://localhost:8000/api/v1/viewing-time/balance/$CHILD_PROFILE_ID \
  -H "Authorization: Bearer $TOKEN"
# Expected: 200 with updated used_minutes and remaining_minutes
```

### 3. Verify PIN Lockout

```bash
# 3a. Enter wrong PIN 5 times
for i in {1..5}; do
  curl -X POST http://localhost:8000/api/v1/parental-controls/pin/verify \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"pin": "0000"}'
done
# Expected: Last response 403 {"detail": "Incorrect PIN. 0 attempt(s) remaining."}

# 3b. Verify lockout is active
curl -X POST http://localhost:8000/api/v1/parental-controls/pin/verify \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pin": "1234"}'
# Expected: 403 {"detail": "PIN locked due to too many failed attempts"}
# Note: X-Locked-Until header contains the lockout expiry timestamp
```

### 4. Verify PIN Reset via Password

```bash
curl -X POST http://localhost:8000/api/v1/parental-controls/pin/reset \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"password": "user_password_here", "new_pin": "5678"}'
# Expected: 200 — PIN reset, lockout cleared
```

### 5. Grant Extra Time

```bash
# 5a. Grant from parent's device (no PIN needed)
curl -X POST http://localhost:8000/api/v1/parental-controls/profiles/$CHILD_PROFILE_ID/viewing-time/grant \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"minutes": 30}'
# Expected: 200 {"remaining_minutes": 30.0, "granted_minutes": 30}

# 5b. Grant unlimited for today
curl -X POST http://localhost:8000/api/v1/parental-controls/profiles/$CHILD_PROFILE_ID/viewing-time/grant \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"minutes": null}'
# Expected: 200 {"remaining_minutes": null, "granted_minutes": null}
```

### 6. Verify Educational Content Exemption

```bash
# Send heartbeat for an educational title
curl -X POST http://localhost:8000/api/v1/viewing-time/heartbeat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "profile_id": "'$CHILD_PROFILE_ID'",
    "title_id": "'$EDUCATIONAL_TITLE_ID'",
    "device_id": "demo-tv-001",
    "device_type": "tv"
  }'
# Expected: 200 {"enforcement": "allowed", "is_educational": true, ...}
# remaining_minutes should NOT decrease
```

### 7. Verify Viewing History

```bash
curl "http://localhost:8000/api/v1/parental-controls/profiles/$CHILD_PROFILE_ID/history?from_date=2026-02-01&to_date=2026-02-13" \
  -H "Authorization: Bearer $TOKEN"
# Expected: 200 with daily grouped sessions showing title, duration, device, educational flag
```

### 8. Verify Weekly Report

```bash
curl http://localhost:8000/api/v1/parental-controls/weekly-report \
  -H "Authorization: Bearer $TOKEN"
# Expected: 200 with per-profile daily totals, averages, most-watched content
```

## Demo Scenario (End-to-End)

1. Log in as parent → Set PIN → Configure child profile: 15-minute weekday limit (for quick demo)
2. Switch to child profile → See "15m left today" indicator
3. Start watching a regular title → Heartbeats decrement balance → Warning at 5 min
4. Time expires → Friendly lock screen appears → "Need more time? Ask a parent"
5. Enter PIN → Grant +15 min → Playback resumes
6. Watch an educational title → Remaining time does NOT decrease → "Educational" badge visible
7. Switch back to parent → View history → See counted vs educational breakdown
8. View weekly report → See daily totals and averages

## Key Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/parental-controls/pin` | POST | Create/update PIN |
| `/api/v1/parental-controls/pin/verify` | POST | Verify PIN |
| `/api/v1/parental-controls/pin/reset` | POST | Reset PIN via password |
| `/api/v1/parental-controls/profiles/{id}/viewing-time` | GET/PUT | Get/set viewing time config |
| `/api/v1/parental-controls/profiles/{id}/viewing-time/grant` | POST | Grant extra time |
| `/api/v1/parental-controls/profiles/{id}/history` | GET | Viewing history |
| `/api/v1/parental-controls/weekly-report` | GET | Weekly summary report |
| `/api/v1/viewing-time/balance/{id}` | GET | Current balance |
| `/api/v1/viewing-time/heartbeat` | POST | Session heartbeat |
| `/api/v1/viewing-time/session/{id}/end` | POST | End session |
| `/api/v1/viewing-time/playback-eligible/{id}` | GET | Pre-flight playback check |
