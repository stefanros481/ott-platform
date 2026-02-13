# Quickstart: Verifying Backend Hardening

**Branch**: `005-backend-hardening`

## Prerequisites

- Docker Compose stack running: `docker compose -f docker/docker-compose.yml up`
- A `.env` file in `docker/` or environment variables set (see below)

## Required Environment Changes

After this feature, the backend requires a `JWT_SECRET` environment variable (no default):

```bash
# Generate a random 64-character secret
export JWT_SECRET=$(openssl rand -hex 32)
```

For Docker Compose, either:
- Set `JWT_SECRET` in your shell before running `docker compose up`, or
- Create a `docker/.env` file with `JWT_SECRET=<your-64-char-secret>`

## Verification Checklist

### 1. JWT Secret Enforcement

```bash
# Should FAIL to start (no secret)
unset JWT_SECRET
docker compose -f docker/docker-compose.yml up backend
# Expected: Exit with error "JWT_SECRET must be configured"

# Should FAIL to start (too short)
JWT_SECRET=tooshort docker compose -f docker/docker-compose.yml up backend
# Expected: Exit with error "JWT_SECRET must be at least 32 characters"

# Should START successfully
JWT_SECRET=$(openssl rand -hex 32) docker compose -f docker/docker-compose.yml up backend
# Expected: Normal startup
```

### 2. Profile Ownership (IDOR Fix)

```bash
# Login as user A
TOKEN_A=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"password123"}' | jq -r '.access_token')

# Get user A's profile ID
PROFILE_A=$(curl -s http://localhost:8000/api/v1/auth/profiles \
  -H "Authorization: Bearer $TOKEN_A" | jq -r '.[0].id')

# Login as user B
TOKEN_B=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"bob@example.com","password":"password123"}' | jq -r '.access_token')

# Try to access user A's profile data with user B's token
# Should return 403 Forbidden
curl -s -w "\nHTTP %{http_code}\n" \
  "http://localhost:8000/api/v1/viewing/continue-watching?profile_id=$PROFILE_A" \
  -H "Authorization: Bearer $TOKEN_B"
# Expected: {"detail":"Profile not found or access denied"} HTTP 403
```

### 3. Health Check Endpoints

```bash
# Liveness (always 200 if process is running)
curl -s http://localhost:8000/health/live
# Expected: {"status":"ok"}

# Readiness (200 if DB is up)
curl -s http://localhost:8000/health/ready
# Expected: {"status":"ok","checks":{"database":"ok"}}

# Stop the database, then check readiness
docker compose -f docker/docker-compose.yml stop postgres
curl -s -w "\nHTTP %{http_code}\n" http://localhost:8000/health/ready
# Expected: {"status":"degraded","checks":{"database":"unreachable"}} HTTP 503

# Liveness should still be 200
curl -s http://localhost:8000/health/live
# Expected: {"status":"ok"}

# Restart database
docker compose -f docker/docker-compose.yml start postgres
```

### 4. CORS Verification

```bash
# Allowed method (GET)
curl -s -X OPTIONS http://localhost:8000/api/v1/catalog/titles \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: GET" \
  -D - -o /dev/null | grep -i "access-control-allow-methods"
# Expected: access-control-allow-methods: GET, POST, PUT, DELETE, OPTIONS

# Disallowed method (PATCH)
curl -s -X OPTIONS http://localhost:8000/api/v1/catalog/titles \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: PATCH" \
  -D - -o /dev/null | grep -i "access-control-allow-methods"
# Expected: PATCH should NOT be in the allowed methods
```

### 5. SQL Injection Safety

```bash
# Search with SQL metacharacters (should return results safely, not error)
curl -s "http://localhost:8000/api/v1/catalog/search?q=%25%27%3B+DROP+TABLE+titles%3B+--" \
  -H "Authorization: Bearer $TOKEN_A"
# Expected: Normal search results (likely empty), not a database error

# Search with ILIKE wildcards (should be treated as literal text)
curl -s "http://localhost:8000/api/v1/catalog/search?q=%25" \
  -H "Authorization: Bearer $TOKEN_A"
# Expected: Only titles containing literal "%" character, NOT all titles
```

### 6. Admin Authorization

```bash
# Non-admin user should get 403
curl -s -w "\nHTTP %{http_code}\n" \
  http://localhost:8000/api/v1/admin/stats \
  -H "Authorization: Bearer $TOKEN_A"
# Expected: 403 if alice is not admin, 200 if alice is admin
```

### 7. Duplicate File Removed

```bash
# Should not exist
test -f backend/main.py && echo "FAIL: duplicate still exists" || echo "PASS: duplicate removed"
```
