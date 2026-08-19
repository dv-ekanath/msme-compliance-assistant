from __future__ import annotations

import math

from app.embeddings.mock_provider import MockEmbeddingProvider


def test_mock_embedding_is_deterministic():
    provider = MockEmbeddingProvider(dimension=384)
    a = provider.embed_text("What is the GST registration threshold?")
    b = provider.embed_text("What is the GST registration threshold?")
    assert a == b


def test_mock_embedding_differs_for_different_text():
    provider = MockEmbeddingProvider(dimension=384)
    a = provider.embed_text("GST registration threshold")
    b = provider.embed_text("EPF applicability threshold")
    assert a != b


def test_mock_embedding_respects_configured_dimension():
    provider = MockEmbeddingProvider(dimension=128)
    vec = provider.embed_text("hello")
    assert len(vec) == 128
    assert provider.dimension == 128


def test_mock_embedding_is_normalized():
    provider = MockEmbeddingProvider(dimension=384)
    vec = provider.embed_text("normalize me")
    norm = math.sqrt(sum(v * v for v in vec))
    assert abs(norm - 1.0) < 1e-6


def test_embed_documents_matches_embed_text_per_item():
    provider = MockEmbeddingProvider(dimension=384)
    texts = ["first chunk", "second chunk", "third chunk"]
    batch = provider.embed_documents(texts)
    individual = [provider.embed_text(t) for t in texts]
    assert batch == individual


def test_embed_documents_returns_one_vector_per_input():
    provider = MockEmbeddingProvider(dimension=384)
    result = provider.embed_documents(["a", "b", "c", "d"])
    assert len(result) == 4
    assert all(len(vec) == 384 for vec in result)
