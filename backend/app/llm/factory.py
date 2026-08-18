from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.llm.base import LLMProvider
from app.llm.mock_provider import MockLLMProvider


@lru_cache
def get_llm_provider() -> LLMProvider:
    """Single entry point the rest of the app should use to get an LLM.

    Selection is controlled entirely by the LLM_PROVIDER env var so no
    calling code needs to know (or import) which vendor SDK is behind it.
    """
    settings = get_settings()

    if settings.llm_provider == "mock":
        return MockLLMProvider()

    if settings.llm_provider == "anthropic":
        from app.llm.anthropic_provider import AnthropicLLMProvider

        return AnthropicLLMProvider(
            api_key=settings.anthropic_api_key,
            model=settings.anthropic_model,
        )

    raise ValueError(
        f"Unknown LLM_PROVIDER: {settings.llm_provider!r} (expected 'mock' or 'anthropic')"
    )
