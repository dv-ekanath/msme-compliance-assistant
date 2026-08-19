from __future__ import annotations

import hashlib
import math
import random

from app.embeddings.base import EmbeddingProvider


class MockEmbeddingProvider(EmbeddingProvider):
    """Deterministic, dependency-free provider for tests and offline dev.

    Same input text always produces the same vector (seeded from a SHA-256
    hash of the text), so retrieval tests are reproducible without loading
    any ML model. Not semantically meaningful -- do not use for a real demo.
    """

    name = "mock"

    def __init__(self, dimension: int = 384) -> None:
        self.dimension = dimension

    def _embed_one(self, text: str) -> list[float]:
        seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16) % (2**32)
        rng = random.Random(seed)
        raw = [rng.uniform(-1.0, 1.0) for _ in range(self.dimension)]
        norm = math.sqrt(sum(v * v for v in raw)) or 1.0
        return [v / norm for v in raw]

    def embed_text(self, text: str) -> list[float]:
        return self._embed_one(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]
