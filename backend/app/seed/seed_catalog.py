"""Seed data for the content catalog: genres, titles, cast, seasons, episodes."""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import Episode, Genre, Season, Title, TitleCast, TitleGenre

# ---------------------------------------------------------------------------
# HLS test streams (public, reliable)
# ---------------------------------------------------------------------------
HLS_STREAMS = [
    "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8",
    "https://devstreaming-cdn.apple.com/videos/streaming/examples/img_bipbop_adv_example_ts/master.m3u8",
    "https://demo.unified-streaming.com/k8s/features/stable/video/tears-of-steel/tears-of-steel.ism/.m3u8",
    "https://cdn.bitmovin.com/content/assets/sintel/hls/playlist.m3u8",
    "https://cph-p2p-msl.akamaized.net/hls/live/2000341/test/master.m3u8",
]

# ---------------------------------------------------------------------------
# Genre definitions
# ---------------------------------------------------------------------------
GENRES: list[dict[str, str]] = [
    {"name": "Action", "slug": "action"},
    {"name": "Comedy", "slug": "comedy"},
    {"name": "Drama", "slug": "drama"},
    {"name": "Thriller", "slug": "thriller"},
    {"name": "Sci-Fi", "slug": "sci-fi"},
    {"name": "Horror", "slug": "horror"},
    {"name": "Romance", "slug": "romance"},
    {"name": "Documentary", "slug": "documentary"},
    {"name": "Animation", "slug": "animation"},
    {"name": "Crime", "slug": "crime"},
    {"name": "Fantasy", "slug": "fantasy"},
    {"name": "Family", "slug": "family"},
]

# ---------------------------------------------------------------------------
# Title data — 65 titles (mix of movies and series)
# ---------------------------------------------------------------------------
# Each entry: title, title_type, synopsis_short, release_year, duration_minutes,
#   age_rating, genres (list of slugs, first is primary), mood_tags, theme_tags,
#   is_featured, hls_index (None or index into HLS_STREAMS),
#   country_of_origin, language
# ---------------------------------------------------------------------------

TITLES: list[dict[str, Any]] = [
    # -----------------------------------------------------------------------
    # ACTION (8 titles)
    # -----------------------------------------------------------------------
    {
        "title": "The Dark Signal",
        "title_type": "movie",
        "synopsis_short": "A covert operative discovers a rogue satellite broadcasting a signal that can override any digital system on Earth. She has 48 hours to trace its source before hostile nations weaponize it.",
        "release_year": 2024,
        "duration_minutes": 132,
        "age_rating": "TV-14",
        "genres": ["action", "thriller"],
        "mood_tags": ["intense", "suspenseful", "dark"],
        "theme_tags": ["survival", "technology", "power"],
        "is_featured": True,
        "hls_index": 0,
        "country_of_origin": "US",
        "language": "en",
    },
    {
        "title": "Iron Frontier",
        "title_type": "movie",
        "synopsis_short": "On a colonized Mars, a band of miners rebel against the megacorporation controlling their oxygen supply. What starts as a strike escalates into full-scale guerrilla warfare across the red wastes.",
        "release_year": 2023,
        "duration_minutes": 148,
        "age_rating": "TV-MA",
        "genres": ["action", "sci-fi"],
        "mood_tags": ["epic", "gritty", "intense"],
        "theme_tags": ["justice", "survival", "corruption"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "US",
        "language": "en",
    },
    {
        "title": "Velocity",
        "title_type": "movie",
        "synopsis_short": "A disgraced Formula 1 driver gets one last shot at the championship after a mysterious sponsor offers unlimited funding — but only if he smuggles data chips across borders during race weekends.",
        "release_year": 2024,
        "duration_minutes": 118,
        "age_rating": "TV-14",
        "genres": ["action", "thriller"],
        "mood_tags": ["thrilling", "intense", "suspenseful"],
        "theme_tags": ["redemption", "betrayal", "identity"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "UK",
        "language": "en",
    },
    {
        "title": "Shadow Protocol",
        "title_type": "series",
        "synopsis_short": "A cyber-intelligence unit embedded in five allied nations uncovers a conspiracy that links their own governments to a shadow arms network. Trust is a liability.",
        "release_year": 2023,
        "duration_minutes": None,
        "age_rating": "TV-MA",
        "genres": ["action", "crime"],
        "mood_tags": ["dark", "suspenseful", "intense"],
        "theme_tags": ["betrayal", "power", "corruption"],
        "is_featured": False,
        "hls_index": 1,
        "country_of_origin": "UK",
        "language": "en",
    },
    {
        "title": "Stormbreakers",
        "title_type": "movie",
        "synopsis_short": "When a Category 6 hurricane traps an elite rescue squad inside a flooding offshore oil rig, they must fight both nature and the armed mercenaries who got there first.",
        "release_year": 2024,
        "duration_minutes": 126,
        "age_rating": "TV-14",
        "genres": ["action"],
        "mood_tags": ["intense", "thrilling", "epic"],
        "theme_tags": ["survival", "friendship", "nature"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "US",
        "language": "en",
    },
    {
        "title": "The Last Extraction",
        "title_type": "movie",
        "synopsis_short": "A retired special forces officer is pulled back into service to extract a whistleblower from a fortified embassy in a destabilized Central Asian republic.",
        "release_year": 2022,
        "duration_minutes": 112,
        "age_rating": "TV-MA",
        "genres": ["action", "thriller"],
        "mood_tags": ["gritty", "intense", "suspenseful"],
        "theme_tags": ["justice", "redemption", "war"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "US",
        "language": "en",
    },
    {
        "title": "Blaze Runners",
        "title_type": "series",
        "synopsis_short": "Hotshot wildfire crews in the Pacific Northwest battle increasingly deadly fire seasons while managing personal rivalries, broken families, and a conspiracy behind the arsons.",
        "release_year": 2024,
        "duration_minutes": None,
        "age_rating": "TV-14",
        "genres": ["action", "drama"],
        "mood_tags": ["intense", "atmospheric", "gritty"],
        "theme_tags": ["survival", "nature", "friendship"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "US",
        "language": "en",
    },
    {
        "title": "Steel Horizon",
        "title_type": "movie",
        "synopsis_short": "A former Navy SEAL must protect a cargo ship carrying classified AI technology across pirate-infested waters in the Indian Ocean.",
        "release_year": 2023,
        "duration_minutes": 108,
        "age_rating": "TV-14",
        "genres": ["action"],
        "mood_tags": ["thrilling", "intense", "suspenseful"],
        "theme_tags": ["technology", "survival", "power"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "US",
        "language": "en",
    },

    # -----------------------------------------------------------------------
    # COMEDY (7 titles)
    # -----------------------------------------------------------------------
    {
        "title": "Neighbours from Mars",
        "title_type": "series",
        "synopsis_short": "When an alien family crash-lands in suburban Ohio, they must blend in as typical Americans while secretly repairing their ship. Their human neighbors think they are just eccentric Canadians.",
        "release_year": 2023,
        "duration_minutes": None,
        "age_rating": "TV-PG",
        "genres": ["comedy", "sci-fi", "family"],
        "mood_tags": ["funny", "quirky", "heartwarming"],
        "theme_tags": ["family", "identity", "friendship"],
        "is_featured": True,
        "hls_index": 2,
        "country_of_origin": "US",
        "language": "en",
    },
    {
        "title": "The Audit",
        "title_type": "movie",
        "synopsis_short": "A bumbling IRS auditor accidentally uncovers a massive money-laundering ring while investigating a small-town pet grooming salon. Nobody believes him, including his own boss.",
        "release_year": 2024,
        "duration_minutes": 102,
        "age_rating": "TV-14",
        "genres": ["comedy", "crime"],
        "mood_tags": ["funny", "quirky", "uplifting"],
        "theme_tags": ["justice", "identity", "corruption"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "US",
        "language": "en",
    },
    {
        "title": "Wedding Season",
        "title_type": "movie",
        "synopsis_short": "Two strangers realize they are invited to all the same weddings one summer and form an unlikely alliance to survive the chaos of open bars, awkward speeches, and meddling relatives.",
        "release_year": 2023,
        "duration_minutes": 105,
        "age_rating": "TV-PG",
        "genres": ["comedy", "romance"],
        "mood_tags": ["funny", "heartwarming", "romantic"],
        "theme_tags": ["love", "friendship", "family"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "UK",
        "language": "en",
    },
    {
        "title": "Fully Booked",
        "title_type": "series",
        "synopsis_short": "A struggling bookshop owner in Dublin accidentally becomes a viral literary influencer after her cat knocks over a stack of books on a live stream.",
        "release_year": 2024,
        "duration_minutes": None,
        "age_rating": "TV-PG",
        "genres": ["comedy", "drama"],
        "mood_tags": ["funny", "quirky", "heartwarming"],
        "theme_tags": ["identity", "friendship", "coming-of-age"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "IE",
        "language": "en",
    },
    {
        "title": "Third Shift",
        "title_type": "series",
        "synopsis_short": "The overnight crew at a 24-hour supermarket forms an unlikely family, dealing with bizarre customers, petty feuds, and surprisingly profound 3AM conversations.",
        "release_year": 2022,
        "duration_minutes": None,
        "age_rating": "TV-14",
        "genres": ["comedy"],
        "mood_tags": ["funny", "quirky", "heartwarming"],
        "theme_tags": ["friendship", "identity", "coming-of-age"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "US",
        "language": "en",
    },
    {
        "title": "The Wrong Groom",
        "title_type": "movie",
        "synopsis_short": "A mixup at a destination wedding resort means two completely different grooms show up to the wrong ceremony. Neither realizes the mistake until the vows.",
        "release_year": 2023,
        "duration_minutes": 98,
        "age_rating": "TV-PG",
        "genres": ["comedy", "romance"],
        "mood_tags": ["funny", "heartwarming", "romantic"],
        "theme_tags": ["love", "identity", "family"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "US",
        "language": "en",
    },
    {
        "title": "Startup Chaos",
        "title_type": "series",
        "synopsis_short": "Three college dropouts raise millions for a tech startup nobody understands, least of all themselves. A satirical look at Silicon Valley delusion and accidental genius.",
        "release_year": 2024,
        "duration_minutes": None,
        "age_rating": "TV-14",
        "genres": ["comedy"],
        "mood_tags": ["funny", "quirky", "whimsical"],
        "theme_tags": ["technology", "friendship", "identity"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "US",
        "language": "en",
    },

    # -----------------------------------------------------------------------
    # DRAMA (8 titles)
    # -----------------------------------------------------------------------
    {
        "title": "The Weight of Water",
        "title_type": "movie",
        "synopsis_short": "A Pulitzer-winning journalist returns to her flooded hometown in Louisiana to cover the aftermath of a catastrophic hurricane, only to confront the family secrets she left behind.",
        "release_year": 2024,
        "duration_minutes": 141,
        "age_rating": "TV-14",
        "genres": ["drama"],
        "mood_tags": ["atmospheric", "thought-provoking", "dark"],
        "theme_tags": ["family", "redemption", "nature"],
        "is_featured": True,
        "hls_index": 3,
        "country_of_origin": "US",
        "language": "en",
    },
    {
        "title": "Glass Houses",
        "title_type": "series",
        "synopsis_short": "Five wealthy families in a gated community are forced to reveal their darkest secrets when an anonymous blackmailer posts threats on the neighborhood social app.",
        "release_year": 2023,
        "duration_minutes": None,
        "age_rating": "TV-MA",
        "genres": ["drama", "thriller"],
        "mood_tags": ["dark", "suspenseful", "intense"],
        "theme_tags": ["betrayal", "power", "corruption"],
        "is_featured": False,
        "hls_index": 4,
        "country_of_origin": "US",
        "language": "en",
    },
    {
        "title": "Chalk Dust",
        "title_type": "series",
        "synopsis_short": "An inner-city high school drama teacher transforms lives while battling systemic underfunding and her own battle with addiction. Inspired by real events.",
        "release_year": 2022,
        "duration_minutes": None,
        "age_rating": "TV-14",
        "genres": ["drama"],
        "mood_tags": ["uplifting", "thought-provoking", "heartwarming"],
        "theme_tags": ["redemption", "identity", "coming-of-age"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "US",
        "language": "en",
    },
    {
        "title": "The Crossing",
        "title_type": "movie",
        "synopsis_short": "Two families from opposite sides of a conflict-ridden border forge an unlikely bond while waiting at a refugee processing center. A story of shared humanity amid chaos.",
        "release_year": 2023,
        "duration_minutes": 137,
        "age_rating": "TV-14",
        "genres": ["drama"],
        "mood_tags": ["thought-provoking", "heartwarming", "atmospheric"],
        "theme_tags": ["family", "survival", "friendship"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "DE",
        "language": "en",
    },
    {
        "title": "Unwritten",
        "title_type": "movie",
        "synopsis_short": "An aging novelist suffering from early-onset dementia races to finish her masterwork before her memory fades entirely. Her estranged daughter becomes her reluctant editor.",
        "release_year": 2024,
        "duration_minutes": 124,
        "age_rating": "TV-PG",
        "genres": ["drama"],
        "mood_tags": ["heartwarming", "thought-provoking", "atmospheric"],
        "theme_tags": ["family", "identity", "love"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "UK",
        "language": "en",
    },
    {
        "title": "Crown of Thorns",
        "title_type": "series",
        "synopsis_short": "A political drama following the first female President of a newly independent Baltic nation as she navigates foreign interference, coalition politics, and personal sacrifice.",
        "release_year": 2024,
        "duration_minutes": None,
        "age_rating": "TV-14",
        "genres": ["drama", "thriller"],
        "mood_tags": ["intense", "dark", "suspenseful"],
        "theme_tags": ["power", "betrayal", "justice"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "LT",
        "language": "en",
    },
    {
        "title": "Still Life",
        "title_type": "movie",
        "synopsis_short": "A reclusive painter in rural Provence opens her studio to a group of art therapy patients. As she helps them heal, they unlock a grief she has buried for decades.",
        "release_year": 2022,
        "duration_minutes": 115,
        "age_rating": "TV-PG",
        "genres": ["drama", "romance"],
        "mood_tags": ["atmospheric", "heartwarming", "thought-provoking"],
        "theme_tags": ["redemption", "love", "identity"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "FR",
        "language": "en",
    },
    {
        "title": "The Foundation",
        "title_type": "series",
        "synopsis_short": "An idealistic young architect wins the contract to rebuild a devastated coastal city. But politics, corruption, and competing visions threaten to derail everything.",
        "release_year": 2023,
        "duration_minutes": None,
        "age_rating": "TV-14",
        "genres": ["drama"],
        "mood_tags": ["intense", "thought-provoking", "atmospheric"],
        "theme_tags": ["justice", "corruption", "identity"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "US",
        "language": "en",
    },

    # -----------------------------------------------------------------------
    # THRILLER (6 titles)
    # -----------------------------------------------------------------------
    {
        "title": "The Silence Between",
        "title_type": "movie",
        "synopsis_short": "A forensic linguist is called in when a kidnapper communicates only through obscure literary quotes. Each clue leads deeper into the kidnapper's twisted literary obsession.",
        "release_year": 2024,
        "duration_minutes": 119,
        "age_rating": "TV-MA",
        "genres": ["thriller", "crime"],
        "mood_tags": ["dark", "suspenseful", "mysterious"],
        "theme_tags": ["justice", "identity", "power"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "US",
        "language": "en",
    },
    {
        "title": "Blindside",
        "title_type": "movie",
        "synopsis_short": "A blind woman overhears a murder in the apartment next door, but nobody believes her because the victim seems perfectly alive the next morning. She must prove a crime happened using only sound.",
        "release_year": 2023,
        "duration_minutes": 104,
        "age_rating": "TV-14",
        "genres": ["thriller"],
        "mood_tags": ["suspenseful", "dark", "intense"],
        "theme_tags": ["justice", "identity", "survival"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "US",
        "language": "en",
    },
    {
        "title": "The Informer",
        "title_type": "series",
        "synopsis_short": "A low-level drug dealer becomes an FBI informant inside a cartel, only to realize the bureau is just as corrupt as the criminals. He is trapped between two organizations that want him dead.",
        "release_year": 2022,
        "duration_minutes": None,
        "age_rating": "TV-MA",
        "genres": ["thriller", "crime"],
        "mood_tags": ["dark", "gritty", "intense"],
        "theme_tags": ["survival", "betrayal", "corruption"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "US",
        "language": "en",
    },
    {
        "title": "Switchback",
        "title_type": "movie",
        "synopsis_short": "A train conductor realizes her nightly express service has been secretly transporting something far more dangerous than passengers. She has one route left to uncover the truth.",
        "release_year": 2024,
        "duration_minutes": 109,
        "age_rating": "TV-14",
        "genres": ["thriller"],
        "mood_tags": ["suspenseful", "intense", "atmospheric"],
        "theme_tags": ["justice", "corruption", "survival"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "UK",
        "language": "en",
    },
    {
        "title": "Deadlock",
        "title_type": "series",
        "synopsis_short": "Two rival hostage negotiators are forced to work together when simultaneous sieges erupt in the same city. They suspect the incidents are connected by a master manipulator.",
        "release_year": 2023,
        "duration_minutes": None,
        "age_rating": "TV-MA",
        "genres": ["thriller", "action"],
        "mood_tags": ["intense", "suspenseful", "dark"],
        "theme_tags": ["justice", "power", "betrayal"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "US",
        "language": "en",
    },
    {
        "title": "The Vanishing Point",
        "title_type": "movie",
        "synopsis_short": "An airline pilot discovers her co-pilot mid-flight is not the man assigned to the route. At 35,000 feet with 200 passengers, she must determine who he really is and what he wants.",
        "release_year": 2024,
        "duration_minutes": 96,
        "age_rating": "TV-14",
        "genres": ["thriller"],
        "mood_tags": ["suspenseful", "intense", "thrilling"],
        "theme_tags": ["survival", "identity", "betrayal"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "US",
        "language": "en",
    },

    # -----------------------------------------------------------------------
    # SCI-FI (6 titles)
    # -----------------------------------------------------------------------
    {
        "title": "Echoes of Tomorrow",
        "title_type": "series",
        "synopsis_short": "A quantum physicist receives messages from her future self, each warning of an impending catastrophe. But changing the present creates new timelines with darker consequences.",
        "release_year": 2024,
        "duration_minutes": None,
        "age_rating": "TV-14",
        "genres": ["sci-fi", "drama"],
        "mood_tags": ["mysterious", "thought-provoking", "atmospheric"],
        "theme_tags": ["technology", "identity", "survival"],
        "is_featured": True,
        "hls_index": 0,
        "country_of_origin": "US",
        "language": "en",
    },
    {
        "title": "Colony Nine",
        "title_type": "series",
        "synopsis_short": "On humanity's ninth attempt at interstellar colonization, the settlers discover the planet they were promised is already inhabited by something that has been waiting for them.",
        "release_year": 2023,
        "duration_minutes": None,
        "age_rating": "TV-MA",
        "genres": ["sci-fi", "thriller"],
        "mood_tags": ["dark", "mysterious", "intense"],
        "theme_tags": ["survival", "technology", "power"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "US",
        "language": "en",
    },
    {
        "title": "Neon Divide",
        "title_type": "movie",
        "synopsis_short": "In a neon-lit megacity where consciousness can be digitized, a detective searches for a missing person who may have chosen to exist only in cyberspace.",
        "release_year": 2024,
        "duration_minutes": 138,
        "age_rating": "TV-MA",
        "genres": ["sci-fi", "crime"],
        "mood_tags": ["dark", "atmospheric", "mysterious"],
        "theme_tags": ["technology", "identity", "justice"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "JP",
        "language": "en",
    },
    {
        "title": "The Terraform Diaries",
        "title_type": "series",
        "synopsis_short": "A docudrama following the first generation of terraformers on Venus, told through personal video logs. Equal parts engineering marvel and human drama.",
        "release_year": 2024,
        "duration_minutes": None,
        "age_rating": "TV-PG",
        "genres": ["sci-fi", "drama"],
        "mood_tags": ["epic", "thought-provoking", "atmospheric"],
        "theme_tags": ["technology", "nature", "survival"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "US",
        "language": "en",
    },
    {
        "title": "Last Light",
        "title_type": "movie",
        "synopsis_short": "When the sun begins to dim, a solar physicist discovers the cause is not natural. She joins a clandestine team racing to reverse the process before Earth freezes.",
        "release_year": 2023,
        "duration_minutes": 145,
        "age_rating": "TV-14",
        "genres": ["sci-fi", "action"],
        "mood_tags": ["epic", "intense", "atmospheric"],
        "theme_tags": ["survival", "technology", "nature"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "US",
        "language": "en",
    },
    {
        "title": "Synthetic",
        "title_type": "movie",
        "synopsis_short": "A bioengineered human escapes from a corporate lab and tries to build a life among ordinary people, but her creators will stop at nothing to reclaim their property.",
        "release_year": 2022,
        "duration_minutes": 113,
        "age_rating": "TV-14",
        "genres": ["sci-fi", "thriller"],
        "mood_tags": ["dark", "thought-provoking", "intense"],
        "theme_tags": ["identity", "technology", "justice"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "US",
        "language": "en",
    },

    # -----------------------------------------------------------------------
    # HORROR (5 titles)
    # -----------------------------------------------------------------------
    {
        "title": "The Hollow",
        "title_type": "movie",
        "synopsis_short": "A family moves into a farmhouse in rural Maine where the previous owners vanished without a trace. The house remembers them — and it remembers what it did.",
        "release_year": 2024,
        "duration_minutes": 108,
        "age_rating": "TV-MA",
        "genres": ["horror", "thriller"],
        "mood_tags": ["dark", "atmospheric", "suspenseful"],
        "theme_tags": ["family", "survival", "nature"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "US",
        "language": "en",
    },
    {
        "title": "Beneath the Skin",
        "title_type": "movie",
        "synopsis_short": "A plastic surgeon begins to see something moving under the skin of every patient she operates on. Is it a hallucination, or has she uncovered a parasitic horror?",
        "release_year": 2023,
        "duration_minutes": 97,
        "age_rating": "TV-MA",
        "genres": ["horror"],
        "mood_tags": ["dark", "intense", "mysterious"],
        "theme_tags": ["identity", "survival", "technology"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "US",
        "language": "en",
    },
    {
        "title": "The Watchers",
        "title_type": "series",
        "synopsis_short": "In a remote Icelandic village, the long polar night brings something more than darkness. The villagers have always known the rules: never look directly at the aurora.",
        "release_year": 2024,
        "duration_minutes": None,
        "age_rating": "TV-MA",
        "genres": ["horror", "drama"],
        "mood_tags": ["dark", "atmospheric", "mysterious"],
        "theme_tags": ["survival", "nature", "family"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "IS",
        "language": "en",
    },
    {
        "title": "Room 413",
        "title_type": "movie",
        "synopsis_short": "Every guest who stays in Room 413 of the Grand Albion Hotel experiences the same nightmare. A curious journalist checks in to debunk the myth and discovers it is not a dream.",
        "release_year": 2022,
        "duration_minutes": 94,
        "age_rating": "TV-MA",
        "genres": ["horror", "thriller"],
        "mood_tags": ["dark", "suspenseful", "mysterious"],
        "theme_tags": ["survival", "identity", "power"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "UK",
        "language": "en",
    },
    {
        "title": "Whisper Creek",
        "title_type": "series",
        "synopsis_short": "A true-crime podcaster investigating disappearances in a small Appalachian town realizes the episodes are attracting the attention of whatever is responsible.",
        "release_year": 2023,
        "duration_minutes": None,
        "age_rating": "TV-MA",
        "genres": ["horror", "crime"],
        "mood_tags": ["dark", "atmospheric", "suspenseful"],
        "theme_tags": ["justice", "survival", "nature"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "US",
        "language": "en",
    },

    # -----------------------------------------------------------------------
    # ROMANCE (5 titles)
    # -----------------------------------------------------------------------
    {
        "title": "Parallel Hearts",
        "title_type": "movie",
        "synopsis_short": "Two strangers keep narrowly missing each other across three cities and five years. A bittersweet love story told in reverse, starting from their eventual meeting.",
        "release_year": 2024,
        "duration_minutes": 112,
        "age_rating": "TV-PG",
        "genres": ["romance", "drama"],
        "mood_tags": ["romantic", "heartwarming", "atmospheric"],
        "theme_tags": ["love", "identity", "coming-of-age"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "FR",
        "language": "en",
    },
    {
        "title": "The Bookshop on the Corner",
        "title_type": "movie",
        "synopsis_short": "A London investment banker inherits a crumbling bookshop in the Cotswolds and clashes with the passionate local bookseller who has kept it alive. Sparks, arguments, and feelings ensue.",
        "release_year": 2023,
        "duration_minutes": 106,
        "age_rating": "TV-PG",
        "genres": ["romance", "comedy"],
        "mood_tags": ["heartwarming", "funny", "romantic"],
        "theme_tags": ["love", "identity", "coming-of-age"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "UK",
        "language": "en",
    },
    {
        "title": "Summer in Seville",
        "title_type": "movie",
        "synopsis_short": "A culinary student spends a transformative summer in Seville where she falls for a flamenco musician. Their love blossoms amid the heat, the music, and the looming end of summer.",
        "release_year": 2024,
        "duration_minutes": 118,
        "age_rating": "TV-PG",
        "genres": ["romance"],
        "mood_tags": ["romantic", "atmospheric", "uplifting"],
        "theme_tags": ["love", "identity", "coming-of-age"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "ES",
        "language": "en",
    },
    {
        "title": "Second Chance Cafe",
        "title_type": "series",
        "synopsis_short": "A divorced couple who co-own a cafe in Portland must work together daily. Old feelings reignite, but so do old wounds. Their staff takes bets on the outcome.",
        "release_year": 2023,
        "duration_minutes": None,
        "age_rating": "TV-14",
        "genres": ["romance", "comedy"],
        "mood_tags": ["heartwarming", "funny", "romantic"],
        "theme_tags": ["love", "redemption", "friendship"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "US",
        "language": "en",
    },
    {
        "title": "Letters from Kyoto",
        "title_type": "movie",
        "synopsis_short": "A travel writer discovers a bundle of love letters hidden in a vintage kimono bought at a Kyoto market. She traces the letters to their origin, uncovering an epic wartime love story.",
        "release_year": 2022,
        "duration_minutes": 128,
        "age_rating": "TV-PG",
        "genres": ["romance", "drama"],
        "mood_tags": ["romantic", "atmospheric", "thought-provoking"],
        "theme_tags": ["love", "war", "identity"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "JP",
        "language": "en",
    },

    # -----------------------------------------------------------------------
    # DOCUMENTARY (5 titles)
    # -----------------------------------------------------------------------
    {
        "title": "The Algorithm Knows",
        "title_type": "movie",
        "synopsis_short": "An investigative documentary exploring how recommendation algorithms shape public opinion, consumer behavior, and democratic elections. Features interviews with whistleblowers from five tech giants.",
        "release_year": 2024,
        "duration_minutes": 96,
        "age_rating": "TV-PG",
        "genres": ["documentary"],
        "mood_tags": ["thought-provoking", "dark", "intense"],
        "theme_tags": ["technology", "power", "justice"],
        "is_featured": True,
        "hls_index": 1,
        "country_of_origin": "US",
        "language": "en",
    },
    {
        "title": "Deep Blue: The Ocean Floor",
        "title_type": "series",
        "synopsis_short": "A stunning 6-part exploration of the deepest ocean trenches, revealing ecosystems never before filmed. Narrated with poetic precision, each episode descends further into the abyss.",
        "release_year": 2023,
        "duration_minutes": None,
        "age_rating": "TV-G",
        "genres": ["documentary"],
        "mood_tags": ["atmospheric", "epic", "mysterious"],
        "theme_tags": ["nature", "survival", "technology"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "UK",
        "language": "en",
    },
    {
        "title": "Rise: The Basketball Story",
        "title_type": "movie",
        "synopsis_short": "The untold story of how a small-town basketball program in rural Arkansas produced three NBA players in a single generation. Features exclusive interviews and archival footage.",
        "release_year": 2023,
        "duration_minutes": 108,
        "age_rating": "TV-G",
        "genres": ["documentary"],
        "mood_tags": ["uplifting", "heartwarming", "intense"],
        "theme_tags": ["coming-of-age", "family", "redemption"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "US",
        "language": "en",
    },
    {
        "title": "Vanishing Borders",
        "title_type": "series",
        "synopsis_short": "A geo-political documentary series examining how climate change is redrawing national borders. From sinking Pacific islands to Arctic territorial disputes, the map is changing.",
        "release_year": 2024,
        "duration_minutes": None,
        "age_rating": "TV-PG",
        "genres": ["documentary"],
        "mood_tags": ["thought-provoking", "atmospheric", "dark"],
        "theme_tags": ["nature", "power", "survival"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "UK",
        "language": "en",
    },
    {
        "title": "Fermented",
        "title_type": "series",
        "synopsis_short": "A globe-trotting series exploring the world of fermented foods and the cultures that created them. From Korean kimchi to Icelandic shark, every jar tells a story.",
        "release_year": 2022,
        "duration_minutes": None,
        "age_rating": "TV-G",
        "genres": ["documentary"],
        "mood_tags": ["quirky", "heartwarming", "atmospheric"],
        "theme_tags": ["nature", "identity", "family"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "US",
        "language": "en",
    },

    # -----------------------------------------------------------------------
    # ANIMATION (5 titles)
    # -----------------------------------------------------------------------
    {
        "title": "Starweaver",
        "title_type": "movie",
        "synopsis_short": "A young girl discovers she can weave starlight into fabric, creating garments that grant the wearer extraordinary abilities. But a shadow merchant covets her power.",
        "release_year": 2024,
        "duration_minutes": 102,
        "age_rating": "TV-Y",
        "genres": ["animation", "fantasy", "family"],
        "mood_tags": ["whimsical", "epic", "heartwarming"],
        "theme_tags": ["coming-of-age", "power", "family"],
        "is_featured": False,
        "hls_index": 2,
        "country_of_origin": "US",
        "language": "en",
    },
    {
        "title": "The Lost Robots",
        "title_type": "series",
        "synopsis_short": "In a junkyard at the edge of a futuristic city, discarded robots form their own society and embark on adventures to prove they still have purpose.",
        "release_year": 2023,
        "duration_minutes": None,
        "age_rating": "TV-Y",
        "genres": ["animation", "family", "sci-fi"],
        "mood_tags": ["heartwarming", "funny", "whimsical"],
        "theme_tags": ["friendship", "identity", "technology"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "US",
        "language": "en",
    },
    {
        "title": "Mythic Lands",
        "title_type": "series",
        "synopsis_short": "An animated anthology series where each episode brings a different mythological story to life, from Norse sagas to West African legends to Japanese folklore.",
        "release_year": 2024,
        "duration_minutes": None,
        "age_rating": "TV-PG",
        "genres": ["animation", "fantasy"],
        "mood_tags": ["epic", "atmospheric", "mysterious"],
        "theme_tags": ["power", "nature", "identity"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "JP",
        "language": "en",
    },
    {
        "title": "Pepper and Pine",
        "title_type": "series",
        "synopsis_short": "A pepper shaker and a pine tree air freshener go on road trip adventures in a campervan driven by an oblivious family. A charming preschool favourite.",
        "release_year": 2022,
        "duration_minutes": None,
        "age_rating": "TV-Y",
        "genres": ["animation", "family"],
        "mood_tags": ["funny", "heartwarming", "whimsical"],
        "theme_tags": ["friendship", "family", "nature"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "UK",
        "language": "en",
    },
    {
        "title": "The Dragon Painter",
        "title_type": "movie",
        "synopsis_short": "A mute boy in feudal Japan discovers that the dragons he paints come to life at night. Pursued by a warlord who wants the power, the boy must protect both his art and his village.",
        "release_year": 2023,
        "duration_minutes": 95,
        "age_rating": "TV-PG",
        "genres": ["animation", "fantasy"],
        "mood_tags": ["atmospheric", "epic", "heartwarming"],
        "theme_tags": ["power", "identity", "war"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "JP",
        "language": "en",
    },

    # -----------------------------------------------------------------------
    # CRIME (5 titles)
    # -----------------------------------------------------------------------
    {
        "title": "Cold Trail",
        "title_type": "series",
        "synopsis_short": "A retired detective is haunted by the one case she never solved. When new evidence surfaces 20 years later, she reopens the investigation against the wishes of the department.",
        "release_year": 2024,
        "duration_minutes": None,
        "age_rating": "TV-MA",
        "genres": ["crime", "drama"],
        "mood_tags": ["dark", "suspenseful", "atmospheric"],
        "theme_tags": ["justice", "redemption", "betrayal"],
        "is_featured": False,
        "hls_index": 3,
        "country_of_origin": "US",
        "language": "en",
    },
    {
        "title": "The Fence",
        "title_type": "movie",
        "synopsis_short": "A seemingly respectable antiques dealer in Amsterdam runs the largest stolen art operation in Europe. When Interpol closes in, his own family becomes his greatest liability.",
        "release_year": 2023,
        "duration_minutes": 121,
        "age_rating": "TV-MA",
        "genres": ["crime", "thriller"],
        "mood_tags": ["dark", "intense", "suspenseful"],
        "theme_tags": ["betrayal", "family", "power"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "NL",
        "language": "en",
    },
    {
        "title": "Undercover Mommy",
        "title_type": "series",
        "synopsis_short": "A narcotics officer goes undercover at an elite suburban school's parent committee to bust a prescription drug ring. The PTA politics turn out to be more dangerous than the criminals.",
        "release_year": 2023,
        "duration_minutes": None,
        "age_rating": "TV-14",
        "genres": ["crime", "comedy"],
        "mood_tags": ["funny", "suspenseful", "quirky"],
        "theme_tags": ["justice", "family", "identity"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "US",
        "language": "en",
    },
    {
        "title": "Blood Ledger",
        "title_type": "movie",
        "synopsis_short": "An accountant discovers that the charity she audits is a front for human trafficking. She embeds a trail of evidence inside the financial records, but the clock is ticking.",
        "release_year": 2024,
        "duration_minutes": 114,
        "age_rating": "TV-MA",
        "genres": ["crime", "thriller"],
        "mood_tags": ["dark", "intense", "gritty"],
        "theme_tags": ["justice", "corruption", "survival"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "US",
        "language": "en",
    },
    {
        "title": "The Precinct",
        "title_type": "series",
        "synopsis_short": "A fly-on-the-wall drama set inside a Chicago police precinct, where overworked detectives, burned-out sergeants, and idealistic rookies collide over every shift.",
        "release_year": 2022,
        "duration_minutes": None,
        "age_rating": "TV-MA",
        "genres": ["crime", "drama"],
        "mood_tags": ["gritty", "intense", "dark"],
        "theme_tags": ["justice", "friendship", "corruption"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "US",
        "language": "en",
    },

    # -----------------------------------------------------------------------
    # FANTASY (5 titles)
    # -----------------------------------------------------------------------
    {
        "title": "The Ember Throne",
        "title_type": "series",
        "synopsis_short": "In a world where fire is a living element, a young blacksmith discovers she can command the flames. A rival kingdom wants to harness her power to fuel their war machine.",
        "release_year": 2024,
        "duration_minutes": None,
        "age_rating": "TV-14",
        "genres": ["fantasy", "action"],
        "mood_tags": ["epic", "dark", "intense"],
        "theme_tags": ["power", "war", "identity"],
        "is_featured": False,
        "hls_index": 4,
        "country_of_origin": "US",
        "language": "en",
    },
    {
        "title": "The Cartographer's Daughter",
        "title_type": "movie",
        "synopsis_short": "The daughter of a legendary mapmaker inherits a map that shows places that should not exist. Following it leads her to a hidden realm between worlds.",
        "release_year": 2023,
        "duration_minutes": 134,
        "age_rating": "TV-PG",
        "genres": ["fantasy", "family"],
        "mood_tags": ["whimsical", "epic", "atmospheric"],
        "theme_tags": ["coming-of-age", "family", "identity"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "UK",
        "language": "en",
    },
    {
        "title": "Moonshade",
        "title_type": "series",
        "synopsis_short": "An order of night-witches protects a crumbling empire from creatures that emerge when the moon disappears. Their ancient pact is fraying, and the longest eclipse in centuries approaches.",
        "release_year": 2024,
        "duration_minutes": None,
        "age_rating": "TV-MA",
        "genres": ["fantasy", "horror"],
        "mood_tags": ["dark", "atmospheric", "mysterious"],
        "theme_tags": ["power", "survival", "betrayal"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "US",
        "language": "en",
    },
    {
        "title": "The Silver Compass",
        "title_type": "movie",
        "synopsis_short": "Three siblings find a compass that always points towards danger. To save their missing parents, they must follow it through enchanted forests, floating cities, and a sea of glass.",
        "release_year": 2023,
        "duration_minutes": 127,
        "age_rating": "TV-PG",
        "genres": ["fantasy", "family"],
        "mood_tags": ["whimsical", "heartwarming", "epic"],
        "theme_tags": ["family", "coming-of-age", "friendship"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "US",
        "language": "en",
    },
    {
        "title": "Thornwood Academy",
        "title_type": "series",
        "synopsis_short": "A scholarship student at an elite school for young magicians discovers the institution is built on a dark secret. The headmaster is not teaching magic — he is harvesting it.",
        "release_year": 2022,
        "duration_minutes": None,
        "age_rating": "TV-14",
        "genres": ["fantasy", "drama"],
        "mood_tags": ["mysterious", "dark", "atmospheric"],
        "theme_tags": ["power", "coming-of-age", "betrayal"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "UK",
        "language": "en",
    },

    # -----------------------------------------------------------------------
    # FAMILY (5 titles)
    # -----------------------------------------------------------------------
    {
        "title": "Paws & Claws Rescue",
        "title_type": "series",
        "synopsis_short": "A heartwarming series following the daily adventures of a coastal animal rescue center run by siblings. Every episode features a real-world animal care lesson.",
        "release_year": 2024,
        "duration_minutes": None,
        "age_rating": "TV-Y",
        "genres": ["family", "comedy"],
        "mood_tags": ["heartwarming", "funny", "uplifting"],
        "theme_tags": ["nature", "friendship", "family"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "US",
        "language": "en",
    },
    {
        "title": "Camp Pinecrest",
        "title_type": "movie",
        "synopsis_short": "A group of misfit kids at summer camp must work together to save the camp from closure by winning an inter-camp competition they have never once entered.",
        "release_year": 2023,
        "duration_minutes": 98,
        "age_rating": "TV-G",
        "genres": ["family", "comedy"],
        "mood_tags": ["heartwarming", "funny", "uplifting"],
        "theme_tags": ["friendship", "coming-of-age", "family"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "US",
        "language": "en",
    },
    {
        "title": "The Treasure Map Trail",
        "title_type": "movie",
        "synopsis_short": "Two cousins spending the summer at their grandfather's farm discover a hand-drawn treasure map hidden inside an old barn. Their quest takes them across the countryside.",
        "release_year": 2024,
        "duration_minutes": 92,
        "age_rating": "TV-G",
        "genres": ["family"],
        "mood_tags": ["heartwarming", "whimsical", "uplifting"],
        "theme_tags": ["family", "friendship", "coming-of-age"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "US",
        "language": "en",
    },
    {
        "title": "Chef Junior",
        "title_type": "series",
        "synopsis_short": "A cooking competition series where kids aged 8-12 tackle ambitious dishes, learn from professional chefs, and compete with creativity, enthusiasm, and the occasional kitchen disaster.",
        "release_year": 2023,
        "duration_minutes": None,
        "age_rating": "TV-G",
        "genres": ["family"],
        "mood_tags": ["heartwarming", "funny", "uplifting"],
        "theme_tags": ["coming-of-age", "friendship", "identity"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "US",
        "language": "en",
    },
    {
        "title": "Melody Makers",
        "title_type": "movie",
        "synopsis_short": "A group of kids from different musical backgrounds form a band to enter a citywide talent show. They learn that harmony means more than just notes on a page.",
        "release_year": 2022,
        "duration_minutes": 96,
        "age_rating": "TV-G",
        "genres": ["family"],
        "mood_tags": ["heartwarming", "uplifting", "funny"],
        "theme_tags": ["friendship", "coming-of-age", "identity"],
        "is_featured": False,
        "hls_index": None,
        "country_of_origin": "US",
        "language": "en",
    },
]


# ---------------------------------------------------------------------------
# Cast data: fictional but realistic names
# ---------------------------------------------------------------------------
# Each entry maps to a title (by index) and contains cast members.
# We generate this programmatically to keep the data file manageable.
# ---------------------------------------------------------------------------

_ACTORS = [
    "Elena Vasquez", "Marcus Chen", "Sarah Okonkwo", "James Thornton",
    "Yuki Tanaka", "Isabella Rossi", "David Kim", "Amara Osei",
    "Liam Fitzgerald", "Priya Sharma", "Noah Williams", "Sofia Martinez",
    "Oliver Grant", "Zara Hassan", "Ethan Brooks", "Maya Johansson",
    "Ryan Patel", "Chloe Dubois", "Daniel Akimoto", "Nadia Petrov",
    "Leo Campbell", "Hannah Yoon", "Sebastian Moore", "Fatima Al-Rashid",
    "Owen Taylor", "Isla MacLeod", "Gabriel Santos", "Emma Lindqvist",
    "Kai Nakamura", "Aria Bennett", "Lucas Bergman", "Rosa Delgado",
    "Aiden Walsh", "Leila Nouri", "Vincent Okafor", "Clara Eriksson",
    "Marcus Powell", "Anya Volkov", "Theo Henderson", "Mei-Ling Wu",
]

_DIRECTORS = [
    "Christopher Leigh", "Ava DeSilva", "Park Jin-soo", "Margot Heller",
    "Tomasz Kowalski", "Ingrid Svensson", "Rafael Mendoza", "Claire Ashford",
    "Adrien Moreau", "Kamila Nowak", "Raj Kapoor", "Helen Zhang",
]

_WRITERS = [
    "Jonathan Mercer", "Lena Osterman", "Davi Ferreira", "Naomi Blackwell",
    "Sven Halvorsen", "Tanvi Mehta", "Fiona O'Brien", "Kenji Watanabe",
    "Petra Koller", "Alex Drummond", "Yara Hamidi", "Brian Kessler",
]

_CHARACTER_NAMES = [
    "Jack Monroe", "Sarah Vance", "Detective Kim", "Dr. Elena Torres",
    "Commander Hayes", "Professor Nguyen", "Agent Riley", "Captain Strand",
    "Maya Cross", "Alex Mercer", "Lila Stone", "Max Hartley",
    "Rosa Gutierrez", "Tom Brennan", "Officer Chen", "Director Walsh",
    "Anna Kowalski", "Ben Archer", "Clara Moon", "Danny Park",
]


def _build_cast_for_title(title_index: int) -> list[dict[str, Any]]:
    """Generate 3-6 cast entries for a given title index."""
    import random

    rng = random.Random(title_index * 31)  # deterministic seed per title
    n_actors = rng.randint(2, 4)
    n_crew = rng.randint(1, 2)

    cast: list[dict[str, Any]] = []
    actor_pool = list(_ACTORS)
    rng.shuffle(actor_pool)

    char_pool = list(_CHARACTER_NAMES)
    rng.shuffle(char_pool)

    for i in range(n_actors):
        cast.append({
            "person_name": actor_pool[i % len(actor_pool)],
            "role": "actor",
            "character_name": char_pool[i % len(char_pool)],
            "sort_order": i,
        })

    director = _DIRECTORS[title_index % len(_DIRECTORS)]
    cast.append({
        "person_name": director,
        "role": "director",
        "character_name": None,
        "sort_order": n_actors,
    })

    for j in range(n_crew - 1):
        writer = _WRITERS[(title_index + j) % len(_WRITERS)]
        cast.append({
            "person_name": writer,
            "role": "writer",
            "character_name": None,
            "sort_order": n_actors + 1 + j,
        })

    return cast


# ---------------------------------------------------------------------------
# Season/Episode generation for series
# ---------------------------------------------------------------------------

_EPISODE_ADJECTIVES = [
    "The", "A New", "Into the", "Beyond the", "Under the",
    "Return of the", "Shadow of", "Heart of", "Edge of", "Rise of",
]

_EPISODE_NOUNS = [
    "Reckoning", "Storm", "Silence", "Truth", "Ashes",
    "Horizon", "Abyss", "Flame", "Cipher", "Mirror",
    "Void", "Crossing", "Promise", "Fracture", "Paradox",
    "Threshold", "Veil", "Catalyst", "Remnant", "Genesis",
]


def _generate_episode_title(season: int, ep: int) -> str:
    """Generate a plausible episode title deterministically."""
    import random

    rng = random.Random(season * 100 + ep)
    adj = rng.choice(_EPISODE_ADJECTIVES)
    noun = rng.choice(_EPISODE_NOUNS)
    return f"{adj} {noun}"


def _generate_episode_synopsis(title_name: str, season: int, ep: int) -> str:
    """Generate a short episode synopsis."""
    synopses = [
        f"The stakes rise as the team faces an unexpected betrayal in the heart of their operation.",
        f"A shocking discovery forces everyone to reconsider their alliances and motives.",
        f"Personal secrets surface at the worst possible time, threatening to unravel months of progress.",
        f"An outsider arrives with information that changes everything the group thought they knew.",
        f"Tensions boil over as two key characters clash over a decision that could define the future.",
        f"A race against time pushes the protagonists to their breaking point.",
        f"Flashbacks reveal a hidden connection between events that seemed unrelated until now.",
        f"The aftermath of a crisis brings unexpected clarity and a dangerous new resolve.",
        f"A quiet episode of reflection precedes the storm everyone knows is coming.",
        f"The season builds toward a confrontation that has been brewing since the very first episode.",
    ]
    import random

    rng = random.Random(hash(title_name) + season * 100 + ep)
    return rng.choice(synopses)


# ---------------------------------------------------------------------------
# Main seed function
# ---------------------------------------------------------------------------


async def seed_catalog(session: AsyncSession) -> dict[str, int]:
    """Seed genres, titles, cast, seasons, and episodes.

    Idempotent: skips if genres already exist.
    Returns counts of created entities.
    """
    # Check if already seeded
    result = await session.execute(select(Genre).limit(1))
    if result.scalar_one_or_none() is not None:
        print("  [seed_catalog] Catalog already seeded, skipping.")
        return {"genres": 0, "titles": 0, "title_genres": 0, "cast_members": 0, "seasons": 0, "episodes": 0}

    # ------------------------------------------------------------------
    # 1. Create genres
    # ------------------------------------------------------------------
    genre_map: dict[str, uuid.UUID] = {}
    for g in GENRES:
        genre_id = uuid.uuid4()
        genre_map[g["slug"]] = genre_id
        session.add(Genre(id=genre_id, name=g["name"], slug=g["slug"]))
    await session.flush()
    print(f"  [seed_catalog] Created {len(GENRES)} genres.")

    # ------------------------------------------------------------------
    # 2. Create titles with genre associations and cast
    # ------------------------------------------------------------------
    title_ids: list[uuid.UUID] = []
    title_genre_count = 0
    cast_count = 0

    for idx, t in enumerate(TITLES):
        title_id = uuid.uuid4()
        title_ids.append(title_id)

        slug = t["title"].lower().replace(" ", "-").replace("'", "").replace(":", "")
        hls_url = HLS_STREAMS[t["hls_index"]] if t["hls_index"] is not None else None

        session.add(Title(
            id=title_id,
            title=t["title"],
            title_type=t["title_type"],
            synopsis_short=t["synopsis_short"],
            release_year=t["release_year"],
            duration_minutes=t["duration_minutes"],
            age_rating=t["age_rating"],
            country_of_origin=t["country_of_origin"],
            language=t["language"],
            poster_url=f"https://picsum.photos/seed/{slug}/300/450",
            landscape_url=f"https://picsum.photos/seed/{slug}/640/360",
            hls_manifest_url=hls_url,
            is_featured=t["is_featured"],
            mood_tags=t["mood_tags"],
            theme_tags=t["theme_tags"],
        ))

        # Genre associations
        for gi, genre_slug in enumerate(t["genres"]):
            if genre_slug in genre_map:
                session.add(TitleGenre(
                    title_id=title_id,
                    genre_id=genre_map[genre_slug],
                    is_primary=(gi == 0),
                ))
                title_genre_count += 1

        # Cast
        cast_entries = _build_cast_for_title(idx)
        for c in cast_entries:
            session.add(TitleCast(
                title_id=title_id,
                person_name=c["person_name"],
                role=c["role"],
                character_name=c["character_name"],
                sort_order=c["sort_order"],
            ))
            cast_count += 1

    await session.flush()
    print(f"  [seed_catalog] Created {len(TITLES)} titles, {title_genre_count} genre links, {cast_count} cast entries.")

    # ------------------------------------------------------------------
    # 3. Create seasons and episodes for series titles
    # ------------------------------------------------------------------
    import random

    rng = random.Random(42)
    season_count = 0
    episode_count = 0

    series_titles = [(idx, t) for idx, t in enumerate(TITLES) if t["title_type"] == "series"]

    for idx, t in series_titles:
        title_id = title_ids[idx]
        hls_url = HLS_STREAMS[t["hls_index"]] if t["hls_index"] is not None else None
        num_seasons = rng.randint(1, 3)

        for s in range(1, num_seasons + 1):
            season_id = uuid.uuid4()
            session.add(Season(
                id=season_id,
                title_id=title_id,
                season_number=s,
                name=f"Season {s}",
                synopsis=f"Season {s} of {t['title']} brings new challenges and deeper mysteries.",
            ))
            season_count += 1

            num_episodes = rng.randint(6, 10)
            for e in range(1, num_episodes + 1):
                ep_title = _generate_episode_title(s, e)
                ep_synopsis = _generate_episode_synopsis(t["title"], s, e)
                ep_duration = rng.choice([22, 28, 32, 42, 45, 48, 52, 55])

                session.add(Episode(
                    season_id=season_id,
                    episode_number=e,
                    title=ep_title,
                    synopsis=ep_synopsis,
                    duration_minutes=ep_duration,
                    hls_manifest_url=hls_url,
                ))
                episode_count += 1

    await session.flush()
    print(f"  [seed_catalog] Created {season_count} seasons, {episode_count} episodes.")

    await session.commit()

    return {
        "genres": len(GENRES),
        "titles": len(TITLES),
        "title_genres": title_genre_count,
        "cast_members": cast_count,
        "seasons": season_count,
        "episodes": episode_count,
    }
