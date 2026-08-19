from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.embeddings.base import EmbeddingProvider
from app.llm.base import LLMProvider
from app.models.business import Business
from app.rag.context import build_twin_context
from app.rag.guardrail import Citation, validate_citations
from app.rag.prompts import build_copilot_messages
from app.rag.retrieval import RetrievalService

INSUFFICIENT_EVIDENCE_ANSWER = (
    "I don't have sufficient regulatory evidence on file to answer this confidently. "
    "Please rephrase the question, or verify directly with the relevant government source "
    "and/or a compliance professional."
)


@dataclass(frozen=True)
class CopilotSource:
    """A retrieved item, whether or not the LLM ended up citing it --
    shown to the user as "what evidence was considered" transparency,
    separate from `citations` (what was actually used in the answer).
    """

    chunk_id: str
    title: str
    authority: str
    section: str | None
    source_url: str
    relevance_score: float
    status: str


@dataclass(frozen=True)
class CopilotAnswer:
    answer: str
    citations: list[Citation]
    retrieved_sources: list[CopilotSource]
    confidence: str
    grounded: bool
    requires_verification: bool


class ComplianceCopilotService:
    """Orchestrates: Digital Twin context -> retrieval -> grounded LLM
    prompt -> citation guardrail. The LLM never decides applicability --
    that's the Rules Engine's job (see app/services/compliance.py); the
    LLM only explains, grounded in retrieved evidence + twin facts.
    """

    def __init__(
        self, db: Session, llm_provider: LLMProvider, embedding_provider: EmbeddingProvider
    ) -> None:
        self.db = db
        self.llm_provider = llm_provider
        self.retrieval = RetrievalService(db, embedding_provider)

    async def ask(self, business: Business, question: str) -> CopilotAnswer:
        settings = get_settings()
        retrieved = self.retrieval.search(
            question,
            top_k=settings.copilot_top_k,
            similarity_threshold=settings.copilot_similarity_threshold,
        )

        retrieved_sources = [
            CopilotSource(
                chunk_id=r.chunk_id,
                title=r.title,
                authority=r.authority,
                section=r.section,
                source_url=r.source_url,
                relevance_score=round(r.score, 4),
                status=r.status,
            )
            for r in retrieved
        ]

        if not retrieved:
            # No point calling the LLM with zero grounding -- that would
            # only invite it to answer from its own uncited, unverifiable
            # knowledge, which this system must never present as evidence.
            return CopilotAnswer(
                answer=INSUFFICIENT_EVIDENCE_ANSWER,
                citations=[],
                retrieved_sources=[],
                confidence="low",
                grounded=False,
                requires_verification=True,
            )

        twin_context = build_twin_context(self.db, business)
        messages = build_copilot_messages(question=question, twin_context=twin_context, retrieved=retrieved)
        response = await self.llm_provider.complete(messages)

        guardrail = validate_citations(response.content, retrieved)

        return CopilotAnswer(
            answer=response.content,
            citations=guardrail.citations,
            retrieved_sources=retrieved_sources,
            confidence=guardrail.confidence,
            grounded=guardrail.grounded,
            requires_verification=guardrail.requires_verification,
        )
