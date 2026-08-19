from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.domain.enums import FilingStatus


class FilingCreate(BaseModel):
    obligation_id: uuid.UUID
    period: str | None = None


class FilingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    obligation_id: uuid.UUID
    business_id: uuid.UUID
    obligation_title: str
    period: str | None
    status: FilingStatus
    document_ref: str | None
    human_approved_by: uuid.UUID | None
    submitted_at: datetime | None
    created_at: datetime
    # Computed from Filing.is_mock_submission/mock_notice -- present on
    # every read of a SUBMITTED filing (list, get, or the submit response
    # itself), not just a one-time flag, so the mock disclosure survives
    # a reload or a direct API call (CLAUDE.md rule 5: "clearly labeled").
    mock: bool = False
    mock_notice: str | None = None
