from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.domain.enums import ObligationApplicability, ObligationFrequency, ObligationStatus, ObligationType


class ObligationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_id: uuid.UUID
    regulation_id: uuid.UUID
    rule_id: str
    obligation_type: ObligationType
    title: str
    reason: str
    frequency: ObligationFrequency | None
    due_date: date | None
    applicability: ObligationApplicability
    status: ObligationStatus
    risk_score: float | None
    last_evaluated_at: datetime


class ObligationStatusUpdate(BaseModel):
    status: ObligationStatus
