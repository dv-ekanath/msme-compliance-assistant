from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.http import get_http_client
from app.schemas.watchdog import RegulationScanOutcomeRead, WatchdogScanSummary
from app.watchdog.scanner import scan_regulations

router = APIRouter(prefix="/watchdog", tags=["watchdog"])


@router.post("/scan", response_model=WatchdogScanSummary)
def trigger_scan(
    db: Session = Depends(get_db), http_client: httpx.Client = Depends(get_http_client)
) -> WatchdogScanSummary:
    """Manually triggers a watchdog scan (the same scan APScheduler runs on
    its interval) -- useful for demo control and immediate verification
    rather than waiting for the schedule.
    """
    result = scan_regulations(db, http_client=http_client)
    return WatchdogScanSummary(
        regulations_checked=result.regulations_checked,
        changes_detected=result.changes_detected,
        alerts_created=result.alerts_created,
        outcomes=[
            RegulationScanOutcomeRead(
                regulation_code=o.regulation_code,
                checked=o.checked,
                changed=o.changed,
                affected_business_count=o.affected_business_count,
                error=o.error,
            )
            for o in result.outcomes
        ],
    )
