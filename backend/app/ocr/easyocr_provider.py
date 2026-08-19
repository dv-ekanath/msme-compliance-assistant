from __future__ import annotations

from app.ocr.base import OCRProvider


class EasyOCRProvider(OCRProvider):
    """EasyOCR running on-box -- no API key, no external credits, real
    text recognition. This is the default provider (OCR_PROVIDER=easyocr).

    `easyocr` is imported lazily inside __init__ (not at module import
    time), matching `app.embeddings.local_provider.LocalEmbeddingProvider`'s
    pattern: importing this module is always safe; only instantiating it
    requires the package to be installed.

    `verbose=False` is not cosmetic: EasyOCR's default progress bar prints
    a Unicode block character that crashes with UnicodeEncodeError on
    Windows' default (cp1252) console codepage during the first-run model
    download -- reproduced during development. Passing verbose=False
    avoids that code path entirely, not just the console noise.
    """

    name = "easyocr"

    def __init__(self, languages: list[str]) -> None:
        try:
            import easyocr
        except ImportError as exc:
            raise RuntimeError(
                "The 'easyocr' package is not installed. It's a listed "
                "dependency in requirements.txt -- run `pip install -r "
                "requirements.txt`, or set OCR_PROVIDER=mock for offline dev."
            ) from exc

        self._reader = easyocr.Reader(languages, gpu=False, verbose=False)

    def extract_text(self, image_bytes: bytes) -> str:
        lines: list[str] = self._reader.readtext(image_bytes, detail=0, paragraph=True)
        return "\n".join(lines)
