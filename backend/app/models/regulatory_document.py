from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import DocumentType, SourceStatus
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RegulatoryDocument(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """One ingested source document backing a Regulation (e.g. the Act
    itself, a notification, an FAQ). Chunked into RegulatoryChunk rows for
    retrieval -- see app/rag/chunking.py and app/rag/ingestion.py.
    """

    __tablename__ = "regulatory_documents"

    code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    regulation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("regulations.id", ondelete="CASCADE"))

    title: Mapped[str] = mapped_column(String(255))
    authority: Mapped[str] = mapped_column(String(255))
    jurisdiction: Mapped[str] = mapped_column(String(50))
    source_url: Mapped[str] = mapped_column(String(500))
    document_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType, native_enum=False, length=20))
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    version: Mapped[str] = mapped_column(String(255))

    # When this document's content was last (re)ingested, and a hash of
    # that content -- so a future watchdog (Phase 3) can detect changes
    # without re-embedding unchanged text.
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    content_hash: Mapped[str] = mapped_column(String(64))

    status: Mapped[SourceStatus] = mapped_column(Enum(SourceStatus, native_enum=False, length=20))

    regulation: Mapped["Regulation"] = relationship()  # noqa: F821
    chunks: Mapped[list["RegulatoryChunk"]] = relationship(  # noqa: F821
        back_populates="document", cascade="all, delete-orphan"
    )
