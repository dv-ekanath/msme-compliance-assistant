from __future__ import annotations


def _register_payload(**overrides) -> dict:
    payload = {
        "email": "newuser@test.local",
        "full_name": "New User",
        "password": "correct-horse-battery",
        "role": "owner",
    }
    payload.update(overrides)
    return payload


def test_register_returns_token(client):
    resp = client.post("/api/v1/auth/register", json=_register_payload())
    assert resp.status_code == 201
    body = resp.json()
    assert body["access_token"]
    assert body["role"] == "owner"
    assert body["user_id"]


def test_register_duplicate_email_rejected(client):
    client.post("/api/v1/auth/register", json=_register_payload())
    resp = client.post("/api/v1/auth/register", json=_register_payload())
    assert resp.status_code == 409


def test_login_with_correct_password_succeeds(client):
    client.post("/api/v1/auth/register", json=_register_payload())
    resp = client.post(
        "/api/v1/auth/login", json={"email": "newuser@test.local", "password": "correct-horse-battery"}
    )
    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_login_with_wrong_password_fails(client):
    client.post("/api/v1/auth/register", json=_register_payload())
    resp = client.post("/api/v1/auth/login", json={"email": "newuser@test.local", "password": "wrong-password"})
    assert resp.status_code == 401


def test_login_unknown_email_fails(client):
    resp = client.post("/api/v1/auth/login", json={"email": "nobody@test.local", "password": "anything"})
    assert resp.status_code == 401


def test_demo_users_can_log_in(client):
    # Seeded by tests/conftest.py's _seed_demo_users -- confirms the
    # fixture and the real login endpoint agree on the password hash.
    resp = client.post("/api/v1/auth/login", json={"email": "owner@test.local", "password": "password123"})
    assert resp.status_code == 200
    assert resp.json()["role"] == "owner"

    resp = client.post("/api/v1/auth/login", json={"email": "ca@test.local", "password": "password123"})
    assert resp.status_code == 200
    assert resp.json()["role"] == "ca"


def test_token_from_login_authenticates_a_gated_route(client, auth_headers):
    # POST /filings requires get_current_user -- a real end-to-end check
    # that a token minted by /auth/login (not just conftest's
    # create_access_token helper) actually authenticates.
    login_resp = client.post("/api/v1/auth/login", json={"email": "owner@test.local", "password": "password123"})
    token = login_resp.json()["access_token"]
    resp = client.get("/api/v1/filings", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_missing_token_rejected_by_gated_route(client):
    resp = client.post("/api/v1/filings", json={"obligation_id": "00000000-0000-0000-0000-000000000000"})
    assert resp.status_code == 401


def test_invalid_token_rejected(client):
    resp = client.post(
        "/api/v1/filings",
        json={"obligation_id": "00000000-0000-0000-0000-000000000000"},
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert resp.status_code == 401
