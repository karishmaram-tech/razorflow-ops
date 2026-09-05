"""
Agent 3: Risk Assessment Agent
Evaluates chargeback propensity, fraud signals, and operational risk
of recovery attempts.
"""
import math
from .models import (
    RiskAssessment, RiskAction, Customer, PaymentFailure,
    InvestigationResult, PredictionResult,
)


CHARGEBACK_PENALTY = 25.0  # Processor fee per chargeback

# Chargeback rates by customer segment
SEGMENT_CHARGEBACK_BASE = {
    "high_ltv_stable": 0.008,
    "mid_ltv_transient": 0.020,
    "low_ltv_at_risk": 0.050,
}

# Strategy friction factors (higher = more likely to cause complaint/chargeback)
STRATEGY_FRICTION = {
    "retry_immediate": 0.01,
    "retry_tomorrow": 0.008,
    "backup_method": 0.012,
    "sms_link": 0.015,
    "email_only": 0.005,
    "payment_link": 0.010,
    "support_call": 0.003,
}


def assess(
    customer: Customer,
    failure: PaymentFailure,
    investigation: InvestigationResult,
    prediction: PredictionResult,
) -> RiskAssessment:
    """
    Comprehensive risk assessment for recovery attempt.
    """
    segment = customer.segment.value

    # 1. Chargeback propensity
    cb_base = SEGMENT_CHARGEBACK_BASE.get(segment, 0.02)
    cb_history_adj = min(0.10, customer.chargeback_count * 0.02)
    complaint_adj = min(0.05, customer.complaint_count * 0.005)
    chargeback_propensity = min(0.15, cb_base + cb_history_adj + complaint_adj)

    # 2. Fraud probability
    fraud = 0.001  # baseline
    if customer.device_consistency < 0.70:
        fraud += 0.03
    if customer.geography_consistency < 0.80:
        fraud += 0.02
    if customer.tenure_months < 2:
        fraud += 0.01
    fraud = min(0.08, fraud)

    # 3. Operational risk (over-contact)
    operational = 0.0
    if customer.complaint_count > 3:
        operational += 0.02
    if customer.recovery_opt_out:
        operational = 0.50  # huge penalty

    # 4. Aggregate risk score
    total = (chargeback_propensity * 0.50 +
             fraud * 0.30 +
             operational * 0.20)

    # 5. Determine risk action
    if total > 0.15 or fraud > 0.05:
        action = RiskAction.ESCALATE
    elif total > 0.05 or chargeback_propensity > 0.08:
        action = RiskAction.CAUTION
    elif customer.recovery_opt_out:
        action = RiskAction.VETO
    else:
        action = RiskAction.PROCEED

    # 6. Recommend conservative strategy if risky
    recommended = None
    if action in (RiskAction.CAUTION, RiskAction.ESCALATE):
        recommended = "email_only"  # lowest friction

    # 7. Build reasoning
    reasoning = _build_reasoning(
        chargeback_propensity, fraud, operational, total,
        action, customer
    )

    return RiskAssessment(
        chargeback_propensity=round(chargeback_propensity, 4),
        fraud_probability=round(fraud, 4),
        operational_risk=round(operational, 4),
        total_risk_score=round(total, 4),
        risk_action=action,
        recommended_strategy=recommended,
        reasoning=reasoning,
    )


def calculate_chargeback_cost(chargeback_propensity: float) -> float:
    return chargeback_propensity * CHARGEBACK_PENALTY


def _build_reasoning(cb, fraud, op, total, action, customer):
    parts = [
        f"Chargeback propensity: {cb:.1%} "
        f"({'elevated' if cb > 0.05 else 'low'}).",
        f"Fraud probability: {fraud:.2%} "
        f"({'concerning' if fraud > 0.03 else 'negligible'}).",
        f"Operational risk: {op:.2%}.",
        f"Total risk score: {total:.3f}.",
    ]

    if action == RiskAction.PROCEED:
        parts.append("Risk level LOW — safe to proceed with recovery.")
    elif action == RiskAction.CAUTION:
        parts.append("Risk level MODERATE — recommend conservative strategy.")
    elif action == RiskAction.ESCALATE:
        parts.append("Risk level HIGH — escalate to human review.")
    elif action == RiskAction.VETO:
        parts.append("Customer opted out — do not attempt recovery.")

    if customer.chargeback_count > 0:
        parts.append(f"Customer has {customer.chargeback_count} prior chargeback(s).")

    return " ".join(parts)
