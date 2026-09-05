"""
Agent 1: Failure Investigator
Classifies payment failures, assesses recoverability, identifies risk signals.
"""
import random
from .models import (
    FailureType, InvestigationResult, PaymentFailure, Customer,
)


# ─── Failure Code Classification ────────────────────────

TEMPORARY_CODES = {"insufficient_funds", "card_expired", "timeout", "processor_error",
                   "do_not_honor", "temporary_hold", "try_again_later"}
RISKY_CODES = {"fraud_blocked", "high_risk", "suspicious_activity", "velocity_check"}
PERMANENT_CODES = {"invalid_account", "account_closed", "no_such_account",
                   "lost_card", "stolen_card", "expired_card_pickup"}

RECOVERY_PATHS = {
    FailureType.TEMPORARY: ["retry_immediate", "retry_tomorrow", "backup_method",
                            "sms_link", "payment_link", "email_only"],
    FailureType.RISKY: ["sms_link", "email_only"],
    FailureType.PERMANENT: [],
    FailureType.AMBIGUOUS: ["email_only", "sms_link"],
}


def investigate(failure: PaymentFailure, customer: Customer) -> InvestigationResult:
    """
    Deep analysis of a payment failure event.
    Returns classification, recoverability score, risk signals, and recovery paths.
    """
    # 1. Classify failure type
    code = failure.failure_code.lower().replace(" ", "_").replace("-", "_")
    if code in TEMPORARY_CODES:
        ft = FailureType.TEMPORARY
    elif code in RISKY_CODES:
        ft = FailureType.RISKY
    elif code in PERMANENT_CODES:
        ft = FailureType.PERMANENT
    else:
        ft = FailureType.AMBIGUOUS

    # 2. Calculate recoverability score
    recoverability = _score_recoverability(ft, customer, failure)

    # 3. Detect risk signals
    risk_signals = _detect_risk_signals(customer)

    # 4. Identify recovery paths
    paths = RECOVERY_PATHS.get(ft, [])
    if customer.backup_payment_methods > 0 and "backup_method" not in paths:
        paths.append("backup_method")

    # 5. Build reasoning
    reasoning = _build_reasoning(ft, customer, recoverability, risk_signals)

    return InvestigationResult(
        failure_type=ft,
        recoverability_score=recoverability,
        recovery_paths=paths,
        risk_signals=risk_signals,
        confidence=min(0.95, 0.70 + customer.tenure_months * 0.005),
        reasoning=reasoning,
    )


def _score_recoverability(ft: FailureType, customer: Customer,
                          failure: PaymentFailure) -> float:
    base = {
        FailureType.TEMPORARY: 0.75,
        FailureType.RISKY: 0.40,
        FailureType.PERMANENT: 0.10,
        FailureType.AMBIGUOUS: 0.50,
    }[ft]

    # Boosts
    tenure_boost = min(0.10, customer.tenure_months * 0.003)
    success_rate = (customer.payment_success_count /
                    max(1, customer.payment_success_count + 3))
    history_boost = success_rate * 0.10
    backup_boost = 0.05 if customer.backup_payment_methods > 0 else 0
    chargeback_penalty = customer.chargeback_count * 0.03

    score = base + tenure_boost + history_boost + backup_boost - chargeback_penalty
    return max(0.0, min(1.0, round(score, 3)))


def _detect_risk_signals(customer: Customer) -> list:
    signals = []
    if customer.chargeback_count > 3:
        signals.append("high_chargeback_history")
    if customer.complaint_count > 5:
        signals.append("frequent_complaints")
    if customer.device_consistency < 0.70:
        signals.append("device_inconsistency")
    if customer.geography_consistency < 0.80:
        signals.append("geographic_inconsistency")
    if customer.tenure_months < 1:
        signals.append("new_customer")
    return signals


def _build_reasoning(ft, customer, recoverability, risk_signals):
    ft_desc = {
        FailureType.TEMPORARY: "temporary issue",
        FailureType.RISKY: "risky signal detected",
        FailureType.PERMANENT: "permanent failure",
        FailureType.AMBIGUOUS: "ambiguous failure reason",
    }[ft]

    parts = [
        f"Failure classified as {ft.value} ({ft_desc}).",
        f"Customer has {customer.tenure_months}-month tenure, "
        f"${customer.subscription_monthly}/mo subscription.",
        f"{customer.payment_success_count} successful payments previously.",
    ]

    if customer.backup_payment_methods > 0:
        parts.append(f"{customer.backup_payment_methods} backup payment method(s) available.")

    if risk_signals:
        parts.append(f"Risk signals: {', '.join(risk_signals)}.")
    else:
        parts.append("No risk signals detected.")

    parts.append(f"Recoverability score: {recoverability:.0%}.")

    if ft == FailureType.PERMANENT:
        parts.append("Recommendation: Accept loss, do not attempt recovery.")
    elif recoverability > 0.70:
        parts.append("Strong recovery candidate.")
    elif recoverability > 0.40:
        parts.append("Moderate recovery candidate.")
    else:
        parts.append("Weak recovery candidate — proceed with caution.")

    return " ".join(parts)
