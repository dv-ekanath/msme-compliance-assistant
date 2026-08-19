"""Creates the two demo accounts used by the live demo script and manual
testing, so nobody has to register through the UI before a walkthrough.

Run from the backend/ directory:
    python -m seed.create_demo_users

Idempotent: upserts by email, safe to re-run. Real accounts created via
the actual POST /auth/register mechanism (SessionLocal + hash_password),
not a schema-level fixture -- consistent with every other resource in
this app (Business, Registration, Filing) being created through a real
code path, not a stub.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.domain.enums import UserRole
from app.models.user import User

DEMO_ACCOUNTS = [
    {"email": "owner@demo.msme", "full_name": "Demo MSME Owner", "role": UserRole.OWNER, "password": "demo1234"},
    {"email": "ca@demo.msme", "full_name": "Demo CA Reviewer", "role": UserRole.CA, "password": "demo1234"},
]


def upsert_demo_users(db: Session) -> int:
    for account in DEMO_ACCOUNTS:
        existing = db.query(User).filter(User.email == account["email"]).one_or_none()
        if existing is None:
            existing = User(email=account["email"])
            db.add(existing)

        existing.full_name = account["full_name"]
        existing.role = account["role"]
        existing.hashed_password = hash_password(account["password"])

    db.commit()
    return len(DEMO_ACCOUNTS)


def create_demo_users() -> None:
    db = SessionLocal()
    try:
        count = upsert_demo_users(db)
        print(f"Upserted {count} demo user(s): {', '.join(a['email'] for a in DEMO_ACCOUNTS)}")
    finally:
        db.close()


if __name__ == "__main__":
    create_demo_users()
