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

    # LLM provider selection: "mock" (default, no external calls/keys needed),
    # "anthropic" (requires anthropic_api_key + the `anthropic` package), or
    # "groq" (requires groq_api_key; uses httpx, already a dependency).
    llm_provider: str = "mock"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-5"
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"

    # Embedding provider selection: "local" (default -- sentence-transformers,
    # runs on-box, no API key/credits) or "mock" (deterministic, dependency-free,
    # used by the test suite). embedding_dimension is the single source of
    # truth for the pgvector column width (app/models/regulatory_chunk.py) and
    # is validated against whatever model actually loads -- never hardcoded
    # a second time.
    embedding_provider: str = "local"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    # Phase 3 watchdog: scans seeded Regulation.source_url values for
    # content changes on an in-process APScheduler interval (no Celery/
    # Redis -- see CLAUDE.md). Disabled in tests (backend/tests/conftest.py
    # sets WATCHDOG_SCHEDULER_ENABLED=false) so the FastAPI TestClient's
    # lifespan doesn't spin up a background job per test.
    watchdog_scan_interval_hours: int = 24
    watchdog_scheduler_enabled: bool = True
    # How many employees away from a regulation's min_employee_count
    # threshold (e.g. EPF's 20, ESI's 10) counts as "approaching" it for a
    # growth-forecast alert.
    growth_forecast_employee_window: int = 3

    # OCR provider selection: "easyocr" (default -- on-box, no API key,
    # downloads a model on first use, same shape as EMBEDDING_PROVIDER=local)
    # or "mock" (deterministic, used by the test suite). English-only by
    # default -- printed GSTIN/PAN/Udyam numbers are Latin-script/digits
    # regardless of surrounding document language, so a second recognition
    # network buys nothing for regex extraction and only costs first-run
    # download time.
    ocr_provider: str = "easyocr"
    ocr_languages: str = "en"

    # Auth (Phase 5). This default secret is dev-only -- override
    # JWT_SECRET_KEY via a real env var for any non-local deployment.
    # A required field with no default would break every test at
    # collection time (Settings is @lru_cache'd, first triggered at
    # import time by app/core/database.py) for no benefit this app's
    # deployment story needs yet.
    jwt_secret_key: str = "dev-only-insecure-secret-change-in-production"
    jwt_expiry_hours: int = 24

    copilot_top_k: int = 5
    # Tuned against the real local model (all-MiniLM-L6-v2): unrelated
    # English text still has a nonzero baseline cosine similarity, so a
    # too-low threshold lets spurious weak matches through as "evidence".
    # 0.3 was verified to filter an off-topic question to zero results
    # while keeping genuine matches (typically 0.4-0.75 in this corpus).
    copilot_similarity_threshold: float = 0.3

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]

    @property
    def ocr_languages_list(self) -> list[str]:
        return [lang.strip() for lang in self.ocr_languages.split(",") if lang.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
