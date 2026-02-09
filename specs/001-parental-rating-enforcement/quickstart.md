# Quickstart: Parental Rating Enforcement

## What This Feature Does

Enforces the profile's `parental_rating` so that Kids and Family profiles only see age-appropriate content. Previously, switching to a Kids profile (TV-Y) showed all content including TV-MA — now it only shows TV-Y content.

## Testing After Implementation

### 1. Start the platform

```bash
cd docker && docker compose up -d
```

### 2. Log in as admin (has a Kids profile)

- URL: http://localhost:5173
- Email: `admin@example.com` / Password: `admin123`

### 3. Test with Adult profile

1. Select the "Admin" profile (TV-MA)
2. Browse catalog — should see all 70 titles
3. Home page rails should be fully populated

### 4. Test with Kids profile

1. Switch to "Kids" profile (TV-Y)
2. Browse catalog — should see only TV-Y titles (4 in seed data)
3. Home page rails should only contain TV-Y content
4. Search for a TV-MA title by name — should return no results
5. Navigate directly to a TV-MA title URL — should see restriction message

### 5. Test with Family profile

1. Log in as `standard@example.com` / `standard123`
2. Select "Family" profile (TV-PG)
3. Browse catalog — should see TV-Y + TV-G + TV-PG titles (28 in seed data)
4. TV-14 and TV-MA titles should not appear

## Seed Data Rating Distribution

| Rating | Count | Visible to TV-Y | Visible to TV-PG | Visible to TV-MA |
|--------|-------|-----------------|-------------------|-------------------|
| TV-Y   | 4     | Yes             | Yes               | Yes               |
| TV-G   | 7     | No              | Yes               | Yes               |
| TV-PG  | 17    | No              | Yes               | Yes               |
| TV-14  | 23    | No              | No                | Yes               |
| TV-MA  | 19    | No              | No                | Yes               |

## Files Changed

### Backend (3 existing + 1 new)
- `backend/app/services/rating_utils.py` — NEW: Rating hierarchy helper
- `backend/app/services/catalog_service.py` — Add age rating filter
- `backend/app/services/recommendation_service.py` — Add age rating filter to all rails + similar
- `backend/app/routers/catalog.py` — Add profile_id param, resolve rating, pass to service
- `backend/app/routers/recommendations.py` — Add profile_id to similar/post-play

### Frontend Client (4 existing)
- `frontend-client/src/api/catalog.ts` — Add profile_id to all API calls
- `frontend-client/src/api/recommendations.ts` — Add profile_id to similar titles
- `frontend-client/src/pages/BrowsePage.tsx` — Pass profile_id
- `frontend-client/src/pages/HomePage.tsx` — Pass profile_id to featured
- `frontend-client/src/pages/SearchPage.tsx` — Pass profile_id
- `frontend-client/src/pages/TitleDetailPage.tsx` — Pass profile_id, handle 403
