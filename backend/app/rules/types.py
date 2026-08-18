from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date

from app.domain.enums import ObligationApplicability, ObligationFrequency, ObligationType


@dataclass(frozen=True)
class RegulationConfig:
    """Read-only view of a Regulation row, as rules see it.

    Keeping this a plain dataclass (rather than passing the SQLAlchemy
    model in) means rule code -- and its tests -- never touch the ORM or a
    DB session, only configuration data. `id` is kept as a real uuid.UUID
    (not stringified) so callers can assign it straight into an
    Obligation.regulation_id FK without a type mismatch.
    """

    id: uuid.UUID
    code: str
    title: str
    authority: str
    source_url: str
    applicability_rules: dict


@dataclass(frozen=True)
class RuleResult:
    """The deterministic, explainable output of one rule for one business.

    Every field a citation-grounded UI needs is here already -- the
    frontend checklist and the /compliance/evaluate response both read
    straight off this, no LLM involved.
    """

    rule_id: str
    regulation_code: str
    applicability: ObligationApplicability
    reason: str
    obligation_type: ObligationType
    title: str
    frequency: ObligationFrequency | None = None
    due_date: date | None = None
