"""Loads backend/seed/regulations/*.json into the `regulations` table.

Run from the backend/ directory:
    python -m seed.load_regulations

Idempotent: upserts by `code`, safe to re-run after editing a seed file.
`load_entries`/`upsert_regulations` are split out (rather than one script
function) so the test suite can seed a scratch DB with the exact same
regulation data without touching the production SessionLocal.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.regulation import Regulation

REGULATIONS_DIR = Path(__file__).parent / "regulations"
REQUIRED_FIELDS = {
    "code",
    "title",
    "authority",
    "jurisdiction",
    "source_url",
    "effective_date",
    "version",
    "applicability_rules",
}


def load_entries() -> list[dict]:
    entries = []
    for path in sorted(REGULATIONS_DIR.glob("*.json")):
        if path.name.startswith("_") or path.name == "schema.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        missing = REQUIRED_FIELDS - data.keys()
        if missing:
            raise ValueError(f"{path.name} is missing required fields: {sorted(missing)}")
        entries.append(data)
    return entries


def upsert_regulations(db: Session, entries: list[dict]) -> int:
    for entry in entries:
        existing = db.query(Regulation).filter(Regulation.code == entry["code"]).one_or_none()

        if existing is None:
            existing = Regulation(code=entry["code"])
            db.add(existing)

        existing.title = entry["title"]
        existing.authority = entry["authority"]
        existing.jurisdiction = entry["jurisdiction"]
        existing.applicability_rules = entry["applicability_rules"]
        existing.source_url = entry["source_url"]
        existing.effective_date = date.fromisoformat(entry["effective_date"])
        existing.version = entry["version"]
        existing.notes = entry.get("notes")

    db.commit()
    return len(entries)


def load_regulations() -> None:
    db = SessionLocal()
    try:
        entries = load_entries()
        count = upsert_regulations(db, entries)
        print(f"Loaded {count} regulation(s): {', '.join(e['code'] for e in entries)}")
    finally:
        db.close()


if __name__ == "__main__":
    load_regulations()
