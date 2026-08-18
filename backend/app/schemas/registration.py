from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.domain.enums import RegistrationStatus, RegistrationType


class RegistrationCreate(BaseModel):
    business_id: uuid.UUID
    type: RegistrationType
    number: str | None = None
    status: RegistrationStatus = RegistrationStatus.ACTIVE
    valid_from: date | None = None
    valid_to: date | None = None
    document_ref: str | None = None


class RegistrationUpdate(BaseModel):
    number: str | None = None
    status: RegistrationStatus | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    document_ref: str | None = None


class RegistrationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_id: uuid.UUID
    type: RegistrationType
    number: str | None
    status: RegistrationStatus
    valid_from: date | None
    valid_to: date | None
    document_ref: str | None
    created_at: datetime
    updated_at: datetime
