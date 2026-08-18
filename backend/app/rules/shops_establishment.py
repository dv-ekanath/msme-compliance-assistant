from __future__ import annotations

from app.domain.enums import ObligationApplicability, ObligationFrequency, ObligationType, RegistrationType
from app.domain.facts import BusinessFacts
from app.rules.base import Rule
from app.rules.types import RegulationConfig, RuleResult


class ShopsEstablishmentRegistrationRule(Rule):
    """Shops & Establishment Acts are state legislation with widely
    varying thresholds and exemptions -- we do not have verified
    per-state rules yet. Per the Phase 1 scope, this rule never asserts a
    fabricated threshold: it returns REVIEW_REQUIRED rather than guessing
    applicable/not_applicable. Jurisdiction-specific config is the
    documented gap -- see backend/seed/regulations/shops_establishment.json.
    """

    rule_id = "shops_establishment_registration"
    regulation_code = "SHOPS_ESTABLISHMENT"

    def evaluate(self, facts: BusinessFacts, regulation: RegulationConfig) -> RuleResult:
        if facts.has_active_registration(RegistrationType.SHOPS_ESTABLISHMENT):
            return RuleResult(
                rule_id=self.rule_id,
                regulation_code=self.regulation_code,
                applicability=ObligationApplicability.NOT_APPLICABLE,
                reason="Business already has an active Shops & Establishment registration on file.",
                obligation_type=ObligationType.REGISTRATION,
                title="Shops & Establishment Registration",
                frequency=ObligationFrequency.ONE_TIME,
            )

        return RuleResult(
            rule_id=self.rule_id,
            regulation_code=self.regulation_code,
            applicability=ObligationApplicability.REVIEW_REQUIRED,
            reason=(
                f"Shops & Establishment registration is administered by {facts.state or 'your state'}'s "
                "labour department and requirements (threshold, exemptions, renewal cycle) vary by "
                "state. This cannot be determined automatically yet -- manual review required "
                "against your state's Act."
            ),
            obligation_type=ObligationType.REGISTRATION,
            title="Shops & Establishment Registration",
        )
