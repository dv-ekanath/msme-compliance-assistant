from __future__ import annotations

import httpx

from app.core.http import get_http_client
from app.main import app as fastapi_app


def _override_http_client(handler):
    def _get_client():
        client = httpx.Client(transport=httpx.MockTransport(handler))
        try:
            yield client
        finally:
            client.close()

    return _get_client


def test_manual_scan_baseline_returns_summary(client):
    fastapi_app.dependency_overrides[get_http_client] = _override_http_client(
        lambda request: httpx.Response(200, content=b"same content")
    )
    try:
        resp = client.post("/api/v1/watchdog/scan")
    finally:
        del fastapi_app.dependency_overrides[get_http_client]

    assert resp.status_code == 200
    body = resp.json()
    assert body["regulations_checked"] > 0
    assert body["changes_detected"] == 0
    assert body["alerts_created"] == 0
    assert len(body["outcomes"]) == body["regulations_checked"]


def test_manual_scan_records_fetch_errors(client):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    fastapi_app.dependency_overrides[get_http_client] = _override_http_client(handler)
    try:
        resp = client.post("/api/v1/watchdog/scan")
    finally:
        del fastapi_app.dependency_overrides[get_http_client]

    assert resp.status_code == 200
    body = resp.json()
    assert body["regulations_checked"] == 0
    assert all(o["error"] for o in body["outcomes"])
