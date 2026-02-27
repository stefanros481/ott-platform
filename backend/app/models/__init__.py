# Import all models so Alembic and SQLAlchemy can discover them
from app.models.catalog import Episode, Genre, Season, Title, TitleCast, TitleGenre  # noqa: F401
from app.models.embedding import ContentEmbedding  # noqa: F401
from app.models.entitlement import ContentPackage, PackageContent, TitleOffer, UserEntitlement  # noqa: F401
from app.models.epg import Channel, ChannelFavorite, ScheduleEntry  # noqa: F401
from app.models.stream_sessions import StreamSession  # noqa: F401
from app.models.user import Profile, RefreshToken, User  # noqa: F401
from app.models.viewing import Bookmark, Rating, WatchlistItem  # noqa: F401
from app.models.viewing_time import TimeGrant, ViewingSession, ViewingTimeBalance, ViewingTimeConfig  # noqa: F401
from app.models.analytics import AnalyticsEvent, QueryJob  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.tstv import DRMKey, Recording, TSTVSession  # noqa: F401
