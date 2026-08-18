from __future__ import annotations

from app.rules.base import Rule
from app.rules.epf import EpfApplicabilityRule, EpfMonthlyFilingRule
from app.rules.esi import EsiApplicabilityRule, EsiMonthlyFilingRule
from app.rules.gst import GstPeriodicFilingRule, GstRegistrationThresholdRule
from app.rules.professional_tax import ProfessionalTaxReviewRule
from app.rules.shops_establishment import ShopsEstablishmentRegistrationRule
from app.rules.udyam import UdyamRegistrationRule

ALL_RULES: list[Rule] = [
    GstRegistrationThresholdRule(),
    GstPeriodicFilingRule(),
    UdyamRegistrationRule(),
    EpfApplicabilityRule(),
    EpfMonthlyFilingRule(),
    EsiApplicabilityRule(),
    EsiMonthlyFilingRule(),
    ShopsEstablishmentRegistrationRule(),
    ProfessionalTaxReviewRule(),
]

REGULATION_CODES: set[str] = {rule.regulation_code for rule in ALL_RULES}
