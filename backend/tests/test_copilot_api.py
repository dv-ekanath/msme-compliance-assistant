from __future__ import annotations

from app.core.config import get_settings
from tests.test_business_api import business_payload


def _allow_all_evidence(monkeypatch) -> None:
    """See tests/test_copilot.py::_allow_all_evidence -- the `client`
    fixture's mock embedding provider is hash-based, not semantic, so a
    natural-language question needs a relaxed threshold to reliably match
    mock-embedded corpus content in tests.
    """
    monkeypatch.setattr(get_settings(), "copilot_similarity_threshold", -1.0)


def test_copilot_ask_normal_grounded_response(client, monkeypatch):
    _allow_all_evidence(monkeypatch)
    business = client.post("/api/v1/business", json=business_payload(sector="trading")).json()

    resp = client.post(
        f"/api/v1/copilot/ask/{business['id']}",
        json={"question": "What is the GST registration threshold?"},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {
        "answer",
        "citations",
        "retrieved_sources",
        "confidence",
        "grounded",
        "requires_verification",
    }
    assert body["grounded"] is True
    assert len(body["citations"]) >= 1
    assert body["retrieved_sources"]
    citation = body["citations"][0]
    assert set(citation.keys()) == {
        "source_id",
        "title",
        "authority",
        "section",
        "source_url",
        "relevance_score",
        "status",
    }
    assert citation["source_url"].startswith("https://")
    # Phase 2's corpus is entirely demo-status -- verification must always
    # be flagged until real verified content is ingested.
    assert body["requires_verification"] is True


def test_copilot_ask_invalid_business_returns_404(client):
    resp = client.post(
        "/api/v1/copilot/ask/00000000-0000-0000-0000-000000000000",
        json={"question": "What compliances apply to my business?"},
    )
    assert resp.status_code == 404


def test_copilot_ask_empty_question_returns_422(client):
    business = client.post("/api/v1/business", json=business_payload()).json()
    resp = client.post(f"/api/v1/copilot/ask/{business['id']}", json={"question": "   "})
    assert resp.status_code == 422


def test_copilot_ask_missing_question_field_returns_422(client):
    business = client.post("/api/v1/business", json=business_payload()).json()
    resp = client.post(f"/api/v1/copilot/ask/{business['id']}", json={})
    assert resp.status_code == 422


def test_copilot_response_does_not_leak_internal_prompt_or_system_instructions(client):
    business = client.post("/api/v1/business", json=business_payload()).json()
    resp = client.post(
        f"/api/v1/copilot/ask/{business['id']}",
        json={"question": "What compliances apply to my business?"},
    )
    raw = resp.text
    assert "Ground rules" not in raw
    assert "You are the Compliance Copilot" not in raw


def test_copilot_ask_uses_mock_provider_with_no_api_key_configured(client, monkeypatch):
    """The client fixture never sets ANTHROPIC_API_KEY -- this proves the
    whole request path works with LLM_PROVIDER effectively mocked out via
    dependency overrides, matching the project's no-API-key-required rule.
    """
    _allow_all_evidence(monkeypatch)
    business = client.post("/api/v1/business", json=business_payload()).json()
    resp = client.post(
        f"/api/v1/copilot/ask/{business['id']}",
        json={"question": "When is my next GST filing due?"},
    )
    assert resp.status_code == 200
    assert "[MOCK LLM RESPONSE]" in resp.json()["answer"]
