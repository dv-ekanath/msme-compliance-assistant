from __future__ import annotations

from app.models.regulation import Regulation
from seed.load_regulations import load_entries

STRING_FIELDS = ["code", "title", "authority", "jurisdiction", "source_url", "version"]


def test_seed_values_fit_within_column_limits():
    """SQLite (used by the rest of this test suite) does not enforce
    VARCHAR length -- it silently accepts oversized strings, which is
    exactly how the `version` VARCHAR(20)-vs-real-seed-data mismatch
    shipped without a failing test and only surfaced against real
    Postgres. This test checks seed values against each column's actual
    declared length directly, independent of which DB backend is running.
    """
    columns = Regulation.__table__.columns
    entries = load_entries()

    assert entries, "no seed entries loaded -- check backend/seed/regulations/"

    for entry in entries:
        for field in STRING_FIELDS:
            column = columns[field]
            max_length = getattr(column.type, "length", None)
            if max_length is None:
                continue  # Text/unbounded column -- nothing to bound-check

            value = entry[field]
            assert len(value) <= max_length, (
                f"{entry['code']}.{field} is {len(value)} chars, which exceeds the "
                f"{column.type} column limit of {max_length}. Either shorten the seed "
                f"value or widen the column (with a new Alembic migration)."
            )


def test_regulation_version_column_is_unbounded():
    """Guards specifically against re-narrowing `version` back to a short
    VARCHAR -- the seed data legitimately needs free-text citation notes,
    not a short semver tag. See alembic/versions/0002_widen_regulation_version_column.py.
    """
    version_type = Regulation.__table__.columns["version"].type
    assert getattr(version_type, "length", None) is None, (
        "regulations.version must remain an unbounded Text column -- seeded "
        "citation/version strings are longer than any reasonable VARCHAR cap."
    )
