"""Data-access repository layer.

Every public function accepts an ``AsyncSession`` so callers control the
transaction boundary.  Methods are grouped into classes per aggregate root
for discoverability, but standalone helpers are also available.

Usage:
    repo = MerchantRepository(session)
    merchant = await repo.get(merchant_id)
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Generic, List, Optional, Type, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute
from src.data.models import (
    Anomaly,
    AnomalyStatus,
    Base,
    Diagnosis,
    Dispute,
    DisputeEvidence,
    DisputeEvidenceTemplate,
    DisputeStatus,
    EvaluationMetric,
    Merchant,
    Recommendation,
    Refund,
    RefundStatus,
    Settlement,
    SettlementAttempt,
    SettlementStatus,
    SeverityLevel,
    Transaction,
    UrgencyLevel,
)

logger = logging.getLogger(__name__)

M = TypeVar("M", bound=Base)


# ── Generic CRUD base ──────────────────────────────────────────────────────────


class BaseRepository(Generic[M]):
    """Minimal generic CRUD for any model."""

    model: Type[M]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Read ───────────────────────────────────────────────────────────

    async def get(self, pk: Any) -> Optional[M]:
        """Fetch a single record by primary key."""
        obj = await self.session.get(self.model, pk)
        if obj is None:
            logger.debug("%s.get(%s) → None", self.model.__name__, pk)
        return obj

    async def get_or_fail(self, pk: Any) -> M:
        """Fetch or raise ``LookupError``."""
        obj = await self.get(pk)
        if obj is None:
            raise LookupError(f"{self.model.__name__} {pk} not found")
        return obj

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        order_by: Optional[InstrumentedAttribute] = None,
        descending: bool = False,
    ) -> List[M]:
        """Return a page of records."""
        stmt: Select = select(self.model)
        if order_by is not None:
            stmt = stmt.order_by(order_by.desc() if descending else order_by)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(self, **filters: Any) -> int:
        """Count rows matching optional keyword filters."""
        stmt = select(func.count()).select_from(self.model)
        for col_name, val in filters.items():
            col = getattr(self.model, col_name, None)
            if col is not None:
                stmt = stmt.where(col == val)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    # ── Write ──────────────────────────────────────────────────────────

    async def create(self, **kwargs: Any) -> M:
        """Insert and flush; returns the new instance."""
        obj = self.model(**kwargs)
        self.session.add(obj)
        await self.session.flush()
        logger.info("%s created (%s)", self.model.__name__, _pk_value(obj))
        return obj

    async def create_many(self, rows: List[dict]) -> List[M]:
        """Bulk-insert a list of dicts."""
        objects = [self.model(**r) for r in rows]
        self.session.add_all(objects)
        await self.session.flush()
        logger.info("%s bulk-created %d rows", self.model.__name__, len(objects))
        return objects

    async def update(self, pk: Any, **fields: Any) -> Optional[M]:
        """Partial update by primary key."""
        obj = await self.get(pk)
        if obj is None:
            return None
        for key, val in fields.items():
            setattr(obj, key, val)
        await self.session.flush()
        logger.info("%s updated (%s): %s", self.model.__name__, pk, list(fields))
        return obj

    async def delete(self, pk: Any) -> bool:
        """Delete by primary key. Returns True if deleted."""
        obj = await self.get(pk)
        if obj is None:
            return False
        await self.session.delete(obj)
        await self.session.flush()
        logger.info("%s deleted (%s)", self.model.__name__, pk)
        return True

    async def exists(self, pk: Any) -> bool:
        return (await self.get(pk)) is not None


# ── Helpers ────────────────────────────────────────────────────────────────────


def _pk_value(obj: Base) -> Any:
    """Extract the first PK column value (for logging)."""
    for col in obj.__table__.primary_key.columns:
        return getattr(obj, col.key)
    return "?"


# ── Merchant ───────────────────────────────────────────────────────────────────


class MerchantRepository(BaseRepository[Merchant]):
    model = Merchant

    async def get_by_name(self, name: str) -> Optional[Merchant]:
        stmt = select(Merchant).where(Merchant.business_name == name).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def search(self, query: str, *, limit: int = 20) -> List[Merchant]:
        """Case-insensitive substring search on business_name."""
        stmt = (
            select(Merchant)
            .where(Merchant.business_name.ilike(f"%{query}%"))
            .order_by(Merchant.business_name)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_industry(
        self, industry: str, *, offset: int = 0, limit: int = 50
    ) -> List[Merchant]:
        stmt = (
            select(Merchant)
            .where(Merchant.industry_category == industry)
            .order_by(Merchant.business_name)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


# ── Settlement ─────────────────────────────────────────────────────────────────


class SettlementRepository(BaseRepository[Settlement]):
    model = Settlement

    async def list_by_merchant(
        self,
        merchant_id: uuid.UUID,
        *,
        status: Optional[SettlementStatus] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> List[Settlement]:
        stmt = select(Settlement).where(Settlement.merchant_id == merchant_id)
        if status is not None:
            stmt = stmt.where(Settlement.status == status)
        stmt = stmt.order_by(Settlement.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_pending(self) -> List[Settlement]:
        """All settlements still awaiting completion."""
        stmt = (
            select(Settlement)
            .where(
                Settlement.status.in_([SettlementStatus.PENDING, SettlementStatus.INITIATED])
            )
            .order_by(Settlement.created_at)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def overdue_settlements(self) -> List[Settlement]:
        """Settlements past expected arrival that haven't succeeded."""
        now = datetime.utcnow()
        stmt = (
            select(Settlement)
            .where(
                Settlement.expected_arrival_at < now,
                Settlement.status.notin_(
                    [SettlementStatus.SUCCESS, SettlementStatus.FAILED]
                ),
            )
            .order_by(Settlement.expected_arrival_at)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


# ── Settlement Attempt ─────────────────────────────────────────────────────────


class SettlementAttemptRepository(BaseRepository[SettlementAttempt]):
    model = SettlementAttempt

    async def list_by_settlement(
        self, settlement_id: str, *, limit: int = 20
    ) -> List[SettlementAttempt]:
        stmt = (
            select(SettlementAttempt)
            .where(SettlementAttempt.settlement_id == settlement_id)
            .order_by(SettlementAttempt.attempt_number)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def next_attempt_number(self, settlement_id: str) -> int:
        stmt = (
            select(func.coalesce(func.max(SettlementAttempt.attempt_number), 0))
            .where(SettlementAttempt.settlement_id == settlement_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() + 1


# ── Transaction ────────────────────────────────────────────────────────────────


class TransactionRepository(BaseRepository[Transaction]):
    model = Transaction

    async def list_by_merchant(
        self, merchant_id: uuid.UUID, *, offset: int = 0, limit: int = 50
    ) -> List[Transaction]:
        stmt = (
            select(Transaction)
            .where(Transaction.merchant_id == merchant_id)
            .order_by(Transaction.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


# ── Refund ─────────────────────────────────────────────────────────────────────


class RefundRepository(BaseRepository[Refund]):
    model = Refund

    async def list_by_merchant(
        self,
        merchant_id: uuid.UUID,
        *,
        status: Optional[RefundStatus] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> List[Refund]:
        stmt = select(Refund).where(Refund.merchant_id == merchant_id)
        if status is not None:
            stmt = stmt.where(Refund.status == status)
        stmt = stmt.order_by(Refund.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_transaction(self, transaction_id: str) -> List[Refund]:
        stmt = (
            select(Refund)
            .where(Refund.transaction_id == transaction_id)
            .order_by(Refund.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def stuck_refunds(self, since_hours: int = 24) -> List[Refund]:
        """Refunds stuck in non-terminal status for too long."""
        cutoff = datetime.utcnow()
        stmt = (
            select(Refund)
            .where(
                Refund.status.in_(
                    [RefundStatus.INITIATED, RefundStatus.PENDING, RefundStatus.PROCESSING]
                ),
                Refund.created_at < cutoff,
            )
            .order_by(Refund.created_at)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


# ── Dispute ────────────────────────────────────────────────────────────────────


class DisputeRepository(BaseRepository[Dispute]):
    model = Dispute

    async def list_by_merchant(
        self,
        merchant_id: uuid.UUID,
        *,
        status: Optional[DisputeStatus] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> List[Dispute]:
        stmt = select(Dispute).where(Dispute.merchant_id == merchant_id)
        if status is not None:
            stmt = stmt.where(Dispute.current_status == status)
        stmt = stmt.order_by(Dispute.filed_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def open_disputes(self) -> List[Dispute]:
        """All disputes still requiring action."""
        stmt = (
            select(Dispute)
            .where(
                Dispute.current_status.in_(
                    [DisputeStatus.EVIDENCE_PENDING, DisputeStatus.UNDER_REVIEW]
                )
            )
            .order_by(Dispute.evidence_deadline)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def approaching_deadline(self, within_hours: int = 48) -> List[Dispute]:
        """Disputes whose evidence deadline is within *within_hours* from now."""
        now = datetime.utcnow()
        from datetime import timedelta

        cutoff = now + timedelta(hours=within_hours)
        stmt = (
            select(Dispute)
            .where(
                Dispute.evidence_deadline.isnot(None),
                Dispute.evidence_deadline <= cutoff,
                Dispute.current_status.in_(
                    [DisputeStatus.EVIDENCE_PENDING, DisputeStatus.UNDER_REVIEW]
                ),
            )
            .order_by(Dispute.evidence_deadline)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


# ── Dispute Evidence ───────────────────────────────────────────────────────────


class DisputeEvidenceRepository(BaseRepository[DisputeEvidence]):
    model = DisputeEvidence

    async def list_by_dispute(self, dispute_id: str) -> List[DisputeEvidence]:
        stmt = (
            select(DisputeEvidence)
            .where(DisputeEvidence.dispute_id == dispute_id)
            .order_by(DisputeEvidence.uploaded_at)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


# ── Dispute Evidence Template ──────────────────────────────────────────────────


class DisputeEvidenceTemplateRepository(BaseRepository[DisputeEvidenceTemplate]):
    model = DisputeEvidenceTemplate

    async def get_by_reason_code(
        self, reason_code: str
    ) -> Optional[DisputeEvidenceTemplate]:
        stmt = (
            select(DisputeEvidenceTemplate)
            .where(DisputeEvidenceTemplate.reason_code == reason_code)
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


# ── Anomaly ────────────────────────────────────────────────────────────────────


class AnomalyRepository(BaseRepository[Anomaly]):
    model = Anomaly

    async def list_by_merchant(
        self,
        merchant_id: uuid.UUID,
        *,
        status: Optional[AnomalyStatus] = None,
        severity: Optional[SeverityLevel] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> List[Anomaly]:
        stmt = select(Anomaly).where(Anomaly.merchant_id == merchant_id)
        if status is not None:
            stmt = stmt.where(Anomaly.status == status)
        if severity is not None:
            stmt = stmt.where(Anomaly.severity == severity)
        stmt = stmt.order_by(Anomaly.detected_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def open_anomalies(
        self, *, severity: Optional[SeverityLevel] = None
    ) -> List[Anomaly]:
        stmt = select(Anomaly).where(Anomaly.status == AnomalyStatus.OPEN)
        if severity is not None:
            stmt = stmt.where(Anomaly.severity == severity)
        stmt = stmt.order_by(Anomaly.detected_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_type(
        self, merchant_id: uuid.UUID
    ) -> List[tuple]:
        """Return ``[(anomaly_type, count), ...]`` grouped by type."""
        stmt = (
            select(Anomaly.anomaly_type, func.count(Anomaly.id))
            .where(Anomaly.merchant_id == merchant_id)
            .group_by(Anomaly.anomaly_type)
            .order_by(func.count(Anomaly.id).desc())
        )
        result = await self.session.execute(stmt)
        return list(result.all())


# ── Diagnosis ──────────────────────────────────────────────────────────────────


class DiagnosisRepository(BaseRepository[Diagnosis]):
    model = Diagnosis

    async def get_for_anomaly(self, anomaly_id: uuid.UUID) -> Optional[Diagnosis]:
        stmt = (
            select(Diagnosis)
            .where(Diagnosis.anomaly_id == anomaly_id)
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


# ── Recommendation ─────────────────────────────────────────────────────────────


class RecommendationRepository(BaseRepository[Recommendation]):
    model = Recommendation

    async def list_for_anomaly(self, anomaly_id: uuid.UUID) -> List[Recommendation]:
        stmt = (
            select(Recommendation)
            .where(Recommendation.anomaly_id == anomaly_id)
            .order_by(Recommendation.created_at)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def unfollowed_by_urgency(
        self, urgency: UrgencyLevel
    ) -> List[Recommendation]:
        stmt = (
            select(Recommendation)
            .where(
                Recommendation.urgency == urgency,
                Recommendation.merchant_followed == False,  # noqa: E712
            )
            .order_by(Recommendation.created_at)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


# ── Evaluation Metrics ─────────────────────────────────────────────────────────


class EvaluationMetricRepository(BaseRepository[EvaluationMetric]):
    model = EvaluationMetric

    async def list_by_name(
        self,
        metric_name: str,
        *,
        merchant_id: Optional[uuid.UUID] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> List[EvaluationMetric]:
        stmt = select(EvaluationMetric).where(
            EvaluationMetric.metric_name == metric_name
        )
        if merchant_id is not None:
            stmt = stmt.where(EvaluationMetric.merchant_id == merchant_id)
        stmt = stmt.order_by(EvaluationMetric.recorded_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def latest_value(
        self, metric_name: str, merchant_id: Optional[uuid.UUID] = None
    ) -> Optional[EvaluationMetric]:
        stmt = select(EvaluationMetric).where(
            EvaluationMetric.metric_name == metric_name
        )
        if merchant_id is not None:
            stmt = stmt.where(EvaluationMetric.merchant_id == merchant_id)
        stmt = stmt.order_by(EvaluationMetric.recorded_at.desc()).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
