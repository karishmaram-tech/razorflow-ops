"""Shared pytest fixtures for the test suite.

Provides ``db_session`` and ``db_engine`` fixtures available to all test
modules via conftest auto-discovery.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from src.data.models import Base


@pytest.fixture(scope="session")
def db_engine() -> Engine:
    """Create a sync engine and all tables once for the entire test session.

    Uses in-memory SQLite so tests run without PostgreSQL.
    """
    import os

    url = os.getenv("DATABASE_URL_SYNC", "sqlite:///:memory:")
    engine = create_engine(
        url,
        echo=False,
        connect_args={"check_same_thread": False} if "sqlite" in url else {},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def db_session(db_engine: Engine) -> Session:
    """Yield a Session that rolls back after every test.

    Guarantees test isolation — no cleanup needed between tests.
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()
