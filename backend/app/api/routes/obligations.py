from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domain.enums import ObligationApplicability, ObligationStatus
from app.models.obligation import Obligation
from app.schemas.obligation import ObligationRead, ObligationStatusUpdate

router = APIRouter(prefix="/obligations", tags=["obligations"])


@router.get("", response_model=list[ObligationRead])
def list_obligations(
    business_id: uuid.UUID | None = Query(default=None),
    status: ObligationStatus | None = Query(default=None),
    applicability: ObligationApplicability | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[Obligation]:
    query = db.query(Obligation)
    if business_id is not None:
        query = query.filter(Obligation.business_id == business_id)
    if status is not None:
        query = query.filter(Obligation.status == status)
    if applicability is not None:
        query = query.filter(Obligation.applicability == applicability)
    return query.order_by(Obligation.due_date.is_(None), Obligation.due_date).all()


@router.patch("/{obligation_id}", response_model=ObligationRead)
def update_obligation_status(
    obligation_id: uuid.UUID, payload: ObligationStatusUpdate, db: Session = Depends(get_db)
) -> Obligation:
    """Manual status update only (e.g. marking an obligation Completed).

    Applicability, due dates, and reasons are owned by the Rules Engine
    (see POST /compliance/evaluate/{business_id}) and are not editable here.
    """
    obligation = db.get(Obligation, obligation_id)
    if obligation is None:
        raise HTTPException(status_code=404, detail="Obligation not found")

    obligation.status = payload.status
    db.commit()
    db.refresh(obligation)
    return obligation
