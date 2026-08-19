from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.domain.enums import DocumentType, SourceStatus
from app.embeddings.base import EmbeddingProvider
from app.models.regulation import Regulation
from app.models.regulatory_chunk import RegulatoryChunk
from app.models.regulatory_document import RegulatoryDocument
from app.rag.chunking import SectionInput, chunk_document

DOCUMENTS_DIR = Path(__file__).resolve().parents[2] / "seed" / "regulatory_documents"
REQUIRED_FIELDS = {
    "code",
    "regulation_code",
    "title",
    "authority",
    "jurisdiction",
    "source_url",
    "document_type",
    "version",
    "status",
    "sections",
}


def load_document_entries() -> list[dict]:
    entries = []
    for path in sorted(DOCUMENTS_DIR.glob("*.json")):
        if path.name.startswith("_") or path.name == "schema.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        missing = REQUIRED_FIELDS - data.keys()
        if missing:
            raise ValueError(f"{path.name} is missing required fields: {sorted(missing)}")
        entries.append(data)
    return entries


def _content_hash(sections: list[dict]) -> str:
    joined = "\n".join(s["content"] for s in sections)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def ingest_documents(
    db: Session, embedding_provider: EmbeddingProvider, entries: list[dict]
) -> dict[str, int]:
    """Idempotent: upserts RegulatoryDocument by `code`; always replaces
    that document's chunks (delete + re-chunk + re-embed), so editing a
    seed file's sections/content and re-running reflects the change
    instead of accumulating stale rows.
    """
    documents_upserted = 0
    chunks_written = 0

    for entry in entries:
        regulation = (
            db.query(Regulation).filter(Regulation.code == entry["regulation_code"]).one_or_none()
        )
        if regulation is None:
            raise ValueError(
                f"{entry['code']} references regulation_code={entry['regulation_code']!r}, "
                "which is not seeded. Run `python -m seed.load_regulations` first."
            )

        document = (
            db.query(RegulatoryDocument).filter(RegulatoryDocument.code == entry["code"]).one_or_none()
        )
        if document is None:
            document = RegulatoryDocument(code=entry["code"])
            db.add(document)

        document.regulation_id = regulation.id
        document.title = entry["title"]
        document.authority = entry["authority"]
        document.jurisdiction = entry["jurisdiction"]
        document.source_url = entry["source_url"]
        document.document_type = DocumentType(entry["document_type"])
        document.effective_date = (
            date.fromisoformat(entry["effective_date"]) if entry.get("effective_date") else None
        )
        document.version = entry["version"]
        document.status = SourceStatus(entry["status"])
        document.content_hash = _content_hash(entry["sections"])
        document.retrieved_at = datetime.now(timezone.utc)
        db.flush()  # populate document.id before chunks reference it

        db.query(RegulatoryChunk).filter(RegulatoryChunk.document_id == document.id).delete()

        sections = [
            SectionInput(
                section=s.get("section"),
                subsection=s.get("subsection"),
                source_reference=s.get("source_reference"),
                source_page=s.get("source_page"),
                content=s["content"],
            )
            for s in entry["sections"]
        ]
        chunk_records = chunk_document(sections)

        if chunk_records:
            embeddings = embedding_provider.embed_documents([c.content for c in chunk_records])
            for record, embedding in zip(chunk_records, embeddings):
                db.add(
                    RegulatoryChunk(
                        document_id=document.id,
                        regulation_id=regulation.id,
                        section=record.section,
                        subsection=record.subsection,
                        content=record.content,
                        source_page=record.source_page,
                        source_reference=record.source_reference,
                        chunk_index=record.chunk_index,
                        embedding=embedding,
                        chunk_metadata=record.metadata,
                    )
                )
            chunks_written += len(chunk_records)

        documents_upserted += 1

    db.commit()
    return {"documents": documents_upserted, "chunks": chunks_written}
