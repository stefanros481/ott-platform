# MCP Tool Contracts: Content Metadata MCP Server

**Branch**: `017-content-mcp` | **Date**: 2026-02-27

These are the MCP tool schemas exposed by the server. Each tool is read-only and returns JSON.

---

## Catalog Tools

### `search_titles`

Search the content catalog by keyword.

**Parameters**:
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `query` | string | yes | — | Search keyword (matches title, synopsis, cast names) |
| `title_type` | string | no | null | Filter: "movie" or "series" |
| `genre` | string | no | null | Filter: genre slug (e.g., "action", "drama") |
| `limit` | integer | no | 20 | Max results (1-100) |

**Returns**: JSON object
```json
{
  "titles": [
    {
      "id": "uuid",
      "title": "string",
      "title_type": "movie|series",
      "synopsis_short": "string",
      "release_year": 2024,
      "duration_minutes": 120,
      "age_rating": "TV-MA",
      "genres": ["Action", "Thriller"],
      "poster_url": "string",
      "is_featured": false
    }
  ],
  "total": 42
}
```

---

### `get_title`

Get full details for a title by UUID.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `title_id` | string | yes | Title UUID |

**Returns**: JSON object
```json
{
  "id": "uuid",
  "title": "string",
  "title_type": "movie|series",
  "synopsis_short": "string",
  "synopsis_long": "string",
  "ai_description": "string",
  "release_year": 2024,
  "duration_minutes": 120,
  "age_rating": "TV-MA",
  "country_of_origin": "US",
  "language": "en",
  "poster_url": "string",
  "landscape_url": "string",
  "logo_url": "string",
  "mood_tags": ["intense", "dark"],
  "theme_tags": ["revenge", "justice"],
  "is_featured": false,
  "is_educational": false,
  "genres": [{"name": "Action", "slug": "action", "is_primary": true}],
  "cast": [{"person_name": "string", "role": "actor", "character_name": "string"}],
  "seasons": [
    {
      "season_number": 1,
      "name": "Season 1",
      "synopsis": "string",
      "episodes": [
        {"episode_number": 1, "title": "string", "synopsis": "string", "duration_minutes": 45}
      ]
    }
  ]
}
```

---

### `list_titles`

Browse the catalog with pagination and optional filters.

**Parameters**:
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `page` | integer | no | 1 | Page number |
| `page_size` | integer | no | 20 | Items per page (1-100) |
| `title_type` | string | no | null | Filter: "movie" or "series" |
| `genre` | string | no | null | Filter: genre slug |

**Returns**: JSON object
```json
{
  "titles": [ "...same shape as search_titles..." ],
  "total": 85,
  "page": 1,
  "page_size": 20
}
```

---

### `list_genres`

List all content genres.

**Parameters**: None

**Returns**: JSON array
```json
[
  {"name": "Action", "slug": "action"},
  {"name": "Drama", "slug": "drama"}
]
```

---

### `get_featured_titles`

Get titles flagged as featured for the hero banner.

**Parameters**: None

**Returns**: JSON array (same shape as search_titles items)

---

### `get_title_offers`

Get pricing and availability for a specific title.

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `title_id` | string | yes | Title UUID |

**Returns**: JSON object
```json
{
  "title_id": "uuid",
  "offers": [
    {
      "offer_type": "rent|buy|free",
      "price_cents": 4900,
      "currency": "NOK",
      "rental_window_hours": 48
    }
  ],
  "included_in_packages": [
    {"name": "Premium", "tier": "premium"}
  ]
}
```

---

## EPG Tools

### `list_channels`

List all TV channels.

**Parameters**: None

**Returns**: JSON array
```json
[
  {
    "id": "uuid",
    "name": "NRK1",
    "channel_number": 1,
    "logo_url": "string",
    "genre": "General",
    "is_hd": true,
    "tstv_enabled": true,
    "startover_enabled": true,
    "catchup_enabled": true,
    "catchup_window_hours": 168
  }
]
```

---

### `get_schedule`

Get the EPG schedule for a channel on a date.

**Parameters**:
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `channel_id` | string | yes | — | Channel UUID |
| `date` | string | no | "today" | Date in YYYY-MM-DD format or "today" |

**Returns**: JSON array
```json
[
  {
    "id": "uuid",
    "title": "Evening News",
    "synopsis": "string",
    "genre": "News",
    "start_time": "2026-02-27T18:00:00+00:00",
    "end_time": "2026-02-27T18:30:00+00:00",
    "age_rating": "TV-G",
    "is_new": true,
    "is_repeat": false,
    "catchup_eligible": true,
    "startover_eligible": true
  }
]
```

---

### `get_now_playing`

Get currently airing programs across all channels.

**Parameters**: None

**Returns**: JSON array
```json
[
  {
    "channel": {"name": "NRK1", "channel_number": 1, "is_hd": true},
    "current_program": {"title": "string", "start_time": "...", "end_time": "..."},
    "next_program": {"title": "string", "start_time": "...", "end_time": "..."}
  }
]
```

---

## Statistics Tools

### `get_catalog_stats`

Get aggregate statistics about the content library.

**Parameters**: None

**Returns**: JSON object
```json
{
  "titles": {"total": 85, "movies": 60, "series": 25},
  "genres": [{"name": "Action", "slug": "action", "count": 15}],
  "age_ratings": {"TV-MA": 20, "TV-14": 30, "TV-G": 35},
  "channels": {"total": 25},
  "packages": [{"name": "Basic", "tier": "basic", "price_cents": 9900, "currency": "NOK"}]
}
```

---

## MCP Resources

### `content://schema`
Static resource providing database schema documentation for agent context.

### `content://tools-guide`
Static resource providing a usage guide for effective tool usage.
