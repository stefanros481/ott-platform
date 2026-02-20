# Quickstart: Semantic Search Validation

## Prerequisites

```bash
cd docker
docker compose up --build
```

Wait for all services to be healthy (~1-2 minutes).

## 1. Backend API Validation

### Hybrid search (default mode)
```bash
curl -s -H "Authorization: Bearer $(curl -s -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{"email":"demo@ott.test","password":"demo123"}' | jq -r .access_token)" \
  "http://localhost:8000/api/v1/catalog/search/semantic?q=dark+comedy+about+office+life" | jq '.total, .mode, .items[:3] | .[] | {title, match_reason, match_type, similarity_score}'
```

Expected: Results with `mode: "hybrid"`, each item has `match_reason` and `match_type`.

### Keyword-only mode
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/catalog/search/semantic?q=Audit&mode=keyword" | jq '.items[:3] | .[] | {title, match_reason, match_type}'
```

Expected: Only results containing "Audit" in title/synopsis/cast. `match_type` is always "keyword". "The Audit" shows "Title match · Description match".

### Semantic-only mode
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/catalog/search/semantic?q=feel-good+family+adventure&mode=semantic" | jq '.items[:3] | .[] | {title, match_reason, similarity_score}'
```

Expected: Results found even though "feel-good family adventure" doesn't appear literally in any metadata.

### Parental filtering
```bash
# Get a child profile ID first, then:
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/catalog/search/semantic?q=thriller&profile_id=$CHILD_PROFILE_ID" | jq '.items | length, .items[].age_rating'
```

Expected: No results with ratings above the child profile's limit.

### Existing search unchanged
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/catalog/search?q=Audit" | jq '.total'
```

Expected: Same results as before — old endpoint untouched. Returns 2 results (same as keyword mode above).

## 2. Frontend Validation

1. Open http://localhost:5173 and log in as `demo@ott.test` / `demo123`
2. Navigate to Search
3. Type "dark comedy about office life" — verify AI badge appears, results show match reasons
4. Toggle to Keyword mode — verify only exact matches, no AI badge
5. Type a known title name — verify "Title match" appears in explanation
6. Toggle back to Smart Search — verify semantic results return

## 3. Fallback Validation

1. Search works normally in hybrid mode
2. If embedding model fails to load (simulated), search still returns keyword results
3. Frontend shows no error — just keyword results without AI badge
