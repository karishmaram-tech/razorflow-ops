"""Merchant Payment Operations Intelligence — Application entry point.

Initialises FastAPI, database, logging, scheduled orchestrator cycles,
and mounts the dashboard UI.

Usage::

    # Development
    uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

    # Production
    gunicorn src.main:app -k uvicorn.workers.UvicornWorker -w 4
"""

from __future__ import annotations

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api.routes import router as api_router
from src.config import settings
from src.data.database import close_db, init_db

logger = logging.getLogger(__name__)

# ── Logging setup ──────────────────────────────────────────────────────────────


def _setup_logging() -> None:
    """Configure structured logging with structlog + stdlib."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer() if settings.debug else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Quiet noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.debug else logging.WARNING
    )


# ── Background orchestrator ────────────────────────────────────────────────────

_scheduler_task: asyncio.Task | None = None


async def _run_orchestrator_cycle(merchant_id: str) -> None:
    """Run one orchestrator cycle for a merchant (called by scheduler)."""
    from src.agents.orchestrator import PaymentOpsOrchestrator
    from src.data.database import get_db_context

    try:
        async with get_db_context() as session:
            from sqlalchemy.orm import Session as SyncSession

            # Bridge to sync session for the orchestrator
            sync = SyncSession(bind=session.sync_session)
            try:
                orchestrator = PaymentOpsOrchestrator(sync)
                dashboard = await asyncio.to_thread(orchestrator.run_agent_cycle, merchant_id)
                logger.info(
                    "Orchestrator cycle complete for %s: %d anomalies",
                    merchant_id,
                    dashboard.summary.get("total_anomalies", 0),
                )
            finally:
                sync.close()
    except Exception:
        logger.exception("Orchestrator cycle failed for merchant %s", merchant_id)


async def _scheduler_loop() -> None:
    """Run orchestrator cycles for all merchants on a schedule."""
    from sqlalchemy import select
    from src.data.database import get_db_context
    from src.data.models import Merchant

    while True:
        try:
            async with get_db_context() as session:
                result = await session.execute(select(Merchant.id))
                merchant_ids = [str(row[0]) for row in result.fetchall()]

            for mid in merchant_ids:
                await _run_orchestrator_cycle(mid)

        except Exception:
            logger.exception("Scheduler loop error")

        # Sleep 15 minutes between cycles
        await asyncio.sleep(15 * 60)


# ── Lifespan ───────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    global _scheduler_task

    _setup_logging()
    logger.info("Starting Merchant Payment Ops Intelligence agent")
    logger.info("Environment: %s", settings.environment.value)
    logger.info("Debug: %s", settings.debug)

    # Database
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception:
        logger.exception("Database initialization failed — continuing without DB")

    # Start background scheduler
    if settings.is_production or settings.debug:
        _scheduler_task = asyncio.create_task(_scheduler_loop())
        logger.info("Background orchestrator scheduler started")

    logger.info("Application ready — listening on %s:%s", settings.api_host, settings.api_port)

    yield

    # Shutdown
    logger.info("Shutting down...")
    if _scheduler_task:
        _scheduler_task.cancel()
        try:
            await _scheduler_task
        except asyncio.CancelledError:
            pass
    await close_db()
    logger.info("Shutdown complete")


# ── FastAPI app ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Merchant Payment Operations Intelligence",
    description=(
        "AI-powered agent for Razorpay merchant payment operations — "
        "automates settlement analysis, refund tracking, and dispute evidence."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(api_router, prefix="/api")

# Mount dashboard UI
_ui_dir = Path(__file__).resolve().parent.parent / "ui"
if _ui_dir.is_dir():
    app.mount("/dashboard", StaticFiles(directory=str(_ui_dir), html=True), name="dashboard")


# ── Health check ───────────────────────────────────────────────────────────────


@app.get("/health", tags=["system"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "merchant-payment-ops-agent",
        "version": "1.0.0",
        "environment": settings.environment.value,
    }


@app.get("/", tags=["system"])
async def root():
    """Root redirect to dashboard."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard")
