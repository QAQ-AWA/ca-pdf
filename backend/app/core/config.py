from functools import lru_cache
from typing import Any, Sequence

from pydantic import EmailStr, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
    )

    app_name: str = Field(default="Monorepo API", alias="APP_NAME")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    uvicorn_host: str = Field(default="0.0.0.0", alias="UVICORN_HOST")
    uvicorn_port: int = Field(default=8000, alias="UVICORN_PORT")
    database_url: str = Field(default="sqlite:///./app.db", alias="DATABASE_URL")
    secret_key: str = Field(default="change-me", alias="SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=15, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_minutes: int = Field(
        default=60 * 24 * 3,
        alias="REFRESH_TOKEN_EXPIRE_MINUTES",
    )
    backend_cors_origins: list[str] = Field(
        default_factory=lambda: ["*"],
        alias="BACKEND_CORS_ORIGINS",
    )
    auth_rate_limit_requests: int = Field(default=5, alias="AUTH_RATE_LIMIT_REQUESTS")
    auth_rate_limit_window_seconds: int = Field(default=60, alias="AUTH_RATE_LIMIT_WINDOW_SECONDS")
    admin_email: EmailStr | None = Field(default=None, alias="ADMIN_EMAIL")
    admin_password: str | None = Field(default=None, alias="ADMIN_PASSWORD")
    admin_role: str = Field(default="admin", alias="ADMIN_ROLE")

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, value: Any) -> list[str]:
        """Normalize backend CORS origins into a string list."""

        if value is None:
            return ["*"]
        if isinstance(value, str):
            if not value:
                return ["*"]
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        if isinstance(value, Sequence):
            return [str(origin) for origin in value]
        raise ValueError("Invalid CORS origins configuration")

    @field_validator("admin_role", mode="before")
    @classmethod
    def normalize_admin_role(cls, value: str) -> str:
        """Ensure the admin role is stored in lowercase for consistency."""

        return value.lower()


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()


def reload_settings() -> Settings:
    """Refresh and return application settings."""

    get_settings.cache_clear()
    new_settings = get_settings()
    globals()["settings"] = new_settings
    return new_settings


settings = get_settings()
