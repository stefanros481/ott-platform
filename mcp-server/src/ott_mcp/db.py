"""Standalone database connection for the MCP server.

Loads configuration from a .env file (mcp-server/.env) via pydantic-settings.
Does NOT import app.config to avoid requiring JWT_SECRET and other backend-specific env vars.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"  # mcp-server/.env


class McpSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+asyncpg://ott_user:ott_password@localhost:5432/ott_platform"
    ott_backend_path: str = str(Path(__file__).resolve().parents[3] / "backend")


settings = McpSettings()

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_size=5,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(engine, expire_on_commit=False)
