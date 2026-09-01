"""Multi-Agent Orchestrator — coordinates the full payment-ops pipeline.

Runs the detect → classify → recommend cycle for settlements, refunds,
and disputes; aggregates results; generates notifications; and records
evaluation metrics.

Usage::

    from src.agents.orchestrator import PaymentOpsOrchestrator

    orchestrator = PaymentOpsOrchestrator(session)
    dashboard = orchestrator.run_agent_cycle(merchant_id)
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.agents.dispute_agent import (
    DisputeWinPredictor,
    EvidenceAssembler,
    EvidencePacket,
    EvidenceRequirementMapper,
)
from src.agents.refund_agent import (
    RefundActionRecommender,
    RefundAnomalyDetector,
    RefundRootCauseClassifier,
)
from src.agents.settlement_agent import (
    SettlementActionRecommender,
    SettlementAnomalyDetector,
    SettlementRootCauseClassifier,
)
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
    SeverityLevel,
    Settlement,
    SettlementStatus,
    UrgencyLevel,
)

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

CYCLE_LOOKBACK_HOURS = 168  # 7 days — long enough for delayed settlements
SEVERITY_ORDER = {
    SeverityLevel.CRITICAL: 0,
    SeverityLevel.WARNING: 1,
    SeverityLevel.INFO: 2,
}


# ══════════════════════════════════════════════════════════════════════════════
# Data containers
# ══════════════════════════════════════════════════════════════════════════════


@dataclass
class ImpactSummary:
    """Aggregate impact metrics for the merchant."""

    time_saved_hours: float = 0.0
    revenue_recovered_inr: float = 0.0
    chargebacks_won: int = 0
    settlement_delays_prevented: int = 0
    anomalies_detected: int = 0
    anomalies_resolved: int = 0


@dataclass
class DashboardUpdate:
    """Complete dashboard view returned by the orchestrator cycle."""

    merchant_id: str
    cycle_at: datetime
    critical_anomalies: List[Dict[str, Any]] = field(default_factory=list)
    warning_anomalies: List[Dict[str, Any]] = field(default_factory=list)
    info_anomalies: List[Dict[str, Any]] = field(default_factory=list)
    top_recommendations: List[Dict[str, Any]] = field(default_factory=list)
    impact: ImpactSummary = field(default_factory=ImpactSummary)
    next_deadline: Optional[datetime] = None
    summary: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CycleResult:
    """Internal result of processing one resource type."""

    anomalies: List[Anomaly] = field(default_factory=list)
    diagnoses: List[Diagnosis] = field(default_factory=list)
    recommendations: List[Recommendation] = field(default_factory=list)


# ══════════════════════════════════════════════════════════════════════════════
# Orchestrator
# ══════════════════════════════════════════════════════════════════════════════


class PaymentOpsOrchestrator:
    """Central coordinator for the payment-ops agent pipeline.

    Parameters
    ----------
    session : Session
        SQLAlchemy session.
    now : datetime, optional
        Override current time (testing).
    """

    def __init__(self, session: Session, *, now: Optional[datetime] = None) -> None:
        self.session = session
        _raw = now or datetime.now(timezone.utc)
        # Normalise to naive UTC so time_utils comparisons work
        self._now = _raw.replace(tzinfo=None) if _raw.tzinfo else _raw

    # ── Public API ────────────────────────────────────────────────────

    def run_agent_cycle(self, merchant_id: str | uuid.UUID) -> DashboardUpdate:
        """Execute the full agent cycle for one merchant.

        Phases: Ingest → Process → Aggregate → Notify → Measure → Return.
        """
        logger.info("Starting agent cycle for merchant %s at %s", merchant_id, self._now)

        merchant = self.session.get(Merchant, merchant_id)
        if merchant is None:
            logger.error("Merchant %s not found — aborting cycle.", merchant_id)
            return DashboardUpdate(
                merchant_id=str(merchant_id),
                cycle_at=self._now,
                summary={"error": "merchant_not_found"},
            )

        # 1. INGESTION
        settlements = self._fetch_recent(Settlement, merchant_id)
        refunds = self._fetch_recent(Refund, merchant_id)
        disputes = self._fetch_recent(Dispute, merchant_id)
        logger.info(
            "Ingested: %d settlements, %d refunds, %d disputes",
            len(settlements), len(refunds), len(disputes),
        )

        # 2. PROCESSING
        settlement_result = self._process_settlements(settlements)
        refund_result = self._process_refunds(refunds)
        dispute_result = self._process_disputes(disputes)

        # Save all to DB
        all_anomalies = (
            settlement_result.anomalies
            + refund_result.anomalies
            + dispute_result.anomalies
        )
        all_diagnoses = (
            settlement_result.diagnoses
            + refund_result.diagnoses
            + dispute_result.diagnoses
        )
        all_recommendations = (
            settlement_result.recommendations
            + refund_result.recommendations
            + dispute_result.recommendations
        )

        self._save_batch(all_anomalies, all_diagnoses, all_recommendations)
        self.session.commit()

        # 3. AGGREGATION
        all_merchant_anomalies = self._fetch_all_anomalies(merchant_id)
        all_merchant_recs = self._fetch_all_recommendations(merchant_id)
        dashboard = self._build_dashboard(
            merchant, all_merchant_anomalies, all_merchant_recs,
        )

        # 4. NOTIFICATION
        notified = self._send_notifications(merchant, dashboard)

        # 5. MEASUREMENT
        self._record_metrics(merchant_id, all_anomalies, notified)

        # 6. RETURN
        logger.info(
            "Cycle complete for merchant %s: %d critical, %d warning, %d info",
            merchant_id,
            len(dashboard.critical_anomalies),
            len(dashboard.warning_anomalies),
            len(dashboard.info_anomalies),
        )
        return dashboard

    # ── 1. Ingestion ──────────────────────────────────────────────────

    def _fetch_recent(
        self, model_class, merchant_id, hours: int = CYCLE_LOOKBACK_HOURS
    ) -> list:
        """Fetch records created in the last *hours* for a merchant."""
        cutoff = self._now - timedelta(hours=hours)
        # Dispute uses 'filed_at' instead of 'created_at'
        time_col = getattr(model_class, 'created_at', None) or getattr(model_class, 'filed_at', None)
        return (
            self.session.query(model_class)
            .filter(
                model_class.merchant_id == merchant_id,
                time_col >= cutoff,
            )
            .all()
        )

    # ── 2. Processing ─────────────────────────────────────────────────

    def _process_settlements(self, settlements: List[Settlement]) -> CycleResult:
        """Run the settlement agent pipeline for each settlement."""
        result = CycleResult()
        detector = SettlementAnomalyDetector(self.session, now=self._now)
        classifier = SettlementRootCauseClassifier(self.session, now=self._now)
        recommender = SettlementActionRecommender(self.session, now=self._now)

        for settlement in settlements:
            anomalies = detector.detect_anomalies(settlement)
            for anomaly in anomalies:
                diagnosis = classifier.classify_root_cause(anomaly, settlement)
                rec = recommender.recommend_action(anomaly, diagnosis)
                result.anomalies.append(anomaly)
                result.diagnoses.append(diagnosis)
                result.recommendations.append(rec)

        logger.info("Settlement processing: %d anomalies from %d settlements",
                     len(result.anomalies), len(settlements))
        return result

    def _process_refunds(self, refunds: List[Refund]) -> CycleResult:
        """Run the refund agent pipeline for each refund."""
        result = CycleResult()
        detector = RefundAnomalyDetector(self.session, now=self._now)
        classifier = RefundRootCauseClassifier(self.session, now=self._now)
        recommender = RefundActionRecommender(self.session, now=self._now)

        for refund in refunds:
            anomalies = detector.detect_anomalies(refund)
            for anomaly in anomalies:
                diagnosis = classifier.classify_root_cause(anomaly, refund)
                rec = recommender.recommend_action(anomaly, diagnosis, refund)
                result.anomalies.append(anomaly)
                result.diagnoses.append(diagnosis)
                result.recommendations.append(rec)

        logger.info("Refund processing: %d anomalies from %d refunds",
                     len(result.anomalies), len(refunds))
        return result

    def _process_disputes(self, disputes: List[Dispute]) -> CycleResult:
        """Run the dispute agent pipeline for each dispute."""
        result = CycleResult()
        mapper = EvidenceRequirementMapper(self.session)
        assembler = EvidenceAssembler(self.session, now=self._now)
        predictor = DisputeWinPredictor(self.session)

        for dispute in disputes:
            reqs = mapper.get_requirements(dispute)
            packet = assembler.assemble_evidence(dispute, reqs)
            win_prob = predictor.predict_win_probability(dispute, packet)

            # If evidence incomplete, create an anomaly
            if packet.completeness_status != "complete":
                anomaly = Anomaly(
                    id=uuid.uuid4(),
                    merchant_id=dispute.merchant_id,
                    anomaly_type=AnomalyType.DISPUTE_EVIDENCE_INCOMPLETE,
                    related_dispute_id=dispute.id,
                    detected_at=self._now,
                    root_cause="evidence_incomplete",
                    root_cause_confidence=Decimal("0.90"),
                    status=AnomalyStatus.OPEN,
                    severity=(
                        SeverityLevel.CRITICAL
                        if packet.completeness_score < 50
                        else SeverityLevel.WARNING
                    ),
                    recommended_action=(
                        f"Evidence {packet.completeness_status} "
                        f"({packet.completeness_score:.0f}%) — "
                        f"win probability: {win_prob:.0%}"
                    ),
                )
                result.anomalies.append(anomaly)

                # Build a simple diagnosis for the dispute
                diagnosis = Diagnosis(
                    id=uuid.uuid4(),
                    anomaly_id=anomaly.id,
                    root_cause_category="evidence_incomplete",
                    root_cause_subcategory=packet.completeness_status,
                    explanation_plain_english=(
                        f"Evidence completeness: {packet.completeness_score:.0f}%. "
                        f"Missing: {', '.join(g.type for g in packet.gaps[:3])}. "
                        f"Predicted win rate: {win_prob:.0%}."
                    ),
                    confidence=Decimal(str(min(win_prob, 0.99))),
                    evidence={
                        "completeness_score": packet.completeness_score,
                        "gaps": [g.type for g in packet.gaps],
                        "win_probability": win_prob,
                    },
                    causal_chain=[],
                    created_at=self._now,
                )
                result.diagnoses.append(diagnosis)

                # Simple recommendation
                rec = Recommendation(
                    id=uuid.uuid4(),
                    anomaly_id=anomaly.id,
                    recommendation_text=(
                        f"Upload missing evidence for dispute {dispute.id}: "
                        f"{', '.join(g.type for g in packet.gaps[:3])}"
                    ),
                    recommended_action="resubmit_evidence",
                    urgency=(
                        UrgencyLevel.CRITICAL
                        if packet.completeness_score < 50
                        else UrgencyLevel.HIGH
                    ),
                    timeline="immediate",
                    expected_resolution_time_hours=24,
                    success_probability=Decimal(str(min(Decimal(str(win_prob)) + Decimal("0.10"), 0.99))),
                    merchant_followed=False,
                    outcome_if_followed=None,
                )
                result.recommendations.append(rec)

            # Check for deadline approaching (within 48h)
            if dispute.evidence_deadline:
                deadline = dispute.evidence_deadline.replace(tzinfo=None) if dispute.evidence_deadline.tzinfo else dispute.evidence_deadline
                if deadline <= self._now + timedelta(hours=48):
                    deadline_anomaly = Anomaly(
                        id=uuid.uuid4(),
                        merchant_id=dispute.merchant_id,
                        anomaly_type=AnomalyType.DISPUTE_DEADLINE_APPROACHING,
                        related_dispute_id=dispute.id,
                        detected_at=self._now,
                        root_cause="deadline_approaching",
                        root_cause_confidence=Decimal("0.95"),
                        status=AnomalyStatus.OPEN,
                        severity=SeverityLevel.CRITICAL,
                        recommended_action=(
                            f"Evidence deadline: {dispute.evidence_deadline}. "
                            f"Current completeness: {packet.completeness_score:.0f}%"
                        ),
                    )
                    result.anomalies.append(deadline_anomaly)

        logger.info("Dispute processing: %d anomalies from %d disputes",
                     len(result.anomalies), len(disputes))
        return result

    # ── Persistence ───────────────────────────────────────────────────

    def _save_batch(
        self,
        anomalies: List[Anomaly],
        diagnoses: List[Diagnosis],
        recommendations: List[Recommendation],
    ) -> None:
        """Persist anomalies, diagnoses, and recommendations to the database."""
        for anomaly in anomalies:
            self.session.add(anomaly)
        for diagnosis in diagnoses:
            self.session.add(diagnosis)
        for rec in recommendations:
            self.session.add(rec)

        logger.info(
            "Saved: %d anomalies, %d diagnoses, %d recommendations",
            len(anomalies), len(diagnoses), len(recommendations),
        )

    # ── 3. Aggregation ────────────────────────────────────────────────

    def _fetch_all_anomalies(self, merchant_id) -> List[Anomaly]:
        """Fetch all open anomalies for a merchant."""
        return (
            self.session.query(Anomaly)
            .filter(
                Anomaly.merchant_id == merchant_id,
                Anomaly.status == AnomalyStatus.OPEN,
            )
            .all()
        )

    def _fetch_all_recommendations(self, merchant_id) -> List[Recommendation]:
        """Fetch all recommendations linked to the merchant's anomalies."""
        anomaly_ids = [
            a.id for a in self._fetch_all_anomalies(merchant_id)
        ]
        if not anomaly_ids:
            return []
        return (
            self.session.query(Recommendation)
            .filter(Recommendation.anomaly_id.in_(anomaly_ids))
            .all()
        )

    def _build_dashboard(
        self,
        merchant: Merchant,
        anomalies: List[Anomaly],
        recommendations: List[Recommendation],
    ) -> DashboardUpdate:
        """Build the dashboard view from aggregated data."""
        critical = []
        warning = []
        info = []

        for a in anomalies:
            entry = {
                "id": str(a.id),
                "type": a.anomaly_type.value,
                "severity": a.severity.value,
                "root_cause": a.root_cause,
                "recommended_action": a.recommended_action,
                "detected_at": str(a.detected_at),
                "related_settlement_id": a.related_settlement_id,
                "related_refund_id": a.related_refund_id,
                "related_dispute_id": a.related_dispute_id,
            }
            if a.severity == SeverityLevel.CRITICAL:
                critical.append(entry)
            elif a.severity == SeverityLevel.WARNING:
                warning.append(entry)
            else:
                info.append(entry)

        # Top recommendations by urgency
        urgency_order = {
            UrgencyLevel.CRITICAL: 0,
            UrgencyLevel.HIGH: 1,
            UrgencyLevel.MEDIUM: 2,
            UrgencyLevel.LOW: 3,
        }
        sorted_recs = sorted(
            recommendations,
            key=lambda r: urgency_order.get(r.urgency, 99),
        )
        top_recs = [
            {
                "anomaly_id": str(r.anomaly_id),
                "action": r.recommended_action.value if hasattr(r.recommended_action, 'value') else str(r.recommended_action),
                "urgency": r.urgency.value,
                "timeline": r.timeline,
                "success_probability": float(r.success_probability) if r.success_probability else 0.0,
                "text": r.recommendation_text,
            }
            for r in sorted_recs[:10]
        ]

        # Next deadline
        next_deadline = self._find_next_deadline(anomalies)

        # Impact
        impact = self._calculate_impact(merchant.id)

        # Summary
        summary = {
            "total_anomalies": len(anomalies),
            "critical_count": len(critical),
            "warning_count": len(warning),
            "info_count": len(info),
            "total_recommendations": len(recommendations),
            "unfollowed_recommendations": sum(
                1 for r in recommendations if not r.merchant_followed
            ),
        }

        return DashboardUpdate(
            merchant_id=str(merchant.id),
            cycle_at=self._now,
            critical_anomalies=critical,
            warning_anomalies=warning,
            info_anomalies=info,
            top_recommendations=top_recs,
            impact=impact,
            next_deadline=next_deadline,
            summary=summary,
        )

    def _find_next_deadline(self, anomalies: List[Anomaly]) -> Optional[datetime]:
        """Find the earliest evidence deadline among disputes."""
        deadlines = []
        for a in anomalies:
            if a.related_dispute_id:
                dispute = self.session.get(Dispute, a.related_dispute_id)
                if dispute and dispute.evidence_deadline:
                    deadlines.append(dispute.evidence_deadline)
        return min(deadlines) if deadlines else None

    # ── 4. Notifications ──────────────────────────────────────────────

    def _send_notifications(
        self, merchant: Merchant, dashboard: DashboardUpdate
    ) -> int:
        """Filter and send notifications based on merchant threshold.

        Returns the number of notifications sent.
        """
        threshold = merchant.alert_threshold_severity or SeverityLevel.WARNING
        channels = merchant.notification_channels or ["email"]
        sent = 0

        threshold_rank = SEVERITY_ORDER.get(threshold, 2)

        for entry in dashboard.critical_anomalies + dashboard.warning_anomalies + dashboard.info_anomalies:
            sev = entry.get("severity", "info")
            sev_enum = SeverityLevel(sev) if sev in ("info", "warning", "critical") else SeverityLevel.INFO
            sev_rank = SEVERITY_ORDER.get(sev_enum, 2)

            # Only notify if anomaly severity meets or exceeds threshold
            if sev_rank <= threshold_rank:
                message = self._format_notification(entry, merchant)
                for channel in channels:
                    success = self._send_to_channel(channel, message, entry)
                    if success:
                        sent += 1
                        logger.info("Notification sent via %s: %s", channel, entry["type"])

        logger.info("Sent %d notifications for merchant %s", sent, merchant.id)
        return sent

    @staticmethod
    def _format_notification(entry: Dict[str, Any], merchant: Merchant) -> str:
        """Format a human-readable notification message."""
        severity = entry.get("severity", "info").upper()
        anomaly_type = entry.get("type", "unknown")
        root_cause = entry.get("root_cause", "unknown")
        action = entry.get("recommended_action", "Check dashboard")

        return (
            f"[{severity}] {merchant.business_name}: "
            f"{anomaly_type.replace('_', ' ').title()} — "
            f"{root_cause.replace('_', ' ').title()}. "
            f"Action: {action}"
        )

    @staticmethod
    def _send_to_channel(channel: str, message: str, entry: Dict[str, Any]) -> bool:
        """Route notification to a channel.  Returns True on success.

        In production this would call email/SMS/webhook APIs.
        """
        logger.info(
            "Would send via %s: %s (dispute=%s)",
            channel, message[:80], entry.get("related_dispute_id"),
        )
        # Stub: always succeeds in dev
        return True

    # ── 5. Measurement ────────────────────────────────────────────────

    def _record_metrics(
        self,
        merchant_id,
        anomalies: List[Anomaly],
        notifications_sent: int,
    ) -> None:
        """Record evaluation metrics for this cycle."""
        metrics = [
            ("anomalies_detected", len(anomalies), "count"),
            ("critical_anomalies", sum(1 for a in anomalies if a.severity == SeverityLevel.CRITICAL), "count"),
            ("warning_anomalies", sum(1 for a in anomalies if a.severity == SeverityLevel.WARNING), "count"),
            ("notifications_sent", notifications_sent, "count"),
        ]

        for name, value, unit in metrics:
            m = EvaluationMetric(
                id=uuid.uuid4(),
                merchant_id=merchant_id,
                metric_name=name,
                metric_value=Decimal(str(value)),
                metric_unit=unit,
                dimensions={"cycle_at": str(self._now)},
                recorded_at=self._now,
            )
            self.session.add(m)

        logger.info("Recorded %d metrics for merchant %s", len(metrics), merchant_id)

    # ── 6. Impact ─────────────────────────────────────────────────────

    def _calculate_impact(self, merchant_id) -> ImpactSummary:
        """Calculate impact summary from resolved anomalies."""
        resolved = (
            self.session.query(Anomaly)
            .filter(
                Anomaly.merchant_id == merchant_id,
                Anomaly.status == AnomalyStatus.RESOLVED,
            )
            .all()
        )

        total = (
            self.session.query(func.count(Anomaly.id))
            .filter(Anomaly.merchant_id == merchant_id)
            .scalar()
        ) or 0

        # Estimate time saved: 2h per resolved settlement delay
        settlement_delays = sum(
            1 for a in resolved
            if a.anomaly_type in (
                AnomalyType.SETTLEMENT_DELAYED,
                AnomalyType.SETTLEMENT_FAILED,
            )
        )

        # Estimate revenue recovered: average settlement amount for resolved
        chargebacks_won = sum(
            1 for a in resolved
            if a.anomaly_type in (
                AnomalyType.DISPUTE_EVIDENCE_INCOMPLETE,
                AnomalyType.DISPUTE_DEADLINE_APPROACHING,
            )
        )

        return ImpactSummary(
            time_saved_hours=settlement_delays * 2.0,
            revenue_recovered_inr=0.0,  # requires settlement amount data
            chargebacks_won=chargebacks_won,
            settlement_delays_prevented=settlement_delays,
            anomalies_detected=total,
            anomalies_resolved=len(resolved),
        )
