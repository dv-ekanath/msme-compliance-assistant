from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.embeddings.base import EmbeddingProvider
from app.embeddings.mock_provider import MockEmbeddingProvider


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    """Single entry point the rest of the app should use to get an
    embedding backend. Selection is controlled by EMBEDDING_PROVIDER so no
    calling code needs to know (or import) sentence-transformers directly.
    """
    settings = get_settings()

    if settings.embedding_provider == "mock":
        return MockEmbeddingProvider(dimension=settings.embedding_dimension)

    if settings.embedding_provider == "local":
        from app.embeddings.local_provider import LocalEmbeddingProvider

        return LocalEmbeddingProvider(
            model_name=settings.embedding_model,
            expected_dimension=settings.embedding_dimension,
        )

    raise ValueError(
        f"Unknown EMBEDDING_PROVIDER: {settings.embedding_provider!r} (expected 'mock' or 'local')"
    )
