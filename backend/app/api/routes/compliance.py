from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.business import Business
from app.schemas.compliance import ComplianceEvaluationResult, ComplianceResultItem
from app.schemas.twin import ComplianceSummary
from app.services.compliance import evaluate_business_compliance
from app.services.twin import compute_summary

router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.post("/evaluate/{business_id}", response_model=ComplianceEvaluationResult)
def evaluate_compliance(business_id: uuid.UUID, db: Session = Depends(get_db)) -> ComplianceEvaluationResult:
    """Runs the deterministic Rules Engine for a business and upserts its
    obligations. The LLM is not involved anywhere in this path -- every
    result here is traceable to a rule_id and a seeded regulation.
    """
    business = db.get(Business, business_id)
    if business is None:
        raise HTTPException(status_code=404, detail="Business not found")

    try:
        obligations, results, regulations_by_code = evaluate_business_compliance(db, business)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    obligations_by_rule = {o.rule_id: o for o in obligations}
    result_items = [
        ComplianceResultItem(
            rule_id=result.rule_id,
            obligation=result.title,
            obligation_type=result.obligation_type,
            applicability=result.applicability,
            status=obligations_by_rule[result.rule_id].status,
            reason=result.reason,
            regulation=regulations_by_code[result.regulation_code].title,
            regulation_code=result.regulation_code,
            source_url=regulations_by_code[result.regulation_code].source_url,
            frequency=result.frequency,
            due_date=result.due_date,
        )
        for result in results
    ]

    summary = compute_summary(obligations)

    return ComplianceEvaluationResult(
        business_id=str(business_id),
        evaluated_at=datetime.now(timezone.utc),
        results=result_items,
        summary=ComplianceSummary(
            total_applicable=summary.total_applicable,
            completed=summary.completed,
            due_soon=summary.due_soon,
            overdue=summary.overdue,
            review_required=summary.review_required,
            compliance_health=summary.compliance_health,
        ),
    )
