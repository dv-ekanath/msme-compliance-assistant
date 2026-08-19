"""add users.hashed_password and the audit_logs table

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-19

Phase 5: users.hashed_password backs POST /auth/register + /auth/login
(app/core/security.py); audit_logs backs app/services/audit.py's
log_audit_event, wired into the new Filing approval workflow and
retrofitted into Phase 1-4's existing mutating routes (Business,
Registration, Obligation status, Alert acknowledge, compliance evaluate).

No changes needed to `filings` -- that table already has the exact shape
this phase needs, created in 0001_initial_schema.

Hand-written to match 0001-0004's convention (no live DB for autogenerate).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("hashed_password", sa.String(255), nullable=True))

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "actor_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
    )
    op.create_index("ix_audit_logs_entity", "audit_logs", ["entity_type", "entity_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_entity", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_column("users", "hashed_password")
