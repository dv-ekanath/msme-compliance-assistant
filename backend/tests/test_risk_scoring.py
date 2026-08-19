from __future__ import annotations

from datetime import date, timedelta

from app.domain.enums import ObligationFrequency, ObligationStatus, ObligationType
from app.rules.risk import band_for_score, explain_risk, score_obligation

TODAY = date(2026, 8, 19)


def test_completed_obligation_has_zero_risk():
    score = score_obligation(
        status=ObligationStatus.COMPLETED,
        obligation_type=ObligationType.FILING,
        frequency=ObligationFrequency.MONTHLY,
        due_date=TODAY - timedelta(days=5),
        today=TODAY,
    )
    assert score == 0.0
    assert band_for_score(score) == "low"


def test_overdue_scores_higher_than_due_soon():
    overdue = score_obligation(
        status=ObligationStatus.OVERDUE,
        obligation_type=ObligationType.FILING,
        frequency=ObligationFrequency.MONTHLY,
        due_date=TODAY - timedelta(days=10),
        today=TODAY,
    )
    due_soon = score_obligation(
        status=ObligationStatus.DUE_SOON,
        obligation_type=ObligationType.FILING,
        frequency=ObligationFrequency.MONTHLY,
        due_date=TODAY + timedelta(days=10),
        today=TODAY,
    )
    pending = score_obligation(
        status=ObligationStatus.PENDING,
        obligation_type=ObligationType.FILING,
        frequency=ObligationFrequency.MONTHLY,
        due_date=None,
        today=TODAY,
    )
    assert overdue > due_soon > pending


def test_overdue_risk_grows_with_days_overdue_then_caps():
    fresh = score_obligation(
        status=ObligationStatus.OVERDUE,
        obligation_type=ObligationType.FILING,
        frequency=ObligationFrequency.MONTHLY,
        due_date=TODAY - timedelta(days=1),
        today=TODAY,
    )
    stale = score_obligation(
        status=ObligationStatus.OVERDUE,
        obligation_type=ObligationType.FILING,
        frequency=ObligationFrequency.MONTHLY,
        due_date=TODAY - timedelta(days=90),
        today=TODAY,
    )
    assert stale > fresh
    assert stale <= 100.0


def test_due_soon_risk_grows_as_deadline_approaches():
    far = score_obligation(
        status=ObligationStatus.DUE_SOON,
        obligation_type=ObligationType.FILING,
        frequency=ObligationFrequency.MONTHLY,
        due_date=TODAY + timedelta(days=13),
        today=TODAY,
    )
    near = score_obligation(
        status=ObligationStatus.DUE_SOON,
        obligation_type=ObligationType.FILING,
        frequency=ObligationFrequency.MONTHLY,
        due_date=TODAY + timedelta(days=1),
        today=TODAY,
    )
    assert near > far


def test_payment_type_scores_higher_than_registration_type():
    payment = score_obligation(
        status=ObligationStatus.OVERDUE,
        obligation_type=ObligationType.PAYMENT,
        frequency=ObligationFrequency.MONTHLY,
        due_date=TODAY - timedelta(days=5),
        today=TODAY,
    )
    registration = score_obligation(
        status=ObligationStatus.OVERDUE,
        obligation_type=ObligationType.REGISTRATION,
        frequency=ObligationFrequency.MONTHLY,
        due_date=TODAY - timedelta(days=5),
        today=TODAY,
    )
    assert payment > registration


def test_monthly_frequency_scores_higher_than_annual():
    monthly = score_obligation(
        status=ObligationStatus.DUE_SOON,
        obligation_type=ObligationType.FILING,
        frequency=ObligationFrequency.MONTHLY,
        due_date=TODAY + timedelta(days=5),
        today=TODAY,
    )
    annual = score_obligation(
        status=ObligationStatus.DUE_SOON,
        obligation_type=ObligationType.FILING,
        frequency=ObligationFrequency.ANNUALLY,
        due_date=TODAY + timedelta(days=5),
        today=TODAY,
    )
    assert monthly > annual


def test_band_thresholds():
    assert band_for_score(0) == "low"
    assert band_for_score(33.9) == "low"
    assert band_for_score(34) == "medium"
    assert band_for_score(66.9) == "medium"
    assert band_for_score(67) == "high"
    assert band_for_score(100) == "high"


def test_explain_risk_is_deterministic_and_status_aware():
    completed = explain_risk(
        status=ObligationStatus.COMPLETED,
        obligation_type=ObligationType.FILING,
        frequency=ObligationFrequency.MONTHLY,
        band="low",
    )
    overdue = explain_risk(
        status=ObligationStatus.OVERDUE,
        obligation_type=ObligationType.FILING,
        frequency=ObligationFrequency.MONTHLY,
        band="high",
    )
    assert "no outstanding risk" in completed.lower()
    assert "overdue" in overdue.lower()
    assert "high" in overdue

    # Deterministic: same inputs -> identical output, no randomness/LLM.
    again = explain_risk(
        status=ObligationStatus.OVERDUE,
        obligation_type=ObligationType.FILING,
        frequency=ObligationFrequency.MONTHLY,
        band="high",
    )
    assert overdue == again
