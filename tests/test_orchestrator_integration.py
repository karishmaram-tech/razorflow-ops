"""Integration tests for the PaymentOpsOrchestrator full agent cycle.

These tests exercise the complete detect → classify → recommend → persist
pipeline end-to-end through the orchestrator, verifying that anomalies,
diagnoses, and recommendations are correctly created and saved to the DB.

Uses in-memory SQLite via the shared ``db_session`` fixture from test_setup.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from src.agents.orchestrator import (
    DashboardUpdate,
    ImpactSummary,
    PaymentOpsOrchestrator,
)
from src.data.models import (
    Anomaly,
    AnomalyStatus,
    AnomalyType,
    Diagnosis,
    Dispute,
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
    SettlementStatus,
    Transaction,
    UrgencyLevel,
)


# ── Test Constants ─────────────────────────────────────────────────────────────

NOW = datetime(2025, 6, 15, 12, 0, 0)


# ── Helpers ────────────────────────────────────────────────────────────────────


def _create_merchant(
    session,
    *,
    name: str = "Integration Test Co",
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


def _create_settlement(
    session,
    *,
    merchant_id,
    status: SettlementStatus = SettlementStatus.PENDING,
    created_at: datetime | None = None,
    amount: Decimal = Decimal("100000.00"),
    fees: Decimal = Decimal("2000.00"),
) -> Settlement:
    s = Settlement(
        id=f"settle_{uuid.uuid4().hex[:8]}",
        merchant_id=merchant_id,
        amount=amount,
        currency="INR",
        status=status,
        created_at=created_at or (NOW - timedelta(days=5)),
        fees=fees,
        taxes=fees * Decimal("0.18"),
        net_amount=amount - fees - (fees * Decimal("0.18")),
        related_refunds=[],
        related_disputes=[],
    )
    session.add(s)
    session.flush()
    return s


def _create_transaction(
    session,
    *,
    merchant_id,
    amount: Decimal = Decimal("5000.00"),
) -> Transaction:
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


def _create_refund(
    session,
    *,
    merchant_id,
    transaction_id: str,
    status: RefundStatus = RefundStatus.PENDING,
    created_at: datetime | None = None,
    amount: Decimal = Decimal("2500.00"),
) -> Refund:
    r = Refund(
        id=f"rfnd_{uuid.uuid4().hex[:8]}",
        merchant_id=merchant_id,
        transaction_id=transaction_id,
        amount=amount,
        reason=RefundReason.CUSTOMER_REQUESTED,
        status=status,
        created_at=created_at or (NOW - timedelta(days=5)),
        initiated_by=RefundInitiator.MERCHANT,
    )
    session.add(r)
    session.flush()
    return r


def _create_dispute(
    session,
    *,
    merchant_id,
    transaction_id: str,
    reason_code: str = "4855",
    filed_at: datetime | None = None,
    evidence_deadline: datetime | None = None,
) -> Dispute:
    d = Dispute(
        id=f"disp_{uuid.uuid4().hex[:8]}",
        merchant_id=merchant_id,
        transaction_id=transaction_id,
        type=DisputeType.CHARGEBACK,
        reason_code=reason_code,
        reason_text=f"Test dispute {reason_code}",
        amount=Decimal("10000.00"),
        filed_at=filed_at or (NOW - timedelta(days=3)),
        evidence_deadline=evidence_deadline or (NOW + timedelta(days=4)),
        current_status=DisputeStatus.EVIDENCE_PENDING,
    )
    session.add(d)
    session.flush()
    return d


# ══════════════════════════════════════════════════════════════════════════════
# Integration Test 1: Full settlement delay cycle
# ══════════════════════════════════════════════════════════════════════════════


class TestSettlementDelayIntegration:
    """Verify the complete pipeline for a delayed settlement."""

    def test_full_cycle_settlement_delay(self, db_session):
        """Delayed settlement → anomaly + diagnosis + recommendation → dashboard."""
        merchant = _create_merchant(db_session, name="Delay Merchant")
        settlement = _create_settlement(
            db_session,
            merchant_id=merchant.id,
            status=SettlementStatus.PENDING,
            created_at=NOW - timedelta(days=5),
        )

        orchestrator = PaymentOpsOrchestrator(db_session, now=NOW)
        dashboard = orchestrator.run_agent_cycle(merchant.id)

        # Dashboard returned
        assert isinstance(dashboard, DashboardUpdate)
        assert dashboard.merchant_id == str(merchant.id)

        # Anomaly created in DB
        anomalies = (
            db_session.query(Anomaly)
            .filter(Anomaly.merchant_id == merchant.id)
            .all()
        )
        assert len(anomalies) >= 1
        settlement_anomalies = [
            a for a in anomalies if a.anomaly_type == AnomalyType.SETTLEMENT_DELAYED
        ]
        assert len(settlement_anomalies) >= 1

        anomaly = settlement_anomalies[0]
        assert anomaly.severity in (SeverityLevel.WARNING, SeverityLevel.CRITICAL)
        assert anomaly.related_settlement_id == settlement.id

        # Diagnosis created and linked
        diagnosis = (
            db_session.query(Diagnosis)
            .filter(Diagnosis.anomaly_id == anomaly.id)
            .first()
        )
        assert diagnosis is not None
        assert diagnosis.root_cause_category is not None
        assert diagnosis.confidence > 0

        # Recommendation created and linked
        recommendation = (
            db_session.query(Recommendation)
            .filter(Recommendation.anomaly_id == anomaly.id)
            .first()
        )
        assert recommendation is not None
        assert recommendation.recommended_action is not None
        assert recommendation.urgency in UrgencyLevel

        # Dashboard contains the anomaly
        total = (
            len(dashboard.critical_anomalies)
            + len(dashboard.warning_anomalies)
            + len(dashboard.info_anomalies)
        )
        assert total >= 1
        assert len(dashboard.top_recommendations) >= 1

        # Metrics recorded
        metrics = (
            db_session.query(EvaluationMetric)
            .filter(EvaluationMetric.merchant_id == merchant.id)
            .all()
        )
        assert len(metrics) >= 1


# ══════════════════════════════════════════════════════════════════════════════
# Integration Test 2: Full refund stuck cycle
# ══════════════════════════════════════════════════════════════════════════════


class TestRefundStuckIntegration:
    """Verify the complete pipeline for a stuck refund."""

    def test_full_cycle_refund_stuck(self, db_session):
        """Stuck refund → anomaly + diagnosis + recommendation."""
        merchant = _create_merchant(db_session, name="Refund Merchant")
        txn = _create_transaction(db_session, merchant_id=merchant.id)
        refund = _create_refund(
            db_session,
            merchant_id=merchant.id,
            transaction_id=txn.id,
            status=RefundStatus.PENDING,
            created_at=NOW - timedelta(days=5),
        )

        orchestrator = PaymentOpsOrchestrator(db_session, now=NOW)
        dashboard = orchestrator.run_agent_cycle(merchant.id)

        # Anomaly in DB
        anomalies = (
            db_session.query(Anomaly)
            .filter(Anomaly.merchant_id == merchant.id)
            .all()
        )
        refund_anomalies = [
            a for a in anomalies if a.anomaly_type == AnomalyType.REFUND_STUCK
        ]
        assert len(refund_anomalies) >= 1

        anomaly = refund_anomalies[0]
        assert anomaly.related_refund_id == refund.id

        # Diagnosis linked
        diagnosis = (
            db_session.query(Diagnosis)
            .filter(Diagnosis.anomaly_id == anomaly.id)
            .first()
        )
        assert diagnosis is not None
        assert diagnosis.explanation_plain_english is not None

        # Recommendation linked
        recommendation = (
            db_session.query(Recommendation)
            .filter(Recommendation.anomaly_id == anomaly.id)
            .first()
        )
        assert recommendation is not None
        assert recommendation.success_probability > 0

        # Dashboard
        total = (
            len(dashboard.critical_anomalies)
            + len(dashboard.warning_anomalies)
            + len(dashboard.info_anomalies)
        )
        assert total >= 1


# ══════════════════════════════════════════════════════════════════════════════
# Integration Test 3: Full dispute evidence cycle
# ══════════════════════════════════════════════════════════════════════════════


class TestDisputeEvidenceIntegration:
    """Verify the complete pipeline for dispute evidence assembly."""

    def test_full_cycle_dispute_evidence(self, db_session):
        """Dispute with no evidence → anomaly + diagnosis + recommendation."""
        merchant = _create_merchant(db_session, name="Dispute Merchant")
        txn = _create_transaction(db_session, merchant_id=merchant.id)
        dispute = _create_dispute(
            db_session,
            merchant_id=merchant.id,
            transaction_id=txn.id,
            reason_code="4855",
            evidence_deadline=NOW + timedelta(days=4),
        )

        orchestrator = PaymentOpsOrchestrator(db_session, now=NOW)
        dashboard = orchestrator.run_agent_cycle(merchant.id)

        # Anomaly for evidence incomplete
        anomalies = (
            db_session.query(Anomaly)
            .filter(Anomaly.merchant_id == merchant.id)
            .all()
        )
        evidence_anomalies = [
            a
            for a in anomalies
            if a.anomaly_type == AnomalyType.DISPUTE_EVIDENCE_INCOMPLETE
        ]
        assert len(evidence_anomalies) >= 1

        anomaly = evidence_anomalies[0]
        assert anomaly.related_dispute_id == dispute.id

        # Diagnosis shows completeness info
        diagnosis = (
            db_session.query(Diagnosis)
            .filter(Diagnosis.anomaly_id == anomaly.id)
            .first()
        )
        assert diagnosis is not None
        assert "completeness" in diagnosis.root_cause_category.lower() or "evidence" in diagnosis.root_cause_category.lower()

        # Recommendation suggests uploading evidence
        rec = (
            db_session.query(Recommendation)
            .filter(Recommendation.anomaly_id == anomaly.id)
            .first()
        )
        assert rec is not None
        assert rec.recommended_action is not None

        # Dashboard contains dispute anomaly
        total = (
            len(dashboard.critical_anomalies)
            + len(dashboard.warning_anomalies)
            + len(dashboard.info_anomalies)
        )
        assert total >= 1


# ══════════════════════════════════════════════════════════════════════════════
# Integration Test 4: Dashboard generation
# ══════════════════════════════════════════════════════════════════════════════


class TestDashboardGenerationIntegration:
    """Verify dashboard structure after running the full cycle."""

    def test_dashboard_generation(self, db_session):
        """Run cycle with mixed issues → verify dashboard structure."""
        merchant = _create_merchant(db_session, name="Dashboard Merchant")

        # Delayed settlement
        _create_settlement(
            db_session,
            merchant_id=merchant.id,
            status=SettlementStatus.PENDING,
            created_at=NOW - timedelta(days=5),
        )

        # Stuck refund
        txn = _create_transaction(db_session, merchant_id=merchant.id)
        _create_refund(
            db_session,
            merchant_id=merchant.id,
            transaction_id=txn.id,
            status=RefundStatus.PENDING,
            created_at=NOW - timedelta(days=5),
        )

        # Dispute with deadline approaching
        _create_dispute(
            db_session,
            merchant_id=merchant.id,
            transaction_id=txn.id,
            evidence_deadline=NOW + timedelta(days=2),
        )

        orchestrator = PaymentOpsOrchestrator(db_session, now=NOW)
        dashboard = orchestrator.run_agent_cycle(merchant.id)

        # Dashboard structure
        assert isinstance(dashboard, DashboardUpdate)
        assert dashboard.merchant_id == str(merchant.id)
        assert isinstance(dashboard.impact, ImpactSummary)
        assert isinstance(dashboard.summary, dict)

        # Summary fields
        assert "total_anomalies" in dashboard.summary
        assert "critical_count" in dashboard.summary
        assert "warning_count" in dashboard.summary
        assert "info_count" in dashboard.summary
        assert "total_recommendations" in dashboard.summary
        assert "unfollowed_recommendations" in dashboard.summary

        # Counts add up
        total = (
            dashboard.summary["critical_count"]
            + dashboard.summary["warning_count"]
            + dashboard.summary["info_count"]
        )
        assert total == dashboard.summary["total_anomalies"]

        # Next deadline should be set (dispute approaching)
        assert dashboard.next_deadline is not None

        # Impact
        assert isinstance(dashboard.impact, ImpactSummary)
        assert dashboard.impact.anomalies_detected >= 0


# ══════════════════════════════════════════════════════════════════════════════
# Integration Test 5: Edge cases
# ══════════════════════════════════════════════════════════════════════════════


class TestEdgeCasesIntegration:
    """Test the 5 edge-case scenarios from the project spec."""

    def test_delayed_settlement_3_days(self, db_session):
        """Edge case 1: Settlement delayed past T+2 → detected as delayed."""
        merchant = _create_merchant(db_session, name="Edge: Delay 5d")
        _create_settlement(
            db_session,
            merchant_id=merchant.id,
            status=SettlementStatus.PENDING,
            created_at=NOW - timedelta(days=5),
        )

        orchestrator = PaymentOpsOrchestrator(db_session, now=NOW)
        dashboard = orchestrator.run_agent_cycle(merchant.id)

        critical = [
            a for a in dashboard.critical_anomalies
            if a["type"] == "settlement_delayed"
        ]
        warning = [
            a for a in dashboard.warning_anomalies
            if a["type"] == "settlement_delayed"
        ]
        # Should be detected as delayed
        assert len(critical) + len(warning) >= 1

    def test_failed_settlement_with_retries(self, db_session):
        """Edge case 2: Settlement failed with multiple retry attempts."""
        from src.data.models import SettlementAttempt

        merchant = _create_merchant(db_session, name="Edge: Failed Retries")
        settlement = _create_settlement(
            db_session,
            merchant_id=merchant.id,
            status=SettlementStatus.FAILED,
            created_at=NOW - timedelta(days=2),
        )

        # Add 3 failed attempts
        for i in range(3):
            attempt = SettlementAttempt(
                settlement_id=settlement.id,
                attempt_number=i + 1,
                method=["IMPS", "NEFT", "RTGS"][i],
                initiated_at=NOW - timedelta(days=2, hours=-i * 4),
                response_code="40091",
                response_message="Insufficient funds",
                status="failed",
            )
            db_session.add(attempt)
        db_session.flush()

        orchestrator = PaymentOpsOrchestrator(db_session, now=NOW)
        dashboard = orchestrator.run_agent_cycle(merchant.id)

        # Should have at least settlement_failed anomaly
        all_anomalies = (
            dashboard.critical_anomalies
            + dashboard.warning_anomalies
            + dashboard.info_anomalies
        )
        types = {a["type"] for a in all_anomalies}
        assert "settlement_failed" in types or "settlement_multiple_failures" in types

    def test_refund_stuck_5_days(self, db_session):
        """Edge case 3: Refund stuck for 5 days → WARNING → CRITICAL."""
        merchant = _create_merchant(db_session, name="Edge: Refund 5d")
        txn = _create_transaction(db_session, merchant_id=merchant.id)
        refund = _create_refund(
            db_session,
            merchant_id=merchant.id,
            transaction_id=txn.id,
            status=RefundStatus.PENDING,
            created_at=NOW - timedelta(days=5),
        )

        orchestrator = PaymentOpsOrchestrator(db_session, now=NOW)
        dashboard = orchestrator.run_agent_cycle(merchant.id)

        all_anomalies = (
            dashboard.critical_anomalies
            + dashboard.warning_anomalies
            + dashboard.info_anomalies
        )
        refund_issues = [a for a in all_anomalies if "refund" in a["type"]]
        assert len(refund_issues) >= 1

    def test_dispute_deadline_2_days_zero_evidence(self, db_session):
        """Edge case 4: Dispute deadline in 2 days, zero evidence → CRITICAL."""
        merchant = _create_merchant(db_session, name="Edge: Deadline 2d")
        txn = _create_transaction(db_session, merchant_id=merchant.id)
        dispute = _create_dispute(
            db_session,
            merchant_id=merchant.id,
            transaction_id=txn.id,
            evidence_deadline=NOW + timedelta(days=2),
        )

        orchestrator = PaymentOpsOrchestrator(db_session, now=NOW)
        dashboard = orchestrator.run_agent_cycle(merchant.id)

        # Should have deadline anomaly or evidence incomplete
        all_anomalies = (
            dashboard.critical_anomalies
            + dashboard.warning_anomalies
            + dashboard.info_anomalies
        )
        dispute_anomalies = [
            a for a in all_anomalies if "dispute" in a["type"]
        ]
        assert len(dispute_anomalies) >= 1

        # At least one should be critical (deadline or evidence)
        critical_dispute = [
            a for a in all_anomalies
            if a["severity"] == "critical" and "dispute" in a["type"]
        ]
        assert len(critical_dispute) >= 1

    def test_high_dispute_rate_merchant(self, db_session):
        """Edge case 5: Merchant with high dispute rate (pattern detection)."""
        merchant = _create_merchant(db_session, name="Edge: High Dispute Rate")

        # Create 5 disputes (high pattern)
        txn = _create_transaction(db_session, merchant_id=merchant.id)
        for i in range(5):
            _create_dispute(
                db_session,
                merchant_id=merchant.id,
                transaction_id=txn.id,
                reason_code=["4855", "4849", "4871", "4834", "4855"][i],
                evidence_deadline=NOW + timedelta(days=7 - i),
            )

        orchestrator = PaymentOpsOrchestrator(db_session, now=NOW)
        dashboard = orchestrator.run_agent_cycle(merchant.id)

        # Should detect multiple dispute-related anomalies
        all_anomalies = (
            dashboard.critical_anomalies
            + dashboard.warning_anomalies
            + dashboard.info_anomalies
        )
        assert len(all_anomalies) >= 3  # At least 3 disputes with evidence gaps


# ══════════════════════════════════════════════════════════════════════════════
# Integration Test 6: Multi-merchant isolation
# ══════════════════════════════════════════════════════════════════════════════


class TestMultiMerchantIntegration:
    """Verify merchant data isolation."""

    def test_merchants_isolated(self, db_session):
        """Merchant A issues don't appear in Merchant B dashboard."""
        m_a = _create_merchant(db_session, name="Merchant A")
        m_b = _create_merchant(db_session, name="Merchant B")

        # Only Merchant A has issues
        _create_settlement(
            db_session,
            merchant_id=m_a.id,
            status=SettlementStatus.PENDING,
            created_at=NOW - timedelta(days=5),
        )

        # Merchant B is clean
        _create_settlement(
            db_session,
            merchant_id=m_b.id,
            status=SettlementStatus.SUCCESS,
            created_at=NOW - timedelta(hours=2),
        )

        orchestrator = PaymentOpsOrchestrator(db_session, now=NOW)
        dash_a = orchestrator.run_agent_cycle(m_a.id)
        dash_b = orchestrator.run_agent_cycle(m_b.id)

        # Merchant A has anomalies
        total_a = (
            len(dash_a.critical_anomalies)
            + len(dash_a.warning_anomalies)
            + len(dash_a.info_anomalies)
        )
        assert total_a >= 1

        # Merchant B has none
        total_b = (
            len(dash_b.critical_anomalies)
            + len(dash_b.warning_anomalies)
            + len(dash_b.info_anomalies)
        )
        assert total_b == 0

        # DB anomalies are isolated
        a_anomalies = (
            db_session.query(Anomaly)
            .filter(Anomaly.merchant_id == m_a.id)
            .all()
        )
        b_anomalies = (
            db_session.query(Anomaly)
            .filter(Anomaly.merchant_id == m_b.id)
            .all()
        )
        assert len(a_anomalies) >= 1
        assert len(b_anomalies) == 0
