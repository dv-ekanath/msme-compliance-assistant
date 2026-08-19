from __future__ import annotations

import uuid

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import UserRole
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Exposed via /auth (Phase 5) -- see app/api/routes/auth.py,
    app/core/security.py. Also what Filing.human_approved_by points to.
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, native_enum=False, length=20))
    business_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("businesses.id", ondelete="SET NULL"), nullable=True
    )
    # Nullable at the column level only because the column must exist
    # before any row does; POST /auth/register always populates it.
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
