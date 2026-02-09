# Data Model: Parental Rating Enforcement

## No Schema Changes Required

This feature uses existing database columns only. No migration needed.

## Existing Entities Used

### Profile (table: `profiles`)

| Field | Type | Description |
|-------|------|-------------|
| id | UUID (PK) | Profile identifier |
| user_id | UUID (FK → users) | Owning user |
| name | VARCHAR(100) | Profile display name |
| parental_rating | VARCHAR(10) | Max content rating for this profile. One of: TV-Y, TV-G, TV-PG, TV-14, TV-MA. Default: TV-MA |
| is_kids | BOOLEAN | Whether this is a kids profile |

### Title (table: `titles`)

| Field | Type | Description |
|-------|------|-------------|
| id | UUID (PK) | Title identifier |
| age_rating | VARCHAR(10), NULLABLE | Content age rating. One of: TV-Y, TV-G, TV-PG, TV-14, TV-MA, or NULL |

## Rating Hierarchy (application-level constant)

```
Index:  0       1       2       3       4
Rating: TV-Y    TV-G    TV-PG   TV-14   TV-MA
```

A profile with `parental_rating = X` can see titles where `age_rating` index <= X's index.

Example: Profile with TV-PG (index 2) can see: TV-Y (0), TV-G (1), TV-PG (2).

## Filtering Logic

```
allowed_ratings(profile_parental_rating) → list[str] | None
  - If TV-MA → return None (no filtering)
  - If TV-14 → return ["TV-Y", "TV-G", "TV-PG", "TV-14"]
  - If TV-PG → return ["TV-Y", "TV-G", "TV-PG"]
  - If TV-G  → return ["TV-Y", "TV-G"]
  - If TV-Y  → return ["TV-Y"]
```

When `allowed_ratings` returns None, no WHERE clause is added (zero overhead for adult profiles).

When a list is returned, SQL applies: `WHERE title.age_rating IN (:allowed_ratings)`.

NULL `age_rating` values are naturally excluded by SQL `IN` semantics (NULL is not equal to any value).
