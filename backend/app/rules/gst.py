from __future__ import annotations

from datetime import date

from app.domain.enums import (
    ObligationApplicability,
    ObligationFrequency,
    ObligationType,
    RegistrationType,
    SectorType,
)
from app.domain.facts import BusinessFacts
from app.rules.base import Rule
from app.rules.dates import periodic_due_date
from app.rules.types import RegulationConfig, RuleResult


class GstRegistrationThresholdRule(Rule):
    """CGST Act 2017, Section 22 -- compulsory registration once aggregate
    turnover crosses the goods/services threshold. Special-category-state
    thresholds are configurable via `regulation.applicability_rules` but
    the seeded `special_category_states` list starts empty (unverified) --
    see backend/seed/regulations/gst.json.
    """

    rule_id = "gst_registration_threshold"
    regulation_code = "GST"

    def evaluate(self, facts: BusinessFacts, regulation: RegulationConfig) -> RuleResult:
        if facts.has_active_registration(RegistrationType.GST):
            return RuleResult(
                rule_id=self.rule_id,
                regulation_code=self.regulation_code,
                applicability=ObligationApplicability.NOT_APPLICABLE,
                reason="Business already has an active GST registration on file.",
                obligation_type=ObligationType.REGISTRATION,
                title="GST Registration",
                frequency=ObligationFrequency.ONE_TIME,
            )

        cfg = regulation.applicability_rules
        is_services = facts.sector == SectorType.SERVICES
        special_states = cfg.get("special_category_states", [])

        if facts.state in special_states:
            threshold = cfg["special_category_services_threshold_inr" if is_services else "special_category_goods_threshold_inr"]
            category_note = " (special category state)"
        else:
            threshold = cfg["services_threshold_inr" if is_services else "goods_threshold_inr"]
            category_note = ""

        turnover_floor = facts.turnover_band.min_inr
        business_kind = "services" if is_services else "goods/trading"

        if turnover_floor >= threshold:
            return RuleResult(
                rule_id=self.rule_id,
                regulation_code=self.regulation_code,
                applicability=ObligationApplicability.APPLICABLE,
                reason=(
                    f"Annual turnover band '{facts.turnover_band.value}' is at or above the "
                    f"₹{threshold:,} GST registration threshold for {business_kind} "
                    f"businesses{category_note} (CGST Act 2017, Section 22)."
                ),
                obligation_type=ObligationType.REGISTRATION,
                title="GST Registration",
                frequency=ObligationFrequency.ONE_TIME,
            )

        return RuleResult(
            rule_id=self.rule_id,
            regulation_code=self.regulation_code,
            applicability=ObligationApplicability.NOT_APPLICABLE,
            reason=(
                f"Annual turnover band '{facts.turnover_band.value}' is below the "
                f"₹{threshold:,} GST registration threshold for {business_kind} businesses{category_note}."
            ),
            obligation_type=ObligationType.REGISTRATION,
            title="GST Registration",
            frequency=ObligationFrequency.ONE_TIME,
        )


class GstPeriodicFilingRule(Rule):
    """Once GST-registered, periodic GSTR-3B return filing is required --
    quarterly under the QRMP scheme if turnover is confidently within the
    configured ceiling, monthly otherwise. Exact statutory due dates
    (20th/22nd/24th depending on scheme and state group) vary; this uses a
    configurable day-offset approximation -- verify against gst.gov.in.
    """

    rule_id = "gst_periodic_filing"
    regulation_code = "GST"

    def evaluate(self, facts: BusinessFacts, regulation: RegulationConfig) -> RuleResult:
        if not facts.has_active_registration(RegistrationType.GST):
            return RuleResult(
                rule_id=self.rule_id,
                regulation_code=self.regulation_code,
                applicability=ObligationApplicability.NOT_APPLICABLE,
                reason="No active GST registration on file; periodic return filing applies only once registered.",
                obligation_type=ObligationType.FILING,
                title="GST Periodic Return Filing",
                frequency=None,
            )

        cfg = regulation.applicability_rules
        ceiling = cfg["quarterly_filing_turnover_ceiling_inr"]
        band_max = facts.turnover_band.max_inr
        is_quarterly = band_max is not None and band_max <= ceiling

        frequency = ObligationFrequency.QUARTERLY if is_quarterly else ObligationFrequency.MONTHLY
        deadline_days = cfg[
            "quarterly_filing_deadline_days_after_period_end"
            if is_quarterly
            else "monthly_filing_deadline_days_after_period_end"
        ]
        due_date: date = periodic_due_date(date.today(), frequency, deadline_days)

        return RuleResult(
            rule_id=self.rule_id,
            regulation_code=self.regulation_code,
            applicability=ObligationApplicability.APPLICABLE,
            reason=(
                f"Active GST registration requires {frequency.value} GSTR-3B return filing "
                f"(QRMP scheme eligibility computed from turnover band vs. ₹{ceiling:,} ceiling; "
                "exact statutory due date is an approximation -- verify on gst.gov.in)."
            ),
            obligation_type=ObligationType.FILING,
            title="GST Periodic Return Filing",
            frequency=frequency,
            due_date=due_date,
        )
