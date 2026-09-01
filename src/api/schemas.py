"""Pydantic schemas for API request and response bodies.

All response models use ``model_config = ConfigDict(from_attributes=True)``
so they can be populated directly from ORM objects or dicts.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Auth ───────────────────────────────────────────────────────────────────────


class MerchantAuth(BaseModel):
    """API-key based merchant authentication context."""

    merchant_id: str
    api_key: str


# ── Dashboard ──────────────────────────────────────────────────────────────────


class AnomalyEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: str
    severity: str
    root_cause: Optional[str] = None
    recommended_action: Optional[str] = None
    detected_at: Optional[str] = None
    related_settlement_id: Optional[str] = None
    related_refund_id: Optional[str] = None
    related_dispute_id: Optional[str] = None


class RecommendationEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    anomaly_id: str
    action: str
    urgency: str
    timeline: Optional[str] = None
    success_probability: float = 0.0
    text: Optional[str] = None


class ImpactSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    time_saved_hours: float = 0.0
    revenue_recovered_inr: float = 0.0
    chargebacks_won: int = 0
    settlement_delays_prevented: int = 0
    anomalies_detected: int = 0
    anomalies_resolved: int = 0


class DashboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    merchant_id: str
    cycle_at: str
    critical_anomalies: List[AnomalyEntry] = Field(default_factory=list)
    warning_anomalies: List[AnomalyEntry] = Field(default_factory=list)
    info_anomalies: List[AnomalyEntry] = Field(default_factory=list)
    top_recommendations: List[RecommendationEntry] = Field(default_factory=list)
    impact: ImpactSummaryResponse = Field(default_factory=ImpactSummaryResponse)
    next_deadline: Optional[str] = None
    summary: Dict[str, Any] = Field(default_factory=dict)


# ── Settlement ─────────────────────────────────────────────────────────────────


class SettlementDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    settlement_id: str
    merchant_id: str
    amount: str
    currency: str
    status: str
    created_at: Optional[str] = None
    expected_arrival_at: Optional[str] = None
    actual_arrival_at: Optional[str] = None
    fees: str = "0.00"
    taxes: str = "0.00"
    net_amount: str = "0.00"
    diagnosis: Optional[Dict[str, Any]] = None
    recommendation: Optional[Dict[str, Any]] = None


# ── Refund ─────────────────────────────────────────────────────────────────────


class RefundDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    refund_id: str
    merchant_id: str
    transaction_id: str
    amount: str
    status: str
    reason: Optional[str] = None
    created_at: Optional[str] = None
    expected_completion_at: Optional[str] = None
    bank_response_code: Optional[str] = None
    diagnosis: Optional[Dict[str, Any]] = None
    recommendation: Optional[Dict[str, Any]] = None


# ── Dispute ────────────────────────────────────────────────────────────────────


class EvidenceRequirementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    type: str
    required: bool
    examples: List[str] = Field(default_factory=list)
    status: str = "needed"


class DisputeDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    dispute_id: str
    merchant_id: str
    transaction_id: str
    type: str
    reason_code: Optional[str] = None
    reason_text: Optional[str] = None
    amount: str
    filed_at: Optional[str] = None
    evidence_deadline: Optional[str] = None
    current_status: str
    evidence_requirements: List[EvidenceRequirementResponse] = Field(default_factory=list)
    completeness_score: Optional[float] = None
    completeness_status: Optional[str] = None
    win_probability: Optional[float] = None


# ── Evidence Upload ────────────────────────────────────────────────────────────


class EvidenceUploadRequest(BaseModel):
    evidence_type: str
    file_url: str


class EvidenceUploadResponse(BaseModel):
    evidence_id: str
    dispute_id: str
    completeness_updated: bool = True
    new_score: float = 0.0
    completeness_status: str = "incomplete"


# ── Metrics ────────────────────────────────────────────────────────────────────


class MetricsResponse(BaseModel):
    merchant_id: str
    time_saved_hours: float = 0.0
    chargebacks_won: int = 0
    revenue_recovered: float = 0.0
    detection_accuracy: float = 0.0
    anomalies_total: int = 0
    anomalies_resolved: int = 0


# ── Error ──────────────────────────────────────────────────────────────────────


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
