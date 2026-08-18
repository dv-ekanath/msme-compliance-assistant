from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.business import Business
from app.models.obligation import Obligation
from app.models.registration import Registration
from app.schemas.twin import ComplianceSummary, DigitalTwin
from app.services.twin import compute_summary, get_upcoming_deadlines

router = APIRouter(prefix="/twin", tags=["twin"])


@router.get("/{business_id}", response_model=DigitalTwin)
def get_twin(business_id: uuid.UUID, db: Session = Depends(get_db)) -> DigitalTwin:
    """The Digital Twin: business facts, registrations, obligations, and a
    compliance-health summary, assembled entirely from structured DB state
    (see app.services.twin) -- no LLM in this path.
    """
    business = db.get(Business, business_id)
    if business is None:
        raise HTTPException(status_code=404, detail="Business not found")

    registrations = db.query(Registration).filter(Registration.business_id == business_id).all()
    obligations = db.query(Obligation).filter(Obligation.business_id == business_id).all()

    summary = compute_summary(obligations)
    upcoming = get_upcoming_deadlines(obligations)

    return DigitalTwin(
        business=business,
        registrations=registrations,
        employee_count=business.employee_count,
        obligations=obligations,
        summary=ComplianceSummary(
            total_applicable=summary.total_applicable,
            completed=summary.completed,
            due_soon=summary.due_soon,
            overdue=summary.overdue,
            review_required=summary.review_required,
            compliance_health=summary.compliance_health,
        ),
        upcoming_deadlines=upcoming,
    )
