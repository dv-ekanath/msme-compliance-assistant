from __future__ import annotations

from tests.test_business_api import business_payload


def test_twin_not_found(client):
    resp = client.get("/api/v1/twin/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


def test_twin_before_evaluation_has_no_obligations(client):
    business = client.post("/api/v1/business", json=business_payload()).json()
    resp = client.get(f"/api/v1/twin/{business['id']}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["obligations"] == []
    assert body["summary"]["total_applicable"] == 0
    assert body["summary"]["compliance_health"] == "good"


def test_twin_after_evaluation_includes_obligations(client):
    business = client.post(
        "/api/v1/business",
        json=business_payload(turnover_band="40l_5cr", employee_count=25, sector="trading"),
    ).json()
    client.post(f"/api/v1/compliance/evaluate/{business['id']}")
    resp = client.get(f"/api/v1/twin/{business['id']}")
    body = resp.json()
    assert len(body["obligations"]) == 9
    titles = {o["title"] for o in body["obligations"]}
    assert "GST Registration" in titles
    assert body["employee_count"] == 25
