"""Tests for src/agents/settlement_agent.py — Settlement Anomaly Detector.

Uses in-memory SQLite via the shared ``db_session`` fixture from test_setup.
All settlement objects are constructed inline for full control over every field.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest

from src.agents.settlement_agent import (
    SEVERITY_CRITICAL_HOURS,
    SEVERITY_WARNING_HOURS,
    SettlementAnomalyDetector,
)
from src.data.models import (
    AnomalyStatus,
    AnomalyType,
    Merchant,
    Settlement,
    SettlementAttempt,
    SettlementAttemptStatus,
    SettlementStatus,
    SeverityLevel,
    Transaction,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

NOW = datetime(2025, 6, 15, 12, 0, 0)  # Monday noon — stable reference


def _merchant(session) -> Merchant:
    m = Merchant(
        id=uuid.uuid4(),
        business_name="Test Merchant",
        industry_category="E-Commerce",
    )
    session.add(m)
    session.flush()
    return m


def _settlement(
    session,
    *,
    merchant_id: uuid.UUID,
    amount: Decimal = Decimal("100000.00"),
    status: SettlementStatus = SettlementStatus.PENDING,
    fees: Decimal = Decimal("2000.00"),
    taxes: Decimal = Decimal("360.00"),
    net_amount: Decimal | None = None,
    created_at: datetime | None = None,
    period_start: date | None = None,
    period_end: date | None = None,
    settlement_id: str | None = None,
) -> Settlement:
    if net_amount is None:
        net_amount = amount - fees - taxes
    s = Settlement(
        id=settlement_id or f"settle_{uuid.uuid4().hex[:8]}",
        merchant_id=merchant_id,
        amount=amount,
        currency="INR",
        status=status,
        created_at=created_at or (NOW - timedelta(days=5)),
        fees=fees,
        taxes=taxes,
        net_amount=net_amount,
        settlement_period_start=period_start or (NOW - timedelta(days=7)).date(),
        settlement_period_end=period_end or (NOW - timedelta(days=1)).date(),
        related_refunds=[],
        related_disputes=[],
    )
    session.add(s)
    session.flush()
    return s


def _attempt(
    session,
    *,
    settlement_id: str,
    number: int = 1,
    status: SettlementAttemptStatus = SettlementAttemptStatus.SUCCESS,
    response_code: str | None = "200",
    response_message: str | None = "OK",
) -> SettlementAttempt:
    a = SettlementAttempt(
        settlement_id=settlement_id,
        attempt_number=number,
        method="NEFT",
        initiated_at=NOW - timedelta(hours=number),
        response_code=response_code,
        response_message=response_message,
        status=status,
        bank_reference_id=f"BANK{number:04d}" if status == SettlementAttemptStatus.SUCCESS else None,
    )
    session.add(a)
    session.flush()
    return a


def _txn(session, *, merchant_id: uuid.UUID, amount: Decimal, created: datetime) -> Transaction:
    t = Transaction(
        id=f"pay_{uuid.uuid4().hex[:8]}",
        merchant_id=merchant_id,
        amount=amount,
        currency="INR",
        status="captured",
        created_at=created,
    )
    session.add(t)
    session.flush()
    return t


# ══════════════════════════════════════════════════════════════════════════════
# Test Cases
# ══════════════════════════════════════════════════════════════════════════════


class TestDelayedSettlement:
    """Test 1: Settlement past T+2 deadline."""

    def test_detect_delayed_settlement_past_deadline(self, db_session):
        """A settlement created 5 working days ago, still PENDING, should be
        flagged as delayed with CRITICAL severity (>24h)."""
        merchant = _merchant(db_session)
        created = NOW - timedelta(days=7)  # well past T+2
        settlement = _settlement(
            db_session,
            merchant_id=merchant.id,
            status=SettlementStatus.PENDING,
            created_at=created,
        )

        detector = SettlementAnomalyDetector(db_session, now=NOW)
        anomalies = detector.detect_anomalies(settlement)

        assert len(anomalies) >= 1
        delay = [a for a in anomalies if a.anomaly_type == AnomalyType.SETTLEMENT_DELAYED]
        assert len(delay) == 1
        assert delay[0].severity == SeverityLevel.CRITICAL
        assert delay[0].related_settlement_id == settlement.id
        assert delay[0].status == AnomalyStatus.OPEN

    def test_detect_delayed_settlement_still_pending(self, db_session):
        """A settlement created 3 working days ago, still PENDING, should
        be flagged with INFO severity (just past deadline, <12h late)."""
        # Create on a Wednesday, check Thursday — barely past T+2
        merchant = _merchant(db_session)
        # Mon 9 Jun 2025, 10 AM → expected Wed 11 Jun 23:59
        created = datetime(2025, 6, 9, 10, 0)
        settlement = _settlement(
            db_session,
            merchant_id=merchant.id,
            status=SettlementStatus.PENDING,
            created_at=created,
        )

        # Check Wed 12 Jun 2025, 08:00 — about 8h past deadline
        detector = SettlementAnomalyDetector(db_session, now=datetime(2025, 6, 12, 8, 0))
        anomalies = detector.detect_anomalies(settlement)

        delay = [a for a in anomalies if a.anomaly_type == AnomalyType.SETTLEMENT_DELAYED]
        assert len(delay) == 1
        assert delay[0].severity == SeverityLevel.INFO  # <12h late


class TestPartialSettlement:
    """Test 2: Settlement amount significantly less than expected."""

    def test_detect_partial_settlement(self, db_session):
        """A PENDING settlement with net_amount 20% less than expected should
        be flagged as partial."""
        merchant = _merchant(db_session)
        period_start = date(2025, 6, 8)
        period_end = date(2025, 6, 14)

        settlement = _settlement(
            db_session,
            merchant_id=merchant.id,
            amount=Decimal("100000.00"),
            status=SettlementStatus.PENDING,
            fees=Decimal("2000.00"),
            taxes=Decimal("360.00"),
            net_amount=Decimal("60000.00"),  # should be ~97640
            created_at=NOW - timedelta(days=3),
            period_start=period_start,
            period_end=period_end,
        )

        # Create transactions summing to 100000
        for i in range(5):
            _txn(
                db_session,
                merchant_id=merchant.id,
                amount=Decimal("20000.00"),
                created=datetime(2025, 6, 10, 10 + i, 0),
            )

        detector = SettlementAnomalyDetector(db_session, now=NOW)
        anomalies = detector.detect_anomalies(settlement)

        partial = [a for a in anomalies if a.anomaly_type == AnomalyType.SETTLEMENT_PARTIAL]
        assert len(partial) >= 1
        assert partial[0].severity == SeverityLevel.WARNING


class TestFailedSettlement:
    """Test 3: Settlement with status 'failed'."""

    def test_detect_failed_settlement(self, db_session):
        """A FAILED settlement should produce a critical anomaly with the
        bank error code mapped as root cause."""
        merchant = _merchant(db_session)
        settlement = _settlement(
            db_session,
            merchant_id=merchant.id,
            status=SettlementStatus.FAILED,
        )
        _attempt(
            db_session,
            settlement_id=settlement.id,
            number=1,
            status=SettlementAttemptStatus.FAILED,
            response_code="40092",
            response_message="Account Closed",
        )

        detector = SettlementAnomalyDetector(db_session, now=NOW)
        anomalies = detector.detect_anomalies(settlement)

        failed = [a for a in anomalies if a.anomaly_type == AnomalyType.SETTLEMENT_FAILED]
        assert len(failed) >= 1
        assert failed[0].severity == SeverityLevel.CRITICAL
        assert failed[0].root_cause == "account_closed"

    def test_detect_failed_settlement_no_code(self, db_session):
        """A FAILED settlement with no attempt/response code should still
        produce an anomaly with 'unknown_failure' root cause."""
        merchant = _merchant(db_session)
        settlement = _settlement(
            db_session,
            merchant_id=merchant.id,
            status=SettlementStatus.FAILED,
        )

        detector = SettlementAnomalyDetector(db_session, now=NOW)
        anomalies = detector.detect_anomalies(settlement)

        failed = [a for a in anomalies if a.anomaly_type == AnomalyType.SETTLEMENT_FAILED]
        assert len(failed) >= 1
        assert failed[0].root_cause == "unknown_failure"


class TestFeeMismatch:
    """Test 4: Fees deviating significantly from expected."""

    def test_detect_fee_mismatch(self, db_session):
        """Fees that are 3x the expected 2% rate should trigger a warning."""
        merchant = _merchant(db_session)
        # amount=100000, expected fee=2000, actual fee=6000 → 200% deviation
        settlement = _settlement(
            db_session,
            merchant_id=merchant.id,
            amount=Decimal("100000.00"),
            fees=Decimal("6000.00"),
            taxes=Decimal("1080.00"),
            net_amount=Decimal("92920.00"),
        )

        detector = SettlementAnomalyDetector(db_session, now=NOW)
        anomalies = detector.detect_anomalies(settlement)

        fee_anomalies = [
            a for a in anomalies
            if a.root_cause and "fee_mismatch" in a.root_cause
        ]
        assert len(fee_anomalies) == 1
        assert fee_anomalies[0].severity == SeverityLevel.WARNING
        assert "overcharged" in fee_anomalies[0].root_cause

    def test_no_fee_mismatch_when_within_threshold(self, db_session):
        """Fees within 10% of expected should NOT trigger an anomaly."""
        merchant = _merchant(db_session)
        # amount=100000, expected=2000, actual=2100 → 5% deviation (below 10% threshold)
        settlement = _settlement(
            db_session,
            merchant_id=merchant.id,
            amount=Decimal("100000.00"),
            fees=Decimal("2100.00"),
            taxes=Decimal("378.00"),
            net_amount=Decimal("97522.00"),
        )

        detector = SettlementAnomalyDetector(db_session, now=NOW)
        anomalies = detector.detect_anomalies(settlement)

        fee_anomalies = [
            a for a in anomalies
            if a.root_cause and "fee_mismatch" in a.root_cause
        ]
        assert len(fee_anomalies) == 0


class TestMultipleFailedAttempts:
    """Test 5: Settlement with ≥2 failed bank transfer attempts."""

    def test_detect_multiple_failed_attempts(self, db_session):
        """3 failed attempts should produce a CRITICAL anomaly."""
        merchant = _merchant(db_session)
        settlement = _settlement(
            db_session,
            merchant_id=merchant.id,
            status=SettlementStatus.FAILED,
        )
        _attempt(db_session, settlement_id=settlement.id, number=1,
                 status=SettlementAttemptStatus.FAILED, response_code="40091")
        _attempt(db_session, settlement_id=settlement.id, number=2,
                 status=SettlementAttemptStatus.FAILED, response_code="40094")
        _attempt(db_session, settlement_id=settlement.id, number=3,
                 status=SettlementAttemptStatus.FAILED, response_code="40098")

        detector = SettlementAnomalyDetector(db_session, now=NOW)
        anomalies = detector.detect_anomalies(settlement)

        multi = [
            a for a in anomalies
            if "multiple_bank_failures" in (a.root_cause or "")
        ]
        assert len(multi) == 1
        assert multi[0].severity == SeverityLevel.CRITICAL
        assert "3 times" in multi[0].recommended_action or "3 attempts" in multi[0].recommended_action

    def test_single_failure_not_flagged(self, db_session):
        """A single failed attempt should NOT produce a multiple_failures anomaly."""
        merchant = _merchant(db_session)
        settlement = _settlement(
            db_session,
            merchant_id=merchant.id,
            status=SettlementStatus.FAILED,
        )
        _attempt(db_session, settlement_id=settlement.id, number=1,
                 status=SettlementAttemptStatus.FAILED, response_code="40091")

        detector = SettlementAnomalyDetector(db_session, now=NOW)
        anomalies = detector.detect_anomalies(settlement)

        multi = [
            a for a in anomalies
            if "multiple_bank_failures" in (a.root_cause or "")
        ]
        assert len(multi) == 0


class TestReconciliationGap:
    """Test 6: Transaction sum doesn't match settlement amount."""

    def test_detect_reconciliation_gap(self, db_session):
        """If transaction total is 200000 but settlement amount is 150000,
        the gap exceeds 1% tolerance."""
        merchant = _merchant(db_session)
        period_start = date(2025, 6, 8)
        period_end = date(2025, 6, 14)

        settlement = _settlement(
            db_session,
            merchant_id=merchant.id,
            amount=Decimal("150000.00"),
            status=SettlementStatus.PENDING,
            fees=Decimal("3000.00"),
            taxes=Decimal("540.00"),
            net_amount=Decimal("146460.00"),
            period_start=period_start,
            period_end=period_end,
        )

        # Transactions sum to 200000
        for _ in range(4):
            _txn(
                db_session,
                merchant_id=merchant.id,
                amount=Decimal("50000.00"),
                created=datetime(2025, 6, 10, 12, 0),
            )

        detector = SettlementAnomalyDetector(db_session, now=NOW)
        anomalies = detector.detect_anomalies(settlement)

        recon = [
            a for a in anomalies
            if a.root_cause and "reconciliation_gap" in a.root_cause
        ]
        assert len(recon) == 1
        assert recon[0].severity == SeverityLevel.WARNING


class TestSuccessfulSettlement:
    """Test 7: No anomalies for a clean, successful settlement."""

    def test_no_anomalies_for_successful_settlement(self, db_session):
        """A successful settlement with normal fees should produce zero anomalies."""
        merchant = _merchant(db_session)
        settlement = _settlement(
            db_session,
            merchant_id=merchant.id,
            status=SettlementStatus.SUCCESS,
            fees=Decimal("2000.00"),
            taxes=Decimal("360.00"),
            net_amount=Decimal("97640.00"),
            created_at=NOW - timedelta(days=3),
        )
        _attempt(db_session, settlement_id=settlement.id, number=1,
                 status=SettlementAttemptStatus.SUCCESS)

        detector = SettlementAnomalyDetector(db_session, now=NOW)
        anomalies = detector.detect_anomalies(settlement)
        assert anomalies == []


class TestSeverityCalculation:
    """Test 8: Severity mapping based on lateness hours."""

    def test_severity_just_past_deadline(self, db_session):
        """<12h late → INFO."""
        merchant = _merchant(db_session)
        created = datetime(2025, 6, 9, 10, 0)
        settlement = _settlement(
            db_session,
            merchant_id=merchant.id,
            status=SettlementStatus.PENDING,
            created_at=created,
        )
        # Expected: Wed 11 Jun 23:59. Check Thu 12 Jun 08:00 = ~8h late
        detector = SettlementAnomalyDetector(db_session, now=datetime(2025, 6, 12, 8, 0))
        anomalies = detector.detect_anomalies(settlement)

        delay = [a for a in anomalies if a.anomaly_type == AnomalyType.SETTLEMENT_DELAYED]
        assert len(delay) == 1
        assert delay[0].severity == SeverityLevel.INFO

    def test_severity_mid_late(self, db_session):
        """12-24h late → WARNING."""
        merchant = _merchant(db_session)
        created = datetime(2025, 6, 9, 10, 0)
        settlement = _settlement(
            db_session,
            merchant_id=merchant.id,
            status=SettlementStatus.PENDING,
            created_at=created,
        )
        # Expected: Wed 11 Jun 23:59. Check Thu 12 Jun 14:00 = ~14h late
        detector = SettlementAnomalyDetector(db_session, now=datetime(2025, 6, 12, 14, 0))
        anomalies = detector.detect_anomalies(settlement)

        delay = [a for a in anomalies if a.anomaly_type == AnomalyType.SETTLEMENT_DELAYED]
        assert len(delay) == 1
        assert delay[0].severity == SeverityLevel.WARNING

    def test_severity_very_late(self, db_session):
        """>24h late → CRITICAL."""
        merchant = _merchant(db_session)
        created = datetime(2025, 6, 9, 10, 0)
        settlement = _settlement(
            db_session,
            merchant_id=merchant.id,
            status=SettlementStatus.PENDING,
            created_at=created,
        )
        # Expected: Wed 11 Jun 23:59. Check Fri 13 Jun 12:00 = ~36h late
        detector = SettlementAnomalyDetector(db_session, now=datetime(2025, 6, 13, 12, 0))
        anomalies = detector.detect_anomalies(settlement)

        delay = [a for a in anomalies if a.anomaly_type == AnomalyType.SETTLEMENT_DELAYED]
        assert len(delay) == 1
        assert delay[0].severity == SeverityLevel.CRITICAL


class TestMultipleIssues:
    """Test 9: A single settlement with several concurrent problems."""

    def test_anomaly_with_multiple_issues(self, db_session):
        """A FAILED settlement that is also late, has multiple attempts,
        AND has a fee mismatch should produce multiple anomalies."""
        merchant = _merchant(db_session)
        created = NOW - timedelta(days=7)
        settlement = _settlement(
            db_session,
            merchant_id=merchant.id,
            status=SettlementStatus.FAILED,
            amount=Decimal("100000.00"),
            fees=Decimal("6000.00"),  # 3x expected fee
            taxes=Decimal("1080.00"),
            net_amount=Decimal("92920.00"),
            created_at=created,
        )
        _attempt(db_session, settlement_id=settlement.id, number=1,
                 status=SettlementAttemptStatus.FAILED, response_code="40091")
        _attempt(db_session, settlement_id=settlement.id, number=2,
                 status=SettlementAttemptStatus.FAILED, response_code="40094")

        detector = SettlementAnomalyDetector(db_session, now=NOW)
        anomalies = detector.detect_anomalies(settlement)

        types_found = {a.anomaly_type for a in anomalies}
        # Should detect: DELAYED + FAILED + fee_mismatch + multiple_failures
        assert AnomalyType.SETTLEMENT_DELAYED in types_found
        assert AnomalyType.SETTLEMENT_FAILED in types_found
        # fee_mismatch uses SETTLEMENT_PARTIAL as the type
        assert any("fee_mismatch" in (a.root_cause or "") for a in anomalies)
        assert any("multiple_bank_failures" in (a.root_cause or "") for a in anomalies)
        assert len(anomalies) >= 4


class TestEdgeCases:
    """Test 10: Edge cases and boundary conditions."""

    def test_zero_amount_settlement(self, db_session):
        """A settlement with amount=0 should not crash on fee/recon checks."""
        merchant = _merchant(db_session)
        settlement = _settlement(
            db_session,
            merchant_id=merchant.id,
            status=SettlementStatus.PENDING,
            amount=Decimal("0.00"),
            fees=Decimal("0.00"),
            taxes=Decimal("0.00"),
            net_amount=Decimal("0.00"),
        )

        detector = SettlementAnomalyDetector(db_session, now=NOW)
        anomalies = detector.detect_anomalies(settlement)
        # May still detect delay, but should not crash
        assert isinstance(anomalies, list)

    def test_settlement_without_period_dates(self, db_session):
        """Reconciliation gap should gracefully skip when period dates are None."""
        merchant = _merchant(db_session)
        settlement = _settlement(
            db_session,
            merchant_id=merchant.id,
            status=SettlementStatus.PENDING,
            period_start=None,
            period_end=None,
        )

        detector = SettlementAnomalyDetector(db_session, now=NOW)
        anomalies = detector.detect_anomalies(settlement)
        # Should not crash — reconciliation check returns None
        assert isinstance(anomalies, list)

    def test_no_attempts_on_failed_settlement(self, db_session):
        """FAILED settlement with no attempts should still produce anomaly."""
        merchant = _merchant(db_session)
        settlement = _settlement(
            db_session,
            merchant_id=merchant.id,
            status=SettlementStatus.FAILED,
        )

        detector = SettlementAnomalyDetector(db_session, now=NOW)
        anomalies = detector.detect_anomalies(settlement)

        failed = [a for a in anomalies if a.anomaly_type == AnomalyType.SETTLEMENT_FAILED]
        assert len(failed) == 1
        assert failed[0].root_cause == "unknown_failure"

    def test_anomaly_objects_not_persisted(self, db_session):
        """Detector should return Anomaly objects without adding them to the session."""
        merchant = _merchant(db_session)
        settlement = _settlement(
            db_session,
            merchant_id=merchant.id,
            status=SettlementStatus.FAILED,
            created_at=NOW - timedelta(days=7),
        )

        detector = SettlementAnomalyDetector(db_session, now=NOW)
        anomalies = detector.detect_anomalies(settlement)
        assert len(anomalies) > 0

        # Anomalies should be transient (not in session identity map)
        for a in anomalies:
            assert db_session.get(type(a), a.id) is None
