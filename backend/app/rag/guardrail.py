from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain.enums import SourceStatus
from app.rag.retrieval import RetrievedChunk

# Tolerant of incidental whitespace inside the brackets (e.g. "[ S1 ]") --
# the prompt instructs the exact form "[S1]", but real LLM output (verified
# live against Groq's openai/gpt-oss-20b) doesn't always follow formatting
# instructions to the letter, and a stricter regex was silently discarding
# otherwise-valid citations, making genuinely grounded answers look
# ungrounded.
_CITATION_TAG_RE = re.compile(r"\[\s*S\s*(\d+)\s*\]")


@dataclass(frozen=True)
class Citation:
    source_id: str
    title: str
    authority: str
    section: str | None
    source_url: str
    relevance_score: float
    status: str


@dataclass(frozen=True)
class GuardrailResult:
    citations: list[Citation]
    grounded: bool
    requires_verification: bool
    confidence: str  # "high" | "medium" | "low"


def validate_citations(answer_text: str, retrieved: list[RetrievedChunk]) -> GuardrailResult:
    """Post-generation citation check.

    Maps every [Sn] tag actually present in the LLM's answer back to a
    retrieved evidence item. An answer is only "grounded" if it cites at
    least one real, retrieved source; it is only "high confidence" if
    every cited source has status=verified. Since nothing in the Phase 2
    seed corpus is status=verified yet (see backend/seed/regulatory_documents/README.md),
    requires_verification is expected to be True for essentially every
    answer right now -- that's the correct, honest state of this MVP, not
    a bug.

    This is deliberately a citation-*presence* check, not an NLI/fact-check
    model: it guarantees every citation traces to something actually
    retrieved, and it never lets an uncited or unevidenced answer present
    as authoritative -- but it cannot verify the LLM's prose is a faithful
    paraphrase of the cited chunk. That's an acceptable, disclosed
    limitation for this MVP (see requires_verification).
    """
    if not retrieved:
        return GuardrailResult(citations=[], grounded=False, requires_verification=True, confidence="low")

    cited_indices = {int(n) for n in _CITATION_TAG_RE.findall(answer_text)}
    valid_indices = sorted(i for i in cited_indices if 1 <= i <= len(retrieved))

    citations = [
        Citation(
            source_id=retrieved[i - 1].chunk_id,
            title=retrieved[i - 1].title,
            authority=retrieved[i - 1].authority,
            section=retrieved[i - 1].section,
            source_url=retrieved[i - 1].source_url,
            relevance_score=round(retrieved[i - 1].score, 4),
            status=retrieved[i - 1].status,
        )
        for i in valid_indices
    ]

    grounded = len(citations) > 0
    all_verified = grounded and all(c.status == SourceStatus.VERIFIED.value for c in citations)
    requires_verification = not all_verified

    if all_verified:
        confidence = "high"
    elif grounded:
        confidence = "medium"
    else:
        confidence = "low"

    return GuardrailResult(
        citations=citations,
        grounded=grounded,
        requires_verification=requires_verification,
        confidence=confidence,
    )
