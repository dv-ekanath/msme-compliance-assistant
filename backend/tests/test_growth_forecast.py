from __future__ import annotations

from tests.test_business_api import business_payload


def _growth_alerts(client, business_id: str) -> list[dict]:
    alerts = client.get("/api/v1/alerts", params={"business_id": business_id}).json()
    return [a for a in alerts if a["alert_type"] == "growth_forecast"]


def test_growth_forecast_alert_created_when_near_epf_threshold(client):
    # EPF threshold is 20; window default is 3 -> 17 employees triggers.
    business = client.post(
        "/api/v1/business",
        json=business_payload(employee_count=17, turnover_band="40l_5cr"),
    ).json()
    client.post(f"/api/v1/compliance/evaluate/{business['id']}")

    growth_alerts = _growth_alerts(client, business["id"])
    assert len(growth_alerts) == 1
    assert growth_alerts[0]["business_id"] == business["id"]


def test_no_growth_forecast_alert_when_far_from_any_threshold(client):
    business = client.post(
        "/api/v1/business",
        json=business_payload(employee_count=2, turnover_band="40l_5cr"),
    ).json()
    client.post(f"/api/v1/compliance/evaluate/{business['id']}")

    assert _growth_alerts(client, business["id"]) == []


def test_no_growth_forecast_alert_once_threshold_already_reached(client):
    # 25 employees -> EPF/ESI are already APPLICABLE, not "approaching".
    business = client.post(
        "/api/v1/business",
        json=business_payload(employee_count=25, turnover_band="40l_5cr"),
    ).json()
    client.post(f"/api/v1/compliance/evaluate/{business['id']}")

    assert _growth_alerts(client, business["id"]) == []


def test_growth_forecast_alert_not_duplicated_on_repeat_evaluate(client):
    # 8 employees -> only ESI (threshold 10) is within the window.
    business = client.post(
        "/api/v1/business",
        json=business_payload(employee_count=8, turnover_band="40l_5cr"),
    ).json()
    client.post(f"/api/v1/compliance/evaluate/{business['id']}")
    client.post(f"/api/v1/compliance/evaluate/{business['id']}")

    assert len(_growth_alerts(client, business["id"])) == 1
