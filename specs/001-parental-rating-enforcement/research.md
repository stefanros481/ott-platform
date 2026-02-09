# Research: Parental Rating Enforcement

## Rating Hierarchy Design

**Decision**: Use a static ordered list `["TV-Y", "TV-G", "TV-PG", "TV-14", "TV-MA"]` where the index defines severity. A profile's `parental_rating` maps to an index; titles with `age_rating` index <= profile index are allowed.

**Rationale**: The US TV Parental Guidelines are a fixed, well-defined set. A simple index lookup is O(1), avoids database changes, and is trivially understandable. No need for a database table or configurable hierarchy for a PoC.

**Alternatives considered**:
- Database table mapping ratings to numeric levels — overkill for 5 fixed values
- Enum in the ORM model — would require a migration; string comparison with a helper is simpler

## Filtering Strategy: Backend vs Frontend

**Decision**: Filter in the backend (SQL WHERE clause). The frontend passes `profile_id`; the backend resolves the profile's `parental_rating` and applies the filter.

**Rationale**: Backend filtering is the only safe approach — client-side filtering would expose restricted content in API responses. Backend filtering also correctly handles pagination counts and keeps the frontend simple.

**Alternatives considered**:
- Frontend-only filtering — insecure, breaks pagination, sends restricted data over the wire
- Middleware/decorator approach — too complex for a PoC; explicit parameter passing is clearer

## Profile Resolution: Where to Load parental_rating

**Decision**: Create a lightweight helper in the catalog/recommendation routers that fetches the profile's `parental_rating` from the `profiles` table given `profile_id`. Return the list of allowed ratings (or None for TV-MA to skip filtering).

**Rationale**: The profile is a small, frequently-accessed record. A single SELECT by primary key is negligible overhead. The helper returns `list[str] | None` — None means "no filter" (TV-MA), a list means "filter to these ratings only". This makes the downstream service code simple: `if allowed_ratings: query.where(Title.age_rating.in_(allowed_ratings))`.

**Alternatives considered**:
- Embedding parental_rating in the JWT token — would require token refresh on profile switch; currently profile_id is a query param
- Creating a FastAPI dependency — reasonable but over-abstracted for 2-3 call sites

## NULL age_rating Handling

**Decision**: Treat NULL `age_rating` as TV-MA (unrestricted). In SQL: `WHERE (t.age_rating IN (:allowed) OR t.age_rating IS NULL)` is NOT applied — NULL titles are excluded from restricted views by default since `IN (...)` does not match NULL.

**Rationale**: SQL `IN` naturally excludes NULL values. This means titles without an `age_rating` are automatically hidden from restricted profiles without extra logic. For TV-MA profiles (no filter applied), NULL titles remain visible. This matches the spec requirement exactly.

## Raw SQL Queries in recommendation_service.py

**Decision**: Add `AND t.age_rating IN (:allowed_ratings)` clauses to the existing raw SQL queries in recommendation_service. For TV-MA profiles, skip the clause entirely (don't add it to the SQL).

**Rationale**: The recommendation service uses raw SQL (via `text()`) for performance-critical pgvector queries. Adding a WHERE clause is straightforward. Conditionally building the SQL string (with/without the age filter) avoids any overhead for unrestricted profiles.

**Alternatives considered**:
- Refactoring to SQLAlchemy ORM — would be a larger change than needed for this feature
- Post-filtering in Python — wasteful (fetches extra rows just to discard them)
