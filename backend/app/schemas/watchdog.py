from __future__ import annotations

from pydantic import BaseModel


class RegulationScanOutcomeRead(BaseModel):
    regulation_code: str
    checked: bool
    changed: bool
    affected_business_count: int
    error: str | None


class WatchdogScanSummary(BaseModel):
    regulations_checked: int
    changes_detected: int
    alerts_created: int
    outcomes: list[RegulationScanOutcomeRead]
