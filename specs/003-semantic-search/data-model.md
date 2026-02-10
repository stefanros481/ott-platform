# Data Model: Semantic Search

No database schema changes required. This feature operates on existing tables only.

## Existing Entities Used

### Title (read-only)
- `id` (UUID, PK)
- `title` (string) — searched via ILIKE
- `synopsis_short` (text, nullable) — searched via ILIKE
- `synopsis_long` (text, nullable) — searched via ILIKE
- `title_type` (string: "movie" | "series")
- `release_year` (int, nullable)
- `duration_minutes` (int, nullable)
- `age_rating` (string, nullable) — used for parental filtering
- `poster_url` (string, nullable)
- `landscape_url` (string, nullable)
- `is_featured` (bool)
- `mood_tags` (string[], nullable)
- Relationship: `genres` → TitleGenre → Genre (name)
- Relationship: `cast_members` → TitleCast (person_name) — searched via ILIKE

### ContentEmbedding (read-only)
- `title_id` (UUID, FK → titles.id, PK)
- `embedding` (vector(384)) — queried via `<=>` cosine distance
- `model_version` (string)
- Index: HNSW on `embedding` column with `vector_cosine_ops`

## New API-Only Entities (no persistence)

### SearchResultItem (response schema only)
Extends TitleListItem fields with search-specific metadata:
- All fields from TitleListItem (id, title, title_type, synopsis_short, release_year, duration_minutes, age_rating, poster_url, landscape_url, is_featured, mood_tags, genres)
- `match_reason` (string) — human-readable explanation, e.g. "Title match · Similar themes"
- `match_type` (string: "keyword" | "semantic" | "both")
- `similarity_score` (float, nullable) — cosine similarity 0.0–1.0, null for keyword-only matches

### SemanticSearchResponse (response schema only)
- `items` (list of SearchResultItem)
- `total` (int) — count of results
- `query` (string) — echo of the search query
- `mode` (string: "keyword" | "semantic" | "hybrid") — echo of the mode used

## No Migrations Required

All data access is read-only against existing `titles`, `title_cast`, `title_genres`, `genres`, and `content_embeddings` tables. No new tables, columns, or indexes are needed.
