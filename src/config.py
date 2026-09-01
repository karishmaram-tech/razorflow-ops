"""Application configuration — validated via pydantic-settings.

Usage:
    from src.config import settings
    settings.DATABASE_URL  # validated & typed
"""

from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Optional

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Top-level settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Razorpay ──────────────────────────────────────────────────────
    razorpay_key_id: str = Field(
        default="rzp_test_xxxxxxxxxxxx",
        description="Razorpay key ID (test or live)",
    )
    razorpay_key_secret: SecretStr = Field(
        default=SecretStr(""),
        description="Razorpay key secret",
    )

    # ── Claude / Anthropic ────────────────────────────────────────────
    anthropic_api_key: SecretStr = Field(
        default=SecretStr(""),
        description="Anthropic API key for Claude",
    )

    # ── Database ──────────────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/merchant_ops",
        description="Async PostgreSQL connection string",
    )
    database_url_sync: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/merchant_ops",
        description="Sync PostgreSQL connection string (for Alembic / tests)",
    )

    # ── Application ───────────────────────────────────────────────────
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Deployment environment",
    )
    log_level: str = Field(default="INFO", description="Root log level")
    api_host: str = Field(default="0.0.0.0", description="API bind host")
    api_port: int = Field(default=8000, description="API bind port")
    debug: bool = Field(default=False, description="Enable debug mode")

    # ── Optional ──────────────────────────────────────────────────────
    redis_url: Optional[str] = Field(
        default=None,
        description="Redis connection string for caching / rate-limiting",
    )

    # ── Derived helpers ───────────────────────────────────────────────

    @field_validator("log_level")
    @classmethod
    def _uppercase_log_level(cls, v: str) -> str:
        return v.upper()

    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        return self.environment == Environment.DEVELOPMENT

    @property
    def anthropic_api_key_str(self) -> str:
        """Convenience accessor – avoids callers needing to .get_secret_value()."""
        return self.anthropic_api_key.get_secret_value()

    @property
    def razorpay_key_secret_str(self) -> str:
        return self.razorpay_key_secret.get_secret_value()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Singleton factory — call once, reuse everywhere."""
    return Settings()


# Module-level shortcut for convenience imports
settings = get_settings()
