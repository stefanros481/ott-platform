# Data Model: Content Metadata MCP Server

**Branch**: `017-content-mcp` | **Date**: 2026-02-27

## Overview

The MCP server does **not** create any new database tables. It reads from existing tables defined in the backend ORM models. This document maps which existing entities each MCP tool queries and what fields are returned.

## Existing Entities Used (Read-Only)

### Catalog Domain

#### Title (`titles`)
- **Source**: `backend/app/models/catalog.py:Title`
- **Used by tools**: `search_titles`, `get_title`, `list_titles`, `get_featured_titles`, `get_catalog_stats`
- **Key fields returned**: id, title, title_type, synopsis_short, synopsis_long, ai_description, release_year, duration_minutes, age_rating, country_of_origin, language, poster_url, landscape_url, logo_url, mood_tags, theme_tags, is_featured, is_educational, created_at

#### Genre (`genres`)
- **Source**: `backend/app/models/catalog.py:Genre`
- **Used by tools**: `list_genres`, `search_titles` (filter), `list_titles` (filter), `get_title` (detail), `get_catalog_stats`
- **Key fields returned**: id, name, slug

#### TitleGenre (`title_genres`) — M:M junction
- **Source**: `backend/app/models/catalog.py:TitleGenre`
- **Used by tools**: all catalog tools (genre resolution)
- **Key fields**: title_id, genre_id, is_primary

#### TitleCast (`title_cast`)
- **Source**: `backend/app/models/catalog.py:TitleCast`
- **Used by tools**: `search_titles` (cast name matching), `get_title` (cast list)
- **Key fields returned**: person_name, role, character_name, sort_order

#### Season (`seasons`)
- **Source**: `backend/app/models/catalog.py:Season`
- **Used by tools**: `get_title` (for series)
- **Key fields returned**: season_number, name, synopsis

#### Episode (`episodes`)
- **Source**: `backend/app/models/catalog.py:Episode`
- **Used by tools**: `get_title` (for series)
- **Key fields returned**: episode_number, title, synopsis, duration_minutes

### EPG Domain

#### Channel (`channels`)
- **Source**: `backend/app/models/epg.py:Channel`
- **Used by tools**: `list_channels`, `get_schedule`, `get_now_playing`, `get_catalog_stats`
- **Key fields returned**: id, name, channel_number, logo_url, genre, is_hd, hls_live_url, tstv_enabled, startover_enabled, catchup_enabled, catchup_window_hours

#### ScheduleEntry (`schedule_entries`)
- **Source**: `backend/app/models/epg.py:ScheduleEntry`
- **Used by tools**: `get_schedule`, `get_now_playing`
- **Key fields returned**: id, channel_id, title, synopsis, genre, start_time, end_time, age_rating, is_new, is_repeat, series_title, season_number, episode_number, catchup_eligible, startover_eligible

### Entitlement Domain

#### ContentPackage (`content_packages`)
- **Source**: `backend/app/models/entitlement.py:ContentPackage`
- **Used by tools**: `get_catalog_stats`, `get_title_offers`
- **Key fields returned**: id, name, tier, max_streams, price_cents, currency

#### TitleOffer (`title_offers`)
- **Source**: `backend/app/models/entitlement.py:TitleOffer`
- **Used by tools**: `get_title_offers`
- **Key fields returned**: id, offer_type, price_cents, currency, rental_window_hours, is_active

#### PackageContent (`package_contents`)
- **Source**: `backend/app/models/entitlement.py:PackageContent`
- **Used by tools**: `get_title_offers` (to find which packages include a title)
- **Key fields**: package_id, content_type, content_id

## New Data Structures (In-Memory Only)

### AppContext (dataclass)
- `session_factory: async_sessionmaker` — used by tools to get database sessions
- Lifecycle: created in FastMCP lifespan, disposed on shutdown

### Tool Response Shapes

All tools return JSON-serialized dicts. No new database entities or Pydantic models are created — serialization is handled by a custom JSON encoder for UUID/datetime types.
