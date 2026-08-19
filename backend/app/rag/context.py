from __future__ import annotations

from sqlalchemy.orm import Session

from app.domain.enums import ObligationApplicability
from app.models.business import Business
from app.models.obligation import Obligation
from app.models.registration import Registration


def build_twin_context(db: Session, business: Business) -> str:
    """Compact, prompt-ready summary of a business's Digital Twin.

    Deliberately terse (not a full DB dump): enough for the LLM to
    personalize an explanation for *this* business, without over-stuffing
    the prompt. Obligation applicability listed here always comes from the
    deterministic Rules Engine (app/services/compliance.py) -- the LLM
    only ever reads this, it never recomputes it.
    """
    registrations = db.query(Registration).filter(Registration.business_id == business.id).all()
    obligations = db.query(Obligation).filter(Obligation.business_id == business.id).all()

    lines = [
        f"Business: {business.name}",
        f"Sector: {business.sector.value}, State: {business.state}, "
        f"Employees: {business.employee_count}, Turnover band: {business.turnover_band.value}",
    ]

    if registrations:
        reg_line = ", ".join(f"{r.type.value} ({r.status.value})" for r in registrations)
        lines.append(f"Registrations on file: {reg_line}")
    else:
        lines.append("Registrations on file: none")

    applicable = [o for o in obligations if o.applicability == ObligationApplicability.APPLICABLE]
    if applicable:
        lines.append("Obligations determined APPLICABLE by the deterministic Rules Engine:")
        for o in applicable:
            due = f", due {o.due_date}" if o.due_date else ""
            lines.append(f"  - {o.title} ({o.status.value}{due})")
    else:
        lines.append(
            "No obligations have been determined applicable yet "
            "(the business may need a POST /compliance/evaluate run)."
        )

    review_required = [o for o in obligations if o.applicability == ObligationApplicability.REVIEW_REQUIRED]
    if review_required:
        lines.append("Obligations flagged for MANUAL REVIEW (jurisdiction-specific, not auto-determined):")
        for o in review_required:
            lines.append(f"  - {o.title}")

    return "\n".join(lines)
