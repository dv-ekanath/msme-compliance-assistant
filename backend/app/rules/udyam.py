from __future__ import annotations

from app.domain.enums import ObligationApplicability, ObligationFrequency, ObligationType, RegistrationType
from app.domain.facts import BusinessFacts
from app.rules.base import Rule
from app.rules.types import RegulationConfig, RuleResult


class UdyamRegistrationRule(Rule):
    """Udyam registration is not compulsory the way GST is, but is required
    to claim statutory MSME benefits (Ministry of MSME). Eligibility is
    officially based on both investment and turnover; this rule only
    models the turnover ceiling (Business has no investment field yet) --
    see the caveat in the seeded regulation notes.
    """

    rule_id = "udyam_registration"
    regulation_code = "UDYAM"

    def evaluate(self, facts: BusinessFacts, regulation: RegulationConfig) -> RuleResult:
        if facts.has_active_registration(RegistrationType.UDYAM):
            return RuleResult(
                rule_id=self.rule_id,
                regulation_code=self.regulation_code,
                applicability=ObligationApplicability.NOT_APPLICABLE,
                reason="Business already has an active Udyam registration on file.",
                obligation_type=ObligationType.REGISTRATION,
                title="Udyam Registration",
                frequency=ObligationFrequency.ONE_TIME,
            )

        medium_ceiling = regulation.applicability_rules["medium_turnover_ceiling_inr"]
        turnover_floor = facts.turnover_band.min_inr

        if turnover_floor < medium_ceiling:
            return RuleResult(
                rule_id=self.rule_id,
                regulation_code=self.regulation_code,
                applicability=ObligationApplicability.APPLICABLE,
                reason=(
                    f"Turnover band '{facts.turnover_band.value}' is within MSME classification "
                    "ceilings. Udyam registration is recommended to access statutory MSME benefits "
                    "(investment-based criteria not modeled yet -- verify full eligibility on "
                    "udyamregistration.gov.in)."
                ),
                obligation_type=ObligationType.REGISTRATION,
                title="Udyam Registration",
                frequency=ObligationFrequency.ONE_TIME,
            )

        return RuleResult(
            rule_id=self.rule_id,
            regulation_code=self.regulation_code,
            applicability=ObligationApplicability.NOT_APPLICABLE,
            reason=(
                f"Turnover band '{facts.turnover_band.value}' is at or above the "
                f"₹{medium_ceiling:,} Medium-enterprise ceiling; not eligible for Udyam "
                "registration as an MSME."
            ),
            obligation_type=ObligationType.REGISTRATION,
            title="Udyam Registration",
            frequency=ObligationFrequency.ONE_TIME,
        )
