from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.domain.enums import ObligationApplicability, ObligationStatus
from app.domain.facts import BusinessFacts
from app.models.business import Business
from app.models.obligation import Obligation
from app.models.regulation import Regulation
from app.rules.engine import RulesEngine
from app.rules.registry import REGULATION_CODES
from app.rules.risk import score_obligation
from app.rules.types import RegulationConfig, RuleResult
from app.services.twin import build_business_facts

DUE_SOON_WINDOW_DAYS = 14


def load_regulation_configs(db: Session) -> dict[str, RegulationConfig]:
    rows = db.query(Regulation).filter(Regulation.code.in_(REGULATION_CODES)).all()
    missing = REGULATION_CODES - {r.code for r in rows}
    if missing:
        raise ValueError(
            f"Required regulation(s) not seeded: {sorted(missing)}. "
            "Run `python -m seed.load_regulations` from the backend/ directory."
        )
    return {
        r.code: RegulationConfig(
            id=r.id,
            code=r.code,
            title=r.title,
            authority=r.authority,
            source_url=r.source_url,
            applicability_rules=r.applicability_rules,
        )
        for r in rows
    }


def _derive_status(due_date: date | None, today: date) -> ObligationStatus:
    if due_date is None:
        return ObligationStatus.PENDING
    if due_date < today:
        return ObligationStatus.OVERDUE
    if due_date <= today + timedelta(days=DUE_SOON_WINDOW_DAYS):
        return ObligationStatus.DUE_SOON
    return ObligationStatus.PENDING


def evaluate_business_compliance(
    db: Session, business: Business
) -> tuple[list[Obligation], list[RuleResult], dict[str, RegulationConfig]]:
    """Runs the deterministic Rules Engine (no LLM) and upserts Obligation
    rows for `business`.

    Idempotent: a rerun updates the same rows (unique on business_id +
    rule_id) rather than duplicating them, and preserves a manually-set
    COMPLETED status for as long as the computed due_date is unchanged
    (i.e. still the same filing period) -- once a new period's due_date
    is computed, status resets like any other obligation.
    """
    facts: BusinessFacts = build_business_facts(db, business)
    regulations_by_code = load_regulation_configs(db)
    results: list[RuleResult] = RulesEngine().evaluate(facts, regulations_by_code)

    today = date.today()
    now = datetime.now(timezone.utc)

    existing_by_rule = {
        o.rule_id: o for o in db.query(Obligation).filter(Obligation.business_id == business.id).all()
    }

    touched: list[Obligation] = []
    for result in results:
        regulation_id = regulations_by_code[result.regulation_code].id
        obligation = existing_by_rule.get(result.rule_id)

        if obligation is None:
            obligation = Obligation(
                business_id=business.id,
                regulation_id=regulation_id,
                rule_id=result.rule_id,
            )
            db.add(obligation)

        obligation.regulation_id = regulation_id
        obligation.obligation_type = result.obligation_type
        obligation.title = result.title
        obligation.reason = result.reason
        obligation.frequency = result.frequency
        obligation.applicability = result.applicability
        obligation.last_evaluated_at = now

        if result.applicability == ObligationApplicability.APPLICABLE and result.due_date is not None:
            same_period = obligation.due_date == result.due_date
            obligation.due_date = result.due_date
            if not (obligation.status == ObligationStatus.COMPLETED and same_period):
                obligation.status = _derive_status(result.due_date, today)
        else:
            # Not applicable, review-required, or a one-time obligation
            # with no computed due date -- no due-date status to derive.
            obligation.due_date = None
            if obligation.status != ObligationStatus.COMPLETED:
                obligation.status = ObligationStatus.PENDING

        if result.applicability == ObligationApplicability.APPLICABLE:
            obligation.risk_score = score_obligation(
                status=obligation.status,
                obligation_type=obligation.obligation_type,
                frequency=obligation.frequency,
                due_date=obligation.due_date,
                today=today,
            )
        else:
            obligation.risk_score = None

        touched.append(obligation)

    db.commit()
    for obligation in touched:
        db.refresh(obligation)

    return touched, results, regulations_by_code
