from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import UserRole


class UserRegister(BaseModel):
    # Plain str, not EmailStr -- RFC-compliant validation needs the
    # email-validator package, which isn't earning its place here (rule 2).
    email: str = Field(min_length=1, max_length=255)
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=255)
    role: UserRole
    business_id: uuid.UUID | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    business_id: uuid.UUID | None
    created_at: datetime
