from __future__ import annotations

from datetime import date

from app.domain.enums import ObligationApplicability, ObligationFrequency, ObligationType, RegistrationType
from app.domain.facts import BusinessFacts
from app.rules.base import Rule
from app.rules.dates import periodic_due_date
from app.rules.types import RegulationConfig, RuleResult


class EsiApplicabilityRule(Rule):
    """ESI Act 1948 -- applies to non-seasonal establishments employing 10
    or more persons in most states/UTs (the threshold was historically 20
    and has been reduced to 10 in most, but not necessarily all,
    jurisdictions -- flagged in the seeded regulation notes).
    """

    rule_id = "esi_applicability"
    regulation_code = "ESI"

    def evaluate(self, facts: BusinessFacts, regulation: RegulationConfig) -> RuleResult:
        if facts.has_active_registration(RegistrationType.ESI):
            return RuleResult(
                rule_id=self.rule_id,
                regulation_code=self.regulation_code,
                applicability=ObligationApplicability.NOT_APPLICABLE,
                reason="Business already has an active ESI registration on file.",
                obligation_type=ObligationType.REGISTRATION,
                title="ESI Registration",
                frequency=ObligationFrequency.ONE_TIME,
            )

        threshold = regulation.applicability_rules["min_employee_count"]
        if facts.employee_count >= threshold:
            return RuleResult(
                rule_id=self.rule_id,
                regulation_code=self.regulation_code,
                applicability=ObligationApplicability.APPLICABLE,
                reason=(
                    f"Employee count ({facts.employee_count}) meets or exceeds the "
                    f"{threshold}-employee ESI applicability threshold used in most states/UTs "
                    "(ESI Act 1948) -- confirm your state has not retained a higher threshold "
                    "for your establishment type."
                ),
                obligation_type=ObligationType.REGISTRATION,
                title="ESI Registration",
                frequency=ObligationFrequency.ONE_TIME,
            )

        return RuleResult(
            rule_id=self.rule_id,
            regulation_code=self.regulation_code,
            applicability=ObligationApplicability.NOT_APPLICABLE,
            reason=f"Employee count ({facts.employee_count}) is below the {threshold}-employee ESI applicability threshold.",
            obligation_type=ObligationType.REGISTRATION,
            title="ESI Registration",
            frequency=ObligationFrequency.ONE_TIME,
        )


class EsiMonthlyFilingRule(Rule):
    """Once ESI-registered, monthly contribution filing/payment is
    required. Exact statutory due date verified against esic.gov.in; this
    uses a configurable day-offset approximation.
    """

    rule_id = "esi_monthly_filing"
    regulation_code = "ESI"

    def evaluate(self, facts: BusinessFacts, regulation: RegulationConfig) -> RuleResult:
        if not facts.has_active_registration(RegistrationType.ESI):
            return RuleResult(
                rule_id=self.rule_id,
                regulation_code=self.regulation_code,
                applicability=ObligationApplicability.NOT_APPLICABLE,
                reason="No active ESI registration on file; monthly filing applies only once registered.",
                obligation_type=ObligationType.FILING,
                title="ESI Monthly Contribution Filing",
                frequency=None,
            )

        deadline_days = regulation.applicability_rules["filing_deadline_days_after_period_end"]
        due_date: date = periodic_due_date(date.today(), ObligationFrequency.MONTHLY, deadline_days)

        return RuleResult(
            rule_id=self.rule_id,
            regulation_code=self.regulation_code,
            applicability=ObligationApplicability.APPLICABLE,
            reason=(
                "Active ESI registration requires monthly contribution filing and payment "
                "(approximate statutory deadline -- verify on esic.gov.in)."
            ),
            obligation_type=ObligationType.FILING,
            title="ESI Monthly Contribution Filing",
            frequency=ObligationFrequency.MONTHLY,
            due_date=due_date,
        )
