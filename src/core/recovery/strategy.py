"""
Agent 5: Strategy Agent
Integrates all agent outputs. Resolves conflicts. Makes the final decision.
"""
from .models import (
    StrategyDecision, RecoveryAction, Customer, PaymentFailure,
    InvestigationResult, PredictionResult, RiskAssessment,
    EconomicsResult, STRATEGY_COSTS,
)


def decide(
    customer: Customer,
    failure: PaymentFailure,
    investigation: InvestigationResult,
    prediction: PredictionResult,
    risk: RiskAssessment,
    economics: EconomicsResult,
) -> StrategyDecision:
    """
    Make the final recovery decision by integrating all agent inputs.
    """
    # ─── Hard stops ──────────────────────────────────────

    if investigation.failure_type.value == "permanent":
        return _skip("permanent_failure", "Failure is permanent — not recoverable",
                     investigation, prediction, risk, economics)

    if investigation.recoverability_score < 0.25:
        return _skip("low_recoverability",
                     f"Recoverability {investigation.recoverability_score:.0%} is below threshold",
                     investigation, prediction, risk, economics)

    if risk.risk_action.value == "VETO":
        return _skip("customer_opt_out", "Customer opted out of recovery",
                     investigation, prediction, risk, economics)

    if risk.risk_action.value == "ESCALATE":
        return _escalate("high_risk",
                         "Risk agent flagged for human review",
                         investigation, prediction, risk, economics)

    if economics.recommendation == "SKIP":
        return _skip("negative_economics",
                     f"Best ENR is ${economics.total_enr:.2f} — not economically viable",
                     investigation, prediction, risk, economics)

    # ─── Strategy selection ──────────────────────────────

    # Try best-by-economics first (revenue-optimal)
    econ_best = economics.best_strategy_by_economics
    pred_best = prediction.best_strategy_by_prob

    # Check for conflicts
    conflict = None
    if econ_best != pred_best:
        conflict = {
            "type": "strategy_disagreement",
            "economics_prefers": econ_best,
            "predictor_prefers": pred_best,
        }

    # Risk may constrain strategy
    if risk.risk_action.value == "CAUTION" and risk.recommended_strategy:
        # Downgrade to conservative strategy
        selected = risk.recommended_strategy
        conflict = conflict or {}
        conflict = {
            "type": "risk_override",
            "original_preference": econ_best,
            "risk_constrained_to": selected,
        }
    else:
        selected = econ_best

    # ─── Calculate confidence ────────────────────────────

    agent_confidences = [
        investigation.confidence,
        prediction.average_confidence,
        0.95,  # risk agent confidence (rule-based, high)
        0.90,  # economics confidence (deterministic)
    ]
    overall_confidence = sum(agent_confidences) / len(agent_confidences)

    # ─── Build execution plan ────────────────────────────

    timing = _determine_timing(selected, investigation)
    communication = _build_communication(selected, customer)
    fallback = _find_fallback(selected, economics)

    execution_plan = {
        "primary_action": selected,
        "strategy": selected,
        "timing": timing,
        "communication": communication,
        "fallback_action": fallback,
        "limits": {
            "max_retry_count": 2,
            "retry_spacing": "24h",
            "max_total_communications": 2,
            "max_spend": min(0.50, customer.subscription_monthly * 0.01),
        },
        "success_criteria": {
            "payment_received": True,
            "customer_complaint": False,
            "chargeback_filed": False,
        },
    }

    # ─── Build reasoning ────────────────────────────────

    strategy_data = economics.strategy_economics.get(selected, {})
    reasoning = {
        "why_this_action": (
            f"Optimal economic outcome (ENR=${strategy_data.get('enr', 0):.2f}, "
            f"ROI={strategy_data.get('roi', 0):.0f}x) with acceptable risk"
        ),
        "agent_inputs": {
            "investigator": investigation.reasoning,
            "predictor": (
                f"Strategy {selected} has "
                f"{prediction.recovery_probabilities.get(selected, {}).get('probability', 0):.0%} "
                f"predicted success"
            ),
            "risk": risk.reasoning,
            "economics": (
                f"ENR=${strategy_data.get('enr', 0):.2f}, "
                f"ROI={strategy_data.get('roi', 0):.0f}x"
            ),
        },
        "conflict": conflict,
    }

    return StrategyDecision(
        action=RecoveryAction.EXECUTE_RECOVERY,
        strategy=selected,
        timing=timing,
        communication=communication,
        fallback_action=fallback,
        confidence_score=round(overall_confidence, 3),
        execution_plan=execution_plan,
        reasoning=reasoning,
    )


def _determine_timing(strategy, investigation):
    if strategy == "retry_immediate":
        return "immediate"
    elif strategy == "retry_tomorrow":
        return "24h_delay"
    elif strategy in ("sms_link", "payment_link"):
        return "within_1_hour"
    elif strategy == "email_only":
        return "within_4_hours"
    elif strategy == "support_call":
        return "within_2_hours"
    return "within_1_hour"


def _build_communication(strategy, customer):
    name = customer.first_name if hasattr(customer, 'first_name') else "there"
    amount = customer.subscription_monthly

    templates = {
        "sms_link": (
            f"Hi {name}, your ${amount:.2f} payment needs a quick update. "
            f"Click here to complete it: [LINK]. Takes 30 seconds."
        ),
        "email_only": (
            f"We noticed your ${amount:.2f} payment couldn't be processed. "
            f"No worries — update your payment method here: [LINK]"
        ),
        "payment_link": (
            f"Hi {name}, here's a direct link to complete your ${amount:.2f} payment: [LINK]"
        ),
        "retry_immediate": "Automatic retry — no customer communication needed",
        "retry_tomorrow": "Automatic retry tomorrow — no communication needed",
        "backup_method": "Automatic retry with backup payment method",
        "support_call": f"Personal support call to help resolve ${amount:.2f} payment",
    }
    return templates.get(strategy, "Recovery attempt in progress")


def _find_fallback(selected, economics):
    # Pick the next-best strategy by ENR
    ranked = sorted(
        economics.strategy_economics.items(),
        key=lambda x: x[1]["enr"],
        reverse=True,
    )
    for strat, data in ranked:
        if strat != selected and data["recommendation"] != "SKIP":
            return strat
    return None


def _skip(reason, text, inv, pred, risk, econ):
    return StrategyDecision(
        action=RecoveryAction.SKIP,
        strategy="none",
        timing="none",
        communication="none",
        fallback_action=None,
        confidence_score=0.0,
        execution_plan={"action": "skip", "reason": reason},
        reasoning={
            "why_skip": text,
            "agent_inputs": {
                "investigator": inv.reasoning if inv else "",
                "risk": risk.reasoning if risk else "",
                "economics": econ.recommendation if econ else "",
            },
        },
    )


def _escalate(reason, text, inv, pred, risk, econ):
    return StrategyDecision(
        action=RecoveryAction.ESCALATE_TO_HUMAN,
        strategy="human_review",
        timing="immediate",
        communication="none — awaiting human",
        fallback_action=None,
        confidence_score=0.5,
        execution_plan={"action": "escalate", "reason": reason},
        reasoning={
            "why_escalate": text,
            "agent_inputs": {
                "investigator": inv.reasoning if inv else "",
                "risk": risk.reasoning if risk else "",
                "economics": econ.total_enr if econ else 0,
            },
        },
    )
