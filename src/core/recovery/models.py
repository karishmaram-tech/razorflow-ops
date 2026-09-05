"""
Data models for RecoveryFlow.
All agents communicate via these shared types.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


# ─── Enums ───────────────────────────────────────────────

class FailureType(str, Enum):
    TEMPORARY = "temporary"
    RISKY = "risky"
    PERMANENT = "permanent"
    AMBIGUOUS = "ambiguous"


class CustomerSegment(str, Enum):
    HIGH_LTV_STABLE = "high_ltv_stable"
    MID_LTV_TRANSIENT = "mid_ltv_transient"
    LOW_LTV_AT_RISK = "low_ltv_at_risk"


class RiskAction(str, Enum):
    PROCEED = "PROCEED"
    CAUTION = "CAUTION"
    ESCALATE = "ESCALATE"
    VETO = "VETO"


class RecoveryAction(str, Enum):
    EXECUTE_RECOVERY = "EXECUTE_RECOVERY"
    ESCALATE_TO_HUMAN = "ESCALATE_TO_HUMAN"
    SKIP = "SKIP"
    DOWNGRADE = "DOWNGRADE"
    STOP = "STOP"


class RecoveryOutcome(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    CHARGEBACK = "chargeback"
    COMPLAINT = "complaint"
    PENDING = "pending"


class WorkflowState(str, Enum):
    INVESTIGATING = "INVESTIGATING"
    PREDICTING = "PREDICTING"
    ASSESSING_RISK = "ASSESSING_RISK"
    CALCULATING_ECONOMICS = "CALCULATING_ECONOMICS"
    DECIDING = "DECIDING"
    EXECUTING = "EXECUTING"
    AWAITING_OUTCOME = "AWAITING_OUTCOME"
    VERIFYING = "VERIFYING"
    LEARNING = "LEARNING"
    COMPLETE = "COMPLETE"
    ESCALATED = "ESCALATED"
    SKIPPED = "SKIPPED"


STRATEGY_COSTS = {
    "email_only": 0.01,
    "sms_link": 0.08,
    "payment_link": 0.05,
    "support_call": 25.00,
    "retry_immediate": 0.08,
    "retry_tomorrow": 0.05,
    "backup_method": 0.05,
}


# ─── Core Data Types ────────────────────────────────────

@dataclass
class Customer:
    id: str
    name: str
    email: str
    phone: str
    tenure_months: int
    ltv_estimate: float
    subscription_monthly: float
    payment_success_count: int
    chargeback_count: int
    complaint_count: int
    backup_payment_methods: int
    device_consistency: float = 0.95
    geography_consistency: float = 0.98
    segment: CustomerSegment = CustomerSegment.MID_LTV_TRANSIENT
    recovery_opt_out: bool = False


@dataclass
class PaymentFailure:
    id: str
    subscription_id: str
    customer_id: str
    merchant_id: str
    amount: float
    failure_reason: str
    failure_code: str
    processor_code: str
    backup_methods_available: int
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class InvestigationResult:
    failure_type: FailureType
    recoverability_score: float
    recovery_paths: list
    risk_signals: list
    confidence: float
    reasoning: str
    agent_name: str = "Failure Investigator"


@dataclass
class PredictionResult:
    recovery_probabilities: dict  # strategy -> {probability, confidence}
    best_strategy_by_prob: str
    customer_segment: str
    average_confidence: float
    agent_name: str = "Recoverability Predictor"


@dataclass
class RiskAssessment:
    chargeback_propensity: float
    fraud_probability: float
    operational_risk: float
    total_risk_score: float
    risk_action: RiskAction
    recommended_strategy: Optional[str]
    reasoning: str
    agent_name: str = "Risk Assessment"


@dataclass
class EconomicsResult:
    strategy_economics: dict  # strategy -> {enr, roi, recommendation}
    best_strategy_by_economics: str
    total_enr: float
    recommendation: str
    agent_name: str = "Economics"


@dataclass
class StrategyDecision:
    action: RecoveryAction
    strategy: str
    timing: str
    communication: str
    fallback_action: Optional[str]
    confidence_score: float
    execution_plan: dict
    reasoning: dict
    agent_name: str = "Strategy"


@dataclass
class RecoveryAttempt:
    id: str
    payment_failure: PaymentFailure
    customer: Customer
    investigation: Optional[InvestigationResult] = None
    prediction: Optional[PredictionResult] = None
    risk: Optional[RiskAssessment] = None
    economics: Optional[EconomicsResult] = None
    decision: Optional[StrategyDecision] = None
    state: WorkflowState = WorkflowState.INVESTIGATING
    outcome: RecoveryOutcome = RecoveryOutcome.PENDING
    cost: float = 0.0
    revenue_recovered: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "customer_name": self.customer.name,
            "subscription_amount": self.customer.subscription_monthly,
            "segment": self.customer.segment.value,
            "failure_reason": self.payment_failure.failure_reason,
            "amount": self.payment_failure.amount,
            "state": self.state.value,
            "strategy": self.decision.strategy if self.decision else None,
            "confidence": self.decision.confidence_score if self.decision else None,
            "outcome": self.outcome.value,
            "cost": self.cost,
            "revenue_recovered": self.revenue_recovered,
            "agent_outputs": self._agent_outputs(),
            "created_at": self.created_at.isoformat(),
        }

    def _agent_outputs(self) -> dict:
        out = {}
        if self.investigation:
            out["investigator"] = {
                "failure_type": self.investigation.failure_type.value,
                "recoverability": self.investigation.recoverability_score,
                "confidence": self.investigation.confidence,
                "reasoning": self.investigation.reasoning,
            }
        if self.prediction:
            out["predictor"] = {
                "probabilities": self.prediction.recovery_probabilities,
                "best": self.prediction.best_strategy_by_prob,
                "confidence": self.prediction.average_confidence,
            }
        if self.risk:
            out["risk"] = {
                "chargeback_risk": self.risk.chargeback_propensity,
                "fraud_risk": self.risk.fraud_probability,
                "total_risk": self.risk.total_risk_score,
                "action": self.risk.risk_action.value,
                "reasoning": self.risk.reasoning,
            }
        if self.economics:
            out["economics"] = {
                "strategies": self.economics.strategy_economics,
                "best": self.economics.best_strategy_by_economics,
                "total_enr": self.economics.total_enr,
                "recommendation": self.economics.recommendation,
            }
        if self.decision:
            out["strategy"] = {
                "action": self.decision.action.value,
                "strategy": self.decision.strategy,
                "confidence": self.decision.confidence_score,
                "reasoning": self.decision.reasoning,
            }
        return out
