from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import BusinessLegalType, SectorType, TurnoverBand
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Business(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "businesses"

    name: Mapped[str] = mapped_column(String(255))
    sector: Mapped[SectorType] = mapped_column(Enum(SectorType, native_enum=False, length=20))
    state: Mapped[str] = mapped_column(String(100))
    registration_type: Mapped[BusinessLegalType] = mapped_column(
        Enum(BusinessLegalType, native_enum=False, length=20)
    )
    turnover_band: Mapped[TurnoverBand] = mapped_column(Enum(TurnoverBand, native_enum=False, length=20))
    employee_count: Mapped[int] = mapped_column(Integer, default=0)
    incorporation_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    udyam_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    gstin: Mapped[str | None] = mapped_column(String(20), nullable=True)
    pan: Mapped[str | None] = mapped_column(String(20), nullable=True)

    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    registrations: Mapped[list["Registration"]] = relationship(  # noqa: F821
        back_populates="business", cascade="all, delete-orphan"
    )
    obligations: Mapped[list["Obligation"]] = relationship(  # noqa: F821
        back_populates="business", cascade="all, delete-orphan"
    )
