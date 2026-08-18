from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel

from app.domain.enums import ObligationApplicability, ObligationFrequency, ObligationStatus, ObligationType
from app.schemas.twin import ComplianceSummary


class ComplianceResultItem(BaseModel):
    rule_id: str
    obligation: str
    obligation_type: ObligationType
    applicability: ObligationApplicability
    status: ObligationStatus
    reason: str
    regulation: str
    regulation_code: str
    source_url: str
    frequency: ObligationFrequency | None
    due_date: date | None


class ComplianceEvaluationResult(BaseModel):
    business_id: str
    evaluated_at: datetime
    results: list[ComplianceResultItem]
    summary: ComplianceSummary
