from __future__ import annotations

import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.domain.enums import UserRole
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

_CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = decode_access_token(token)
        user_id = uuid.UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise _CREDENTIALS_ERROR from exc

    user = db.get(User, user_id)
    if user is None:
        raise _CREDENTIALS_ERROR
    return user


def require_reviewer(user: User = Depends(get_current_user)) -> User:
    """CA and ADMIN form one "reviewer" tier for authorization purposes --
    CLAUDE.md's "two roles: MSME owner, CA/admin" line, not a 3-tier
    permissions framework (rule 2).
    """
    if user.role not in (UserRole.CA, UserRole.ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CA/admin role required")
    return user
