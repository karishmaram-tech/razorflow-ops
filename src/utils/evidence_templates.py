"""Dispute evidence templates — reason-code → evidence requirements mapping.

Provides the evidence checklist and historical win rates for every major
Visa/Mastercard/RuPay dispute reason code encountered by Razorpay merchants.

Usage::

    from src.utils.evidence_templates import get_evidence_requirements

    req = get_evidence_requirements("4855")
    print(req["avg_win_rate"])  # 0.92
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


# ── Evidence type definitions ──────────────────────────────────────────────────

DISPUTE_EVIDENCE_TEMPLATES: dict[str, dict[str, Any]] = {
    # ═══ Goods / Services ═════════════════════════════════════════════════════
    "4855": {
        "reason_text": "Goods/Services Not Received",
        "required_evidence": [
            {
                "type": "proof_of_shipment",
                "required": True,
                "examples": ["shipping_label", "carrier_confirmation", "dispatch_receipt"],
            },
            {
                "type": "proof_of_delivery",
                "required": True,
                "examples": ["delivery_photo", "signature_confirmation", "tracking_url", "delivery_receipt"],
            },
            {
                "type": "customer_communication",
                "required": True,
                "examples": ["email_confirmation", "whatsapp_chat", "support_ticket", "sms_confirmation"],
            },
            {
                "type": "invoice",
                "required": False,
                "examples": ["receipt", "order_confirmation", "tax_invoice"],
            },
        ],
        "avg_win_rate": 0.92,
        "typical_timeline_days": 45,
    },

    "4841": {
        "reason_text": "Cancelled/Recurring Transaction",
        "required_evidence": [
            {
                "type": "cancellation_proof",
                "required": True,
                "examples": ["cancellation_email", "refund_confirmation", "merchant_acknowledgement"],
            },
            {
                "type": "customer_communication",
                "required": True,
                "examples": ["email_request", "support_chat", "call_log"],
            },
            {
                "type": "terms_of_service",
                "required": False,
                "examples": ["subscription_terms", "auto_renewal_policy"],
            },
        ],
        "avg_win_rate": 0.65,
        "typical_timeline_days": 30,
    },

    "4846": {
        "reason_text": "Credit Not Processed",
        "required_evidence": [
            {
                "type": "refund_proof",
                "required": True,
                "examples": ["refund_confirmation", "bank_credit_advice", "settlement_proof"],
            },
            {
                "type": "customer_communication",
                "required": True,
                "examples": ["refund_notification_email", "bank_statement_credit"],
            },
        ],
        "avg_win_rate": 0.88,
        "typical_timeline_days": 30,
    },

    "4849": {
        "reason_text": "Unauthorized Use of Account",
        "required_evidence": [
            {
                "type": "customer_communication",
                "required": True,
                "examples": ["email_confirmation", "purchase_acknowledgement", "delivery_confirmation"],
            },
            {
                "type": "auth_proof",
                "required": True,
                "examples": ["3d_secure_log", "avs_match", "cvv_match", "ip_address_log", "device_fingerprint"],
            },
            {
                "type": "refund_proof",
                "required": False,
                "examples": ["prior refund_record", "dispute_history"],
            },
        ],
        "avg_win_rate": 0.45,
        "typical_timeline_days": 45,
    },

    "4853": {
        "reason_text": "Not as Described / Defective",
        "required_evidence": [
            {
                "type": "product_description",
                "required": True,
                "examples": ["product_listing", "description_page", "screenshots", "catalog"],
            },
            {
                "type": "customer_communication",
                "required": True,
                "examples": ["complaint_chat", "return_request", "quality_dispute"],
            },
            {
                "type": "inspection_report",
                "required": False,
                "examples": ["quality_check_report", "photo_evidence", "video_unboxing"],
            },
        ],
        "avg_win_rate": 0.55,
        "typical_timeline_days": 45,
    },

    "4854": {
        "reason_text": "Not as Described (Credit Card)",
        "required_evidence": [
            {
                "type": "product_listing",
                "required": True,
                "examples": ["website_listing", "invoice_description", "agreed_terms"],
            },
            {
                "type": "return_policy",
                "required": True,
                "examples": ["return_policy_page", "refund_terms"],
            },
        ],
        "avg_win_rate": 0.52,
        "typical_timeline_days": 45,
    },

    "4863": {
        "reason_text": "Cardholder Does Not Recognise Transaction",
        "required_evidence": [
            {
                "type": "receipt",
                "required": True,
                "examples": ["transaction_receipt", "order_confirmation", "merchant_descriptor_info"],
            },
            {
                "type": "proof_of_delivery",
                "required": True,
                "examples": ["delivery_confirmation", "service_activation_record"],
            },
            {
                "type": "customer_communication",
                "required": True,
                "examples": ["purchase_email", "account_creation_date", "login_history"],
            },
        ],
        "avg_win_rate": 0.82,
        "typical_timeline_days": 30,
    },

    # ═══ Amount Disputes ══════════════════════════════════════════════════════
    "4871": {
        "reason_text": "Incorrect Transaction Amount",
        "required_evidence": [
            {
                "type": "receipt",
                "required": True,
                "examples": ["original_invoice", "agreed_amount_proof", "price_screenshot"],
            },
            {
                "type": "terms_of_service",
                "required": True,
                "examples": ["pricing_page", "service_agreement", "terms_checkout"],
            },
            {
                "type": "customer_communication",
                "required": False,
                "examples": ["agreed_price_email", "chat_confirmation"],
            },
        ],
        "avg_win_rate": 0.78,
        "typical_timeline_days": 30,
    },

    "4877": {
        "reason_text": "Late Presentment",
        "required_evidence": [
            {
                "type": "timeline_proof",
                "required": True,
                "examples": ["transaction_timestamp", "processing_log", "batch_record"],
            },
            {
                "type": "merchant_mitigation",
                "required": True,
                "examples": ["settlement_schedule", "bank_processing_proof"],
            },
        ],
        "avg_win_rate": 0.35,
        "typical_timeline_days": 30,
    },

    "4899": {
        "reason_text": "Quasi-Cash Transaction Dispute",
        "required_evidence": [
            {
                "type": "transaction_proof",
                "required": True,
                "examples": ["transaction_details", "service_description"],
            },
            {
                "type": "terms_of_service",
                "required": True,
                "examples": ["acceptable_use_policy", "quasi_cash_disclosure"],
            },
        ],
        "avg_win_rate": 0.42,
        "typical_timeline_days": 45,
    },

    # ═══ Fraud-related ════════════════════════════════════════════════════════
    "10.1": {
        "reason_text": "EMV Liability Shift Counterfeit Fraud",
        "required_evidence": [
            {
                "type": "auth_proof",
                "required": True,
                "examples": ["emv_chip_log", "pin_verification", "terminal_record"],
            },
            {
                "type": "transaction_proof",
                "required": True,
                "examples": ["transaction_log", "terminal_id", "merchant_id"],
            },
        ],
        "avg_win_rate": 0.30,
        "typical_timeline_days": 60,
    },

    "10.2": {
        "reason_text": "EMV Liability Shift Non-Counterfeit Fraud",
        "required_evidence": [
            {
                "type": "auth_proof",
                "required": True,
                "examples": ["chip_card_record", "terminal_compliance_proof"],
            },
        ],
        "avg_win_rate": 0.32,
        "typical_timeline_days": 60,
    },

    "10.3": {
        "reason_text": "Other Fraud (Card-Absent Environment)",
        "required_evidence": [
            {
                "type": "auth_proof",
                "required": True,
                "examples": ["3d_secure_log", "avs_result", "cvv_match", "ip_geolocation"],
            },
            {
                "type": "customer_communication",
                "required": True,
                "examples": ["account_login_history", "device_trusted_list", "otp_record"],
            },
            {
                "type": "delivery_proof",
                "required": False,
                "examples": ["delivery_to_billing_address", "signature_match"],
            },
        ],
        "avg_win_rate": 0.38,
        "typical_timeline_days": 60,
    },

    "10.4": {
        "reason_text": "Other Fraud (Non-Card)",
        "required_evidence": [
            {
                "type": "transaction_proof",
                "required": True,
                "examples": ["transaction_context", "authorization_record"],
            },
            {
                "type": "customer_communication",
                "required": True,
                "examples": ["agreement_proof", "consent_record"],
            },
        ],
        "avg_win_rate": 0.40,
        "typical_timeline_days": 45,
    },

    # ═══ Processing errors ════════════════════════════════════════════════════
    "4807": {
        "reason_text": "Warning Against Acceptance",
        "required_evidence": [
            {
                "type": "merchant_mitigation",
                "required": True,
                "examples": ["fraud_alert_response", "verification_steps_taken", "risk_assessment"],
            },
            {
                "type": "transaction_proof",
                "required": True,
                "examples": ["transaction_log", "auth_code", "settlement_record"],
            },
            {
                "type": "customer_communication",
                "required": False,
                "examples": ["fraud_notification", "bank_alert_response"],
            },
        ],
        "avg_win_rate": 0.48,
        "typical_timeline_days": 30,
    },

    "4808": {
        "reason_text": "Authorisation-Related Complaint",
        "required_evidence": [
            {
                "type": "auth_proof",
                "required": True,
                "examples": ["auth_code", "approval_record", "bank_authorisation_log"],
            },
            {
                "type": "transaction_proof",
                "required": True,
                "examples": ["transaction_receipt", "settlement_record"],
            },
        ],
        "avg_win_rate": 0.72,
        "typical_timeline_days": 30,
    },

    "4812": {
        "reason_text": "Late Presentment (Alt Code)",
        "required_evidence": [
            {
                "type": "timeline_proof",
                "required": True,
                "examples": ["settlement_timestamp", "batch_processing_log"],
            },
        ],
        "avg_win_rate": 0.33,
        "typical_timeline_days": 30,
    },

    "4842": {
        "reason_text": "Duplicate Processing",
        "required_evidence": [
            {
                "type": "transaction_proof",
                "required": True,
                "examples": ["single_charge_proof", "batch_dedup_log", "transaction_ids"],
            },
            {
                "type": "refund_proof",
                "required": False,
                "examples": ["duplicate_refund", "credit_memo"],
            },
        ],
        "avg_win_rate": 0.90,
        "typical_timeline_days": 30,
    },

    "4860": {
        "reason_text": "Services Not Rendered",
        "required_evidence": [
            {
                "type": "proof_of_delivery",
                "required": True,
                "examples": ["service_activation_date", "usage_log", "access_record"],
            },
            {
                "type": "terms_of_service",
                "required": True,
                "examples": ["service_agreement", "delivery_timeline", "cancellation_policy"],
            },
        ],
        "avg_win_rate": 0.70,
        "typical_timeline_days": 45,
    },

    "4862": {
        "reason_text": "Recurring Transaction Dispute",
        "required_evidence": [
            {
                "type": "terms_of_service",
                "required": True,
                "examples": ["subscription_terms", "auto_renewal_consent", "pricing_page"],
            },
            {
                "type": "cancellation_proof",
                "required": False,
                "examples": ["cancellation_log", "unsubscribe_record"],
            },
            {
                "type": "customer_communication",
                "required": True,
                "examples": ["signup_email", "renewal_notification", "account_dashboard"],
            },
        ],
        "avg_win_rate": 0.75,
        "typical_timeline_days": 30,
    },

    # ═══ RuPay / India-specific ════════════════════════════════════════════════
    "4867": {
        "reason_text": "Other Fraud",
        "required_evidence": [
            {
                "type": "transaction_proof",
                "required": True,
                "examples": ["transaction_context", "authorization_record", "risk_score"],
            },
            {
                "type": "auth_proof",
                "required": True,
                "examples": ["3d_secure_log", "otp_verification", "device_fingerprint"],
            },
            {
                "type": "customer_communication",
                "required": False,
                "examples": ["fraud_report", "account_activity_log"],
            },
        ],
        "avg_win_rate": 0.35,
        "typical_timeline_days": 60,
    },

    "RUPAY_CHARGEBACK": {
        "reason_text": "RuPay Generic Chargeback",
        "required_evidence": [
            {
                "type": "receipt",
                "required": True,
                "examples": ["transaction_receipt", "order_details"],
            },
            {
                "type": "customer_communication",
                "required": True,
                "examples": ["communication_log", "support_ticket"],
            },
        ],
        "avg_win_rate": 0.60,
        "typical_timeline_days": 45,
    },

    "UPI_DISPUTE": {
        "reason_text": "UPI Transaction Dispute",
        "required_evidence": [
            {
                "type": "upi_proof",
                "required": True,
                "examples": ["upi_transaction_id", "vpa_details", "bank_reference"],
            },
            {
                "type": "customer_communication",
                "required": True,
                "examples": ["consent_proof", "transaction_context"],
            },
        ],
        "avg_win_rate": 0.55,
        "typical_timeline_days": 30,
    },

    "NPCI_ARBITRATION": {
        "reason_text": "NPCI Arbitration Dispute",
        "required_evidence": [
            {
                "type": "transaction_proof",
                "required": True,
                "examples": ["arbitration_notice", "transaction_details", "settlement_record"],
            },
            {
                "type": "terms_of_service",
                "required": True,
                "examples": ["merchant_agreement", "npci_guidelines_compliance"],
            },
            {
                "type": "customer_communication",
                "required": False,
                "examples": ["prior_resolution_attempt", "support_history"],
            },
        ],
        "avg_win_rate": 0.50,
        "typical_timeline_days": 60,
    },
}


# ── Public API ─────────────────────────────────────────────────────────────────

_NO_TEMPLATE: dict[str, Any] = {
    "reason_text": "Unknown Reason Code",
    "required_evidence": [
        {"type": "receipt", "required": True, "examples": ["transaction_receipt", "order_confirmation"]},
        {"type": "customer_communication", "required": True, "examples": ["email", "chat", "ticket"]},
        {"type": "proof_of_delivery", "required": True, "examples": ["tracking", "signature", "photo"]},
        {"type": "terms_of_service", "required": False, "examples": ["policy_page", "tos"]},
    ],
    "avg_win_rate": 0.50,
    "typical_timeline_days": 45,
}


def get_evidence_requirements(reason_code: str) -> dict[str, Any]:
    """Return the evidence template for a dispute reason code.

    Falls back to a generic template if the code is not mapped.

    Parameters
    ----------
    reason_code : str
        Dispute reason code (e.g. ``"4855"``, ``"10.1"``).

    Returns
    -------
    dict
        Keys: ``reason_text``, ``required_evidence`` (list of dicts),
        ``avg_win_rate``, ``typical_timeline_days``.
    """
    code = str(reason_code).strip()
    template = DISPUTE_EVIDENCE_TEMPLATES.get(code)
    if template is None:
        logger.warning(
            "No evidence template for reason code %s — using generic fallback.",
            code,
        )
        return dict(_NO_TEMPLATE)
    return dict(template)


def get_required_types(reason_code: str) -> list[str]:
    """Return just the required evidence type names for a reason code."""
    req = get_evidence_requirements(reason_code)
    return [
        item["type"]
        for item in req["required_evidence"]
        if item.get("required", False)
    ]


def get_win_rate(reason_code: str) -> float:
    """Return the historical win rate for a dispute reason code."""
    req = get_evidence_requirements(reason_code)
    return req.get("avg_win_rate", 0.50)


def summarize_evidence_gaps(
    reason_code: str, submitted_types: list[str]
) -> dict[str, Any]:
    """Compare submitted evidence against the template and identify gaps.

    Returns
    -------
    dict
        ``missing_required``: list of required types not yet submitted.
        ``missing_optional``: list of optional types not yet submitted.
        ``coverage_pct``: percentage of required evidence submitted.
    """
    template = get_evidence_requirements(reason_code)
    submitted_set = set(submitted_types)

    missing_required = []
    missing_optional = []
    total_required = 0

    for item in template["required_evidence"]:
        if item.get("required", False):
            total_required += 1
            if item["type"] not in submitted_set:
                missing_required.append(item["type"])
        else:
            if item["type"] not in submitted_set:
                missing_optional.append(item["type"])

    if total_required == 0:
        coverage = 1.0
    else:
        coverage = (total_required - len(missing_required)) / total_required

    return {
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "coverage_pct": round(coverage * 100, 1),
    }
