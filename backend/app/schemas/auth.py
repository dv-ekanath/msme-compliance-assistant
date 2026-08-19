from __future__ import annotations

import uuid

from pydantic import BaseModel

from app.domain.enums import UserRole


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    user_id: uuid.UUID
