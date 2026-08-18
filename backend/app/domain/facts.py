from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from app.domain.enums import (
    BusinessLegalType,
    RegistrationStatus,
    RegistrationType,
    SectorType,
    TurnoverBand,
)


@dataclass(frozen=True)
class RegistrationFact:
    type: RegistrationType
    status: RegistrationStatus
    valid_to: date | None = None

    @property
    def is_active(self) -> bool:
        return self.status == RegistrationStatus.ACTIVE


@dataclass(frozen=True)
class BusinessFacts:
    """Plain, DB-independent snapshot of a business's structured state.

    This -- not the LLM, not the raw ORM objects -- is what the rules
    engine evaluates against. Built once per evaluation by
    `app.services.twin.build_business_facts`.
    """

    business_id: str
    name: str
    sector: SectorType
    state: str
    legal_type: BusinessLegalType
    turnover_band: TurnoverBand
    employee_count: int
    incorporation_date: date | None
    registrations: dict[RegistrationType, RegistrationFact] = field(default_factory=dict)

    def registration(self, reg_type: RegistrationType) -> RegistrationFact | None:
        return self.registrations.get(reg_type)

    def has_active_registration(self, reg_type: RegistrationType) -> bool:
        fact = self.registrations.get(reg_type)
        return fact is not None and fact.is_active
