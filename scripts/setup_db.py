#!/usr/bin/env python3
"""Drop and recreate all database tables.

Usage:
    cd merchant-payment-ops-agent
    python scripts/setup_db.py
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# ── Path bootstrap ─────────────────────────────────────────────────────────────
# Allow running from project root as `python scripts/setup_db.py`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import settings  # noqa: E402
from src.data.models import Base  # noqa: E402

logger = logging.getLogger("setup_db")


def _build_sync_engine() -> Engine:
    """Create a synchronous engine using the sync database URL."""
    return create_engine(
        settings.database_url_sync,
        pool_pre_ping=True,
        echo=settings.debug,
    )


def drop_all(engine: Engine) -> None:
    """Drop every table defined in the ORM metadata."""
    logger.info("Dropping all tables …")
    with engine.begin() as conn:
        # Disable FK checks temporarily so we don't hit constraint errors
        conn.execute(text("SET session_replication_role = 'replica';"))
        Base.metadata.drop_all(bind=conn)
        conn.execute(text("SET session_replication_role = 'origin';"))
    logger.info("All tables dropped.")


def create_all(engine: Engine) -> None:
    """Create every table (and index) defined in the ORM metadata."""
    logger.info("Creating all tables …")
    with engine.begin() as conn:
        Base.metadata.create_all(bind=conn)
    logger.info("All tables created.")


def verify_tables(engine: Engine) -> list[str]:
    """Return a list of table names that now exist in the public schema."""
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT tablename FROM pg_catalog.pg_tables "
                "WHERE schemaname = 'public' ORDER BY tablename"
            )
        )
        return [row[0] for row in result.fetchall()]


def seed_evidence_templates(engine: Engine) -> None:
    """Insert the default dispute-reason-code → evidence mapping."""
    from sqlalchemy import insert
    from src.data.models import DisputeEvidenceTemplate

    templates = [
        {
            "reason_code": "4855",
            "reason_description": "Goods/services not received",
            "required_evidence_types": ["proof_of_delivery", "customer_communication"],
            "template_text": (
                "Provide tracking information showing delivery to the customer's "
                "address, along with any communication confirming receipt."
            ),
        },
        {
            "reason_code": "4849",
            "reason_description": "Transaction not authorised",
            "required_evidence_types": ["terms_of_service", "customer_communication"],
            "template_text": (
                "Provide evidence that the cardholder authorised the transaction, "
                "including AVS/CVV match results and any saved consent records."
            ),
        },
        {
            "reason_code": "4871",
            "reason_description": "Incorrect transaction amount",
            "required_evidence_types": ["receipt", "terms_of_service"],
            "template_text": (
                "Provide the original receipt or invoice showing the agreed amount, "
                "and explain any discrepancy between charged and expected amounts."
            ),
        },
        {
            "reason_code": "4863",
            "reason_description": "Cardholder does not recognise transaction",
            "required_evidence_types": [
                "receipt",
                "proof_of_delivery",
                "customer_communication",
            ],
            "template_text": (
                "Provide documentation linking the transaction to the cardholder, "
                "including order confirmation, delivery proof, and merchant descriptor."
            ),
        },
        {
            "reason_code": "10.4",
            "reason_description": "Other (wire fraud / ACH return)",
            "required_evidence_types": ["terms_of_service", "other"],
            "template_text": (
                "Provide a detailed explanation of the transaction context and "
                "any supporting documentation specific to this dispute type."
            ),
        },
    ]

    logger.info("Seeding %d dispute evidence templates …", len(templates))
    with engine.begin() as conn:
        # Upsert-style: skip if reason_code already exists
        for t in templates:
            existing = conn.execute(
                text(
                    "SELECT 1 FROM dispute_evidence_templates "
                    "WHERE reason_code = :rc LIMIT 1"
                ),
                {"rc": t["reason_code"]},
            ).fetchone()
            if not existing:
                conn.execute(
                    insert(DisputeEvidenceTemplate).values(**t)
                )
    logger.info("Evidence templates seeded.")


# ── CLI ────────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="Reset and seed the database.")
    parser.add_argument(
        "--skip-drop",
        action="store_true",
        help="Skip dropping tables (create only).",
    )
    parser.add_argument(
        "--skip-seed",
        action="store_true",
        help="Skip seeding evidence templates.",
    )
    parser.add_argument(
        "--drop-only",
        action="store_true",
        help="Drop tables and exit.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if settings.debug else logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    )

    engine = _build_sync_engine()

    try:
        # 1. Drop
        if not args.skip_drop:
            drop_all(engine)

        if args.drop_only:
            logger.info("Drop-only mode — exiting.")
            return

        # 2. Create
        create_all(engine)

        # 3. Verify
        tables = verify_tables(engine)
        logger.info("Tables in public schema (%d): %s", len(tables), ", ".join(tables))

        # 4. Seed templates
        if not args.skip_seed:
            seed_evidence_templates(engine)

        logger.info("✅  Database setup complete.")

    except Exception:
        logger.exception("❌  Database setup FAILED")
        sys.exit(1)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
