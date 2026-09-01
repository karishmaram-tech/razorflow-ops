"""Explainability Agent — LLM-powered plain-English explanations.

Uses Claude API to generate merchant-friendly explanations of payment
operations issues.  Includes in-memory caching to avoid duplicate API calls.

Usage::

    from src.agents.explainability import ExplainabilityAgent

    agent = ExplainabilityAgent(api_key="sk-ant-...")
    text = agent.generate_explanation(context, "settlement_delay_explanation")
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# Prompt templates
# ══════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are a merchant-friendly payment operations advisor for Razorpay.
Explain payment issues in simple, clear language that a business owner can understand.

Rules:
- Keep to 2-3 sentences max
- Write from the merchant's perspective
- Be specific with amounts, dates, and actions
- Always mention concrete next steps
- Avoid technical jargon (no "root_cause", no "anomaly_type")
- Be reassuring but honest about severity"""

PROMPT_TEMPLATES: Dict[str, str] = {
    "settlement_delay_explanation": (
        "A settlement was delayed. Here are the details:\n"
        "- Settlement amount: {amount}\n"
        "- Created: {created_at}\n"
        "- Expected arrival: {expected_arrival}\n"
        "- Current status: {status}\n"
        "- Root cause: {root_cause}\n"
        "- Diagnosis confidence: {confidence}\n"
        "- Hours late: {hours_late}\n\n"
        "Explain why this settlement is delayed and what the merchant should do."
    ),
    "refund_issue_explanation": (
        "A refund has an issue. Here are the details:\n"
        "- Refund amount: {amount}\n"
        "- Customer: {customer_name}\n"
        "- Status: {status}\n"
        "- Created: {created_at}\n"
        "- Root cause: {root_cause}\n"
        "- Bank response: {bank_response}\n\n"
        "Explain what went wrong with this refund and what the merchant should do next."
    ),
    "dispute_evidence_explanation": (
        "A dispute/chargeback needs evidence. Here are the details:\n"
        "- Dispute amount: {amount}\n"
        "- Reason code: {reason_code} ({reason_text})\n"
        "- Filed: {filed_at}\n"
        "- Evidence deadline: {evidence_deadline}\n"
        "- Evidence completeness: {completeness_pct}%\n"
        "- Documents found: {docs_found}\n"
        "- Documents needed: {docs_needed}\n"
        "- Predicted win rate: {win_probability}%\n\n"
        "Explain the evidence situation and what the merchant should upload."
    ),
    "recommendation_explanation": (
        "A recommendation has been generated. Here are the details:\n"
        "- Issue type: {anomaly_type}\n"
        "- Severity: {severity}\n"
        "- Recommended action: {action}\n"
        "- Timeline: {timeline}\n"
        "- Urgency: {urgency}\n"
        "- Success probability: {success_probability}%\n"
        "- Details: {details}\n\n"
        "Explain what the merchant should do and why it matters."
    ),
}


# ══════════════════════════════════════════════════════════════════════════════
# Cache
# ══════════════════════════════════════════════════════════════════════════════


@dataclass
class ExplanationCache:
    """Simple in-memory LRU-ish cache for explanations."""

    _store: Dict[str, tuple[str, float]] = field(default_factory=dict)
    max_size: int = 500
    ttl_seconds: float = 3600  # 1 hour

    def get(self, key: str) -> Optional[str]:
        if key in self._store:
            text, ts = self._store[key]
            if (datetime.utcnow().timestamp() - ts) < self.ttl_seconds:
                logger.debug("Cache hit for key %s", key[:16])
                return text
            del self._store[key]
        return None

    def set(self, key: str, value: str) -> None:
        if len(self._store) >= self.max_size:
            # Evict oldest
            oldest_key = min(self._store, key=lambda k: self._store[k][1])
            del self._store[oldest_key]
        self._store[key] = (value, datetime.utcnow().timestamp())

    def clear(self) -> None:
        self._store.clear()


# ══════════════════════════════════════════════════════════════════════════════
# Explainability Agent
# ══════════════════════════════════════════════════════════════════════════════


class ExplainabilityAgent:
    """Generate merchant-friendly explanations using Claude API.

    Parameters
    ----------
    api_key : str, optional
        Anthropic API key.  Falls back to ``settings.anthropic_api_key_str``.
    model : str
        Claude model to use.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
    ) -> None:
        if api_key:
            self._api_key = api_key
        else:
            from src.config import settings
            self._api_key = settings.anthropic_api_key_str

        self._model = model
        self._cache = ExplanationCache()
        self._client = None  # lazy init

    def _get_client(self):
        """Lazy-init the Anthropic client."""
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self._api_key)
            except ImportError:
                logger.warning("anthropic package not installed — LLM explanations disabled")
                return None
        return self._client

    # ── Public API ────────────────────────────────────────────────────

    def generate_explanation(
        self, context: Dict[str, Any], explanation_type: str
    ) -> str:
        """Generate a plain-English explanation for the given context.

        Parameters
        ----------
        context : dict
            Structured data relevant to the explanation type.
        explanation_type : str
            One of: settlement_delay_explanation, refund_issue_explanation,
            dispute_evidence_explanation, recommendation_explanation.

        Returns
        -------
        str
            Plain-English explanation text.
        """
        logger.info("Generating explanation: type=%s", explanation_type)

        # Check cache
        cache_key = self._cache_key(context, explanation_type)
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        # Build prompt
        prompt = self._build_prompt(context, explanation_type)

        # Call Claude API
        explanation = self._call_claude(prompt)

        # Cache result
        self._cache.set(cache_key, explanation)

        return explanation

    # ── Prompt building ───────────────────────────────────────────────

    def _build_prompt(self, context: Dict[str, Any], explanation_type: str) -> str:
        """Format context into the appropriate prompt template."""
        template = PROMPT_TEMPLATES.get(explanation_type)
        if template is None:
            # Generic fallback
            return (
                f"Explain this payment operations issue in simple language:\n\n"
                f"{self._format_context(context)}\n\n"
                f"Type: {explanation_type}"
            )

        # Fill template with context, using .get() for safety
        try:
            return template.format(**context)
        except KeyError as e:
            # Missing key — fall back to formatted context
            logger.warning("Missing context key %s for template %s", e, explanation_type)
            return (
                f"{template}\n\n"
                f"Additional context:\n{self._format_context(context)}"
            )

    @staticmethod
    def _format_context(context: Dict[str, Any]) -> str:
        """Format a context dict into a readable string."""
        lines = []
        for key, value in context.items():
            if isinstance(value, dict):
                for k2, v2 in value.items():
                    lines.append(f"- {key}.{k2}: {v2}")
            elif isinstance(value, list):
                lines.append(f"- {key}: {', '.join(str(v) for v in value)}")
            else:
                lines.append(f"- {key}: {value}")
        return "\n".join(lines)

    # ── Claude API call ───────────────────────────────────────────────

    def _call_claude(self, prompt: str) -> str:
        """Call the Claude API and return the response text."""
        client = self._get_client()
        if client is None:
            return self._fallback_explanation(prompt)

        try:
            response = client.messages.create(
                model=self._model,
                max_tokens=300,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text.strip()
            logger.info("Claude explanation generated (%d chars)", len(text))
            return text

        except Exception as e:
            logger.error("Claude API error: %s — using fallback", e)
            return self._fallback_explanation(prompt)

    @staticmethod
    def _fallback_explanation(prompt: str) -> str:
        """Generate a generic fallback explanation when the API is unavailable."""
        # Extract key info from prompt
        if "settlement" in prompt.lower():
            return (
                "Your settlement has been delayed. Our system is investigating the cause. "
                "Please check your dashboard for updates, or contact Razorpay support if this persists beyond 48 hours."
            )
        if "refund" in prompt.lower():
            return (
                "Your refund is experiencing a delay. The bank is processing the transfer. "
                "If it doesn't complete within 3 business days, please contact Razorpay support."
            )
        if "dispute" in prompt.lower() or "chargeback" in prompt.lower():
            return (
                "A dispute has been filed against one of your transactions. "
                "Please upload the required evidence (proof of delivery, customer communication) as soon as possible."
            )
        return (
            "We're investigating this issue. Please check your dashboard for the latest status."
        )

    # ── Caching helpers ───────────────────────────────────────────────

    @staticmethod
    def _cache_key(context: Dict[str, Any], explanation_type: str) -> str:
        """Generate a deterministic cache key from context + type."""
        raw = json.dumps({"type": explanation_type, "context": context}, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()
