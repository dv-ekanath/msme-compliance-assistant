from __future__ import annotations

from tests.test_business_api import business_payload


def test_list_alerts_empty_for_new_business(client):
    business = client.post("/api/v1/business", json=business_payload()).json()
    resp = client.get("/api/v1/alerts", params={"business_id": business["id"]})
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_alerts_requires_business_id(client):
    resp = client.get("/api/v1/alerts")
    assert resp.status_code == 422


def test_acknowledge_alert_not_found(client):
    resp = client.post("/api/v1/alerts/00000000-0000-0000-0000-000000000000/acknowledge")
    assert resp.status_code == 404


def test_acknowledge_alert_sets_timestamp(client):
    business = client.post(
        "/api/v1/business",
        json=business_payload(employee_count=17, turnover_band="40l_5cr"),
    ).json()
    client.post(f"/api/v1/compliance/evaluate/{business['id']}")

    alerts = client.get("/api/v1/alerts", params={"business_id": business["id"]}).json()
    assert len(alerts) == 1
    assert alerts[0]["acknowledged_at"] is None

    resp = client.post(f"/api/v1/alerts/{alerts[0]['id']}/acknowledge")
    assert resp.status_code == 200
    assert resp.json()["acknowledged_at"] is not None
