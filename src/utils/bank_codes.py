"""Bank response code mapping for Razorpay settlements and refunds.

Usage::

    from src.utils.bank_codes import get_root_cause_from_code

    info = get_root_cause_from_code("40091")
    print(info["cause"])
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


# ── Bank response codes ────────────────────────────────────────────────────────

BANK_RESPONSE_CODES: dict[str, dict[str, Any]] = {
    # ═══ Settlement / Payout codes ════════════════════════════════════════════
    "40091": {
        "category": "insufficient_funds",
        "description": "Insufficient Funds in Settlement Account",
        "cause": "Merchant's settlement account doesn't have enough balance to receive the payout",
        "merchant_impact": "Settlement delayed; will retry automatically on next cycle",
        "recommended_action": "Ensure settlement account has sufficient balance; check with bank",
        "retryable": True,
    },
    "40092": {
        "category": "account_closed",
        "description": "Account Closed or Frozen",
        "cause": "The beneficiary bank account has been closed, dormant, or frozen by the bank",
        "merchant_impact": "Settlement will fail repeatedly until account is reactivated",
        "recommended_action": "Contact bank to reactivate account or update bank details in Razorpay dashboard",
        "retryable": False,
    },
    "40093": {
        "category": "invalid_account",
        "description": "Invalid Account Number or IFSC",
        "cause": "The account number or IFSC code provided is incorrect or doesn't match",
        "merchant_impact": "Settlement will fail; funds returned to Razorpay within 2-3 working days",
        "recommended_action": "Verify bank details and update in Razorpay dashboard; reinitiate settlement",
        "retryable": False,
    },
    "40094": {
        "category": "bank_processing_delay",
        "description": "Bank Processing Delay",
        "cause": "The receiving bank is experiencing processing delays or high volume",
        "merchant_impact": "Settlement delayed but expected to succeed within 1 working day",
        "recommended_action": "Wait for automatic completion; no manual intervention needed",
        "retryable": True,
    },
    "40095": {
        "category": "amount_limit_exceeded",
        "description": "Amount Exceeds Bank Transfer Limit",
        "cause": "Transfer amount exceeds the per-transaction or daily limit for the payment method",
        "merchant_impact": "Settlement failed; will be retried or needs to be split",
        "recommended_action": "Check bank limits; contact Razorpay support to split large settlements",
        "retryable": True,
    },
    "40096": {
        "category": "duplicate_transaction",
        "description": "Duplicate Settlement Detected",
        "cause": "Bank detected a duplicate transaction and rejected it",
        "merchant_impact": "No funds lost; original settlement may still be processing",
        "recommended_action": "Check settlement dashboard for duplicate status; contact support if unclear",
        "retryable": False,
    },
    "40097": {
        "category": "fraud_block",
        "description": "Transaction Flagged as Fraudulent",
        "cause": "Bank's fraud detection system flagged the transaction for review",
        "merchant_impact": "Settlement frozen pending investigation; may take 5-10 working days",
        "recommended_action": "Contact bank immediately with supporting documents; escalate via Razorpay",
        "retryable": False,
    },
    "40098": {
        "category": "network_timeout",
        "description": "Bank Network Timeout",
        "cause": "Communication timeout between Razorpay's bank partner and the beneficiary bank",
        "merchant_impact": "Settlement status uncertain; will be reconciled within 24 hours",
        "recommended_action": "Wait for reconciliation; check settlement status next working day",
        "retryable": True,
    },
    "40099": {
        "category": "bank_maintenance",
        "description": "Bank System Under Maintenance",
        "cause": "Beneficiary bank's systems are down for scheduled or unscheduled maintenance",
        "merchant_impact": "Settlement delayed until bank systems are back online",
        "recommended_action": "Wait for bank maintenance to complete; settlement will auto-resume",
        "retryable": True,
    },
    "40100": {
        "category": "currency_mismatch",
        "description": "Currency Mismatch",
        "cause": "Settlement currency doesn't match the account's supported currencies",
        "merchant_impact": "Settlement will fail; funds returned to Razorpay",
        "recommended_action": "Update settlement currency to INR or contact support for multi-currency setup",
        "retryable": False,
    },

    # ═══ Refund codes ═════════════════════════════════════════════════════════
    "50001": {
        "category": "refund_rejected_by_bank",
        "description": "Refund Rejected by Beneficiary Bank",
        "cause": "Customer's bank rejected the refund credit",
        "merchant_impact": "Refund failed; funds returned to merchant's Razorpay balance",
        "recommended_action": "Retry refund or contact customer to provide updated bank details",
        "retryable": True,
    },
    "50002": {
        "category": "refund_expired_card",
        "description": "Refund to Expired Card",
        "cause": "Customer's card on file has expired and bank cannot credit the refund",
        "merchant_impact": "Refund failed; needs alternative refund method",
        "recommended_action": "Ask customer for updated card details or process refund via bank transfer",
        "retryable": False,
    },
    "50003": {
        "category": "refund_processing_timeout",
        "description": "Refund Processing Timeout",
        "cause": "Network or system timeout during refund processing",
        "merchant_impact": "Refund status uncertain; will be reconciled within 48 hours",
        "recommended_action": "Wait for reconciliation; refund will auto-complete or fail with clear status",
        "retryable": True,
    },
    "50004": {
        "category": "refund_account_inactive",
        "description": "Customer Account Inactive",
        "cause": "Customer's bank account or wallet is inactive or suspended",
        "merchant_impact": "Refund cannot be credited; funds stay with merchant",
        "recommended_action": "Contact customer to use an active account for refund",
        "retryable": False,
    },
    "50005": {
        "category": "refund_amount_mismatch",
        "description": "Refund Amount Exceeds Original",
        "cause": "Requested refund amount is greater than the original transaction amount",
        "merchant_impact": "Partial refund only; excess amount rejected",
        "recommended_action": "Adjust refund to match or be less than original transaction amount",
        "retryable": False,
    },

    # ═══ Dispute / Chargeback codes ══════════════════════════════════════════
    "60001": {
        "category": "dispute_evidence_expired",
        "description": "Evidence Submission Deadline Passed",
        "cause": "Merchant failed to submit evidence within the dispute resolution window",
        "merchant_impact": "Automatic chargeback; funds debited from merchant account",
        "recommended_action": "File appeal within 15 days with additional evidence",
        "retryable": False,
    },
    "60002": {
        "category": "dispute_invalid_reason",
        "description": "Invalid or Unclear Dispute Reason",
        "cause": "Bank filed a dispute with an unclear or non-standard reason code",
        "merchant_impact": "May delay resolution; requires manual review by Razorpay",
        "recommended_action": "Contact Razorpay support to clarify dispute details and reason code",
        "retryable": False,
    },

    # ═══ Generic / System codes ═══════════════════════════════════════════════
    "90001": {
        "category": "bank_processing_delay",
        "description": "Bank Processing Delay (Generic)",
        "cause": "Bank is taking longer than usual to process the transaction",
        "merchant_impact": "Settlement delayed but will succeed on next retry",
        "recommended_action": "Wait for automatic completion by EOD",
        "retryable": True,
    },
    "90002": {
        "category": "system_error",
        "description": "Internal System Error",
        "cause": "Unexpected error in Razorpay's payment processing system",
        "merchant_impact": "Transaction may be in unknown state; reconciliation required",
        "recommended_action": "Contact Razorpay support with transaction ID for manual resolution",
        "retryable": True,
    },
    "90003": {
        "category": "rate_limit_exceeded",
        "description": "API Rate Limit Exceeded",
        "cause": "Too many requests in a short time window",
        "merchant_impact": "Request rejected; needs to be retried after cooldown",
        "recommended_action": "Implement exponential backoff; retry after 60 seconds",
        "retryable": True,
    },
    "90004": {
        "category": "authentication_failed",
        "description": "Bank Authentication Failed",
        "cause": "Two-factor or step-up authentication failed for the transaction",
        "merchant_impact": "Transaction cannot proceed without proper authentication",
        "recommended_action": "Complete required authentication steps and retry",
        "retryable": False,
    },
    "90005": {
        "category": "compliance_hold",
        "description": "Regulatory Compliance Hold",
        "cause": "Transaction flagged for compliance review (AML/KYC checks)",
        "merchant_impact": "Funds held until compliance clearance; may take 3-7 working days",
        "recommended_action": "Provide requested compliance documents; cooperate with review",
        "retryable": False,
    },

    # ═══ Additional edge-case codes ═══════════════════════════════════════════
    "40101": {
        "category": "bank_account_seized",
        "description": "Bank Account Seized by Authorities",
        "cause": "Beneficiary bank account has been seized or attached by a court or regulatory order",
        "merchant_impact": "Settlement will fail; funds held until legal proceedings resolve",
        "recommended_action": "Contact legal counsel; inform Razorpay support immediately",
        "retryable": False,
    },
    "40102": {
        "category": "ifsc_mismatch",
        "description": "IFSC Code Does Not Match Bank",
        "cause": "The IFSC code provided doesn't correspond to the bank branch holding the account",
        "merchant_impact": "Settlement rejected; funds returned within 2-3 working days",
        "recommended_action": "Verify IFSC from bank statement; update bank details in Razorpay",
        "retryable": False,
    },
    "40103": {
        "category": "beneficiary_details_mismatch",
        "description": "Beneficiary Name Does Not Match Account",
        "cause": "The name on the settlement doesn't match the bank account holder's name",
        "merchant_impact": "Settlement rejected by bank due to name mismatch",
        "recommended_action": "Ensure Razorpay business name matches bank account holder name",
        "retryable": False,
    },
    "40104": {
        "category": "nach_rejection",
        "description": "NACH Mandate Rejection",
        "cause": "National Automated Clearing House mandate rejected by customer's bank",
        "merchant_impact": "Recurring debit failed; customer needs to re-authorize",
        "recommended_action": "Contact customer to re-authorize NACH mandate",
        "retryable": True,
    },
    "50006": {
        "category": "refund_wrong_account",
        "description": "Refund Sent to Wrong Account",
        "cause": "Refund was processed but credited to an incorrect bank account",
        "merchant_impact": "Customer did not receive refund; requires investigation",
        "recommended_action": "Initiate trace with Razorpay; request customer's bank statement as proof",
        "retryable": False,
    },
    "60003": {
        "category": "dispute_won_by_customer",
        "description": "Dispute Ruled in Customer's Favor",
        "cause": "Bank or card network ruled the dispute in favor of the customer",
        "merchant_impact": "Chargeback applied; funds debited from merchant account",
        "recommended_action": "Review evidence submitted; file appeal within 15 days if grounds exist",
        "retryable": False,
    },
    "90006": {
        "category": "settlement_account_verification",
        "description": "Settlement Account Pending Verification",
        "cause": "New bank account requires RBI-mandated verification before credits can be made",
        "merchant_impact": "All settlements paused until verification completes (typically 2-3 days)",
        "recommended_action": "Complete KYC verification via Razorpay dashboard",
        "retryable": True,
    },
    "90007": {
        "category": "holiday_processing_hold",
        "description": "Holiday Processing Hold",
        "cause": "Settlement processing paused due to bank holiday or RBI holiday window",
        "merchant_impact": "Settlement will resume on next working day",
        "recommended_action": "No action required; settlement will auto-resume",
        "retryable": True,
    },
    "99999": {
        "category": "unknown_error",
        "description": "Unknown Error",
        "cause": "Error code not in our mapping; could be a new code or bank-specific issue",
        "merchant_impact": "Uncertain; manual investigation required",
        "recommended_action": "Contact Razorpay support with full error details for investigation",
        "retryable": True,
    },
}


# ── Public API ─────────────────────────────────────────────────────────────────

_UNKNOWN = {
    "category": "unknown_error",
    "description": "Unknown Bank Response Code",
    "cause": "No mapping available for this response code",
    "merchant_impact": "Uncertain impact; requires manual investigation",
    "recommended_action": "Contact Razorpay support with the error code for clarification",
    "retryable": True,
}


def get_root_cause_from_code(code: str) -> dict[str, Any]:
    """Return cause information for a bank response code.

    Falls back to a generic ``unknown_error`` dict if the code is not mapped.

    Parameters
    ----------
    code : str
        The bank response code (e.g. ``"40091"``).

    Returns
    -------
    dict
        Keys: ``category``, ``description``, ``cause``, ``merchant_impact``,
        ``recommended_action``, ``retryable``.
    """
    code_str = str(code).strip()
    info = BANK_RESPONSE_CODES.get(code_str)
    if info is None:
        logger.warning("Unknown bank response code: %s — falling back to generic.", code_str)
        return dict(_UNKNOWN)  # return a copy
    return dict(info)  # return a copy to prevent mutation


def is_retryable(code: str) -> bool:
    """Quick check: can this error be retried automatically?"""
    info = get_root_cause_from_code(code)
    return info.get("retryable", True)


def get_category_counts(codes: list[str]) -> dict[str, int]:
    """Aggregate a list of response codes into category counts.

    Useful for dashboard summaries and anomaly classification.
    """
    counts: dict[str, int] = {}
    for code in codes:
        info = get_root_cause_from_code(code)
        cat = info["category"]
        counts[cat] = counts.get(cat, 0) + 1
    return counts
