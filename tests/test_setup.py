"""Pytest configuration and base fixtures for the test suite.

Provides:
- ``db_session`` fixture with automatic rollback per test
- ``db_engine`` fixture for schema creation (session-scoped)
- Smoke tests for the ORM models and factory functions
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.data.models import Base, Merchant, Settlement, SettlementStatus


# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def db_engine() -> Engine:
    """Create a sync engine and all tables once for the entire test session.

    Override DATABASE_URL_SYNC env var to point at a test database.
    Defaults to an in-memory SQLite DB so tests run without PostgreSQL.
    """
    import os

    url = os.getenv("DATABASE_URL_SYNC", "sqlite:///:memory:")
    engine = create_engine(url, echo=False)

    # Create tables
    Base.metadata.create_all(bind=engine)

    yield engine

    engine.dispose()


@pytest.fixture()
def db_session(db_engine: Engine) -> Session:
    """Yield a Session that rolls back after every test.

    This guarantees test isolation — no need to clean up between tests.
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ── Smoke Tests ────────────────────────────────────────────────────────────────


class TestDatabaseSetup:
    """Verify that the ORM models can be instantiated and persisted."""

    def test_merchant_create(self, db_session: Session) -> None:
        from tests.fixtures.test_data import create_merchant

        m = create_merchant(session=db_session, business_name="Smoke Test Co")
        assert m.id is not None
        assert m.business_name == "Smoke Test Co"

    def test_settlement_create(self, db_session: Session) -> None:
        from tests.fixtures.test_data import create_merchant, create_settlement

        m = create_merchant(session=db_session)
        s = create_settlement(session=db_session, merchant=m)
        assert s.merchant_id == m.id
        assert s.status in SettlementStatus

    def test_full_profile(self, db_session: Session) -> None:
        from tests.fixtures.test_data import create_merchant_with_full_profile

        profile = create_merchant_with_full_profile(
            session=db_session,
            n_settlements=3,
            n_refunds=2,
            n_disputes=1,
        )
        assert len(profile["settlements"]) == 3
        assert len(profile["refunds"]) == 2
        assert len(profile["disputes"]) == 1

    def test_anomaly_scenario(self, db_session: Session) -> None:
        from tests.fixtures.test_data import create_anomaly_scenario
        from src.data.models import AnomalyType, SeverityLevel

        anomaly, diagnosis, recommendation = create_anomaly_scenario(
            session=db_session,
            anomaly_type=AnomalyType.REFUND_STUCK,
            severity=SeverityLevel.CRITICAL,
        )
        assert anomaly.anomaly_type == AnomalyType.REFUND_STUCK
        assert diagnosis is not None
        assert recommendation is not None

    def test_dispute_with_evidence(self, db_session: Session) -> None:
        from tests.fixtures.test_data import create_dispute_with_evidence

        dispute, evidence_list = create_dispute_with_evidence(
            session=db_session, n_evidence=3
        )
        assert len(evidence_list) == 3
        assert all(e.dispute_id == dispute.id for e in evidence_list)
