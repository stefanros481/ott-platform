# Import all models so Alembic and SQLAlchemy can discover them
from app.models.catalog import Episode, Genre, Season, Title, TitleCast, TitleGenre  # noqa: F401
from app.models.embedding import ContentEmbedding  # noqa: F401
from app.models.entitlement import ContentPackage, PackageContent, UserEntitlement  # noqa: F401
from app.models.epg import Channel, ChannelFavorite, ScheduleEntry  # noqa: F401
from app.models.user import Profile, RefreshToken, User  # noqa: F401
from app.models.viewing import Bookmark, Rating, WatchlistItem  # noqa: F401
