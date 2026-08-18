from __future__ import annotations

from tests.test_business_api import business_payload


def test_create_registration(client):
    business = client.post("/api/v1/business", json=business_payload()).json()
    resp = client.post(
        "/api/v1/registrations", json={"business_id": business["id"], "type": "gst", "status": "active"}
    )
    assert resp.status_code == 201
    assert resp.json()["type"] == "gst"


def test_create_registration_for_missing_business_404(client):
    resp = client.post(
        "/api/v1/registrations",
        json={"business_id": "00000000-0000-0000-0000-000000000000", "type": "gst"},
    )
    assert resp.status_code == 404


def test_duplicate_registration_type_conflict(client):
    business = client.post("/api/v1/business", json=business_payload()).json()
    client.post("/api/v1/registrations", json={"business_id": business["id"], "type": "gst"})
    resp = client.post("/api/v1/registrations", json={"business_id": business["id"], "type": "gst"})
    assert resp.status_code == 409


def test_list_registrations_by_business(client):
    business = client.post("/api/v1/business", json=business_payload()).json()
    client.post("/api/v1/registrations", json={"business_id": business["id"], "type": "gst"})
    resp = client.get("/api/v1/registrations", params={"business_id": business["id"]})
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_update_registration(client):
    business = client.post("/api/v1/business", json=business_payload()).json()
    reg = client.post("/api/v1/registrations", json={"business_id": business["id"], "type": "gst"}).json()
    resp = client.patch(f"/api/v1/registrations/{reg['id']}", json={"status": "inactive"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "inactive"
