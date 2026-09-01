"""Settlement Anomaly Detector — identifies operational issues in settlement records.

Detects:
1. Delayed settlements (past T+2 working days)
2. Partial settlements (amount shortfall >5%)
3. Failed settlements
4. Fee mismatches (>10% deviation)
5. Multiple failed attempts (≥2)
6. Reconciliation gaps (transaction sum != settlement amount)

Usage::

    from src.agents.settlement_agent import SettlementAnomalyDetector

    detector = SettlementAnomalyDetector(session)
    anomalies = detector.detect_anomalies(settlement)
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.data.models import (
    Anomaly,
    AnomalyStatus,
    AnomalyType,
    Diagnosis,
    RecommendedAction,
    Recommendation,
    Refund,
    RefundStatus,
    Settlement,
    SettlementAttempt,
    SettlementAttemptStatus,
    SettlementStatus,
    SeverityLevel,
    Transaction,
    UrgencyLevel,
)
from src.utils.bank_codes import get_root_cause_from_code
from src.utils.time_utils import is_settlement_late

logger = logging.getLogger(__name__)

# ── Thresholds ─────────────────────────────────────────────────────────────────

PARTIAL_THRESHOLD_PCT = Decimal("5.00")    # >5% shortfall triggers anomaly
FEE_MISMATCH_THRESHOLD_PCT = Decimal("10.00")  # >10% fee deviation triggers anomaly
SEVERITY_WARNING_HOURS = 12                 # <12h late → warning
SEVERITY_CRITICAL_HOURS = 24                # >24h late → critical
DEFAULT_FEE_PCT = Decimal("0.02")           # 2% standard Razorpay fee
ACCEPTED_VARIANCE_PCT = Decimal("0.01")     # 1% reconciliation tolerance


# ── Detector ───────────────────────────────────────────────────────────────────


class SettlementAnomalyDetector:
    """Analyse a single Settlement and return a list of detected anomalies.

    Parameters
    ----------
    session : Session
        A SQLAlchemy session for database lookups.
    now : datetime, optional
        Override the current time (useful for testing).
    """

    def __init__(self, session: Session, *, now: Optional[datetime] = None) -> None:
        self.session = session
        _raw = now or datetime.now(timezone.utc)
        self._now = _raw.replace(tzinfo=None) if _raw.tzinfo else _raw

    # ── Public API ────────────────────────────────────────────────────

    def detect_anomalies(self, settlement: Settlement) -> List[Anomaly]:
        """Run all detection checks and return a list of Anomaly objects.

        Each Anomaly is created with ``status=OPEN`` and an appropriate
        severity level.  No objects are added to the session — the caller
        decides whether to persist them.
        """
        logger.info(
            "Running anomaly detection for settlement %s (merchant=%s, status=%s, amount=%s)",
            settlement.id, settlement.merchant_id, settlement.status, settlement.amount,
        )

        anomalies: List[Anomaly] = []

        # 1. Delay detection
        delay = self._detect_delay(settlement)
        if delay is not None:
            anomalies.append(delay)

        # 2. Partial settlement
        partial = self._detect_partial(settlement)
        if partial is not None:
            anomalies.append(partial)

        # 3. Failed settlement
        failed = self._detect_failed(settlement)
        if failed is not None:
            anomalies.append(failed)

        # 4. Fee mismatch
        fee = self._detect_fee_mismatch(settlement)
        if fee is not None:
            anomalies.append(fee)

        # 5. Multiple failed attempts
        multi_fail = self._detect_multiple_failures(settlement)
        if multi_fail is not None:
            anomalies.append(multi_fail)

        # 6. Reconciliation gap
        recon = self._detect_reconciliation_gap(settlement)
        if recon is not None:
            anomalies.append(recon)

        logger.info(
            "Settlement %s: %d anomalies detected.", settlement.id, len(anomalies),
        )
        return anomalies

    # ── 1. Delay Detection ────────────────────────────────────────────

    def _detect_delay(self, settlement: Settlement) -> Optional[Anomaly]:
        """Detect settlements past their expected T+2 arrival deadline."""
        if settlement.status == SettlementStatus.SUCCESS:
            return None

        is_late, delta = is_settlement_late(
            settlement.created_at, self._now, getattr(settlement.status, 'value', str(settlement.status)),
        )
        if not is_late:
            return None

        hours_late = delta.total_seconds() / 3600
        severity = self._map_severity(hours_late, AnomalyType.SETTLEMENT_DELAYED)
        root_cause = self._infer_delay_root_cause(settlement)

        logger.warning(
            "Settlement %s is %.1fh late (severity=%s, root_cause=%s)",
            settlement.id, hours_late, severity.value, root_cause,
        )

        return Anomaly(
            id=uuid.uuid4(),
            merchant_id=settlement.merchant_id,
            anomaly_type=AnomalyType.SETTLEMENT_DELAYED,
            related_settlement_id=settlement.id,
            detected_at=self._now,
            root_cause=root_cause,
            root_cause_confidence=Decimal("0.85"),
            status=AnomalyStatus.OPEN,
            severity=severity,
            recommended_action="Contact bank or Razorpay support to expedite settlement",
        )

    def _infer_delay_root_cause(self, settlement: Settlement) -> str:
        """Infer root cause from the latest attempt's bank response code."""
        attempt = self._get_latest_attempt(settlement)
        if attempt is None or attempt.response_code is None:
            return "unknown_delay"
        info = get_root_cause_from_code(attempt.response_code)
        return info.get("category", "unknown_delay")

    # ── 2. Partial Settlement Detection ───────────────────────────────

    def _detect_partial(self, settlement: Settlement) -> Optional[Anomaly]:
        """Detect settlements where the actual amount is significantly less
        than the expected amount calculated from transactions + refunds."""
        if settlement.status not in (SettlementStatus.PARTIAL, SettlementStatus.PENDING):
            return None

        expected = self._calculate_expected_settlement_amount(settlement)
        if expected <= 0:
            return None

        actual = settlement.net_amount
        shortfall = expected - actual
        shortfall_pct = (shortfall / expected * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        if shortfall_pct <= PARTIAL_THRESHOLD_PCT:
            return None

        logger.warning(
            "Settlement %s: partial — expected %s, got %s (%s%% shortfall)",
            settlement.id, expected, actual, shortfall_pct,
        )

        return Anomaly(
            id=uuid.uuid4(),
            merchant_id=settlement.merchant_id,
            anomaly_type=AnomalyType.SETTLEMENT_PARTIAL,
            related_settlement_id=settlement.id,
            detected_at=self._now,
            root_cause=f"amount_shortfall_{shortfall_pct}pct",
            root_cause_confidence=Decimal("0.90"),
            status=AnomalyStatus.OPEN,
            severity=SeverityLevel.WARNING,
            recommended_action=(
                f"Review settlement breakdown — {shortfall_pct}% shortfall detected. "
                "Check for refund deductions or bank charges."
            ),
        )

    def _calculate_expected_settlement_amount(self, settlement: Settlement) -> Decimal:
        """Calculate the expected net settlement amount.

        Formula:
            sum(transaction.amount) - sum(completed_refunds.amount) - fees - taxes
        """
        if settlement.settlement_period_start is None or settlement.settlement_period_end is None:
            return settlement.amount  # fallback to declared amount

        # Sum captured transactions in the settlement period
        stmt_txn = select(
            func.coalesce(
                func.sum(Transaction.amount),
                Decimal("0.00"),
            )
        ).select_from(Transaction).where(
            Transaction.merchant_id == settlement.merchant_id,
            Transaction.status == "captured",
            Transaction.created_at >= datetime.combine(settlement.settlement_period_start, datetime.min.time()),
            Transaction.created_at <= datetime.combine(settlement.settlement_period_end, datetime.max.time()),
        )
        total_txn = self.session.execute(stmt_txn).scalar_one()

        # Sum successful refunds in the same period
        stmt_refund = select(
            func.coalesce(
                func.sum(Refund.amount),
                Decimal("0.00"),
            )
        ).select_from(Refund).where(
            Refund.merchant_id == settlement.merchant_id,
            Refund.status == RefundStatus.SUCCESS,
            Refund.created_at >= datetime.combine(settlement.settlement_period_start, datetime.min.time()),
            Refund.created_at <= datetime.combine(settlement.settlement_period_end, datetime.max.time()),
        )
        total_refunds = self.session.execute(stmt_refund).scalar_one()

        expected_net = Decimal(total_txn) - Decimal(total_refunds) - settlement.fees - settlement.taxes
        logger.debug(
            "Expected settlement for %s: txns=%s, refunds=%s, fees=%s, taxes=%s → net=%s",
            settlement.id, total_txn, total_refunds, settlement.fees, settlement.taxes, expected_net,
        )
        return max(expected_net, Decimal("0.00"))

    # ── 3. Failed Settlement Detection ────────────────────────────────

    def _detect_failed(self, settlement: Settlement) -> Optional[Anomaly]:
        """Detect settlements with status 'failed' and extract the root cause."""
        if settlement.status != SettlementStatus.FAILED:
            return None

        attempt = self._get_latest_attempt(settlement)
        response_code = attempt.response_code if attempt else None

        if response_code:
            info = get_root_cause_from_code(response_code)
            root_cause = info.get("category", "unknown_failure")
            description = info.get("description", "Unknown failure")
        else:
            root_cause = "unknown_failure"
            description = "Settlement failed with no response code"

        logger.error(
            "Settlement %s FAILED (code=%s, root_cause=%s)",
            settlement.id, response_code, root_cause,
        )

        return Anomaly(
            id=uuid.uuid4(),
            merchant_id=settlement.merchant_id,
            anomaly_type=AnomalyType.SETTLEMENT_FAILED,
            related_settlement_id=settlement.id,
            detected_at=self._now,
            root_cause=root_cause,
            root_cause_confidence=Decimal("0.95"),
            status=AnomalyStatus.OPEN,
            severity=SeverityLevel.CRITICAL,
            recommended_action=(
                f"{description}. "
                "Update bank details or contact Razorpay support."
            ),
        )

    # ── 4. Fee Mismatch Detection ─────────────────────────────────────

    def _detect_fee_mismatch(self, settlement: Settlement) -> Optional[Anomaly]:
        """Detect if actual fees deviate from expected fees by >10%."""
        if settlement.amount <= 0:
            return None

        expected_fee = (settlement.amount * DEFAULT_FEE_PCT).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        actual_fee = settlement.fees

        if expected_fee <= 0:
            return None

        deviation_pct = (
            abs(actual_fee - expected_fee) / expected_fee * 100
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        if deviation_pct <= FEE_MISMATCH_THRESHOLD_PCT:
            return None

        direction = "overcharged" if actual_fee > expected_fee else "undercharged"

        logger.warning(
            "Settlement %s: fee mismatch — expected %s, got %s (%s%% %s)",
            settlement.id, expected_fee, actual_fee, deviation_pct, direction,
        )

        return Anomaly(
            id=uuid.uuid4(),
            merchant_id=settlement.merchant_id,
            anomaly_type=AnomalyType.SETTLEMENT_PARTIAL,  # no dedicated fee type
            related_settlement_id=settlement.id,
            detected_at=self._now,
            root_cause=f"fee_mismatch_{direction}_{deviation_pct}pct",
            root_cause_confidence=Decimal("0.88"),
            status=AnomalyStatus.OPEN,
            severity=SeverityLevel.WARNING,
            recommended_action=(
                f"Fee {direction} by {deviation_pct}% "
                f"(expected ₹{expected_fee}, charged ₹{actual_fee}). "
                "Contact Razorpay support for fee review."
            ),
        )

    # ── 5. Multiple Failed Attempts ───────────────────────────────────

    def _detect_multiple_failures(self, settlement: Settlement) -> Optional[Anomaly]:
        """Detect settlements with ≥2 failed transfer attempts."""
        failed_attempts = [
            a for a in settlement.attempts
            if a.status == SettlementAttemptStatus.FAILED
        ]

        if len(failed_attempts) < 2:
            return None

        methods_tried = [getattr(a.method, "value", str(a.method)) for a in failed_attempts]
        last_code = failed_attempts[-1].response_code

        logger.error(
            "Settlement %s: %d failed attempts (methods=%s, last_code=%s)",
            settlement.id, len(failed_attempts), methods_tried, last_code,
        )

        return Anomaly(
            id=uuid.uuid4(),
            merchant_id=settlement.merchant_id,
            anomaly_type=AnomalyType.SETTLEMENT_FAILED,
            related_settlement_id=settlement.id,
            detected_at=self._now,
            root_cause=f"multiple_bank_failures_{len(failed_attempts)}_attempts",
            root_cause_confidence=Decimal("0.92"),
            status=AnomalyStatus.OPEN,
            severity=SeverityLevel.CRITICAL,
            recommended_action=(
                f"Settlement failed {len(failed_attempts)} times across methods {methods_tried}. "
                "Verify bank account details and contact Razorpay support."
            ),
        )

    # ── 6. Reconciliation Gap Detection ───────────────────────────────

    def _detect_reconciliation_gap(self, settlement: Settlement) -> Optional[Anomaly]:
        """Detect if transaction sum doesn't match settlement amount
        (beyond a 1% tolerance)."""
        if settlement.settlement_period_start is None or settlement.settlement_period_end is None:
            return None

        # Sum all captured transactions
        stmt_txn2 = select(
            func.coalesce(func.sum(Transaction.amount), Decimal("0.00"))
        ).select_from(Transaction).where(
            Transaction.merchant_id == settlement.merchant_id,
            Transaction.status == "captured",
            Transaction.created_at >= datetime.combine(settlement.settlement_period_start, datetime.min.time()),
            Transaction.created_at <= datetime.combine(settlement.settlement_period_end, datetime.max.time()),
        )
        total_txn = Decimal(self.session.execute(stmt_txn2).scalar_one())

        if total_txn <= 0:
            return None

        # Settlement amount should equal total_txn minus known refunds minus fees/taxes
        expected_gross = total_txn - settlement.fees - settlement.taxes
        actual_gross = settlement.amount

        gap = abs(expected_gross - actual_gross)
        variance_pct = (gap / expected_gross * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if expected_gross > 0 else Decimal("0")

        if variance_pct <= ACCEPTED_VARIANCE_PCT:
            return None

        logger.warning(
            "Settlement %s: reconciliation gap — txn_total=%s, expected_gross=%s, actual=%s (%s%%)",
            settlement.id, total_txn, expected_gross, actual_gross, variance_pct,
        )

        return Anomaly(
            id=uuid.uuid4(),
            merchant_id=settlement.merchant_id,
            anomaly_type=AnomalyType.SETTLEMENT_PARTIAL,  # using partial as closest match
            related_settlement_id=settlement.id,
            detected_at=self._now,
            root_cause=f"reconciliation_gap_{variance_pct}pct",
            root_cause_confidence=Decimal("0.80"),
            status=AnomalyStatus.OPEN,
            severity=SeverityLevel.WARNING,
            recommended_action=(
                f"Reconciliation gap of {variance_pct}% detected. "
                "Verify transaction records and settlement breakdown."
            ),
        )

    # ── Helpers ────────────────────────────────────────────────────────

    def _get_latest_attempt(self, settlement: Settlement) -> Optional[SettlementAttempt]:
        """Return the most recent settlement attempt, or None."""
        if not settlement.attempts:
            return None
        return max(settlement.attempts, key=lambda a: a.attempt_number)

    @staticmethod
    def _map_severity(hours_late: float, anomaly_type: AnomalyType) -> SeverityLevel:
        """Map lateness and anomaly type to a severity level.

        Rules:
        - CRITICAL: >24h late
        - WARNING: >12h late
        - INFO: <12h late

        Note: settlement_failed and multiple_failures set severity directly
        to CRITICAL in their respective detection methods.
        """
        if hours_late > SEVERITY_CRITICAL_HOURS:
            return SeverityLevel.CRITICAL
        if hours_late > SEVERITY_WARNING_HOURS:
            return SeverityLevel.WARNING
        return SeverityLevel.INFO


# ══════════════════════════════════════════════════════════════════════════════
# Root-Cause Classifier
# ══════════════════════════════════════════════════════════════════════════════


class SettlementRootCauseClassifier:
    """Classify the root cause of a settlement anomaly and produce a Diagnosis.

    Uses bank response codes, attempt history, and timing patterns to build
    a structured root-cause diagnosis with confidence scoring.

    Parameters
    ----------
    session : Session
        SQLAlchemy session for historical lookups.
    now : datetime, optional
        Override current time (useful for testing).
    """

    def __init__(self, session: Session, *, now: Optional[datetime] = None) -> None:
        self.session = session
        _raw = now or datetime.now(timezone.utc)
        self._now = _raw.replace(tzinfo=None) if _raw.tzinfo else _raw

    # ── Public API ────────────────────────────────────────────────────

    def classify_root_cause(
        self, anomaly: Anomaly, settlement: Settlement
    ) -> Diagnosis:
        """Produce a Diagnosis for the given anomaly + settlement pair.

        Steps:
        1. Fetch latest attempt and its bank response code.
        2. Look up the code in bank_codes mapping.
        3. Compute a confidence score with boosters.
        4. Build an evidence list and causal chain.
        5. Return an unsaved ``Diagnosis`` object.
        """
        logger.info(
            "Classifying root cause for anomaly %s (settlement %s)",
            anomaly.id, settlement.id,
        )

        attempt = self._get_latest_attempt(settlement)
        code = attempt.response_code if attempt else None

        if code:
            code_info = self._look_up_bank_code(code)
            root_cause = code_info.get("category", "unknown_error")
            base_confidence = self._get_confidence_score(code)
            confidence = self._apply_boosters(
                base_confidence, merchant_id=settlement.merchant_id,
                code=code, attempt=attempt, settlement=settlement,
            )
        else:
            code_info = {
                "category": "bank_processing_delay",
                "description": "No response code received",
                "cause": "Settlement is still being processed by the bank",
                "merchant_impact": "Settlement may complete shortly",
                "recommended_action": "Wait for bank processing to complete",
                "retryable": True,
            }
            root_cause = "bank_processing_delay"
            confidence = Decimal("0.60")

        evidence = self._build_evidence_list(settlement, attempt, code_info)
        causal_chain = self._build_causal_chain(root_cause, attempt)

        explanation = self._build_explanation(root_cause, code_info, attempt)

        diagnosis = Diagnosis(
            id=uuid.uuid4(),
            anomaly_id=anomaly.id,
            root_cause_category=root_cause,
            root_cause_subcategory=code_info.get("description", "unclassified"),
            explanation_plain_english=explanation,
            confidence=confidence,
            evidence={"facts": evidence},
            causal_chain=causal_chain,
            created_at=self._now,
        )

        logger.info(
            "Diagnosis for anomaly %s: root_cause=%s, confidence=%s",
            anomaly.id, root_cause, confidence,
        )
        return diagnosis

    # ── Helpers ────────────────────────────────────────────────────────

    def _get_latest_attempt(
        self, settlement: Settlement
    ) -> Optional[SettlementAttempt]:
        """Return the most recent settlement attempt, or None."""
        if not settlement.attempts:
            return None
        return max(settlement.attempts, key=lambda a: a.attempt_number)

    def _look_up_bank_code(self, code: str) -> dict:
        """Look up a bank response code and return cause information."""
        return get_root_cause_from_code(code)

    def _check_previous_failures(
        self, merchant_id, code: str
    ) -> int:
        """Count prior settlements for this merchant that failed with the same code."""
        from src.data.models import Settlement as SettModel  # avoid name clash

        stmt_count = select(
            func.count(SettModel.id)
        ).select_from(SettModel).join(
            SettlementAttempt,
            SettlementAttempt.settlement_id == SettModel.id,
        ).filter(
            SettModel.merchant_id == merchant_id,
            SettModel.status == SettlementStatus.FAILED,
            SettlementAttempt.response_code == code,
        )
        count = self.session.execute(stmt_count).scalar()
        return count or 0

    @staticmethod
    def _get_confidence_score(code: str) -> Decimal:
        """Return base confidence for a bank response code.

        Well-mapped codes get higher base confidence; unknown codes get low.
        """
        from src.utils.bank_codes import BANK_RESPONSE_CODES

        info = BANK_RESPONSE_CODES.get(str(code).strip())
        if info is None:
            return Decimal("0.40")  # unknown code
        if info.get("retryable") is True:
            return Decimal("0.75")  # known, retryable → fairly confident
        return Decimal("0.85")      # known, non-retryable → very confident

    def _apply_boosters(
        self,
        base: Decimal,
        *,
        merchant_id,
        code: str,
        attempt: Optional[SettlementAttempt],
        settlement: Settlement,
    ) -> Decimal:
        """Apply confidence boosters for patterns and history.

        Boosters:
        - Same code seen before for this merchant → ×1.2
        - Multiple attempts on this settlement → ×1.1
        - Failure during peak hours (9 AM–6 PM IST) → ×1.15
        """
        confidence = base

        # Previous failures with same code
        prev_count = self._check_previous_failures(merchant_id, code)
        if prev_count > 0:
            confidence = min(confidence * Decimal("1.20"), Decimal("0.99"))
            logger.debug(
                "Confidence boosted to %s (previous failures with code %s: %d)",
                confidence, code, prev_count,
            )

        # Multiple attempts on this settlement
        if settlement.attempts and len(settlement.attempts) >= 2:
            confidence = min(confidence * Decimal("1.10"), Decimal("0.99"))
            logger.debug(
                "Confidence boosted to %s (%d attempts)",
                confidence, len(settlement.attempts),
            )

        # Timing correlates with peak hours (9 AM – 6 PM)
        if attempt and attempt.initiated_at:
            hour = attempt.initiated_at.hour
            if 9 <= hour <= 18:
                confidence = min(confidence * Decimal("1.15"), Decimal("0.99"))
                logger.debug(
                    "Confidence boosted to %s (peak hours, hour=%d)",
                    confidence, hour,
                )

        return confidence

    @staticmethod
    def _build_evidence_list(
        settlement: Settlement,
        attempt: Optional[SettlementAttempt],
        code_info: dict,
    ) -> List[str]:
        """Compile a structured evidence list supporting the diagnosis."""
        evidence: List[str] = []

        # Settlement facts
        evidence.append(
            f"Settlement {settlement.id}: amount=₹{settlement.amount}, "
            f"status={getattr(settlement.status, "value", str(settlement.status))}, created={settlement.created_at}"
        )
        evidence.append(
            f"Net amount: ₹{settlement.net_amount} (fees=₹{settlement.fees}, "
            f"taxes=₹{settlement.taxes})"
        )

        # Attempt facts
        if attempt:
            evidence.append(
                f"Latest attempt #{attempt.attempt_number}: method={getattr(attempt.method, "value", str(attempt.method))}, "
                f"status={getattr(attempt.status, "value", str(attempt.status))}, response_code={attempt.response_code}"
            )
            if attempt.response_message:
                evidence.append(
                    f"Bank response: {attempt.response_message}"
                )
            if attempt.bank_reference_id:
                evidence.append(
                    f"Bank reference: {attempt.bank_reference_id}"
                )
        else:
            evidence.append("No settlement attempts recorded")

        # Bank code info
        if code_info.get("cause"):
            evidence.append(f"Bank error cause: {code_info['cause']}")
        if code_info.get("merchant_impact"):
            evidence.append(f"Impact: {code_info['merchant_impact']}")
        evidence.append(
            f"Retryable: {'Yes' if code_info.get('retryable') else 'No'}"
        )

        # Settlement period
        if settlement.settlement_period_start and settlement.settlement_period_end:
            evidence.append(
                f"Settlement period: {settlement.settlement_period_start} to "
                f"{settlement.settlement_period_end}"
            )

        # Attempt history
        if settlement.attempts:
            methods_tried = [getattr(a.method, "value", str(a.method)) for a in settlement.attempts]
            evidence.append(
                f"Total attempts: {len(settlement.attempts)}, "
                f"methods: {', '.join(methods_tried)}"
            )

        return evidence

    @staticmethod
    def _build_causal_chain(
        root_cause: str, attempt: Optional[SettlementAttempt]
    ) -> List[dict]:
        """Build a structured causal chain: [condition] → [action] → [outcome]."""
        method = getattr(attempt.method, "value", str(attempt.method)) if attempt else "unknown"
        response = attempt.response_message if attempt else "No response"
        attempt_status = getattr(attempt.status, "value", str(attempt.status)) if attempt else "unknown"

        chain = [
            {
                "step": 1,
                "role": "initial_condition",
                "event": f"Settlement payout initiated via {method}",
            },
            {
                "step": 2,
                "role": "bank_action",
                "event": f"Bank processed transfer: {response}",
                "response_code": attempt.response_code if attempt else None,
            },
            {
                "step": 3,
                "role": "outcome",
                "event": f"Transfer {attempt_status} — root cause: {root_cause}",
            },
        ]

        # Add remediation step for retryable errors
        if attempt and attempt.status == SettlementAttemptStatus.FAILED:
            chain.append(
                {
                    "step": 4,
                    "role": "remediation",
                    "event": f"System will auto-retry settlement; root cause: {root_cause}",
                }
            )

        return chain

    @staticmethod
    def _build_explanation(
        root_cause: str,
        code_info: dict,
        attempt: Optional[SettlementAttempt],
    ) -> str:
        """Generate a plain-English explanation of the diagnosis."""
        description = code_info.get("description", "Unknown issue")
        cause = code_info.get("cause", "No details available")
        action = code_info.get("recommended_action", "Contact support")

        if attempt:
            method = getattr(attempt.method, "value", str(attempt.method))
            parts = [
                f"The settlement failed with root cause: {root_cause}.",
                f"Bank returned: {description}.",
                f"Cause: {cause}.",
                f"Recommended action: {action}.",
                f"Transfer method used: {method}.",
            ]
        else:
            parts = [
                f"The settlement has root cause: {root_cause}.",
                f"Bank returned: {description}.",
                f"Cause: {cause}.",
                f"Recommended action: {action}.",
                "No transfer attempt was recorded.",
            ]

        return " ".join(parts)


# ══════════════════════════════════════════════════════════════════════════════
# Action Recommender
# ══════════════════════════════════════════════════════════════════════════════


# ── Decision tree: root_cause → (action, timeline, probability, urgency) ──

ACTION_TREE: dict[str, tuple[RecommendedAction, str, Decimal, UrgencyLevel]] = {
    "insufficient_funds": (
        RecommendedAction.WAIT,
        "24_hours",
        Decimal("0.95"),
        UrgencyLevel.LOW,
    ),
    "bank_processing_delay": (
        RecommendedAction.WAIT,
        "48_hours",
        Decimal("0.90"),
        UrgencyLevel.LOW,
    ),
    "account_closed": (
        RecommendedAction.CONTACT_RAZORPAY,
        "immediate",
        Decimal("0.50"),
        UrgencyLevel.CRITICAL,
    ),
    "fraud_block": (
        RecommendedAction.CONTACT_RAZORPAY,
        "immediate",
        Decimal("0.40"),
        UrgencyLevel.CRITICAL,
    ),
    "invalid_account": (
        RecommendedAction.CONTACT_RAZORPAY,
        "immediate",
        Decimal("0.55"),
        UrgencyLevel.HIGH,
    ),
    "amount_limit_exceeded": (
        RecommendedAction.CONTACT_BANK,
        "24_hours",
        Decimal("0.70"),
        UrgencyLevel.MEDIUM,
    ),
    "network_timeout": (
        RecommendedAction.WAIT,
        "24_hours",
        Decimal("0.85"),
        UrgencyLevel.LOW,
    ),
    "duplicate_transaction": (
        RecommendedAction.WAIT,
        "24_hours",
        Decimal("0.90"),
        UrgencyLevel.LOW,
    ),
    "bank_maintenance": (
        RecommendedAction.WAIT,
        "48_hours",
        Decimal("0.88"),
        UrgencyLevel.LOW,
    ),
    "currency_mismatch": (
        RecommendedAction.CONTACT_RAZORPAY,
        "24_hours",
        Decimal("0.60"),
        UrgencyLevel.HIGH,
    ),
    "system_error": (
        RecommendedAction.WAIT,
        "24_hours",
        Decimal("0.75"),
        UrgencyLevel.MEDIUM,
    ),
    "rate_limit_exceeded": (
        RecommendedAction.WAIT,
        "24_hours",
        Decimal("0.80"),
        UrgencyLevel.LOW,
    ),
    "unknown_error": (
        RecommendedAction.CONTACT_RAZORPAY,
        "24_hours",
        Decimal("0.50"),
        UrgencyLevel.MEDIUM,
    ),
}

# ── Anomaly-type overrides (when type takes priority over root_cause) ────

ANOMALY_TYPE_TREE: dict[str, tuple[RecommendedAction, str, Decimal, UrgencyLevel]] = {
    AnomalyType.SETTLEMENT_FAILED.value: (
        RecommendedAction.CONTACT_RAZORPAY,
        "immediate",
        Decimal("0.50"),
        UrgencyLevel.CRITICAL,
    ),
    AnomalyType.SETTLEMENT_DELAYED.value: (
        RecommendedAction.WAIT,
        "24_hours",
        Decimal("0.80"),
        UrgencyLevel.MEDIUM,
    ),
    AnomalyType.SETTLEMENT_PARTIAL.value: (
        RecommendedAction.CONTACT_BANK,
        "48_hours",
        Decimal("0.70"),
        UrgencyLevel.MEDIUM,
    ),
}

# ── Timeline → hours mapping ────

TIMELINE_HOURS: dict[str, int] = {
    "immediate": 2,
    "24_hours": 24,
    "48_hours": 48,
    "1_week": 168,
}

# ── Merchant-friendly templates ────

MERCHANT_TEXT: dict[str, str] = {
    "insufficient_funds": (
        "Your settlement account doesn't have enough balance to receive the payout. "
        "Don't worry — Razorpay will automatically retry the transfer by end of day. "
        "Just make sure your bank account has sufficient funds before the retry."
    ),
    "bank_processing_delay": (
        "Your bank is taking a bit longer than usual to process the settlement. "
        "This is normal during high-volume periods. The transfer should complete "
        "within 2 business days. No action needed from your side."
    ),
    "account_closed": (
        "It looks like your settlement bank account may be closed or frozen. "
        "This needs your immediate attention. Please contact Razorpay support "
        "right away with your settlement ID so we can update your bank details."
    ),
    "fraud_block": (
        "Your settlement has been flagged for a security review. This is a precautionary "
        "measure. Please contact Razorpay support immediately with your business "
        "documents to get this resolved quickly."
    ),
    "invalid_account": (
        "The bank account details on file appear to be incorrect. Please verify your "
        "account number and IFSC code in the Razorpay dashboard, then contact support "
        "to reinitiate the settlement."
    ),
    "amount_limit_exceeded": (
        "The settlement amount exceeds your bank's per-transaction limit. "
        "Contact your bank or Razorpay support to arrange a split transfer."
    ),
    "network_timeout": (
        "There was a temporary communication issue with the bank. "
        "The settlement should process automatically. Check back in 24 hours."
    ),
    "duplicate_transaction": (
        "The system detected a potential duplicate settlement and blocked it "
        "to protect your account. This is a safety measure. Check your dashboard "
        "to confirm which settlement is correct."
    ),
    "bank_maintenance": (
        "Your bank's systems are currently under maintenance. "
        "The settlement will resume once maintenance is complete. "
        "No action needed — this typically resolves within 24-48 hours."
    ),
    "currency_mismatch": (
        "There's a currency mismatch between your settlement and account settings. "
        "Contact Razorpay support to correct the settlement currency."
    ),
    "system_error": (
        "We encountered a temporary technical issue while processing your settlement. "
        "It should resolve automatically within 24 hours. If not, please contact support."
    ),
    "rate_limit_exceeded": (
        "Too many settlement requests were processed in a short time. "
        "The system will retry shortly. No action needed."
    ),
    "unknown_error": (
        "We're not sure what caused this issue. "
        "Please contact Razorpay support with your settlement ID for investigation."
    ),
}


class SettlementActionRecommender:
    """Recommend the next action for a settlement anomaly based on root cause.

    Uses a decision tree to map root causes to recommended actions, timelines,
    success probabilities, and urgency levels.  Generates merchant-friendly
    explanations and calculates follow-up check times.

    Parameters
    ----------
    session : Session
        SQLAlchemy session for merchant history lookups.
    now : datetime, optional
        Override current time (useful for testing).
    """

    def __init__(self, session: Session, *, now: Optional[datetime] = None) -> None:
        self.session = session
        _raw = now or datetime.now(timezone.utc)
        self._now = _raw.replace(tzinfo=None) if _raw.tzinfo else _raw

    # ── Public API ────────────────────────────────────────────────────

    def recommend_action(
        self, anomaly: Anomaly, diagnosis: Diagnosis
    ) -> Recommendation:
        """Produce a Recommendation for the given anomaly + diagnosis.

        Steps:
        1. Look up root cause in the decision tree.
        2. Apply anomaly-type overrides if applicable.
        3. Compute success probability with merchant-history adjustment.
        4. Generate merchant-friendly explanation text.
        5. Return an unsaved ``Recommendation`` object.
        """
        root_cause = diagnosis.root_cause_category or "unknown_error"
        anomaly_type = anomaly.anomaly_type.value if anomaly.anomaly_type else None

        logger.info(
            "Recommending action for anomaly %s (root_cause=%s, type=%s)",
            anomaly.id, root_cause, anomaly_type,
        )

        # 1. Decision tree lookup
        action, timeline, base_prob, urgency = self._resolve_action(
            root_cause, anomaly_type
        )

        # 2. Confidence-adjusted probability
        base_prob = self._adjust_probability_with_confidence(
            base_prob, diagnosis.confidence
        )

        # 3. Merchant history adjustment
        success_prob = self._estimate_success_probability(
            root_cause, anomaly.merchant_id
        )
        # Blend: 70% base + 30% merchant history
        final_prob = (base_prob * Decimal("0.7") + success_prob * Decimal("0.3")).quantize(
            Decimal("0.01")
        )
        final_prob = min(max(final_prob, Decimal("0.10")), Decimal("0.99"))

        # 4. Timeline hours
        hours = TIMELINE_HOURS.get(timeline, 24)
        next_check = self._now + timedelta(hours=hours)

        # 5. Merchant-friendly text
        text = self._generate_merchant_friendly_text(root_cause, timeline)

        recommendation = Recommendation(
            id=uuid.uuid4(),
            anomaly_id=anomaly.id,
            recommendation_text=text,
            recommended_action=action,
            urgency=urgency,
            timeline=timeline,
            expected_resolution_time_hours=hours,
            success_probability=final_prob,
            merchant_followed=False,
            outcome_if_followed=None,
        )

        logger.info(
            "Recommendation for anomaly %s: action=%s, urgency=%s, prob=%s",
            anomaly.id, action.value, urgency.value, final_prob,
        )
        return recommendation

    # ── Decision tree ─────────────────────────────────────────────────

    def _resolve_action(
        self, root_cause: str, anomaly_type: Optional[str]
    ) -> tuple[RecommendedAction, str, Decimal, UrgencyLevel]:
        """Resolve the action from the decision tree.

        Anomaly-type overrides take precedence for critical failure types.
        """
        # Anomaly-type override for settlement_failed (highest priority)
        if anomaly_type == AnomalyType.SETTLEMENT_FAILED.value:
            return ANOMALY_TYPE_TREE[AnomalyType.SETTLEMENT_FAILED.value]

        # Root-cause lookup
        if root_cause in ACTION_TREE:
            return ACTION_TREE[root_cause]

        # Fallback: try anomaly type
        if anomaly_type and anomaly_type in ANOMALY_TYPE_TREE:
            return ANOMALY_TYPE_TREE[anomaly_type]

        # Final fallback
        logger.warning(
            "No action found for root_cause=%s, type=%s — using default",
            root_cause, anomaly_type,
        )
        return (
            RecommendedAction.CONTACT_RAZORPAY,
            "24_hours",
            Decimal("0.50"),
            UrgencyLevel.MEDIUM,
        )

    # ── Probability adjustment ────────────────────────────────────────

    @staticmethod
    def _adjust_probability_with_confidence(
        base_prob: Decimal, confidence: Optional[Decimal]
    ) -> Decimal:
        """Adjust success probability by diagnosis confidence.

        Low confidence reduces the probability; high confidence keeps it stable.
        """
        if confidence is None:
            return base_prob
        # confidence acts as a dampener: prob × (0.7 + 0.3 × confidence)
        factor = Decimal("0.7") + Decimal("0.3") * confidence
        return (base_prob * factor).quantize(Decimal("0.01"))

    def _estimate_success_probability(
        self, root_cause: str, merchant_id
    ) -> Decimal:
        """Estimate success probability based on merchant history.

        Counts previous resolutions for this root cause and merchant.
        Falls back to base probability if no history.
        """
        # Count anomalies with same root cause that were resolved
        from src.data.models import Anomaly as AnomModel

        stmt_resolved = select(
            func.count(AnomModel.id)
        ).select_from(AnomModel).filter(
            AnomModel.merchant_id == merchant_id,
            AnomModel.root_cause == root_cause,
            AnomModel.status == AnomalyStatus.RESOLVED,
        )
        resolved_count = self.session.execute(stmt_resolved).scalar() or 0

        stmt_total = select(
            func.count(AnomModel.id)
        ).select_from(AnomModel).filter(
            AnomModel.merchant_id == merchant_id,
            AnomModel.root_cause == root_cause,
        )
        total_count = self.session.execute(stmt_total).scalar() or 0

        if total_count == 0:
            # No history — use base from decision tree
            tree_entry = ACTION_TREE.get(root_cause)
            return tree_entry[2] if tree_entry else Decimal("0.50")

        # Historical success rate
        rate = Decimal(resolved_count) / Decimal(total_count)
        return rate.quantize(Decimal("0.01"))

    # ── Text generation ───────────────────────────────────────────────

    @staticmethod
    def _generate_merchant_friendly_text(root_cause: str, timeline: str) -> str:
        """Generate clear, actionable explanation from the merchant's perspective."""
        template = MERCHANT_TEXT.get(root_cause)
        if template is None:
            template = (
                "We encountered an issue with your settlement. "
                "Please contact Razorpay support for assistance."
            )
        return template

    @staticmethod
    def _map_action_to_timeline(action: RecommendedAction) -> str:
        """Return appropriate timeline for an action type."""
        if action == RecommendedAction.WAIT:
            return "24_hours"
        if action in (
            RecommendedAction.CONTACT_RAZORPAY,
            RecommendedAction.CONTACT_BANK,
            RecommendedAction.ESCALATE,
        ):
            return "immediate"
        return "48_hours"

    # ── Next-check helper ─────────────────────────────────────────────

    def _calculate_next_check(self, timeline: str) -> datetime:
        """Calculate the next follow-up check time."""
        hours = TIMELINE_HOURS.get(timeline, 24)
        return self._now + timedelta(hours=hours)
