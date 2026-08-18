from __future__ import annotations

from pydantic import BaseModel

from app.schemas.business import BusinessRead
from app.schemas.obligation import ObligationRead
from app.schemas.registration import RegistrationRead


class ComplianceSummary(BaseModel):
    total_applicable: int
    completed: int
    due_soon: int
    overdue: int
    review_required: int
    compliance_health: str


class DigitalTwin(BaseModel):
    business: BusinessRead
    registrations: list[RegistrationRead]
    employee_count: int
    obligations: list[ObligationRead]
    summary: ComplianceSummary
    upcoming_deadlines: list[ObligationRead]
