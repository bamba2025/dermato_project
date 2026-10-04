from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    database_url: str
    redis_url: str
    s3_endpoint: str
    s3_bucket: str = "derma-private"
    s3_access_key: str
    s3_secret_key: str
    jwt_secret: str = Field(min_length=32)
    jwt_issuer: str = "derma-api"
    jwt_audience: str = "derma-client"
    access_token_minutes: int = Field(default=15, ge=1, le=60)
    refresh_token_days: int = Field(default=30, ge=1, le=90)
    auth_rate_limit: int = Field(default=10, ge=1)
    auth_rate_window_seconds: int = Field(default=60, ge=1)
    cors_origins: list[str] = ["http://localhost:3000"]
    model_backbone: str = "mock"
    model_path: str = "/models"
    medgemma_enabled: bool = False
    gpu_device: str = "cpu"

    @model_validator(mode="after")
    def validate_environment(self) -> "Settings":
        if self.environment not in {"development", "test", "production"}:
            raise ValueError("Unknown environment")
        if self.environment == "production":
            if not self.s3_endpoint.startswith("https://"):
                raise ValueError("Production object storage requires HTTPS")
            if not self.database_url.startswith("postgresql"):
                raise ValueError("Production requires PostgreSQL")
            if any(not origin.startswith("https://") for origin in self.cors_origins):
                raise ValueError("Production CORS origins require HTTPS")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
