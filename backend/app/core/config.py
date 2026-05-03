from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "IMS Backend"
    app_env: str = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    redis_url: str = "redis://localhost:6379/0"
    postgres_dsn: str = "postgresql://ims:ims@localhost:5432/ims"
    mongo_url: str = "mongodb://localhost:27017"
    mongo_db: str = "ims"

    queue_stream: str = "ims:signals"
    queue_group: str = "ims-workers"
    queue_consumer: str = "worker-1"

    rate_limit_per_minute: int = Field(default=600, ge=1)
    rate_limit_window_seconds: int = Field(default=60, ge=1)
    debounce_ttl_seconds: int = Field(default=10, ge=1)
    metrics_interval_seconds: int = Field(default=5, ge=1)
    queue_block_ms: int = Field(default=1000, ge=1)
    queue_read_count: int = Field(default=100, ge=1)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
