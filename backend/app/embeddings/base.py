from __future__ import annotations

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Interface every embedding backend must implement.

    Mirrors `app.llm.base.LLMProvider`: the rest of the application
    (retrieval, ingestion) depends only on this interface, never on a
    specific embedding library, so the backend can be swapped via the
    EMBEDDING_PROVIDER env var. See `app.embeddings.factory.get_embedding_provider`.
    """

    name: str = "base"
    dimension: int

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """Embed a single piece of text (e.g. a user query)."""

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts (e.g. chunks being ingested)."""
