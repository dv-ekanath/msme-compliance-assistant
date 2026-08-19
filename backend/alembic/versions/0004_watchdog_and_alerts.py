"""add watchdog scan state to regulations, and the alerts table

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-19

Phase 3: `regulations.content_hash`/`last_checked_at` let the watchdog scan
(app/watchdog/scanner.py) detect changes at each Regulation's live
source_url between scans -- distinct from RegulatoryDocument.content_hash
(0003), which tracks re-ingestion of the static local demo corpus, not the
live government page. `alerts` holds both REGULATION_CHANGE (global,
business_id NULL) and GROWTH_FORECAST (per-business) signals.

Hand-written to match 0001-0003's convention (no live DB for autogenerate).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from app.domain.enums import AlertSeverity, AlertType

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("regulations", sa.Column("content_hash", sa.String(64), nullable=True))
    op.add_column(
        "regulations", sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True)
    )

    op.create_table(
        "alerts",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("alert_type", sa.Enum(AlertType, native_enum=False, length=20), nullable=False),
        sa.Column(
            "business_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("businesses.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "regulation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("regulations.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "obligation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("obligations.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("severity", sa.Enum(AlertSeverity, native_enum=False, length=20), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_alerts_business_id", "alerts", ["business_id"])
    op.create_index("ix_alerts_regulation_id", "alerts", ["regulation_id"])


def downgrade() -> None:
    op.drop_index("ix_alerts_regulation_id", table_name="alerts")
    op.drop_index("ix_alerts_business_id", table_name="alerts")
    op.drop_table("alerts")

    op.drop_column("regulations", "last_checked_at")
    op.drop_column("regulations", "content_hash")
