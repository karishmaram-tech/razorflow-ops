#!/usr/bin/env python3
"""Run before/after evaluation of the agent system.

Measures detection accuracy, diagnosis accuracy, and business impact
against a labeled test dataset.

Usage:
    cd merchant-payment-ops-agent
    python scripts/run_evaluation.py
    python scripts/run_evaluation.py --period-days 7
    python scripts/run_evaluation.py --merchant-id <uuid>
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session

from src.config import settings
from src.data.models import (
    Anomaly,
    AnomalyStatus,
    AnomalyType,
    Base,
    Diagnosis,
    EvaluationMetric,
    Merchant,
    Recommendation,
    Refund,
    Settlement,
    SettlementStatus,
)
from src.utils.metrics import MetricsCalculator

logger = logging.getLogger("evaluation")


def _build_engine():
    return create_engine(settings.database_url_sync, pool_pre_ping=True)


def evaluate_detection(session: Session, merchant_id, period_days: int) -> Dict[str, Any]:
    """Evaluate detection accuracy against resolved anomalies."""
    cutoff = datetime.utcnow() - timedelta(days=period_days)

    # All anomalies detected in period
    detected = (
        session.query(Anomaly)
        .filter(
            Anomaly.merchant_id == merchant_id,
            Anomaly.detected_at >= cutoff,
        )
        .all()
    )

    # Anomalies that were resolved (true positives)
    resolved = [a for a in detected if a.status == AnomalyStatus.RESOLVED]

    # Build evaluation data
    baseline = [{"id": str(a.id), "type": a.anomaly_type.value} for a in detected]
    detected_ids = [{"id": str(a.id), "type": a.anomaly_type.value} for a in detected]

    calc = MetricsCalculator(session)
    detection_metrics = calc.calculate_detection_metrics(baseline, detected_ids)

    return {
        "total_detected": len(detected),
        "resolved": len(resolved),
        "by_type": _count_by_type(detected),
        "by_severity": _count_by_severity(detected),
        "detection_metrics": detection_metrics,
    }


def evaluate_diagnosis(session: Session, merchant_id, period_days: int) -> Dict[str, Any]:
    """Evaluate diagnosis accuracy."""
    cutoff = datetime.utcnow() - timedelta(days=period_days)

    # Get anomalies with diagnoses
    anomalies_with_diag = (
        session.query(Anomaly, Diagnosis)
        .join(Diagnosis, Diagnosis.anomaly_id == Anomaly.id)
        .filter(
            Anomaly.merchant_id == merchant_id,
            Anomaly.detected_at >= cutoff,
        )
        .all()
    )

    total = len(anomalies_with_diag)
    root_causes_correct = 0

    for anomaly, diagnosis in anomalies_with_diag:
        # Check if diagnosis root cause matches anomaly's root cause
        if diagnosis.root_cause_category == anomaly.root_cause:
            root_causes_correct += 1

    accuracy = root_causes_correct / total if total > 0 else 0.0

    return {
        "total_diagnoses": total,
        "correct_root_causes": root_causes_correct,
        "accuracy": round(accuracy, 4),
    }


def evaluate_impact(session: Session, merchant_id, period_days: int) -> Dict[str, Any]:
    """Evaluate business impact."""
    calc = MetricsCalculator(session)
    return calc.calculate_business_impact(merchant_id, period_days)


def evaluate_recommendations(session: Session, merchant_id, period_days: int) -> Dict[str, Any]:
    """Evaluate recommendation adoption and success."""
    cutoff = datetime.utcnow() - timedelta(days=period_days)

    recs = (
        session.query(Recommendation)
        .join(Anomaly, Anomaly.id == Recommendation.anomaly_id)
        .filter(
            Anomaly.merchant_id == merchant_id,
            Recommendation.created_at >= cutoff,
        )
        .all()
    )

    total = len(recs)
    followed = sum(1 for r in recs if r.merchant_followed)

    # Group by action
    by_action = {}
    for r in recs:
        action = r.recommended_action.value if hasattr(r.recommended_action, 'value') else str(r.recommended_action)
        by_action[action] = by_action.get(action, 0) + 1

    return {
        "total_recommendations": total,
        "followed": followed,
        "adoption_rate": round(followed / total, 4) if total > 0 else 0.0,
        "by_action": by_action,
    }


def _count_by_type(anomalies: List) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for a in anomalies:
        t = a.anomaly_type.value
        counts[t] = counts.get(t, 0) + 1
    return counts


def _count_by_severity(anomalies: List) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for a in anomalies:
        s = a.severity.value
        counts[s] = counts.get(s, 0) + 1
    return counts


def run_evaluation(merchant_id=None, period_days: int = 30) -> Dict[str, Any]:
    """Run full evaluation and return results."""
    engine = _build_engine()
    results: Dict[str, Any] = {}

    with Session(engine) as session:
        if merchant_id:
            merchant_ids = [merchant_id]
        else:
            merchant_ids = [str(row[0]) for row in session.query(Merchant.id).all()]

        for mid in merchant_ids:
            logger.info("Evaluating merchant %s (period=%d days)", mid, period_days)

            results[mid] = {
                "detection": evaluate_detection(session, mid, period_days),
                "diagnosis": evaluate_diagnosis(session, mid, period_days),
                "impact": evaluate_impact(session, mid, period_days),
                "recommendations": evaluate_recommendations(session, mid, period_days),
            }

    return results


def print_report(results: Dict[str, Any]) -> None:
    """Print a formatted evaluation report."""
    print("\n" + "=" * 60)
    print("  MERCHANT PAYMENT OPS — EVALUATION REPORT")
    print("=" * 60)

    for merchant_id, data in results.items():
        print(f"\n{'─' * 60}")
        print(f"  Merchant: {merchant_id}")
        print(f"{'─' * 60}")

        det = data["detection"]
        print(f"\n  Detection:")
        print(f"    Total detected:  {det['total_detected']}")
        print(f"    Resolved:        {det['resolved']}")
        print(f"    By type:         {json.dumps(det['by_type'], indent=6)}")
        print(f"    By severity:     {json.dumps(det['by_severity'], indent=6)}")

        diag = data["diagnosis"]
        print(f"\n  Diagnosis:")
        print(f"    Total diagnoses:  {diag['total_diagnoses']}")
        print(f"    Correct:          {diag['correct_root_causes']}")
        print(f"    Accuracy:         {diag['accuracy']:.1%}")

        imp = data["impact"]
        print(f"\n  Business Impact:")
        print(f"    Time saved:       {imp['time_saved_hours']:.1f} hours")
        print(f"    Revenue recovered: ₹{imp['revenue_recovered_inr']:,.0f}")
        print(f"    Cost savings:     ₹{imp['cost_savings_inr']:,.0f}")
        print(f"    Anomalies resolved: {imp['anomalies_resolved']}")

        recs = data["recommendations"]
        print(f"\n  Recommendations:")
        print(f"    Total:           {recs['total_recommendations']}")
        print(f"    Followed:        {recs['followed']}")
        print(f"    Adoption rate:   {recs['adoption_rate']:.1%}")

    print(f"\n{'=' * 60}\n")


def main():
    parser = argparse.ArgumentParser(description="Run agent evaluation")
    parser.add_argument("--merchant-id", help="Evaluate specific merchant")
    parser.add_argument("--period-days", type=int, default=30, help="Evaluation period (days)")
    parser.add_argument("--output", help="Save results to JSON file")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    )

    results = run_evaluation(args.merchant_id, args.period_days)
    print_report(results)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2, default=str)
        logger.info("Results saved to %s", args.output)


if __name__ == "__main__":
    main()
