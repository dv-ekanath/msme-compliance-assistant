from __future__ import annotations

from datetime import datetime, timezone

from app.domain.enums import DocumentType, SourceStatus
from app.models.regulation import Regulation
from app.models.regulatory_chunk import RegulatoryChunk
from app.models.regulatory_document import RegulatoryDocument
from app.rag.retrieval import RetrievalService

# MockEmbeddingProvider is deterministic and hash-based (not semantically
# meaningful): the reliable way to test retrieval logic with it is to query
# using a chunk's *exact known content* (cosine similarity ~1.0 against
# itself) rather than a paraphrase. Filters/threshold/status-exclusion are
# tested against that same reliable signal.


def test_search_returns_the_matching_chunk_near_the_top(db_session, mock_embedding_provider):
    service = RetrievalService(db_session, mock_embedding_provider)
    known_chunk = db_session.query(RegulatoryChunk).join(Regulation).filter(Regulation.code == "GST").first()
    assert known_chunk is not None

    results = service.search(known_chunk.content, top_k=5)

    assert any(r.chunk_id == str(known_chunk.id) for r in results)
    top_match = next(r for r in results if r.chunk_id == str(known_chunk.id))
    assert top_match.score > 0.99  # querying with its own content -> near-identical vector


def test_search_includes_source_metadata(db_session, mock_embedding_provider):
    service = RetrievalService(db_session, mock_embedding_provider)
    known_chunk = db_session.query(RegulatoryChunk).join(Regulation).filter(Regulation.code == "EPF").first()

    results = service.search(known_chunk.content, top_k=3)
    match = next(r for r in results if r.chunk_id == str(known_chunk.id))

    assert match.regulation_code == "EPF"
    assert match.authority == "Employees' Provident Fund Organisation (EPFO)"
    assert match.source_url.startswith("https://")
    assert match.status == "demo"


def test_top_k_limits_result_count(db_session, mock_embedding_provider):
    service = RetrievalService(db_session, mock_embedding_provider)
    results = service.search("compliance obligations for a business", top_k=2)
    assert len(results) <= 2


def test_similarity_threshold_filters_low_relevance(db_session, mock_embedding_provider):
    service = RetrievalService(db_session, mock_embedding_provider)
    # Mock embeddings of unrelated text are effectively uncorrelated
    # (near-zero cosine similarity on average in high dimensions), so an
    # unreasonably high threshold should filter everything out.
    results = service.search("completely unrelated filler query text", top_k=10, similarity_threshold=0.999)
    assert results == []


def test_regulation_code_filter_restricts_results(db_session, mock_embedding_provider):
    service = RetrievalService(db_session, mock_embedding_provider)
    gst_chunk = db_session.query(RegulatoryChunk).join(Regulation).filter(Regulation.code == "GST").first()

    results = service.search(gst_chunk.content, top_k=10, regulation_code="EPF")

    assert all(r.regulation_code == "EPF" for r in results)
    assert not any(r.chunk_id == str(gst_chunk.id) for r in results)


def test_jurisdiction_filter_restricts_results(db_session, mock_embedding_provider):
    service = RetrievalService(db_session, mock_embedding_provider)
    results = service.search("state administered registration", top_k=10, jurisdiction="IN-STATE")
    assert results  # Shops & Establishment / Professional Tax are IN-STATE
    assert all(r.regulation_code in {"SHOPS_ESTABLISHMENT", "PROFESSIONAL_TAX"} for r in results)


def test_unverified_status_is_never_returned(db_session, mock_embedding_provider):
    regulation = db_session.query(Regulation).filter(Regulation.code == "GST").first()
    unverified_doc = RegulatoryDocument(
        code="GST-UNVERIFIED-TEST",
        regulation_id=regulation.id,
        title="Unreviewed draft excerpt",
        authority="Draft",
        jurisdiction="IN-Central",
        source_url="https://example.gov.in/draft",
        document_type=DocumentType.OTHER,
        version="draft",
        retrieved_at=datetime.now(timezone.utc),
        content_hash="deadbeef",
        status=SourceStatus.UNVERIFIED,
    )
    db_session.add(unverified_doc)
    db_session.flush()

    secret_content = "This unverified draft claims a fictitious 99% GST rate."
    db_session.add(
        RegulatoryChunk(
            document_id=unverified_doc.id,
            regulation_id=regulation.id,
            section=None,
            content=secret_content,
            chunk_index=0,
            embedding=mock_embedding_provider.embed_text(secret_content),
            chunk_metadata={},
        )
    )
    db_session.commit()

    service = RetrievalService(db_session, mock_embedding_provider)
    results = service.search(secret_content, top_k=5)

    assert all(r.status != "unverified" for r in results)
    assert not any("99% GST rate" in r.content for r in results)
