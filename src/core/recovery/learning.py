"""
Agent 6: Learning & Feedback Agent
Thompson Sampling (contextual bandits) for strategy selection,
model degradation detection, and outcome tracking.
"""
import random
import math
from dataclasses import dataclass, field
from typing import Dict
from .models import CustomerSegment


STRATEGIES = [
    "retry_immediate", "retry_tomorrow", "backup_method",
    "sms_link", "email_only", "payment_link", "support_call",
]

# ─── Thompson Sampling Bandit ───────────────────────────

@dataclass
class BetaBelief:
    alpha: float
    beta: float

    @property
    def mean(self) -> float:
        return self.alpha / (self.alpha + self.beta)

    @property
    def variance(self) -> float:
        a, b = self.alpha, self.beta
        return (a * b) / ((a + b) ** 2 * (a + b + 1))

    def sample(self) -> float:
        """Sample from Beta(alpha, beta) posterior."""
        return random.betavariate(self.alpha, self.beta)

    def update(self, success: bool, weight: float = 1.0):
        if success:
            self.alpha += weight
        else:
            self.beta += weight


class StrategyBandit:
    """
    Per-segment contextual bandit for strategy selection.
    Uses Thompson Sampling for efficient exploration/exploitation.
    """

    # Pre-seeded beliefs from industry data
    SEEDS = {
        CustomerSegment.HIGH_LTV_STABLE: {
            "retry_immediate": (25, 35),
            "retry_tomorrow": (40, 20),
            "backup_method": (45, 16),
            "sms_link": (82, 18),
            "email_only": (45, 55),
            "payment_link": (55, 20),
            "support_call": (45, 5),
        },
        CustomerSegment.MID_LTV_TRANSIENT: {
            "retry_immediate": (18, 35),
            "retry_tomorrow": (30, 25),
            "backup_method": (32, 20),
            "sms_link": (58, 22),
            "email_only": (38, 48),
            "payment_link": (40, 20),
            "support_call": (30, 8),
        },
        CustomerSegment.LOW_LTV_AT_RISK: {
            "retry_immediate": (12, 35),
            "retry_tomorrow": (18, 28),
            "backup_method": (18, 22),
            "sms_link": (30, 25),
            "email_only": (25, 45),
            "payment_link": (22, 22),
            "support_call": (15, 10),
        },
    }

    def __init__(self):
        self.beliefs: Dict[str, Dict[str, BetaBelief]] = {}
        self._init_beliefs()
        self.outcome_history: list = []

    def _init_beliefs(self):
        for segment in CustomerSegment:
            self.beliefs[segment.value] = {}
            seeds = self.SEEDS.get(segment, self.SEEDS[CustomerSegment.MID_LTV_TRANSIENT])
            for strat in STRATEGIES:
                a, b = seeds.get(strat, (20, 30))
                self.beliefs[segment.value][strat] = BetaBelief(alpha=a, beta=b)

    def select_strategy(self, segment: str) -> str:
        """Thompson Sampling: sample from each posterior, return highest."""
        segment_beliefs = self.beliefs.get(segment, self.beliefs["mid_ltv_transient"])
        samples = {s: b.sample() for s, b in segment_beliefs.items()}
        return max(samples, key=samples.get)

    def get_allocations(self, segment: str) -> Dict[str, float]:
        """Current strategy allocation percentages."""
        segment_beliefs = self.beliefs.get(segment, self.beliefs["mid_ltv_transient"])
        total = sum(b.mean for b in segment_beliefs.values())
        return {s: round(b.mean / total, 3) for s, b in segment_beliefs.items()}

    def update(self, segment: str, strategy: str, success: bool):
        """Update belief after outcome observed."""
        belief = self.beliefs.get(segment, {}).get(strategy)
        if belief:
            belief.update(success, weight=1.0)
        self.outcome_history.append({
            "segment": segment,
            "strategy": strategy,
            "success": success,
        })

    def get_stats(self, segment: str) -> dict:
        """Return current strategy performance for segment."""
        segment_beliefs = self.beliefs.get(segment, self.beliefs["mid_ltv_transient"])
        return {
            strat: {
                "success_rate_estimate": round(b.mean, 3),
                "confidence_interval": (
                    round(max(0, b.mean - 1.96 * math.sqrt(b.variance)), 3),
                    round(min(1, b.mean + 1.96 * math.sqrt(b.variance)), 3),
                ),
                "sample_size": round(b.alpha + b.beta),
            }
            for strat, b in segment_beliefs.items()
        }

    def detect_degradation(self, segment: str, strategy: str,
                           lookback: int = 20) -> bool:
        """Check if a strategy is performing worse than its belief."""
        recent = [
            h for h in self.outcome_history[-lookback:]
            if h["segment"] == segment and h["strategy"] == strategy
        ]
        if len(recent) < 5:
            return False
        recent_rate = sum(1 for h in recent if h["success"]) / len(recent)
        belief_rate = self.beliefs[segment][strategy].mean
        return recent_rate < belief_rate - 0.15


# ─── Learning Agent ─────────────────────────────────────

_bandit = StrategyBandit()


def get_bandit() -> StrategyBandit:
    return _bandit


def process_outcome(
    segment: str,
    strategy: str,
    recovered: bool,
    predicted_probability: float,
    chargeback: bool = False,
) -> dict:
    """
    Process a recovery outcome and update learning.
    """
    # Update bandit
    _bandit.update(segment, strategy, recovered)

    # Check prediction accuracy
    actual = 1.0 if recovered else 0.0
    accuracy = "good" if abs(predicted_probability - actual) < 0.15 else "needs_improvement"

    # Check degradation
    degraded = _bandit.detect_degradation(segment, strategy)

    # Get current allocations
    allocations = _bandit.get_allocations(segment)
    stats = _bandit.get_stats(segment)

    result = {
        "segment": segment,
        "strategy": strategy,
        "outcome": "success" if recovered else "failure",
        "predicted": predicted_probability,
        "actual": actual,
        "prediction_accuracy": accuracy,
        "strategy_degraded": degraded,
        "current_allocations": allocations,
        "strategy_stats": stats.get(strategy, {}),
    }

    if degraded:
        result["recommendation"] = (
            f"Strategy {strategy} degrading for {segment} — "
            f"reduce allocation, explore alternatives"
        )

    if chargeback:
        result["chargeback_flagged"] = True
        # Penalize bandit for chargeback
        _bandit.update(segment, strategy, success=False, weight=2.0)

    return result


def select_strategy_adaptive(segment: str) -> str:
    """Use bandit to select optimal strategy for segment."""
    return _bandit.select_strategy(segment)
