from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central app configuration, loaded from environment variables / .env.

    Nothing here hard-codes a vendor SDK. `llm_provider` is the single
    switch that decides which implementation `app.llm.factory` hands back.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    backend_cors_origins: str = "http://localhost:5173"

    database_url: str = (
        "postgresql+psycopg://msme_admin:changeme_dev_password@localhost:5432/msme_compliance"
    )

    # LLM provider selection: "mock" (default, no external calls/keys needed)
    # or "anthropic" (requires anthropic_api_key + the `anthropic` package).
    llm_provider: str = "mock"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-5"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
