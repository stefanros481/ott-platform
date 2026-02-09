"""Seed data for channels and EPG schedule entries (7-day window)."""

import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.epg import Channel, ScheduleEntry

# ---------------------------------------------------------------------------
# HLS test streams (rotated across channels)
# ---------------------------------------------------------------------------
HLS_STREAMS = [
    "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",
    "https://devstreaming-cdn.apple.com/videos/streaming/examples/img_bipbop_adv_example_ts/master.m3u8",
    "https://demo.unified-streaming.com/k8s/features/stable/video/tears-of-steel/tears-of-steel.ism/.m3u8",
    "https://cdn.bitmovin.com/content/assets/sintel/hls/playlist.m3u8",
    "https://cph-p2p-msl.akamaized.net/hls/live/2000341/test/master.m3u8",
]

# ---------------------------------------------------------------------------
# Channel definitions
# ---------------------------------------------------------------------------
CHANNELS: list[dict[str, Any]] = [
    # Entertainment (1-5)
    {"name": "OTT One", "channel_number": 1, "genre": "entertainment", "is_hd": True},
    {"name": "OTT Two", "channel_number": 2, "genre": "entertainment", "is_hd": True},
    {"name": "OTT Drama", "channel_number": 3, "genre": "entertainment", "is_hd": True},
    {"name": "OTT Comedy", "channel_number": 4, "genre": "entertainment", "is_hd": True},
    {"name": "OTT Gold", "channel_number": 5, "genre": "entertainment", "is_hd": True},
    # News (6-8)
    {"name": "OTT News", "channel_number": 6, "genre": "news", "is_hd": True},
    {"name": "OTT News 24", "channel_number": 7, "genre": "news", "is_hd": True},
    {"name": "World News Network", "channel_number": 8, "genre": "news", "is_hd": True},
    # Sports (9-12)
    {"name": "OTT Sports", "channel_number": 9, "genre": "sports", "is_hd": True},
    {"name": "OTT Sports 2", "channel_number": 10, "genre": "sports", "is_hd": True},
    {"name": "Sports Extra", "channel_number": 11, "genre": "sports", "is_hd": True},
    {"name": "Sports Arena", "channel_number": 12, "genre": "sports", "is_hd": True},
    # Movies (13-15)
    {"name": "OTT Cinema", "channel_number": 13, "genre": "movies", "is_hd": True},
    {"name": "Movie Classics", "channel_number": 14, "genre": "movies", "is_hd": True},
    {"name": "Indie Films", "channel_number": 15, "genre": "movies", "is_hd": True},
    # Kids (16-18)
    {"name": "KidsZone", "channel_number": 16, "genre": "kids", "is_hd": True},
    {"name": "Cartoon World", "channel_number": 17, "genre": "kids", "is_hd": True},
    {"name": "Family Fun", "channel_number": 18, "genre": "kids", "is_hd": True},
    # Documentary (19-21)
    {"name": "Discovery OTT", "channel_number": 19, "genre": "documentary", "is_hd": True},
    {"name": "Nature Channel", "channel_number": 20, "genre": "documentary", "is_hd": True},
    {"name": "History Today", "channel_number": 21, "genre": "documentary", "is_hd": True},
    # Music (22-23)
    {"name": "Music Hits", "channel_number": 22, "genre": "music", "is_hd": False},
    {"name": "Music Live", "channel_number": 23, "genre": "music", "is_hd": False},
    # Lifestyle (24-25)
    {"name": "Food & Travel", "channel_number": 24, "genre": "lifestyle", "is_hd": False},
    {"name": "Home & Garden", "channel_number": 25, "genre": "lifestyle", "is_hd": False},
]

# ---------------------------------------------------------------------------
# Program templates per genre
# Each template: (title_pattern, duration_minutes, age_rating, is_series, series_title)
# title_pattern may contain {day} or {n} placeholders
# ---------------------------------------------------------------------------

_ENTERTAINMENT_PROGRAMS: list[dict[str, Any]] = [
    # Morning block
    {"title": "Morning Brew with Sarah", "duration": 60, "age_rating": "TV-G", "series_title": "Morning Brew", "genre": "talk-show"},
    {"title": "The Daily Chat", "duration": 30, "age_rating": "TV-PG", "series_title": "The Daily Chat", "genre": "talk-show"},
    # Daytime
    {"title": "Love Island Express", "duration": 60, "age_rating": "TV-14", "series_title": "Love Island Express", "genre": "reality"},
    {"title": "Home Swap", "duration": 30, "age_rating": "TV-G", "series_title": "Home Swap", "genre": "reality"},
    {"title": "The Talent Stage", "duration": 60, "age_rating": "TV-PG", "series_title": "The Talent Stage", "genre": "game-show"},
    {"title": "Afternoon Drama: The Lawsons", "duration": 30, "age_rating": "TV-14", "series_title": "The Lawsons", "genre": "drama"},
    # Primetime
    {"title": "Glass Houses", "duration": 60, "age_rating": "TV-MA", "series_title": "Glass Houses", "genre": "drama"},
    {"title": "Crown of Thorns", "duration": 60, "age_rating": "TV-14", "series_title": "Crown of Thorns", "genre": "drama"},
    {"title": "The Quick Quiz", "duration": 30, "age_rating": "TV-G", "series_title": "The Quick Quiz", "genre": "game-show"},
    {"title": "Shadow Protocol", "duration": 60, "age_rating": "TV-MA", "series_title": "Shadow Protocol", "genre": "drama"},
    # Late night
    {"title": "Late Night with Marcus", "duration": 60, "age_rating": "TV-14", "series_title": "Late Night with Marcus", "genre": "talk-show"},
    {"title": "Comedy Vault", "duration": 30, "age_rating": "TV-14", "series_title": "Comedy Vault", "genre": "comedy"},
    {"title": "After Hours", "duration": 30, "age_rating": "TV-MA", "series_title": "After Hours", "genre": "talk-show"},
    {"title": "Rerun Theatre", "duration": 60, "age_rating": "TV-PG", "series_title": None, "genre": "drama"},
    {"title": "The Entertainers", "duration": 30, "age_rating": "TV-PG", "series_title": "The Entertainers", "genre": "variety"},
    {"title": "Weekend Special", "duration": 90, "age_rating": "TV-14", "series_title": None, "genre": "special"},
    {"title": "Nightcap", "duration": 30, "age_rating": "TV-14", "series_title": "Nightcap", "genre": "talk-show"},
]

_NEWS_PROGRAMS: list[dict[str, Any]] = [
    {"title": "Morning Headlines", "duration": 60, "age_rating": "TV-G", "series_title": "Morning Headlines", "genre": "news"},
    {"title": "World This Morning", "duration": 30, "age_rating": "TV-G", "series_title": "World This Morning", "genre": "news"},
    {"title": "Market Watch", "duration": 30, "age_rating": "TV-G", "series_title": "Market Watch", "genre": "finance"},
    {"title": "Midday Report", "duration": 30, "age_rating": "TV-G", "series_title": "Midday Report", "genre": "news"},
    {"title": "Afternoon Briefing", "duration": 30, "age_rating": "TV-G", "series_title": "Afternoon Briefing", "genre": "news"},
    {"title": "Tech Insider", "duration": 30, "age_rating": "TV-PG", "series_title": "Tech Insider", "genre": "technology"},
    {"title": "Evening News at Six", "duration": 60, "age_rating": "TV-G", "series_title": "Evening News", "genre": "news"},
    {"title": "The Debate", "duration": 60, "age_rating": "TV-14", "series_title": "The Debate", "genre": "politics"},
    {"title": "Investigative Report", "duration": 60, "age_rating": "TV-14", "series_title": "Investigative Report", "genre": "news"},
    {"title": "Late News", "duration": 30, "age_rating": "TV-G", "series_title": "Late News", "genre": "news"},
    {"title": "Weather Outlook", "duration": 30, "age_rating": "TV-G", "series_title": "Weather Outlook", "genre": "weather"},
    {"title": "Global Perspective", "duration": 60, "age_rating": "TV-PG", "series_title": "Global Perspective", "genre": "news"},
    {"title": "Health Matters", "duration": 30, "age_rating": "TV-G", "series_title": "Health Matters", "genre": "health"},
    {"title": "Overnight News Desk", "duration": 60, "age_rating": "TV-G", "series_title": None, "genre": "news"},
    {"title": "Special Report", "duration": 30, "age_rating": "TV-PG", "series_title": None, "genre": "news"},
]

_SPORTS_PROGRAMS: list[dict[str, Any]] = [
    {"title": "Sports Breakfast", "duration": 60, "age_rating": "TV-G", "series_title": "Sports Breakfast", "genre": "sports-talk"},
    {"title": "Champions League Highlights", "duration": 90, "age_rating": "TV-G", "series_title": None, "genre": "football"},
    {"title": "Premier League Live", "duration": 120, "age_rating": "TV-G", "series_title": None, "genre": "football"},
    {"title": "Sports Center", "duration": 60, "age_rating": "TV-G", "series_title": "Sports Center", "genre": "sports-news"},
    {"title": "Tennis Grand Slam Highlights", "duration": 60, "age_rating": "TV-G", "series_title": None, "genre": "tennis"},
    {"title": "The Boxing Ring", "duration": 120, "age_rating": "TV-14", "series_title": None, "genre": "boxing"},
    {"title": "Pre-Game Show", "duration": 30, "age_rating": "TV-G", "series_title": "Pre-Game Show", "genre": "sports-talk"},
    {"title": "Match Day Analysis", "duration": 60, "age_rating": "TV-G", "series_title": "Match Day Analysis", "genre": "sports-talk"},
    {"title": "Sports Classics: Memorable Finals", "duration": 90, "age_rating": "TV-G", "series_title": "Sports Classics", "genre": "sports-archive"},
    {"title": "Extreme Sports Magazine", "duration": 30, "age_rating": "TV-PG", "series_title": "Extreme Sports", "genre": "sports"},
    {"title": "NBA Courtside", "duration": 120, "age_rating": "TV-G", "series_title": None, "genre": "basketball"},
    {"title": "Formula Racing Review", "duration": 60, "age_rating": "TV-G", "series_title": "Racing Review", "genre": "motorsport"},
    {"title": "Olympic Moments", "duration": 60, "age_rating": "TV-G", "series_title": "Olympic Moments", "genre": "sports-archive"},
    {"title": "Late Sports Round-Up", "duration": 30, "age_rating": "TV-G", "series_title": "Late Sports", "genre": "sports-news"},
    {"title": "Cricket World", "duration": 60, "age_rating": "TV-G", "series_title": "Cricket World", "genre": "cricket"},
]

_MOVIE_PROGRAMS: list[dict[str, Any]] = [
    {"title": "Morning Matinee", "duration": 120, "age_rating": "TV-PG", "series_title": None, "genre": "movie"},
    {"title": "Classic Cinema: Golden Age", "duration": 120, "age_rating": "TV-PG", "series_title": None, "genre": "movie"},
    {"title": "Thriller Thursday", "duration": 120, "age_rating": "TV-14", "series_title": None, "genre": "movie"},
    {"title": "Action Blockbuster", "duration": 120, "age_rating": "TV-14", "series_title": None, "genre": "movie"},
    {"title": "Indie Spotlight", "duration": 90, "age_rating": "TV-14", "series_title": None, "genre": "movie"},
    {"title": "Romance at Eight", "duration": 120, "age_rating": "TV-PG", "series_title": None, "genre": "movie"},
    {"title": "Sci-Fi Saturdays", "duration": 120, "age_rating": "TV-14", "series_title": None, "genre": "movie"},
    {"title": "Late Night Horror", "duration": 120, "age_rating": "TV-MA", "series_title": None, "genre": "movie"},
    {"title": "Award Winners Collection", "duration": 120, "age_rating": "TV-14", "series_title": None, "genre": "movie"},
    {"title": "Behind the Scenes", "duration": 30, "age_rating": "TV-G", "series_title": "Behind the Scenes", "genre": "making-of"},
    {"title": "Director's Cut Special", "duration": 150, "age_rating": "TV-MA", "series_title": None, "genre": "movie"},
    {"title": "Comedy Feature", "duration": 90, "age_rating": "TV-PG", "series_title": None, "genre": "movie"},
    {"title": "World Cinema", "duration": 120, "age_rating": "TV-14", "series_title": None, "genre": "movie"},
    {"title": "Double Feature Night", "duration": 120, "age_rating": "TV-14", "series_title": None, "genre": "movie"},
]

_KIDS_PROGRAMS: list[dict[str, Any]] = [
    {"title": "Pepper and Pine", "duration": 30, "age_rating": "TV-Y", "series_title": "Pepper and Pine", "genre": "cartoon"},
    {"title": "Dino Explorers", "duration": 30, "age_rating": "TV-Y", "series_title": "Dino Explorers", "genre": "cartoon"},
    {"title": "Space Cadets Academy", "duration": 30, "age_rating": "TV-Y", "series_title": "Space Cadets Academy", "genre": "cartoon"},
    {"title": "The Magic Garden", "duration": 30, "age_rating": "TV-Y", "series_title": "The Magic Garden", "genre": "educational"},
    {"title": "Robot Friends", "duration": 30, "age_rating": "TV-Y", "series_title": "Robot Friends", "genre": "cartoon"},
    {"title": "Puzzle Island", "duration": 30, "age_rating": "TV-Y", "series_title": "Puzzle Island", "genre": "educational"},
    {"title": "Adventure Time Tales", "duration": 30, "age_rating": "TV-Y", "series_title": "Adventure Time Tales", "genre": "cartoon"},
    {"title": "Nature Pals", "duration": 30, "age_rating": "TV-Y", "series_title": "Nature Pals", "genre": "educational"},
    {"title": "Saturday Morning Movie", "duration": 90, "age_rating": "TV-G", "series_title": None, "genre": "kids-movie"},
    {"title": "Fairy Tale Theatre", "duration": 30, "age_rating": "TV-Y", "series_title": "Fairy Tale Theatre", "genre": "cartoon"},
    {"title": "Art Attack Junior", "duration": 30, "age_rating": "TV-Y", "series_title": "Art Attack Junior", "genre": "educational"},
    {"title": "Superhero Squad", "duration": 30, "age_rating": "TV-Y", "series_title": "Superhero Squad", "genre": "cartoon"},
    {"title": "Bedtime Stories", "duration": 30, "age_rating": "TV-Y", "series_title": "Bedtime Stories", "genre": "educational"},
    {"title": "Zoo Adventures", "duration": 30, "age_rating": "TV-Y", "series_title": "Zoo Adventures", "genre": "educational"},
]

_DOCUMENTARY_PROGRAMS: list[dict[str, Any]] = [
    {"title": "Planet Earth: Deep Ocean", "duration": 60, "age_rating": "TV-G", "series_title": "Planet Earth", "genre": "nature"},
    {"title": "The Cosmos Revealed", "duration": 60, "age_rating": "TV-G", "series_title": "The Cosmos Revealed", "genre": "science"},
    {"title": "Ancient Civilizations", "duration": 60, "age_rating": "TV-PG", "series_title": "Ancient Civilizations", "genre": "history"},
    {"title": "Wild Africa", "duration": 60, "age_rating": "TV-G", "series_title": "Wild Africa", "genre": "nature"},
    {"title": "Engineering Marvels", "duration": 60, "age_rating": "TV-G", "series_title": "Engineering Marvels", "genre": "science"},
    {"title": "Vanishing Borders", "duration": 60, "age_rating": "TV-PG", "series_title": "Vanishing Borders", "genre": "politics"},
    {"title": "The Human Body", "duration": 60, "age_rating": "TV-PG", "series_title": "The Human Body", "genre": "science"},
    {"title": "World War Stories", "duration": 60, "age_rating": "TV-14", "series_title": "World War Stories", "genre": "history"},
    {"title": "Rainforest Diaries", "duration": 60, "age_rating": "TV-G", "series_title": "Rainforest Diaries", "genre": "nature"},
    {"title": "Volcano Hunters", "duration": 60, "age_rating": "TV-PG", "series_title": "Volcano Hunters", "genre": "science"},
    {"title": "Secrets of the Pyramids", "duration": 60, "age_rating": "TV-PG", "series_title": None, "genre": "history"},
    {"title": "Ocean Rescue", "duration": 60, "age_rating": "TV-G", "series_title": "Ocean Rescue", "genre": "nature"},
    {"title": "The Innovation Age", "duration": 60, "age_rating": "TV-G", "series_title": "The Innovation Age", "genre": "technology"},
    {"title": "Frozen Planet", "duration": 60, "age_rating": "TV-G", "series_title": "Frozen Planet", "genre": "nature"},
]

_MUSIC_PROGRAMS: list[dict[str, Any]] = [
    {"title": "Top Hits Countdown", "duration": 60, "age_rating": "TV-G", "series_title": "Top Hits Countdown", "genre": "chart-show"},
    {"title": "Live at the Apollo", "duration": 120, "age_rating": "TV-PG", "series_title": None, "genre": "concert"},
    {"title": "Acoustic Sessions", "duration": 60, "age_rating": "TV-G", "series_title": "Acoustic Sessions", "genre": "live-music"},
    {"title": "Music Quiz Night", "duration": 30, "age_rating": "TV-G", "series_title": "Music Quiz Night", "genre": "game-show"},
    {"title": "Artist Profile: In Depth", "duration": 60, "age_rating": "TV-PG", "series_title": "Artist Profile", "genre": "documentary"},
    {"title": "Vinyl Hour", "duration": 60, "age_rating": "TV-G", "series_title": "Vinyl Hour", "genre": "music-show"},
    {"title": "Festival Highlights", "duration": 90, "age_rating": "TV-PG", "series_title": None, "genre": "concert"},
    {"title": "Classical Evenings", "duration": 60, "age_rating": "TV-G", "series_title": "Classical Evenings", "genre": "classical"},
    {"title": "Beats & Bars", "duration": 30, "age_rating": "TV-14", "series_title": "Beats & Bars", "genre": "hip-hop"},
    {"title": "Rock Legends", "duration": 60, "age_rating": "TV-PG", "series_title": "Rock Legends", "genre": "documentary"},
    {"title": "Jazz After Dark", "duration": 60, "age_rating": "TV-G", "series_title": "Jazz After Dark", "genre": "jazz"},
    {"title": "New Music Friday", "duration": 30, "age_rating": "TV-G", "series_title": "New Music Friday", "genre": "chart-show"},
    {"title": "Music Video Marathon", "duration": 60, "age_rating": "TV-PG", "series_title": None, "genre": "music-video"},
]

_LIFESTYLE_PROGRAMS: list[dict[str, Any]] = [
    {"title": "Morning Kitchen with Chef Rosa", "duration": 30, "age_rating": "TV-G", "series_title": "Morning Kitchen", "genre": "cooking"},
    {"title": "Street Food Adventures", "duration": 60, "age_rating": "TV-G", "series_title": "Street Food Adventures", "genre": "food-travel"},
    {"title": "Home Makeover Challenge", "duration": 60, "age_rating": "TV-G", "series_title": "Home Makeover Challenge", "genre": "home"},
    {"title": "Garden Rescue", "duration": 30, "age_rating": "TV-G", "series_title": "Garden Rescue", "genre": "garden"},
    {"title": "Passport: Hidden Gems", "duration": 60, "age_rating": "TV-G", "series_title": "Passport", "genre": "travel"},
    {"title": "Baking Championship", "duration": 60, "age_rating": "TV-G", "series_title": "Baking Championship", "genre": "cooking"},
    {"title": "Property Dreams", "duration": 30, "age_rating": "TV-G", "series_title": "Property Dreams", "genre": "property"},
    {"title": "Wine Country", "duration": 30, "age_rating": "TV-PG", "series_title": "Wine Country", "genre": "food-travel"},
    {"title": "DIY Disasters", "duration": 30, "age_rating": "TV-G", "series_title": "DIY Disasters", "genre": "home"},
    {"title": "Coastal Living", "duration": 60, "age_rating": "TV-G", "series_title": "Coastal Living", "genre": "lifestyle"},
    {"title": "Yoga & Wellness", "duration": 30, "age_rating": "TV-G", "series_title": "Yoga & Wellness", "genre": "health"},
    {"title": "The Artisan", "duration": 30, "age_rating": "TV-G", "series_title": "The Artisan", "genre": "craft"},
    {"title": "Taste of Italy", "duration": 60, "age_rating": "TV-G", "series_title": "Taste of Italy", "genre": "cooking"},
    {"title": "Antique Treasures", "duration": 30, "age_rating": "TV-G", "series_title": "Antique Treasures", "genre": "antiques"},
]

# Map channel genre to program pools
_GENRE_PROGRAMS: dict[str, list[dict[str, Any]]] = {
    "entertainment": _ENTERTAINMENT_PROGRAMS,
    "news": _NEWS_PROGRAMS,
    "sports": _SPORTS_PROGRAMS,
    "movies": _MOVIE_PROGRAMS,
    "kids": _KIDS_PROGRAMS,
    "documentary": _DOCUMENTARY_PROGRAMS,
    "music": _MUSIC_PROGRAMS,
    "lifestyle": _LIFESTYLE_PROGRAMS,
}


def _build_day_schedule(
    channel_id: uuid.UUID,
    channel_genre: str,
    day: datetime,
    rng: random.Random,
) -> list[ScheduleEntry]:
    """Build a full day of schedule entries for a channel.

    Fills 06:00 to 06:00 next day (24 hours), producing 14-18 programs.
    """
    programs_pool = _GENRE_PROGRAMS.get(channel_genre, _ENTERTAINMENT_PROGRAMS)
    entries: list[ScheduleEntry] = []

    # Start at 06:00 on the given day
    current_time = day.replace(hour=6, minute=0, second=0, microsecond=0)
    end_of_day = current_time + timedelta(hours=24)

    # Shuffle a copy of the pool so each day feels different
    available = list(programs_pool)
    rng.shuffle(available)
    prog_idx = 0

    while current_time < end_of_day:
        prog = available[prog_idx % len(available)]
        prog_idx += 1

        duration = timedelta(minutes=prog["duration"])
        end_time = current_time + duration

        # Clamp end time to end of day
        if end_time > end_of_day:
            end_time = end_of_day

        # Determine if this is a series entry (~30% of programs)
        is_series = prog["series_title"] is not None
        season_num = None
        episode_num = None
        if is_series:
            season_num = rng.randint(1, 5)
            episode_num = rng.randint(1, 24)

        # ~20% are new
        is_new = rng.random() < 0.20

        entries.append(ScheduleEntry(
            channel_id=channel_id,
            title=prog["title"],
            synopsis=_generate_program_synopsis(prog["title"], prog["genre"]),
            genre=prog["genre"],
            start_time=current_time,
            end_time=end_time,
            age_rating=prog["age_rating"],
            is_new=is_new,
            is_repeat=not is_new and rng.random() < 0.30,
            series_title=prog["series_title"],
            season_number=season_num,
            episode_number=episode_num,
        ))

        current_time = end_time

    return entries


def _generate_program_synopsis(title: str, genre: str) -> str:
    """Generate a short synopsis based on the program title and genre."""
    _synopses: dict[str, list[str]] = {
        "news": [
            "Comprehensive coverage of the day's top stories from around the world.",
            "Breaking news and in-depth analysis of the stories that matter most.",
            "Your trusted source for up-to-the-minute news and current affairs.",
        ],
        "sports-talk": [
            "Expert pundits break down the latest results, transfers, and controversies.",
            "All the sports news, views, and previews you need to start your day.",
        ],
        "football": [
            "All the action from the latest round of fixtures, with highlights and analysis.",
            "Live coverage of today's match with pre-game analysis and post-match reaction.",
        ],
        "basketball": [
            "Court-side coverage of today's NBA action with expert commentary.",
        ],
        "motorsport": [
            "From the pit lane to the podium, a full review of the weekend's racing action.",
        ],
        "sports-news": [
            "A round-up of the biggest stories in sport from the past 24 hours.",
        ],
        "sports-archive": [
            "Relive the greatest moments in sporting history with classic match footage.",
        ],
        "drama": [
            "Compelling drama exploring complex characters and gripping storylines.",
            "A tightly woven narrative that keeps viewers guessing until the final scene.",
        ],
        "talk-show": [
            "Celebrity guests, lively discussion, and the stories everyone is talking about.",
            "Engaging conversation with the biggest names in entertainment and culture.",
        ],
        "reality": [
            "Unscripted drama, unexpected twists, and the moments that keep audiences hooked.",
        ],
        "game-show": [
            "Contestants compete for prizes in a fast-paced battle of wit and knowledge.",
        ],
        "comedy": [
            "Stand-up specials and sketch comedy guaranteed to make you laugh.",
        ],
        "movie": [
            "A cinematic journey that captivates from opening credits to closing scene.",
            "Feature-length entertainment showcasing brilliant performances and storytelling.",
        ],
        "making-of": [
            "Go behind the camera to see how your favourite films are made.",
        ],
        "cartoon": [
            "Fun, colourful adventures for young viewers with positive messages.",
        ],
        "educational": [
            "Learning through play, with engaging activities for curious young minds.",
        ],
        "kids-movie": [
            "A family-friendly film adventure perfect for a weekend morning.",
        ],
        "nature": [
            "Stunning cinematography reveals the wonders of the natural world.",
            "An immersive journey into wildlife habitats rarely seen by human eyes.",
        ],
        "science": [
            "Exploring the frontiers of scientific discovery with expert storytelling.",
        ],
        "history": [
            "Bringing the past to life through dramatic reconstruction and archival footage.",
        ],
        "technology": [
            "How cutting-edge innovation is shaping the future of everyday life.",
        ],
        "politics": [
            "Rigorous analysis of the political landscape and its impact on society.",
        ],
        "chart-show": [
            "Counting down the biggest hits of the week with exclusive performances.",
        ],
        "concert": [
            "A live music event capturing the energy and atmosphere of a legendary performance.",
        ],
        "live-music": [
            "Intimate acoustic performances from today's most exciting artists.",
        ],
        "classical": [
            "An evening of orchestral masterpieces performed by world-class musicians.",
        ],
        "jazz": [
            "Smooth jazz sessions to accompany your late-night wind-down.",
        ],
        "cooking": [
            "Delicious recipes, cooking tips, and culinary inspiration for every skill level.",
        ],
        "food-travel": [
            "A globe-trotting journey through the world's most exciting food scenes.",
        ],
        "travel": [
            "Discover hidden destinations and travel secrets from seasoned explorers.",
        ],
        "home": [
            "Transforming living spaces with creative ideas and expert craftsmanship.",
        ],
        "garden": [
            "Tips, tricks, and transformations to make the most of your outdoor space.",
        ],
        "property": [
            "House hunters search for their dream home with expert guidance.",
        ],
        "craft": [
            "Skilled artisans demonstrate traditional and contemporary craft techniques.",
        ],
        "antiques": [
            "Fascinating finds and surprising valuations in the world of antiques.",
        ],
        "lifestyle": [
            "Inspiration for better living covering wellness, style, and home.",
        ],
        "health": [
            "Expert advice on fitness, nutrition, and mental well-being.",
        ],
    }

    options = _synopses.get(genre, [f"Enjoy {title} on this channel."])
    return random.Random(hash(title + genre)).choice(options)


# ---------------------------------------------------------------------------
# Main seed function
# ---------------------------------------------------------------------------


async def seed_epg(session: AsyncSession) -> dict[str, int]:
    """Seed channels and a 7-day EPG schedule.

    Idempotent: skips if channels already exist.
    Returns counts of created entities.
    """
    result = await session.execute(select(Channel).limit(1))
    if result.scalar_one_or_none() is not None:
        print("  [seed_epg] EPG already seeded, skipping.")
        return {"channels": 0, "schedule_entries": 0}

    rng = random.Random(12345)

    # ------------------------------------------------------------------
    # 1. Create channels
    # ------------------------------------------------------------------
    channel_ids: list[uuid.UUID] = []
    channel_genres: list[str] = []

    for ch in CHANNELS:
        ch_id = uuid.uuid4()
        channel_ids.append(ch_id)
        channel_genres.append(ch["genre"])

        session.add(Channel(
            id=ch_id,
            name=ch["name"],
            channel_number=ch["channel_number"],
            logo_url=f"https://picsum.photos/seed/ch{ch['channel_number']}/100/100",
            genre=ch["genre"],
            is_hd=ch["is_hd"],
            hls_live_url=HLS_STREAMS[ch["channel_number"] % len(HLS_STREAMS)],
        ))

    await session.flush()
    print(f"  [seed_epg] Created {len(CHANNELS)} channels.")

    # ------------------------------------------------------------------
    # 2. Generate 7-day schedule (today - 3 days to today + 3 days)
    # ------------------------------------------------------------------
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    start_day = today - timedelta(days=3)
    total_entries = 0

    for day_offset in range(7):
        day = start_day + timedelta(days=day_offset)
        for ch_idx in range(len(CHANNELS)):
            entries = _build_day_schedule(
                channel_id=channel_ids[ch_idx],
                channel_genre=channel_genres[ch_idx],
                day=day,
                rng=random.Random(rng.randint(0, 2**31)),
            )
            for entry in entries:
                session.add(entry)
            total_entries += len(entries)

        # Flush each day to avoid huge pending state
        await session.flush()

    print(f"  [seed_epg] Created {total_entries} schedule entries across 7 days.")

    await session.commit()

    return {
        "channels": len(CHANNELS),
        "schedule_entries": total_entries,
    }
