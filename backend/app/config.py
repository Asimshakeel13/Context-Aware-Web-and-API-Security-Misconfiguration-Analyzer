"""Central application configuration.

All settings are loaded from environment variables (or a local ``.env`` file)
via ``pydantic-settings``. Nothing in the codebase should read ``os.environ``
directly -- import :data:`settings` from here instead. This keeps configuration
in one place, typed and validated at startup.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings.

    Values are validated once at process start. A missing required value or a
    wrong type raises immediately, so the service fails fast instead of dying
    mid-scan.
    """

    model_config = SettingsConfigDict(
        # Repo-root .env (shared with docker compose), then a local override.
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- Environment -------------------------------------------------------
    ENVIRONMENT: Literal["development", "staging", "production", "test"] = "development"
    DEBUG: bool = True

    # --- Datastores --------------------------------------------------------
    # Async driver (asyncpg) everywhere: FastAPI, the scanner pipeline, Celery
    # tasks and Alembic migrations.
    DATABASE_URL: str = "postgresql+asyncpg://cawasma:cawasma@localhost:5432/cawasma"
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # --- Frontend / CORS ---------------------------------------------------
    # Comma-separated list of allowed origins. Never "*": the scanner returns
    # sensitive assessment data, so origins are explicit.
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # --- Scanner safety limits ---------------------------------------------
    REQUEST_TIMEOUT: float = 15.0            # seconds per HTTP request
    MAX_RESPONSE_SIZE: int = 5_000_000       # bytes; larger bodies are truncated
    MAX_ENDPOINTS: int = 200                 # hard cap on discovered endpoints
    MAX_CRAWL_DEPTH: int = 2                 # recursive crawl depth
    MAX_REDIRECTS: int = 5
    MAX_CONCURRENT_REQUESTS: int = 10        # httpx connection concurrency
    RATE_LIMIT_PROBE_COUNT: int = 15         # burst size for rate-limit check
    USER_AGENT: str = "CAWASMA-Scanner/1.0 (+defensive-security-research)"

    # Dispatch scans to Celery on creation. Disabled in tests (no broker).
    AUTO_DISPATCH_SCANS: bool = True
    # Run scans in-process (no Celery/Redis needed). For simple deploys / demos.
    RUN_SCANS_INLINE: bool = False
    # Contract v1 routes answer with example data (app/api/mock.py): no DB or
    # scanner needed. For frontend development only.
    MOCK_API: bool = False

    # Spec files (checks.yaml, cvss_mapping.yaml, chains.yaml). Defaults to the
    # repo's config/ dir; in Docker that resolves to /config (mounted).
    CONFIG_DIR: str = str(Path(__file__).resolve().parents[2] / "config")

    # --- Optional LLM (never required for core scanning) -------------------
    # Used by the NLP classifier to expand URL abbreviations (usr -> user).
    # When disabled or no key is set, the built-in abbreviation table is used.
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    LLM_ENABLED: bool = False
    LLM_PROVIDER: Literal["openai", "anthropic"] = "anthropic"
    LLM_MODEL: str = ""   # blank -> provider default

    # --- Derived helpers ---------------------------------------------------
    @property
    def frontend_origins(self) -> list[str]:
        """CORS origins as a clean list."""
        return [o.strip() for o in self.FRONTEND_ORIGIN.split(",") if o.strip()]

    @field_validator("MAX_CRAWL_DEPTH")
    @classmethod
    def _cap_depth(cls, v: int) -> int:
        # Depth is intentionally shallow for a safe black-box scanner.
        if v > 4:
            raise ValueError("MAX_CRAWL_DEPTH must be <= 4 for safe scanning")
        return v


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance (one per process)."""
    return Settings()


settings = get_settings()
