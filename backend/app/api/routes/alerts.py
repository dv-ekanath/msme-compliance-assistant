from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.alert import Alert
from app.schemas.alert import AlertRead
from app.services.alerts import acknowledge_alert, list_alerts_for_business

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertRead])
def list_alerts(business_id: uuid.UUID = Query(...), db: Session = Depends(get_db)) -> list[Alert]:
    return list_alerts_for_business(db, business_id)


@router.post("/{alert_id}/acknowledge", response_model=AlertRead)
def acknowledge(alert_id: uuid.UUID, db: Session = Depends(get_db)) -> Alert:
    alert = db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return acknowledge_alert(db, alert)
