"""Tests for src/agents/settlement_agent.py — SettlementActionRecommender.

Uses in-memory SQLite via the shared ``db_session`` fixture from test_setup.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from src.agents.settlement_agent import (
    ACTION_TREE,
    TIMELINE_HOURS,
    SettlementActionRecommender,
)
from src.data.models import (
    Anomaly,
    AnomalyStatus,
    AnomalyType,
    Diagnosis,
    Merchant,
    RecommendedAction,
    Recommendation,
    SeverityLevel,
    UrgencyLevel,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

NOW = datetime(2025, 6, 15, 12, 0, 0)


def _merchant(session) -> Merchant:
    m = Merchant(id=uuid.uuid4(), business_name="Recommender Test Co")
    session.add(m)
    session.flush()
    return m


def _anomaly(
    session,
    *,
    merchant_id,
    anomaly_type: AnomalyType = AnomalyType.SETTLEMENT_DELAYED,
    settlement_id: str | None = None,
) -> Anomaly:
    a = Anomaly(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        anomaly_type=anomaly_type,
        related_settlement_id=settlement_id,
        detected_at=NOW,
        root_cause="insufficient_funds",
        root_cause_confidence=Decimal("0.85"),
        status=AnomalyStatus.OPEN,
        severity=SeverityLevel.WARNING,
        recommended_action="Investigate",
    )
    session.add(a)
    session.flush()
    return a


def _diagnosis(
    session,
    *,
    anomaly_id,
    root_cause: str = "insufficient_funds",
    confidence: Decimal = Decimal("0.85"),
) -> Diagnosis:
    d = Diagnosis(
        id=uuid.uuid4(),
        anomaly_id=anomaly_id,
        root_cause_category=root_cause,
        root_cause_subcategory="test_subcategory",
        explanation_plain_english=f"Test explanation for {root_cause}",
        confidence=confidence,
        evidence={"facts": ["test evidence"]},
        causal_chain=[],
    )
    session.add(d)
    session.flush()
    return d


# ══════════════════════════════════════════════════════════════════════════════
# Test Cases
# ══════════════════════════════════════════════════════════════════════════════


class TestRecommendWaitInsufficientFunds:
    """Test 1: WAIT action for insufficient funds."""

    def test_recommend_wait_for_insufficient_funds(self, db_session):
        merchant = _merchant(db_session)
        anomaly = _anomaly(db_session, merchant_id=merchant.id)
        diagnosis = _diagnosis(db_session, anomaly_id=anomaly.id, root_cause="insufficient_funds")

        recommender = SettlementActionRecommender(db_session, now=NOW)
        rec = recommender.recommend_action(anomaly, diagnosis)

        assert isinstance(rec, Recommendation)
        assert rec.anomaly_id == anomaly.id
        assert rec.recommended_action == RecommendedAction.WAIT
        assert rec.timeline == "24_hours"
        assert rec.expected_resolution_time_hours == 24
        assert rec.success_probability >= Decimal("0.50")
        assert rec.urgency == UrgencyLevel.LOW
        # Next check should be NOW + 24h
        assert rec.expected_resolution_time_hours == 24

    def test_merchant_friendly_text_mentions_balance(self, db_session):
        merchant = _merchant(db_session)
        anomaly = _anomaly(db_session, merchant_id=merchant.id)
        diagnosis = _diagnosis(db_session, anomaly_id=anomaly.id, root_cause="insufficient_funds")

        recommender = SettlementActionRecommender(db_session, now=NOW)
        rec = recommender.recommend_action(anomaly, diagnosis)

        text = rec.recommendation_text.lower()
        assert "balance" in text or "funds" in text
        assert "retry" in text or "automatically" in text


class TestRecommendWaitProcessingDelay:
    """Test 2: WAIT action for bank processing delay."""

    def test_recommend_wait_for_processing_delay(self, db_session):
        merchant = _merchant(db_session)
        anomaly = _anomaly(db_session, merchant_id=merchant.id)
        diagnosis = _diagnosis(db_session, anomaly_id=anomaly.id, root_cause="bank_processing_delay")

        recommender = SettlementActionRecommender(db_session, now=NOW)
        rec = recommender.recommend_action(anomaly, diagnosis)

        assert rec.recommended_action == RecommendedAction.WAIT
        assert rec.timeline == "48_hours"
        assert rec.expected_resolution_time_hours == 48
        assert rec.success_probability >= Decimal("0.75")
        assert rec.urgency == UrgencyLevel.LOW

    def test_merchant_friendly_text_mentions_processing(self, db_session):
        merchant = _merchant(db_session)
        anomaly = _anomaly(db_session, merchant_id=merchant.id)
        diagnosis = _diagnosis(db_session, anomaly_id=anomaly.id, root_cause="bank_processing_delay")

        recommender = SettlementActionRecommender(db_session, now=NOW)
        rec = recommender.recommend_action(anomaly, diagnosis)

        text = rec.recommendation_text.lower()
        assert "process" in text or "processing" in text


class TestRecommendEscalateAccountClosed:
    """Test 3: ESCALATE for account closed."""

    def test_recommend_escalate_for_account_closed(self, db_session):
        merchant = _merchant(db_session)
        anomaly = _anomaly(db_session, merchant_id=merchant.id)
        diagnosis = _diagnosis(db_session, anomaly_id=anomaly.id, root_cause="account_closed")

        recommender = SettlementActionRecommender(db_session, now=NOW)
        rec = recommender.recommend_action(anomaly, diagnosis)

        assert rec.recommended_action == RecommendedAction.CONTACT_RAZORPAY
        assert rec.timeline == "immediate"
        assert rec.expected_resolution_time_hours == 2
        assert rec.urgency == UrgencyLevel.CRITICAL
        assert rec.success_probability <= Decimal("0.60")

    def test_merchant_friendly_text_mentions_urgent(self, db_session):
        merchant = _merchant(db_session)
        anomaly = _anomaly(db_session, merchant_id=merchant.id)
        diagnosis = _diagnosis(db_session, anomaly_id=anomaly.id, root_cause="account_closed")

        recommender = SettlementActionRecommender(db_session, now=NOW)
        rec = recommender.recommend_action(anomaly, diagnosis)

        text = rec.recommendation_text.lower()
        assert "immediate" in text or "right away" in text or "contact" in text


class TestRecommendEscalateFraud:
    """Test 4: ESCALATE for fraud block."""

    def test_recommend_escalate_for_fraud(self, db_session):
        merchant = _merchant(db_session)
        anomaly = _anomaly(db_session, merchant_id=merchant.id)
        diagnosis = _diagnosis(db_session, anomaly_id=anomaly.id, root_cause="fraud_block")

        recommender = SettlementActionRecommender(db_session, now=NOW)
        rec = recommender.recommend_action(anomaly, diagnosis)

        assert rec.recommended_action == RecommendedAction.CONTACT_RAZORPAY
        assert rec.timeline == "immediate"
        assert rec.urgency == UrgencyLevel.CRITICAL
        assert rec.success_probability <= Decimal("0.50")

    def test_merchant_friendly_text_mentions_security(self, db_session):
        merchant = _merchant(db_session)
        anomaly = _anomaly(db_session, merchant_id=merchant.id)
        diagnosis = _diagnosis(db_session, anomaly_id=anomaly.id, root_cause="fraud_block")

        recommender = SettlementActionRecommender(db_session, now=NOW)
        rec = recommender.recommend_action(anomaly, diagnosis)

        text = rec.recommendation_text.lower()
        assert "security" in text or "review" in text


class TestTimelineCalculation:
    """Test 5: Timeline → hours mapping is correct."""

    def test_timeline_calculation(self, db_session):
        merchant = _merchant(db_session)

        test_cases = [
            ("insufficient_funds", "24_hours", 24),
            ("bank_processing_delay", "48_hours", 48),
            ("account_closed", "immediate", 2),
            ("fraud_block", "immediate", 2),
        ]

        for root_cause, expected_timeline, expected_hours in test_cases:
            anomaly = _anomaly(db_session, merchant_id=merchant.id)
            diagnosis = _diagnosis(db_session, anomaly_id=anomaly.id, root_cause=root_cause)

            recommender = SettlementActionRecommender(db_session, now=NOW)
            rec = recommender.recommend_action(anomaly, diagnosis)

            assert rec.timeline == expected_timeline, f"Failed for {root_cause}"
            assert rec.expected_resolution_time_hours == expected_hours, f"Failed for {root_cause}"


class TestSuccessProbabilityAdjustment:
    """Test 6: Probability adjusts with diagnosis confidence."""

    def test_success_probability_adjustment(self, db_session):
        merchant = _merchant(db_session)
        anomaly = _anomaly(db_session, merchant_id=merchant.id)

        # High confidence diagnosis
        diag_high = _diagnosis(
            db_session, anomaly_id=anomaly.id,
            root_cause="insufficient_funds", confidence=Decimal("0.95"),
        )
        rec_high = SettlementActionRecommender(db_session, now=NOW).recommend_action(anomaly, diag_high)

        # Low confidence diagnosis
        anomaly2 = _anomaly(db_session, merchant_id=merchant.id)
        diag_low = _diagnosis(
            db_session, anomaly_id=anomaly2.id,
            root_cause="insufficient_funds", confidence=Decimal("0.30"),
        )
        rec_low = SettlementActionRecommender(db_session, now=NOW).recommend_action(anomaly2, diag_low)

        # High confidence should yield higher probability
        assert rec_high.success_probability >= rec_low.success_probability

    def test_probability_bounded(self, db_session):
        """Probability should always be between 0.10 and 0.99."""
        merchant = _merchant(db_session)
        for rc in ["insufficient_funds", "fraud_block", "unknown_error", "bank_processing_delay"]:
            anomaly = _anomaly(db_session, merchant_id=merchant.id)
            diagnosis = _diagnosis(db_session, anomaly_id=anomaly.id, root_cause=rc)

            rec = SettlementActionRecommender(db_session, now=NOW).recommend_action(anomaly, diagnosis)
            assert Decimal("0.10") <= rec.success_probability <= Decimal("0.99"), (
                f"Probability out of bounds for {rc}: {rec.success_probability}"
            )


class TestMerchantFriendlyText:
    """Test 7: Text generation produces meaningful merchant-facing copy."""

    def test_merchant_friendly_text_generation(self, db_session):
        merchant = _merchant(db_session)

        root_causes = [
            "insufficient_funds",
            "bank_processing_delay",
            "account_closed",
            "fraud_block",
            "invalid_account",
            "network_timeout",
            "unknown_error",
        ]

        for rc in root_causes:
            anomaly = _anomaly(db_session, merchant_id=merchant.id)
            diagnosis = _diagnosis(db_session, anomaly_id=anomaly.id, root_cause=rc)

            rec = SettlementActionRecommender(db_session, now=NOW).recommend_action(anomaly, diagnosis)

            text = rec.recommendation_text
            # Should be non-empty and reasonably long
            assert len(text) > 30, f"Text too short for {rc}"
            # Should not contain technical jargon
            assert "40091" not in text, f"Technical code leaked into text for {rc}"
            assert "root_cause" not in text.lower() or "root cause" in text.lower()


class TestUrgencyAssignment:
    """Test 8: Urgency levels are correctly assigned."""

    def test_urgency_level_assignment(self, db_session):
        merchant = _merchant(db_session)

        expected = {
            "insufficient_funds": UrgencyLevel.LOW,
            "bank_processing_delay": UrgencyLevel.LOW,
            "account_closed": UrgencyLevel.CRITICAL,
            "fraud_block": UrgencyLevel.CRITICAL,
            "invalid_account": UrgencyLevel.HIGH,
            "amount_limit_exceeded": UrgencyLevel.MEDIUM,
            "network_timeout": UrgencyLevel.LOW,
            "unknown_error": UrgencyLevel.MEDIUM,
        }

        for rc, expected_urgency in expected.items():
            anomaly = _anomaly(db_session, merchant_id=merchant.id)
            diagnosis = _diagnosis(db_session, anomaly_id=anomaly.id, root_cause=rc)

            rec = SettlementActionRecommender(db_session, now=NOW).recommend_action(anomaly, diagnosis)
            assert rec.urgency == expected_urgency, (
                f"Urgency mismatch for {rc}: expected {expected_urgency}, got {rec.urgency}"
            )


class TestNextCheckTime:
    """Test 9: Next check time = now + timeline hours."""

    def test_next_check_time_calculation(self, db_session):
        merchant = _merchant(db_session)
        anomaly = _anomaly(db_session, merchant_id=merchant.id)
        diagnosis = _diagnosis(db_session, anomaly_id=anomaly.id, root_cause="insufficient_funds")

        recommender = SettlementActionRecommender(db_session, now=NOW)
        rec = recommender.recommend_action(anomaly, diagnosis)

        expected_next = NOW + timedelta(hours=24)
        # The expected_resolution_time_hours encodes the next check
        actual_next = NOW + timedelta(hours=rec.expected_resolution_time_hours)
        assert actual_next == expected_next

    def test_immediate_action_next_check(self, db_session):
        merchant = _merchant(db_session)
        anomaly = _anomaly(db_session, merchant_id=merchant.id)
        diagnosis = _diagnosis(db_session, anomaly_id=anomaly.id, root_cause="account_closed")

        recommender = SettlementActionRecommender(db_session, now=NOW)
        rec = recommender.recommend_action(anomaly, diagnosis)

        expected_next = NOW + timedelta(hours=2)
        actual_next = NOW + timedelta(hours=rec.expected_resolution_time_hours)
        assert actual_next == expected_next


class TestMultipleActionTypes:
    """Test 10: Different root causes produce different recommendations."""

    def test_multiple_action_types(self, db_session):
        merchant = _merchant(db_session)
        root_causes = [
            "insufficient_funds",
            "bank_processing_delay",
            "account_closed",
            "fraud_block",
            "invalid_account",
        ]

        recs = []
        for rc in root_causes:
            anomaly = _anomaly(db_session, merchant_id=merchant.id)
            diagnosis = _diagnosis(db_session, anomaly_id=anomaly.id, root_cause=rc)
            rec = SettlementActionRecommender(db_session, now=NOW).recommend_action(anomaly, diagnosis)
            recs.append((rc, rec))

        # Should have a mix of actions
        actions = {r.recommended_action for _, r in recs}
        assert len(actions) >= 2, "Should have at least 2 different action types"

        # Should have a mix of urgencies
        urgencies = {r.urgency for _, r in recs}
        assert len(urgencies) >= 2, "Should have at least 2 different urgency levels"

        # Should have a mix of timelines
        timelines = {r.timeline for _, r in recs}
        assert len(timelines) >= 2, "Should have at least 2 different timelines"

    def test_settlement_failed_overrides_root_cause(self, db_session):
        """When anomaly_type is SETTLEMENT_FAILED, it should override
        the root_cause-based action."""
        merchant = _merchant(db_session)
        # Even with a low-severity root cause like insufficient_funds,
        # the anomaly type SETTLEMENT_FAILED should force escalation
        anomaly = _anomaly(
            db_session,
            merchant_id=merchant.id,
            anomaly_type=AnomalyType.SETTLEMENT_FAILED,
        )
        diagnosis = _diagnosis(
            db_session,
            anomaly_id=anomaly.id,
            root_cause="insufficient_funds",
        )

        rec = SettlementActionRecommender(db_session, now=NOW).recommend_action(anomaly, diagnosis)

        # SETTLEMENT_FAILED type should force CONTACT_RAZORPAY + immediate
        assert rec.recommended_action == RecommendedAction.CONTACT_RAZORPAY
        assert rec.timeline == "immediate"
        assert rec.urgency == UrgencyLevel.CRITICAL

    def test_recommendation_not_persisted(self, db_session):
        """Recommendation objects should be transient (not in session)."""
        merchant = _merchant(db_session)
        anomaly = _anomaly(db_session, merchant_id=merchant.id)
        diagnosis = _diagnosis(db_session, anomaly_id=anomaly.id, root_cause="insufficient_funds")

        rec = SettlementActionRecommender(db_session, now=NOW).recommend_action(anomaly, diagnosis)
        assert rec.id is not None

        # Should not be persisted
        from src.data.models import Recommendation as RecModel
        assert db_session.get(RecModel, rec.id) is None

    def test_all_decision_tree_entries_produce_valid_recommendations(self, db_session):
        """Every root cause in ACTION_TREE should produce a valid recommendation."""
        merchant = _merchant(db_session)
        recommender = SettlementActionRecommender(db_session, now=NOW)

        for root_cause in ACTION_TREE:
            anomaly = _anomaly(db_session, merchant_id=merchant.id)
            diagnosis = _diagnosis(db_session, anomaly_id=anomaly.id, root_cause=root_cause)

            rec = recommender.recommend_action(anomaly, diagnosis)

            assert isinstance(rec.recommended_action, RecommendedAction)
            assert isinstance(rec.urgency, UrgencyLevel)
            assert Decimal("0.10") <= rec.success_probability <= Decimal("0.99")
            assert rec.timeline in TIMELINE_HOURS
            assert len(rec.recommendation_text) > 0
