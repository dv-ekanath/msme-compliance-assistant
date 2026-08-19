from __future__ import annotations

import httpx

from app.domain.enums import AlertType
from app.models.alert import Alert
from app.models.regulation import Regulation
from app.watchdog.scanner import scan_regulations
from tests.test_business_api import business_payload


def _mock_client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_first_scan_baselines_without_flagging_changes(db_session):
    result = scan_regulations(
        db_session, http_client=_mock_client(lambda request: httpx.Response(200, content=b"same content"))
    )

    assert result.regulations_checked > 0
    assert result.changes_detected == 0
    assert result.alerts_created == 0
    assert all(o.checked and not o.changed for o in result.outcomes)

    regulations = db_session.query(Regulation).all()
    assert all(r.content_hash is not None for r in regulations)
    assert all(r.last_checked_at is not None for r in regulations)


def test_unchanged_content_on_second_scan_is_not_flagged(db_session):
    handler = lambda request: httpx.Response(200, content=b"same content")  # noqa: E731
    scan_regulations(db_session, http_client=_mock_client(handler))
    result = scan_regulations(db_session, http_client=_mock_client(handler))

    assert result.changes_detected == 0
    assert result.alerts_created == 0


def test_content_change_creates_alert_and_counts_affected_businesses(client, db_session):
    business = client.post(
        "/api/v1/business",
        json=business_payload(turnover_band="40l_5cr", employee_count=5, sector="trading"),
    ).json()
    client.post(f"/api/v1/compliance/evaluate/{business['id']}")

    # Baseline scan: first-ever check never counts as a "change".
    scan_regulations(
        db_session, http_client=_mock_client(lambda request: httpx.Response(200, content=b"v1"))
    )

    gst = db_session.query(Regulation).filter(Regulation.code == "GST").one()

    def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url) == gst.source_url:
            return httpx.Response(200, content=b"v2 -- changed")
        return httpx.Response(200, content=b"v1")

    result = scan_regulations(db_session, http_client=_mock_client(handler))

    assert result.changes_detected == 1
    assert result.alerts_created == 1

    outcome = next(o for o in result.outcomes if o.regulation_code == "GST")
    assert outcome.changed is True
    assert outcome.affected_business_count == 1

    alert = db_session.query(Alert).filter(Alert.alert_type == AlertType.REGULATION_CHANGE).one()
    assert alert.regulation_id == gst.id
    assert alert.business_id is None


def test_network_error_is_recorded_without_aborting_scan(db_session):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    result = scan_regulations(db_session, http_client=_mock_client(handler))

    assert result.regulations_checked == 0
    assert len(result.outcomes) > 0
    assert all(o.error is not None for o in result.outcomes)
