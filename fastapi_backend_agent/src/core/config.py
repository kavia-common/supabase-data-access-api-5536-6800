from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class _AppSettings(BaseSettings):
    """
    Internal settings model for the application using pydantic-settings.

    Loads environment variables and provides defaults where applicable.
    """

    # Application
    APP_PORT: int = Field(default=3001, description="Port the FastAPI app should run on")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level (e.g., DEBUG, INFO, WARNING, ERROR)")
    CORS_ALLOW_ORIGINS: str = Field(
        default="*",
        description="Comma-separated list of origins for CORS. e.g. http://localhost:3000,https://example.com or '*'",
    )

    # Supabase
    SUPABASE_URL: str = Field(..., description="Supabase Project URL")
    # Prefer service role key if available, otherwise allow anon key; either can be used depending on context
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = Field(
        default=None, description="Supabase service role API key (more privileged)"
    )
    SUPABASE_ANON_KEY: Optional[str] = Field(
        default=None, description="Supabase anon/public API key (less privileged)"
    )
    SUPABASE_SCHEMA: str = Field(default="public", description="Target Postgres schema")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")

    # PUBLIC_INTERFACE
    def get_cors_origins(self) -> List[str]:
        """Return parsed CORS origins as a list."""
        raw = (self.CORS_ALLOW_ORIGINS or "").strip()
        if raw == "" or raw == "*":
            return ["*"]
        # Split by comma and trim whitespace
        return [o.strip() for o in raw.split(",") if o.strip()]

    # PUBLIC_INTERFACE
    def get_supabase_key(self) -> Optional[str]:
        """Return the effective Supabase key preferring service role key over anon key."""
        return self.SUPABASE_SERVICE_ROLE_KEY or self.SUPABASE_ANON_KEY


# PUBLIC_INTERFACE
class Settings(BaseModel):
    """
    Public-facing settings model used throughout the app.

    Wraps the BaseSettings-backed _AppSettings to expose a stable interface.
    """

    app_port: int = 3001
    log_level: str = "INFO"
    cors_allow_origins: List[str] = Field(default_factory=lambda: ["*"])

    supabase_url: str
    supabase_key: Optional[str] = None
    supabase_schema: str = "public"

    # PUBLIC_INTERFACE
    @classmethod
    def from_env(cls) -> "Settings":
        """
        Build Settings by reading the environment via pydantic BaseSettings.
        """
        _raw = _AppSettings()  # reads env and .env based on model_config
        return cls(
            app_port=_raw.APP_PORT,
            log_level=_normalize_log_level(_raw.LOG_LEVEL),
            cors_allow_origins=_raw.get_cors_origins(),
            supabase_url=_raw.SUPABASE_URL,
            supabase_key=_raw.get_supabase_key(),
            supabase_schema=_raw.SUPABASE_SCHEMA,
        )


def _normalize_log_level(level: str) -> str:
    """Normalize and validate log level string."""
    value = (level or "INFO").upper()
    valid = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "TRACE", "NOTSET"}
    # Maintain compatibility with common uvicorn levels
    if value not in valid:
        return "INFO"
    return value


# PUBLIC_INTERFACE
@lru_cache
def get_settings() -> Settings:
    """
    Cached retrieval of Settings for dependency injection.

    This ensures settings are computed once while still allowing unit tests
    to clear the cache if needed.
    """
    return Settings.from_env()
