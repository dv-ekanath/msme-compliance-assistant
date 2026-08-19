from __future__ import annotations

from app.ocr.extraction import extract_fields

GST_TEXT = """
GOVERNMENT OF INDIA
GOODS AND SERVICES TAX REGISTRATION CERTIFICATE
GSTIN: 22AAAAA0000A1Z5
Legal Name: SAMPLE ENTERPRISES
"""

UDYAM_TEXT = """
UDYAM REGISTRATION CERTIFICATE
Udyam Registration Number: UDYAM-MH-03-1234567
Name of Enterprise: SAMPLE ENTERPRISES
"""

PAN_TEXT = """
INCOME TAX DEPARTMENT
GOVT. OF INDIA
Permanent Account Number Card
ABCDE1234F
SAMPLE PERSON
"""


def test_extracts_gstin_from_gst_certificate():
    result = extract_fields(GST_TEXT, "gst_certificate")
    assert result.fields["gstin"] == "22AAAAA0000A1Z5"
    assert result.warning is None


def test_extracts_udyam_number_from_udyam_certificate():
    result = extract_fields(UDYAM_TEXT, "udyam_certificate")
    assert result.fields["udyam_number"] == "UDYAM-MH-03-1234567"
    assert result.warning is None


def test_extracts_pan_from_pan_card():
    result = extract_fields(PAN_TEXT, "pan_card")
    assert result.fields["pan"] == "ABCDE1234F"
    assert result.warning is None


def test_missing_expected_field_sets_warning():
    result = extract_fields("This is an unrelated block of text.", "gst_certificate")
    assert "gstin" not in result.fields
    assert result.warning is not None
    assert "gstin" in result.warning.lower()


def test_unrelated_text_extracts_nothing():
    result = extract_fields("Just some random notes about lunch plans.", "pan_card")
    assert result.fields == {}
    assert result.warning is not None


def test_whitespace_mangled_gstin_still_matches():
    mangled = "GSTIN : 22 AAAAA 0000 A1 Z5 issued today"
    result = extract_fields(mangled, "gst_certificate")
    assert result.fields["gstin"] == "22AAAAA0000A1Z5"


def test_lowercase_input_still_matches():
    result = extract_fields(GST_TEXT.lower(), "gst_certificate")
    assert result.fields["gstin"] == "22AAAAA0000A1Z5"


def test_pan_not_spuriously_extracted_from_gst_certificate():
    # A GSTIN's characters 3-12 are a valid PAN by construction; PAN
    # detection must stay gated to document_type == "pan_card".
    result = extract_fields(GST_TEXT, "gst_certificate")
    assert "pan" not in result.fields


def test_pan_extraction_only_runs_for_pan_card_document_type():
    result = extract_fields(PAN_TEXT, "gst_certificate")
    assert "pan" not in result.fields


def test_gstin_and_udyam_are_extracted_regardless_of_document_type():
    combined = GST_TEXT + UDYAM_TEXT
    result = extract_fields(combined, "pan_card")
    assert result.fields["gstin"] == "22AAAAA0000A1Z5"
    assert result.fields["udyam_number"] == "UDYAM-MH-03-1234567"
