from __future__ import annotations

from tests.test_business_api import business_payload


def _make_applicable_filing_obligation(client) -> tuple[str, str]:
    """Returns (business_id, obligation_id) for a GST periodic filing
    obligation that's genuinely APPLICABLE -- mirrors
    test_compliance_api.py's test_registering_gst_flips_registration_and_filing_obligations
    setup (register GST, then the periodic filing rule flips applicable).
    """
    business = client.post(
        "/api/v1/business",
        json=business_payload(turnover_band="40l_5cr", employee_count=5, sector="trading"),
    ).json()
    client.post(f"/api/v1/compliance/evaluate/{business['id']}")
    client.post("/api/v1/registrations", json={"business_id": business["id"], "type": "gst"})
    client.post(f"/api/v1/compliance/evaluate/{business['id']}")

    obligations = client.get("/api/v1/obligations", params={"business_id": business["id"]}).json()
    filing_obligation = next(o for o in obligations if o["rule_id"] == "gst_periodic_filing")
    assert filing_obligation["applicability"] == "applicable"
    return business["id"], filing_obligation["id"]


def test_create_filing_requires_auth(client):
    _business_id, obligation_id = _make_applicable_filing_obligation(client)
    resp = client.post("/api/v1/filings", json={"obligation_id": obligation_id})
    assert resp.status_code == 401


def test_create_filing_generates_deterministic_mock_draft(client, auth_headers):
    _business_id, obligation_id = _make_applicable_filing_obligation(client)
    resp = client.post(
        "/api/v1/filings", json={"obligation_id": obligation_id}, headers=auth_headers["owner"]
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "draft"
    assert body["document_ref"]
    assert "mock" in body["document_ref"].lower()
    assert body["human_approved_by"] is None


def test_create_filing_duplicate_draft_rejected(client, auth_headers):
    _business_id, obligation_id = _make_applicable_filing_obligation(client)
    client.post("/api/v1/filings", json={"obligation_id": obligation_id}, headers=auth_headers["owner"])
    resp = client.post("/api/v1/filings", json={"obligation_id": obligation_id}, headers=auth_headers["owner"])
    assert resp.status_code == 409


def test_owner_cannot_approve(client, auth_headers):
    _business_id, obligation_id = _make_applicable_filing_obligation(client)
    filing = client.post(
        "/api/v1/filings", json={"obligation_id": obligation_id}, headers=auth_headers["owner"]
    ).json()
    resp = client.post(f"/api/v1/filings/{filing['id']}/approve", headers=auth_headers["owner"])
    assert resp.status_code == 403


def test_ca_can_approve_then_submit(client, auth_headers):
    _business_id, obligation_id = _make_applicable_filing_obligation(client)
    filing = client.post(
        "/api/v1/filings", json={"obligation_id": obligation_id}, headers=auth_headers["owner"]
    ).json()

    approve_resp = client.post(f"/api/v1/filings/{filing['id']}/approve", headers=auth_headers["ca"])
    assert approve_resp.status_code == 200
    approved = approve_resp.json()
    assert approved["status"] == "approved"
    assert approved["human_approved_by"]

    submit_resp = client.post(f"/api/v1/filings/{filing['id']}/submit", headers=auth_headers["ca"])
    assert submit_resp.status_code == 200
    submitted = submit_resp.json()
    assert submitted["status"] == "submitted"
    assert submitted["submitted_at"] is not None
    assert submitted["mock"] is True
    assert "simulated" in submitted["mock_notice"].lower()


def test_mock_notice_survives_a_later_get_not_just_the_submit_response(client, auth_headers):
    # Regression: mock/mock_notice must be computed on every read of a
    # SUBMITTED filing, not just returned once by POST /submit -- a page
    # reload or a direct GET must still carry the disclosure.
    _business_id, obligation_id = _make_applicable_filing_obligation(client)
    filing = client.post(
        "/api/v1/filings", json={"obligation_id": obligation_id}, headers=auth_headers["owner"]
    ).json()
    client.post(f"/api/v1/filings/{filing['id']}/approve", headers=auth_headers["ca"])
    client.post(f"/api/v1/filings/{filing['id']}/submit", headers=auth_headers["ca"])

    refetched = client.get(f"/api/v1/filings/{filing['id']}").json()
    assert refetched["status"] == "submitted"
    assert refetched["mock"] is True
    assert refetched["mock_notice"] and "simulated" in refetched["mock_notice"].lower()


def test_draft_filing_is_not_flagged_mock(client, auth_headers):
    _business_id, obligation_id = _make_applicable_filing_obligation(client)
    filing = client.post(
        "/api/v1/filings", json={"obligation_id": obligation_id}, headers=auth_headers["owner"]
    ).json()
    assert filing["mock"] is False
    assert filing["mock_notice"] is None


def test_cannot_submit_before_approval(client, auth_headers):
    _business_id, obligation_id = _make_applicable_filing_obligation(client)
    filing = client.post(
        "/api/v1/filings", json={"obligation_id": obligation_id}, headers=auth_headers["owner"]
    ).json()
    resp = client.post(f"/api/v1/filings/{filing['id']}/submit", headers=auth_headers["ca"])
    assert resp.status_code == 409


def test_cannot_approve_twice(client, auth_headers):
    _business_id, obligation_id = _make_applicable_filing_obligation(client)
    filing = client.post(
        "/api/v1/filings", json={"obligation_id": obligation_id}, headers=auth_headers["owner"]
    ).json()
    client.post(f"/api/v1/filings/{filing['id']}/approve", headers=auth_headers["ca"])
    resp = client.post(f"/api/v1/filings/{filing['id']}/approve", headers=auth_headers["ca"])
    assert resp.status_code == 409


def test_ca_can_reject(client, auth_headers):
    _business_id, obligation_id = _make_applicable_filing_obligation(client)
    filing = client.post(
        "/api/v1/filings", json={"obligation_id": obligation_id}, headers=auth_headers["owner"]
    ).json()
    resp = client.post(f"/api/v1/filings/{filing['id']}/reject", headers=auth_headers["ca"])
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"


def test_list_filings_filters_by_business_and_status(client, auth_headers):
    business_id, obligation_id = _make_applicable_filing_obligation(client)
    client.post("/api/v1/filings", json={"obligation_id": obligation_id}, headers=auth_headers["owner"])

    resp = client.get("/api/v1/filings", params={"business_id": business_id, "status": "draft"})
    assert resp.status_code == 200
    filings = resp.json()
    assert len(filings) == 1
    assert filings[0]["business_id"] == business_id


def test_filing_state_transitions_are_audit_logged(client, auth_headers, session_factory):
    import uuid

    from app.models.audit_log import AuditLog

    _business_id, obligation_id = _make_applicable_filing_obligation(client)
    filing = client.post(
        "/api/v1/filings", json={"obligation_id": obligation_id}, headers=auth_headers["owner"]
    ).json()
    client.post(f"/api/v1/filings/{filing['id']}/approve", headers=auth_headers["ca"])
    client.post(f"/api/v1/filings/{filing['id']}/submit", headers=auth_headers["ca"])

    session = session_factory()
    try:
        actions = {
            row.action
            for row in session.query(AuditLog)
            .filter(AuditLog.entity_id == uuid.UUID(filing["id"]))
            .all()
        }
    finally:
        session.close()
    assert actions == {"filing.created", "filing.approved", "filing.submitted"}
