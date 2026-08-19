"""add regulatory_documents and regulatory_chunks tables (RAG corpus)

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-19

Adds the Phase 2 knowledge-base tables: RegulatoryDocument (one ingested
source per regulation) and RegulatoryChunk (retrievable, embedded units of
that document's text). `embedding` uses pgvector's native `vector(n)` type
-- width read from Settings.embedding_dimension, the single source of
truth also used by the embedding providers (app/embeddings/).

No ANN index (ivfflat/hnsw) is created here: the demo corpus is a handful
of chunks, small enough that pgvector's exact `<=>` cosine-distance search
is fast without one. Add an ivfflat index in a later migration if/when the
corpus grows large enough to need approximate search.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

from app.core.config import get_settings
from app.domain.enums import DocumentType, SourceStatus

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

_EMBEDDING_DIM = get_settings().embedding_dimension


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "regulatory_documents",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column(
            "regulation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("regulations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("authority", sa.String(255), nullable=False),
        sa.Column("jurisdiction", sa.String(50), nullable=False),
        sa.Column("source_url", sa.String(500), nullable=False),
        sa.Column("document_type", sa.Enum(DocumentType, native_enum=False, length=20), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("version", sa.String(255), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.Enum(SourceStatus, native_enum=False, length=20), nullable=False),
        sa.UniqueConstraint("code", name="uq_regulatory_documents_code"),
    )
    op.create_index("ix_regulatory_documents_code", "regulatory_documents", ["code"])

    op.create_table(
        "regulatory_chunks",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "document_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("regulatory_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "regulation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("regulations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("section", sa.String(255), nullable=True),
        sa.Column("subsection", sa.String(255), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source_page", sa.String(50), nullable=True),
        sa.Column("source_reference", sa.String(255), nullable=True),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("embedding", Vector(_EMBEDDING_DIM), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
    )
    op.create_index("ix_regulatory_chunks_document_id", "regulatory_chunks", ["document_id"])
    op.create_index("ix_regulatory_chunks_regulation_id", "regulatory_chunks", ["regulation_id"])


def downgrade() -> None:
    op.drop_index("ix_regulatory_chunks_regulation_id", table_name="regulatory_chunks")
    op.drop_index("ix_regulatory_chunks_document_id", table_name="regulatory_chunks")
    op.drop_table("regulatory_chunks")

    op.drop_index("ix_regulatory_documents_code", table_name="regulatory_documents")
    op.drop_table("regulatory_documents")
