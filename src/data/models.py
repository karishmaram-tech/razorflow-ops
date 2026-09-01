"""SQLAlchemy ORM models for the Merchant Payment Operations Intelligence agent.

All models use:
- UUID primary keys (except settlement_attempts.auto_increment id)
- Soft-delete-safe timestamp columns (created_at / updated_at)
- Proper FK constraints with cascade rules
- Composite and single-column indexes for common query patterns
"""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    validates,
)


# ── Enums ──────────────────────────────────────────────────────────────────────


class SeverityLevel(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class SettlementStatus(str, enum.Enum):
    INITIATED = "initiated"
    PENDING = "pending"
    PARTIAL = "partial"
    FAILED = "failed"
    SUCCESS = "success"


class TransferMethod(str, enum.Enum):
    IMPS = "IMPS"
    NEFT = "NEFT"
    RTGS = "RTGS"
    UPI = "UPI"


class SettlementAttemptStatus(str, enum.Enum):
    INITIATED = "initiated"
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class RefundReason(str, enum.Enum):
    CUSTOMER_REQUESTED = "customer_requested"
    DUPLICATE_CHARGE = "duplicate_charge"
    FRAUD = "fraud"
    PROCESSING_ERROR = "processing_error"
    OTHER = "other"


class RefundStatus(str, enum.Enum):
    INITIATED = "initiated"
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    REVERSED = "reversed"


class RefundInitiator(str, enum.Enum):
    MERCHANT = "merchant"
    CUSTOMER_DISPUTE = "customer_dispute"
    SYSTEM = "system"


class DisputeType(str, enum.Enum):
    CHARGEBACK = "chargeback"
    RETRIEVAL = "retrieval"
    COMPLAINT = "complaint"
    FRAUD_CLAIM = "fraud_claim"


class DisputeStatus(str, enum.Enum):
    EVIDENCE_PENDING = "evidence_pending"
    UNDER_REVIEW = "under_review"
    WON = "won"
    LOST = "lost"
    RESOLVED = "resolved"


class EvidenceType(str, enum.Enum):
    PROOF_OF_SHIPMENT = "proof_of_shipment"
    PROOF_OF_DELIVERY = "proof_of_delivery"
    CUSTOMER_COMMUNICATION = "customer_communication"
    TERMS_OF_SERVICE = "terms_of_service"
    RECEIPT = "receipt"
    REFUND_POLICY = "refund_policy"
    OTHER = "other"


class AnomalyType(str, enum.Enum):
    SETTLEMENT_DELAYED = "settlement_delayed"
    SETTLEMENT_PARTIAL = "settlement_partial"
    SETTLEMENT_FAILED = "settlement_failed"
    REFUND_STUCK = "refund_stuck"
    REFUND_FAILED = "refund_failed"
    REFUND_REVERSED = "refund_reversed"
    REFUND_MISMATCH = "refund_mismatch"
    REFUND_DUPLICATE = "refund_duplicate"
    REFUND_PROCESSING_DELAY = "refund_processing_delay"
    DISPUTE_EVIDENCE_INCOMPLETE = "dispute_evidence_incomplete"
    DISPUTE_DEADLINE_APPROACHING = "dispute_deadline_approaching"
    HIGH_DISPUTE_RATE = "high_dispute_rate"
    UNUSUAL_TRANSACTION_PATTERN = "unusual_transaction_pattern"


class AnomalyStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"


class RecommendedAction(str, enum.Enum):
    WAIT = "wait"
    CONTACT_BANK = "contact_bank"
    CONTACT_RAZORPAY = "contact_razorpay"
    RESUBMIT_EVIDENCE = "resubmit_evidence"
    ESCALATE = "escalate"
    FILE_DISPUTE = "file_dispute"
    PROCESS_REFUND = "process_refund"
    REVERT = "revert"


class UrgencyLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ── Base ───────────────────────────────────────────────────────────────────────


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""

    pass


# ── Helper ─────────────────────────────────────────────────────────────────────


def _new_uuid() -> uuid.UUID:
    """Generate a new UUID v4."""
    return uuid.uuid4()


# ── Models ─────────────────────────────────────────────────────────────────────


class Merchant(Base):
    """Razorpay merchant profile."""

    __tablename__ = "merchants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_new_uuid
    )
    business_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    annual_revenue: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    transaction_volume_monthly: Mapped[Optional[int]] = mapped_column(Integer)
    dispute_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    industry_category: Mapped[Optional[str]] = mapped_column(String(128))
    alert_threshold_severity: Mapped[SeverityLevel] = mapped_column(
        Enum(SeverityLevel, name="severity_level", create_constraint=True),
        default=SeverityLevel.WARNING,
        server_default="WARNING",
    )
    notification_channels: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────────────
    settlements: Mapped[List["Settlement"]] = relationship(
        "Settlement", back_populates="merchant", cascade="all, delete-orphan"
    )
    refunds: Mapped[List["Refund"]] = relationship(
        "Refund", back_populates="merchant", cascade="all, delete-orphan"
    )
    disputes: Mapped[List["Dispute"]] = relationship(
        "Dispute", back_populates="merchant", cascade="all, delete-orphan"
    )
    anomalies: Mapped[List["Anomaly"]] = relationship(
        "Anomaly", back_populates="merchant", cascade="all, delete-orphan"
    )

    @validates("dispute_rate")
    def _validate_dispute_rate(self, _key: str, value: Any) -> Any:
        if value is not None and (value < 0 or value > 100):
            raise ValueError(f"dispute_rate must be 0-100, got {value}")
        return value

    def __repr__(self) -> str:
        return f"<Merchant id={self.id} name={self.business_name!r}>"

    def __str__(self) -> str:
        return self.business_name or str(self.id)


class Settlement(Base):
    """Settlement record for a merchant payout."""

    __tablename__ = "settlements"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", server_default="INR")
    status: Mapped[SettlementStatus] = mapped_column(
        Enum(SettlementStatus, name="settlement_status", create_constraint=True),
        default=SettlementStatus.INITIATED,
        server_default="INITIATED",
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expected_arrival_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    actual_arrival_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    fees: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0.00"), server_default="0"
    )
    taxes: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0.00"), server_default="0"
    )
    net_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0.00"), server_default="0"
    )
    settlement_period_start: Mapped[Optional[date]] = mapped_column(Date)
    settlement_period_end: Mapped[Optional[date]] = mapped_column(Date)
    related_refunds: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    related_disputes: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    last_checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # ── Relationships ──────────────────────────────────────────────────
    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="settlements")
    attempts: Mapped[List["SettlementAttempt"]] = relationship(
        "SettlementAttempt", back_populates="settlement", cascade="all, delete-orphan"
    )
    anomalies: Mapped[List["Anomaly"]] = relationship(
        "Anomaly", back_populates="settlement"
    )
    refunds: Mapped[List["Refund"]] = relationship("Refund", back_populates="settlement")

    __table_args__ = (
        Index("ix_settlements_merchant_status", "merchant_id", "status"),
        Index("ix_settlements_created_at", "created_at"),
    )

    @validates("amount")
    def _validate_amount(self, _key: str, value: Any) -> Any:
        if value is not None and value < 0:
            raise ValueError(f"amount must be >= 0, got {value}")
        return value

    def __repr__(self) -> str:
        return f"<Settlement id={self.id} amount={self.amount} status={self.status}>"

    def __str__(self) -> str:
        return f"Settlement {self.id} ({self.status})"


class SettlementAttempt(Base):
    """Individual bank-transfer attempt for a settlement."""

    __tablename__ = "settlement_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    settlement_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("settlements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    method: Mapped[TransferMethod] = mapped_column(
        Enum(TransferMethod, name="transfer_method", create_constraint=True),
        nullable=False,
    )
    initiated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    response_code: Mapped[Optional[str]] = mapped_column(String(32))
    response_message: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[SettlementAttemptStatus] = mapped_column(
        Enum(
            SettlementAttemptStatus,
            name="settlement_attempt_status",
            create_constraint=True,
        ),
        default=SettlementAttemptStatus.INITIATED,
        server_default="INITIATED",
    )
    bank_reference_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)

    # ── Relationships ──────────────────────────────────────────────────
    settlement: Mapped["Settlement"] = relationship(
        "Settlement", back_populates="attempts"
    )

    __table_args__ = (
        Index("ix_settlement_attempts_settlement_number", "settlement_id", "attempt_number"),
    )

    def __repr__(self) -> str:
        return (
            f"<SettlementAttempt settlement={self.settlement_id} "
            f"#{self.attempt_number} method={self.method}>"
        )

    def __str__(self) -> str:
        return f"Attempt #{self.attempt_number} via {self.method}"


class Transaction(Base):
    """Payment transaction record."""

    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    customer_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", server_default="INR")
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    payment_method: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    captured_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Transaction id={self.id} amount={self.amount} status={self.status}>"

    def __str__(self) -> str:
        return f"Txn {self.id}"


class Refund(Base):
    """Refund record linked to a transaction and merchant."""

    __tablename__ = "refunds"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    transaction_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    settlement_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("settlements.id", ondelete="SET NULL"),
        index=True,
    )
    customer_id: Mapped[Optional[str]] = mapped_column(String(64))
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    reason: Mapped[RefundReason] = mapped_column(
        Enum(RefundReason, name="refund_reason", create_constraint=True),
        default=RefundReason.OTHER,
        server_default="OTHER",
    )
    status: Mapped[RefundStatus] = mapped_column(
        Enum(RefundStatus, name="refund_status", create_constraint=True),
        default=RefundStatus.INITIATED,
        server_default="INITIATED",
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expected_completion_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    actual_completion_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    initiated_by: Mapped[RefundInitiator] = mapped_column(
        Enum(RefundInitiator, name="refund_initiator", create_constraint=True),
        default=RefundInitiator.MERCHANT,
        server_default="MERCHANT",
    )
    bank_response_code: Mapped[Optional[str]] = mapped_column(String(32))
    bank_response_message: Mapped[Optional[str]] = mapped_column(Text)
    related_dispute_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("disputes.id", ondelete="SET NULL", name="fk_refund_dispute"),
        index=True,
    )

    # ── Relationships ──────────────────────────────────────────────────
    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="refunds")
    transaction: Mapped["Transaction"] = relationship("Transaction")
    settlement: Mapped[Optional["Settlement"]] = relationship(
        "Settlement", back_populates="refunds"
    )
    dispute: Mapped[Optional["Dispute"]] = relationship(
        "Dispute",
        foreign_keys="Refund.related_dispute_id",
        remote_side="Dispute.id",
    )
    anomalies: Mapped[List["Anomaly"]] = relationship("Anomaly", back_populates="refund")

    __table_args__ = (
        Index("ix_refunds_merchant_status", "merchant_id", "status"),
        Index("ix_refunds_created_at", "created_at"),
    )

    @validates("amount")
    def _validate_amount(self, _key: str, value: Any) -> Any:
        if value is not None and value < 0:
            raise ValueError(f"refund amount must be >= 0, got {value}")
        return value

    def __repr__(self) -> str:
        return f"<Refund id={self.id} amount={self.amount} status={self.status}>"

    def __str__(self) -> str:
        return f"Refund {self.id} ({self.status})"


class Dispute(Base):
    """Chargeback / dispute record."""

    __tablename__ = "disputes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    transaction_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    related_refund_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("refunds.id", ondelete="SET NULL", name="fk_dispute_refund"),
        index=True,
    )
    type: Mapped[DisputeType] = mapped_column(
        Enum(DisputeType, name="dispute_type", create_constraint=True),
        nullable=False,
    )
    reason_code: Mapped[Optional[str]] = mapped_column(String(16), index=True)
    reason_text: Mapped[Optional[str]] = mapped_column(String(512))
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    filed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    evidence_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    resolution_deadline: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    current_status: Mapped[DisputeStatus] = mapped_column(
        Enum(DisputeStatus, name="dispute_status", create_constraint=True),
        default=DisputeStatus.EVIDENCE_PENDING,
        server_default="EVIDENCE_PENDING",
        index=True,
    )
    won: Mapped[Optional[bool]] = mapped_column(Boolean, default=None)
    outcome_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # ── Relationships ──────────────────────────────────────────────────
    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="disputes")
    transaction: Mapped["Transaction"] = relationship("Transaction")
    refund: Mapped[Optional["Refund"]] = relationship(
        "Refund",
        foreign_keys="Dispute.related_refund_id",
        remote_side="Refund.id",
    )
    evidence: Mapped[List["DisputeEvidence"]] = relationship(
        "DisputeEvidence", back_populates="dispute", cascade="all, delete-orphan"
    )
    anomalies: Mapped[List["Anomaly"]] = relationship(
        "Anomaly", back_populates="dispute"
    )

    __table_args__ = (
        Index("ix_disputes_merchant_status", "merchant_id", "current_status"),
        Index("ix_disputes_filed_at", "filed_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<Dispute id={self.id} type={self.type} "
            f"status={self.current_status}>"
        )

    def __str__(self) -> str:
        return f"Dispute {self.id} ({self.current_status})"


class DisputeEvidence(Base):
    """Evidence submitted for a dispute."""

    __tablename__ = "dispute_evidence"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_new_uuid
    )
    dispute_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("disputes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    evidence_type: Mapped[EvidenceType] = mapped_column(
        Enum(EvidenceType, name="evidence_type", create_constraint=True),
        nullable=False,
    )
    file_url: Mapped[Optional[str]] = mapped_column(String(1024))
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )

    # ── Relationships ──────────────────────────────────────────────────
    dispute: Mapped["Dispute"] = relationship("Dispute", back_populates="evidence")

    def __repr__(self) -> str:
        return (
            f"<DisputeEvidence id={self.id} type={self.evidence_type} "
            f"verified={self.is_verified}>"
        )

    def __str__(self) -> str:
        return f"Evidence {self.evidence_type}"


class DisputeEvidenceTemplate(Base):
    """Maps dispute reason codes to recommended evidence types."""

    __tablename__ = "dispute_evidence_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reason_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    reason_description: Mapped[Optional[str]] = mapped_column(String(512))
    required_evidence_types: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    template_text: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("reason_code", name="uq_evidence_template_reason_code"),
    )

    def __repr__(self) -> str:
        return f"<DisputeEvidenceTemplate code={self.reason_code!r}>"

    def __str__(self) -> str:
        return f"Template for {self.reason_code}"


class Anomaly(Base):
    """Detected operational anomaly."""

    __tablename__ = "anomalies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_new_uuid
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    anomaly_type: Mapped[AnomalyType] = mapped_column(
        Enum(AnomalyType, name="anomaly_type", create_constraint=True),
        nullable=False,
        index=True,
    )
    related_settlement_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("settlements.id", ondelete="SET NULL"),
        index=True,
    )
    related_refund_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("refunds.id", ondelete="SET NULL"),
        index=True,
    )
    related_dispute_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("disputes.id", ondelete="SET NULL"),
        index=True,
    )
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    root_cause: Mapped[Optional[str]] = mapped_column(String(512))
    root_cause_confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2))
    status: Mapped[AnomalyStatus] = mapped_column(
        Enum(AnomalyStatus, name="anomaly_status", create_constraint=True),
        default=AnomalyStatus.OPEN,
        server_default="OPEN",
        index=True,
    )
    severity: Mapped[SeverityLevel] = mapped_column(
        Enum(SeverityLevel, name="severity_level_anomaly", create_constraint=True),
        default=SeverityLevel.WARNING,
        server_default="WARNING",
        index=True,
    )
    recommended_action: Mapped[Optional[str]] = mapped_column(Text)
    merchant_action_taken: Mapped[Optional[str]] = mapped_column(String(256))
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # ── Relationships ──────────────────────────────────────────────────
    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="anomalies")
    settlement: Mapped[Optional["Settlement"]] = relationship(
        "Settlement", back_populates="anomalies"
    )
    refund: Mapped[Optional["Refund"]] = relationship(
        "Refund", back_populates="anomalies"
    )
    dispute: Mapped[Optional["Dispute"]] = relationship(
        "Dispute", back_populates="anomalies"
    )
    diagnosis: Mapped[Optional["Diagnosis"]] = relationship(
        "Diagnosis", back_populates="anomaly", uselist=False, cascade="all, delete-orphan"
    )
    recommendations: Mapped[List["Recommendation"]] = relationship(
        "Recommendation", back_populates="anomaly", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_anomalies_merchant_status", "merchant_id", "status"),
        Index("ix_anomalies_severity_detected", "severity", "detected_at"),
    )

    @validates("root_cause_confidence")
    def _validate_confidence(self, _key: str, value: Any) -> Any:
        if value is not None and (value < 0 or value > 1):
            raise ValueError(f"root_cause_confidence must be 0-1, got {value}")
        return value

    def __repr__(self) -> str:
        return (
            f"<Anomaly id={self.id} type={self.anomaly_type} "
            f"severity={self.severity}>"
        )

    def __str__(self) -> str:
        return f"Anomaly {self.anomaly_type} ({self.severity})"


class Diagnosis(Base):
    """Root-cause analysis for an anomaly (LLM-generated)."""

    __tablename__ = "diagnoses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_new_uuid
    )
    anomaly_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("anomalies.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    root_cause_category: Mapped[Optional[str]] = mapped_column(String(128))
    root_cause_subcategory: Mapped[Optional[str]] = mapped_column(String(128))
    explanation_plain_english: Mapped[Optional[str]] = mapped_column(Text)
    confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2))
    evidence: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    causal_chain: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ──────────────────────────────────────────────────
    anomaly: Mapped["Anomaly"] = relationship("Anomaly", back_populates="diagnosis")

    @validates("confidence")
    def _validate_confidence(self, _key: str, value: Any) -> Any:
        if value is not None and (value < 0 or value > 1):
            raise ValueError(f"confidence must be 0-1, got {value}")
        return value

    def __repr__(self) -> str:
        return (
            f"<Diagnosis id={self.id} category={self.root_cause_category!r} "
            f"confidence={self.confidence}>"
        )

    def __str__(self) -> str:
        return f"Diagnosis: {self.root_cause_category}"


class Recommendation(Base):
    """Recommended action for an anomaly."""

    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_new_uuid
    )
    anomaly_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("anomalies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recommendation_text: Mapped[Optional[str]] = mapped_column(Text)
    recommended_action: Mapped[RecommendedAction] = mapped_column(
        Enum(RecommendedAction, name="recommended_action", create_constraint=True),
        nullable=False,
    )
    urgency: Mapped[UrgencyLevel] = mapped_column(
        Enum(UrgencyLevel, name="urgency_level", create_constraint=True),
        default=UrgencyLevel.MEDIUM,
        server_default="MEDIUM",
    )
    timeline: Mapped[Optional[str]] = mapped_column(String(64))
    expected_resolution_time_hours: Mapped[Optional[int]] = mapped_column(Integer)
    success_probability: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2))
    merchant_followed: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    outcome_if_followed: Mapped[Optional[str]] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ──────────────────────────────────────────────────
    anomaly: Mapped["Anomaly"] = relationship(
        "Anomaly", back_populates="recommendations"
    )

    @validates("success_probability")
    def _validate_probability(self, _key: str, value: Any) -> Any:
        if value is not None and (value < 0 or value > 1):
            raise ValueError(f"success_probability must be 0-1, got {value}")
        return value

    def __repr__(self) -> str:
        return (
            f"<Recommendation id={self.id} action={self.recommended_action} "
            f"urgency={self.urgency}>"
        )

    def __str__(self) -> str:
        return f"Recommendation: {self.recommended_action}"


class EvaluationMetric(Base):
    """Measurement data for agent performance and operational KPIs."""

    __tablename__ = "evaluation_metrics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_new_uuid
    )
    merchant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id", ondelete="SET NULL"),
        index=True,
    )
    metric_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    metric_value: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    metric_unit: Mapped[Optional[str]] = mapped_column(String(32))
    dimensions: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_eval_metrics_name_time", "metric_name", "recorded_at"),
        Index("ix_eval_metrics_merchant_name", "merchant_id", "metric_name"),
    )

    def __repr__(self) -> str:
        return (
            f"<EvaluationMetric name={self.metric_name!r} "
            f"value={self.metric_value}>"
        )

    def __str__(self) -> str:
        return f"{self.metric_name}: {self.metric_value} {self.metric_unit or ''}"
