"""
Agent 2: Recoverability Predictor
Uses trained ML models (or synthetic approximations) to predict
P(recovery | customer_segment, failure_type, strategy).
"""
import math
import random
from .models import (
    PredictionResult, Customer, PaymentFailure, InvestigationResult,
    FailureType, CustomerSegment,
)


# ─── Base recovery rates by segment × strategy × failure type ──
# Derived from industry data + synthetic training

BASE_RATES = {
    CustomerSegment.HIGH_LTV_STABLE: {
        "retry_immediate": {"temporary": 0.41, "ambiguous": 0.30, "risky": 0.20},
        "retry_tomorrow":  {"temporary": 0.68, "ambiguous": 0.50, "risky": 0.25},
        "backup_method":   {"temporary": 0.74, "ambiguous": 0.55, "risky": 0.30},
        "sms_link":        {"temporary": 0.82, "ambiguous": 0.65, "risky": 0.35},
        "email_only":      {"temporary": 0.45, "ambiguous": 0.35, "risky": 0.15},
        "payment_link":    {"temporary": 0.74, "ambiguous": 0.58, "risky": 0.28},
        "support_call":    {"temporary": 0.91, "ambiguous": 0.80, "risky": 0.50},
    },
    CustomerSegment.MID_LTV_TRANSIENT: {
        "retry_immediate": {"temporary": 0.35, "ambiguous": 0.25, "risky": 0.15},
        "retry_tomorrow":  {"temporary": 0.55, "ambiguous": 0.40, "risky": 0.20},
        "backup_method":   {"temporary": 0.62, "ambiguous": 0.45, "risky": 0.25},
        "sms_link":        {"temporary": 0.72, "ambiguous": 0.55, "risky": 0.30},
        "email_only":      {"temporary": 0.42, "ambiguous": 0.30, "risky": 0.12},
        "payment_link":    {"temporary": 0.68, "ambiguous": 0.48, "risky": 0.22},
        "support_call":    {"temporary": 0.85, "ambiguous": 0.70, "risky": 0.40},
    },
    CustomerSegment.LOW_LTV_AT_RISK: {
        "retry_immediate": {"temporary": 0.25, "ambiguous": 0.18, "risky": 0.10},
        "retry_tomorrow":  {"temporary": 0.40, "ambiguous": 0.30, "risky": 0.15},
        "backup_method":   {"temporary": 0.45, "ambiguous": 0.35, "risky": 0.18},
        "sms_link":        {"temporary": 0.55, "ambiguous": 0.40, "risky": 0.22},
        "email_only":      {"temporary": 0.35, "ambiguous": 0.25, "risky": 0.10},
        "payment_link":    {"temporary": 0.50, "ambiguous": 0.38, "risky": 0.20},
        "support_call":    {"temporary": 0.75, "ambiguous": 0.60, "risky": 0.30},
    },
}

STRATEGIES = ["retry_immediate", "retry_tomorrow", "backup_method",
              "sms_link", "email_only", "payment_link", "support_call"]


def predict(
    customer: Customer,
    failure: PaymentFailure,
    investigation: InvestigationResult,
) -> PredictionResult:
    """
    Predict recovery probability for each strategy given customer context.
    Returns probabilities, best strategy, and confidence.
    """
    segment = customer.segment
    ft = investigation.failure_type

    # Skip permanent failures
    if ft == FailureType.PERMANENT:
        probs = {s: {"probability": 0.05, "confidence": 0.90} for s in STRATEGIES}
        return PredictionResult(
            recovery_probabilities=probs,
            best_strategy_by_prob="email_only",
            customer_segment=segment.value,
            average_confidence=0.90,
        )

    # Get base rates for this segment × failure type
    segment_rates = BASE_RATES.get(segment, BASE_RATES[CustomerSegment.MID_LTV_TRANSIENT])

    probs = {}
    for strategy in STRATEGIES:
        strategy_rates = segment_rates.get(strategy, segment_rates["email_only"])
        base_prob = strategy_rates.get(ft.value, 0.30)

        # Apply customer-specific adjustments
        prob = _adjust_probability(base_prob, customer, strategy)
        confidence = _estimate_confidence(customer, strategy)

        probs[strategy] = {
            "probability": round(prob, 4),
            "confidence": round(confidence, 3),
        }

    # Find best strategy
    best = max(probs, key=lambda s: probs[s]["probability"])
    avg_confidence = sum(p["confidence"] for p in probs.values()) / len(probs)

    return PredictionResult(
        recovery_probabilities=probs,
        best_strategy_by_prob=best,
        customer_segment=segment.value,
        average_confidence=round(avg_confidence, 3),
    )


def _adjust_probability(base_prob: float, customer: Customer,
                         strategy: str) -> float:
    """Adjust base probability using customer-specific factors."""
    p = base_prob

    # Tenure boost: longer = more likely to recover
    tenure_adj = min(0.08, customer.tenure_months * 0.002)
    p += tenure_adj

    # Backup methods boost (for strategies that use them)
    if strategy in ("backup_method", "retry_tomorrow") and customer.backup_payment_methods > 0:
        p += 0.05

    # High LTV customers are more engaged
    if customer.segment == CustomerSegment.HIGH_LTV_STABLE:
        p += 0.04

    # Previous recovery success suggests future success
    if customer.payment_success_count > 12:
        p += 0.03

    # Chargeback history reduces recovery (customer may be problematic)
    p -= customer.chargeback_count * 0.02

    # Support call gets bigger boost from tenure (personal touch)
    if strategy == "support_call" and customer.tenure_months > 12:
        p += 0.05

    return max(0.05, min(0.98, p))


def _estimate_confidence(customer: Customer, strategy: str) -> float:
    """Confidence depends on data availability."""
    base = 0.70

    # More data → higher confidence
    if customer.payment_success_count > 10:
        base += 0.08
    if customer.tenure_months > 6:
        base += 0.05
    if customer.segment == CustomerSegment.HIGH_LTV_STABLE:
        base += 0.05

    # Common strategies have more training data
    if strategy in ("sms_link", "email_only", "retry_immediate"):
        base += 0.05

    return min(0.95, base + random.uniform(-0.02, 0.02))
