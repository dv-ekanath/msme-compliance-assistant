from __future__ import annotations

from app.embeddings.base import EmbeddingProvider


class LocalEmbeddingProvider(EmbeddingProvider):
    """sentence-transformers running on-box -- no API key, no external
    credits, real semantic embeddings. This is the default provider
    (EMBEDDING_PROVIDER=local).

    `sentence_transformers` is imported lazily inside __init__ (not at
    module import time), matching `app.llm.anthropic_provider`'s pattern:
    importing this module is always safe; only instantiating it requires
    the package to be installed.
    """

    name = "local"

    def __init__(self, model_name: str, expected_dimension: int) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "The 'sentence-transformers' package is not installed. It's a "
                "listed dependency in requirements.txt -- run `pip install -r "
                "requirements.txt`, or set EMBEDDING_PROVIDER=mock for offline dev."
            ) from exc

        self._model = SentenceTransformer(model_name)
        get_dimension = getattr(self._model, "get_embedding_dimension", None) or getattr(
            self._model, "get_sentence_embedding_dimension"
        )
        actual_dimension = get_dimension()
        if actual_dimension != expected_dimension:
            raise RuntimeError(
                f"EMBEDDING_MODEL '{model_name}' produces {actual_dimension}-dim "
                f"vectors, but EMBEDDING_DIMENSION is configured as "
                f"{expected_dimension} (this must match the pgvector column "
                "width -- update backend/.env and re-run the Phase 2 migration "
                "if you intentionally changed the model)."
            )
        self.dimension = actual_dimension

    def embed_text(self, text: str) -> list[float]:
        return self._model.encode(text, normalize_embeddings=True).tolist()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._model.encode(texts, normalize_embeddings=True).tolist()
