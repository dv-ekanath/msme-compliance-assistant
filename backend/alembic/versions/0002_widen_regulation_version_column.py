"""widen regulations.version from VARCHAR(20) to Text

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-19

Root cause: `version` was modeled as a short VARCHAR(20) semver-style tag,
but the seeded regulation data actually uses it for a citation/version
description with verification caveats (e.g. "CGST Act 2017, Section 22
(paraphrased; verify current notifications)", 69 chars). Every one of the
6 seeded regulations exceeds 20 chars, so `python -m seed.load_regulations`
fails against real Postgres with StringDataRightTruncation (SQLite doesn't
enforce VARCHAR length, which is why this passed the Phase 1 test suite
but failed against a real Postgres DB). Widened to Text, matching `notes`
which holds the same kind of free-text disclaimer.

No other regulations column is close to its limit for current seed data
(see backend/tests/test_regulation_seed_integrity.py, which now asserts
this for every seeded field going forward).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "regulations",
        "version",
        existing_type=sa.String(20),
        type_=sa.Text(),
        existing_nullable=False,
    )


def downgrade() -> None:
    # Reversible, but note: this will fail if any stored value is longer
    # than 20 chars -- which every currently-seeded regulation's version
    # is. That's intentional: silently truncating real regulation citation
    # text on downgrade would be worse than a loud failure.
    op.alter_column(
        "regulations",
        "version",
        existing_type=sa.Text(),
        type_=sa.String(20),
        existing_nullable=False,
    )
