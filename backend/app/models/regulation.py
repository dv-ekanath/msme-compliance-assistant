from __future__ import annotations

from datetime import date

from sqlalchemy import Date, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Regulation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A citable regulation. `applicability_rules` holds the configurable
    thresholds Phase 1 rule implementations read from -- values live here,
    not hardcoded in Python, so they can be corrected/tuned without a code
    change. See backend/seed/regulations/ for the seeded content and
    backend/app/rules/ for the code that consumes it.
    """

    __tablename__ = "regulations"

    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    authority: Mapped[str] = mapped_column(String(255))
    jurisdiction: Mapped[str] = mapped_column(String(50))
    applicability_rules: Mapped[dict] = mapped_column(JSON, default=dict)
    source_url: Mapped[str] = mapped_column(String(500))
    effective_date: Mapped[date] = mapped_column(Date)
    # Not a short semver tag -- seed data uses this for a citation/version
    # description that includes verification caveats (e.g. "CGST Act 2017,
    # Section 22 (paraphrased; verify current notifications)"), so it needs
    # the same unbounded Text as `notes`, not an arbitrary VARCHAR cap.
    version: Mapped[str] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
