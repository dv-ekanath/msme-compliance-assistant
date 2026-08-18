from __future__ import annotations


def business_payload(**overrides) -> dict:
    payload = {
        "name": "Test Traders",
        "sector": "trading",
        "state": "Delhi",
        "registration_type": "proprietorship",
        "turnover_band": "20l_40l",
        "employee_count": 5,
        "incorporation_date": "2020-01-01",
    }
    payload.update(overrides)
    return payload


def test_create_business(client):
    resp = client.post("/api/v1/business", json=business_payload())
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Test Traders"
    assert body["sector"] == "trading"
    assert "id" in body


def test_create_business_missing_required_field_fails(client):
    payload = business_payload()
    del payload["sector"]
    resp = client.post("/api/v1/business", json=payload)
    assert resp.status_code == 422


def test_get_business_not_found(client):
    resp = client.get("/api/v1/business/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


def test_get_business(client):
    created = client.post("/api/v1/business", json=business_payload()).json()
    resp = client.get(f"/api/v1/business/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_list_businesses(client):
    client.post("/api/v1/business", json=business_payload(name="A"))
    client.post("/api/v1/business", json=business_payload(name="B"))
    resp = client.get("/api/v1/business")
    assert resp.status_code == 200
    names = {b["name"] for b in resp.json()}
    assert {"A", "B"} <= names


def test_update_business(client):
    created = client.post("/api/v1/business", json=business_payload()).json()
    resp = client.patch(f"/api/v1/business/{created['id']}", json={"employee_count": 25})
    assert resp.status_code == 200
    assert resp.json()["employee_count"] == 25
