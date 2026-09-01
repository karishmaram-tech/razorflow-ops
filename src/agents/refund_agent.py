"""Refund Operations Agent — detect, classify, and recommend for refund anomalies.

Pipeline:  RefundAnomalyDetector  →  RefundRootCauseClassifier  →  RefundActionRecommender

Usage::

    from src.agents.refund_agent import (
        RefundAnomalyDetector,
        RefundRootCauseClassifier,
        RefundActionRecommender,
    )

    detector = RefundAnomalyDetector(session)
    anomalies = detector.detect_anomalies(refund)
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.data.models import (
    Anomaly,
    AnomalyStatus,
    AnomalyType,
    Diagnosis,
    Dispute,
    DisputeStatus,
    RecommendedAction,
    Recommendation,
    Refund,
    RefundStatus,
    SeverityLevel,
    UrgencyLevel,
)
from src.utils.bank_codes import get_root_cause_from_code
from src.utils.time_utils import _add_working_days, _next_working_day

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

REFUND_T_PLUS_DAYS = 3          # T+3 working days expected completion
STUCK_WARNING_HOURS = 24        # <24h stuck → WARNING
STUCK_CRITICAL_HOURS = 48       # >48h stuck → CRITICAL
DUP_WINDOW_HOURS = 24           # same txn refunds within 24h = duplicate suspect
PROCESSING_DELAY_DAYS = 2       # >2 working days in "processing" → delay anomaly


# ══════════════════════════════════════════════════════════════════════════════
# 1. Anomaly Detector
# ══════════════════════════════════════════════════════════════════════════════


class RefundAnomalyDetector:
    """Analyse a single Refund and return detected anomalies.

    Parameters
    ----------
    session : Session
        SQLAlchemy session for lookups.
    now : datetime, optional
        Override current time (testing).
    """

    def __init__(self, session: Session, *, now: Optional[datetime] = None) -> None:
        self.session = session
        _raw = now or datetime.now(timezone.utc)
        self._now = _raw.replace(tzinfo=None) if _raw.tzinfo else _raw

    # ── Public API ────────────────────────────────────────────────────

    def detect_anomalies(self, refund: Refund) -> List[Anomaly]:
        """Run all refund checks and return unsaved Anomaly objects."""
        logger.info(
            "Running refund anomaly detection for %s (merchant=%s, status=%s, amount=%s)",
            refund.id, refund.merchant_id, refund.status, refund.amount,
        )
        anomalies: List[Anomaly] = []

        checks = [
            self._detect_stuck,
            self._detect_reversed,
            self._detect_mismatch,
            self._detect_duplicate,
            self._detect_processing_delay,
        ]
        for check in checks:
            result = check(refund)
            if result is not None:
                anomalies.append(result)

        logger.info("Refund %s: %d anomalies detected.", refund.id, len(anomalies))
        return anomalies

    # ── 1. Stuck refund ───────────────────────────────────────────────

    def _detect_stuck(self, refund: Refund) -> Optional[Anomaly]:
        """Refund past T+3 working days and not yet succeeded."""
        if refund.status in (RefundStatus.SUCCESS, RefundStatus.FAILED, RefundStatus.REVERSED):
            return None

        expected = self._calculate_expected_completion(refund)
        if expected is None:
            return None

        if self._now <= expected:
            return None

        hours_stuck = (self._now - expected).total_seconds() / 3600

        if hours_stuck > STUCK_CRITICAL_HOURS:
            severity = SeverityLevel.CRITICAL
        elif hours_stuck > STUCK_WARNING_HOURS:
            severity = SeverityLevel.WARNING
        else:
            severity = SeverityLevel.INFO

        logger.warning(
            "Refund %s stuck for %.1fh past expected completion (severity=%s)",
            refund.id, hours_stuck, severity.value,
        )

        return Anomaly(
            id=uuid.uuid4(),
            merchant_id=refund.merchant_id,
            anomaly_type=AnomalyType.REFUND_STUCK,
            related_refund_id=refund.id,
            related_dispute_id=refund.related_dispute_id,
            detected_at=self._now,
            root_cause="refund_stuck",
            root_cause_confidence=Decimal("0.80"),
            status=AnomalyStatus.OPEN,
            severity=severity,
            recommended_action=f"Refund stuck for {hours_stuck:.0f} hours past expected completion",
        )

    def _calculate_expected_completion(self, refund: Refund) -> Optional[datetime]:
        """Compute expected completion = created_at + T+3 working days."""
        if refund.created_at is None:
            return None
        start = _next_working_day(refund.created_at.date())
        arrival = _add_working_days(start, REFUND_T_PLUS_DAYS)
        return datetime.combine(arrival, datetime.min.time().replace(hour=23, minute=59, second=59))

    # ── 2. Reversed refund ────────────────────────────────────────────

    def _detect_reversed(self, refund: Refund) -> Optional[Anomaly]:
        """Refund that was reversed by the bank."""
        if refund.status != RefundStatus.REVERSED:
            return None

        logger.error(
            "Refund %s was REVERSED (bank_response_code=%s)",
            refund.id, refund.bank_response_code,
        )

        return Anomaly(
            id=uuid.uuid4(),
            merchant_id=refund.merchant_id,
            anomaly_type=AnomalyType.REFUND_REVERSED,
            related_refund_id=refund.id,
            related_dispute_id=refund.related_dispute_id,
            detected_at=self._now,
            root_cause="refund_reversed",
            root_cause_confidence=Decimal("0.90"),
            status=AnomalyStatus.OPEN,
            severity=SeverityLevel.CRITICAL,
            recommended_action="Bank reversed the refund — investigate immediately",
        )

    # ── 3. Mismatch (dispute filed but refund not received) ───────────

    def _detect_mismatch(self, refund: Refund) -> Optional[Anomaly]:
        """Refund linked to a dispute that's been filed but customer claims
        not receiving the refund."""
        if refund.related_dispute_id is None:
            return None

        # Check if the related dispute is active
        dispute = self.session.get(Dispute, refund.related_dispute_id)
        if dispute is None:
            return None

        if dispute.current_status not in (
            DisputeStatus.EVIDENCE_PENDING,
            DisputeStatus.UNDER_REVIEW,
        ):
            return None

        # If refund is still pending/processing while dispute is active → mismatch
        if refund.status in (RefundStatus.INITIATED, RefundStatus.PENDING, RefundStatus.PROCESSING):
            logger.warning(
                "Refund %s: mismatch — dispute %s is active but refund not completed (status=%s)",
                refund.id, dispute.id, refund.status.value,
            )
            return Anomaly(
                id=uuid.uuid4(),
                merchant_id=refund.merchant_id,
                anomaly_type=AnomalyType.REFUND_MISMATCH,
                related_refund_id=refund.id,
                related_dispute_id=dispute.id,
                detected_at=self._now,
                root_cause="refund_not_received_by_customer",
                root_cause_confidence=Decimal("0.80"),
                status=AnomalyStatus.OPEN,
                severity=SeverityLevel.CRITICAL,
                recommended_action="Customer disputes but refund not yet received — resolve urgently",
            )

        return None

    # ── 4. Duplicate refund ───────────────────────────────────────────

    def _detect_duplicate(self, refund: Refund) -> Optional[Anomaly]:
        """Multiple refunds for the same transaction within a short window."""
        window_start = refund.created_at - timedelta(hours=DUP_WINDOW_HOURS)
        window_end = refund.created_at + timedelta(hours=DUP_WINDOW_HOURS)

        stmt_dup = select(
            func.count(Refund.id)
        ).select_from(Refund).filter(
            Refund.transaction_id == refund.transaction_id,
            Refund.id != refund.id,
            Refund.created_at >= window_start,
            Refund.created_at <= window_end,
        )
        count = self.session.execute(stmt_dup).scalar() or 0

        if count < 1:
            return None

        logger.warning(
            "Refund %s: %d other refunds for same transaction %s within %dh window",
            refund.id, count, refund.transaction_id, DUP_WINDOW_HOURS,
        )

        return Anomaly(
            id=uuid.uuid4(),
            merchant_id=refund.merchant_id,
            anomaly_type=AnomalyType.REFUND_DUPLICATE,
            related_refund_id=refund.id,
            detected_at=self._now,
            root_cause="duplicate_refund_initiated",
            root_cause_confidence=Decimal("0.95"),
            status=AnomalyStatus.OPEN,
            severity=SeverityLevel.WARNING,
            recommended_action=f"{count + 1} refunds detected for the same transaction — verify and reverse if needed",
        )

    # ── 5. Processing delay ───────────────────────────────────────────

    def _detect_processing_delay(self, refund: Refund) -> Optional[Anomaly]:
        """Refund stuck in 'processing' for >2 working days."""
        if refund.status != RefundStatus.PROCESSING:
            return None

        expected_done = self._calculate_expected_completion(refund)
        if expected_done is None:
            return None

        # If we're past T+3 it's already caught by _detect_stuck;
        # this catches the window between T+2 and T+3.
        delay_threshold = expected_done - timedelta(days=1)
        if self._now < delay_threshold:
            return None

        logger.warning(
            "Refund %s: processing delay detected (status=processing, now=%s)",
            refund.id, self._now,
        )

        return Anomaly(
            id=uuid.uuid4(),
            merchant_id=refund.merchant_id,
            anomaly_type=AnomalyType.REFUND_PROCESSING_DELAY,
            related_refund_id=refund.id,
            detected_at=self._now,
            root_cause="bank_processing_delay",
            root_cause_confidence=Decimal("0.75"),
            status=AnomalyStatus.OPEN,
            severity=SeverityLevel.WARNING,
            recommended_action="Refund processing longer than expected — monitor closely",
        )


# ══════════════════════════════════════════════════════════════════════════════
# 2. Root-Cause Classifier
# ══════════════════════════════════════════════════════════════════════════════


# Reversal reason codes (common bank-side reasons)
REVERSAL_REASONS: dict[str, dict] = {
    "customer_account_closed": {
        "description": "Customer's bank account has been closed",
        "cause": "The beneficiary account no longer exists",
        "confidence": Decimal("0.85"),
    },
    "customer_account_flagged": {
        "description": "Customer's account flagged for suspicious activity",
        "cause": "Bank's fraud system blocked the credit",
        "confidence": Decimal("0.75"),
    },
    "duplicate_reversal": {
        "description": "Bank detected duplicate credit and reversed",
        "cause": "Duplicate refund detected by bank reconciliation",
        "confidence": Decimal("0.80"),
    },
    "bank_error": {
        "description": "Bank processing error caused reversal",
        "cause": "Technical issue at the receiving bank",
        "confidence": Decimal("0.65"),
    },
}


class RefundRootCauseClassifier:
    """Classify the root cause of a refund anomaly into a Diagnosis.

    Parameters
    ----------
    session : Session
        SQLAlchemy session.
    now : datetime, optional
        Override current time.
    """

    def __init__(self, session: Session, *, now: Optional[datetime] = None) -> None:
        self.session = session
        _raw = now or datetime.now(timezone.utc)
        self._now = _raw.replace(tzinfo=None) if _raw.tzinfo else _raw

    # ── Public API ────────────────────────────────────────────────────

    def classify_root_cause(self, anomaly: Anomaly, refund: Refund) -> Diagnosis:
        """Produce a Diagnosis for the given anomaly + refund pair."""
        logger.info(
            "Classifying refund root cause for anomaly %s (refund %s, type=%s)",
            anomaly.id, refund.id, anomaly.anomaly_type.value,
        )

        atype = anomaly.anomaly_type

        if atype == AnomalyType.REFUND_STUCK:
            return self._classify_stuck(anomaly, refund)
        if atype == AnomalyType.REFUND_REVERSED:
            return self._classify_reversed(anomaly, refund)
        if atype == AnomalyType.REFUND_MISMATCH:
            return self._classify_mismatch(anomaly, refund)
        if atype == AnomalyType.REFUND_DUPLICATE:
            return self._classify_duplicate(anomaly, refund)
        if atype == AnomalyType.REFUND_PROCESSING_DELAY:
            return self._classify_processing_delay(anomaly, refund)

        # Fallback
        return self._make_diagnosis(
            anomaly, "unknown_error", "Unclassified refund anomaly",
            Decimal("0.40"), ["No specific classifier matched"],
        )

    # ── Per-type classifiers ──────────────────────────────────────────

    def _classify_stuck(self, anomaly: Anomaly, refund: Refund) -> Diagnosis:
        code = refund.bank_response_code
        if code:
            info = get_root_cause_from_code(code)
            root_cause = info.get("category", "bank_processing_delay")
            base_confidence = Decimal("0.85") if not info.get("retryable", True) else Decimal("0.75")
        else:
            root_cause = "bank_processing_delay"
            base_confidence = Decimal("0.65")

        evidence = [
            f"Refund {refund.id}: status={refund.status.value}, amount=₹{refund.amount}",
            f"Created: {refund.created_at}, expected completion: T+3 working days",
            f"Bank response code: {code or 'None'}",
        ]
        if refund.bank_response_message:
            evidence.append(f"Bank message: {refund.bank_response_message}")

        return self._make_diagnosis(anomaly, root_cause, root_cause, base_confidence, evidence)

    def _classify_reversed(self, anomaly: Anomaly, refund: Refund) -> Diagnosis:
        # Try to map the bank response code to a reversal reason
        code = refund.bank_response_code
        if code and code in REVERSAL_REASONS:
            reason_info = REVERSAL_REASONS[code]
            root_cause = code
            confidence = reason_info["confidence"]
        else:
            # Default: look up in bank_codes
            if code:
                info = get_root_cause_from_code(code)
                root_cause = info.get("category", "bank_error")
                confidence = Decimal("0.70")
            else:
                root_cause = "bank_error"
                confidence = Decimal("0.70")

        evidence = [
            f"Refund {refund.id}: status=REVERSED, amount=₹{refund.amount}",
            f"Bank response code: {code or 'None'}",
            f"Reversal detected at: {self._now}",
        ]

        return self._make_diagnosis(anomaly, root_cause, root_cause, confidence, evidence)

    def _classify_mismatch(self, anomaly: Anomaly, refund: Refund) -> Diagnosis:
        evidence = [
            f"Refund {refund.id}: status={refund.status.value}, amount=₹{refund.amount}",
            f"Related dispute: {refund.related_dispute_id}",
            "Customer claims refund not received but dispute is active",
        ]

        return self._make_diagnosis(
            anomaly, "refund_not_received_by_customer",
            "Refund Not Received", Decimal("0.80"), evidence,
        )

    def _classify_duplicate(self, anomaly: Anomaly, refund: Refund) -> Diagnosis:
        # Count refunds for same transaction
        stmt_dup2 = select(
            func.count(Refund.id)
        ).select_from(Refund).filter(
            Refund.transaction_id == refund.transaction_id,
        )
        count = self.session.execute(stmt_dup2).scalar() or 0

        evidence = [
            f"Refund {refund.id}: amount=₹{refund.amount}, transaction={refund.transaction_id}",
            f"Total refunds for this transaction: {count}",
            "Multiple refunds detected within short window",
        ]

        return self._make_diagnosis(
            anomaly, "duplicate_refund_initiated",
            "Duplicate Refund", Decimal("0.95"), evidence,
        )

    def _classify_processing_delay(self, anomaly: Anomaly, refund: Refund) -> Diagnosis:
        evidence = [
            f"Refund {refund.id}: status=PROCESSING, amount=₹{refund.amount}",
            f"Created: {refund.created_at}, now: {self._now}",
            "No failure indicators — likely bank processing queue",
        ]

        return self._make_diagnosis(
            anomaly, "bank_processing_delay",
            "Bank Processing Delay", Decimal("0.75"), evidence,
        )

    # ── Factory ───────────────────────────────────────────────────────

    @staticmethod
    def _make_diagnosis(
        anomaly: Anomaly,
        root_cause: str,
        subcategory: str,
        confidence: Decimal,
        evidence: List[str],
    ) -> Diagnosis:
        causal_chain = [
            {"step": 1, "role": "trigger", "event": f"Refund anomaly detected: {anomaly.anomaly_type.value}"},
            {"step": 2, "role": "analysis", "event": f"Root cause classified as: {root_cause}"},
            {"step": 3, "role": "outcome", "event": f"Confidence: {confidence}"},
        ]

        return Diagnosis(
            id=uuid.uuid4(),
            anomaly_id=anomaly.id,
            root_cause_category=root_cause,
            root_cause_subcategory=subcategory,
            explanation_plain_english=f"Root cause: {root_cause}. Confidence: {confidence}.",
            confidence=confidence,
            evidence={"facts": evidence},
            causal_chain=causal_chain,
            created_at=datetime.now(timezone.utc),
        )


# ══════════════════════════════════════════════════════════════════════════════
# 3. Action Recommender
# ══════════════════════════════════════════════════════════════════════════════


# ── Decision tree: root_cause → (action, timeline, probability, urgency) ──

REFUND_ACTION_TREE: dict[str, tuple[RecommendedAction, str, Decimal, UrgencyLevel]] = {
    "bank_processing_delay": (
        RecommendedAction.WAIT,
        "72_hours",
        Decimal("0.85"),
        UrgencyLevel.LOW,
    ),
    "customer_account_closed": (
        RecommendedAction.PROCESS_REFUND,
        "immediate",
        Decimal("0.70"),
        UrgencyLevel.HIGH,
    ),
    "customer_account_flagged": (
        RecommendedAction.CONTACT_RAZORPAY,
        "immediate",
        Decimal("0.50"),
        UrgencyLevel.CRITICAL,
    ),
    "duplicate_reversal": (
        RecommendedAction.CONTACT_RAZORPAY,
        "immediate",
        Decimal("0.60"),
        UrgencyLevel.HIGH,
    ),
    "bank_error": (
        RecommendedAction.CONTACT_RAZORPAY,
        "immediate",
        Decimal("0.55"),
        UrgencyLevel.HIGH,
    ),
    "refund_not_received_by_customer": (
        RecommendedAction.PROCESS_REFUND,
        "immediate",
        Decimal("0.60"),
        UrgencyLevel.CRITICAL,
    ),
    "duplicate_refund_initiated": (
        RecommendedAction.CONTACT_RAZORPAY,
        "immediate",
        Decimal("0.50"),
        UrgencyLevel.HIGH,
    ),
    "refund_reversed": (
        RecommendedAction.ESCALATE,
        "immediate",
        Decimal("0.40"),
        UrgencyLevel.CRITICAL,
    ),
}

# ── Anomaly-type overrides ──

REFUND_TYPE_TREE: dict[str, tuple[RecommendedAction, str, Decimal, UrgencyLevel]] = {
    AnomalyType.REFUND_STUCK.value: (
        RecommendedAction.WAIT,
        "72_hours",
        Decimal("0.85"),
        UrgencyLevel.LOW,
    ),
    AnomalyType.REFUND_REVERSED.value: (
        RecommendedAction.ESCALATE,
        "immediate",
        Decimal("0.40"),
        UrgencyLevel.CRITICAL,
    ),
    AnomalyType.REFUND_MISMATCH.value: (
        RecommendedAction.PROCESS_REFUND,
        "immediate",
        Decimal("0.60"),
        UrgencyLevel.CRITICAL,
    ),
    AnomalyType.REFUND_DUPLICATE.value: (
        RecommendedAction.CONTACT_RAZORPAY,
        "immediate",
        Decimal("0.50"),
        UrgencyLevel.HIGH,
    ),
    AnomalyType.REFUND_PROCESSING_DELAY.value: (
        RecommendedAction.WAIT,
        "48_hours",
        Decimal("0.80"),
        UrgencyLevel.MEDIUM,
    ),
}

REFUND_TIMELINE_HOURS: dict[str, int] = {
    "immediate": 2,
    "24_hours": 24,
    "48_hours": 48,
    "72_hours": 72,
    "1_week": 168,
}

# ── Merchant-friendly text templates ──

REFUND_MERCHANT_TEXT: dict[str, str] = {
    "bank_processing_delay": (
        "Your refund is still being processed by the bank. This is normal — "
        "banks typically complete refunds within 3 working days. No action needed "
        "right now."
    ),
    "customer_account_closed": (
        "The customer's bank account appears to be closed. Please ask the customer "
        "for an alternative bank account or updated card details so we can resend the refund."
    ),
    "customer_account_flagged": (
        "The customer's bank account has been flagged. Please contact Razorpay support "
        "with the refund details to resolve this."
    ),
    "duplicate_reversal": (
        "The bank detected what it thinks is a duplicate credit and reversed the refund. "
        "Contact Razorpay support to investigate and reinitiate if needed."
    ),
    "bank_error": (
        "The bank encountered a technical error while processing the refund. "
        "Contact Razorpay support to reinitiate the refund."
    ),
    "refund_not_received_by_customer": (
        "The customer says they haven't received the refund, and it's still showing as "
        "processing. Check with the bank first, then resubmit if needed."
    ),
    "duplicate_refund_initiated": (
        "Multiple refunds were found for the same transaction. Please verify which refund "
        "is correct and contact Razorpay to reverse the duplicate."
    ),
    "refund_reversed": (
        "The bank has reversed the refund. This is urgent — please contact Razorpay support "
        "and the customer's bank immediately to understand why."
    ),
}


class RefundActionRecommender:
    """Recommend the next action for a refund anomaly.

    Parameters
    ----------
    session : Session
        SQLAlchemy session.
    now : datetime, optional
        Override current time.
    """

    def __init__(self, session: Session, *, now: Optional[datetime] = None) -> None:
        self.session = session
        _raw = now or datetime.now(timezone.utc)
        self._now = _raw.replace(tzinfo=None) if _raw.tzinfo else _raw

    # ── Public API ────────────────────────────────────────────────────

    def recommend_action(
        self, anomaly: Anomaly, diagnosis: Diagnosis, refund: Refund
    ) -> Recommendation:
        """Produce a Recommendation for the given anomaly + diagnosis + refund."""
        root_cause = diagnosis.root_cause_category or "unknown_error"
        anomaly_type = anomaly.anomaly_type.value if anomaly.anomaly_type else None

        logger.info(
            "Recommending refund action for anomaly %s (root_cause=%s, type=%s)",
            anomaly.id, root_cause, anomaly_type,
        )

        # 1. Resolve from decision tree (anomaly-type override for reversed)
        action, timeline, base_prob, urgency = self._resolve_action(
            root_cause, anomaly_type, refund,
        )

        # 2. Adjust probability with diagnosis confidence
        adjusted_prob = self._adjust_probability(base_prob, diagnosis.confidence)

        # 3. Generate merchant-friendly text
        text = self._generate_text(root_cause, timeline)

        # 4. Timeline hours
        hours = REFUND_TIMELINE_HOURS.get(timeline, 24)

        recommendation = Recommendation(
            id=uuid.uuid4(),
            anomaly_id=anomaly.id,
            recommendation_text=text,
            recommended_action=action,
            urgency=urgency,
            timeline=timeline,
            expected_resolution_time_hours=hours,
            success_probability=adjusted_prob,
            merchant_followed=False,
            outcome_if_followed=None,
        )

        logger.info(
            "Refund recommendation for anomaly %s: action=%s, urgency=%s, prob=%s",
            anomaly.id, action.value, urgency.value, adjusted_prob,
        )
        return recommendation

    # ── Decision tree ─────────────────────────────────────────────────

    def _resolve_action(
        self, root_cause: str, anomaly_type: Optional[str], refund: Refund
    ) -> tuple[RecommendedAction, str, Decimal, UrgencyLevel]:
        """Resolve action from decision tree with refund-specific overrides."""

        # Override: refund_reversed always escalates
        if anomaly_type == AnomalyType.REFUND_REVERSED.value:
            return REFUND_TYPE_TREE[AnomalyType.REFUND_REVERSED.value]

        # Override: if bank_processing_delay AND already >4 days → contact bank
        if root_cause == "bank_processing_delay" and self._is_long_delay(refund):
            return (
                RecommendedAction.CONTACT_BANK,
                "immediate",
                Decimal("0.70"),
                UrgencyLevel.HIGH,
            )

        # Root-cause lookup
        if root_cause in REFUND_ACTION_TREE:
            return REFUND_ACTION_TREE[root_cause]

        # Anomaly-type fallback
        if anomaly_type and anomaly_type in REFUND_TYPE_TREE:
            return REFUND_TYPE_TREE[anomaly_type]

        # Default
        logger.warning("No refund action for root_cause=%s, type=%s", root_cause, anomaly_type)
        return (
            RecommendedAction.CONTACT_RAZORPAY,
            "24_hours",
            Decimal("0.50"),
            UrgencyLevel.MEDIUM,
        )

    def _is_long_delay(self, refund: Refund) -> bool:
        """Check if refund is >4 calendar days old (beyond typical T+3)."""
        if refund.created_at is None:
            return False
        created = refund.created_at.replace(tzinfo=None) if refund.created_at.tzinfo else refund.created_at
        return (self._now - created).days > 4

    # ── Probability ───────────────────────────────────────────────────

    @staticmethod
    def _adjust_probability(base: Decimal, confidence: Optional[Decimal]) -> Decimal:
        if confidence is None:
            return base
        factor = Decimal("0.7") + Decimal("0.3") * confidence
        result = (base * factor).quantize(Decimal("0.01"))
        return min(max(result, Decimal("0.10")), Decimal("0.99"))

    # ── Text ──────────────────────────────────────────────────────────

    @staticmethod
    def _generate_text(root_cause: str, timeline: str) -> str:
        template = REFUND_MERCHANT_TEXT.get(root_cause)
        if template is None:
            return "We're looking into your refund issue. Please contact Razorpay support for help."
        return template
