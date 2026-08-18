from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import (
    ObligationApplicability,
    ObligationFrequency,
    ObligationStatus,
    ObligationType,
)
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Obligation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """One row per (business, rule) pair. Upserted on every
    /compliance/evaluate run rather than recreated, so a business's
    obligation history (status, completion) survives re-evaluation.
    """

    __tablename__ = "obligations"
    __table_args__ = (
        UniqueConstraint("business_id", "rule_id", name="uq_obligation_business_rule"),
    )

    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    regulation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("regulations.id"))

    rule_id: Mapped[str] = mapped_column(String(100), index=True)
    obligation_type: Mapped[ObligationType] = mapped_column(Enum(ObligationType, native_enum=False, length=20))
    title: Mapped[str] = mapped_column(String(255))
    reason: Mapped[str] = mapped_column(Text)

    frequency: Mapped[ObligationFrequency | None] = mapped_column(
        Enum(ObligationFrequency, native_enum=False, length=20), nullable=True
    )
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    applicability: Mapped[ObligationApplicability] = mapped_column(
        Enum(ObligationApplicability, native_enum=False, length=20)
    )
    status: Mapped[ObligationStatus] = mapped_column(
        Enum(ObligationStatus, native_enum=False, length=20), default=ObligationStatus.PENDING
    )

    # Reserved for the Phase 3 predictive risk model -- always NULL in
    # Phase 1, which only computes basic due-date status (see `status`).
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    last_evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    business: Mapped["Business"] = relationship(back_populates="obligations")  # noqa: F821
    regulation: Mapped["Regulation"] = relationship()  # noqa: F821

    @property
    def regulation_title(self) -> str:
        return self.regulation.title

    @property
    def regulation_source_url(self) -> str:
        return self.regulation.source_url
