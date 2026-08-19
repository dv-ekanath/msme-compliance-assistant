from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.business import Business
from app.schemas.business import BusinessCreate, BusinessRead, BusinessUpdate
from app.services.audit import log_audit_event

router = APIRouter(prefix="/business", tags=["business"])


def _get_business_or_404(db: Session, business_id: uuid.UUID) -> Business:
    business = db.get(Business, business_id)
    if business is None:
        raise HTTPException(status_code=404, detail="Business not found")
    return business


@router.post("", response_model=BusinessRead, status_code=201)
def create_business(payload: BusinessCreate, db: Session = Depends(get_db)) -> Business:
    business = Business(**payload.model_dump())
    db.add(business)
    db.flush()
    log_audit_event(
        db,
        actor_id=None,
        action="business.created",
        entity_type="business",
        entity_id=business.id,
        detail=f"Business '{business.name}' onboarded.",
    )
    db.commit()
    db.refresh(business)
    return business


@router.get("", response_model=list[BusinessRead])
def list_businesses(db: Session = Depends(get_db)) -> list[Business]:
    return db.query(Business).order_by(Business.created_at.desc()).all()


@router.get("/{business_id}", response_model=BusinessRead)
def get_business(business_id: uuid.UUID, db: Session = Depends(get_db)) -> Business:
    return _get_business_or_404(db, business_id)


@router.patch("/{business_id}", response_model=BusinessRead)
def update_business(business_id: uuid.UUID, payload: BusinessUpdate, db: Session = Depends(get_db)) -> Business:
    business = _get_business_or_404(db, business_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(business, field, value)
    log_audit_event(
        db,
        actor_id=None,
        action="business.updated",
        entity_type="business",
        entity_id=business.id,
        detail=f"Business '{business.name}' updated: {sorted(payload.model_dump(exclude_unset=True).keys())}.",
    )
    db.commit()
    db.refresh(business)
    return business
