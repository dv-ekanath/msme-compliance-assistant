from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_reviewer
from app.core.database import get_db
from app.domain.enums import FilingStatus
from app.models.filing import Filing
from app.models.obligation import Obligation
from app.models.user import User
from app.schemas.filing import FilingCreate, FilingRead
from app.services.filings import FilingStateError, approve_filing, create_filing, reject_filing, submit_filing

router = APIRouter(prefix="/filings", tags=["filings"])


@router.get("", response_model=list[FilingRead])
def list_filings(
    business_id: uuid.UUID | None = Query(default=None),
    status: FilingStatus | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[Filing]:
    query = db.query(Filing).join(Obligation, Filing.obligation_id == Obligation.id)
    if business_id is not None:
        query = query.filter(Obligation.business_id == business_id)
    if status is not None:
        query = query.filter(Filing.status == status)
    return query.order_by(Filing.created_at.desc()).all()


@router.get("/{filing_id}", response_model=FilingRead)
def get_filing(filing_id: uuid.UUID, db: Session = Depends(get_db)) -> Filing:
    filing = db.get(Filing, filing_id)
    if filing is None:
        raise HTTPException(status_code=404, detail="Filing not found")
    return filing


@router.post("", response_model=FilingRead, status_code=201)
def create_filing_route(
    payload: FilingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Filing:
    obligation = db.get(Obligation, payload.obligation_id)
    if obligation is None:
        raise HTTPException(status_code=404, detail="Obligation not found")

    try:
        return create_filing(db, obligation=obligation, actor=current_user, period=payload.period)
    except FilingStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


def _get_filing_or_404(db: Session, filing_id: uuid.UUID) -> Filing:
    filing = db.get(Filing, filing_id)
    if filing is None:
        raise HTTPException(status_code=404, detail="Filing not found")
    return filing


@router.post("/{filing_id}/approve", response_model=FilingRead)
def approve_filing_route(
    filing_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reviewer),
) -> Filing:
    filing = _get_filing_or_404(db, filing_id)
    try:
        return approve_filing(db, filing=filing, actor=current_user)
    except FilingStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{filing_id}/reject", response_model=FilingRead)
def reject_filing_route(
    filing_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reviewer),
) -> Filing:
    filing = _get_filing_or_404(db, filing_id)
    try:
        return reject_filing(db, filing=filing, actor=current_user)
    except FilingStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{filing_id}/submit", response_model=FilingRead)
def submit_filing_route(
    filing_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reviewer),
) -> Filing:
    filing = _get_filing_or_404(db, filing_id)
    try:
        return submit_filing(db, filing=filing, actor=current_user)
    except FilingStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
