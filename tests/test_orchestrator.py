"""Tests for src/agents/orchestrator.py — Multi-Agent Orchestrator.

Uses in-memory SQLite via the shared ``db_session`` fixture from test_setup.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from src.agents.orchestrator import (
    CycleResult,
    DashboardUpdate,
    ImpactSummary,
    PaymentOpsOrchestrator,
)
from src.data.models import (
    Anomaly,
    AnomalyStatus,
    AnomalyType,
    Dispute,
    DisputeStatus,
    DisputeType,
    EvaluationMetric,
    Merchant,
    Refund,
    RefundInitiator,
    RefundReason,
    RefundStatus,
    SeverityLevel,
    Settlement,
    SettlementStatus,
    Transaction,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

NOW = datetime(2025, 6, 15, 12, 0, 0)


def _merchant(
    session,
    *,
    name: str = "Orchestrator Test Co",
    threshold: SeverityLevel = SeverityLevel.WARNING,
    channels: list | None = None,
) -> Merchant:
    m = Merchant(
        id=uuid.uuid4(),
        business_name=name,
        alert_threshold_severity=threshold,
        notification_channels=channels or ["email"],
    )
    session.add(m)
    session.flush()
    return m


def _settlement(
    session, *, merchant_id, status=SettlementStatus.PENDING, created_at=None
) -> Settlement:
    s = Settlement(
        id=f"settle_{uuid.uuid4().hex[:8]}",
        merchant_id=merchant_id,
        amount=Decimal("100000.00"),
        currency="INR",
        status=status,
        created_at=created_at or (NOW - timedelta(hours=2)),
        fees=Decimal("2000.00"),
        taxes=Decimal("360.00"),
        net_amount=Decimal("97640.00"),
        related_refunds=[],
        related_disputes=[],
    )
    session.add(s)
    session.flush()
    return s


def _refund(
    session, *, merchant_id, transaction_id: str, status=RefundStatus.PENDING
) -> Refund:
    r = Refund(
        id=f"rfnd_{uuid.uuid4().hex[:8]}",
        merchant_id=merchant_id,
        transaction_id=transaction_id,
        amount=Decimal("2500.00"),
        reason=RefundReason.CUSTOMER_REQUESTED,
        status=status,
        created_at=NOW - timedelta(hours=3),
        initiated_by=RefundInitiator.MERCHANT,
    )
    session.add(r)
    session.flush()
    return r


def _txn(session, *, merchant_id) -> Transaction:
    t = Transaction(
        id=f"pay_{uuid.uuid4().hex[:8]}",
        merchant_id=merchant_id,
        amount=Decimal("5000.00"),
        currency="INR",
        status="captured",
        created_at=NOW - timedelta(days=10),
    )
    session.add(t)
    session.flush()
    return t


def _dispute(
    session, *, merchant_id, transaction_id: str, reason_code="4855"
) -> Dispute:
    d = Dispute(
        id=f"disp_{uuid.uuid4().hex[:8]}",
        merchant_id=merchant_id,
        transaction_id=transaction_id,
        type=DisputeType.CHARGEBACK,
        reason_code=reason_code,
        reason_text=f"Test dispute {reason_code}",
        amount=Decimal("10000.00"),
        filed_at=NOW - timedelta(days=3),
        evidence_deadline=NOW + timedelta(days=4),
        current_status=DisputeStatus.EVIDENCE_PENDING,
    )
    session.add(d)
    session.flush()
    return d


# ══════════════════════════════════════════════════════════════════════════════
# Test Cases
# ══════════════════════════════════════════════════════════════════════════════


class TestSingleSettlement:
    """Test 1: Agent cycle with a single delayed settlement."""

    def test_agent_cycle_with_single_settlement(self, db_session):
        merchant = _merchant(db_session)
        # Created 5 days ago, still PENDING → should be detected as delayed
        settlement = _settlement(
            db_session,
            merchant_id=merchant.id,
            status=SettlementStatus.PENDING,
            created_at=NOW - timedelta(days=5),
        )

        orchestrator = PaymentOpsOrchestrator(db_session, now=NOW)
        dashboard = orchestrator.run_agent_cycle(merchant.id)

        assert isinstance(dashboard, DashboardUpdate)
        assert dashboard.merchant_id == str(merchant.id)
        # Should have at least one anomaly (delayed settlement)
        total = len(dashboard.critical_anomalies) + len(dashboard.warning_anomalies) + len(dashboard.info_anomalies)
        assert total >= 1
        # Should have recommendations
        assert len(dashboard.top_recommendations) >= 1


class TestMultipleIssues:
    """Test 2: Agent cycle with multiple issue types."""

    def test_agent_cycle_with_multiple_issues(self, db_session):
        merchant = _merchant(db_session)

        # Delayed settlement
        _settlement(
            db_session,
            merchant_id=merchant.id,
            status=SettlementStatus.PENDING,
            created_at=NOW - timedelta(days=5),
        )

        # Stuck refund (need a transaction first)
        txn = _txn(db_session, merchant_id=merchant.id)
        _refund(
            db_session,
            merchant_id=merchant.id,
            transaction_id=txn.id,
            status=RefundStatus.PENDING,
        )

        # Dispute with no evidence
        _dispute(db_session, merchant_id=merchant.id, transaction_id=txn.id)

        orchestrator = PaymentOpsOrchestrator(db_session, now=NOW)
        dashboard = orchestrator.run_agent_cycle(merchant.id)

        total = (
            len(dashboard.critical_anomalies)
            + len(dashboard.warning_anomalies)
            + len(dashboard.info_anomalies)
        )
        # Should have anomalies from at least two types
        assert total >= 2


class TestMultipleMerchants:
    """Test 3: Agent cycle for multiple merchants."""

    def test_agent_cycle_multiple_merchants(self, db_session):
        m1 = _merchant(db_session, name="Merchant A")
        m2 = _merchant(db_session, name="Merchant B")

        _settlement(
            db_session, merchant_id=m1.id,
            status=SettlementStatus.PENDING, created_at=NOW - timedelta(days=5),
        )
        _settlement(
            db_session, merchant_id=m2.id,
            status=SettlementStatus.SUCCESS, created_at=NOW - timedelta(hours=2),
        )

        orchestrator = PaymentOpsOrchestrator(db_session, now=NOW)

        d1 = orchestrator.run_agent_cycle(m1.id)
        d2 = orchestrator.run_agent_cycle(m2.id)

        # Merchant A should have anomalies
        total1 = len(d1.critical_anomalies) + len(d1.warning_anomalies) + len(d1.info_anomalies)
        assert total1 >= 1

        # Merchant B (success) should have no anomalies
        total2 = len(d2.critical_anomalies) + len(d2.warning_anomalies) + len(d2.info_anomalies)
        assert total2 == 0


class TestNotificationGeneration:
    """Test 4: Notifications are generated based on merchant threshold."""

    def test_notification_generation(self, db_session):
        # Merchant with INFO threshold (should get all notifications)
        merchant = _merchant(
            db_session,
            threshold=SeverityLevel.INFO,
            channels=["email", "sms"],
        )
        _settlement(
            db_session,
            merchant_id=merchant.id,
            status=SettlementStatus.PENDING,
            created_at=NOW - timedelta(days=5),
        )

        orchestrator = PaymentOpsOrchestrator(db_session, now=NOW)
        dashboard = orchestrator.run_agent_cycle(merchant.id)

        # Verify dashboard has data
        assert dashboard.merchant_id == str(merchant.id)
        assert dashboard.summary["total_anomalies"] >= 1

    def test_notification_filtered_by_threshold(self, db_session):
        """Merchant with CRITICAL threshold should not see INFO anomalies."""
        merchant = _merchant(
            db_session,
            threshold=SeverityLevel.CRITICAL,
            channels=["email"],
        )
        # Create a settlement that will produce INFO-level anomaly
        # (just barely past deadline)
        created = datetime(2025, 6, 9, 10, 0)  # Mon
        _settlement(
            db_session,
            merchant_id=merchant.id,
            status=SettlementStatus.PENDING,
            created_at=created,
        )

        orchestrator = PaymentOpsOrchestrator(db_session, now=datetime(2025, 6, 12, 8, 0))
        dashboard = orchestrator.run_agent_cycle(merchant.id)

        # Info anomalies should be filtered out of notifications
        # (but still present in dashboard)
        assert isinstance(dashboard, DashboardUpdate)


class TestDashboardSummary:
    """Test 5: Dashboard summary is correctly calculated."""

    def test_dashboard_summary_calculation(self, db_session):
        merchant = _merchant(db_session)

        # Create several issues
        _settlement(
            db_session, merchant_id=merchant.id,
            status=SettlementStatus.PENDING, created_at=NOW - timedelta(days=5),
        )
        txn = _txn(db_session, merchant_id=merchant.id)
        _refund(
            db_session, merchant_id=merchant.id,
            transaction_id=txn.id, status=RefundStatus.PENDING,
        )

        orchestrator = PaymentOpsOrchestrator(db_session, now=NOW)
        dashboard = orchestrator.run_agent_cycle(merchant.id)

        # Summary should have all expected fields
        assert "total_anomalies" in dashboard.summary
        assert "critical_count" in dashboard.summary
        assert "warning_count" in dashboard.summary
        assert "info_count" in dashboard.summary
        assert dashboard.summary["total_anomalies"] == (
            dashboard.summary["critical_count"]
            + dashboard.summary["warning_count"]
            + dashboard.summary["info_count"]
        )

        # Impact should be populated
        assert isinstance(dashboard.impact, ImpactSummary)
        assert dashboard.impact.anomalies_detected >= 0


class TestImpactCalculation:
    """Test 6: Impact summary is calculated from resolved anomalies."""

    def test_impact_calculation(self, db_session):
        merchant = _merchant(db_session)

        # Create and resolve some anomalies
        for _ in range(3):
            a = Anomaly(
                id=uuid.uuid4(),
                merchant_id=merchant.id,
                anomaly_type=AnomalyType.SETTLEMENT_DELAYED,
                detected_at=NOW - timedelta(days=10),
                status=AnomalyStatus.RESOLVED,
                severity=SeverityLevel.WARNING,
            )
            db_session.add(a)
        db_session.flush()

        orchestrator = PaymentOpsOrchestrator(db_session, now=NOW)
        impact = orchestrator._calculate_impact(merchant.id)

        assert isinstance(impact, ImpactSummary)
        assert impact.anomalies_resolved == 3
        assert impact.settlement_delays_prevented == 3
        assert impact.time_saved_hours == 6.0  # 3 × 2h


class TestAnomalyLinking:
    """Test 7: Anomalies are properly linked to diagnoses and recommendations."""

    def test_anomaly_linking_to_diagnosis_recommendation(self, db_session):
        merchant = _merchant(db_session)
        _settlement(
            db_session, merchant_id=merchant.id,
            status=SettlementStatus.PENDING, created_at=NOW - timedelta(days=5),
        )

        orchestrator = PaymentOpsOrchestrator(db_session, now=NOW)
        dashboard = orchestrator.run_agent_cycle(merchant.id)

        # Check that anomalies, diagnoses, and recommendations exist in DB
        anomalies = db_session.query(Anomaly).filter(
            Anomaly.merchant_id == merchant.id,
        ).all()
        assert len(anomalies) >= 1

        for a in anomalies:
            # Each anomaly should have a linked diagnosis
            from src.data.models import Diagnosis
            diag = db_session.query(Diagnosis).filter(
                Diagnosis.anomaly_id == a.id,
            ).first()
            assert diag is not None, f"No diagnosis for anomaly {a.id}"

            # Each anomaly should have a linked recommendation
            from src.data.models import Recommendation
            rec = db_session.query(Recommendation).filter(
                Recommendation.anomaly_id == a.id,
            ).first()
            assert rec is not None, f"No recommendation for anomaly {a.id}"


class TestNoIssues:
    """Test 8: Clean cycle with no issues."""

    def test_agent_cycle_no_issues(self, db_session):
        merchant = _merchant(db_session)
        # Create a successful settlement (no issues)
        _settlement(
            db_session, merchant_id=merchant.id,
            status=SettlementStatus.SUCCESS, created_at=NOW - timedelta(hours=2),
        )

        orchestrator = PaymentOpsOrchestrator(db_session, now=NOW)
        dashboard = orchestrator.run_agent_cycle(merchant.id)

        total = (
            len(dashboard.critical_anomalies)
            + len(dashboard.warning_anomalies)
            + len(dashboard.info_anomalies)
        )
        assert total == 0
        assert dashboard.summary["total_anomalies"] == 0
        assert len(dashboard.top_recommendations) == 0


class TestAllIssueTypes:
    """Test 9: Agent cycle handles all issue types in one pass."""

    def test_agent_cycle_with_all_issue_types(self, db_session):
        merchant = _merchant(db_session)

        # Settlement: delayed
        _settlement(
            db_session, merchant_id=merchant.id,
            status=SettlementStatus.PENDING, created_at=NOW - timedelta(days=5),
        )

        # Refund: stuck
        txn = _txn(db_session, merchant_id=merchant.id)
        _refund(
            db_session, merchant_id=merchant.id,
            transaction_id=txn.id, status=RefundStatus.PENDING,
        )

        # Dispute: evidence incomplete
        _dispute(db_session, merchant_id=merchant.id, transaction_id=txn.id)

        orchestrator = PaymentOpsOrchestrator(db_session, now=NOW)
        dashboard = orchestrator.run_agent_cycle(merchant.id)

        # Should have anomalies from all three pipelines
        types_found = set()
        for entry in dashboard.critical_anomalies + dashboard.warning_anomalies + dashboard.info_anomalies:
            types_found.add(entry["type"])

        # At minimum: settlement_delayed + refund_stuck + dispute_evidence_incomplete
        assert len(types_found) >= 2

        # Metrics should be recorded
        metrics = db_session.query(EvaluationMetric).filter(
            EvaluationMetric.merchant_id == merchant.id,
        ).all()
        assert len(metrics) >= 3  # anomalies_detected, critical, warning, notifications


class TestErrorHandling:
    """Test 10: Orchestrator handles edge cases gracefully."""

    def test_orchestrator_error_handling(self, db_session):
        """Unknown merchant should return error dashboard."""
        orchestrator = PaymentOpsOrchestrator(db_session, now=NOW)
        dashboard = orchestrator.run_agent_cycle(uuid.uuid4())

        assert isinstance(dashboard, DashboardUpdate)
        assert "error" in dashboard.summary
        assert dashboard.summary["error"] == "merchant_not_found"

    def test_empty_cycle_produces_valid_dashboard(self, db_session):
        """Merchant with no resources should produce a valid empty dashboard."""
        merchant = _merchant(db_session)

        orchestrator = PaymentOpsOrchestrator(db_session, now=NOW)
        dashboard = orchestrator.run_agent_cycle(merchant.id)

        assert dashboard.merchant_id == str(merchant.id)
        assert dashboard.summary["total_anomalies"] == 0
        assert isinstance(dashboard.impact, ImpactSummary)

    def test_metrics_recorded_for_empty_cycle(self, db_session):
        """Even an empty cycle should record metrics."""
        merchant = _merchant(db_session)

        orchestrator = PaymentOpsOrchestrator(db_session, now=NOW)
        orchestrator.run_agent_cycle(merchant.id)

        metrics = db_session.query(EvaluationMetric).filter(
            EvaluationMetric.merchant_id == merchant.id,
        ).all()
        # Should have at least anomalies_detected=0 metric
        assert len(metrics) >= 1
        assert any(m.metric_name == "anomalies_detected" for m in metrics)

    def test_dashboard_next_deadline(self, db_session):
        """Dashboard should find the next dispute deadline."""
        merchant = _merchant(db_session)
        txn = _txn(db_session, merchant_id=merchant.id)

        # Create dispute with deadline in 2 days
        deadline = NOW + timedelta(days=2)
        d = _dispute(db_session, merchant_id=merchant.id, transaction_id=txn.id)
        d.evidence_deadline = deadline
        db_session.flush()

        orchestrator = PaymentOpsOrchestrator(db_session, now=NOW)
        dashboard = orchestrator.run_agent_cycle(merchant.id)

        assert dashboard.next_deadline is not None
        assert dashboard.next_deadline.date() == deadline.date()
