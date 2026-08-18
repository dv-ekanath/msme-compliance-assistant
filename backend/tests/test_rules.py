from __future__ import annotations

from app.domain.enums import (
    ObligationApplicability,
    ObligationFrequency,
    RegistrationStatus,
    RegistrationType,
    SectorType,
    TurnoverBand,
)
from app.domain.facts import RegistrationFact
from app.rules.epf import EpfApplicabilityRule, EpfMonthlyFilingRule
from app.rules.esi import EsiApplicabilityRule, EsiMonthlyFilingRule
from app.rules.gst import GstPeriodicFilingRule, GstRegistrationThresholdRule
from app.rules.professional_tax import ProfessionalTaxReviewRule
from app.rules.shops_establishment import ShopsEstablishmentRegistrationRule
from app.rules.udyam import UdyamRegistrationRule
from tests.conftest import make_facts

APPLICABLE = ObligationApplicability.APPLICABLE
NOT_APPLICABLE = ObligationApplicability.NOT_APPLICABLE
REVIEW_REQUIRED = ObligationApplicability.REVIEW_REQUIRED


def active(reg_type: RegistrationType) -> dict:
    return {reg_type: RegistrationFact(type=reg_type, status=RegistrationStatus.ACTIVE)}


# --- GST registration threshold -------------------------------------------------


def test_gst_registration_not_applicable_below_threshold(regulation_configs):
    facts = make_facts(sector=SectorType.TRADING, turnover_band=TurnoverBand.UNDER_10L)
    result = GstRegistrationThresholdRule().evaluate(facts, regulation_configs["GST"])
    assert result.applicability == NOT_APPLICABLE


def test_gst_registration_applicable_above_threshold_goods(regulation_configs):
    facts = make_facts(sector=SectorType.TRADING, turnover_band=TurnoverBand.L40L_5CR)
    result = GstRegistrationThresholdRule().evaluate(facts, regulation_configs["GST"])
    assert result.applicability == APPLICABLE


def test_gst_registration_applicable_above_threshold_services(regulation_configs):
    facts = make_facts(sector=SectorType.SERVICES, turnover_band=TurnoverBand.L20_40L)
    result = GstRegistrationThresholdRule().evaluate(facts, regulation_configs["GST"])
    assert result.applicability == APPLICABLE


def test_gst_registration_not_applicable_when_already_registered(regulation_configs):
    facts = make_facts(
        sector=SectorType.TRADING,
        turnover_band=TurnoverBand.ABOVE_250CR,
        registrations=active(RegistrationType.GST),
    )
    result = GstRegistrationThresholdRule().evaluate(facts, regulation_configs["GST"])
    assert result.applicability == NOT_APPLICABLE
    assert "already" in result.reason.lower()


def test_gst_registration_special_category_state_lowers_threshold(regulation_configs):
    # Config mechanism, not seed data: prove the threshold is genuinely
    # read from regulation config rather than hardcoded in the rule.
    cfg = regulation_configs["GST"]
    special_cfg = type(cfg)(
        id=cfg.id,
        code=cfg.code,
        title=cfg.title,
        authority=cfg.authority,
        source_url=cfg.source_url,
        applicability_rules={**cfg.applicability_rules, "special_category_states": ["Sikkim"]},
    )
    facts = make_facts(sector=SectorType.SERVICES, state="Sikkim", turnover_band=TurnoverBand.L10_20L)
    result = GstRegistrationThresholdRule().evaluate(facts, special_cfg)
    # 10L-20L band floor (Rs 1,000,000) is at/above the Rs 10L special
    # category services threshold, so this should now be applicable.
    assert result.applicability == APPLICABLE


# --- GST periodic filing ---------------------------------------------------------


def test_gst_filing_not_applicable_when_unregistered(regulation_configs):
    facts = make_facts(turnover_band=TurnoverBand.L40L_5CR)
    result = GstPeriodicFilingRule().evaluate(facts, regulation_configs["GST"])
    assert result.applicability == NOT_APPLICABLE
    assert result.due_date is None


def test_gst_filing_quarterly_when_within_qrmp_ceiling(regulation_configs):
    facts = make_facts(turnover_band=TurnoverBand.L40L_5CR, registrations=active(RegistrationType.GST))
    result = GstPeriodicFilingRule().evaluate(facts, regulation_configs["GST"])
    assert result.applicability == APPLICABLE
    assert result.frequency == ObligationFrequency.QUARTERLY
    assert result.due_date is not None


def test_gst_filing_monthly_when_above_qrmp_ceiling(regulation_configs):
    facts = make_facts(turnover_band=TurnoverBand.CR5_50CR, registrations=active(RegistrationType.GST))
    result = GstPeriodicFilingRule().evaluate(facts, regulation_configs["GST"])
    assert result.applicability == APPLICABLE
    assert result.frequency == ObligationFrequency.MONTHLY


# --- Udyam -------------------------------------------------------------------


def test_udyam_applicable_when_within_msme_ceiling(regulation_configs):
    facts = make_facts(turnover_band=TurnoverBand.L20_40L)
    result = UdyamRegistrationRule().evaluate(facts, regulation_configs["UDYAM"])
    assert result.applicability == APPLICABLE


def test_udyam_not_applicable_when_already_registered(regulation_configs):
    facts = make_facts(turnover_band=TurnoverBand.L20_40L, registrations=active(RegistrationType.UDYAM))
    result = UdyamRegistrationRule().evaluate(facts, regulation_configs["UDYAM"])
    assert result.applicability == NOT_APPLICABLE


def test_udyam_not_applicable_above_medium_ceiling(regulation_configs):
    facts = make_facts(turnover_band=TurnoverBand.ABOVE_250CR)
    result = UdyamRegistrationRule().evaluate(facts, regulation_configs["UDYAM"])
    assert result.applicability == NOT_APPLICABLE


# --- EPF -----------------------------------------------------------------------


def test_epf_not_applicable_below_threshold(regulation_configs):
    facts = make_facts(employee_count=5)
    result = EpfApplicabilityRule().evaluate(facts, regulation_configs["EPF"])
    assert result.applicability == NOT_APPLICABLE


def test_epf_applicable_at_threshold(regulation_configs):
    facts = make_facts(employee_count=20)
    result = EpfApplicabilityRule().evaluate(facts, regulation_configs["EPF"])
    assert result.applicability == APPLICABLE


def test_epf_not_applicable_when_already_registered(regulation_configs):
    facts = make_facts(employee_count=50, registrations=active(RegistrationType.EPF))
    result = EpfApplicabilityRule().evaluate(facts, regulation_configs["EPF"])
    assert result.applicability == NOT_APPLICABLE


def test_epf_filing_not_applicable_when_unregistered(regulation_configs):
    facts = make_facts(employee_count=50)
    result = EpfMonthlyFilingRule().evaluate(facts, regulation_configs["EPF"])
    assert result.applicability == NOT_APPLICABLE


def test_epf_filing_applicable_when_registered(regulation_configs):
    facts = make_facts(employee_count=50, registrations=active(RegistrationType.EPF))
    result = EpfMonthlyFilingRule().evaluate(facts, regulation_configs["EPF"])
    assert result.applicability == APPLICABLE
    assert result.frequency == ObligationFrequency.MONTHLY
    assert result.due_date is not None


# --- ESI -----------------------------------------------------------------------


def test_esi_not_applicable_below_threshold(regulation_configs):
    facts = make_facts(employee_count=3)
    result = EsiApplicabilityRule().evaluate(facts, regulation_configs["ESI"])
    assert result.applicability == NOT_APPLICABLE


def test_esi_applicable_at_threshold(regulation_configs):
    facts = make_facts(employee_count=10)
    result = EsiApplicabilityRule().evaluate(facts, regulation_configs["ESI"])
    assert result.applicability == APPLICABLE


def test_esi_not_applicable_when_already_registered(regulation_configs):
    facts = make_facts(employee_count=25, registrations=active(RegistrationType.ESI))
    result = EsiApplicabilityRule().evaluate(facts, regulation_configs["ESI"])
    assert result.applicability == NOT_APPLICABLE


def test_esi_filing_applicable_when_registered(regulation_configs):
    facts = make_facts(employee_count=25, registrations=active(RegistrationType.ESI))
    result = EsiMonthlyFilingRule().evaluate(facts, regulation_configs["ESI"])
    assert result.applicability == APPLICABLE
    assert result.due_date is not None


# --- Shops & Establishment (structure-only, no invented threshold) -------------


def test_shops_establishment_review_required_when_not_registered(regulation_configs):
    facts = make_facts()
    result = ShopsEstablishmentRegistrationRule().evaluate(facts, regulation_configs["SHOPS_ESTABLISHMENT"])
    assert result.applicability == REVIEW_REQUIRED


def test_shops_establishment_not_applicable_when_registered(regulation_configs):
    facts = make_facts(registrations=active(RegistrationType.SHOPS_ESTABLISHMENT))
    result = ShopsEstablishmentRegistrationRule().evaluate(facts, regulation_configs["SHOPS_ESTABLISHMENT"])
    assert result.applicability == NOT_APPLICABLE


# --- Professional Tax (structure-only, no invented slabs) ----------------------


def test_professional_tax_not_applicable_with_no_employees(regulation_configs):
    facts = make_facts(employee_count=0)
    result = ProfessionalTaxReviewRule().evaluate(facts, regulation_configs["PROFESSIONAL_TAX"])
    assert result.applicability == NOT_APPLICABLE


def test_professional_tax_review_required_with_employees(regulation_configs):
    facts = make_facts(employee_count=5)
    result = ProfessionalTaxReviewRule().evaluate(facts, regulation_configs["PROFESSIONAL_TAX"])
    assert result.applicability == REVIEW_REQUIRED
