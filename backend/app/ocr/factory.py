from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.ocr.base import OCRProvider
from app.ocr.mock_provider import MockOCRProvider


@lru_cache
def get_ocr_provider() -> OCRProvider:
    """Single entry point the rest of the app should use to get an OCR
    backend. Selection is controlled by OCR_PROVIDER so no calling code
    needs to know (or import) easyocr directly.
    """
    settings = get_settings()

    if settings.ocr_provider == "mock":
        return MockOCRProvider()

    if settings.ocr_provider == "easyocr":
        from app.ocr.easyocr_provider import EasyOCRProvider

        return EasyOCRProvider(languages=settings.ocr_languages_list)

    raise ValueError(f"Unknown OCR_PROVIDER: {settings.ocr_provider!r} (expected 'mock' or 'easyocr')")
