#!/usr/bin/env python3
"""Generate realistic test data for the Merchant Payment Operations Intelligence agent.

Creates 100 merchants with settlements, refunds, disputes, anomalies,
diagnoses, and recommendations using realistic Razorpay patterns.

Usage:
    cd merchant-payment-ops-agent
    python scripts/load_test_data.py
"""

from __future__ import annotations

import logging
import random
import sys
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import settings  # noqa: E402
from src.data.models import (  # noqa: E402
    Anomaly,
    AnomalyStatus,
    AnomalyType,
    Base,
    Diagnosis,
    Dispute,
    DisputeEvidence,
    DisputeEvidenceTemplate,
    DisputeStatus,
    DisputeType,
    EvaluationMetric,
    Merchant,
    Recommendation,
    RecommendedAction,
    Refund,
    RefundInitiator,
    RefundReason,
    RefundStatus,
    Settlement,
    SettlementAttempt,
    SettlementAttemptStatus,
    SettlementStatus,
    SeverityLevel,
    Transaction,
    TransferMethod,
    UrgencyLevel,
)

logger = logging.getLogger("load_test_data")

# ── Constants ──────────────────────────────────────────────────────────────────

NOW = datetime.utcnow()

INDUSTRIES = [
    "E-Commerce",
    "SaaS",
    "Education",
    "Healthcare",
    "Food & Beverage",
    "Travel & Hospitality",
    "Digital Marketing",
    "Gaming",
    "Fitness & Wellness",
    "Fashion & Apparel",
    "Electronics",
    "Grocery & Essentials",
]

BUSINESS_PREFIXES = [
    "Quick", "Prime", "Nova", "Apex", "Zen", "Blu", "Nexa", "Swift",
    "Pure", "Core", "Vibe", "Urban", "Bright", "Eco", "Byte", "Cloud",
]

BUSINESS_SUFFIXES = [
    "Mart", "Shop", "Solutions", "Hub", "Store", "Kart", "Dealz",
    "Direct", "Express", "Point", "Zone", "World", "Go", "Box", "Nest",
]

DISPUTE_REASON_CODES = [
    ("4855", "Goods/services not received", DisputeType.CHARGEBACK),
    ("4849", "Transaction not authorised", DisputeType.CHARGEBACK),
    ("4871", "Incorrect transaction amount", DisputeType.CHARGEBACK),
    ("4863", "Cardholder does not recognise transaction", DisputeType.RETRIEVAL),
    ("10.4", "Other", DisputeType.COMPLAINT),
]

BANK_REFERENCE_PREFIXES = ["HDFC", "ICICI", "SBIN", "UTIB", "KKBK", "PUNB", "BARB"]

# ── Helpers ────────────────────────────────────────────────────────────────────


def _new_id(prefix: str = "") -> str:
    short = uuid.uuid4().hex[:12].upper()
    return f"{prefix}{short}" if prefix else short


def _random_amount(lo: Decimal, hi: Decimal) -> Decimal:
    cents = random.randint(int(lo * 100), int(hi * 100))
    return Decimal(cents) / Decimal(100)


def _add_days(dt: datetime, days: int) -> datetime:
    return dt + timedelta(days=days)


def _add_hours(dt: datetime, hours: int) -> datetime:
    return dt + timedelta(hours=hours)


def _rnd_date(lo_days: int, hi_days: int) -> datetime:
    return _add_days(NOW, random.randint(-hi_days, -lo_days))


def _random_method() -> TransferMethod:
    return random.choice(list(TransferMethod))


def _bank_ref() -> str:
    return f"{random.choice(BANK_REFERENCE_PREFIXES)}{_new_id()[:8]}"


# ── Generators ─────────────────────────────────────────────────────────────────


def _make_merchants(n: int) -> list[Merchant]:
    merchants = []
    for _ in range(n):
        name = f"{random.choice(BUSINESS_PREFIXES)} {random.choice(BUSINESS_SUFFIXES)}"
        m = Merchant(
            id=uuid.uuid4(),
            business_name=name,
            annual_revenue=_random_amount(Decimal("500000"), Decimal("50000000")),
            transaction_volume_monthly=random.randint(500, 100000),
            dispute_rate=_random_amount(Decimal("0.01"), Decimal("8.00")),
            industry_category=random.choice(INDUSTRIES),
            alert_threshold_severity=random.choice(list(SeverityLevel)),
            notification_channels=random.choice(
                [["email"], ["sms"], ["email", "slack"], ["email", "sms", "whatsapp"]]
            ),
        )
        merchants.append(m)
    return merchants


def _make_transactions(
    merchant: Merchant, n: int, session: Session
) -> list[Transaction]:
    txns = []
    for _ in range(n):
        t = Transaction(
            id=_new_id("pay_"),
            merchant_id=merchant.id,
            customer_id=_new_id("cust_"),
            amount=_random_amount(Decimal("100"), Decimal("50000")),
            currency="INR",
            status=random.choice(["captured", "captured", "captured", "failed"]),
            payment_method=random.choice(
                ["upi", "card", "netbanking", "wallet", "emi"]
            ),
            created_at=_rnd_date(1, 60),
            captured_at=_rnd_date(1, 58),
        )
        session.add(t)
        txns.append(t)
    return txns


def _make_settlement(
    merchant: Merchant,
    session: Session,
    *,
    status_override: SettlementStatus | None = None,
    created: datetime | None = None,
    expected: datetime | None = None,
) -> Settlement:
    status = status_override or random.choice(
        [
            SettlementStatus.SUCCESS,
            SettlementStatus.SUCCESS,
            SettlementStatus.SUCCESS,
            SettlementStatus.PENDING,
            SettlementStatus.PARTIAL,
            SettlementStatus.FAILED,
        ]
    )

    created_at = created or _rnd_date(1, 30)
    # T+2 working days ≈ +3 calendar days
    expected_at = expected or _add_days(created_at, 3)
    actual_at: datetime | None = None
    if status == SettlementStatus.SUCCESS:
        actual_at = _add_hours(expected_at, random.randint(-12, 24))
    elif status == SettlementStatus.FAILED:
        actual_at = None

    amount = _random_amount(Decimal("10000"), Decimal("500000"))
    fee_pct = Decimal("0.02")  # 2%
    fee = (amount * fee_pct).quantize(Decimal("0.01"))
    tax = (fee * Decimal("0.18")).quantize(Decimal("0.01"))
    net = amount - fee - tax

    period_start = created_at.date() - timedelta(days=1)
    period_end = created_at.date()

    s = Settlement(
        id=_new_id("settle_"),
        merchant_id=merchant.id,
        amount=amount,
        currency="INR",
        status=status,
        created_at=created_at,
        expected_arrival_at=expected_at,
        actual_arrival_at=actual_at,
        fees=fee,
        taxes=tax,
        net_amount=max(net, Decimal("0.00")),
        settlement_period_start=period_start,
        settlement_period_end=period_end,
        related_refunds=[],
        related_disputes=[],
        last_checked_at=NOW if status in (SettlementStatus.PENDING, SettlementStatus.PARTIAL) else actual_at,
    )
    session.add(s)
    return s


def _make_settlement_attempt(
    settlement: Settlement,
    session: Session,
    *,
    attempt_number: int = 1,
    status_override: SettlementAttemptStatus | None = None,
    method_override: TransferMethod | None = None,
) -> SettlementAttempt:
    status = status_override or SettlementAttemptStatus.SUCCESS
    initiated_at = _add_hours(settlement.created_at, attempt_number * 2)
    resp_code = "200" if status == SettlementAttemptStatus.SUCCESS else "500"
    resp_msg = (
        "Transfer successful" if status == SettlementAttemptStatus.SUCCESS
        else random.choice(["Bank timeout", "Insufficient funds", "Invalid account"])
    )

    a = SettlementAttempt(
        settlement_id=settlement.id,
        attempt_number=attempt_number,
        method=method_override or _random_method(),
        initiated_at=initiated_at,
        response_code=resp_code,
        response_message=resp_msg,
        status=status,
        bank_reference_id=_bank_ref() if status == SettlementAttemptStatus.SUCCESS else None,
    )
    session.add(a)
    return a


def _make_refund(
    merchant: Merchant,
    transaction: Transaction,
    session: Session,
    *,
    status_override: RefundStatus | None = None,
    created: datetime | None = None,
    related_dispute_id: str | None = None,
) -> Refund:
    status = status_override or random.choice(
        [RefundStatus.SUCCESS, RefundStatus.SUCCESS, RefundStatus.PENDING,
         RefundStatus.PROCESSING, RefundStatus.FAILED]
    )
    created_at = created or _rnd_date(1, 20)
    expected_at = _add_days(created_at, 3)
    actual_at = None
    if status == RefundStatus.SUCCESS:
        actual_at = _add_hours(expected_at, random.randint(-6, 18))

    r = Refund(
        id=_new_id("rfnd_"),
        merchant_id=merchant.id,
        transaction_id=transaction.id,
        customer_id=transaction.customer_id,
        amount=min(transaction.amount, _random_amount(Decimal("500"), Decimal("50000"))),
        reason=random.choice(list(RefundReason)),
        status=status,
        created_at=created_at,
        expected_completion_at=expected_at,
        actual_completion_at=actual_at,
        initiated_by=random.choice(list(RefundInitiator)),
        bank_response_code="200" if status == RefundStatus.SUCCESS else None,
        bank_response_message="Refund processed" if status == RefundStatus.SUCCESS else None,
        related_dispute_id=related_dispute_id,
    )
    session.add(r)
    return r


def _make_dispute(
    merchant: Merchant,
    transaction: Transaction,
    session: Session,
    *,
    status_override: DisputeStatus | None = None,
    filed: datetime | None = None,
    related_refund_id: str | None = None,
) -> Dispute:
    code, text_val, dtype = random.choice(DISPUTE_REASON_CODES)
    status = status_override or random.choice(
        [DisputeStatus.EVIDENCE_PENDING, DisputeStatus.UNDER_REVIEW,
         DisputeStatus.WON, DisputeStatus.LOST]
    )
    filed_at = filed or _rnd_date(1, 14)
    evidence_deadline = _add_days(filed_at, 7)
    resolution_deadline = _add_days(filed_at, 30)

    won_flag: bool | None = None
    outcome_amount: Decimal | None = None
    resolved_at: datetime | None = None
    if status in (DisputeStatus.WON, DisputeStatus.LOST):
        won_flag = status == DisputeStatus.WON
        outcome_amount = transaction.amount if won_flag else Decimal("0.00")
        resolved_at = _add_days(evidence_deadline, random.randint(5, 20))

    d = Dispute(
        id=_new_id("disp_"),
        merchant_id=merchant.id,
        transaction_id=transaction.id,
        related_refund_id=related_refund_id,
        type=dtype,
        reason_code=code,
        reason_text=text_val,
        amount=transaction.amount,
        filed_at=filed_at,
        evidence_deadline=evidence_deadline,
        resolution_deadline=resolution_deadline,
        current_status=status,
        won=won_flag,
        outcome_amount=outcome_amount,
        resolved_at=resolved_at,
    )
    session.add(d)
    return d


def _make_evidence(
    dispute: Dispute, session: Session
) -> DisputeEvidence:
    from src.data.models import EvidenceType

    ev = DisputeEvidence(
        id=uuid.uuid4(),
        dispute_id=dispute.id,
        evidence_type=random.choice(list(EvidenceType)),
        file_url=f"https://evidence.s3.amazonaws.com/{_new_id()}.pdf",
        uploaded_at=_add_days(dispute.filed_at, random.randint(0, 3)),
        is_verified=random.choice([True, False]),
    )
    session.add(ev)
    return ev


def _make_anomaly(
    merchant: Merchant,
    session: Session,
    *,
    anomaly_type_override: AnomalyType | None = None,
    severity_override: SeverityLevel | None = None,
    status_override: AnomalyStatus | None = None,
    settlement_id: str | None = None,
    refund_id: str | None = None,
    dispute_id: str | None = None,
    detected: datetime | None = None,
) -> Anomaly:
    atype = anomaly_type_override or random.choice(list(AnomalyType))
    severity = severity_override or random.choice(list(SeverityLevel))
    status = status_override or random.choice(list(AnomalyStatus))
    detected_at = detected or _rnd_date(0, 7)

    root_cause_map = {
        AnomalyType.SETTLEMENT_DELAYED: ("bank_processing_delay", "NEFT batch queue backlog"),
        AnomalyType.SETTLEMENT_PARTIAL: ("refund_offset", "Partial amount retained for refunds"),
        AnomalyType.SETTLEMENT_FAILED: ("bank_account_mismatch", "Incorrect IFSC or account number"),
        AnomalyType.REFUND_STUCK: ("pg_processing_queue", "Refund queued in intermediate state"),
        AnomalyType.REFUND_FAILED: ("bank_rejection", "Customer bank rejected credit"),
        AnomalyType.DISPUTE_EVIDENCE_INCOMPLETE: ("missing_delivery_proof", "No tracking number uploaded"),
        AnomalyType.DISPUTE_DEADLINE_APPROACHING: ("evidence_gathering_delay", "Merchant hasn't responded"),
        AnomalyType.HIGH_DISPUTE_RATE: ("product_quality_issue", "Elevated complaints in category"),
        AnomalyType.UNUSUAL_TRANSACTION_PATTERN: ("potential_fraud", "Abnormal geo + velocity pattern"),
    }
    rc_cat, rc_sub = root_cause_map.get(atype, ("unknown", "unclassified"))

    a = Anomaly(
        id=uuid.uuid4(),
        merchant_id=merchant.id,
        anomaly_type=atype,
        related_settlement_id=settlement_id,
        related_refund_id=refund_id,
        related_dispute_id=dispute_id,
        detected_at=detected_at,
        root_cause=rc_cat,
        root_cause_confidence=_random_amount(Decimal("0.50"), Decimal("0.99")),
        status=status,
        severity=severity,
        recommended_action=f"Follow up on {atype.value}",
        merchant_action_taken=None,
        resolved_at=_add_days(detected_at, random.randint(1, 5)) if status == AnomalyStatus.RESOLVED else None,
    )
    session.add(a)
    return a


def _make_diagnosis(anomaly: Anomaly, session: Session) -> Diagnosis:
    causal_chain = [
        {"step": 1, "event": "Transaction initiated", "timestamp": str(anomaly.detected_at)},
        {"step": 2, "event": "Processing delay detected", "timestamp": str(_add_hours(anomaly.detected_at, 2))},
        {"step": 3, "event": "Anomaly flagged", "timestamp": str(anomaly.detected_at)},
    ]
    d = Diagnosis(
        id=uuid.uuid4(),
        anomaly_id=anomaly.id,
        root_cause_category=anomaly.root_cause or "unclassified",
        root_cause_subcategory="automated_analysis",
        explanation_plain_english=(
            f"The anomaly of type '{anomaly.anomaly_type.value}' was detected "
            f"for merchant {anomaly.merchant_id}. Root cause: {anomaly.root_cause}. "
            f"Confidence: {anomaly.root_cause_confidence}."
        ),
        confidence=anomaly.root_cause_confidence,
        evidence={"anomaly_id": str(anomaly.id), "type": anomaly.anomaly_type.value},
        causal_chain=causal_chain,
    )
    session.add(d)
    return d


def _make_recommendation(anomaly: Anomaly, session: Session) -> Recommendation:
    action_map = {
        AnomalyType.SETTLEMENT_DELAYED: RecommendedAction.CONTACT_BANK,
        AnomalyType.SETTLEMENT_PARTIAL: RecommendedAction.WAIT,
        AnomalyType.SETTLEMENT_FAILED: RecommendedAction.CONTACT_RAZORPAY,
        AnomalyType.REFUND_STUCK: RecommendedAction.CONTACT_RAZORPAY,
        AnomalyType.REFUND_FAILED: RecommendedAction.CONTACT_BANK,
        AnomalyType.DISPUTE_EVIDENCE_INCOMPLETE: RecommendedAction.RESUBMIT_EVIDENCE,
        AnomalyType.DISPUTE_DEADLINE_APPROACHING: RecommendedAction.ESCALATE,
        AnomalyType.HIGH_DISPUTE_RATE: RecommendedAction.WAIT,
        AnomalyType.UNUSUAL_TRANSACTION_PATTERN: RecommendedAction.ESCALATE,
    }
    action = action_map.get(anomaly.anomaly_type, RecommendedAction.WAIT)

    urgency_map = {
        SeverityLevel.CRITICAL: UrgencyLevel.CRITICAL,
        SeverityLevel.WARNING: UrgencyLevel.HIGH,
        SeverityLevel.INFO: UrgencyLevel.LOW,
    }
    urgency = urgency_map.get(anomaly.severity, UrgencyLevel.MEDIUM)

    timeline_map = {
        UrgencyLevel.CRITICAL: "immediate",
        UrgencyLevel.HIGH: "24_hours",
        UrgencyLevel.MEDIUM: "48_hours",
        UrgencyLevel.LOW: "1_week",
    }

    r = Recommendation(
        id=uuid.uuid4(),
        anomaly_id=anomaly.id,
        recommendation_text=f"Action required: {action.value} for {anomaly.anomaly_type.value}",
        recommended_action=action,
        urgency=urgency,
        timeline=timeline_map.get(urgency, "48_hours"),
        expected_resolution_time_hours={
            UrgencyLevel.CRITICAL: 4,
            UrgencyLevel.HIGH: 24,
            UrgencyLevel.MEDIUM: 48,
            UrgencyLevel.LOW: 168,
        }.get(urgency, 48),
        success_probability=_random_amount(Decimal("0.50"), Decimal("0.95")),
        merchant_followed=random.choice([True, False]),
        outcome_if_followed="Resolved" if random.random() > 0.3 else "Pending",
    )
    session.add(r)
    return r


def _make_evaluation_metric(
    merchant: Merchant, session: Session, metric_name: str, value: float, unit: str
) -> EvaluationMetric:
    m = EvaluationMetric(
        id=uuid.uuid4(),
        merchant_id=merchant.id,
        metric_name=metric_name,
        metric_value=Decimal(str(value)),
        metric_unit=unit,
        dimensions={"source": "test_data_loader"},
        recorded_at=_rnd_date(0, 7),
    )
    session.add(m)
    return m


# ── Edge cases ─────────────────────────────────────────────────────────────────


def _create_edge_cases(merchants: list[Merchant], session: Session) -> None:
    """Inject specific problematic scenarios for agent testing."""
    logger.info("Creating edge-case scenarios …")

    # 1. Delayed settlement (past T+2)
    m1 = merchants[0]
    delayed = _make_settlement(
        m1, session,
        status_override=SettlementStatus.PENDING,
        created=_add_days(NOW, -5),
        expected=_add_days(NOW, -2),
    )
    _make_settlement_attempt(delayed, session, status_override=SettlementAttemptStatus.SUCCESS)
    _make_anomaly(
        m1, session,
        anomaly_type_override=AnomalyType.SETTLEMENT_DELAYED,
        severity_override=SeverityLevel.CRITICAL,
        status_override=AnomalyStatus.OPEN,
        settlement_id=delayed.id,
        detected=_add_days(NOW, -1),
    )

    # 2. Failed settlement with 3 retry attempts
    m2 = merchants[1]
    failed = _make_settlement(
        m2, session,
        status_override=SettlementStatus.FAILED,
        created=_add_days(NOW, -4),
    )
    _make_settlement_attempt(failed, session, attempt_number=1, status_override=SettlementAttemptStatus.FAILED, method_override=TransferMethod.NEFT)
    _make_settlement_attempt(failed, session, attempt_number=2, status_override=SettlementAttemptStatus.FAILED, method_override=TransferMethod.IMPS)
    _make_settlement_attempt(failed, session, attempt_number=3, status_override=SettlementAttemptStatus.FAILED, method_override=TransferMethod.RTGS)
    _make_anomaly(
        m2, session,
        anomaly_type_override=AnomalyType.SETTLEMENT_FAILED,
        severity_override=SeverityLevel.CRITICAL,
        status_override=AnomalyStatus.OPEN,
        settlement_id=failed.id,
    )

    # 3. Stuck refund (>3 days in processing)
    m3 = merchants[2]
    txn3 = _make_transactions(m3, 1, session)[0]
    stuck_refund = _make_refund(
        m3, txn3, session,
        status_override=RefundStatus.PROCESSING,
        created=_add_days(NOW, -5),
    )
    _make_anomaly(
        m3, session,
        anomaly_type_override=AnomalyType.REFUND_STUCK,
        severity_override=SeverityLevel.WARNING,
        status_override=AnomalyStatus.OPEN,
        refund_id=stuck_refund.id,
    )

    # 4. Dispute with missing evidence (deadline approaching)
    m4 = merchants[3]
    txn4 = _make_transactions(m4, 1, session)[0]
    upcoming_disp = _make_dispute(
        m4, txn4, session,
        status_override=DisputeStatus.EVIDENCE_PENDING,
        filed=_add_days(NOW, -5),  # deadline in 2 days
    )
    _make_anomaly(
        m4, session,
        anomaly_type_override=AnomalyType.DISPUTE_DEADLINE_APPROACHING,
        severity_override=SeverityLevel.CRITICAL,
        status_override=AnomalyStatus.OPEN,
        dispute_id=upcoming_disp.id,
    )

    # 5. High-dispute-rate merchant (3+ disputes)
    m5 = merchants[4]
    m5.dispute_rate = Decimal("12.50")
    m5.alert_threshold_severity = SeverityLevel.WARNING
    txns5 = _make_transactions(m5, 3, session)
    for txn in txns5:
        d = _make_dispute(m5, txn, session, filed=_rnd_date(2, 20))
        # give each dispute some evidence
        _make_evidence(d, session)
    _make_anomaly(
        m5, session,
        anomaly_type_override=AnomalyType.HIGH_DISPUTE_RATE,
        severity_override=SeverityLevel.WARNING,
        status_override=AnomalyStatus.IN_PROGRESS,
    )

    logger.info("Edge cases created.")


# ── Main ───────────────────────────────────────────────────────────────────────


def _build_engine() -> Engine:
    return create_engine(settings.database_url_sync, pool_pre_ping=True, echo=False)


def main() -> None:
    logging.basicConfig(
        level=logging.DEBUG if settings.debug else logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    )

    engine = _build_engine()
    random.seed(42)  # reproducible data

    try:
        logger.info("Generating test data …")

        with Session(engine) as session:
            # Merchants
            merchants = _make_merchants(100)
            session.add_all(merchants)
            session.flush()
            logger.info("Created %d merchants.", len(merchants))

            # Per-merchant records
            all_disputes: list[Dispute] = []
            for merchant in merchants:
                n_settlements = random.randint(10, 20)
                n_txn = random.randint(10, 20)
                n_refunds = random.randint(5, 10)
                n_disputes = random.randint(3, 5)

                # Transactions (needed by refunds and disputes)
                txns = _make_transactions(merchant, n_txn, session)

                # Settlements
                for _ in range(n_settlements):
                    _make_settlement(merchant, session)

                # Refunds (some linked to disputes later)
                refund_txns = random.sample(txns, min(n_refunds, len(txns)))
                refunds = []
                for txn in refund_txns:
                    r = _make_refund(merchant, txn, session)
                    refunds.append(r)

                # Disputes (some with related refunds)
                dispute_txns = random.sample(txns, min(n_disputes, len(txns)))
                for i, txn in enumerate(dispute_txns):
                    rel_refund_id = refunds[i].id if i < len(refunds) else None
                    disp = _make_dispute(
                        merchant, txn, session,
                        related_refund_id=rel_refund_id,
                    )
                    all_disputes.append(disp)

                    # Partial evidence on ~60% of disputes
                    if random.random() < 0.6:
                        _make_evidence(disp, session)

            # Anomalies with diagnoses + recommendations for ~30 merchants
            sample_merchants = random.sample(merchants, min(30, len(merchants)))
            for merchant in sample_merchants:
                n_anomalies = random.randint(1, 3)
                for _ in range(n_anomalies):
                    anomaly = _make_anomaly(merchant, session)
                    # Diagnosis on ~70% of anomalies
                    if random.random() < 0.7:
                        _make_diagnosis(anomaly, session)
                    # Recommendation always
                    _make_recommendation(anomaly, session)

            # Evaluation metrics
            metric_names = [
                ("settlement_success_rate", "%"),
                ("avg_refund_processing_hours", "hours"),
                ("dispute_win_rate", "%"),
                ("avg_settlement_tat_hours", "hours"),
                ("customer_satisfaction_score", "score"),
            ]
            for merchant in random.sample(merchants, min(50, len(merchants))):
                for name, unit in random.sample(metric_names, k=random.randint(2, 4)):
                    _make_evaluation_metric(
                        merchant, session,
                        metric_name=name,
                        value=round(random.uniform(50, 99), 2),
                        unit=unit,
                    )

            # Edge cases
            _create_edge_cases(merchants, session)

            session.commit()

        logger.info("✅  Test data loaded successfully.")
        _print_summary(engine)

    except Exception:
        logger.exception("❌  Test data loading FAILED")
        sys.exit(1)
    finally:
        engine.dispose()


def _print_summary(engine: Engine) -> None:
    """Print row counts for every table."""
    with engine.connect() as conn:
        tables = [
            "merchants", "settlements", "settlement_attempts",
            "transactions", "refunds", "disputes", "dispute_evidence",
            "dispute_evidence_templates", "anomalies", "diagnoses",
            "recommendations", "evaluation_metrics",
        ]
        print("\n" + "=" * 50)
        print("  DATA SUMMARY")
        print("=" * 50)
        for t in tables:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
            print(f"  {t:<30s} {count:>6d}")
        print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
