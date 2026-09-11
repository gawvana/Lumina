"""Central typed configuration for Lumina Telegram School OS."""

import logging
import os
from typing import List, Literal, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("lumina.config")

DEV_JWT_SECRET = "lumina_dev_only_jwt_insecure_secret_key_change_in_production_32b"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    LOG_LEVEL: str = "INFO"

    @property
    def is_dev(self) -> bool:
        return self.ENVIRONMENT == "development"

    # Database connection URL
    DATABASE_URL: str = "sqlite+aiosqlite:///./lumina.db"

    # Telegram Bot configurations
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_BOT_USERNAME: str = "LuminzBot"
    TELEGRAM_WEBHOOK_SECRET: str = ""

    # WebApp URL
    WEBAPP_URL: str = "http://localhost:8000/app"

    # JWT Authentication
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440  # 24 hours standard session
    JWT_ISSUER: str = "lumina-school-os"
    JWT_AUDIENCE: str = "lumina-webapp"

    # Telegram initData replay window (24h max)
    INIT_DATA_MAX_AGE_SECONDS: int = 86400

    # CORS configuration
    ALLOWED_ORIGINS: Union[str, List[str]] = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://web.telegram.org",
        "https://oauth.telegram.org",
    ]

    # Localization and Timezone
    DEFAULT_TIMEZONE: str = "Asia/Tashkent"

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str, info) -> str:
        # Normalize postgres schemes for asyncpg
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://") and "+asyncpg" not in v:
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)

        # Enforce PostgreSQL in production, unless running serverless demo on Vercel
        env = info.data.get("ENVIRONMENT")
        if env == "production" and "sqlite" in v:
            if not os.environ.get("VERCEL"):
                raise ValueError(
                    "SQLite is strictly prohibited in production. Configure a PostgreSQL DATABASE_URL."
                )
            logger.warning(
                "Running SQLite on Vercel serverless. Database in /tmp is ephemeral. "
                "For production persistence, configure PostgreSQL in DATABASE_URL."
            )
            if "./lumina.db" in v:
                v = "sqlite+aiosqlite:////tmp/lumina.db"
        return v

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, v: str, info) -> str:
        env = info.data.get("ENVIRONMENT", "development")
        if env == "production":
            if not v or len(v) < 32 or "dev" in v.lower():
                raise ValueError(
                    "JWT_SECRET_KEY must be a cryptographically secure key of at least 32 characters in production."
                )
            return v
        # In development, fall back safely if unset
        if not v:
            logger.warning("No JWT_SECRET_KEY provided. Using development fallback secret.")
            return DEV_JWT_SECRET
        return v

    @field_validator("TELEGRAM_BOT_TOKEN")
    @classmethod
    def validate_bot_token(cls, v: str, info) -> str:
        env = info.data.get("ENVIRONMENT", "development")
        if env == "production":
            if not v or ":" not in v:
                raise ValueError("Valid TELEGRAM_BOT_TOKEN is required in production.")
        return v

    @field_validator("ALLOWED_ORIGINS")
    @classmethod
    def parse_allowed_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.strip() == "*":
                return ["*"]
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


settings = Settings()
