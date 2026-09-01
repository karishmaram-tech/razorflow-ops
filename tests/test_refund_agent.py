"""Tests for src/agents/refund_agent.py — Refund anomaly pipeline.

Uses in-memory SQLite via the shared ``db_session`` fixture from test_setup.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from src.agents.refund_agent import (
    REFUND_ACTION_TREE,
    REFUND_TIMELINE_HOURS,
    RefundActionRecommender,
    RefundAnomalyDetector,
    RefundRootCauseClassifier,
)
from src.data.models import (
    Anomaly,
    AnomalyStatus,
    AnomalyType,
    Diagnosis,
    Dispute,
    DisputeStatus,
    DisputeType,
    Merchant,
    RecommendedAction,
    Recommendation,
    Refund,
    RefundInitiator,
    RefundReason,
    RefundStatus,
    SeverityLevel,
    Transaction,
    UrgencyLevel,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

NOW = datetime(2025, 6, 15, 12, 0, 0)


def _merchant(session) -> Merchant:
    m = Merchant(id=uuid.uuid4(), business_name="Refund Test Co")
    session.add(m)
    session.flush()
    return m


def _txn(session, *, merchant_id, amount=Decimal("5000.00")) -> Transaction:
    t = Transaction(
        id=f"pay_{uuid.uuid4().hex[:8]}",
        merchant_id=merchant_id,
        amount=amount,
        currency="INR",
        status="captured",
        created_at=NOW - timedelta(days=10),
    )
    session.add(t)
    session.flush()
    return t


def _refund(
    session,
    *,
    merchant_id,
    transaction_id: str,
    status: RefundStatus = RefundStatus.PENDING,
    amount: Decimal = Decimal("2500.00"),
    created_at: datetime | None = None,
    bank_response_code: str | None = None,
    bank_response_message: str | None = None,
    related_dispute_id: str | None = None,
    refund_id: str | None = None,
) -> Refund:
    r = Refund(
        id=refund_id or f"rfnd_{uuid.uuid4().hex[:8]}",
        merchant_id=merchant_id,
        transaction_id=transaction_id,
        amount=amount,
        reason=RefundReason.CUSTOMER_REQUESTED,
        status=status,
        created_at=created_at or (NOW - timedelta(days=5)),
        initiated_by=RefundInitiator.MERCHANT,
        bank_response_code=bank_response_code,
        bank_response_message=bank_response_message,
        related_dispute_id=related_dispute_id,
    )
    session.add(r)
    session.flush()
    return r


def _dispute(
    session,
    *,
    merchant_id,
    transaction_id: str,
    related_refund_id: str | None = None,
    status: DisputeStatus = DisputeStatus.EVIDENCE_PENDING,
) -> Dispute:
    d = Dispute(
        id=f"disp_{uuid.uuid4().hex[:8]}",
        merchant_id=merchant_id,
        transaction_id=transaction_id,
        related_refund_id=related_refund_id,
        type=DisputeType.CHARGEBACK,
        reason_code="4855",
        reason_text="Goods not received",
        amount=Decimal("5000.00"),
        filed_at=NOW - timedelta(days=3),
        current_status=status,
    )
    session.add(d)
    session.flush()
    return d


def _anomaly_for_refund(
    session,
    *,
    merchant_id,
    refund_id: str,
    anomaly_type: AnomalyType = AnomalyType.REFUND_STUCK,
) -> Anomaly:
    a = Anomaly(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        anomaly_type=anomaly_type,
        related_refund_id=refund_id,
        detected_at=NOW,
        root_cause="test",
        root_cause_confidence=Decimal("0.80"),
        status=AnomalyStatus.OPEN,
        severity=SeverityLevel.WARNING,
        recommended_action="Test",
    )
    session.add(a)
    session.flush()
    return a


def _diagnosis(
    session,
    *,
    anomaly_id,
    root_cause: str = "bank_processing_delay",
    confidence: Decimal = Decimal("0.80"),
) -> Diagnosis:
    d = Diagnosis(
        id=uuid.uuid4(),
        anomaly_id=anomaly_id,
        root_cause_category=root_cause,
        root_cause_subcategory="test",
        explanation_plain_english=f"Test for {root_cause}",
        confidence=confidence,
        evidence={"facts": ["test evidence"]},
        causal_chain=[],
    )
    session.add(d)
    session.flush()
    return d


# ══════════════════════════════════════════════════════════════════════════════
# 1. Anomaly Detection Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestDetectRefundStuck:
    """Test 1: Refund past T+3 working days."""

    def test_detect_refund_stuck(self, db_session):
        merchant = _merchant(db_session)
        txn = _txn(db_session, merchant_id=merchant.id)
        # Created 7 days ago, still PENDING → well past T+3
        refund = _refund(
            db_session,
            merchant_id=merchant.id,
            transaction_id=txn.id,
            status=RefundStatus.PENDING,
            created_at=NOW - timedelta(days=7),
        )

        detector = RefundAnomalyDetector(db_session, now=NOW)
        anomalies = detector.detect_anomalies(refund)

        stuck = [a for a in anomalies if a.anomaly_type == AnomalyType.REFUND_STUCK]
        assert len(stuck) == 1
        assert stuck[0].severity in (SeverityLevel.WARNING, SeverityLevel.CRITICAL)
        assert stuck[0].related_refund_id == refund.id

    def test_no_stuck_for_success(self, db_session):
        """Successful refunds should not be flagged."""
        merchant = _merchant(db_session)
        txn = _txn(db_session, merchant_id=merchant.id)
        refund = _refund(
            db_session,
            merchant_id=merchant.id,
            transaction_id=txn.id,
            status=RefundStatus.SUCCESS,
            created_at=NOW - timedelta(days=7),
        )

        anomalies = RefundAnomalyDetector(db_session, now=NOW).detect_anomalies(refund)
        stuck = [a for a in anomalies if a.anomaly_type == AnomalyType.REFUND_STUCK]
        assert len(stuck) == 0


class TestDetectRefundReversed:
    """Test 2: Reversed refund detection."""

    def test_detect_refund_reversed(self, db_session):
        merchant = _merchant(db_session)
        txn = _txn(db_session, merchant_id=merchant.id)
        refund = _refund(
            db_session,
            merchant_id=merchant.id,
            transaction_id=txn.id,
            status=RefundStatus.REVERSED,
            bank_response_code="50001",
            bank_response_message="Refund Rejected by Bank",
        )

        anomalies = RefundAnomalyDetector(db_session, now=NOW).detect_anomalies(refund)

        reversed_anomalies = [a for a in anomalies if a.anomaly_type == AnomalyType.REFUND_REVERSED]
        assert len(reversed_anomalies) == 1
        assert reversed_anomalies[0].severity == SeverityLevel.CRITICAL


class TestDetectRefundMismatch:
    """Test 3: Refund not received but dispute is active."""

    def test_detect_refund_mismatch(self, db_session):
        merchant = _merchant(db_session)
        txn = _txn(db_session, merchant_id=merchant.id)
        dispute = _dispute(
            db_session,
            merchant_id=merchant.id,
            transaction_id=txn.id,
            status=DisputeStatus.EVIDENCE_PENDING,
        )
        refund = _refund(
            db_session,
            merchant_id=merchant.id,
            transaction_id=txn.id,
            status=RefundStatus.PENDING,
            related_dispute_id=dispute.id,
        )

        anomalies = RefundAnomalyDetector(db_session, now=NOW).detect_anomalies(refund)

        mismatch = [a for a in anomalies if a.anomaly_type == AnomalyType.REFUND_MISMATCH]
        assert len(mismatch) == 1
        assert mismatch[0].severity == SeverityLevel.CRITICAL
        assert mismatch[0].related_dispute_id == dispute.id

    def test_no_mismatch_for_success_refund(self, db_session):
        """Successful refund with active dispute → no mismatch (refund was received)."""
        merchant = _merchant(db_session)
        txn = _txn(db_session, merchant_id=merchant.id)
        dispute = _dispute(
            db_session,
            merchant_id=merchant.id,
            transaction_id=txn.id,
            status=DisputeStatus.EVIDENCE_PENDING,
        )
        refund = _refund(
            db_session,
            merchant_id=merchant.id,
            transaction_id=txn.id,
            status=RefundStatus.SUCCESS,
            related_dispute_id=dispute.id,
        )

        anomalies = RefundAnomalyDetector(db_session, now=NOW).detect_anomalies(refund)
        mismatch = [a for a in anomalies if a.anomaly_type == AnomalyType.REFUND_MISMATCH]
        assert len(mismatch) == 0


class TestDetectDuplicateRefund:
    """Test 4: Multiple refunds for same transaction."""

    def test_detect_duplicate_refund(self, db_session):
        merchant = _merchant(db_session)
        txn = _txn(db_session, merchant_id=merchant.id)

        # First refund
        _refund(
            db_session,
            merchant_id=merchant.id,
            transaction_id=txn.id,
            status=RefundStatus.SUCCESS,
            created_at=NOW - timedelta(hours=2),
        )
        # Second refund for same transaction (duplicate)
        refund2 = _refund(
            db_session,
            merchant_id=merchant.id,
            transaction_id=txn.id,
            status=RefundStatus.PENDING,
            created_at=NOW - timedelta(hours=1),
        )

        anomalies = RefundAnomalyDetector(db_session, now=NOW).detect_anomalies(refund2)

        dup = [a for a in anomalies if a.anomaly_type == AnomalyType.REFUND_DUPLICATE]
        assert len(dup) == 1
        assert dup[0].severity == SeverityLevel.WARNING
        assert dup[0].root_cause_confidence == Decimal("0.95")


class TestDetectProcessingDelay:
    """Test 5: Refund in 'processing' past threshold."""

    def test_detect_processing_delay(self, db_session):
        merchant = _merchant(db_session)
        txn = _txn(db_session, merchant_id=merchant.id)
        # Created 4 days ago, still PROCESSING
        # T+3 from June 11 = June 16, NOW = June 15 → still within window
        refund = _refund(
            db_session,
            merchant_id=merchant.id,
            transaction_id=txn.id,
            status=RefundStatus.PROCESSING,
            created_at=NOW - timedelta(days=4),
        )

        anomalies = RefundAnomalyDetector(db_session, now=NOW).detect_anomalies(refund)

        # Still within T+3 window — no anomaly yet
        delay = [a for a in anomalies if a.anomaly_type == AnomalyType.REFUND_PROCESSING_DELAY]
        stuck = [a for a in anomalies if a.anomaly_type == AnomalyType.REFUND_STUCK]
        assert len(delay) == 0
        assert len(stuck) == 0


# ══════════════════════════════════════════════════════════════════════════════
# 2. Classification Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestClassifyBankDelay:
    """Test 6: Classification for stuck refund with bank delay."""

    def test_classify_bank_delay(self, db_session):
        merchant = _merchant(db_session)
        txn = _txn(db_session, merchant_id=merchant.id)
        refund = _refund(
            db_session,
            merchant_id=merchant.id,
            transaction_id=txn.id,
            status=RefundStatus.PENDING,
            bank_response_code="50003",
        )
        anomaly = _anomaly_for_refund(
            db_session, merchant_id=merchant.id, refund_id=refund.id,
            anomaly_type=AnomalyType.REFUND_STUCK,
        )

        classifier = RefundRootCauseClassifier(db_session, now=NOW)
        diagnosis = classifier.classify_root_cause(anomaly, refund)

        assert isinstance(diagnosis, Diagnosis)
        assert diagnosis.anomaly_id == anomaly.id
        assert diagnosis.root_cause_category == "refund_processing_timeout"
        assert Decimal("0.00") <= diagnosis.confidence <= Decimal("1.00")
        assert "facts" in diagnosis.evidence

    def test_classify_stuck_no_code(self, db_session):
        """Stuck refund with no response code → bank_processing_delay."""
        merchant = _merchant(db_session)
        txn = _txn(db_session, merchant_id=merchant.id)
        refund = _refund(
            db_session,
            merchant_id=merchant.id,
            transaction_id=txn.id,
            status=RefundStatus.PENDING,
            bank_response_code=None,
        )
        anomaly = _anomaly_for_refund(
            db_session, merchant_id=merchant.id, refund_id=refund.id,
            anomaly_type=AnomalyType.REFUND_STUCK,
        )

        diagnosis = RefundRootCauseClassifier(db_session, now=NOW).classify_root_cause(anomaly, refund)
        assert diagnosis.root_cause_category == "bank_processing_delay"
        assert diagnosis.confidence == Decimal("0.65")


class TestClassifyAccountClosed:
    """Test 7: Classification for reversed refund."""

    def test_classify_account_closed(self, db_session):
        merchant = _merchant(db_session)
        txn = _txn(db_session, merchant_id=merchant.id)
        refund = _refund(
            db_session,
            merchant_id=merchant.id,
            transaction_id=txn.id,
            status=RefundStatus.REVERSED,
            bank_response_code="50001",
        )
        anomaly = _anomaly_for_refund(
            db_session, merchant_id=merchant.id, refund_id=refund.id,
            anomaly_type=AnomalyType.REFUND_REVERSED,
        )

        diagnosis = RefundRootCauseClassifier(db_session, now=NOW).classify_root_cause(anomaly, refund)
        assert diagnosis.root_cause_category in ("refund_rejected_by_bank", "bank_error", "50001")
        assert diagnosis.confidence >= Decimal("0.65")


class TestClassifyDuplicate:
    """Classification for duplicate refund."""

    def test_classify_duplicate(self, db_session):
        merchant = _merchant(db_session)
        txn = _txn(db_session, merchant_id=merchant.id)
        refund = _refund(
            db_session,
            merchant_id=merchant.id,
            transaction_id=txn.id,
            status=RefundStatus.PENDING,
        )
        anomaly = _anomaly_for_refund(
            db_session, merchant_id=merchant.id, refund_id=refund.id,
            anomaly_type=AnomalyType.REFUND_DUPLICATE,
        )

        diagnosis = RefundRootCauseClassifier(db_session, now=NOW).classify_root_cause(anomaly, refund)
        assert diagnosis.root_cause_category == "duplicate_refund_initiated"
        assert diagnosis.confidence == Decimal("0.95")


class TestClassifyMismatch:
    """Classification for refund mismatch."""

    def test_classify_mismatch(self, db_session):
        merchant = _merchant(db_session)
        txn = _txn(db_session, merchant_id=merchant.id)
        refund = _refund(
            db_session,
            merchant_id=merchant.id,
            transaction_id=txn.id,
            status=RefundStatus.PENDING,
        )
        anomaly = _anomaly_for_refund(
            db_session, merchant_id=merchant.id, refund_id=refund.id,
            anomaly_type=AnomalyType.REFUND_MISMATCH,
        )

        diagnosis = RefundRootCauseClassifier(db_session, now=NOW).classify_root_cause(anomaly, refund)
        assert diagnosis.root_cause_category == "refund_not_received_by_customer"
        assert diagnosis.confidence == Decimal("0.80")


# ══════════════════════════════════════════════════════════════════════════════
# 3. Recommendation Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestRecommendWaitForCompletion:
    """Test 8: WAIT recommendation for bank processing delay."""

    def test_recommend_wait_for_completion(self, db_session):
        merchant = _merchant(db_session)
        txn = _txn(db_session, merchant_id=merchant.id)
        refund = _refund(
            db_session,
            merchant_id=merchant.id,
            transaction_id=txn.id,
            status=RefundStatus.PENDING,
            created_at=NOW - timedelta(days=2),
        )
        anomaly = _anomaly_for_refund(
            db_session, merchant_id=merchant.id, refund_id=refund.id,
            anomaly_type=AnomalyType.REFUND_STUCK,
        )
        diagnosis = _diagnosis(
            db_session, anomaly_id=anomaly.id,
            root_cause="bank_processing_delay", confidence=Decimal("0.80"),
        )

        recommender = RefundActionRecommender(db_session, now=NOW)
        rec = recommender.recommend_action(anomaly, diagnosis, refund)

        assert isinstance(rec, Recommendation)
        assert rec.anomaly_id == anomaly.id
        assert rec.recommended_action == RecommendedAction.WAIT
        assert rec.timeline == "72_hours"
        assert rec.expected_resolution_time_hours == 72
        assert rec.success_probability >= Decimal("0.70")
        assert rec.urgency == UrgencyLevel.LOW


class TestRecommendResubmit:
    """Test 9: RESUBMIT for customer account closed."""

    def test_recommend_resubmit(self, db_session):
        merchant = _merchant(db_session)
        txn = _txn(db_session, merchant_id=merchant.id)
        refund = _refund(
            db_session,
            merchant_id=merchant.id,
            transaction_id=txn.id,
            status=RefundStatus.FAILED,
        )
        anomaly = _anomaly_for_refund(
            db_session, merchant_id=merchant.id, refund_id=refund.id,
            anomaly_type=AnomalyType.REFUND_STUCK,
        )
        diagnosis = _diagnosis(
            db_session, anomaly_id=anomaly.id,
            root_cause="customer_account_closed", confidence=Decimal("0.85"),
        )

        rec = RefundActionRecommender(db_session, now=NOW).recommend_action(anomaly, diagnosis, refund)

        assert rec.recommended_action == RecommendedAction.PROCESS_REFUND
        assert rec.timeline == "immediate"
        assert rec.urgency == UrgencyLevel.HIGH
        assert "account" in rec.recommendation_text.lower()


class TestRecommendEscalate:
    """Test 10: ESCALATE for reversed refund."""

    def test_recommend_escalate(self, db_session):
        merchant = _merchant(db_session)
        txn = _txn(db_session, merchant_id=merchant.id)
        refund = _refund(
            db_session,
            merchant_id=merchant.id,
            transaction_id=txn.id,
            status=RefundStatus.REVERSED,
        )
        anomaly = _anomaly_for_refund(
            db_session, merchant_id=merchant.id, refund_id=refund.id,
            anomaly_type=AnomalyType.REFUND_REVERSED,
        )
        diagnosis = _diagnosis(
            db_session, anomaly_id=anomaly.id,
            root_cause="refund_reversed", confidence=Decimal("0.70"),
        )

        rec = RefundActionRecommender(db_session, now=NOW).recommend_action(anomaly, diagnosis, refund)

        assert rec.recommended_action == RecommendedAction.ESCALATE
        assert rec.timeline == "immediate"
        assert rec.urgency == UrgencyLevel.CRITICAL
        assert rec.success_probability <= Decimal("0.50")

    def test_recommend_mismatch_escalate(self, db_session):
        """Refund mismatch should also escalate urgently."""
        merchant = _merchant(db_session)
        txn = _txn(db_session, merchant_id=merchant.id)
        refund = _refund(
            db_session,
            merchant_id=merchant.id,
            transaction_id=txn.id,
            status=RefundStatus.PENDING,
        )
        anomaly = _anomaly_for_refund(
            db_session, merchant_id=merchant.id, refund_id=refund.id,
            anomaly_type=AnomalyType.REFUND_MISMATCH,
        )
        diagnosis = _diagnosis(
            db_session, anomaly_id=anomaly.id,
            root_cause="refund_not_received_by_customer", confidence=Decimal("0.80"),
        )

        rec = RefundActionRecommender(db_session, now=NOW).recommend_action(anomaly, diagnosis, refund)

        assert rec.recommended_action == RecommendedAction.PROCESS_REFUND
        assert rec.urgency == UrgencyLevel.CRITICAL


# ══════════════════════════════════════════════════════════════════════════════
# Extra edge-case tests
# ══════════════════════════════════════════════════════════════════════════════


class TestEdgeCases:
    """Additional edge-case coverage."""

    def test_all_action_tree_entries_produce_valid_recommendations(self, db_session):
        """Every root cause in REFUND_ACTION_TREE should produce a valid recommendation."""
        merchant = _merchant(db_session)
        txn = _txn(db_session, merchant_id=merchant.id)
        refund = _refund(db_session, merchant_id=merchant.id, transaction_id=txn.id)

        for root_cause in REFUND_ACTION_TREE:
            anomaly = _anomaly_for_refund(
                db_session, merchant_id=merchant.id, refund_id=refund.id,
            )
            diagnosis = _diagnosis(db_session, anomaly_id=anomaly.id, root_cause=root_cause)

            rec = RefundActionRecommender(db_session, now=NOW).recommend_action(anomaly, diagnosis, refund)
            assert isinstance(rec.recommended_action, RecommendedAction)
            assert Decimal("0.10") <= rec.success_probability <= Decimal("0.99")
            assert rec.timeline in REFUND_TIMELINE_HOURS

    def test_long_delay_escalates_bank_contact(self, db_session):
        """Refund >4 days old with bank_processing_delay should escalate."""
        merchant = _merchant(db_session)
        txn = _txn(db_session, merchant_id=merchant.id)
        refund = _refund(
            db_session,
            merchant_id=merchant.id,
            transaction_id=txn.id,
            status=RefundStatus.PENDING,
            created_at=NOW - timedelta(days=6),
        )
        anomaly = _anomaly_for_refund(
            db_session, merchant_id=merchant.id, refund_id=refund.id,
        )
        diagnosis = _diagnosis(
            db_session, anomaly_id=anomaly.id,
            root_cause="bank_processing_delay", confidence=Decimal("0.80"),
        )

        rec = RefundActionRecommender(db_session, now=NOW).recommend_action(anomaly, diagnosis, refund)
        # >4 days → should contact bank, not just wait
        assert rec.recommended_action == RecommendedAction.CONTACT_BANK
        assert rec.timeline == "immediate"

    def test_anomalies_not_persisted(self, db_session):
        """All returned anomalies should be transient."""
        merchant = _merchant(db_session)
        txn = _txn(db_session, merchant_id=merchant.id)
        refund = _refund(
            db_session,
            merchant_id=merchant.id,
            transaction_id=txn.id,
            status=RefundStatus.PENDING,
            created_at=NOW - timedelta(days=7),
        )

        anomalies = RefundAnomalyDetector(db_session, now=NOW).detect_anomalies(refund)
        assert len(anomalies) > 0

        for a in anomalies:
            assert db_session.get(type(a), a.id) is None
