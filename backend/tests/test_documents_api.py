from __future__ import annotations

GST_TEXT = b"MOCKTEXT:GSTIN: 22AAAAA0000A1Z5\nLegal Name: SAMPLE ENTERPRISES"
UDYAM_TEXT = b"MOCKTEXT:Udyam Registration Number: UDYAM-MH-03-1234567"
PAN_TEXT = b"MOCKTEXT:Permanent Account Number ABCDE1234F"
UNRELATED_TEXT = b"MOCKTEXT:Just some random notes."


def _upload(client, document_type: str, content: bytes, content_type: str = "image/jpeg"):
    return client.post(
        "/api/v1/documents/extract",
        data={"document_type": document_type},
        files={"file": ("document.jpg", content, content_type)},
    )


def test_extract_gst_certificate_returns_gstin(client):
    resp = _upload(client, "gst_certificate", GST_TEXT)
    assert resp.status_code == 200
    body = resp.json()
    assert body["fields"]["gstin"] == "22AAAAA0000A1Z5"
    assert body["warning"] is None


def test_extract_udyam_certificate_returns_udyam_number(client):
    resp = _upload(client, "udyam_certificate", UDYAM_TEXT)
    assert resp.status_code == 200
    body = resp.json()
    assert body["fields"]["udyam_number"] == "UDYAM-MH-03-1234567"
    assert body["warning"] is None


def test_extract_pan_card_returns_pan(client):
    resp = _upload(client, "pan_card", PAN_TEXT)
    assert resp.status_code == 200
    body = resp.json()
    assert body["fields"]["pan"] == "ABCDE1234F"
    assert body["warning"] is None


def test_extract_missing_expected_field_returns_warning(client):
    resp = _upload(client, "gst_certificate", UNRELATED_TEXT)
    assert resp.status_code == 200
    body = resp.json()
    assert "gstin" not in body["fields"]
    assert body["warning"] is not None


def test_extract_rejects_unsupported_content_type(client):
    resp = _upload(client, "gst_certificate", GST_TEXT, content_type="application/pdf")
    assert resp.status_code == 422


def test_extract_rejects_invalid_document_type(client):
    resp = _upload(client, "passport", GST_TEXT)
    assert resp.status_code == 422


def test_extract_default_mock_ocr_output_without_prefix(client):
    # No MOCKTEXT: prefix -> falls back to MockOCRProvider's canned text,
    # which contains a valid sample GSTIN.
    resp = _upload(client, "gst_certificate", b"some-real-looking-jpeg-bytes")
    assert resp.status_code == 200
    assert resp.json()["fields"]["gstin"] == "22AAAAA0000A1Z5"
