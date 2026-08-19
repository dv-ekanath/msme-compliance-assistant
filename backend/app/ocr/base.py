from __future__ import annotations

from abc import ABC, abstractmethod


class OCRProvider(ABC):
    """Interface every OCR backend must implement.

    Mirrors `app.llm.base.LLMProvider` / `app.embeddings.base.EmbeddingProvider`:
    the rest of the application (the document-extraction route) depends
    only on this interface, never on a specific OCR library, so the
    backend can be swapped via the OCR_PROVIDER env var. See
    `app.ocr.factory.get_ocr_provider`.
    """

    name: str = "base"

    @abstractmethod
    def extract_text(self, image_bytes: bytes) -> str:
        """Recognize and return all text found in an image."""
