"""Async and sync database engines, session factories, and lifecycle helpers.

Usage:
    from src.data.database import async_session_factory, get_sync_session_factory, init_db

    # Async (FastAPI routes)
    async with async_session_factory() as session:
        result = await session.execute(select(Merchant))

    # Sync (agent code, run via asyncio.to_thread)
    SyncSession = get_sync_session_factory()
    with SyncSession() as session:
        result = session.execute(select(Merchant))
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker

from src.config import settings

logger = logging.getLogger(__name__)

# ── Async Engine ──────────────────────────────────────────────────────────────

_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    """Return the singleton async engine, creating it on first call."""
    global _engine
    if _engine is None:
        pool_size = 5 if settings.is_production else 2
        max_overflow = 10 if settings.is_production else 5
        _engine = create_async_engine(
            settings.database_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=settings.debug,
        )
        logger.info(
            "Async engine created (pool_size=%d, max_overflow=%d, debug=%s)",
            pool_size,
            max_overflow,
            settings.debug,
        )
    return _engine


# ── Sync Engine (for agent code running in thread pool) ──────────────────────

_sync_engine: Engine | None = None
_sync_session_factory_cls: sessionmaker | None = None


def get_sync_engine() -> Engine:
    """Return the singleton sync engine, creating it on first call.

    Converts the async database URL (postgresql+async://) to a sync URL
    (postgresql://) for use by agent code that runs in ``asyncio.to_thread``.
    """
    global _sync_engine
    if _sync_engine is None:
        # Convert async URL to sync URL
        sync_url = settings.database_url
        if "+asyncpg" in sync_url:
            sync_url = sync_url.replace("+asyncpg", "")
        elif "+aiopg" in sync_url:
            sync_url = sync_url.replace("+aiopg", "")
        elif "+aioodbc" in sync_url:
            sync_url = sync_url.replace("+aioodbc", "")

        _sync_engine = create_engine(
            sync_url,
            pool_size=3,
            max_overflow=5,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=settings.debug,
        )
        logger.info("Sync engine created for agent thread pool.")
    return _sync_engine


def get_sync_session_factory() -> sessionmaker:
    """Return a sync sessionmaker bound to the sync engine."""
    global _sync_session_factory_cls
    if _sync_session_factory_cls is None:
        _sync_session_factory_cls = sessionmaker(
            bind=get_sync_engine(),
            class_=Session,
            expire_on_commit=False,
        )
    return _sync_session_factory_cls


def get_sync_session() -> Session:
    """Create and return a new sync Session for agent code."""
    factory = get_sync_session_factory()
    return factory()


# ── Async Session Factory ─────────────────────────────────────────────────────

async_session_factory = async_sessionmaker(
    bind=get_engine(),
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Dependency / context helpers ───────────────────────────────────────────────


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields an async session and ensures cleanup."""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        else:
            await session.commit()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Standalone async context-manager for non-FastAPI callers."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ── Lifecycle helpers ──────────────────────────────────────────────────────────


async def init_db() -> None:
    """Create all tables (useful for dev / tests; prefer Alembic in prod)."""
    from src.data.models import Base  # noqa: F811 – avoids circular import at module level

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created / verified.")


async def close_db() -> None:
    """Dispose of the engine pools on application shutdown."""
    global _engine, _sync_engine
    if _engine is not None:
        await _engine.dispose()
        logger.info("Async database engine disposed.")
        _engine = None
    if _sync_engine is not None:
        _sync_engine.dispose()
        logger.info("Sync database engine disposed.")
        _sync_engine = None
