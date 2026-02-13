# Data Model: Backend Hardening

**Date**: 2026-02-13
**Branch**: `005-backend-hardening`

## Overview

This feature introduces **no new database tables or columns**. It modifies application-level behavior around existing entities. This document captures the existing entities relevant to the hardening changes and the new application-level constructs.

## Existing Entities (unchanged)

### User
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Primary key |
| email | string | Unique |
| password_hash | string | bcrypt |
| is_admin | boolean | Used by AdminUser dependency |
| subscription_tier | string | Not relevant to hardening |
| created_at | timestamp | |

### Profile
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Primary key |
| user_id | UUID FK → users.id | **Key relationship for IDOR fix** |
| name | string | Display name |
| avatar_url | string | |
| is_kids | boolean | |
| age_rating | string | Parental control level |

**Ownership relationship**: `Profile.user_id == User.id` — each profile belongs to exactly one user. This FK is the basis for the VerifiedProfileId dependency.

## New Application Constructs (no DB changes)

### VerifiedProfileId (dependency)
- Input: `profile_id: UUID` query parameter + authenticated `User`
- Behavior: Queries `Profile` where `id == profile_id AND user_id == user.id`
- Output: Validated `UUID` if found, `403 Forbidden` if not
- Applied to: 15 required-profile endpoints across viewing, epg, recommendations routers

### OptionalVerifiedProfileId (dependency)
- Input: `profile_id: UUID | None` query parameter + authenticated `User`
- Behavior: Returns `None` if not provided; validates ownership if provided
- Output: `UUID | None`
- Applied to: 7 optional-profile endpoints across catalog, epg, recommendations routers

### AdminUser (dependency)
- Input: Authenticated `User`
- Behavior: Checks `user.is_admin == True`
- Output: `User` if admin, `403 Forbidden` if not
- Applied to: All 15 admin endpoints

### Health Check Responses

**Liveness** (`/health/live`):
```json
{"status": "ok"}
```

**Readiness** (`/health/ready`) — healthy:
```json
{
  "status": "ok",
  "checks": {
    "database": "ok"
  }
}
```

**Readiness** (`/health/ready`) — unhealthy:
```json
{
  "status": "degraded",
  "checks": {
    "database": "unreachable"
  }
}
```

## Configuration Additions

### New Settings Fields
| Field | Type | Default | Env Var |
|-------|------|---------|---------|
| jwt_secret | SecretStr | *(none — required)* | JWT_SECRET |
| db_pool_size | int | 20 | DB_POOL_SIZE |
| db_max_overflow | int | 10 | DB_MAX_OVERFLOW |
| db_pool_recycle | int | 3600 | DB_POOL_RECYCLE |

### Modified Settings Fields
| Field | Before | After |
|-------|--------|-------|
| jwt_secret | `str = "poc-secret-key-change-in-production"` | `SecretStr` (no default) |
