from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AuditLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Who did what, to what, and when -- see app/services/audit.py's
    log_audit_event(). Covers human-triggered state changes, not
    system/scheduled ones (e.g. the watchdog's automatic Alert creation
    isn't logged here -- there's no human actor to attribute it to, and
    it's already visible via the Alert table itself).
    """

    __tablename__ = "audit_logs"

    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(100))
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True))
    detail: Mapped[str] = mapped_column(Text)
