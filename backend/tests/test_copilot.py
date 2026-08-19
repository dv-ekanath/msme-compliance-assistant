from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from app.core.config import get_settings
from app.domain.enums import (
    BusinessLegalType,
    ObligationApplicability,
    ObligationType,
    SectorType,
    TurnoverBand,
)
from app.llm.base import LLMMessage, LLMProvider, LLMResponse
from app.models.business import Business
from app.models.obligation import Obligation
from app.models.regulation import Regulation
from app.rag.copilot import INSUFFICIENT_EVIDENCE_ANSWER, ComplianceCopilotService


class SpyLLMProvider(LLMProvider):
    """Records exactly what the Copilot sends it, without needing a real
    model -- lets tests assert on prompt contents without parsing a
    mock-specific canned-answer format.
    """

    name = "spy"

    def __init__(self, canned_answer: str = "Grounded explanation [S1]."):
        self.received_messages: list[LLMMessage] | None = None
        self.canned_answer = canned_answer
        self.call_count = 0

    async def complete(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        self.call_count += 1
        self.received_messages = messages
        return LLMResponse(content=self.canned_answer, provider=self.name, model="spy-1")

    async def health_check(self) -> bool:
        return True


def _allow_all_evidence(monkeypatch) -> None:
    """MockEmbeddingProvider is hash-based, not semantic (see its
    docstring): a natural-language question has ~zero expected cosine
    similarity to mock-embedded corpus content, so the real,
    semantically-tuned default threshold (COPILOT_SIMILARITY_THRESHOLD)
    would spuriously filter everything out here. These tests are about
    prompt plumbing / provider wiring, not retrieval ranking quality
    (that's covered separately in test_retrieval.py using
    exact-content queries against the mock embedder) -- so we relax the
    threshold to isolate what's actually under test.
    """
    monkeypatch.setattr(get_settings(), "copilot_similarity_threshold", -1.0)


def _make_business(db_session) -> Business:
    business = Business(
        name="Ganga Textiles",
        sector=SectorType.TRADING,
        state="Maharashtra",
        registration_type=BusinessLegalType.PROPRIETORSHIP,
        turnover_band=TurnoverBand.CR5_50CR,
        employee_count=45,
    )
    db_session.add(business)
    db_session.commit()
    db_session.refresh(business)
    return business


def test_question_and_evidence_reach_the_llm_provider(db_session, mock_embedding_provider, monkeypatch):
    _allow_all_evidence(monkeypatch)
    business = _make_business(db_session)
    spy = SpyLLMProvider()
    service = ComplianceCopilotService(db_session, spy, mock_embedding_provider)

    asyncio.run(service.ask(business, "What is the GST registration threshold?"))

    assert spy.call_count == 1
    user_message = next(m for m in spy.received_messages if m.role == "user")
    assert "QUESTION: What is the GST registration threshold?" in user_message.content
    assert "EVIDENCE:" in user_message.content
    assert "[S1]" in user_message.content


def test_digital_twin_context_is_included_in_prompt(db_session, mock_embedding_provider, monkeypatch):
    _allow_all_evidence(monkeypatch)
    business = _make_business(db_session)
    spy = SpyLLMProvider()
    service = ComplianceCopilotService(db_session, spy, mock_embedding_provider)

    asyncio.run(service.ask(business, "What compliances apply to my business?"))

    user_message = next(m for m in spy.received_messages if m.role == "user")
    assert "BUSINESS CONTEXT:" in user_message.content
    assert "Ganga Textiles" in user_message.content
    assert "Employees: 45" in user_message.content
    assert "Maharashtra" in user_message.content


def test_applicable_obligations_from_rules_engine_appear_in_context(
    db_session, mock_embedding_provider, monkeypatch
):
    _allow_all_evidence(monkeypatch)
    business = _make_business(db_session)
    regulation = db_session.query(Regulation).filter(Regulation.code == "GST").first()
    db_session.add(
        Obligation(
            business_id=business.id,
            regulation_id=regulation.id,
            rule_id="gst_registration_threshold",
            obligation_type=ObligationType.REGISTRATION,
            title="GST Registration",
            reason="Turnover exceeds the threshold.",
            applicability=ObligationApplicability.APPLICABLE,
            last_evaluated_at=datetime.now(timezone.utc),
        )
    )
    db_session.commit()

    spy = SpyLLMProvider()
    service = ComplianceCopilotService(db_session, spy, mock_embedding_provider)
    asyncio.run(service.ask(business, "Why does GST apply to me?"))

    user_message = next(m for m in spy.received_messages if m.role == "user")
    assert "determined APPLICABLE by the deterministic Rules Engine" in user_message.content
    assert "GST Registration" in user_message.content


def test_mock_llm_produces_a_grounded_answer_without_any_api_key(
    db_session, mock_embedding_provider, mock_llm_provider, monkeypatch
):
    _allow_all_evidence(monkeypatch)
    business = _make_business(db_session)
    service = ComplianceCopilotService(db_session, mock_llm_provider, mock_embedding_provider)

    result = asyncio.run(service.ask(business, "What is the GST registration threshold?"))

    assert result.grounded is True
    assert len(result.citations) >= 1
    assert result.retrieved_sources
    assert "[MOCK LLM RESPONSE]" in result.answer


def test_no_retrieved_evidence_short_circuits_without_calling_llm(db_session, mock_embedding_provider, monkeypatch):
    business = _make_business(db_session)
    spy = SpyLLMProvider()
    service = ComplianceCopilotService(db_session, spy, mock_embedding_provider)

    # Force zero retrieval results deterministically: cosine similarity
    # can never exceed 1.0, so this threshold guarantees an empty match set
    # regardless of the embedding scheme.
    monkeypatch.setattr(get_settings(), "copilot_similarity_threshold", 1.1)

    result = asyncio.run(service.ask(business, "Some question with no matching evidence"))

    assert spy.call_count == 0
    assert result.answer == INSUFFICIENT_EVIDENCE_ANSWER
    assert result.grounded is False
    assert result.requires_verification is True
    assert result.citations == []
    assert result.retrieved_sources == []
