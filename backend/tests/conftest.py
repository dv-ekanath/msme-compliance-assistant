from __future__ import annotations

import os

# Must run before any `app.*` import: Settings.get_settings() is @lru_cache'd
# and first triggered at import time (app/core/database.py imports it at
# module scope), so this has to land before the `import app.models` below.
# Without it, the FastAPI TestClient's lifespan (triggered by every `client`
# fixture use) would start a real APScheduler background job per test.
os.environ.setdefault("WATCHDOG_SCHEDULER_ENABLED", "false")

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  registers all tables on Base.metadata
from app.core.database import get_db
from app.core.security import create_access_token, hash_password
from app.domain.enums import BusinessLegalType, SectorType, TurnoverBand, UserRole
from app.domain.facts import BusinessFacts
from app.embeddings.base import EmbeddingProvider
from app.embeddings.factory import get_embedding_provider
from app.embeddings.mock_provider import MockEmbeddingProvider
from app.llm.base import LLMProvider
from app.llm.factory import get_llm_provider
from app.llm.mock_provider import MockLLMProvider
from app.main import app as fastapi_app
from app.models.base import Base
from app.models.user import User
from app.ocr.base import OCRProvider
from app.ocr.factory import get_ocr_provider
from app.ocr.mock_provider import MockOCRProvider
from app.rag.ingestion import ingest_documents, load_document_entries
from app.rules.types import RegulationConfig
from seed.load_regulations import load_entries, upsert_regulations

TEST_EMBEDDING_DIMENSION = 384
DEMO_OWNER_EMAIL = "owner@test.local"
DEMO_CA_EMAIL = "ca@test.local"
DEMO_PASSWORD = "password123"


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


def _seed_demo_users(session) -> None:
    """A demo owner + CA user (Phase 5), so any test needing an
    authenticated actor can look them up by DEMO_OWNER_EMAIL/DEMO_CA_EMAIL
    without each test hand-rolling its own User rows.

    Idempotent: `client` and `db_session` each call _seed_full_corpus on
    their own session, but both share the same underlying engine when a
    test requests both fixtures together (StaticPool = one connection) --
    without this check, the second call's INSERT would hit users.email's
    unique constraint.
    """
    if session.query(User).filter(User.email == DEMO_OWNER_EMAIL).first() is not None:
        return
    session.add(
        User(
            email=DEMO_OWNER_EMAIL,
            full_name="Demo Owner",
            role=UserRole.OWNER,
            hashed_password=hash_password(DEMO_PASSWORD),
        )
    )
    session.add(
        User(
            email=DEMO_CA_EMAIL,
            full_name="Demo CA",
            role=UserRole.CA,
            hashed_password=hash_password(DEMO_PASSWORD),
        )
    )
    session.commit()


def _seed_full_corpus(session) -> None:
    """Regulations (Phase 1) + the RAG demo document/chunk corpus (Phase 2)
    + demo users (Phase 5), embedded with the deterministic
    MockEmbeddingProvider -- no ML model load needed for the test suite.
    """
    upsert_regulations(session, load_entries())
    ingest_documents(session, MockEmbeddingProvider(dimension=TEST_EMBEDDING_DIMENSION), load_document_entries())
    _seed_demo_users(session)


@pytest.fixture()
def db_session(session_factory):
    """A DB session with regulations + the RAG demo corpus already loaded."""
    session = session_factory()
    _seed_full_corpus(session)
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(session_factory):
    """FastAPI TestClient wired to an isolated, seeded SQLite DB per test,
    with LLM/embedding providers overridden to their mock implementations
    -- fast, deterministic, no model download, no API key.
    """
    seed_session = session_factory()
    _seed_full_corpus(seed_session)
    seed_session.close()

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[get_llm_provider] = lambda: MockLLMProvider()
    fastapi_app.dependency_overrides[get_embedding_provider] = lambda: MockEmbeddingProvider(
        dimension=TEST_EMBEDDING_DIMENSION
    )
    fastapi_app.dependency_overrides[get_ocr_provider] = lambda: MockOCRProvider()
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client, session_factory) -> dict[str, dict[str, str]]:
    """Bearer-token Authorization headers for the demo users _seed_full_corpus
    creates, keyed by role ('owner'/'ca'). Depends on `client` so the
    corpus (and demo users) is guaranteed seeded before this runs.
    """
    session = session_factory()
    try:
        owner = session.query(User).filter(User.email == DEMO_OWNER_EMAIL).one()
        ca = session.query(User).filter(User.email == DEMO_CA_EMAIL).one()
        return {
            "owner": {"Authorization": f"Bearer {create_access_token(owner.id, owner.role)}"},
            "ca": {"Authorization": f"Bearer {create_access_token(ca.id, ca.role)}"},
        }
    finally:
        session.close()


@pytest.fixture()
def mock_embedding_provider() -> EmbeddingProvider:
    return MockEmbeddingProvider(dimension=TEST_EMBEDDING_DIMENSION)


@pytest.fixture()
def mock_llm_provider() -> LLMProvider:
    return MockLLMProvider()


@pytest.fixture()
def mock_ocr_provider() -> OCRProvider:
    return MockOCRProvider()


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
