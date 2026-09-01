"""Dispute Evidence Agent — map requirements, assemble evidence, predict outcomes.

Pipeline:  EvidenceRequirementMapper  →  EvidenceAssembler  →  DisputeWinPredictor

Usage::

    from src.agents.dispute_agent import (
        EvidenceRequirementMapper,
        EvidenceAssembler,
        DisputeWinPredictor,
    )

    mapper = EvidenceRequirementMapper(session)
    reqs = mapper.get_requirements(dispute)

    assembler = EvidenceAssembler(session)
    packet = assembler.assemble_evidence(dispute, reqs)

    predictor = DisputeWinPredictor(session)
    win_prob = predictor.predict_win_probability(dispute, packet)
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, List, Optional

from sqlalchemy.orm import Session

from src.data.models import (
    Dispute,
    DisputeEvidence,
    EvidenceType,
    Refund,
    RefundStatus,
    Transaction,
)
from src.utils.evidence_templates import (
    get_evidence_requirements,
    get_win_rate,
    summarize_evidence_gaps,
)

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# Data containers
# ══════════════════════════════════════════════════════════════════════════════


@dataclass
class EvidenceRequirement:
    """A single evidence item required (or optional) for a dispute."""

    type: str
    required: bool
    examples: List[str] = field(default_factory=list)
    status: str = "needed"  # "needed" | "found" | "missing"


@dataclass
class EvidenceDocument:
    """A document that has been found or generated."""

    doc_type: str
    description: str
    source: str  # "transaction_record" | "refund_record" | "merchant_upload" | etc.
    relevance_score: float  # 0.0 – 1.0
    data: dict = field(default_factory=dict)  # extracted key-value pairs
    is_verified: bool = False


@dataclass
class EvidencePacket:
    """The fully assembled evidence package for a dispute."""

    dispute_id: str
    assembled_at: datetime
    documents: List[EvidenceDocument] = field(default_factory=list)
    gaps: List[EvidenceRequirement] = field(default_factory=list)
    completeness_score: float = 0.0  # 0–100
    completeness_status: str = "incomplete"  # complete | mostly_complete | incomplete


# ══════════════════════════════════════════════════════════════════════════════
# Generic evidence template (fallback)
# ══════════════════════════════════════════════════════════════════════════════

_GENERIC_EVIDENCE = [
    {"type": "receipt", "required": True, "examples": ["transaction_receipt", "order_confirmation"]},
    {"type": "customer_communication", "required": True, "examples": ["email", "chat", "ticket"]},
    {"type": "proof_of_delivery", "required": True, "examples": ["tracking", "signature", "photo"]},
    {"type": "terms_of_service", "required": False, "examples": ["policy_page", "tos"]},
]


# ══════════════════════════════════════════════════════════════════════════════
# 1. Evidence Requirement Mapper
# ══════════════════════════════════════════════════════════════════════════════


class EvidenceRequirementMapper:
    """Map a Dispute's reason_code to a list of EvidenceRequirement objects.

    Parameters
    ----------
    session : Session
        SQLAlchemy session (currently unused but reserved for future
        template-DB lookups).
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_requirements(self, dispute: Dispute) -> List[EvidenceRequirement]:
        """Return evidence requirements for the dispute's reason code.

        If no template exists for the code, a generic fallback is returned.
        """
        code = dispute.reason_code or "UNKNOWN"
        logger.info("Mapping evidence requirements for reason_code=%s", code)

        template = get_evidence_requirements(code)
        raw_evidence = template.get("required_evidence", _GENERIC_EVIDENCE)

        requirements: List[EvidenceRequirement] = []
        for item in raw_evidence:
            requirements.append(
                EvidenceRequirement(
                    type=item["type"],
                    required=item.get("required", False),
                    examples=item.get("examples", []),
                    status="needed",
                )
            )

        logger.info(
            "Dispute %s (code=%s): %d requirements (%d required)",
            dispute.id,
            code,
            len(requirements),
            sum(1 for r in requirements if r.required),
        )
        return requirements

    def get_win_rate(self, dispute: Dispute) -> float:
        """Return the historical win rate for this dispute's reason code."""
        code = dispute.reason_code or "UNKNOWN"
        return get_win_rate(code)


# ══════════════════════════════════════════════════════════════════════════════
# 2. Evidence Assembler
# ══════════════════════════════════════════════════════════════════════════════


class EvidenceAssembler:
    """Assemble an EvidencePacket by searching merchant records for each
    required evidence type.

    Parameters
    ----------
    session : Session
        SQLAlchemy session for database lookups.
    now : datetime, optional
        Override current time (testing).
    """

    def __init__(self, session: Session, *, now: Optional[datetime] = None) -> None:
        self.session = session
        _raw = now or datetime.now(timezone.utc)
        self._now = _raw.replace(tzinfo=None) if _raw.tzinfo else _raw

    # ── Public API ────────────────────────────────────────────────────

    def assemble_evidence(
        self, dispute: Dispute, requirements: List[EvidenceRequirement]
    ) -> EvidencePacket:
        """Search merchant records for each requirement and build a packet."""
        logger.info(
            "Assembling evidence for dispute %s (%d requirements)",
            dispute.id, len(requirements),
        )

        documents: List[EvidenceDocument] = []
        gaps: List[EvidenceRequirement] = []

        for req in requirements:
            found = self._search_for_requirement(dispute, req)
            if found:
                documents.extend(found)
                req.status = "found"
            else:
                req.status = "missing"
                gaps.append(req)

        # Also check already-uploaded evidence on the dispute
        uploaded = self._get_uploaded_evidence(dispute)
        documents.extend(uploaded)

        # Re-check: uploaded evidence may satisfy previously-missing requirements
        uploaded_types = {d.doc_type for d in uploaded}
        for req in requirements:
            if req.status == "missing" and req.type in uploaded_types:
                req.status = "found"
                if req in gaps:
                    gaps.remove(req)

        # Deduplicate by (doc_type, source)
        documents = self._deduplicate(documents)

        # Completeness
        total_required = sum(1 for r in requirements if r.required)
        found_required = sum(1 for r in requirements if r.required and r.status == "found")
        if total_required == 0:
            completeness = 100.0
        else:
            completeness = round((found_required / total_required) * 100, 1)

        if completeness >= 90:
            status = "complete"
        elif completeness >= 75:
            status = "mostly_complete"
        else:
            status = "incomplete"

        packet = EvidencePacket(
            dispute_id=dispute.id,
            assembled_at=self._now,
            documents=documents,
            gaps=gaps,
            completeness_score=completeness,
            completeness_status=status,
        )

        logger.info(
            "Evidence packet for dispute %s: %.0f%% complete (%s), %d docs, %d gaps",
            dispute.id, completeness, status, len(documents), len(gaps),
        )
        return packet

    # ── Requirement search dispatch ───────────────────────────────────

    def _search_for_requirement(
        self, dispute: Dispute, req: EvidenceRequirement
    ) -> List[EvidenceDocument]:
        """Dispatch to the appropriate search method based on evidence type."""
        searchers = {
            "receipt": self._search_for_invoice,
            "invoice": self._search_for_invoice,
            "proof_of_shipment": self._search_for_proof_of_delivery,
            "proof_of_delivery": self._search_for_proof_of_delivery,
            "delivery_proof": self._search_for_proof_of_delivery,
            "customer_communication": self._search_for_customer_communication,
            "auth_proof": self._search_for_auth_proof,
            "refund_proof": self._search_for_refund_proof,
            "terms_of_service": self._search_for_terms_of_service,
            "terms": self._search_for_terms_of_service,
        }
        searcher = searchers.get(req.type)
        if searcher is None:
            logger.debug("No searcher for evidence type '%s' — marking as missing", req.type)
            return []
        return searcher(dispute, req)

    # ── Individual searchers ──────────────────────────────────────────

    def _search_for_invoice(
        self, dispute: Dispute, req: EvidenceRequirement
    ) -> List[EvidenceDocument]:
        """Query the transactions table for an invoice / order confirmation."""
        txn: Optional[Transaction] = self.session.get(Transaction, dispute.transaction_id)
        if txn is None:
            return []

        doc = EvidenceDocument(
            doc_type=req.type,
            description=f"Invoice for transaction {txn.id} — ₹{txn.amount}",
            source="transaction_record",
            relevance_score=self._calculate_relevance(txn, req.type),
            data={
                "transaction_id": txn.id,
                "amount": str(txn.amount),
                "currency": txn.currency,
                "status": txn.status,
                "created_at": str(txn.created_at),
                "payment_method": txn.payment_method or "unknown",
            },
            is_verified=txn.status == "captured",
        )
        return [doc]

    def _search_for_proof_of_delivery(
        self, dispute: Dispute, req: EvidenceRequirement
    ) -> List[EvidenceDocument]:
        """Attempt to find delivery proof.  In a real system this would query
        Shiprocket / courier APIs.  Here we return a placeholder if the
        transaction exists."""
        txn = self.session.get(Transaction, dispute.transaction_id)
        if txn is None:
            return []

        # Digital goods / services always count as "delivered"
        if txn.payment_method in ("upi", "netbanking", "wallet"):
            doc = EvidenceDocument(
                doc_type=req.type,
                description=f"Digital delivery confirmed for {txn.payment_method} payment",
                source="digital_delivery",
                relevance_score=0.85,
                data={
                    "transaction_id": txn.id,
                    "delivery_method": "digital",
                    "note": "Digital product — no physical shipment required",
                },
                is_verified=True,
            )
            return [doc]

        # Physical goods: placeholder
        doc = EvidenceDocument(
            doc_type=req.type,
            description="Physical shipment — ask merchant for courier tracking",
            source="merchant_action_required",
            relevance_score=0.55,
            data={
                "transaction_id": txn.id,
                "note": "Ask merchant for Shiprocket / courier tracking number and delivery proof",
                "action_needed": True,
            },
            is_verified=False,
        )
        return [doc]

    def _search_for_customer_communication(
        self, dispute: Dispute, req: EvidenceRequirement
    ) -> List[EvidenceDocument]:
        """Search for customer communication.  In production this would query
        a CRM / support ticket system.  Here we check for any linked refund
        messages."""
        documents: List[EvidenceDocument] = []

        # Check refund records for bank messages
        if dispute.related_refund_id:
            refund = self.session.get(Refund, dispute.related_refund_id)
            if refund and refund.bank_response_message:
                documents.append(
                    EvidenceDocument(
                        doc_type=req.type,
                        description=f"Refund bank communication: {refund.bank_response_message}",
                        source="refund_record",
                        relevance_score=0.70,
                        data={
                            "refund_id": refund.id,
                            "bank_message": refund.bank_response_message,
                            "refund_status": refund.status.value,
                        },
                        is_verified=refund.status == RefundStatus.SUCCESS,
                    )
                )

        # Check all refunds for this transaction
        txn_refunds = self.session.query(Refund).filter(
            Refund.transaction_id == dispute.transaction_id,
        ).all()
        for r in txn_refunds:
            if r.bank_response_message and (not documents or r.id != dispute.related_refund_id):
                documents.append(
                    EvidenceDocument(
                        doc_type=req.type,
                        description=f"Refund communication ({r.id}): {r.bank_response_message}",
                        source="refund_record",
                        relevance_score=0.60,
                        data={
                            "refund_id": r.id,
                            "bank_message": r.bank_response_message,
                        },
                        is_verified=False,
                    )
                )

        return documents

    def _search_for_auth_proof(
        self, dispute: Dispute, req: EvidenceRequirement
    ) -> List[EvidenceDocument]:
        """Search for authentication proof (3DS, OTP, etc.)."""
        txn = self.session.get(Transaction, dispute.transaction_id)
        if txn is None:
            return []

        doc = EvidenceDocument(
            doc_type=req.type,
            description=f"Payment authentication for {txn.payment_method}",
            source="transaction_record",
            relevance_score=0.75,
            data={
                "transaction_id": txn.id,
                "payment_method": txn.payment_method or "unknown",
                "note": "Auth proof available via payment gateway logs",
            },
            is_verified=txn.status == "captured",
        )
        return [doc]

    def _search_for_refund_proof(
        self, dispute: Dispute, req: EvidenceRequirement
    ) -> List[EvidenceDocument]:
        """Query the refunds table for a completed refund receipt."""
        if dispute.related_refund_id is None:
            return []

        refund = self.session.get(Refund, dispute.related_refund_id)
        if refund is None:
            return []

        doc = EvidenceDocument(
            doc_type=req.type,
            description=f"Refund {refund.id}: ₹{refund.amount} — {refund.status.value}",
            source="refund_record",
            relevance_score=0.90 if refund.status == RefundStatus.SUCCESS else 0.50,
            data={
                "refund_id": refund.id,
                "amount": str(refund.amount),
                "status": refund.status.value,
                "created_at": str(refund.created_at),
                "bank_response_code": refund.bank_response_code or "N/A",
            },
            is_verified=refund.status == RefundStatus.SUCCESS,
        )
        return [doc]

    def _search_for_terms_of_service(
        self, dispute: Dispute, req: EvidenceRequirement
    ) -> List[EvidenceDocument]:
        """Terms of service are merchant-provided.  Return a placeholder
        prompting the merchant to upload."""
        doc = EvidenceDocument(
            doc_type=req.type,
            description="Terms of service / refund policy — requires merchant upload",
            source="merchant_action_required",
            relevance_score=0.30,
            data={
                "note": "Ask merchant to upload current ToS / refund policy PDF",
                "action_needed": True,
            },
            is_verified=False,
        )
        return [doc]

    # ── Uploaded evidence ─────────────────────────────────────────────

    def _get_uploaded_evidence(self, dispute: Dispute) -> List[EvidenceDocument]:
        """Fetch evidence already uploaded to the dispute."""
        uploaded = (
            self.session.query(DisputeEvidence)
            .filter(DisputeEvidence.dispute_id == dispute.id)
            .all()
        )
        documents: List[EvidenceDocument] = []
        for ev in uploaded:
            documents.append(
                EvidenceDocument(
                    doc_type=ev.evidence_type.value,
                    description=f"Uploaded: {ev.file_url or 'no URL'}",
                    source="merchant_upload",
                    relevance_score=0.95 if ev.is_verified else 0.70,
                    data={
                        "evidence_id": str(ev.id),
                        "file_url": ev.file_url or "",
                        "uploaded_at": str(ev.uploaded_at),
                    },
                    is_verified=ev.is_verified,
                )
            )
        return documents

    # ── Helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _calculate_relevance(txn: Transaction, evidence_type: str) -> float:
        """Score how relevant a transaction record is to a requirement."""
        if evidence_type in ("receipt", "invoice"):
            return 0.90 if txn.status == "captured" else 0.50
        if evidence_type in ("proof_of_delivery", "proof_of_shipment", "delivery_proof"):
            return 0.85 if txn.status == "captured" else 0.40
        return 0.70

    @staticmethod
    def _deduplicate(documents: List[EvidenceDocument]) -> List[EvidenceDocument]:
        """Remove duplicate documents by (doc_type, source)."""
        seen: set[str] = set()
        unique: List[EvidenceDocument] = []
        for doc in documents:
            key = f"{doc.doc_type}::{doc.source}"
            if key not in seen:
                seen.add(key)
                unique.append(doc)
        return unique


# ══════════════════════════════════════════════════════════════════════════════
# 3. Dispute Win Predictor
# ══════════════════════════════════════════════════════════════════════════════


class DisputeWinPredictor:
    """Predict the probability of winning a dispute based on reason code
    and evidence quality.

    Parameters
    ----------
    session : Session
        SQLAlchemy session.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def predict_win_probability(
        self, dispute: Dispute, evidence_packet: EvidencePacket
    ) -> float:
        """Calculate win probability (0.0 – 1.0).

        Factors:
        1. Base win rate from dispute reason code template.
        2. Completeness adjustment (±5–15%).
        3. Evidence quality adjustment (±5–10%).
        """
        # 1. Base win rate
        base_rate = get_win_rate(dispute.reason_code or "UNKNOWN")
        probability = Decimal(str(base_rate))

        logger.info(
            "Win prediction for dispute %s (code=%s): base_rate=%.2f",
            dispute.id, dispute.reason_code, base_rate,
        )

        # 2. Completeness adjustment
        completeness = Decimal(str(evidence_packet.completeness_score))
        if completeness >= 90:
            probability += Decimal("0.10")
            logger.debug("+10%% boost for completeness >= 90%%")
        elif completeness >= 75:
            probability += Decimal("0.05")
            logger.debug("+5%% boost for completeness 75-89%%")
        else:
            probability -= Decimal("0.15")
            logger.debug("-15%% penalty for completeness < 75%%")

        # 3. Evidence quality adjustment
        quality_delta = self._assess_evidence_quality(evidence_packet)
        probability += quality_delta

        # Clamp
        probability = max(Decimal("0.01"), min(Decimal("0.99"), probability))
        result = float(probability.quantize(Decimal("0.01")))

        logger.info(
            "Win prediction for dispute %s: final=%.2f (completeness=%.0f%%, quality_delta=%s)",
            dispute.id, result, evidence_packet.completeness_score, quality_delta,
        )
        return result

    # ── Quality assessment ────────────────────────────────────────────

    @staticmethod
    def _assess_evidence_quality(packet: EvidencePacket) -> Decimal:
        """Assess overall evidence quality and return an adjustment delta.

        High quality: verified docs, high relevance scores → +5%
        Low quality:  unverified, low relevance, many gaps → -10%
        """
        if not packet.documents:
            return Decimal("-0.10")

        total_score = sum(d.relevance_score for d in packet.documents)
        avg_score = total_score / len(packet.documents)

        verified_count = sum(1 for d in packet.documents if d.is_verified)
        verified_pct = verified_count / len(packet.documents)

        # High quality: avg relevance > 0.8 AND > 50% verified
        if avg_score > 0.8 and verified_pct > 0.5:
            return Decimal("0.05")

        # Low quality: avg relevance < 0.5 OR < 20% verified
        if avg_score < 0.5 or verified_pct < 0.2:
            return Decimal("-0.10")

        # Neutral
        return Decimal("0.00")
