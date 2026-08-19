from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserRegister
from app.services.audit import log_audit_event

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: UserRegister, db: Session = Depends(get_db)) -> TokenResponse:
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        role=payload.role,
        business_id=payload.business_id,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="A user with this email already exists.") from exc

    log_audit_event(
        db,
        actor_id=user.id,
        action="user.registered",
        entity_type="user",
        entity_id=user.id,
        detail=f"{user.email} registered as {user.role.value}.",
    )
    db.commit()

    return TokenResponse(
        access_token=create_access_token(user.id, user.role),
        role=user.role,
        user_id=user.id,
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or user.hashed_password is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    return TokenResponse(
        access_token=create_access_token(user.id, user.role),
        role=user.role,
        user_id=user.id,
    )
