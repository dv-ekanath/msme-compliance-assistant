from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import FilingStatus
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

MOCK_SUBMISSION_NOTICE = (
    "This is a simulated submission to a government portal -- no real filing occurred."
)


class Filing(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Phase 5 human-in-the-loop submission/approval workflow -- see
    app/services/filings.py for the state machine
    (DRAFT -> APPROVED|REJECTED -> (if APPROVED) SUBMITTED) and
    app/api/routes/filings.py for the HTTP surface.
    """

    __tablename__ = "filings"

    obligation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("obligations.id", ondelete="CASCADE"))
    period: Mapped[str | None] = mapped_column(String(20), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[FilingStatus] = mapped_column(
        Enum(FilingStatus, native_enum=False, length=20), default=FilingStatus.DRAFT
    )
    # Reused for both approval and rejection (records *who decided*, not
    # just who approved) -- keeps the schema additive rather than needing
    # a second nullable FK column for a rejecter.
    human_approved_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    # Widened from VARCHAR(500) in 0006 -- holds the full deterministic
    # draft document text (app/services/filings.py's generate_draft_document),
    # not just a short reference/URL, and can exceed 500 chars.
    document_ref: Mapped[str | None] = mapped_column(Text, nullable=True)

    obligation: Mapped["Obligation"] = relationship()  # noqa: F821

    @property
    def obligation_title(self) -> str:
        return self.obligation.title

    @property
    def business_id(self) -> uuid.UUID:
        return self.obligation.business_id

    @property
    def mock(self) -> bool:
        return self.status == FilingStatus.SUBMITTED

    @property
    def mock_notice(self) -> str | None:
        """Present on every read of a SUBMITTED filing -- not just the
        one-time submit response -- so the mock disclosure (CLAUDE.md rule
        5: "clearly labeled") survives a page reload or a direct GET, not
        only the initial POST /submit response.
        """
        return MOCK_SUBMISSION_NOTICE if self.mock else None
