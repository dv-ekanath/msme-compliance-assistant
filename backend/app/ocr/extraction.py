from __future__ import annotations

import re
from dataclasses import dataclass, field

# Deterministic pattern-matching over well-known Indian government ID
# formats -- CLAUDE.md rule 4 (deterministic core, LLM for explanation
# only). No LLM/ML decides what gets extracted here.
#
# GSTIN (15 chars): 2-digit state code + 10-char PAN + 1 alphanumeric
# entity code (a PAN can hold multiple GSTINs per state, so this isn't
# digit-only) + fixed 'Z' + 1 alphanumeric checksum.
_GSTIN_RE = re.compile(r"[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]")

# PAN (10 chars): 5 letters + 4 digits + 1 letter.
_PAN_RE = re.compile(r"[A-Z]{5}[0-9]{4}[A-Z]")

# Udyam Registration Number: UDYAM-<2-letter state code>-<2 digits>-<7 digits>.
_UDYAM_RE = re.compile(r"UDYAM-[A-Z]{2}-[0-9]{2}-[0-9]{7}")

_EXPECTED_FIELD_BY_DOCUMENT_TYPE = {
    "gst_certificate": "gstin",
    "udyam_certificate": "udyam_number",
    "pan_card": "pan",
}


@dataclass(frozen=True)
class FieldExtractionResult:
    fields: dict[str, str] = field(default_factory=dict)
    warning: str | None = None


def extract_fields(raw_text: str, document_type: str) -> FieldExtractionResult:
    """Pure, deterministic extraction from OCR-recognized text -- no
    image/OCR involved, fully unit-testable with plain text fixtures.

    OCR line-wrapping/kerning can insert spurious whitespace inside a
    token, but these IDs never legitimately contain whitespace -- so
    matching is done against the whitespace-stripped, upper-cased text
    rather than trying to build a whitespace-tolerant regex.

    PAN detection is gated to document_type == "pan_card": a GSTIN's
    characters 3-12 are a valid PAN by construction, so running the PAN
    regex unconditionally would spuriously "detect" a PAN on every GST
    certificate.
    """
    compact = re.sub(r"\s+", "", raw_text.upper())

    fields: dict[str, str] = {}
    if match := _GSTIN_RE.search(compact):
        fields["gstin"] = match.group()
    if match := _UDYAM_RE.search(compact):
        fields["udyam_number"] = match.group()
    if document_type == "pan_card":
        if match := _PAN_RE.search(compact):
            fields["pan"] = match.group()

    expected_field = _EXPECTED_FIELD_BY_DOCUMENT_TYPE.get(document_type)
    warning = None
    if expected_field is not None and expected_field not in fields:
        warning = (
            f"Could not confidently detect a {expected_field.replace('_', ' ')} in the "
            "uploaded document. Please check the image quality or enter it manually."
        )

    return FieldExtractionResult(fields=fields, warning=warning)
