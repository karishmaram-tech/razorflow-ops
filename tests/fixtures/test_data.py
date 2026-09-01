"""Pytest fixtures and factory functions for creating test records.

Every factory returns an *unsaved* ORM object — the caller is responsible
for ``session.add()`` / ``session.commit()``.  This keeps fixtures composable
and avoids hidden side-effects.

Usage in tests::

    from tests.fixtures.test_data import create_merchant, create_settlement

    def test_something(db_session):
        merchant = create_merchant(session=db_session, business_name="Acme")
        session.add(merchant)
        session.commit()
        ...
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy.orm import Session

from src.data.models import (
    Anomaly,
    AnomalyStatus,
    AnomalyType,
    Diagnosis,
    Dispute,
    DisputeEvidence,
    DisputeEvidenceTemplate,
    DisputeStatus,
    DisputeType,
    EvaluationMetric,
    Merchant,
    RecommendedAction,
    Recommendation,
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

# ── Time helpers ───────────────────────────────────────────────────────────────

NOW = datetime.utcnow()


def _ago(days: int = 0, hours: int = 0) -> datetime:
    return NOW - timedelta(days=days, hours=hours)


def _future(days: int = 0, hours: int = 0) -> datetime:
    return NOW + timedelta(days=days, hours=hours)


def _date_ago(days: int) -> date:
    return (NOW - timedelta(days=days)).date()


# ── ID helpers ─────────────────────────────────────────────────────────────────

def _id(prefix: str = "") -> str:
    short = uuid.uuid4().hex[:12].upper()
    return f"{prefix}{short}" if prefix else short


# ── Factories ──────────────────────────────────────────────────────────────────


def create_merchant(
    *,
    session: Session | None = None,
    business_name: str | None = None,
    annual_revenue: Decimal | None = None,
    transaction_volume_monthly: int | None = None,
    dispute_rate: Decimal | None = None,
    industry_category: str | None = None,
    alert_threshold_severity: SeverityLevel = SeverityLevel.WARNING,
    notification_channels: list[str] | None = None,
    **extra: Any,
) -> Merchant:
    """Create a Merchant with sensible defaults."""
    m = Merchant(
        id=extra.pop("id", uuid.uuid4()),
        business_name=business_name or f"Test Merchant {uuid.uuid4().hex[:6]}",
        annual_revenue=annual_revenue or Decimal("10000000.00"),
        transaction_volume_monthly=transaction_volume_monthly or 10000,
        dispute_rate=dispute_rate or Decimal("2.50"),
        industry_category=industry_category or "E-Commerce",
        alert_threshold_severity=alert_threshold_severity,
        notification_channels=notification_channels or ["email"],
        **extra,
    )
    if session is not None:
        session.add(m)
        session.flush()
    return m


def create_transaction(
    *,
    session: Session | None = None,
    merchant: Merchant | None = None,
    merchant_id: uuid.UUID | None = None,
    amount: Decimal | None = None,
    status: str = "captured",
    created_at: datetime | None = None,
    **extra: Any,
) -> Transaction:
    """Create a Transaction linked to a merchant."""
    t = Transaction(
        id=extra.pop("id", _id("pay_")),
        merchant_id=merchant_id or (merchant.id if merchant else uuid.uuid4()),
        customer_id=extra.pop("customer_id", _id("cust_")),
        amount=amount or Decimal("5000.00"),
        currency="INR",
        status=status,
        payment_method=extra.pop("payment_method", "upi"),
        created_at=created_at or _ago(days=3),
        captured_at=created_at or _ago(days=3),
    )
    if session is not None:
        session.add(t)
        session.flush()
    return t


def create_settlement(
    *,
    session: Session | None = None,
    merchant: Merchant | None = None,
    merchant_id: uuid.UUID | None = None,
    amount: Decimal | None = None,
    status: SettlementStatus = SettlementStatus.SUCCESS,
    created_at: datetime | None = None,
    expected_arrival_at: datetime | None = None,
    actual_arrival_at: datetime | None = None,
    **extra: Any,
) -> Settlement:
    """Create a Settlement with configurable status and timestamps."""
    _created = created_at or _ago(days=3)
    _expected = expected_arrival_at or _future(days=0)
    _actual = actual_arrival_at
    if status == SettlementStatus.SUCCESS and _actual is None:
        _actual = _ago(days=0, hours=2)

    _amount = amount or Decimal("150000.00")
    fee = (_amount * Decimal("0.02")).quantize(Decimal("0.01"))
    tax = (fee * Decimal("0.18")).quantize(Decimal("0.01"))

    s = Settlement(
        id=extra.pop("id", _id("settle_")),
        merchant_id=merchant_id or (merchant.id if merchant else uuid.uuid4()),
        amount=_amount,
        currency="INR",
        status=status,
        created_at=_created,
        expected_arrival_at=_expected,
        actual_arrival_at=_actual,
        fees=fee,
        taxes=tax,
        net_amount=max(_amount - fee - tax, Decimal("0.00")),
        settlement_period_start=extra.pop("settlement_period_start", _date_ago(1)),
        settlement_period_end=extra.pop("settlement_period_end", _date_ago(0)),
        related_refunds=extra.pop("related_refunds", []),
        related_disputes=extra.pop("related_disputes", []),
        **extra,
    )
    if session is not None:
        session.add(s)
        session.flush()
    return s


def create_settlement_attempt(
    *,
    session: Session | None = None,
    settlement: Settlement | None = None,
    settlement_id: str | None = None,
    attempt_number: int = 1,
    method: TransferMethod = TransferMethod.IMPS,
    status: SettlementAttemptStatus = SettlementAttemptStatus.SUCCESS,
    initiated_at: datetime | None = None,
    **extra: Any,
) -> SettlementAttempt:
    """Create a SettlementAttempt."""
    a = SettlementAttempt(
        settlement_id=settlement_id or (settlement.id if settlement else _id("settle_")),
        attempt_number=attempt_number,
        method=method,
        initiated_at=initiated_at or _ago(hours=attempt_number * 2),
        response_code=extra.pop("response_code", "200" if status == SettlementAttemptStatus.SUCCESS else "500"),
        response_message=extra.pop("response_message", "OK"),
        status=status,
        bank_reference_id=extra.pop("bank_reference_id", _id("BANK")),
    )
    if session is not None:
        session.add(a)
        session.flush()
    return a


def create_refund(
    *,
    session: Session | None = None,
    merchant: Merchant | None = None,
    merchant_id: uuid.UUID | None = None,
    transaction: Transaction | None = None,
    transaction_id: str | None = None,
    amount: Decimal | None = None,
    status: RefundStatus = RefundStatus.SUCCESS,
    reason: RefundReason = RefundReason.CUSTOMER_REQUESTED,
    created_at: datetime | None = None,
    related_dispute_id: str | None = None,
    **extra: Any,
) -> Refund:
    """Create a Refund."""
    _created = created_at or _ago(days=2)
    _expected = _created + timedelta(days=3)
    _actual = _ago(days=0) if status == RefundStatus.SUCCESS else None

    r = Refund(
        id=extra.pop("id", _id("rfnd_")),
        merchant_id=merchant_id or (merchant.id if merchant else uuid.uuid4()),
        transaction_id=transaction_id or (transaction.id if transaction else _id("pay_")),
        customer_id=extra.pop("customer_id", _id("cust_")),
        amount=amount or Decimal("2500.00"),
        reason=reason,
        status=status,
        created_at=_created,
        expected_completion_at=_expected,
        actual_completion_at=_actual,
        initiated_by=extra.pop("initiated_by", RefundInitiator.MERCHANT),
        related_dispute_id=related_dispute_id,
    )
    if session is not None:
        session.add(r)
        session.flush()
    return r


def create_dispute(
    *,
    session: Session | None = None,
    merchant: Merchant | None = None,
    merchant_id: uuid.UUID | None = None,
    transaction: Transaction | None = None,
    transaction_id: str | None = None,
    amount: Decimal | None = None,
    dtype: DisputeType = DisputeType.CHARGEBACK,
    reason_code: str = "4855",
    status: DisputeStatus = DisputeStatus.EVIDENCE_PENDING,
    filed_at: datetime | None = None,
    related_refund_id: str | None = None,
    **extra: Any,
) -> Dispute:
    """Create a Dispute."""
    _filed = filed_at or _ago(days=5)
    d = Dispute(
        id=extra.pop("id", _id("disp_")),
        merchant_id=merchant_id or (merchant.id if merchant else uuid.uuid4()),
        transaction_id=transaction_id or (transaction.id if transaction else _id("pay_")),
        related_refund_id=related_refund_id,
        type=dtype,
        reason_code=reason_code,
        reason_text=extra.pop("reason_text", f"Dispute code {reason_code}"),
        amount=amount or Decimal("10000.00"),
        filed_at=_filed,
        evidence_deadline=_filed + timedelta(days=7),
        resolution_deadline=_filed + timedelta(days=30),
        current_status=status,
        won=extra.pop("won", None),
        outcome_amount=extra.pop("outcome_amount", None),
        resolved_at=extra.pop("resolved_at", None),
    )
    if session is not None:
        session.add(d)
        session.flush()
    return d


def create_dispute_evidence(
    *,
    session: Session | None = None,
    dispute: Dispute | None = None,
    dispute_id: str | None = None,
    evidence_type: str = "proof_of_delivery",
    is_verified: bool = False,
    uploaded_at: datetime | None = None,
    **extra: Any,
) -> DisputeEvidence:
    """Create a DisputeEvidence record."""
    from src.data.models import EvidenceType

    # Map string to enum
    ev_type = evidence_type
    if isinstance(evidence_type, str):
        try:
            ev_type = EvidenceType(evidence_type)
        except ValueError:
            ev_type = EvidenceType.PROOF_OF_DELIVERY

    e = DisputeEvidence(
        id=uuid.uuid4(),
        dispute_id=dispute_id or (dispute.id if dispute else _id("disp_")),
        evidence_type=ev_type,
        file_url=extra.pop("file_url", f"https://s3.example.com/{_id()}.pdf"),
        uploaded_at=uploaded_at or _ago(days=1),
        is_verified=is_verified,
    )
    if session is not None:
        session.add(e)
        session.flush()
    return e


def create_dispute_with_evidence(
    *,
    session: Session | None = None,
    merchant: Merchant | None = None,
    n_evidence: int = 2,
    **dispute_kwargs: Any,
) -> tuple[Dispute, list[DisputeEvidence]]:
    """Create a Dispute and attach *n_evidence* evidence records.

    Returns ``(dispute, [evidence, ...])``.
    """
    d = create_dispute(session=session, merchant=merchant, **dispute_kwargs)
    evidence_list = [
        create_dispute_evidence(session=session, dispute=d) for _ in range(n_evidence)
    ]
    return d, evidence_list


def create_anomaly(
    *,
    session: Session | None = None,
    merchant: Merchant | None = None,
    merchant_id: uuid.UUID | None = None,
    anomaly_type: AnomalyType = AnomalyType.SETTLEMENT_DELAYED,
    severity: SeverityLevel = SeverityLevel.WARNING,
    status: AnomalyStatus = AnomalyStatus.OPEN,
    settlement_id: str | None = None,
    refund_id: str | None = None,
    dispute_id: str | None = None,
    detected_at: datetime | None = None,
    root_cause: str | None = "bank_processing_delay",
    root_cause_confidence: Decimal | None = Decimal("0.85"),
    **extra: Any,
) -> Anomaly:
    """Create an Anomaly."""
    a = Anomaly(
        id=uuid.uuid4(),
        merchant_id=merchant_id or (merchant.id if merchant else uuid.uuid4()),
        anomaly_type=anomaly_type,
        related_settlement_id=settlement_id,
        related_refund_id=refund_id,
        related_dispute_id=dispute_id,
        detected_at=detected_at or _ago(days=1),
        root_cause=root_cause,
        root_cause_confidence=root_cause_confidence,
        status=status,
        severity=severity,
        recommended_action=extra.pop("recommended_action", f"Address {anomaly_type.value}"),
        resolved_at=extra.pop("resolved_at", None),
    )
    if session is not None:
        session.add(a)
        session.flush()
    return a


def create_anomaly_scenario(
    *,
    session: Session | None = None,
    merchant: Merchant | None = None,
    anomaly_type: AnomalyType = AnomalyType.SETTLEMENT_DELAYED,
    severity: SeverityLevel = SeverityLevel.WARNING,
    anomaly_status: AnomalyStatus = AnomalyStatus.OPEN,
    with_diagnosis: bool = True,
    with_recommendation: bool = True,
) -> tuple[Anomaly, Diagnosis | None, Recommendation | None]:
    """Create a full anomaly → diagnosis → recommendation chain.

    Returns ``(anomaly, diagnosis_or_none, recommendation_or_none)``.
    """
    _merchant = merchant or create_merchant(session=session)
    anomaly = create_anomaly(
        session=session,
        merchant=_merchant,
        anomaly_type=anomaly_type,
        severity=severity,
        status=anomaly_status,
    )

    diagnosis = None
    if with_diagnosis:
        diagnosis = create_diagnosis(session=session, anomaly=anomaly)

    recommendation = None
    if with_recommendation:
        recommendation = create_recommendation(session=session, anomaly=anomaly)

    return anomaly, diagnosis, recommendation


def create_diagnosis(
    *,
    session: Session | None = None,
    anomaly: Anomaly | None = None,
    anomaly_id: uuid.UUID | None = None,
    category: str = "bank_processing_delay",
    confidence: Decimal | None = Decimal("0.85"),
    **extra: Any,
) -> Diagnosis:
    """Create a Diagnosis."""
    d = Diagnosis(
        id=uuid.uuid4(),
        anomaly_id=anomaly_id or (anomaly.id if anomaly else uuid.uuid4()),
        root_cause_category=category,
        root_cause_subcategory=extra.pop("subcategory", "automated"),
        explanation_plain_english=extra.pop(
            "explanation",
            f"Root cause analysis: {category}. Automated diagnosis generated.",
        ),
        confidence=confidence,
        evidence=extra.pop("evidence", {"source": "test"}),
        causal_chain=extra.pop("causal_chain", [
            {"step": 1, "event": "Trigger detected"},
            {"step": 2, "event": "Anomaly flagged"},
        ]),
    )
    if session is not None:
        session.add(d)
        session.flush()
    return d


def create_recommendation(
    *,
    session: Session | None = None,
    anomaly: Anomaly | None = None,
    anomaly_id: uuid.UUID | None = None,
    action: RecommendedAction = RecommendedAction.CONTACT_RAZORPAY,
    urgency: UrgencyLevel = UrgencyLevel.HIGH,
    merchant_followed: bool = False,
    **extra: Any,
) -> Recommendation:
    """Create a Recommendation."""
    r = Recommendation(
        id=uuid.uuid4(),
        anomaly_id=anomaly_id or (anomaly.id if anomaly else uuid.uuid4()),
        recommendation_text=extra.pop(
            "text",
            f"Recommended: {action.value} with {urgency.value} urgency",
        ),
        recommended_action=action,
        urgency=urgency,
        timeline=extra.pop("timeline", "24_hours"),
        expected_resolution_time_hours=extra.pop("expected_hours", 24),
        success_probability=extra.pop("success_probability", Decimal("0.80")),
        merchant_followed=merchant_followed,
        outcome_if_followed=extra.pop("outcome", None),
    )
    if session is not None:
        session.add(r)
        session.flush()
    return r


def create_evaluation_metric(
    *,
    session: Session | None = None,
    merchant: Merchant | None = None,
    merchant_id: uuid.UUID | None = None,
    metric_name: str = "settlement_success_rate",
    metric_value: float = 95.5,
    metric_unit: str = "%",
    **extra: Any,
) -> EvaluationMetric:
    """Create an EvaluationMetric."""
    m = EvaluationMetric(
        id=uuid.uuid4(),
        merchant_id=merchant_id or (merchant.id if merchant else uuid.uuid4()),
        metric_name=metric_name,
        metric_value=Decimal(str(metric_value)),
        metric_unit=metric_unit,
        dimensions=extra.pop("dimensions", {}),
        recorded_at=extra.pop("recorded_at", NOW),
    )
    if session is not None:
        session.add(m)
        session.flush()
    return m


# ── Batch helpers ──────────────────────────────────────────────────────────────


def create_merchant_with_full_profile(
    *, session: Session, n_settlements: int = 3, n_refunds: int = 2, n_disputes: int = 1
) -> dict:
    """Create a merchant with a full cascade of related records.

    Returns a dict with all created objects for easy assertion in tests.
    """
    merchant = create_merchant(session=session)
    settlements = [
        create_settlement(session=session, merchant=merchant) for _ in range(n_settlements)
    ]
    txns = [
        create_transaction(session=session, merchant=merchant) for _ in range(n_refunds + n_disputes)
    ]
    refunds = [
        create_refund(session=session, merchant=merchant, transaction=txns[i])
        for i in range(min(n_refunds, len(txns)))
    ]
    disputes = [
        create_dispute(session=session, merchant=merchant, transaction=txns[min(n_refunds, len(txns)) + i])
        for i in range(min(n_disputes, len(txns) - n_refunds))
    ]

    return {
        "merchant": merchant,
        "settlements": settlements,
        "transactions": txns,
        "refunds": refunds,
        "disputes": disputes,
    }
