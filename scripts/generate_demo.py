#!/usr/bin/env python3
"""Generate demo data for the razorflow-ops merchant payment operations agent.

Creates 5 representative merchants with specific scenarios to demonstrate
agent capabilities, then prints curl commands for testing each endpoint.

Usage:
    python scripts/generate_demo.py
    python scripts/generate_demo.py --clean
    python scripts/generate_demo.py --merchants 10
"""

from __future__ import annotations

import argparse
import logging
import sys
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from src.data.models import (
    Anomaly,
    AnomalyStatus,
    AnomalyType,
    Base,
    Diagnosis,
    Dispute,
    DisputeEvidence,
    DisputeStatus,
    DisputeType,
    EvaluationMetric,
    Merchant,
    Recommendation,
    Refund,
    RefundInitiator,
    RefundReason,
    RefundStatus,
    SeverityLevel,
    Settlement,
    SettlementAttempt,
    SettlementStatus,
    Transaction,
    UrgencyLevel,
)

logger = logging.getLogger(__name__)

# ── Demo Constants ─────────────────────────────────────────────────────────────

NOW = datetime.utcnow()
HOUR = timedelta(hours=1)
DAY = timedelta(days=1)

DEMO_MERCHANTS = [
    {
        "id": uuid.UUID("11111111-1111-1111-1111-111111111111"),
        "name": "QuickCommerce India",
        "industry": "e-commerce",
        "revenue": Decimal("50000000.00"),
        "volume": 8500,
        "dispute_rate": Decimal("2.1"),
        "threshold": "warning",
        "channels": ["email", "webhook"],
    },
    {
        "id": uuid.UUID("22222222-2222-2222-2222-222222222222"),
        "name": "CloudBazaar SaaS",
        "industry": "saas",
        "revenue": Decimal("25000000.00"),
        "volume": 3200,
        "dispute_rate": Decimal("0.8"),
        "threshold": "info",
        "channels": ["email"],
    },
    {
        "id": uuid.UUID("33333333-3333-3333-3333-333333333333"),
        "name": "FreshBasket Marketplace",
        "industry": "marketplace",
        "revenue": Decimal("80000000.00"),
        "volume": 15000,
        "dispute_rate": Decimal("3.5"),
        "threshold": "critical",
        "channels": ["email", "webhook", "sms"],
    },
    {
        "id": uuid.UUID("44444444-4444-4444-4444-444444444444"),
        "name": "SkillPay Academy",
        "industry": "education",
        "revenue": Decimal("12000000.00"),
        "volume": 1800,
        "dispute_rate": Decimal("1.2"),
        "threshold": "warning",
        "channels": ["email"],
    },
    {
        "id": uuid.UUID("55555555-5555-5555-5555-555555555555"),
        "name": "MediSupply Direct",
        "industry": "healthcare",
        "revenue": Decimal("35000000.00"),
        "volume": 6200,
        "dispute_rate": Decimal("4.8"),
        "threshold": "info",
        "channels": ["email", "webhook"],
    },
]


# ── Setup ──────────────────────────────────────────────────────────────────────


def get_session() -> Session:
    """Create a synchronous SQLAlchemy session."""
    import os

    db_url = os.getenv(
        "DATABASE_URL_SYNC",
        "postgresql://postgres:postgres@localhost:5432/merchant_ops",
    )
    engine = create_engine(db_url, echo=False)
    factory = sessionmaker(bind=engine)
    return factory()


def clean_database(session: Session) -> None:
    """Delete all existing demo data."""
    logger.info("Cleaning database...")
    for table in [
        "evaluation_metrics",
        "recommendations",
        "diagnoses",
        "anomalies",
        "dispute_evidence",
        "disputes",
        "refunds",
        "settlement_attempts",
        "settlements",
        "transactions",
        "merchants",
    ]:
        session.execute(text(f"DELETE FROM {table}"))
    session.commit()
    logger.info("Database cleaned.")


def create_tables() -> None:
    """Create all tables from ORM metadata."""
    import os

    db_url = os.getenv(
        "DATABASE_URL_SYNC",
        "postgresql://postgres:postgres@localhost:5432/merchant_ops",
    )
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(bind=engine)
    engine.dispose()


# ── Merchant Generators ────────────────────────────────────────────────────────


def _create_merchant(session: Session, config: dict) -> Merchant:
    """Create a merchant from config dict."""
    m = Merchant(
        id=config["id"],
        business_name=config["name"],
        annual_revenue=config["revenue"],
        transaction_volume_monthly=config["volume"],
        dispute_rate=config["dispute_rate"],
        industry_category=config["industry"],
        alert_threshold_severity=config["threshold"],
        notification_channels=config["channels"],
    )
    session.add(m)
    session.flush()
    return m


def _create_txn(
    session: Session, merchant_id, amount: Decimal, days_ago: int
) -> Transaction:
    t = Transaction(
        id=f"pay_{uuid.uuid4().hex[:10]}",
        merchant_id=merchant_id,
        amount=amount,
        currency="INR",
        status="captured",
        created_at=NOW - DAY * days_ago,
    )
    session.add(t)
    session.flush()
    return t


def _create_settlement_for_demo(
    session: Session,
    merchant_id,
    *,
    status: SettlementStatus,
    amount: Decimal,
    days_ago: int,
    fees: Decimal = Decimal("2000.00"),
) -> Settlement:
    s = Settlement(
        id=f"settle_{uuid.uuid4().hex[:10]}",
        merchant_id=merchant_id,
        amount=amount,
        currency="INR",
        status=status,
        created_at=NOW - DAY * days_ago,
        fees=fees,
        taxes=fees * Decimal("0.18"),
        net_amount=amount - fees - (fees * Decimal("0.18")),
        related_refunds=[],
        related_disputes=[],
    )
    session.add(s)
    session.flush()
    return s


# ── Scenario Generators ────────────────────────────────────────────────────────


def generate_scenario_1_delayed_settlement(session: Session, merchant: Merchant) -> dict:
    """Scenario 1: Settlement delayed 3+ days (CRITICAL)."""
    settlement = _create_settlement_for_demo(
        session,
        merchant.id,
        status=SettlementStatus.PENDING,
        amount=Decimal("245000.00"),
        days_ago=5,
        fees=Decimal("4900.00"),
    )

    # Add a failed attempt
    attempt = SettlementAttempt(
        settlement_id=settlement.id,
        attempt_number=1,
        method="IMPS",
        initiated_at=NOW - DAY * 5 + HOUR * 2,
        response_code="40091",
        response_message="Insufficient Funds in Settlement Account",
        status="failed",
        bank_reference_id=f"REF_{uuid.uuid4().hex[:8]}",
    )
    session.add(attempt)
    session.flush()

    return {
        "scenario": "Delayed Settlement",
        "severity": "CRITICAL",
        "settlement_id": settlement.id,
        "details": f"Rs {settlement.amount} delayed {(NOW - settlement.created_at).days} days",
    }


def generate_scenario_2_failed_retries(session: Session, merchant: Merchant) -> dict:
    """Scenario 2: Failed settlement with 3 retry attempts (CRITICAL)."""
    settlement = _create_settlement_for_demo(
        session,
        merchant.id,
        status=SettlementStatus.FAILED,
        amount=Decimal("180000.00"),
        days_ago=3,
        fees=Decimal("3600.00"),
    )

    for i, (method, code, msg) in enumerate(
        [
            ("IMPS", "40091", "Insufficient funds"),
            ("NEFT", "90001", "Bank processing delay"),
            ("RTGS", "40091", "Insufficient funds"),
        ],
        1,
    ):
        attempt = SettlementAttempt(
            settlement_id=settlement.id,
            attempt_number=i,
            method=method,
            initiated_at=NOW - DAY * 3 + HOUR * (i * 4),
            response_code=code,
            response_message=msg,
            status="failed",
            bank_reference_id=f"REF_{uuid.uuid4().hex[:8]}",
        )
        session.add(attempt)
    session.flush()

    return {
        "scenario": "Failed Settlement with Retries",
        "severity": "CRITICAL",
        "settlement_id": settlement.id,
        "details": f"Rs {settlement.amount} failed after 3 attempts",
    }


def generate_scenario_3_stuck_refund(
    session: Session, merchant: Merchant
) -> dict:
    """Scenario 3: Refund stuck for 5 days (CRITICAL)."""
    txn = _create_txn(session, merchant.id, Decimal("8500.00"), days_ago=10)

    refund = Refund(
        id=f"rfnd_{uuid.uuid4().hex[:10]}",
        merchant_id=merchant.id,
        transaction_id=txn.id,
        amount=Decimal("8500.00"),
        reason=RefundReason.CUSTOMER_REQUESTED,
        status=RefundStatus.PENDING,
        created_at=NOW - DAY * 5,
        initiated_by=RefundInitiator.MERCHANT,
        expected_completion_at=NOW - DAY * 2,
    )
    session.add(refund)
    session.flush()

    return {
        "scenario": "Stuck Refund",
        "severity": "CRITICAL",
        "refund_id": refund.id,
        "details": f"Rs {refund.amount} stuck for 5 days",
    }


def generate_scenario_4_dispute_no_evidence(
    session: Session, merchant: Merchant
) -> dict:
    """Scenario 4: Dispute deadline in 2 days, zero evidence (CRITICAL)."""
    txn = _create_txn(session, merchant.id, Decimal("15000.00"), days_ago=12)

    dispute = Dispute(
        id=f"disp_{uuid.uuid4().hex[:10]}",
        merchant_id=merchant.id,
        transaction_id=txn.id,
        type=DisputeType.CHARGEBACK,
        reason_code="4855",
        reason_text="Goods/Services Not Received",
        amount=Decimal("15000.00"),
        filed_at=NOW - DAY * 5,
        evidence_deadline=NOW + DAY * 2,
        current_status=DisputeStatus.EVIDENCE_PENDING,
    )
    session.add(dispute)
    session.flush()

    return {
        "scenario": "Dispute No Evidence",
        "severity": "CRITICAL",
        "dispute_id": dispute.id,
        "details": f"Rs {dispute.amount} dispute, deadline in 2 days, 0% evidence",
    }


def generate_scenario_5_high_dispute_rate(
    session: Session, merchant: Merchant
) -> dict:
    """Scenario 5: Merchant with 12.5% dispute rate (pattern)."""
    disputes_created = []
    txn = _create_txn(session, merchant.id, Decimal("22000.00"), days_ago=15)

    for i, (code, text_) in enumerate(
        [
            ("4855", "Goods/Services Not Received"),
            ("4849", "Unauthorized Use"),
            ("4871", "Incorrect Amount"),
            ("4834", "Duplicate Processing"),
            ("4855", "Goods/Services Not Received"),
        ],
        1,
    ):
        dispute = Dispute(
            id=f"disp_{uuid.uuid4().hex[:10]}",
            merchant_id=merchant.id,
            transaction_id=txn.id,
            type=DisputeType.CHARGEBACK,
            reason_code=code,
            reason_text=text_,
            amount=Decimal(f"{5000 + i * 2000}.00"),
            filed_at=NOW - DAY * (10 - i),
            evidence_deadline=NOW + DAY * (7 - i),
            current_status=DisputeStatus.EVIDENCE_PENDING,
        )
        session.add(dispute)
        disputes_created.append(dispute)
    session.flush()

    return {
        "scenario": "High Dispute Rate Pattern",
        "severity": "CRITICAL",
        "dispute_count": len(disputes_created),
        "details": f"{len(disputes_created)} disputes in 10 days, high risk pattern",
    }


# ── Main ───────────────────────────────────────────────────────────────────────


def generate_demo(merchants_count: int = 5, clean: bool = False) -> dict:
    """Generate complete demo data.

    Parameters
    ----------
    merchants_count : int
        Number of merchants to create (default 5).
    clean : bool
        If True, delete all existing data first.

    Returns
    -------
    dict
        Summary of generated data.
    """
    session = get_session()
    summary = {
        "merchants": 0,
        "settlements": 0,
        "refunds": 0,
        "disputes": 0,
        "transactions": 0,
        "anomalies": 0,
        "scenarios": [],
    }

    try:
        if clean:
            clean_database(session)

        # Create merchants
        demo_configs = DEMO_MERCHANTS[:merchants_count]
        merchants = []
        for config in demo_configs:
            merchant = _create_merchant(session, config)
            merchants.append(merchant)
            summary["merchants"] += 1
        session.commit()

        logger.info("Created %d merchants.", summary["merchants"])

        # Generate scenarios for each merchant
        scenario_generators = [
            generate_scenario_1_delayed_settlement,
            generate_scenario_2_failed_retries,
            generate_scenario_3_stuck_refund,
            generate_scenario_4_dispute_no_evidence,
            generate_scenario_5_high_dispute_rate,
        ]

        for i, merchant in enumerate(merchants):
            logger.info("Generating scenarios for merchant: %s", merchant.business_name)

            for j, generator in enumerate(scenario_generators):
                if j >= len(merchants):
                    break
                if i == j:  # One scenario per merchant
                    result = generator(session, merchant)
                    summary["scenarios"].append(result)
                    logger.info("  Scenario: %s", result["scenario"])

            # Also generate some normal (successful) settlements
            for k in range(3):
                _create_settlement_for_demo(
                    session,
                    merchant.id,
                    status=SettlementStatus.SUCCESS,
                    amount=Decimal(f"{50000 + k * 30000}.00"),
                    days_ago=k + 1,
                )
                summary["settlements"] += 1

            # Generate some successful refunds
            for k in range(2):
                txn = _create_txn(
                    session, merchant.id, Decimal(f"{2000 + k * 1500}.00"), days_ago=k + 2
                )
                refund = Refund(
                    id=f"rfnd_{uuid.uuid4().hex[:10]}",
                    merchant_id=merchant.id,
                    transaction_id=txn.id,
                    amount=Decimal(f"{2000 + k * 1500}.00"),
                    reason=RefundReason.CUSTOMER_REQUESTED,
                    status=RefundStatus.SUCCESS,
                    created_at=NOW - DAY * (k + 2),
                    initiated_by=RefundInitiator.MERCHANT,
                    actual_completion_at=NOW - DAY * k,
                )
                session.add(refund)
                summary["refunds"] += 1

            session.commit()

        # Final counts
        summary["transactions"] = (
            session.query(Transaction)
            .filter(Transaction.merchant_id.in_([m.id for m in merchants]))
            .count()
        )
        summary["settlements"] = (
            session.query(Settlement)
            .filter(Settlement.merchant_id.in_([m.id for m in merchants]))
            .count()
        )
        summary["refunds"] = (
            session.query(Refund)
            .filter(Refund.merchant_id.in_([m.id for m in merchants]))
            .count()
        )
        summary["disputes"] = (
            session.query(Dispute)
            .filter(Dispute.merchant_id.in_([m.id for m in merchants]))
            .count()
        )

        logger.info("Demo generation complete.")
        return summary

    except Exception as e:
        session.rollback()
        logger.error("Demo generation failed: %s", e)
        raise
    finally:
        session.close()


def print_summary(summary: dict) -> None:
    """Print a formatted summary of generated data."""
    print("\n" + "=" * 60)
    print("  razorflow-ops — Demo Data Generated")
    print("=" * 60)
    print(f"\n  Merchants:       {summary['merchants']}")
    print(f"  Settlements:     {summary['settlements']}")
    print(f"  Refunds:         {summary['refunds']}")
    print(f"  Disputes:        {summary['disputes']}")
    print(f"  Transactions:    {summary['transactions']}")
    print(f"\n  Scenarios:")
    for s in summary["scenarios"]:
        print(f"    - {s['scenario']} [{s['severity']}]: {s['details']}")

    print("\n" + "-" * 60)
    print("  Test endpoints with curl:")
    print("-" * 60)

    first_merchant_id = DEMO_MERCHANTS[0]["id"]
    print(f"\n  # Dashboard")
    print(f'  curl http://localhost:8000/api/dashboard \\')
    print(f'    -H "X-Merchant-API-Key: rzp_merchant_{first_merchant_id}"')

    print(f"\n  # Health")
    print(f"  curl http://localhost:8000/health")

    print(f"\n  # Metrics")
    print(f'  curl http://localhost:8000/api/metrics \\')
    print(f'    -H "X-Merchant-API-Key: rzp_merchant_{first_merchant_id}"')

    print(f"\n  # Dashboard UI")
    print(f"  Open: http://localhost:8000")

    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Generate demo data for razorflow-ops")
    parser.add_argument(
        "--merchants", type=int, default=5, help="Number of merchants (default: 5)"
    )
    parser.add_argument(
        "--clean", action="store_true", help="Delete existing data before generating"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging"
    )
    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    print(f"\nGenerating demo data for {args.merchants} merchants...")
    summary = generate_demo(merchants_count=args.merchants, clean=args.clean)
    print_summary(summary)


if __name__ == "__main__":
    main()
