from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.domain.enums import AlertSeverity, AlertType


class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    alert_type: AlertType
    business_id: uuid.UUID | None
    regulation_id: uuid.UUID | None
    obligation_id: uuid.UUID | None
    severity: AlertSeverity
    title: str
    message: str
    detected_at: datetime
    acknowledged_at: datetime | None
    regulation_title: str | None
    regulation_source_url: str | None
