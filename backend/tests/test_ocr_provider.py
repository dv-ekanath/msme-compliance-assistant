from __future__ import annotations

from app.ocr.mock_provider import MockOCRProvider


def test_default_mock_text_contains_a_valid_gstin():
    provider = MockOCRProvider()
    text = provider.extract_text(b"irrelevant-bytes")
    assert "22AAAAA0000A1Z5" in text


def test_mocktext_prefix_returns_verbatim_remainder():
    provider = MockOCRProvider()
    text = provider.extract_text(b"MOCKTEXT:hello world")
    assert text == "hello world"


def test_extract_text_is_deterministic():
    provider = MockOCRProvider()
    a = provider.extract_text(b"same-input")
    b = provider.extract_text(b"same-input")
    assert a == b
