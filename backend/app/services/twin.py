from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.domain.enums import ObligationApplicability, ObligationStatus
from app.domain.facts import BusinessFacts, RegistrationFact
from app.models.business import Business
from app.models.obligation import Obligation
from app.models.registration import Registration


def build_business_facts(db: Session, business: Business) -> BusinessFacts:
    """The Digital Twin's factual core: a plain snapshot of DB state, with
    no LLM or inference involved. This is what the Rules Engine evaluates.
    """
    registrations = db.query(Registration).filter(Registration.business_id == business.id).all()
    registration_facts = {
        r.type: RegistrationFact(type=r.type, status=r.status, valid_to=r.valid_to) for r in registrations
    }
    return BusinessFacts(
        business_id=str(business.id),
        name=business.name,
        sector=business.sector,
        state=business.state,
        legal_type=business.registration_type,
        turnover_band=business.turnover_band,
        employee_count=business.employee_count,
        incorporation_date=business.incorporation_date,
        registrations=registration_facts,
    )


@dataclass
class ObligationSummary:
    total_applicable: int
    completed: int
    due_soon: int
    overdue: int
    review_required: int
    compliance_health: str  # "good" | "attention_needed" | "critical"


def compute_summary(obligations: list[Obligation]) -> ObligationSummary:
    applicable = [o for o in obligations if o.applicability == ObligationApplicability.APPLICABLE]
    review_required = [o for o in obligations if o.applicability == ObligationApplicability.REVIEW_REQUIRED]
    completed = sum(1 for o in applicable if o.status == ObligationStatus.COMPLETED)
    due_soon = sum(1 for o in applicable if o.status == ObligationStatus.DUE_SOON)
    overdue = sum(1 for o in applicable if o.status == ObligationStatus.OVERDUE)

    if overdue > 0:
        health = "critical"
    elif due_soon > 0 or review_required:
        health = "attention_needed"
    else:
        health = "good"

    return ObligationSummary(
        total_applicable=len(applicable),
        completed=completed,
        due_soon=due_soon,
        overdue=overdue,
        review_required=len(review_required),
        compliance_health=health,
    )


def get_upcoming_deadlines(obligations: list[Obligation], limit: int = 5) -> list[Obligation]:
    dated = [
        o
        for o in obligations
        if o.applicability == ObligationApplicability.APPLICABLE
        and o.due_date is not None
        and o.status != ObligationStatus.COMPLETED
    ]
    return sorted(dated, key=lambda o: o.due_date)[:limit]
