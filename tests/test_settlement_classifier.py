"""Tests for src/agents/settlement_agent.py — SettlementRootCauseClassifier.

Uses in-memory SQLite via the shared ``db_session`` fixture from test_setup.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from src.agents.settlement_agent import SettlementRootCauseClassifier
from src.data.models import (
    Anomaly,
    AnomalyStatus,
    AnomalyType,
    Diagnosis,
    Merchant,
    SeverityLevel,
    Settlement,
    SettlementAttempt,
    SettlementAttemptStatus,
    SettlementStatus,
    TransferMethod,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

NOW = datetime(2025, 6, 15, 12, 0, 0)


def _merchant(session) -> Merchant:
    m = Merchant(id=uuid.uuid4(), business_name="Classifier Test Co")
    session.add(m)
    session.flush()
    return m


def _settlement(session, *, merchant_id, status=SettlementStatus.FAILED, **kw) -> Settlement:
    defaults = dict(
        id=f"settle_{uuid.uuid4().hex[:8]}",
        merchant_id=merchant_id,
        amount=Decimal("100000.00"),
        currency="INR",
        status=status,
        created_at=NOW - timedelta(days=3),
        fees=Decimal("2000.00"),
        taxes=Decimal("360.00"),
        net_amount=Decimal("97640.00"),
        related_refunds=[],
        related_disputes=[],
    )
    defaults.update(kw)
    s = Settlement(**defaults)
    session.add(s)
    session.flush()
    return s


def _attempt(
    session,
    *,
    settlement_id: str,
    number: int = 1,
    status: SettlementAttemptStatus = SettlementAttemptStatus.FAILED,
    method: TransferMethod = TransferMethod.NEFT,
    response_code: str | None = "40091",
    response_message: str | None = "Insufficient funds",
    initiated_at: datetime | None = None,
) -> SettlementAttempt:
    a = SettlementAttempt(
        settlement_id=settlement_id,
        attempt_number=number,
        method=method,
        initiated_at=initiated_at or NOW - timedelta(hours=2),
        response_code=response_code,
        response_message=response_message,
        status=status,
        bank_reference_id=f"BANK{number:04d}" if status == SettlementAttemptStatus.SUCCESS else None,
    )
    session.add(a)
    session.flush()
    return a


def _anomaly(session, *, merchant_id, settlement_id) -> Anomaly:
    a = Anomaly(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        anomaly_type=AnomalyType.SETTLEMENT_FAILED,
        related_settlement_id=settlement_id,
        detected_at=NOW,
        root_cause="settlement_failed",
        root_cause_confidence=Decimal("0.90"),
        status=AnomalyStatus.OPEN,
        severity=SeverityLevel.CRITICAL,
        recommended_action="Investigate",
    )
    session.add(a)
    session.flush()
    return a


# ══════════════════════════════════════════════════════════════════════════════
# Test Cases
# ══════════════════════════════════════════════════════════════════════════════


class TestClassifyInsufficientFunds:
    """Test 1: Classification with bank code 40091."""

    def test_classify_insufficient_funds(self, db_session):
        merchant = _merchant(db_session)
        settlement = _settlement(db_session, merchant_id=merchant.id)
        _attempt(
            db_session,
            settlement_id=settlement.id,
            response_code="40091",
            response_message="Insufficient Funds in Settlement Account",
        )
        anomaly = _anomaly(db_session, merchant_id=merchant.id, settlement_id=settlement.id)

        classifier = SettlementRootCauseClassifier(db_session, now=NOW)
        diagnosis = classifier.classify_root_cause(anomaly, settlement)

        assert isinstance(diagnosis, Diagnosis)
        assert diagnosis.anomaly_id == anomaly.id
        assert diagnosis.root_cause_category == "insufficient_funds"
        assert Decimal("0.00") <= diagnosis.confidence <= Decimal("1.00")
        assert diagnosis.confidence >= Decimal("0.75")  # known code base confidence
        assert "insufficient" in (diagnosis.root_cause_subcategory or "").lower()

    def test_diagnosis_object_structure(self, db_session):
        """Test 10: Verify the Diagnosis object has all required fields."""
        merchant = _merchant(db_session)
        settlement = _settlement(db_session, merchant_id=merchant.id)
        _attempt(
            db_session,
            settlement_id=settlement.id,
            response_code="40091",
        )
        anomaly = _anomaly(db_session, merchant_id=merchant.id, settlement_id=settlement.id)

        classifier = SettlementRootCauseClassifier(db_session, now=NOW)
        diagnosis = classifier.classify_root_cause(anomaly, settlement)

        # Verify all required fields are populated
        assert diagnosis.id is not None
        assert diagnosis.anomaly_id == anomaly.id
        assert isinstance(diagnosis.root_cause_category, str)
        assert isinstance(diagnosis.root_cause_subcategory, str)
        assert isinstance(diagnosis.explanation_plain_english, str)
        assert isinstance(diagnosis.confidence, Decimal)
        assert isinstance(diagnosis.evidence, dict)
        assert isinstance(diagnosis.causal_chain, list)
        assert diagnosis.created_at == NOW

        # Evidence should have facts
        assert "facts" in diagnosis.evidence
        assert isinstance(diagnosis.evidence["facts"], list)
        assert len(diagnosis.evidence["facts"]) > 0

        # Causal chain should have steps
        assert len(diagnosis.causal_chain) >= 3
        for step in diagnosis.causal_chain:
            assert "step" in step
            assert "role" in step
            assert "event" in step


class TestClassifyBankProcessingDelay:
    """Test 2: Classification with bank code 40094 (retryable)."""

    def test_classify_bank_processing_delay(self, db_session):
        merchant = _merchant(db_session)
        settlement = _settlement(db_session, merchant_id=merchant.id)
        _attempt(
            db_session,
            settlement_id=settlement.id,
            response_code="40094",
            response_message="Bank Processing Delay",
        )
        anomaly = _anomaly(db_session, merchant_id=merchant.id, settlement_id=settlement.id)

        classifier = SettlementRootCauseClassifier(db_session, now=NOW)
        diagnosis = classifier.classify_root_cause(anomaly, settlement)

        assert diagnosis.root_cause_category == "bank_processing_delay"
        # Retryable codes get 0.75 base
        assert diagnosis.confidence >= Decimal("0.75")
        # Check explanation mentions processing delay
        assert "processing" in diagnosis.explanation_plain_english.lower()


class TestClassifyAccountClosed:
    """Test 3: Classification with bank code 40092 (non-retryable)."""

    def test_classify_account_closed(self, db_session):
        merchant = _merchant(db_session)
        settlement = _settlement(db_session, merchant_id=merchant.id)
        _attempt(
            db_session,
            settlement_id=settlement.id,
            response_code="40092",
            response_message="Account Closed or Frozen",
        )
        anomaly = _anomaly(db_session, merchant_id=merchant.id, settlement_id=settlement.id)

        classifier = SettlementRootCauseClassifier(db_session, now=NOW)
        diagnosis = classifier.classify_root_cause(anomaly, settlement)

        assert diagnosis.root_cause_category == "account_closed"
        # Non-retryable codes get 0.85 base
        assert diagnosis.confidence >= Decimal("0.85")
        assert "closed" in (diagnosis.root_cause_subcategory or "").lower()


class TestClassifyFraudBlock:
    """Test 4: Classification with bank code 40097 (fraud)."""

    def test_classify_fraud_block(self, db_session):
        merchant = _merchant(db_session)
        settlement = _settlement(db_session, merchant_id=merchant.id)
        _attempt(
            db_session,
            settlement_id=settlement.id,
            response_code="40097",
            response_message="Transaction Flagged as Fraudulent",
        )
        anomaly = _anomaly(db_session, merchant_id=merchant.id, settlement_id=settlement.id)

        classifier = SettlementRootCauseClassifier(db_session, now=NOW)
        diagnosis = classifier.classify_root_cause(anomaly, settlement)

        assert diagnosis.root_cause_category == "fraud_block"
        assert diagnosis.confidence >= Decimal("0.85")  # non-retryable
        # Should mention fraud in explanation
        assert "fraud" in diagnosis.explanation_plain_english.lower()


class TestConfidenceBoosting:
    """Test 5: Confidence score boosting from pattern detection."""

    def test_confidence_boosting_from_pattern(self, db_session):
        """When the same merchant has had the same error code before,
        confidence should be boosted above the base score."""
        merchant = _merchant(db_session)

        # Create a previous failed settlement with code 40091
        old_settlement = _settlement(
            db_session,
            merchant_id=merchant.id,
            status=SettlementStatus.FAILED,
            created_at=NOW - timedelta(days=10),
        )
        _attempt(
            db_session,
            settlement_id=old_settlement.id,
            response_code="40091",
            initiated_at=NOW - timedelta(days=10, hours=2),
        )

        # Now classify a new failure with the same code
        new_settlement = _settlement(db_session, merchant_id=merchant.id)
        _attempt(
            db_session,
            settlement_id=new_settlement.id,
            response_code="40091",
        )
        anomaly = _anomaly(db_session, merchant_id=merchant.id, settlement_id=new_settlement.id)

        classifier = SettlementRootCauseClassifier(db_session, now=NOW)
        diagnosis = classifier.classify_root_cause(anomaly, new_settlement)

        # Base for 40091 (retryable) = 0.75, with 1.2x boost = 0.90
        assert diagnosis.confidence >= Decimal("0.85")


class TestMultipleFailures:
    """Test 6: Multiple attempts boost confidence."""

    def test_multiple_failures_detected(self, db_session):
        merchant = _merchant(db_session)
        settlement = _settlement(db_session, merchant_id=merchant.id)

        # 3 failed attempts
        _attempt(db_session, settlement_id=settlement.id, number=1, response_code="40091")
        _attempt(db_session, settlement_id=settlement.id, number=2, response_code="40094")
        _attempt(db_session, settlement_id=settlement.id, number=3, response_code="40098")

        anomaly = _anomaly(db_session, merchant_id=merchant.id, settlement_id=settlement.id)

        classifier = SettlementRootCauseClassifier(db_session, now=NOW)
        diagnosis = classifier.classify_root_cause(anomaly, settlement)

        # Base 0.75 × 1.10 (multiple attempts) = 0.825
        assert diagnosis.confidence >= Decimal("0.80")
        # Evidence should mention all 3 attempts
        facts = diagnosis.evidence.get("facts", [])
        attempt_facts = [f for f in facts if "Total attempts: 3" in f]
        assert len(attempt_facts) == 1


class TestEvidenceList:
    """Test 7: Evidence list is comprehensive."""

    def test_evidence_list_generation(self, db_session):
        merchant = _merchant(db_session)
        settlement = _settlement(db_session, merchant_id=merchant.id)
        _attempt(
            db_session,
            settlement_id=settlement.id,
            response_code="40093",
            response_message="Invalid Account Number or IFSC",
        )
        anomaly = _anomaly(db_session, merchant_id=merchant.id, settlement_id=settlement.id)

        classifier = SettlementRootCauseClassifier(db_session, now=NOW)
        diagnosis = classifier.classify_root_cause(anomaly, settlement)

        facts = diagnosis.evidence["facts"]
        facts_text = " ".join(facts)

        # Should contain settlement ID
        assert settlement.id in facts_text
        # Should contain response code
        assert "40093" in facts_text
        # Should contain bank cause
        assert "IFSC" in facts_text or "account" in facts_text.lower()
        # Should contain attempt info
        assert any("attempt" in f.lower() for f in facts)
        # Should contain attempt info
        assert any("attempt" in f.lower() for f in facts)


class TestCausalChain:
    """Test 8: Causal chain has proper structure."""

    def test_causal_chain_building(self, db_session):
        merchant = _merchant(db_session)
        settlement = _settlement(db_session, merchant_id=merchant.id)
        _attempt(
            db_session,
            settlement_id=settlement.id,
            response_code="40095",
            response_message="Amount Exceeds Bank Transfer Limit",
            method=TransferMethod.IMPS,
        )
        anomaly = _anomaly(db_session, merchant_id=merchant.id, settlement_id=settlement.id)

        classifier = SettlementRootCauseClassifier(db_session, now=NOW)
        diagnosis = classifier.classify_root_cause(anomaly, settlement)

        chain = diagnosis.causal_chain
        assert len(chain) >= 3  # at least condition → action → outcome

        # Step 1: initial condition
        assert chain[0]["step"] == 1
        assert chain[0]["role"] == "initial_condition"
        assert "IMPS" in chain[0]["event"]

        # Step 2: bank action
        assert chain[1]["step"] == 2
        assert chain[1]["role"] == "bank_action"
        assert "40095" in str(chain[1].get("response_code", ""))

        # Step 3: outcome
        assert chain[2]["step"] == 3
        assert chain[2]["role"] == "outcome"
        assert "amount_limit_exceeded" in chain[2]["event"]

        # Step 4: remediation (for failed attempts)
        assert chain[3]["step"] == 4
        assert chain[3]["role"] == "remediation"


class TestUnknownCodeFallback:
    """Test 9: Unknown code produces a valid fallback diagnosis."""

    def test_unknown_code_fallback(self, db_session):
        merchant = _merchant(db_session)
        settlement = _settlement(db_session, merchant_id=merchant.id)
        _attempt(
            db_session,
            settlement_id=settlement.id,
            response_code="99999",
            response_message="Unknown error",
        )
        anomaly = _anomaly(db_session, merchant_id=merchant.id, settlement_id=settlement.id)

        classifier = SettlementRootCauseClassifier(db_session, now=NOW)
        diagnosis = classifier.classify_root_cause(anomaly, settlement)

        assert diagnosis.root_cause_category == "unknown_error"
        # Unknown code → low base confidence, may be boosted by patterns
        assert diagnosis.confidence <= Decimal("0.99")
        assert len(diagnosis.evidence["facts"]) > 0
        assert len(diagnosis.causal_chain) >= 3

    def test_no_attempt_no_code(self, db_session):
        """When there's no attempt at all, classifier should handle gracefully."""
        merchant = _merchant(db_session)
        settlement = _settlement(db_session, merchant_id=merchant.id)
        anomaly = _anomaly(db_session, merchant_id=merchant.id, settlement_id=settlement.id)

        classifier = SettlementRootCauseClassifier(db_session, now=NOW)
        diagnosis = classifier.classify_root_cause(anomaly, settlement)

        # Should fall back to bank_processing_delay with 0.60 confidence
        assert diagnosis.root_cause_category == "bank_processing_delay"
        assert diagnosis.confidence == Decimal("0.60")
        # Should mention no attempts in evidence
        facts = diagnosis.evidence["facts"]
        assert any("No settlement attempts" in f for f in facts)

    def test_peak_hours_boost(self, db_session):
        """Attempt during peak hours (9 AM – 6 PM) should get a timing boost."""
        merchant = _merchant(db_session)
        settlement = _settlement(db_session, merchant_id=merchant.id)
        # Attempt at 14:00 (peak hours)
        _attempt(
            db_session,
            settlement_id=settlement.id,
            response_code="40091",
            initiated_at=datetime(2025, 6, 15, 14, 0),
        )
        anomaly = _anomaly(db_session, merchant_id=merchant.id, settlement_id=settlement.id)

        classifier = SettlementRootCauseClassifier(db_session, now=NOW)
        diagnosis = classifier.classify_root_cause(anomaly, settlement)

        # Base 0.75 × 1.15 (peak hours) = 0.8625
        assert diagnosis.confidence >= Decimal("0.85")

    def test_confidence_capped_at_99(self, db_session):
        """Multiple boosts should not exceed 0.99."""
        merchant = _merchant(db_session)

        # Create 3 previous failures with same code
        for i in range(3):
            old = _settlement(
                db_session,
                merchant_id=merchant.id,
                status=SettlementStatus.FAILED,
                created_at=NOW - timedelta(days=10 + i),
            )
            _attempt(
                db_session,
                settlement_id=old.id,
                response_code="40092",
                initiated_at=NOW - timedelta(days=10 + i, hours=2),
            )

        # New failure with same code + multiple attempts + peak hours
        settlement = _settlement(db_session, merchant_id=merchant.id)
        _attempt(
            db_session,
            settlement_id=settlement.id,
            number=1,
            response_code="40092",
            initiated_at=datetime(2025, 6, 15, 10, 0),
        )
        _attempt(
            db_session,
            settlement_id=settlement.id,
            number=2,
            response_code="40092",
            initiated_at=datetime(2025, 6, 15, 14, 0),
        )
        anomaly = _anomaly(db_session, merchant_id=merchant.id, settlement_id=settlement.id)

        classifier = SettlementRootCauseClassifier(db_session, now=NOW)
        diagnosis = classifier.classify_root_cause(anomaly, settlement)

        # Should be capped at 0.99
        assert diagnosis.confidence <= Decimal("0.99")


class TestExplanationQuality:
    """Extra: Verify explanation text is meaningful."""

    def test_explanation_mentions_root_cause(self, db_session):
        merchant = _merchant(db_session)
        settlement = _settlement(db_session, merchant_id=merchant.id)
        _attempt(
            db_session,
            settlement_id=settlement.id,
            response_code="40092",
            response_message="Account Closed",
        )
        anomaly = _anomaly(db_session, merchant_id=merchant.id, settlement_id=settlement.id)

        classifier = SettlementRootCauseClassifier(db_session, now=NOW)
        diagnosis = classifier.classify_root_cause(anomaly, settlement)

        explanation = diagnosis.explanation_plain_english
        assert "account_closed" in explanation
        assert "Account Closed" in explanation
        assert "recommended" in explanation.lower()
        assert len(explanation) > 50  # should be a full explanation
