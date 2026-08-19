from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.domain.enums import AlertSeverity, AlertType, ObligationApplicability, RegistrationType
from app.models.alert import Alert
from app.models.business import Business
from app.models.obligation import Obligation
from app.rules.types import RegulationConfig
from app.services.audit import log_audit_event
from app.services.twin import build_business_facts

# Regulation codes whose applicability_rules include a min_employee_count
# threshold, mapped to the RegistrationType a business would already hold
# if it registered ahead of reaching that threshold -- skip forecasting for
# those (already compliant, not "approaching" anything).
_EMPLOYEE_THRESHOLD_REGISTRATION_TYPE: dict[str, RegistrationType] = {
    "EPF": RegistrationType.EPF,
    "ESI": RegistrationType.ESI,
}


def generate_growth_forecast_alerts(
    db: Session,
    business: Business,
    regulations_by_code: dict[str, RegulationConfig],
) -> list[Alert]:
    """Predicts obligations before they're APPLICABLE yet: flags when
    business.employee_count is within growth_forecast_employee_window of a
    regulation's min_employee_count threshold (e.g. EPF's 20, ESI's 10).
    Generic over any regulation carrying that key -- no regulation-code
    logic beyond the registration-status exclusion above. Deterministic
    heuristic, no LLM/ML -- CLAUDE.md rule 4.

    One GROWTH_FORECAST alert ever per (business, regulation) pair -- no
    re-spam on repeated /compliance/evaluate calls.
    """
    window = get_settings().growth_forecast_employee_window
    facts = build_business_facts(db, business)
    now = datetime.now(timezone.utc)

    already_alerted = {
        a.regulation_id
        for a in db.query(Alert)
        .filter(Alert.alert_type == AlertType.GROWTH_FORECAST, Alert.business_id == business.id)
        .all()
    }

    created: list[Alert] = []
    for code, regulation in regulations_by_code.items():
        threshold = regulation.applicability_rules.get("min_employee_count")
        if threshold is None or regulation.id in already_alerted:
            continue

        registration_type = _EMPLOYEE_THRESHOLD_REGISTRATION_TYPE.get(code)
        if registration_type and facts.has_active_registration(registration_type):
            continue

        gap = threshold - business.employee_count
        if 0 < gap <= window:
            alert = Alert(
                alert_type=AlertType.GROWTH_FORECAST,
                business_id=business.id,
                regulation_id=regulation.id,
                severity=AlertSeverity.MEDIUM,
                title=f"Approaching the {regulation.title} employee threshold",
                message=(
                    f"{business.name} has {business.employee_count} employee(s); "
                    f"{regulation.title} becomes mandatory at {threshold}. "
                    f"You are {gap} employee(s) away -- plan ahead to register in time."
                ),
                detected_at=now,
            )
            db.add(alert)
            created.append(alert)

    if created:
        db.commit()
        for alert in created:
            db.refresh(alert)
    return created


def list_alerts_for_business(db: Session, business_id: uuid.UUID) -> list[Alert]:
    """Growth-forecast alerts belong to this business directly.
    Regulation-change alerts are global events (business_id NULL) scoped
    down to regulations this business is currently affected by -- has an
    APPLICABLE Obligation against. Single filtered query, no UNION.
    """
    applicable_regulation_ids = [
        row[0]
        for row in db.query(Obligation.regulation_id)
        .filter(
            Obligation.business_id == business_id,
            Obligation.applicability == ObligationApplicability.APPLICABLE,
        )
        .distinct()
        .all()
    ]

    return (
        db.query(Alert)
        .filter(
            or_(
                and_(Alert.alert_type == AlertType.GROWTH_FORECAST, Alert.business_id == business_id),
                and_(
                    Alert.alert_type == AlertType.REGULATION_CHANGE,
                    Alert.regulation_id.in_(applicable_regulation_ids),
                ),
            )
        )
        .order_by(Alert.detected_at.desc())
        .all()
    )


def acknowledge_alert(db: Session, alert: Alert) -> Alert:
    alert.acknowledged_at = datetime.now(timezone.utc)
    log_audit_event(
        db,
        actor_id=None,
        action="alert.acknowledged",
        entity_type="alert",
        entity_id=alert.id,
        detail=f"Alert '{alert.title}' acknowledged.",
    )
    db.commit()
    db.refresh(alert)
    return alert
