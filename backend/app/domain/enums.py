from __future__ import annotations

from enum import Enum


class UserRole(str, Enum):
    OWNER = "owner"
    CA = "ca"
    ADMIN = "admin"


class SectorType(str, Enum):
    MANUFACTURING = "manufacturing"
    TRADING = "trading"
    SERVICES = "services"
    OTHER = "other"


class BusinessLegalType(str, Enum):
    PROPRIETORSHIP = "proprietorship"
    PARTNERSHIP = "partnership"
    LLP = "llp"
    PRIVATE_LIMITED = "private_limited"
    PUBLIC_LIMITED = "public_limited"
    HUF = "huf"
    OTHER = "other"


class TurnoverBand(str, Enum):
    """Bucketed annual turnover, deliberately bounded at the exact rupee
    figures that matter to the Phase 1 rules (GST threshold, QRMP ceiling,
    Udyam classification ceilings) so a band boundary always corresponds to
    a real legal threshold rather than an arbitrary bucket.
    """

    UNDER_10L = "under_10l"
    L10_20L = "10l_20l"
    L20_40L = "20l_40l"
    L40L_5CR = "40l_5cr"
    CR5_50CR = "5cr_50cr"
    CR50_250CR = "50cr_250cr"
    ABOVE_250CR = "above_250cr"

    @property
    def min_inr(self) -> int:
        """Conservative lower bound of the band, in INR.

        Rules use this (rather than an unknown exact figure) to evaluate
        ">= threshold" conditions, so a business is only ever judged
        against the amount it has confirmed it has *at least*.
        """
        return {
            TurnoverBand.UNDER_10L: 0,
            TurnoverBand.L10_20L: 1_000_000,
            TurnoverBand.L20_40L: 2_000_000,
            TurnoverBand.L40L_5CR: 4_000_000,
            TurnoverBand.CR5_50CR: 50_000_000,
            TurnoverBand.CR50_250CR: 500_000_000,
            TurnoverBand.ABOVE_250CR: 2_500_000_000,
        }[self]

    @property
    def max_inr(self) -> int | None:
        """Upper bound of the band, in INR; None for the open-ended top band.

        Needed for "definitely at or under a ceiling" checks (e.g. QRMP
        quarterly-filing eligibility), which the lower-bound-only
        `min_inr` can't safely answer.
        """
        return {
            TurnoverBand.UNDER_10L: 1_000_000,
            TurnoverBand.L10_20L: 2_000_000,
            TurnoverBand.L20_40L: 4_000_000,
            TurnoverBand.L40L_5CR: 50_000_000,
            TurnoverBand.CR5_50CR: 500_000_000,
            TurnoverBand.CR50_250CR: 2_500_000_000,
            TurnoverBand.ABOVE_250CR: None,
        }[self]


class RegistrationType(str, Enum):
    GST = "gst"
    UDYAM = "udyam"
    SHOPS_ESTABLISHMENT = "shops_establishment"
    EPF = "epf"
    ESI = "esi"
    PROFESSIONAL_TAX = "professional_tax"
    OTHER = "other"


class RegistrationStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    EXPIRED = "expired"


class ObligationType(str, Enum):
    REGISTRATION = "registration"
    FILING = "filing"
    RENEWAL = "renewal"
    PAYMENT = "payment"


class ObligationFrequency(str, Enum):
    ONE_TIME = "one_time"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"


class ObligationApplicability(str, Enum):
    """Result of the deterministic rules engine for one business+rule pair."""

    APPLICABLE = "applicable"
    NOT_APPLICABLE = "not_applicable"
    REVIEW_REQUIRED = "review_required"


class ObligationStatus(str, Enum):
    """Due-date-derived status. Only meaningful when applicability is
    APPLICABLE or REVIEW_REQUIRED; this is a basic date computation, not
    the predictive risk model (that's Phase 3).
    """

    PENDING = "pending"
    DUE_SOON = "due_soon"
    OVERDUE = "overdue"
    COMPLETED = "completed"


class FilingStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


class DocumentType(str, Enum):
    ACT = "act"
    NOTIFICATION = "notification"
    CIRCULAR = "circular"
    FAQ = "faq"
    DEMO_EXCERPT = "demo_excerpt"
    OTHER = "other"


class SourceStatus(str, Enum):
    """How much to trust a RegulatoryDocument/Chunk as legal evidence.

    VERIFIED  -- ingested from an authoritative source with confirmed
                 verbatim/faithfully-paraphrased text (none yet in Phase 2 --
                 see backend/seed/regulatory_documents/README.md).
    DEMO      -- system-authored summary derived from Phase 1's verified
                 regulation metadata, clearly not verbatim statute text.
                 Everything currently seeded is DEMO.
    UNVERIFIED -- ingested but not yet reviewed; retrieval must never
                 surface these as evidence.
    """

    VERIFIED = "verified"
    DEMO = "demo"
    UNVERIFIED = "unverified"


class AlertType(str, Enum):
    """REGULATION_CHANGE is a global event (business_id is NULL -- relevance
    is computed via the Obligation join, not stored per-business).
    GROWTH_FORECAST is inherently per-business.
    """

    REGULATION_CHANGE = "regulation_change"
    GROWTH_FORECAST = "growth_forecast"


class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
