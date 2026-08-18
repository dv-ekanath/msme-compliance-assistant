from __future__ import annotations

from datetime import date

from app.domain.enums import ObligationApplicability, ObligationFrequency, ObligationType, RegistrationType
from app.domain.facts import BusinessFacts
from app.rules.base import Rule
from app.rules.dates import periodic_due_date
from app.rules.types import RegulationConfig, RuleResult


class EpfApplicabilityRule(Rule):
    """EPF & Miscellaneous Provisions Act 1952, Section 1(3) -- applies to
    establishments employing 20 or more persons.
    """

    rule_id = "epf_applicability"
    regulation_code = "EPF"

    def evaluate(self, facts: BusinessFacts, regulation: RegulationConfig) -> RuleResult:
        if facts.has_active_registration(RegistrationType.EPF):
            return RuleResult(
                rule_id=self.rule_id,
                regulation_code=self.regulation_code,
                applicability=ObligationApplicability.NOT_APPLICABLE,
                reason="Business already has an active EPF registration on file.",
                obligation_type=ObligationType.REGISTRATION,
                title="EPF Registration",
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
                    f"{threshold}-employee EPF applicability threshold (EPF & MP Act 1952, "
                    "Section 1(3))."
                ),
                obligation_type=ObligationType.REGISTRATION,
                title="EPF Registration",
                frequency=ObligationFrequency.ONE_TIME,
            )

        return RuleResult(
            rule_id=self.rule_id,
            regulation_code=self.regulation_code,
            applicability=ObligationApplicability.NOT_APPLICABLE,
            reason=f"Employee count ({facts.employee_count}) is below the {threshold}-employee EPF applicability threshold.",
            obligation_type=ObligationType.REGISTRATION,
            title="EPF Registration",
            frequency=ObligationFrequency.ONE_TIME,
        )


class EpfMonthlyFilingRule(Rule):
    """Once EPF-registered, monthly Electronic Challan-cum-Return (ECR)
    filing is required. Exact statutory due date verified against
    epfindia.gov.in; this uses a configurable day-offset approximation.
    """

    rule_id = "epf_monthly_filing"
    regulation_code = "EPF"

    def evaluate(self, facts: BusinessFacts, regulation: RegulationConfig) -> RuleResult:
        if not facts.has_active_registration(RegistrationType.EPF):
            return RuleResult(
                rule_id=self.rule_id,
                regulation_code=self.regulation_code,
                applicability=ObligationApplicability.NOT_APPLICABLE,
                reason="No active EPF registration on file; monthly filing applies only once registered.",
                obligation_type=ObligationType.FILING,
                title="EPF Monthly Filing (ECR)",
                frequency=None,
            )

        deadline_days = regulation.applicability_rules["filing_deadline_days_after_period_end"]
        due_date: date = periodic_due_date(date.today(), ObligationFrequency.MONTHLY, deadline_days)

        return RuleResult(
            rule_id=self.rule_id,
            regulation_code=self.regulation_code,
            applicability=ObligationApplicability.APPLICABLE,
            reason=(
                "Active EPF registration requires monthly Electronic Challan-cum-Return (ECR) "
                "filing (approximate statutory deadline -- verify on epfindia.gov.in)."
            ),
            obligation_type=ObligationType.FILING,
            title="EPF Monthly Filing (ECR)",
            frequency=ObligationFrequency.MONTHLY,
            due_date=due_date,
        )
