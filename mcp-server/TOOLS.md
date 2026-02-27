# OTT Content MCP Server — Tool Reference

Read-only MCP server exposing the OTT platform's content metadata database to AI agents.

**Transport:** stdio
**Server name:** `ott-content`

---

## Resources

| URI | Description |
|---|---|
| `content://schema` | Data model overview — tables, relationships, and key fields |
| `content://tools-guide` | Usage guide with example workflows for common tasks |

---

## Tools

### Catalog & Discovery

#### `list_genres`
List all content genres with their slugs (for use as filters in other tools).

**Parameters:** none

---

#### `search_titles`
Search the content catalog by keyword. Matches against title, synopsis, and cast names.

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `query` | string | yes | — | Search keyword |
| `title_type` | string | no | — | `"movie"` or `"series"` |
| `genre` | string | no | — | Genre slug (use `list_genres` for valid values) |
| `limit` | int | no | 20 | Max results (1–100) |

---

#### `list_titles`
Browse the content catalog with pagination.

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `page` | int | no | 1 | Page number |
| `page_size` | int | no | 20 | Items per page (1–100) |
| `title_type` | string | no | — | `"movie"` or `"series"` |
| `genre` | string | no | — | Genre slug |

---

#### `get_title`
Get full details for a title including cast, genres, seasons, and episodes.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `title_id` | string | yes | UUID of the title |

---

#### `get_featured_titles`
Get titles flagged as featured for the hero banner.

**Parameters:** none

---

#### `browse_titles`
Browse titles with advanced filters not available in `list_titles`.

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `age_rating` | string | no | — | e.g. `"TV-MA"`, `"TV-PG"`, `"TV-14"` |
| `language` | string | no | — | Language code, e.g. `"en"`, `"no"`, `"es"` |
| `country` | string | no | — | Country of origin, e.g. `"US"`, `"NO"`, `"GB"` |
| `is_educational` | bool | no | — | Filter to educational content |
| `mood_tag` | string | no | — | e.g. `"gritty"`, `"epic"`, `"heartwarming"` |
| `theme_tag` | string | no | — | e.g. `"justice"`, `"survival"`, `"family"` |
| `title_type` | string | no | — | `"movie"` or `"series"` |
| `page` | int | no | 1 | Page number |
| `page_size` | int | no | 20 | Items per page (1–100) |

---

#### `list_mood_tags`
List all distinct mood tags used across titles, with counts.

**Parameters:** none

---

#### `list_theme_tags`
List all distinct theme tags used across titles, with counts.

**Parameters:** none

---

### Cast & Crew

#### `search_cast`
Search for actors, directors, or writers by name.

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `query` | string | yes | — | Name or partial name |
| `role` | string | no | — | `"actor"`, `"director"`, or `"writer"` |
| `limit` | int | no | 20 | Max results (1–100) |

---

#### `get_person_titles`
Get all titles associated with a person (their filmography).

| Parameter | Type | Required | Description |
|---|---|---|---|
| `person_name` | string | yes | Exact name (use `search_cast` to find it first) |
| `role` | string | no | `"actor"`, `"director"`, or `"writer"` |

---

### EPG & Live TV

#### `list_channels`
List all TV channels with channel number, genre, HD status, and TSTV capabilities.

**Parameters:** none

---

#### `get_schedule`
Get the EPG schedule for a channel on a given date.

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `channel_id` | string | yes | — | UUID of the channel |
| `date` | string | no | `"today"` | `YYYY-MM-DD` or `"today"` |

---

#### `get_now_playing`
Get the currently airing program and next program for every channel.

**Parameters:** none

---

#### `get_catchup_available`
List programs available on catch-up TV right now (aired recently, still within the catchup window).

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `channel_id` | string | no | — | UUID to filter by channel |
| `limit` | int | no | 50 | Max results (1–200) |

---

#### `search_schedule`
Search the EPG schedule by program title or series title across all channels.

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `query` | string | yes | — | Search keyword |
| `date` | string | no | `"today"` | `YYYY-MM-DD` or `"today"` |
| `limit` | int | no | 20 | Max results (1–100) |

---

### Packages & Entitlements

#### `get_title_offers`
Get pricing and availability for a title (TVOD offers and SVOD package inclusion).

| Parameter | Type | Required | Description |
|---|---|---|---|
| `title_id` | string | yes | UUID of the title |

---

#### `get_packages`
List all content packages with full details (description, tier, pricing, stream limits).

**Parameters:** none

---

#### `get_package_contents`
List all titles and channels included in a content package.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `package_id` | string | yes | UUID of the content package |

---

### Analytics & Engagement

#### `get_title_popularity`
Get the most-watched titles by play count over a recent time period.

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `title_type` | string | no | — | `"movie"` or `"series"` |
| `days` | int | no | 30 | Look-back period in days |
| `limit` | int | no | 20 | Top titles to return (1–100) |

---

#### `get_service_type_stats`
Get play count breakdown by service type (Linear, VoD, SVoD, TSTV, Catch_up, Cloud_PVR).

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `days` | int | no | 30 | Look-back period in days |

---

#### `get_title_ratings`
Get audience rating summary for a title (thumbs up/down counts and approval rate).

| Parameter | Type | Required | Description |
|---|---|---|---|
| `title_id` | string | yes | UUID of the title |

---

#### `get_most_wishlisted`
Get titles with the most watchlist additions (demand signal).

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `limit` | int | no | 20 | Top titles to return (1–100) |

---

#### `get_catalog_stats`
Get summary statistics: total titles, genre distribution, age ratings, channels, and packages.

**Parameters:** none

---

### Operational Health

#### `get_embedding_status`
Check content embedding coverage — how many titles have vector embeddings vs missing.

**Parameters:** none

---

#### `get_tstv_stats`
Get TSTV usage statistics — Start Over vs Catch-up sessions, completion rates.

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `days` | int | no | 30 | Look-back period in days |

---

#### `get_recording_stats`
Get Cloud PVR recording statistics — counts by status (pending, recording, completed, failed).

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `days` | int | no | 30 | Look-back period in days |
