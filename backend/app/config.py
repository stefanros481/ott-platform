from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://ott_user:ott_password@localhost:5432/ott_platform"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret: SecretStr
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60
    jwt_refresh_expiry_days: int = 7

    # Database Pool
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_pool_recycle: int = 3600

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:5174"

    # AI / Embeddings
    embedding_model: str = "all-MiniLM-L6-v2"

    # Logging
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


settings = Settings()
