"""Structured logging configuration for the Merchant Payment Ops agent.

Provides a ``setup_logging()`` function that configures both stdlib logging
and structlog with environment-aware formatting:

- **Development**: human-readable console output with colours
- **Production**: machine-readable JSON for log aggregators

Usage::

    from src.utils.logging import setup_logging
    setup_logging(log_level="INFO", json_output=False)
"""

from __future__ import annotations

import logging
import sys
from typing import Optional

import structlog


# ── Public API ─────────────────────────────────────────────────────────────────


def setup_logging(
    log_level: Optional[str] = None,
    json_output: Optional[bool] = None,
    service_name: str = "merchant-ops-agent",
) -> None:
    """Configure application-wide logging.

    Parameters
    ----------
    log_level : str, optional
        Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        Falls back to the ``LOG_LEVEL`` env var, then ``INFO``.
    json_output : bool, optional
        ``True`` for JSON lines, ``False`` for human-readable.
        Falls back to ``True`` in production, ``False`` in development.
    service_name : str
        Included in every log entry for easy filtering.
    """
    import os

    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO")
    level = getattr(logging, log_level.upper(), logging.INFO)

    if json_output is None:
        env = os.getenv("ENVIRONMENT", "development")
        json_output = env == "production"

    # ── structlog processors ──────────────────────────────────────────

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_output:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty())

    structlog.configure(
        processors=[
            *shared_processors,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )

    # ── stdlib logging ────────────────────────────────────────────────

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,
        level=level,
    )

    # Quieten noisy third-party loggers
    for noisy in (
        "uvicorn.access",
        "uvicorn.error",
        "sqlalchemy.engine",
        "sqlalchemy.pool",
        "httpx",
        "httpcore",
        "anthropic",
    ):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    # Let our app log at the configured level
    logging.getLogger("src").setLevel(level)

    logger = structlog.get_logger("logging")
    logger.info(
        "Logging initialised",
        level=log_level,
        json_output=json_output,
        service=service_name,
    )


# ── Convenience logger factory ─────────────────────────────────────────────────


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a named structlog logger.

    Usage::

        logger = get_logger(__name__)
        logger.info("Settlement processed", settlement_id="settle_xxx")
    """
    return structlog.get_logger(name)


# ── Decorators ────────────────────────────────────────────────────────────────


def log_operation(func: callable) -> callable:
    """Decorator that logs function entry, exit, and exceptions.

    Usage::

        @log_operation
        def process_settlement(settlement_id: str) -> dict:
            ...
    """
    import functools
    import time

    logger = structlog.get_logger(func.__module__ or "logging")

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__qualname__
        logger.info("operation_started", function=func_name)
        start = time.monotonic()
        try:
            result = func(*args, **kwargs)
            elapsed = time.monotonic() - start
            logger.info(
                "operation_completed",
                function=func_name,
                duration_ms=round(elapsed * 1000, 1),
            )
            return result
        except Exception as exc:
            elapsed = time.monotonic() - start
            logger.error(
                "operation_failed",
                function=func_name,
                error=str(exc),
                duration_ms=round(elapsed * 1000, 1),
            )
            raise

    return wrapper


def log_database_operation(
    operation: str,
    table: str,
    duration: float,
    success: bool,
    **extra: object,
) -> None:
    """Log a database operation with timing information.

    Parameters
    ----------
    operation : str
        Type of operation (e.g. ``"SELECT"``, ``"INSERT"``, ``"UPDATE"``).
    table : str
        Table name.
    duration : float
        Elapsed time in seconds.
    success : bool
        Whether the operation succeeded.
    **extra
        Additional context fields.
    """
    logger = structlog.get_logger("database")
    log_fn = logger.info if success else logger.error
    log_fn(
        "db_operation",
        operation=operation,
        table=table,
        duration_ms=round(duration * 1000, 1),
        success=success,
        **extra,
    )
