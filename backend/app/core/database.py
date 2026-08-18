from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# Without an explicit timeout, a connect attempt to an unreachable Postgres
# (e.g. Docker not started yet) can hang far longer than a health-check
# endpoint should ever take. `connect_timeout` is a psycopg/libpq option
# with no SQLite equivalent, so it's only applied for non-SQLite URLs --
# DATABASE_URL is pointed at SQLite for local scripts/tests when Postgres
# isn't available (see backend/tests/conftest.py, seed/load_regulations.py).
_connect_args = {} if settings.database_url.startswith("sqlite") else {"connect_timeout": 3}

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    future=True,
    connect_args=_connect_args,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a request-scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
