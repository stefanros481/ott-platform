import functools

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database — M-07: no default credentials; must be provided via .env or env var
    database_url: str

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

    # CORS — M-07: default to empty; must be explicitly configured
    cors_origins: str = ""

    # AI / Embeddings
    embedding_model: str = "all-MiniLM-L6-v2"

    # HLS / SimLive
    hls_segment_dir: str = "/hls_data"
    hls_sources_dir: str = "/hls_sources"
    hls_segment_duration: int = 6
    cdn_base_url: str = "http://localhost:8081"
    api_base_url: str = "http://localhost:8000/api/v1"

    # DRM
    drm_enabled: bool = True

    # Logging
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "extra": "ignore"}

    @functools.cached_property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


settings = Settings()
