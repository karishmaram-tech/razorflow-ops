"""
Agent 4: Economics Agent
Calculates Expected Net Recovery (ENR) for each recovery strategy.
Every decision is economically justified.
"""
from .models import (
    EconomicsResult, Customer, PaymentFailure, PredictionResult,
    RiskAssessment, STRATEGY_COSTS,
)
from .risk import calculate_chargeback_cost


def calculate(
    customer: Customer,
    failure: PaymentFailure,
    prediction: PredictionResult,
    risk: RiskAssessment,
) -> EconomicsResult:
    """
    ENR = P(recovery) × Recoverable_Revenue
          - Strategy_Cost
          - P(chargeback) × Chargeback_Penalty
          - P(additional_churn) × LTV_Loss
          + P(lifetime_extension) × Extension_Value
    """
    recoverable_revenue = failure.amount * 12  # Annual subscription value
    ltv = customer.ltv_estimate

    strategies = {}
    for strat, prob_data in prediction.recovery_probabilities.items():
        prob = prob_data["probability"]
        cost = STRATEGY_COSTS.get(strat, 0.10)

        # Base recovery value
        base_recovery = prob * recoverable_revenue

        # Strategy cost
        strategy_cost = cost

        # Chargeback cost (proportional to risk)
        cb_cost = risk.chargeback_propensity * 25.0

        # Customer friction → incremental churn
        friction = _friction_factor(strat)
        churn_cost = friction * ltv

        # Lifetime extension bonus (recovery handled well)
        lifetime_bonus = 0.05 * ltv if prob > 0.70 else 0.0

        # Complaint cost
        complaint_cost = friction * 0.5 * 30  # $30 per complaint

        enr = (base_recovery
               - strategy_cost
               - cb_cost
               - churn_cost
               + lifetime_bonus
               - complaint_cost)

        roi = enr / cost if cost > 0 else 0

        if enr > 10:
            rec = "EXECUTE"
        elif enr > 0:
            rec = "CONSIDER"
        else:
            rec = "SKIP"

        strategies[strat] = {
            "probability": prob,
            "recoverable_revenue": round(recoverable_revenue, 2),
            "strategy_cost": cost,
            "chargeback_cost": round(cb_cost, 2),
            "churn_cost": round(churn_cost, 2),
            "lifetime_bonus": round(lifetime_bonus, 2),
            "enr": round(enr, 2),
            "roi": round(roi, 1),
            "recommendation": rec,
        }

    # Find best by ENR
    best = max(strategies, key=lambda s: strategies[s]["enr"])
    total_enr = strategies[best]["enr"]

    # Overall recommendation
    if total_enr > 10:
        rec = "EXECUTE"
    elif total_enr > 0:
        rec = "CONSIDER"
    else:
        rec = "SKIP"

    return EconomicsResult(
        strategy_economics=strategies,
        best_strategy_by_economics=best,
        total_enr=round(total_enr, 2),
        recommendation=rec,
    )


def _friction_factor(strategy: str) -> float:
    """How much customer friction does each strategy cause?"""
    friction = {
        "retry_immediate": 0.005,
        "retry_tomorrow": 0.004,
        "backup_method": 0.006,
        "sms_link": 0.008,
        "email_only": 0.003,
        "payment_link": 0.005,
        "support_call": -0.05,  # Negative friction (personal touch helps)
    }
    return friction.get(strategy, 0.005)
