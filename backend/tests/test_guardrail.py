from __future__ import annotations

from app.rag.guardrail import validate_citations
from app.rag.retrieval import RetrievedChunk


def _chunk(**overrides) -> RetrievedChunk:
    defaults = dict(
        chunk_id="chunk-1",
        document_id="doc-1",
        regulation_id="reg-1",
        regulation_code="GST",
        title="GST Registration",
        authority="CBIC",
        source_url="https://www.gst.gov.in/",
        section="Registration Threshold",
        subsection=None,
        source_reference="CGST Act 2017, Section 22",
        status="demo",
        content="Businesses must register once turnover crosses the threshold.",
        score=0.87,
    )
    defaults.update(overrides)
    return RetrievedChunk(**defaults)


def test_supported_claim_passes_and_is_cited():
    retrieved = [_chunk()]
    result = validate_citations("You must register for GST above the threshold [S1].", retrieved)

    assert result.grounded is True
    assert len(result.citations) == 1
    assert result.citations[0].source_id == "chunk-1"
    assert result.citations[0].section == "Registration Threshold"


def test_unsupported_claim_with_no_citation_tag_is_flagged():
    retrieved = [_chunk()]
    result = validate_citations("You must register for GST above the threshold.", retrieved)

    assert result.grounded is False
    assert result.citations == []
    assert result.requires_verification is True
    assert result.confidence == "low"


def test_out_of_range_citation_tag_is_ignored():
    retrieved = [_chunk()]
    result = validate_citations("This references a source that doesn't exist [S7].", retrieved)

    assert result.grounded is False
    assert result.citations == []


def test_missing_evidence_causes_verification_warning():
    result = validate_citations("Some answer text with no evidence available.", [])

    assert result.grounded is False
    assert result.requires_verification is True
    assert result.confidence == "low"
    assert result.citations == []


def test_demo_status_source_is_medium_confidence_and_requires_verification():
    retrieved = [_chunk(status="demo")]
    result = validate_citations("Explanation grounded in evidence [S1].", retrieved)

    assert result.grounded is True
    assert result.confidence == "medium"
    assert result.requires_verification is True


def test_verified_status_source_is_high_confidence_and_does_not_require_verification():
    retrieved = [_chunk(status="verified")]
    result = validate_citations("Explanation grounded in evidence [S1].", retrieved)

    assert result.grounded is True
    assert result.confidence == "high"
    assert result.requires_verification is False


def test_mixed_verified_and_demo_citations_requires_verification():
    retrieved = [_chunk(chunk_id="c1", status="verified"), _chunk(chunk_id="c2", status="demo")]
    result = validate_citations("Explanation grounded in evidence [S1][S2].", retrieved)

    assert result.grounded is True
    assert len(result.citations) == 2
    # any non-verified citation caps confidence and forces verification
    assert result.confidence == "medium"
    assert result.requires_verification is True


def test_multiple_valid_citations_are_all_captured_in_order():
    retrieved = [_chunk(chunk_id="c1"), _chunk(chunk_id="c2"), _chunk(chunk_id="c3")]
    result = validate_citations("First point [S1]. Second point [S3].", retrieved)

    assert [c.source_id for c in result.citations] == ["c1", "c3"]
