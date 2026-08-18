from __future__ import annotations

from tests.test_business_api import business_payload


def test_evaluate_not_found(client):
    resp = client.post("/api/v1/compliance/evaluate/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


def test_evaluate_small_business_mostly_not_applicable(client):
    business = client.post(
        "/api/v1/business",
        json=business_payload(turnover_band="under_10l", employee_count=2, sector="services"),
    ).json()
    resp = client.post(f"/api/v1/compliance/evaluate/{business['id']}")
    assert resp.status_code == 200
    body = resp.json()
    results_by_rule = {r["rule_id"]: r for r in body["results"]}

    assert results_by_rule["gst_registration_threshold"]["applicability"] == "not_applicable"
    assert results_by_rule["epf_applicability"]["applicability"] == "not_applicable"
    assert results_by_rule["esi_applicability"]["applicability"] == "not_applicable"
    assert results_by_rule["shops_establishment_registration"]["applicability"] == "review_required"
    assert results_by_rule["professional_tax_review"]["applicability"] == "review_required"

    # Every result must explain itself and cite a real, verifiable source.
    for r in body["results"]:
        assert r["reason"]
        assert r["source_url"].startswith("https://")


def test_evaluate_large_business_triggers_multiple_obligations(client):
    business = client.post(
        "/api/v1/business",
        json=business_payload(turnover_band="5cr_50cr", employee_count=50, sector="trading"),
    ).json()
    resp = client.post(f"/api/v1/compliance/evaluate/{business['id']}")
    body = resp.json()
    results_by_rule = {r["rule_id"]: r for r in body["results"]}

    assert results_by_rule["gst_registration_threshold"]["applicability"] == "applicable"
    assert results_by_rule["epf_applicability"]["applicability"] == "applicable"
    assert results_by_rule["esi_applicability"]["applicability"] == "applicable"
    assert results_by_rule["udyam_registration"]["applicability"] == "applicable"
    assert body["summary"]["total_applicable"] >= 4


def test_evaluate_is_idempotent(client):
    business = client.post(
        "/api/v1/business",
        json=business_payload(turnover_band="5cr_50cr", employee_count=50, sector="trading"),
    ).json()
    client.post(f"/api/v1/compliance/evaluate/{business['id']}")
    client.post(f"/api/v1/compliance/evaluate/{business['id']}")
    obligations = client.get("/api/v1/obligations", params={"business_id": business["id"]}).json()
    assert len(obligations) == 9  # upserted, not duplicated


def test_registering_gst_flips_registration_and_filing_obligations(client):
    business = client.post(
        "/api/v1/business",
        json=business_payload(turnover_band="40l_5cr", employee_count=5, sector="trading"),
    ).json()
    client.post(f"/api/v1/compliance/evaluate/{business['id']}")
    before = {
        o["rule_id"]: o
        for o in client.get("/api/v1/obligations", params={"business_id": business["id"]}).json()
    }
    assert before["gst_registration_threshold"]["applicability"] == "applicable"
    assert before["gst_periodic_filing"]["applicability"] == "not_applicable"

    client.post("/api/v1/registrations", json={"business_id": business["id"], "type": "gst"})
    client.post(f"/api/v1/compliance/evaluate/{business['id']}")

    after = {
        o["rule_id"]: o
        for o in client.get("/api/v1/obligations", params={"business_id": business["id"]}).json()
    }
    assert after["gst_registration_threshold"]["applicability"] == "not_applicable"
    assert after["gst_periodic_filing"]["applicability"] == "applicable"


def test_marking_one_time_obligation_completed_persists_across_reevaluate(client):
    business = client.post(
        "/api/v1/business",
        json=business_payload(turnover_band="40l_5cr", employee_count=2, sector="trading"),
    ).json()
    client.post(f"/api/v1/compliance/evaluate/{business['id']}")
    obligations = client.get("/api/v1/obligations", params={"business_id": business["id"]}).json()
    gst_reg = next(o for o in obligations if o["rule_id"] == "gst_registration_threshold")
    assert gst_reg["applicability"] == "applicable"

    resp = client.patch(f"/api/v1/obligations/{gst_reg['id']}", json={"status": "completed"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"

    client.post(f"/api/v1/compliance/evaluate/{business['id']}")
    refreshed = {
        o["rule_id"]: o
        for o in client.get("/api/v1/obligations", params={"business_id": business["id"]}).json()
    }
    assert refreshed["gst_registration_threshold"]["status"] == "completed"


def test_obligations_filter_by_status(client):
    business = client.post(
        "/api/v1/business",
        json=business_payload(turnover_band="5cr_50cr", employee_count=50, sector="trading"),
    ).json()
    client.post(f"/api/v1/compliance/evaluate/{business['id']}")

    resp = client.get(
        "/api/v1/obligations", params={"business_id": business["id"], "applicability": "review_required"}
    )
    assert resp.status_code == 200
    rule_ids = {o["rule_id"] for o in resp.json()}
    assert rule_ids == {"shops_establishment_registration", "professional_tax_review"}
