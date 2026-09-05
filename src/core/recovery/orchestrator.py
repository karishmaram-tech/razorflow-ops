"""
RecoveryFlow Orchestrator
Runs the full multi-agent recovery workflow end-to-end.
"""
import time
from datetime import datetime
from typing import Callable, Optional

from .models import (
    RecoveryAttempt, WorkflowState, RecoveryOutcome,
    PaymentFailure, Customer,
)
from .investigator import investigate
from .predictor import predict
from .risk import assess
from .economics import calculate
from .strategy import decide
from .learning import process_outcome, get_bandit
from .synthetic_data import simulate_outcome


class RecoveryOrchestrator:
    """
    Orchestrates the 6-agent recovery workflow.
    Supports a callback for live event streaming to frontend.
    """

    def __init__(self, on_event: Optional[Callable] = None):
        self.on_event = on_event or (lambda *a, **kw: None)
        self.attempts: list[RecoveryAttempt] = []

    def _emit(self, event_type: str, data: dict):
        self.on_event(event_type, {
            **data,
            "timestamp": datetime.utcnow().isoformat(),
        })

    def process_failure(self, customer: Customer,
                        failure: PaymentFailure) -> RecoveryAttempt:
        """
        Run the full 6-agent workflow for a single payment failure.
        Returns the RecoveryAttempt with all agent outputs.
        """
        attempt = RecoveryAttempt(
            id=f"rec_{failure.id}",
            payment_failure=failure,
            customer=customer,
        )
        self.attempts.append(attempt)

        self._emit("recovery_started", {
            "attempt_id": attempt.id,
            "customer": customer.name,
            "amount": failure.amount,
            "failure_reason": failure.failure_reason,
        })

        # ─── Stage 1: Investigation ──────────────────────
        attempt.state = WorkflowState.INVESTIGATING
        self._emit("state_changed", {
            "attempt_id": attempt.id,
            "state": "INVESTIGATING",
            "agent": "Failure Investigator",
            "detail": f"Analyzing failure: {failure.failure_reason}",
        })
        time.sleep(0.05)  # Simulate processing

        investigation = investigate(failure, customer)
        attempt.investigation = investigation
        self._emit("agent_complete", {
            "attempt_id": attempt.id,
            "agent": "investigator",
            "result": {
                "failure_type": investigation.failure_type.value,
                "recoverability": investigation.recoverability_score,
                "confidence": investigation.confidence,
                "reasoning": investigation.reasoning,
            },
        })

        # ─── Stage 2: Prediction ─────────────────────────
        attempt.state = WorkflowState.PREDICTING
        self._emit("state_changed", {
            "attempt_id": attempt.id,
            "state": "PREDICTING",
            "agent": "Recoverability Predictor",
            "detail": "Running ML models on recovery probabilities",
        })
        time.sleep(0.05)

        prediction = predict(customer, failure, investigation)
        attempt.prediction = prediction
        self._emit("agent_complete", {
            "attempt_id": attempt.id,
            "agent": "predictor",
            "result": {
                "probabilities": prediction.recovery_probabilities,
                "best_strategy": prediction.best_strategy_by_prob,
                "confidence": prediction.average_confidence,
            },
        })

        # ─── Stage 3: Risk Assessment (parallel with predict in prod) ──
        attempt.state = WorkflowState.ASSESSING_RISK
        self._emit("state_changed", {
            "attempt_id": attempt.id,
            "state": "ASSESSING_RISK",
            "agent": "Risk Assessment",
            "detail": "Evaluating chargeback, fraud, operational risk",
        })
        time.sleep(0.05)

        risk_result = assess(customer, failure, investigation, prediction)
        attempt.risk = risk_result
        self._emit("agent_complete", {
            "attempt_id": attempt.id,
            "agent": "risk",
            "result": {
                "chargeback_risk": risk_result.chargeback_propensity,
                "fraud_risk": risk_result.fraud_probability,
                "total_risk": risk_result.total_risk_score,
                "action": risk_result.risk_action.value,
                "reasoning": risk_result.reasoning,
            },
        })

        # ─── Stage 4: Economics ──────────────────────────
        attempt.state = WorkflowState.CALCULATING_ECONOMICS
        self._emit("state_changed", {
            "attempt_id": attempt.id,
            "state": "CALCULATING_ECONOMICS",
            "agent": "Economics Agent",
            "detail": "Computing Expected Net Recovery for each strategy",
        })
        time.sleep(0.05)

        economics = calculate(customer, failure, prediction, risk_result)
        attempt.economics = economics
        self._emit("agent_complete", {
            "attempt_id": attempt.id,
            "agent": "economics",
            "result": {
                "strategies": economics.strategy_economics,
                "best": economics.best_strategy_by_economics,
                "total_enr": economics.total_enr,
                "recommendation": economics.recommendation,
            },
        })

        # ─── Stage 5: Strategy Decision ──────────────────
        attempt.state = WorkflowState.DECIDING
        self._emit("state_changed", {
            "attempt_id": attempt.id,
            "state": "DECIDING",
            "agent": "Strategy Agent",
            "detail": "Integrating all agent inputs, resolving conflicts",
        })
        time.sleep(0.05)

        decision = decide(customer, failure, investigation, prediction,
                         risk_result, economics)
        attempt.decision = decision
        self._emit("agent_complete", {
            "attempt_id": attempt.id,
            "agent": "strategy",
            "result": {
                "action": decision.action.value,
                "strategy": decision.strategy,
                "confidence": decision.confidence_score,
                "reasoning": decision.reasoning,
            },
        })

        # ─── Stage 6: Execution ──────────────────────────
        if decision.action.value == "EXECUTE_RECOVERY":
            attempt.state = WorkflowState.EXECUTING
            self._emit("state_changed", {
                "attempt_id": attempt.id,
                "state": "EXECUTING",
                "agent": "Execution Agent",
                "detail": f"Executing {decision.strategy} — {decision.communication[:60]}...",
            })
            time.sleep(0.05)

            # Simulate execution
            attempt.cost = decision.execution_plan.get("limits", {}).get(
                "max_spend", 0.08)

            # Simulate outcome
            outcome = simulate_outcome(decision.strategy, customer)

            self._emit("recovery_executed", {
                "attempt_id": attempt.id,
                "strategy": decision.strategy,
                "cost": attempt.cost,
                "simulated_outcome": outcome["outcome"],
            })

            # ─── Stage 7: Learning ───────────────────────
            attempt.state = WorkflowState.LEARNING
            self._emit("state_changed", {
                "attempt_id": attempt.id,
                "state": "LEARNING",
                "agent": "Learning Agent",
                "detail": "Updating models and bandit beliefs",
            })

            learning = process_outcome(
                segment=customer.segment.value,
                strategy=decision.strategy,
                recovered=outcome["recovered"],
                predicted_probability=prediction.recovery_probabilities.get(
                    decision.strategy, {}).get("probability", 0.5),
                chargeback=outcome["chargeback"],
            )

            attempt.outcome = RecoveryOutcome(outcome["outcome"])
            attempt.revenue_recovered = outcome["recovered_amount"]
            attempt.cost = outcome["cost"]
            attempt.state = WorkflowState.COMPLETE
            attempt.completed_at = datetime.utcnow()

            self._emit("recovery_complete", {
                "attempt_id": attempt.id,
                "outcome": outcome["outcome"],
                "recovered_amount": outcome["recovered_amount"],
                "cost": outcome["cost"],
                "learning": learning,
            })

        elif decision.action.value == "ESCALATE_TO_HUMAN":
            attempt.state = WorkflowState.ESCALATED
            self._emit("recovery_escalated", {
                "attempt_id": attempt.id,
                "reason": decision.reasoning,
            })

        else:  # SKIP
            attempt.state = WorkflowState.SKIPPED
            self._emit("recovery_skipped", {
                "attempt_id": attempt.id,
                "reason": decision.reasoning,
            })

        return attempt

    def get_stats(self) -> dict:
        """Aggregate stats for all processed attempts."""
        total = len(self.attempts)
        if total == 0:
            return {"total": 0}

        recovered = sum(1 for a in self.attempts
                       if a.outcome == RecoveryOutcome.SUCCESS)
        chargebacks = sum(1 for a in self.attempts
                         if a.outcome == RecoveryOutcome.CHARGEBACK)
        escalated = sum(1 for a in self.attempts
                       if a.state == WorkflowState.ESCALATED)
        skipped = sum(1 for a in self.attempts
                     if a.state == WorkflowState.SKIPPED)

        total_revenue = sum(a.revenue_recovered for a in self.attempts)
        total_cost = sum(a.cost for a in self.attempts)
        total_risk = sum(1 for a in self.attempts
                        if a.risk and a.risk.risk_action.value in ("CAUTION", "ESCALATE"))

        # By segment
        segments = {}
        for a in self.attempts:
            seg = a.customer.segment.value
            if seg not in segments:
                segments[seg] = {"total": 0, "recovered": 0, "revenue": 0}
            segments[seg]["total"] += 1
            if a.outcome == RecoveryOutcome.SUCCESS:
                segments[seg]["recovered"] += 1
            segments[seg]["revenue"] += a.revenue_recovered

        # By strategy
        strategies = {}
        for a in self.attempts:
            if a.decision and a.decision.strategy != "none":
                s = a.decision.strategy
                if s not in strategies:
                    strategies[s] = {"attempted": 0, "recovered": 0, "cost": 0}
                strategies[s]["attempted"] += 1
                if a.outcome == RecoveryOutcome.SUCCESS:
                    strategies[s]["recovered"] += 1
                strategies[s]["cost"] += a.cost

        return {
            "total": total,
            "recovered": recovered,
            "recovery_rate": round(recovered / total, 3) if total else 0,
            "chargebacks": chargebacks,
            "escalated": escalated,
            "skipped": skipped,
            "total_risk_managed": total_risk,
            "total_revenue_recovered": round(total_revenue, 2),
            "total_cost": round(total_cost, 2),
            "net_recovery": round(total_revenue - total_cost, 2),
            "roi": round((total_revenue - total_cost) / max(0.01, total_cost), 0),
            "by_segment": segments,
            "by_strategy": strategies,
        }
