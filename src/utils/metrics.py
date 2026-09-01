"""Measurement framework — KPI calculations for the agent pipeline.

Provides deterministic metrics for detection quality, diagnosis accuracy,
evidence effectiveness, recommendation success, and business impact.

Usage::

    from src.utils.metrics import MetricsCalculator

    calc = MetricsCalculator(session)
    detection = calc.calculate_detection_metrics(baseline, detected)
    impact = calc.calculate_business_impact(merchant_id)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.data.models import (
    Anomaly,
    AnomalyStatus,
    AnomalyType,
    Diagnosis,
    Dispute,
    DisputeStatus,
    EvaluationMetric,
    Merchant,
    Recommendation,
    Refund,
    RefundStatus,
    Settlement,
    SettlementStatus,
    SeverityLevel,
)

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

DEFAULT_HOURLY_RATE_INR = Decimal("500.00")  # avg merchant ops person cost
SETTLEMENT_DELAY_COST_INR = Decimal("1000.00")  # estimated cost per delay event
CHARGEBACK_COST_INR = Decimal("15000.00")  # avg chargeback loss prevented
SUPPORT_TICKET_COST_INR = Decimal("200.00")  # avg cost per support ticket


class MetricsCalculator:
    """Calculate agent performance and business-impact metrics.

    Parameters
    ----------
    session : Session
        SQLAlchemy session for database queries.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    # ── 1. Detection metrics ──────────────────────────────────────────

    def calculate_detection_metrics(
        self,
        baseline_anomalies: List[Dict[str, Any]],
        detected_anomalies: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Calculate precision, recall, and F1 for anomaly detection.

        Parameters
        ----------
        baseline_anomalies : list of dict
            Ground-truth anomalies, each with at least ``id`` and ``type``.
        detected_anomalies : list of dict
            Agent-detected anomalies, each with ``id`` and ``type``.

        Returns
        -------
        dict
            precision, recall, f1, true_positives, false_positives, false_negatives
        """
        baseline_ids = {a["id"] for a in baseline_anomalies}
        detected_ids = {a["id"] for a in detected_anomalies}

        tp = len(baseline_ids & detected_ids)
        fp = len(detected_ids - baseline_ids)
        fn = len(baseline_ids - detected_ids)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )

        result = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
        }

        logger.info("Detection metrics: %s", result)
        return result

    # ── 2. Diagnosis accuracy ─────────────────────────────────────────

    def calculate_diagnosis_accuracy(
        self,
        true_diagnoses: List[Dict[str, Any]],
        predicted_diagnoses: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Calculate accuracy of root-cause predictions.

        Parameters
        ----------
        true_diagnoses : list of dict
            Actual root causes, each with ``id`` and ``root_cause``.
        predicted_diagnoses : list of dict
            Predicted root causes, each with ``id`` and ``root_cause``.

        Returns
        -------
        dict
            accuracy (0-1), correct_count, total_count
        """
        true_map = {d["id"]: d["root_cause"] for d in true_diagnoses}
        pred_map = {d["id"]: d["root_cause"] for d in predicted_diagnoses}

        common_ids = set(true_map.keys()) & set(pred_map.keys())
        total = len(common_ids)

        if total == 0:
            return {"accuracy": 0.0, "correct_count": 0, "total_count": 0}

        correct = sum(
            1 for cid in common_ids if true_map[cid] == pred_map[cid]
        )

        result = {
            "accuracy": round(correct / total, 4),
            "correct_count": correct,
            "total_count": total,
        }

        logger.info("Diagnosis accuracy: %s", result)
        return result

    # ── 3. Evidence metrics ───────────────────────────────────────────

    def calculate_evidence_metrics(
        self, dispute_outcomes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate evidence effectiveness for disputes.

        Parameters
        ----------
        dispute_outcomes : list of dict
            Each with ``dispute_id``, ``used_agent`` (bool), ``won`` (bool).

        Returns
        -------
        dict
            win_rate_with_agent, win_rate_baseline, improvement_percent
        """
        agent_disputes = [d for d in dispute_outcomes if d.get("used_agent")]
        baseline_disputes = [d for d in dispute_outcomes if not d.get("used_agent")]

        agent_wins = sum(1 for d in agent_disputes if d.get("won"))
        agent_total = len(agent_disputes)
        agent_rate = agent_wins / agent_total if agent_total > 0 else 0.0

        baseline_wins = sum(1 for d in baseline_disputes if d.get("won"))
        baseline_total = len(baseline_disputes)
        baseline_rate = baseline_wins / baseline_total if baseline_total > 0 else 0.0

        improvement = (
            ((agent_rate - baseline_rate) / baseline_rate * 100)
            if baseline_rate > 0
            else 0.0
        )

        result = {
            "win_rate_with_agent": round(agent_rate * 100, 1),
            "win_rate_baseline": round(baseline_rate * 100, 1),
            "improvement_percent": round(improvement, 1),
        }

        logger.info("Evidence metrics: %s", result)
        return result

    # ── 4. Action success rate ────────────────────────────────────────

    def calculate_action_success_rate(
        self,
        recommendations: List[Dict[str, Any]],
        outcomes: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Calculate how often followed recommendations resolved the issue.

        Parameters
        ----------
        recommendations : list of dict
            Each with ``id``, ``merchant_followed`` (bool).
        outcomes : list of dict
            Each with ``recommendation_id``, ``resolved`` (bool).

        Returns
        -------
        dict
            success_rate, total_followed, successful_outcomes
        """
        followed_ids = {
            r["id"] for r in recommendations if r.get("merchant_followed")
        }
        outcome_map = {o["recommendation_id"]: o.get("resolved", False) for o in outcomes}

        total_followed = len(followed_ids)
        successful = sum(
            1 for rid in followed_ids if outcome_map.get(rid, False)
        )

        success_rate = successful / total_followed if total_followed > 0 else 0.0

        result = {
            "success_rate": round(success_rate, 4),
            "total_followed": total_followed,
            "successful_outcomes": successful,
        }

        logger.info("Action success rate: %s", result)
        return result

    # ── 5. Business impact ────────────────────────────────────────────

    def calculate_business_impact(
        self, merchant_id, period_days: int = 30, now: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Calculate business impact for a merchant over a period.

        Queries resolved anomalies and calculates:
        - Time saved (hours × hourly rate)
        - Revenue recovered (chargebacks + settlement delays)
        - Support tickets reduced (estimate)
        - Net cost savings

        Returns
        -------
        dict
            time_saved_hours, revenue_recovered_inr, support_reduction,
            cost_savings_inr
        """
        cutoff = (now or datetime.utcnow()) - timedelta(days=period_days)

        # Query resolved anomalies in period
        resolved = (
            self.session.query(Anomaly)
            .filter(
                Anomaly.merchant_id == merchant_id,
                Anomaly.status == AnomalyStatus.RESOLVED,
                Anomaly.resolved_at >= cutoff,
            )
            .all()
        )

        # Time saved: 2h per settlement delay resolved, 1h per refund stuck
        time_saved = 0.0
        chargebacks_won = 0
        settlement_delays = 0
        refund_issues = 0

        for a in resolved:
            if a.anomaly_type in (
                AnomalyType.SETTLEMENT_DELAYED,
                AnomalyType.SETTLEMENT_FAILED,
                AnomalyType.SETTLEMENT_PARTIAL,
            ):
                time_saved += 2.0
                settlement_delays += 1
            elif a.anomaly_type in (
                AnomalyType.REFUND_STUCK,
                AnomalyType.REFUND_FAILED,
                AnomalyType.REFUND_REVERSED,
            ):
                time_saved += 1.5
                refund_issues += 1
            elif a.anomaly_type in (
                AnomalyType.DISPUTE_EVIDENCE_INCOMPLETE,
                AnomalyType.DISPUTE_DEADLINE_APPROACHING,
            ):
                time_saved += 3.0
                chargebacks_won += 1

        # Revenue recovered
        revenue_recovered = (
            Decimal(str(chargebacks_won)) * CHARGEBACK_COST_INR
            + Decimal(str(settlement_delays)) * SETTLEMENT_DELAY_COST_INR
        )

        # Time saved in monetary terms
        time_saved_value = Decimal(str(time_saved)) * DEFAULT_HOURLY_RATE_INR

        # Support tickets reduced (estimate: 0.5 tickets per resolved anomaly)
        support_reduction = len(resolved) * 0.5
        support_savings = Decimal(str(support_reduction)) * SUPPORT_TICKET_COST_INR

        # Net cost savings
        cost_savings = time_saved_value + revenue_recovered + support_savings

        result = {
            "time_saved_hours": round(time_saved, 1),
            "time_saved_value_inr": float(time_saved_value),
            "revenue_recovered_inr": float(revenue_recovered),
            "support_reduction_tickets": round(support_reduction, 1),
            "support_savings_inr": float(support_savings),
            "cost_savings_inr": float(cost_savings),
            "period_days": period_days,
            "anomalies_resolved": len(resolved),
            "chargebacks_won": chargebacks_won,
            "settlement_delays_prevented": settlement_delays,
            "refund_issues_resolved": refund_issues,
        }

        logger.info("Business impact for %s: %s", merchant_id, result)
        return result

    # ── 6. Record metrics to DB ───────────────────────────────────────

    def record_metric(
        self,
        merchant_id,
        metric_name: str,
        value: float,
        unit: str = "",
        dimensions: Optional[Dict] = None,
    ) -> EvaluationMetric:
        """Write a single metric to the evaluation_metrics table."""
        m = EvaluationMetric(
            merchant_id=merchant_id,
            metric_name=metric_name,
            metric_value=Decimal(str(value)),
            metric_unit=unit,
            dimensions=dimensions or {},
            recorded_at=datetime.utcnow(),
        )
        self.session.add(m)
        self.session.flush()
        logger.info("Recorded metric: %s = %s %s", metric_name, value, unit)
        return m

    def record_detection_cycle(
        self,
        merchant_id,
        detection_result: Dict[str, Any],
        diagnosis_result: Optional[Dict[str, Any]] = None,
        evidence_result: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record all metrics from a single detection cycle."""
        for key, val in detection_result.items():
            if isinstance(val, (int, float)):
                self.record_metric(
                    merchant_id, f"detection.{key}", val, unit="ratio"
                )

        if diagnosis_result:
            for key, val in diagnosis_result.items():
                if isinstance(val, (int, float)):
                    self.record_metric(
                        merchant_id, f"diagnosis.{key}", val, unit="ratio"
                    )

        if evidence_result:
            for key, val in evidence_result.items():
                if isinstance(val, (int, float)):
                    self.record_metric(
                        merchant_id, f"evidence.{key}", val, unit="ratio"
                    )

    # ── 7. Query historical metrics ───────────────────────────────────

    def get_metric_history(
        self,
        merchant_id,
        metric_name: str,
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """Fetch historical values for a metric."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        rows = (
            self.session.query(EvaluationMetric)
            .filter(
                EvaluationMetric.merchant_id == merchant_id,
                EvaluationMetric.metric_name == metric_name,
                EvaluationMetric.recorded_at >= cutoff,
            )
            .order_by(EvaluationMetric.recorded_at)
            .all()
        )
        return [
            {
                "recorded_at": str(r.recorded_at),
                "value": float(r.metric_value),
                "unit": r.metric_unit,
                "dimensions": r.dimensions,
            }
            for r in rows
        ]

    def get_latest_metric(
        self, merchant_id, metric_name: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch the most recent value for a metric."""
        row = (
            self.session.query(EvaluationMetric)
            .filter(
                EvaluationMetric.merchant_id == merchant_id,
                EvaluationMetric.metric_name == metric_name,
            )
            .order_by(EvaluationMetric.recorded_at.desc())
            .first()
        )
        if row is None:
            return None
        return {
            "recorded_at": str(row.recorded_at),
            "value": float(row.metric_value),
            "unit": row.metric_unit,
        }
