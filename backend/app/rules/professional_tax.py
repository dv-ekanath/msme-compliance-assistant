from __future__ import annotations

from app.domain.enums import ObligationApplicability, ObligationType
from app.domain.facts import BusinessFacts
from app.rules.base import Rule
from app.rules.types import RegulationConfig, RuleResult


class ProfessionalTaxReviewRule(Rule):
    """Professional Tax is levied by some states (e.g. Maharashtra,
    Karnataka, West Bengal) and not others (e.g. Delhi, Haryana), with
    state-specific salary slabs -- we do not have verified per-state slab
    data yet. Per the Phase 1 scope, this never asserts a fabricated
    slab/threshold: it gates only on "any employees at all" and otherwise
    returns REVIEW_REQUIRED. See backend/seed/regulations/professional_tax.json.
    """

    rule_id = "professional_tax_review"
    regulation_code = "PROFESSIONAL_TAX"

    def evaluate(self, facts: BusinessFacts, regulation: RegulationConfig) -> RuleResult:
        if facts.employee_count < 1:
            return RuleResult(
                rule_id=self.rule_id,
                regulation_code=self.regulation_code,
                applicability=ObligationApplicability.NOT_APPLICABLE,
                reason="No employees on record; Professional Tax employer-deduction obligations are not triggered.",
                obligation_type=ObligationType.PAYMENT,
                title="Professional Tax",
            )

        return RuleResult(
            rule_id=self.rule_id,
            regulation_code=self.regulation_code,
            applicability=ObligationApplicability.REVIEW_REQUIRED,
            reason=(
                f"Professional Tax applies only in certain states with state-specific salary "
                f"slabs; applicability for {facts.state or 'your state'} could not be determined "
                "automatically. Manual review required."
            ),
            obligation_type=ObligationType.PAYMENT,
            title="Professional Tax",
        )
