import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)


class Title(Base):
    __tablename__ = "titles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    title_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'movie' or 'series'
    synopsis_short: Mapped[str | None] = mapped_column(Text)
    synopsis_long: Mapped[str | None] = mapped_column(Text)
    release_year: Mapped[int | None] = mapped_column(Integer)
    duration_minutes: Mapped[int | None] = mapped_column(Integer)  # for movies
    age_rating: Mapped[str | None] = mapped_column(String(10))
    country_of_origin: Mapped[str | None] = mapped_column(String(5))
    language: Mapped[str | None] = mapped_column(String(10))
    poster_url: Mapped[str | None] = mapped_column(String(500))
    landscape_url: Mapped[str | None] = mapped_column(String(500))
    logo_url: Mapped[str | None] = mapped_column(String(500))
    hls_manifest_url: Mapped[str | None] = mapped_column(String(500))
    is_featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mood_tags: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    theme_tags: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    ai_description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    genres: Mapped[list["TitleGenre"]] = relationship(back_populates="title", cascade="all, delete-orphan")
    cast_members: Mapped[list["TitleCast"]] = relationship(back_populates="title", cascade="all, delete-orphan")
    seasons: Mapped[list["Season"]] = relationship(back_populates="title", cascade="all, delete-orphan")


class TitleGenre(Base):
    __tablename__ = "title_genres"

    title_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("titles.id", ondelete="CASCADE"), primary_key=True)
    genre_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    title: Mapped["Title"] = relationship(back_populates="genres")
    genre: Mapped["Genre"] = relationship()


class TitleCast(Base):
    __tablename__ = "title_cast"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("titles.id", ondelete="CASCADE"), nullable=False)
    person_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # 'actor', 'director', 'writer'
    character_name: Mapped[str | None] = mapped_column(String(200))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    title: Mapped["Title"] = relationship(back_populates="cast_members")


class Season(Base):
    __tablename__ = "seasons"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("titles.id", ondelete="CASCADE"), nullable=False)
    season_number: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str | None] = mapped_column(String(200))
    synopsis: Mapped[str | None] = mapped_column(Text)

    title: Mapped["Title"] = relationship(back_populates="seasons")
    episodes: Mapped[list["Episode"]] = relationship(back_populates="season", cascade="all, delete-orphan")


class Episode(Base):
    __tablename__ = "episodes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    season_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False)
    episode_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    synopsis: Mapped[str | None] = mapped_column(Text)
    duration_minutes: Mapped[int | None] = mapped_column(Integer)
    hls_manifest_url: Mapped[str | None] = mapped_column(String(500))

    season: Mapped["Season"] = relationship(back_populates="episodes")
