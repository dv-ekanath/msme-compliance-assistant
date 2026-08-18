from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import FilingStatus
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Filing(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Schema readiness for the Phase 5 submission/approval workflow.
    Not populated or exposed via any API in Phase 1.
    """

    __tablename__ = "filings"

    obligation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("obligations.id", ondelete="CASCADE"))
    period: Mapped[str | None] = mapped_column(String(20), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[FilingStatus] = mapped_column(
        Enum(FilingStatus, native_enum=False, length=20), default=FilingStatus.DRAFT
    )
    human_approved_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    document_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)
