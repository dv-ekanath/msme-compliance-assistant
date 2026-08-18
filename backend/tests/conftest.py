from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  registers all tables on Base.metadata
from app.core.database import get_db
from app.domain.enums import BusinessLegalType, SectorType, TurnoverBand
from app.domain.facts import BusinessFacts
from app.main import app as fastapi_app
from app.models.base import Base
from app.rules.types import RegulationConfig
from seed.load_regulations import load_entries, upsert_regulations


@pytest.fixture()
def db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def session_factory(db_engine):
    return sessionmaker(bind=db_engine, autoflush=False, autocommit=False, future=True)


@pytest.fixture()
def db_session(session_factory):
    """A DB session with the real regulation seed data already loaded."""
    session = session_factory()
    upsert_regulations(session, load_entries())
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(session_factory):
    """FastAPI TestClient wired to an isolated, seeded SQLite DB per test."""
    seed_session = session_factory()
    upsert_regulations(seed_session, load_entries())
    seed_session.close()

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()


@pytest.fixture()
def regulation_configs() -> dict[str, RegulationConfig]:
    """Rule-level unit tests evaluate against the *real* seeded regulation
    config (not a hand-rolled stand-in), so they fail if the seed data and
    the rule code drift apart.
    """
    return {
        entry["code"]: RegulationConfig(
            id=entry["code"],
            code=entry["code"],
            title=entry["title"],
            authority=entry["authority"],
            source_url=entry["source_url"],
            applicability_rules=entry["applicability_rules"],
        )
        for entry in load_entries()
    }


def make_facts(
    *,
    sector: SectorType = SectorType.SERVICES,
    state: str = "Delhi",
    turnover_band: TurnoverBand = TurnoverBand.UNDER_10L,
    employee_count: int = 0,
    registrations: dict | None = None,
) -> BusinessFacts:
    return BusinessFacts(
        business_id="00000000-0000-0000-0000-000000000000",
        name="Test Business",
        sector=sector,
        state=state,
        legal_type=BusinessLegalType.PROPRIETORSHIP,
        turnover_band=turnover_band,
        employee_count=employee_count,
        incorporation_date=date(2020, 1, 1),
        registrations=registrations or {},
    )
