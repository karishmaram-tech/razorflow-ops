"""Tests for src/agents/explainability.py — LLM-powered explanations.

Tests run without a real Claude API key — they verify the prompt building,
caching, fallback logic, and response structure.
"""

from __future__ import annotations

import pytest

from src.agents.explainability import (
    ExplanationCache,
    ExplainabilityAgent,
    PROMPT_TEMPLATES,
)


# ══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def agent():
    """Create an ExplainabilityAgent with a dummy API key (will trigger fallback)."""
    return ExplainabilityAgent(api_key="sk-ant-test-key-dummy")


@pytest.fixture
def settlement_context():
    return {
        "amount": "₹50,000",
        "created_at": "2025-06-10 10:00",
        "expected_arrival": "2025-06-13 23:59",
        "status": "pending",
        "root_cause": "bank_processing_delay",
        "confidence": "0.75",
        "hours_late": "48",
    }


@pytest.fixture
def refund_context():
    return {
        "amount": "₹2,000",
        "customer_name": "Rahul Sharma",
        "status": "processing",
        "created_at": "2025-06-12 14:30",
        "root_cause": "bank_processing_delay",
        "bank_response": "Processing",
    }


@pytest.fixture
def dispute_context():
    return {
        "amount": "₹10,000",
        "reason_code": "4855",
        "reason_text": "Goods not received",
        "filed_at": "2025-06-08",
        "evidence_deadline": "2025-06-15",
        "completeness_pct": "66.7",
        "docs_found": "2",
        "docs_needed": "3",
        "win_probability": "78",
    }


@pytest.fixture
def recommendation_context():
    return {
        "anomaly_type": "settlement_delayed",
        "severity": "critical",
        "action": "contact_razorpay",
        "timeline": "immediate",
        "urgency": "critical",
        "success_probability": "50",
        "details": "Settlement is 36 hours overdue",
    }


# ══════════════════════════════════════════════════════════════════════════════
# Explanation Type Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestSettlementDelayExplanation:
    """Test 1: Settlement delay explanation generation."""

    def test_settlement_delay_explanation(self, agent, settlement_context):
        explanation = agent.generate_explanation(
            settlement_context, "settlement_delay_explanation"
        )

        assert isinstance(explanation, str)
        assert len(explanation) > 20
        # Should mention settlement-related content
        assert any(word in explanation.lower() for word in ("settlement", "delay", "bank"))


class TestRefundIssueExplanation:
    """Test 2: Refund issue explanation generation."""

    def test_refund_issue_explanation(self, agent, refund_context):
        explanation = agent.generate_explanation(
            refund_context, "refund_issue_explanation"
        )

        assert isinstance(explanation, str)
        assert len(explanation) > 20
        # Should mention refund-related content
        assert any(word in explanation.lower() for word in ("refund", "processing", "bank"))


class TestDisputeEvidenceExplanation:
    """Test 3: Dispute evidence explanation generation."""

    def test_dispute_evidence_explanation(self, agent, dispute_context):
        explanation = agent.generate_explanation(
            dispute_context, "dispute_evidence_explanation"
        )

        assert isinstance(explanation, str)
        assert len(explanation) > 20
        # Should mention dispute/evidence content
        assert any(word in explanation.lower() for word in ("dispute", "evidence", "upload"))


class TestRecommendationExplanation:
    """Test 4: Recommendation explanation generation."""

    def test_recommendation_explanation(self, agent, recommendation_context):
        explanation = agent.generate_explanation(
            recommendation_context, "recommendation_explanation"
        )

        assert isinstance(explanation, str)
        assert len(explanation) > 20


# ══════════════════════════════════════════════════════════════════════════════
# Caching Tests
# ══════════════════════════════════════════════════════════════════════════════


class TestCaching:
    """Test 5: Cache hit avoids duplicate generation."""

    def test_caching_works(self, agent, settlement_context):
        # First call — generates explanation
        explanation1 = agent.generate_explanation(
            settlement_context, "settlement_delay_explanation"
        )

        # Second call with same context — should hit cache
        explanation2 = agent.generate_explanation(
            settlement_context, "settlement_delay_explanation"
        )

        assert explanation1 == explanation2

    def test_different_context_different_cache(self, agent):
        ctx1 = {"amount": "₹1000", "status": "pending"}
        ctx2 = {"amount": "₹5000", "status": "failed"}

        e1 = agent.generate_explanation(ctx1, "settlement_delay_explanation")
        e2 = agent.generate_explanation(ctx2, "settlement_delay_explanation")

        # Different contexts should produce different cache keys
        # (but may produce same fallback text — that's OK)
        key1 = agent._cache_key(ctx1, "settlement_delay_explanation")
        key2 = agent._cache_key(ctx2, "settlement_delay_explanation")
        assert key1 != key2

    def test_cache_expiry(self):
        """Cache entries should expire after TTL."""
        cache = ExplanationCache(ttl_seconds=0)  # instant expiry
        cache.set("test_key", "test_value")
        result = cache.get("test_key")
        assert result is None  # expired

    def test_cache_eviction(self):
        """Cache should evict oldest when full."""
        cache = ExplanationCache(max_size=3)
        for i in range(5):
            cache.set(f"key_{i}", f"value_{i}")
        # Only last 3 should remain
        assert cache.get("key_0") is None
        assert cache.get("key_1") is None
        assert cache.get("key_4") == "value_4"


# ══════════════════════════════════════════════════════════════════════════════
# API Error Handling
# ══════════════════════════════════════════════════════════════════════════════


class TestAPIErrorHandling:
    """Test 6: Graceful fallback when Claude API is unavailable."""

    def test_api_error_handling(self, agent):
        """Invalid API key should trigger fallback, not crash."""
        ctx = {"amount": "₹5000", "status": "failed"}
        explanation = agent.generate_explanation(ctx, "settlement_delay_explanation")

        # Should return fallback text, not raise
        assert isinstance(explanation, str)
        assert len(explanation) > 10

    def test_unknown_explanation_type(self, agent):
        """Unknown type should produce a generic explanation."""
        ctx = {"issue": "something went wrong"}
        explanation = agent.generate_explanation(ctx, "unknown_type_xyz")

        assert isinstance(explanation, str)
        assert len(explanation) > 10


# ══════════════════════════════════════════════════════════════════════════════
# Explanation Quality
# ══════════════════════════════════════════════════════════════════════════════


class TestExplanationQuality:
    """Test 7: Explanations are merchant-friendly."""

    def test_explanation_quality(self, agent, settlement_context, refund_context, dispute_context, recommendation_context):
        """All explanation types should produce readable, non-empty text."""
        contexts = [
            ("settlement_delay_explanation", settlement_context),
            ("refund_issue_explanation", refund_context),
            ("dispute_evidence_explanation", dispute_context),
            ("recommendation_explanation", recommendation_context),
        ]

        for exp_type, ctx in contexts:
            explanation = agent.generate_explanation(ctx, exp_type)

            assert len(explanation) > 20, f"Too short for {exp_type}"
            # Should not contain raw technical keys
            assert "root_cause" not in explanation.lower(), f"Jargon leaked for {exp_type}"
            assert "anomaly_type" not in explanation.lower(), f"Jargon leaked for {exp_type}"

    def test_prompt_templates_exist(self):
        """All expected prompt templates should be defined."""
        expected = [
            "settlement_delay_explanation",
            "refund_issue_explanation",
            "dispute_evidence_explanation",
            "recommendation_explanation",
        ]
        for name in expected:
            assert name in PROMPT_TEMPLATES, f"Missing template: {name}"

    def test_format_context(self, agent):
        """Context formatting should produce readable output."""
        ctx = {
            "amount": "₹5000",
            "items": ["a", "b", "c"],
            "nested": {"key": "value"},
        }
        formatted = agent._format_context(ctx)
        assert "₹5000" in formatted
        assert "a, b, c" in formatted
        assert "key" in formatted
