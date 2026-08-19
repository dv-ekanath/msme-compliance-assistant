from __future__ import annotations

import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import get_settings
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

# Single source of truth for the embedding width: Settings.embedding_dimension
# (backend/.env / .env.example). Both this column and every embedding
# provider validate against the same value -- see
# app/embeddings/local_provider.py and app/embeddings/mock_provider.py.
_EMBEDDING_DIM = get_settings().embedding_dimension

# Native pgvector column on Postgres (enables real ANN similarity search);
# falls back to a plain JSON array of floats on SQLite, where
# app/rag/retrieval.py computes cosine similarity in Python instead. This
# keeps the test suite fully offline (see backend/tests/conftest.py) while
# production uses the real pgvector path.
_EmbeddingType = Vector(_EMBEDDING_DIM).with_variant(JSON(), "sqlite")


class RegulatoryChunk(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A retrievable unit of regulatory text. One RegulatoryDocument is
    split into many of these by app/rag/chunking.py, each embedded via an
    EmbeddingProvider and stored here for pgvector similarity search.
    """

    __tablename__ = "regulatory_chunks"

    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("regulatory_documents.id", ondelete="CASCADE")
    )
    # Denormalized from the document for cheap filtering (regulation/
    # jurisdiction) without an extra join on every retrieval query.
    regulation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("regulations.id", ondelete="CASCADE"))

    section: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subsection: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text)
    source_page: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)

    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    embedding: Mapped[list[float]] = mapped_column(_EmbeddingType)
    chunk_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict)

    document: Mapped["RegulatoryDocument"] = relationship(back_populates="chunks")  # noqa: F821
    regulation: Mapped["Regulation"] = relationship()  # noqa: F821
