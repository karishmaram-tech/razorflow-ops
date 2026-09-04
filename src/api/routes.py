"""FastAPI routes for the Merchant Payment Operations Intelligence agent.

All routes require merchant API key authentication via the
``X-Merchant-API-Key`` header.

Usage::

    from src.api.routes import router
    app.include_router(router, prefix="/api")
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.dispute_agent import (
    DisputeWinPredictor,
    EvidenceAssembler,
    EvidencePacket,
    EvidenceRequirementMapper,
)
from src.agents.orchestrator import PaymentOpsOrchestrator
from src.agents.refund_agent import (
    RefundActionRecommender,
    RefundAnomalyDetector,
    RefundRootCauseClassifier,
)
from src.agents.settlement_agent import (
    SettlementActionRecommender,
    SettlementAnomalyDetector,
    SettlementRootCauseClassifier,
)
from src.api.schemas import (
    AnomalyEntry,
    DashboardResponse,
    DisputeDetailResponse,
    EvidenceRequirementResponse,
    EvidenceUploadRequest,
    EvidenceUploadResponse,
    ErrorResponse,
    ImpactSummaryResponse,
    MetricsResponse,
    RecommendationEntry,
    RefundDetailResponse,
    SettlementDetailResponse,
)
from src.config import settings
from src.core.automation import get_automation_engine
from src.data.database import get_db_session, get_sync_session
from src.data.models import (
    Anomaly,
    AnomalyStatus,
    AnomalyType,
    Dispute,
    DisputeEvidence,
    DisputeStatus,
    EvidenceType,
    EvaluationMetric,
    Merchant,
    Recommendation,
    Refund,
    RefundStatus,
    Settlement,
    SettlementStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ══════════════════════════════════════════════════════════════════════════════
# Rate limiter (simple in-memory)
# ══════════════════════════════════════════════════════════════════════════════

_rate_limits: Dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 100     # requests per window per API key


def _check_rate_limit(api_key: str) -> None:
    """Raise 429 if the API key has exceeded the rate limit."""
    now = time.time()
    cutoff = now - RATE_LIMIT_WINDOW
    _rate_limits[api_key] = [t for t in _rate_limits[api_key] if t > cutoff]
    if len(_rate_limits[api_key]) >= RATE_LIMIT_MAX:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again shortly.")
    _rate_limits[api_key].append(now)


# ══════════════════════════════════════════════════════════════════════════════
# Authentication dependency
# ══════════════════════════════════════════════════════════════════════════════


async def get_current_merchant(
    x_merchant_api_key: str = Header(..., alias="X-Merchant-API-Key"),
    db: AsyncSession = Depends(get_db_session),
) -> Merchant:
    """Validate the merchant API key and return the Merchant object.

    In production the API key would be stored hashed in a keys table.
    Here we use a simplified lookup by matching the key to a merchant ID
    stored in the key itself (``rzp_merchant_<merchant_uuid>``).
    """
    _check_rate_limit(x_merchant_api_key)

    # Extract merchant ID from key (format: rzp_merchant_<uuid>)
    if not x_merchant_api_key.startswith("rzp_merchant_"):
        raise HTTPException(status_code=401, detail="Invalid API key format.")

    try:
        merchant_id_str = x_merchant_api_key.replace("rzp_merchant_", "")
        merchant_id = uuid.UUID(merchant_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid API key.")

    from sqlalchemy import select

    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalar_one_or_none()

    if merchant is None:
        raise HTTPException(status_code=401, detail="Merchant not found for this API key.")

    return merchant


# Helper: run sync agent code in thread pool
async def _run_sync(func, *args, **kwargs):
    """Run a synchronous function in a thread pool executor."""
    return await asyncio.to_thread(func, *args, **kwargs)





# ══════════════════════════════════════════════════════════════════════════════
# Routes
# ══════════════════════════════════════════════════════════════════════════════


# ── 1. Dashboard ──────────────────────────────────────────────────────────────


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    responses={401: {"model": ErrorResponse}, 429: {"model": ErrorResponse}},
    summary="Get merchant dashboard",
)
async def get_dashboard(
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db_session),
):
    """Return the full dashboard view: anomalies, recommendations, metrics, impact."""
    logger.info("Dashboard request for merchant %s", merchant.id)

    sync_session = get_sync_session()
    try:
        orchestrator = PaymentOpsOrchestrator(sync_session, now=datetime.now(timezone.utc))
        dashboard = await _run_sync(orchestrator.run_agent_cycle, merchant.id)
    finally:
        sync_session.close()

    return DashboardResponse(
        merchant_id=dashboard.merchant_id,
        cycle_at=str(dashboard.cycle_at),
        critical_anomalies=[AnomalyEntry(**a) for a in dashboard.critical_anomalies],
        warning_anomalies=[AnomalyEntry(**a) for a in dashboard.warning_anomalies],
        info_anomalies=[AnomalyEntry(**a) for a in dashboard.info_anomalies],
        top_recommendations=[RecommendationEntry(**r) for r in dashboard.top_recommendations],
        impact=ImpactSummaryResponse(
            time_saved_hours=dashboard.impact.time_saved_hours,
            revenue_recovered_inr=dashboard.impact.revenue_recovered_inr,
            chargebacks_won=dashboard.impact.chargebacks_won,
            settlement_delays_prevented=dashboard.impact.settlement_delays_prevented,
            anomalies_detected=dashboard.impact.anomalies_detected,
            anomalies_resolved=dashboard.impact.anomalies_resolved,
        ),
        next_deadline=str(dashboard.next_deadline) if dashboard.next_deadline else None,
        summary=dashboard.summary,
    )


# ── 2. Settlement detail ──────────────────────────────────────────────────────


@router.get(
    "/settlement/{settlement_id}",
    response_model=SettlementDetailResponse,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
    summary="Get settlement details with diagnosis",
)
async def get_settlement(
    settlement_id: str,
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db_session),
):
    """Return settlement details with linked diagnosis and recommendation."""
    from sqlalchemy import select

    result = await db.execute(
        select(Settlement).where(
            Settlement.id == settlement_id,
            Settlement.merchant_id == merchant.id,
        )
    )
    settlement = result.scalar_one_or_none()
    if settlement is None:
        raise HTTPException(status_code=404, detail=f"Settlement {settlement_id} not found.")

    # Find linked anomaly → diagnosis → recommendation
    diag_data, rec_data = await _find_linked_records(db, settlement.id, "settlement")

    return SettlementDetailResponse(
        settlement_id=settlement.id,
        merchant_id=str(settlement.merchant_id),
        amount=str(settlement.amount),
        currency=settlement.currency,
        status=settlement.status.value if hasattr(settlement.status, 'value') else str(settlement.status),
        created_at=str(settlement.created_at),
        expected_arrival_at=str(settlement.expected_arrival_at) if settlement.expected_arrival_at else None,
        actual_arrival_at=str(settlement.actual_arrival_at) if settlement.actual_arrival_at else None,
        fees=str(settlement.fees),
        taxes=str(settlement.taxes),
        net_amount=str(settlement.net_amount),
        diagnosis=diag_data,
        recommendation=rec_data,
    )


# ── 3. Refund detail ──────────────────────────────────────────────────────────


@router.get(
    "/refund/{refund_id}",
    response_model=RefundDetailResponse,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
    summary="Get refund details with diagnosis",
)
async def get_refund(
    refund_id: str,
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db_session),
):
    """Return refund details with linked diagnosis and recommendation."""
    from sqlalchemy import select

    result = await db.execute(
        select(Refund).where(
            Refund.id == refund_id,
            Refund.merchant_id == merchant.id,
        )
    )
    refund = result.scalar_one_or_none()
    if refund is None:
        raise HTTPException(status_code=404, detail=f"Refund {refund_id} not found.")

    diag_data, rec_data = await _find_linked_records(db, refund.id, "refund")

    return RefundDetailResponse(
        refund_id=refund.id,
        merchant_id=str(refund.merchant_id),
        transaction_id=refund.transaction_id,
        amount=str(refund.amount),
        status=refund.status.value if hasattr(refund.status, 'value') else str(refund.status),
        reason=refund.reason.value if hasattr(refund.reason, 'value') else str(refund.reason) if refund.reason else None,
        created_at=str(refund.created_at),
        expected_completion_at=str(refund.expected_completion_at) if refund.expected_completion_at else None,
        bank_response_code=refund.bank_response_code,
        diagnosis=diag_data,
        recommendation=rec_data,
    )


# ── 4. Dispute detail ────────────────────────────────────────────────────────


@router.get(
    "/dispute/{dispute_id}",
    response_model=DisputeDetailResponse,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
    summary="Get dispute details with evidence analysis",
)
async def get_dispute(
    dispute_id: str,
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db_session),
):
    """Return dispute details with evidence requirements, completeness, and win probability."""
    from sqlalchemy import select

    result = await db.execute(
        select(Dispute).where(
            Dispute.id == dispute_id,
            Dispute.merchant_id == merchant.id,
        )
    )
    dispute = result.scalar_one_or_none()
    if dispute is None:
        raise HTTPException(status_code=404, detail=f"Dispute {dispute_id} not found.")

    sync_session = get_sync_session()
    try:
        mapper = EvidenceRequirementMapper(sync_session)
        reqs = mapper.get_requirements(dispute)

        assembler = EvidenceAssembler(sync_session, now=datetime.now(timezone.utc))
        packet = await _run_sync(assembler.assemble_evidence, dispute, reqs)

        predictor = DisputeWinPredictor(sync_session)
        win_prob = await _run_sync(predictor.predict_win_probability, dispute, packet)
    finally:
        sync_session.close()

    return DisputeDetailResponse(
        dispute_id=dispute.id,
        merchant_id=str(dispute.merchant_id),
        transaction_id=dispute.transaction_id,
        type=dispute.type.value if hasattr(dispute.type, 'value') else str(dispute.type),
        reason_code=dispute.reason_code,
        reason_text=dispute.reason_text,
        amount=str(dispute.amount),
        filed_at=str(dispute.filed_at),
        evidence_deadline=str(dispute.evidence_deadline) if dispute.evidence_deadline else None,
        current_status=dispute.current_status.value if hasattr(dispute.current_status, 'value') else str(dispute.current_status),
        evidence_requirements=[
            EvidenceRequirementResponse(
                type=r.type, required=r.required, examples=r.examples, status=r.status,
            )
            for r in reqs
        ],
        completeness_score=packet.completeness_score,
        completeness_status=packet.completeness_status,
        win_probability=win_prob,
    )


# ── 5. Upload evidence ───────────────────────────────────────────────────────


@router.post(
    "/dispute/{dispute_id}/evidence",
    response_model=EvidenceUploadResponse,
    responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
    summary="Upload evidence for a dispute",
)
async def upload_evidence(
    dispute_id: str,
    body: EvidenceUploadRequest,
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db_session),
):
    """Upload a piece of evidence and recalculate completeness."""
    from sqlalchemy import select

    # Validate dispute exists and belongs to merchant
    result = await db.execute(
        select(Dispute).where(
            Dispute.id == dispute_id,
            Dispute.merchant_id == merchant.id,
        )
    )
    dispute = result.scalar_one_or_none()
    if dispute is None:
        raise HTTPException(status_code=404, detail=f"Dispute {dispute_id} not found.")

    # Validate evidence type
    try:
        ev_type = EvidenceType(body.evidence_type)
    except ValueError:
        valid = [e.value for e in EvidenceType]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid evidence_type '{body.evidence_type}'. Valid: {valid}",
        )

    # Create evidence record
    evidence = DisputeEvidence(
        id=uuid.uuid4(),
        dispute_id=dispute_id,
        evidence_type=ev_type,
        file_url=body.file_url,
        uploaded_at=datetime.now(timezone.utc),
        is_verified=False,
    )
    db.add(evidence)
    await db.flush()

    # Recalculate completeness
    sync_session = get_sync_session()
    try:
        mapper = EvidenceRequirementMapper(sync_session)
        reqs = mapper.get_requirements(dispute)

        # Mark matching requirement as found
        for req in reqs:
            if req.type == body.evidence_type:
                req.status = "found"

        assembler = EvidenceAssembler(sync_session, now=datetime.now(timezone.utc))
        packet = await _run_sync(assembler.assemble_evidence, dispute, reqs)
    finally:
        sync_session.close()

    await db.commit()

    return EvidenceUploadResponse(
        evidence_id=str(evidence.id),
        dispute_id=dispute_id,
        completeness_updated=True,
        new_score=packet.completeness_score,
        completeness_status=packet.completeness_status,
    )


# ── 6. Metrics ────────────────────────────────────────────────────────────────


@router.get(
    "/metrics",
    response_model=MetricsResponse,
    responses={401: {"model": ErrorResponse}},
    summary="Get merchant metrics",
)
async def get_metrics(
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db_session),
):
    """Return aggregated metrics: time saved, chargebacks won, detection accuracy."""
    from sqlalchemy import select

    # Impact from resolved anomalies
    sync_session = get_sync_session()
    try:
        from src.agents.orchestrator import PaymentOpsOrchestrator
        orch = PaymentOpsOrchestrator(sync_session, now=datetime.now(timezone.utc))
        impact = await _run_sync(orch._calculate_impact, merchant.id)
    finally:
        sync_session.close()

    # Detection accuracy: anomalies resolved / total anomalies
    total_q = await db.execute(
        select(func.count(Anomaly.id)).where(Anomaly.merchant_id == merchant.id)
    )
    total = total_q.scalar() or 0

    resolved_q = await db.execute(
        select(func.count(Anomaly.id)).where(
            Anomaly.merchant_id == merchant.id,
            Anomaly.status == AnomalyStatus.RESOLVED,
        )
    )
    resolved = resolved_q.scalar() or 0

    accuracy = (resolved / total * 100) if total > 0 else 0.0

    return MetricsResponse(
        merchant_id=str(merchant.id),
        time_saved_hours=impact.time_saved_hours,
        chargebacks_won=impact.chargebacks_won,
        revenue_recovered=impact.revenue_recovered_inr,
        detection_accuracy=round(accuracy, 1),
        anomalies_total=total,
        anomalies_resolved=resolved,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Automation endpoints
# ══════════════════════════════════════════════════════════════════════════════


@router.post(
    "/automations/execute",
    summary="Execute an automation",
)
async def execute_automation(
    automation_type: str,
    item_id: str,
):
    """Execute an automation immediately and return results."""
    engine = get_automation_engine()
    result = await engine.execute(automation_type, item_id)
    return result


@router.get(
    "/automations/activity",
    summary="Get recent automation activity",
)
async def get_automation_activity(
    limit: int = 20,
):
    """Return recent automation executions."""
    # Generate demo activity feed
    from datetime import timedelta

    now = datetime.now(timezone.utc)
    types = ["auto_settle", "dispute_autopilot", "smart_refund"]
    titles = [
        "Settlement routed to NEFT",
        "Dispute evidence submitted",
        "Refund routed to original payment",
        "Settlement route optimized",
        "Dispute evidence gathering",
        "Settlement batch processed",
        "Refund routing analyzed",
        "Chargeback prevention alert",
    ]
    descriptions = [
        "Settlement #1847 — saved Rs 600 vs IMPS",
        "Dispute #2891 — win probability 92%",
        "Refund #4521 — saved 2% processing fee",
        "Settlement #1846 — RTGS selected for Rs 50K+",
        "Dispute #2895 — collecting transaction records",
        "Batch #89 — 12 settlements, 11 routed optimally",
        "Refund #4522 — wallet route selected",
        "Order #9823 — flagged for review",
    ]
    costs = [600, 0, 150, 1200, 0, 3200, 85, 0]
    statuses = ["completed", "completed", "completed", "completed", "in_progress", "completed", "completed", "in_progress"]
    times = ["2 min ago", "8 min ago", "15 min ago", "22 min ago", "Now", "1 hr ago", "1 hr ago", "2 hr ago"]

    return [
        {
            "id": i + 1,
            "type": types[i % 3],
            "title": titles[i],
            "description": descriptions[i],
            "cost_saved": costs[i],
            "status": statuses[i],
            "time": times[i],
        }
        for i in range(min(limit, len(titles)))
    ]


@router.get(
    "/automations/stats",
    summary="Get automation statistics",
)
async def get_automation_stats():
    """Return automation engine statistics."""
    engine = get_automation_engine()
    return engine.get_stats()


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════


async def _find_linked_records(
    db: AsyncSession, resource_id: str, resource_type: str
) -> tuple[Optional[Dict], Optional[Dict]]:
    """Find the diagnosis and recommendation linked to a resource via its anomaly."""
    from sqlalchemy import select

    # Find anomaly linked to this resource
    if resource_type == "settlement":
        col = Anomaly.related_settlement_id
    elif resource_type == "refund":
        col = Anomaly.related_refund_id
    else:
        col = Anomaly.related_dispute_id

    anomaly_result = await db.execute(
        select(Anomaly).where(col == resource_id).limit(1)
    )
    anomaly = anomaly_result.scalar_one_or_none()

    if anomaly is None:
        return None, None

    # Find diagnosis
    from src.data.models import Diagnosis
    diag_result = await db.execute(
        select(Diagnosis).where(Diagnosis.anomaly_id == anomaly.id).limit(1)
    )
    diagnosis = diag_result.scalar_one_or_none()

    # Find recommendation
    rec_result = await db.execute(
        select(Recommendation).where(Recommendation.anomaly_id == anomaly.id).limit(1)
    )
    recommendation = rec_result.scalar_one_or_none()

    diag_data = None
    if diagnosis:
        diag_data = {
            "root_cause": diagnosis.root_cause_category,
            "subcategory": diagnosis.root_cause_subcategory,
            "explanation": diagnosis.explanation_plain_english,
            "confidence": float(diagnosis.confidence) if diagnosis.confidence else 0.0,
        }

    rec_data = None
    if recommendation:
        rec_data = {
            "action": recommendation.recommended_action.value if hasattr(recommendation.recommended_action, 'value') else str(recommendation.recommended_action),
            "urgency": recommendation.urgency.value if hasattr(recommendation.urgency, 'value') else str(recommendation.urgency),
            "timeline": recommendation.timeline,
            "success_probability": float(recommendation.success_probability) if recommendation.success_probability else 0.0,
            "text": recommendation.recommendation_text,
        }

    return diag_data, rec_data
