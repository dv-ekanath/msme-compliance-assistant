from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import BusinessLegalType, SectorType, TurnoverBand


class BusinessCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    sector: SectorType
    state: str = Field(min_length=1, max_length=100)
    registration_type: BusinessLegalType
    turnover_band: TurnoverBand
    employee_count: int = Field(default=0, ge=0)
    incorporation_date: date | None = None
    udyam_number: str | None = None
    gstin: str | None = None
    pan: str | None = None
    address: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None


class BusinessUpdate(BaseModel):
    name: str | None = None
    sector: SectorType | None = None
    state: str | None = None
    registration_type: BusinessLegalType | None = None
    turnover_band: TurnoverBand | None = None
    employee_count: int | None = Field(default=None, ge=0)
    incorporation_date: date | None = None
    udyam_number: str | None = None
    gstin: str | None = None
    pan: str | None = None
    address: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None


class BusinessRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    sector: SectorType
    state: str
    registration_type: BusinessLegalType
    turnover_band: TurnoverBand
    employee_count: int
    incorporation_date: date | None
    udyam_number: str | None
    gstin: str | None
    pan: str | None
    address: str | None
    contact_phone: str | None
    contact_email: str | None
    created_at: datetime
    updated_at: datetime
