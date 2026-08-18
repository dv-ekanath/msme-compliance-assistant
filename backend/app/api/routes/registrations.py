from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.business import Business
from app.models.registration import Registration
from app.schemas.registration import RegistrationCreate, RegistrationRead, RegistrationUpdate

router = APIRouter(prefix="/registrations", tags=["registrations"])


@router.post("", response_model=RegistrationRead, status_code=201)
def create_registration(payload: RegistrationCreate, db: Session = Depends(get_db)) -> Registration:
    if db.get(Business, payload.business_id) is None:
        raise HTTPException(status_code=404, detail="Business not found")

    registration = Registration(**payload.model_dump())
    db.add(registration)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"A '{payload.type.value}' registration already exists for this business; use PATCH to update it.",
        ) from exc
    db.refresh(registration)
    return registration


@router.get("", response_model=list[RegistrationRead])
def list_registrations(
    business_id: uuid.UUID | None = Query(default=None), db: Session = Depends(get_db)
) -> list[Registration]:
    query = db.query(Registration)
    if business_id is not None:
        query = query.filter(Registration.business_id == business_id)
    return query.order_by(Registration.created_at.desc()).all()


@router.patch("/{registration_id}", response_model=RegistrationRead)
def update_registration(
    registration_id: uuid.UUID, payload: RegistrationUpdate, db: Session = Depends(get_db)
) -> Registration:
    registration = db.get(Registration, registration_id)
    if registration is None:
        raise HTTPException(status_code=404, detail="Registration not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(registration, field, value)

    db.commit()
    db.refresh(registration)
    return registration
