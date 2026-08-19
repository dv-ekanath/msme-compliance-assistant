"""widen filings.document_ref from VARCHAR(500) to Text

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-19

Root cause: `document_ref` was modeled in 0001 as a short VARCHAR(500)
reference/URL, but app/services/filings.py's generate_draft_document
stores the full deterministic draft document text there, which routinely
exceeds 500 chars. Live-verified against real Postgres: creating a filing
through POST /filings failed with StringDataRightTruncation (SQLite
doesn't enforce VARCHAR length, so this passed the test suite but failed
against real Postgres -- same class of bug 0002 fixed for
regulations.version). Widened to Text, matching that precedent.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "filings",
        "document_ref",
        existing_type=sa.String(500),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    # Reversible, but will fail if any stored draft exceeds 500 chars --
    # intentional, matching 0002's "loud failure over silent truncation".
    op.alter_column(
        "filings",
        "document_ref",
        existing_type=sa.Text(),
        type_=sa.String(500),
        existing_nullable=True,
    )
