"""Loads backend/seed/regulatory_documents/*.json: chunks each document
and embeds every chunk via the configured EmbeddingProvider, then upserts
regulatory_documents + regulatory_chunks.

Run from the backend/ directory (after `python -m seed.load_regulations`):
    python -m seed.load_regulatory_documents

Idempotent: upserts documents by `code` and always replaces that
document's chunks -- safe to re-run after editing a seed file.
"""

from __future__ import annotations

from app.core.database import SessionLocal
from app.embeddings.factory import get_embedding_provider
from app.rag.ingestion import ingest_documents, load_document_entries


def main() -> None:
    db = SessionLocal()
    try:
        entries = load_document_entries()
        provider = get_embedding_provider()
        print(f"Embedding with provider={provider.name!r} (dimension={provider.dimension})...")
        result = ingest_documents(db, provider, entries)
        print(f"Ingested {result['documents']} document(s), {result['chunks']} chunk(s).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
