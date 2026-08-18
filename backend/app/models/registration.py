from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import RegistrationStatus, RegistrationType
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Registration(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "registrations"
    __table_args__ = (
        UniqueConstraint("business_id", "type", name="uq_registration_business_type"),
    )

    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    type: Mapped[RegistrationType] = mapped_column(Enum(RegistrationType, native_enum=False, length=30))
    number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[RegistrationStatus] = mapped_column(
        Enum(RegistrationStatus, native_enum=False, length=20), default=RegistrationStatus.ACTIVE
    )
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    document_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)

    business: Mapped["Business"] = relationship(back_populates="registrations")  # noqa: F821
