from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.domain.enums import AlertSeverity, AlertType, ObligationApplicability
from app.models.alert import Alert
from app.models.obligation import Obligation
from app.models.regulation import Regulation


@dataclass(frozen=True)
class RegulationScanOutcome:
    regulation_code: str
    checked: bool
    changed: bool
    affected_business_count: int
    error: str | None = None


@dataclass(frozen=True)
class WatchdogScanResult:
    outcomes: list[RegulationScanOutcome]

    @property
    def regulations_checked(self) -> int:
        return sum(1 for o in self.outcomes if o.checked)

    @property
    def changes_detected(self) -> int:
        return sum(1 for o in self.outcomes if o.changed)

    @property
    def alerts_created(self) -> int:
        return self.changes_detected


def _count_affected_businesses(db: Session, regulation_id: uuid.UUID) -> int:
    """Business->Obligation->Regulation *is* the knowledge graph per
    CLAUDE.md rule 2 -- affected-business matching is this join, not a
    separate graph store or an LLM call (rule 4).
    """
    return (
        db.query(Obligation)
        .filter(
            Obligation.regulation_id == regulation_id,
            Obligation.applicability == ObligationApplicability.APPLICABLE,
        )
        .count()
    )


def scan_regulations(db: Session, http_client: httpx.Client | None = None) -> WatchdogScanResult:
    """Fetches each seeded Regulation's source_url, hashes the response,
    and compares to the last-stored hash. A regulation's first-ever check
    (content_hash is None) just baselines -- it is not counted as a change.

    A network error for one regulation is recorded on its outcome and does
    not abort the rest of the scan -- government sites can be flaky, and
    this is real code making real requests (CLAUDE.md rule 5), not a stub,
    so it needs to tolerate that.
    """
    owns_client = http_client is None
    client = http_client or httpx.Client(timeout=10.0, follow_redirects=True)

    now = datetime.now(timezone.utc)
    outcomes: list[RegulationScanOutcome] = []

    try:
        regulations = db.query(Regulation).order_by(Regulation.code).all()
        for regulation in regulations:
            try:
                response = client.get(regulation.source_url)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                outcomes.append(
                    RegulationScanOutcome(
                        regulation_code=regulation.code,
                        checked=False,
                        changed=False,
                        affected_business_count=0,
                        error=str(exc),
                    )
                )
                continue

            new_hash = hashlib.sha256(response.content).hexdigest()
            previous_hash = regulation.content_hash
            regulation.content_hash = new_hash
            regulation.last_checked_at = now

            changed = previous_hash is not None and previous_hash != new_hash
            affected_count = 0

            if changed:
                affected_count = _count_affected_businesses(db, regulation.id)
                db.add(
                    Alert(
                        alert_type=AlertType.REGULATION_CHANGE,
                        business_id=None,
                        regulation_id=regulation.id,
                        severity=AlertSeverity.HIGH if affected_count > 0 else AlertSeverity.MEDIUM,
                        title=f"{regulation.title} may have changed",
                        message=(
                            f"The content at {regulation.source_url} changed since the last check. "
                            f"{affected_count} business(es) currently have an applicable obligation "
                            "under this regulation and may be affected. Re-verify before relying on "
                            "citations from this source."
                        ),
                        detected_at=now,
                    )
                )

            outcomes.append(
                RegulationScanOutcome(
                    regulation_code=regulation.code,
                    checked=True,
                    changed=changed,
                    affected_business_count=affected_count,
                )
            )

        db.commit()
    finally:
        if owns_client:
            client.close()

    return WatchdogScanResult(outcomes=outcomes)
