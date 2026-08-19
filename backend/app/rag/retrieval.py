from __future__ import annotations

import math
from dataclasses import dataclass

from sqlalchemy.orm import Query, Session

from app.domain.enums import SourceStatus
from app.embeddings.base import EmbeddingProvider
from app.models.regulation import Regulation
from app.models.regulatory_chunk import RegulatoryChunk
from app.models.regulatory_document import RegulatoryDocument


@dataclass(frozen=True)
class RetrievedChunk:
    """Retrieval evidence, already flattened to what a citation needs --
    no raw vector internals leak past this dataclass (see app/rag/copilot.py
    and app/schemas/copilot.py, which build citations directly from this).
    """

    chunk_id: str
    document_id: str
    regulation_id: str
    regulation_code: str
    title: str
    authority: str
    source_url: str
    section: str | None
    subsection: str | None
    source_reference: str | None
    status: str
    content: str
    score: float  # cosine similarity, higher = more relevant (roughly 0..1)


class RetrievalService:
    """Semantic retrieval over RegulatoryChunk.

    Uses pgvector's native cosine-distance operator on Postgres (the real
    production path). On SQLite -- used only by the offline test suite,
    see backend/tests/conftest.py -- falls back to an in-Python cosine
    similarity scan, since SQLite has no vector operator. Both paths share
    the same filtering/scoring semantics.

    `status="unverified"` documents are excluded unconditionally: retrieval
    must never surface content that hasn't been reviewed, no matter how
    well it scores.
    """

    def __init__(self, db: Session, embedding_provider: EmbeddingProvider) -> None:
        self.db = db
        self.embedding_provider = embedding_provider

    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        similarity_threshold: float = 0.0,
        regulation_code: str | None = None,
        jurisdiction: str | None = None,
    ) -> list[RetrievedChunk]:
        query_embedding = self.embedding_provider.embed_text(query)

        base_query = (
            self.db.query(RegulatoryChunk, RegulatoryDocument, Regulation)
            .join(RegulatoryDocument, RegulatoryChunk.document_id == RegulatoryDocument.id)
            .join(Regulation, RegulatoryChunk.regulation_id == Regulation.id)
            .filter(RegulatoryDocument.status != SourceStatus.UNVERIFIED)
        )
        if regulation_code:
            base_query = base_query.filter(Regulation.code == regulation_code)
        if jurisdiction:
            base_query = base_query.filter(Regulation.jurisdiction == jurisdiction)

        dialect = self.db.get_bind().dialect.name
        if dialect == "postgresql":
            results = self._search_postgres(base_query, query_embedding, top_k)
        else:
            results = self._search_python(base_query, query_embedding, top_k)

        return [r for r in results if r.score >= similarity_threshold]

    def _search_postgres(
        self, base_query: Query, query_embedding: list[float], top_k: int
    ) -> list[RetrievedChunk]:
        distance_expr = RegulatoryChunk.embedding.cosine_distance(query_embedding)
        rows = base_query.order_by(distance_expr).limit(top_k).all()
        return [self._to_retrieved_chunk(c, d, r, query_embedding) for c, d, r in rows]

    def _search_python(
        self, base_query: Query, query_embedding: list[float], top_k: int
    ) -> list[RetrievedChunk]:
        rows = base_query.all()
        scored = [self._to_retrieved_chunk(c, d, r, query_embedding) for c, d, r in rows]
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:top_k]

    @staticmethod
    def _to_retrieved_chunk(
        chunk: RegulatoryChunk,
        document: RegulatoryDocument,
        regulation: Regulation,
        query_embedding: list[float],
    ) -> RetrievedChunk:
        return RetrievedChunk(
            chunk_id=str(chunk.id),
            document_id=str(document.id),
            regulation_id=str(regulation.id),
            regulation_code=regulation.code,
            title=document.title,
            authority=document.authority,
            source_url=document.source_url,
            section=chunk.section,
            subsection=chunk.subsection,
            source_reference=chunk.source_reference,
            status=document.status.value,
            content=chunk.content,
            score=_cosine_similarity(list(chunk.embedding), query_embedding),
        )


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a)) or 1.0
    norm_b = math.sqrt(sum(y * y for y in b)) or 1.0
    return float(dot / (norm_a * norm_b))
