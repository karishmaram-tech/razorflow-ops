"""Tests for src/utils/metrics.py — MetricsCalculator.

Uses in-memory SQLite via the shared ``db_session`` fixture from test_setup.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from src.data.models import (
    Anomaly,
    AnomalyStatus,
    AnomalyType,
    EvaluationMetric,
    Merchant,
    SeverityLevel,
)
from src.utils.metrics import MetricsCalculator


# ── Helpers ────────────────────────────────────────────────────────────────────

NOW = datetime(2025, 6, 15, 12, 0, 0)


def _merchant(session) -> Merchant:
    m = Merchant(id=uuid.uuid4(), business_name="Metrics Test Co")
    session.add(m)
    session.flush()
    return m


def _anomaly(
    session,
    *,
    merchant_id,
    anomaly_type: AnomalyType = AnomalyType.SETTLEMENT_DELAYED,
    status: AnomalyStatus = AnomalyStatus.OPEN,
    resolved_at=None,
) -> Anomaly:
    a = Anomaly(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        anomaly_type=anomaly_type,
        detected_at=NOW - timedelta(days=5),
        status=status,
        severity=SeverityLevel.WARNING,
        root_cause="bank_processing_delay",
        resolved_at=resolved_at,
    )
    session.add(a)
    session.flush()
    return a


# ══════════════════════════════════════════════════════════════════════════════
# 1. Detection Metrics
# ══════════════════════════════════════════════════════════════════════════════


class TestDetectionMetrics:
    def test_perfect_detection(self, db_session):
        calc = MetricsCalculator(db_session)
        baseline = [{"id": "a1", "type": "delayed"}, {"id": "a2", "type": "failed"}]
        detected = [{"id": "a1", "type": "delayed"}, {"id": "a2", "type": "failed"}]

        result = calc.calculate_detection_metrics(baseline, detected)

        assert result["precision"] == 1.0
        assert result["recall"] == 1.0
        assert result["f1"] == 1.0
        assert result["true_positives"] == 2
        assert result["false_positives"] == 0
        assert result["false_negatives"] == 0

    def test_partial_detection(self, db_session):
        calc = MetricsCalculator(db_session)
        baseline = [{"id": "a1"}, {"id": "a2"}, {"id": "a3"}]
        detected = [{"id": "a1"}, {"id": "a4"}]  # a1=TP, a4=FP, a2,a3=FN

        result = calc.calculate_detection_metrics(baseline, detected)

        assert result["true_positives"] == 1
        assert result["false_positives"] == 1
        assert result["false_negatives"] == 2
        assert 0 < result["precision"] < 1
        assert 0 < result["recall"] < 1

    def test_no_detections(self, db_session):
        calc = MetricsCalculator(db_session)
        result = calc.calculate_detection_metrics(
            [{"id": "a1"}], []
        )
        assert result["recall"] == 0.0
        assert result["false_negatives"] == 1

    def test_empty_baseline(self, db_session):
        calc = MetricsCalculator(db_session)
        result = calc.calculate_detection_metrics(
            [], [{"id": "a1"}]
        )
        assert result["precision"] == 0.0
        assert result["false_positives"] == 1

    def test_both_empty(self, db_session):
        calc = MetricsCalculator(db_session)
        result = calc.calculate_detection_metrics([], [])
        assert result["precision"] == 0.0
        assert result["recall"] == 0.0
        assert result["f1"] == 0.0


# ══════════════════════════════════════════════════════════════════════════════
# 2. Diagnosis Accuracy
# ══════════════════════════════════════════════════════════════════════════════


class TestDiagnosisAccuracy:
    def test_perfect_accuracy(self, db_session):
        calc = MetricsCalculator(db_session)
        true = [{"id": "d1", "root_cause": "account_closed"}, {"id": "d2", "root_cause": "fraud_block"}]
        pred = [{"id": "d1", "root_cause": "account_closed"}, {"id": "d2", "root_cause": "fraud_block"}]

        result = calc.calculate_diagnosis_accuracy(true, pred)
        assert result["accuracy"] == 1.0
        assert result["correct_count"] == 2
        assert result["total_count"] == 2

    def test_partial_accuracy(self, db_session):
        calc = MetricsCalculator(db_session)
        true = [{"id": "d1", "root_cause": "account_closed"}, {"id": "d2", "root_cause": "fraud_block"}]
        pred = [{"id": "d1", "root_cause": "account_closed"}, {"id": "d2", "root_cause": "bank_error"}]

        result = calc.calculate_diagnosis_accuracy(true, pred)
        assert result["accuracy"] == 0.5
        assert result["correct_count"] == 1

    def test_no_overlap(self, db_session):
        calc = MetricsCalculator(db_session)
        true = [{"id": "d1", "root_cause": "a"}]
        pred = [{"id": "d99", "root_cause": "a"}]

        result = calc.calculate_diagnosis_accuracy(true, pred)
        assert result["accuracy"] == 0.0
        assert result["total_count"] == 0


# ══════════════════════════════════════════════════════════════════════════════
# 3. Evidence Metrics
# ══════════════════════════════════════════════════════════════════════════════


class TestEvidenceMetrics:
    def test_agent_improves_win_rate(self, db_session):
        calc = MetricsCalculator(db_session)
        outcomes = [
            {"dispute_id": "d1", "used_agent": True, "won": True},
            {"dispute_id": "d2", "used_agent": True, "won": True},
            {"dispute_id": "d3", "used_agent": True, "won": False},
            {"dispute_id": "d4", "used_agent": False, "won": False},
            {"dispute_id": "d5", "used_agent": False, "won": True},
        ]

        result = calc.calculate_evidence_metrics(outcomes)

        assert result["win_rate_with_agent"] == pytest.approx(66.7, abs=0.1)
        assert result["win_rate_baseline"] == pytest.approx(50.0, abs=0.1)
        assert result["improvement_percent"] > 0

    def test_no_agent_disputes(self, db_session):
        calc = MetricsCalculator(db_session)
        outcomes = [{"dispute_id": "d1", "used_agent": False, "won": True}]

        result = calc.calculate_evidence_metrics(outcomes)
        assert result["win_rate_with_agent"] == 0.0
        assert result["win_rate_baseline"] == 100.0

    def test_empty_outcomes(self, db_session):
        calc = MetricsCalculator(db_session)
        result = calc.calculate_evidence_metrics([])
        assert result["win_rate_with_agent"] == 0.0
        assert result["win_rate_baseline"] == 0.0


# ══════════════════════════════════════════════════════════════════════════════
# 4. Action Success Rate
# ══════════════════════════════════════════════════════════════════════════════


class TestActionSuccessRate:
    def test_high_success_rate(self, db_session):
        calc = MetricsCalculator(db_session)
        recs = [
            {"id": "r1", "merchant_followed": True},
            {"id": "r2", "merchant_followed": True},
            {"id": "r3", "merchant_followed": True},
            {"id": "r4", "merchant_followed": False},
        ]
        outcomes = [
            {"recommendation_id": "r1", "resolved": True},
            {"recommendation_id": "r2", "resolved": True},
            {"recommendation_id": "r3", "resolved": False},
        ]

        result = calc.calculate_action_success_rate(recs, outcomes)

        assert result["total_followed"] == 3
        assert result["successful_outcomes"] == 2
        assert result["success_rate"] == pytest.approx(0.6667, abs=0.01)

    def test_no_followed_recommendations(self, db_session):
        calc = MetricsCalculator(db_session)
        recs = [{"id": "r1", "merchant_followed": False}]
        result = calc.calculate_action_success_rate(recs, [])
        assert result["success_rate"] == 0.0
        assert result["total_followed"] == 0


# ══════════════════════════════════════════════════════════════════════════════
# 5. Business Impact
# ══════════════════════════════════════════════════════════════════════════════


class TestBusinessImpact:
    def test_impact_with_resolved_anomalies(self, db_session):
        merchant = _merchant(db_session)

        # Create resolved anomalies
        _anomaly(db_session, merchant_id=merchant.id,
                 anomaly_type=AnomalyType.SETTLEMENT_DELAYED,
                 status=AnomalyStatus.RESOLVED, resolved_at=NOW - timedelta(days=1))
        _anomaly(db_session, merchant_id=merchant.id,
                 anomaly_type=AnomalyType.SETTLEMENT_DELAYED,
                 status=AnomalyStatus.RESOLVED, resolved_at=NOW - timedelta(days=2))
        _anomaly(db_session, merchant_id=merchant.id,
                 anomaly_type=AnomalyType.REFUND_STUCK,
                 status=AnomalyStatus.RESOLVED, resolved_at=NOW - timedelta(days=3))
        _anomaly(db_session, merchant_id=merchant.id,
                 anomaly_type=AnomalyType.DISPUTE_EVIDENCE_INCOMPLETE,
                 status=AnomalyStatus.RESOLVED, resolved_at=NOW - timedelta(days=4))

        calc = MetricsCalculator(db_session)
        result = calc.calculate_business_impact(merchant.id, period_days=30, now=NOW)

        assert result["time_saved_hours"] == 8.5  # 2+2+1.5+3 = 8.5
        assert result["chargebacks_won"] == 1
        assert result["settlement_delays_prevented"] == 2
        assert result["anomalies_resolved"] == 4
        assert result["cost_savings_inr"] > 0

    def test_impact_no_resolved(self, db_session):
        merchant = _merchant(db_session)
        calc = MetricsCalculator(db_session)
        result = calc.calculate_business_impact(merchant.id)

        assert result["time_saved_hours"] == 0.0
        assert result["anomalies_resolved"] == 0
        assert result["cost_savings_inr"] == 0.0


# ══════════════════════════════════════════════════════════════════════════════
# 6. Record & Query Metrics
# ══════════════════════════════════════════════════════════════════════════════


class TestRecordAndQuery:
    def test_record_metric(self, db_session):
        merchant = _merchant(db_session)
        calc = MetricsCalculator(db_session)

        m = calc.record_metric(merchant.id, "test.metric", 42.5, unit="count")
        assert m.metric_name == "test.metric"
        assert m.metric_value == Decimal("42.5000")

    def test_record_detection_cycle(self, db_session):
        merchant = _merchant(db_session)
        calc = MetricsCalculator(db_session)

        calc.record_detection_cycle(
            merchant.id,
            detection_result={"precision": 0.9, "recall": 0.85, "f1": 0.87},
        )

        metrics = calc.get_metric_history(merchant.id, "detection.precision", days=1)
        assert len(metrics) == 1
        assert metrics[0]["value"] == 0.9

    def test_get_latest_metric(self, db_session):
        merchant = _merchant(db_session)
        calc = MetricsCalculator(db_session)

        calc.record_metric(merchant.id, "test.latest", 10.0)
        calc.record_metric(merchant.id, "test.latest", 20.0)

        latest = calc.get_latest_metric(merchant.id, "test.latest")
        assert latest is not None
        assert latest["value"] == 20.0

    def test_get_metric_history_empty(self, db_session):
        merchant = _merchant(db_session)
        calc = MetricsCalculator(db_session)
        history = calc.get_metric_history(merchant.id, "nonexistent.metric")
        assert history == []
