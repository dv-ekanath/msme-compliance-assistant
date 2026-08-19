from __future__ import annotations

from app.ocr.base import OCRProvider

_MOCK_PREFIX = b"MOCKTEXT:"

_DEFAULT_TEXT = (
    "GOVERNMENT OF INDIA\n"
    "GOODS AND SERVICES TAX REGISTRATION CERTIFICATE\n"
    "GSTIN: 22AAAAA0000A1Z5\n"
    "Legal Name: SAMPLE ENTERPRISES\n"
    "[MOCK OCR OUTPUT] No external OCR model was called.\n"
)


class MockOCRProvider(OCRProvider):
    """Deterministic, fully offline provider for local development and
    tests -- same role as `MockLLMProvider`/`MockEmbeddingProvider`.

    By default returns a canned block of text containing a valid sample
    GSTIN, so the document-extraction pipeline is testable/demoable
    end-to-end without a real OCR model. Recognizes one documented
    convention: if `image_bytes` starts with `MOCKTEXT:`, the remainder
    (UTF-8 decoded) is returned verbatim instead -- lets tests control
    exactly what "OCR produced" per call without needing a real image.
    """

    name = "mock"

    def extract_text(self, image_bytes: bytes) -> str:
        if image_bytes.startswith(_MOCK_PREFIX):
            return image_bytes[len(_MOCK_PREFIX) :].decode("utf-8")
        return _DEFAULT_TEXT
