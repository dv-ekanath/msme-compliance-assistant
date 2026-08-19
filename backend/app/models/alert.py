from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import AlertSeverity, AlertType
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Alert(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A surfaced signal for a business owner: either a REGULATION_CHANGE
    (global event -- business_id is NULL, relevance to a given business is
    computed via the Obligation join at read time, see
    app/services/alerts.py) or a GROWTH_FORECAST (inherently per-business --
    business.employee_count is approaching a regulation's threshold before
    the obligation is actually APPLICABLE yet).
    """

    __tablename__ = "alerts"

    alert_type: Mapped[AlertType] = mapped_column(Enum(AlertType, native_enum=False, length=20))
    business_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), nullable=True, index=True
    )
    regulation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("regulations.id", ondelete="CASCADE"), nullable=True, index=True
    )
    obligation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("obligations.id", ondelete="CASCADE"), nullable=True
    )

    severity: Mapped[AlertSeverity] = mapped_column(Enum(AlertSeverity, native_enum=False, length=20))
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)

    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    regulation: Mapped["Regulation | None"] = relationship()  # noqa: F821

    @property
    def regulation_title(self) -> str | None:
        return self.regulation.title if self.regulation else None

    @property
    def regulation_source_url(self) -> str | None:
        return self.regulation.source_url if self.regulation else None
