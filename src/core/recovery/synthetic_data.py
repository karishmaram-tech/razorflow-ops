"""
Synthetic data generator for RecoveryFlow.
Produces realistic customer profiles, payment failures, and recovery outcomes.
"""
import random
import uuid
from datetime import datetime, timedelta
from .models import (
    Customer, PaymentFailure, CustomerSegment,
    RecoveryAttempt, RecoveryOutcome, WorkflowState,
)


FIRST_NAMES = [
    "Sarah", "John", "Maria", "James", "Priya", "Chen", "Alex", "Fatima",
    "David", "Emma", "Raj", "Olivia", "Marcus", "Yuki", "Carlos", "Aisha",
    "Daniel", "Sophie", "Liam", "Maya", "Ethan", "Zara", "Noah", "Lena",
]

LAST_NAMES = [
    "Kumar", "Smith", "Chen", "Patel", "Garcia", "Müller", "Tanaka", "Ali",
    "Johnson", "Kim", "Williams", "Das", "Brown", "Singh", "Taylor", "Lee",
    "Wilson", "Sharma", "Anderson", "Thomas", "Jackson", "White", "Harris", "Clark",
]

COMPANIES = [
    "Acme Corp", "TechStart", "CloudBase", "DataFlow", "NexusAI",
    "VelocityInc", "BrightPath", "QuantumLeap", "StellarOps", "BlueShift",
    "NovaTech", "ApexLabs", "CipherSec", "PulseAI", "Vertex.io",
    "HyperScale", "DeepMind Co", "SynthWave", "IronClad", "PrimeStack",
]

FAILURE_REASONS = {
    CustomerSegment.HIGH_LTV_STABLE: [
        ("card_expired", "card_expired", "temporary"),
        ("insufficient_funds", "insufficient_funds", "temporary"),
        ("timeout", "timeout", "temporary"),
    ],
    CustomerSegment.MID_LTV_TRANSIENT: [
        ("card_declined", "do_not_honor", "temporary"),
        ("insufficient_funds", "insufficient_funds", "temporary"),
        ("fraud_blocked", "fraud_check", "risky"),
    ],
    CustomerSegment.LOW_LTV_AT_RISK: [
        ("card_declined", "do_not_honor", "temporary"),
        ("fraud_blocked", "fraud_check", "risky"),
        ("invalid_account", "no_such_account", "permanent"),
    ],
}

# Success rates per strategy (for outcome simulation)
STRATEGY_SUCCESS_RATES = {
    "retry_immediate": 0.38,
    "retry_tomorrow": 0.55,
    "backup_method": 0.62,
    "sms_link": 0.72,
    "email_only": 0.42,
    "payment_link": 0.68,
    "support_call": 0.88,
}

CHARGEBACK_RATES = {
    "retry_immediate": 0.015,
    "retry_tomorrow": 0.010,
    "backup_method": 0.012,
    "sms_link": 0.012,
    "email_only": 0.005,
    "payment_link": 0.008,
    "support_call": 0.003,
}

STRATEGY_COSTS = {
    "retry_immediate": 0.08,
    "retry_tomorrow": 0.05,
    "backup_method": 0.05,
    "sms_link": 0.08,
    "email_only": 0.01,
    "payment_link": 0.05,
    "support_call": 25.00,
}


def generate_customer(segment: CustomerSegment = None) -> Customer:
    if segment is None:
        segment = random.choices(
            list(CustomerSegment),
            weights=[0.20, 0.50, 0.30]
        )[0]

    if segment == CustomerSegment.HIGH_LTV_STABLE:
        tenure = random.randint(12, 60)
        monthly = round(random.uniform(79, 499), 2)
        success_count = int(tenure * random.uniform(0.95, 0.99))
        cb_count = random.choices([0, 1, 2], weights=[0.8, 0.15, 0.05])[0]
        ltv = round(monthly * tenure * random.uniform(0.8, 1.2), 2)
    elif segment == CustomerSegment.MID_LTV_TRANSIENT:
        tenure = random.randint(3, 18)
        monthly = round(random.uniform(19, 149), 2)
        success_count = int(tenure * random.uniform(0.88, 0.96))
        cb_count = random.choices([0, 1, 2, 3], weights=[0.6, 0.25, 0.10, 0.05])[0]
        ltv = round(monthly * tenure * random.uniform(0.6, 1.0), 2)
    else:
        tenure = random.randint(0, 4)
        monthly = round(random.uniform(5, 49), 2)
        success_count = int(tenure * random.uniform(0.80, 0.92))
        cb_count = random.choices([0, 1, 2, 3, 5], weights=[0.5, 0.25, 0.12, 0.08, 0.05])[0]
        ltv = round(monthly * tenure * random.uniform(0.3, 0.7), 2)

    name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

    return Customer(
        id=f"cust_{uuid.uuid4().hex[:8]}",
        name=name,
        email=f"{name.split()[0].lower()}@{random.choice(['gmail', 'yahoo', 'outlook', 'proton']).com}",
        phone=f"+1{random.randint(2000000000, 9999999999)}",
        tenure_months=tenure,
        ltv_estimate=ltv,
        subscription_monthly=monthly,
        payment_success_count=success_count,
        chargeback_count=cb_count,
        complaint_count=random.randint(0, max(1, cb_count)),
        backup_payment_methods=random.choices([0, 1, 2], weights=[0.3, 0.5, 0.2])[0],
        device_consistency=round(random.uniform(0.80, 0.99), 2),
        geography_consistency=round(random.uniform(0.85, 0.99), 2),
        segment=segment,
    )


def generate_failure(customer: Customer) -> PaymentFailure:
    reasons = FAILURE_REASONS.get(
        customer.segment,
        FAILURE_REASONS[CustomerSegment.MID_LTV_TRANSIENT]
    )
    reason_name, code, _ = random.choice(reasons)

    return PaymentFailure(
        id=f"fail_{uuid.uuid4().hex[:8]}",
        subscription_id=f"sub_{uuid.uuid4().hex[:8]}",
        customer_id=customer.id,
        merchant_id="merchant_default",
        amount=customer.subscription_monthly,
        failure_reason=reason_name,
        failure_code=code,
        processor_code=f"PCODE_{random.randint(1000, 9999)}",
        backup_methods_available=customer.backup_payment_methods,
    )


def simulate_outcome(strategy: str, customer: Customer) -> dict:
    """Simulate what happens when recovery is attempted."""
    base_rate = STRATEGY_SUCCESS_RATES.get(strategy, 0.40)

    # Adjust by segment
    seg_adj = {
        CustomerSegment.HIGH_LTV_STABLE: 0.08,
        CustomerSegment.MID_LTV_TRANSIENT: 0.0,
        CustomerSegment.LOW_LTV_AT_RISK: -0.10,
    }
    adjusted_rate = base_rate + seg_adj.get(customer.segment, 0)
    adjusted_rate = max(0.10, min(0.95, adjusted_rate))

    rand = random.random()
    cost = STRATEGY_COSTS.get(strategy, 0.10)

    if rand < adjusted_rate:
        return {
            "recovered": True,
            "chargeback": False,
            "outcome": "success",
            "recovered_amount": customer.subscription_monthly,
            "cost": cost,
        }
    elif rand < adjusted_rate + CHARGEBACK_RATES.get(strategy, 0.01):
        return {
            "recovered": False,
            "chargeback": True,
            "outcome": "chargeback",
            "recovered_amount": 0,
            "cost": cost + 25.0,
        }
    else:
        return {
            "recovered": False,
            "chargeback": False,
            "outcome": "failure",
            "recovered_amount": 0,
            "cost": cost,
        }


def generate_batch(n: int = 100) -> list:
    """Generate a batch of failure scenarios for demo."""
    cases = []
    for _ in range(n):
        segment = random.choices(
            list(CustomerSegment),
            weights=[0.20, 0.50, 0.30]
        )[0]
        customer = generate_customer(segment)
        failure = generate_failure(customer)
        cases.append({"customer": customer, "failure": failure})
    return cases


def generate_demo_scenario(scenario: str = "high_value_recovery") -> dict:
    """
    Generate specific demo scenarios for the 5-minute presentation.
    """
    if scenario == "high_value_recovery":
        customer = Customer(
            id="cust_demo_001",
            name="Sarah Kumar",
            email="sarah@example.com",
            phone="+1234567890",
            tenure_months=36,
            ltv_estimate=3564.0,
            subscription_monthly=99.0,
            payment_success_count=36,
            chargeback_count=0,
            complaint_count=0,
            backup_payment_methods=2,
            device_consistency=0.98,
            geography_consistency=0.99,
            segment=CustomerSegment.HIGH_LTV_STABLE,
        )
        failure = PaymentFailure(
            id="fail_demo_001",
            subscription_id="sub_456xyz",
            customer_id="cust_demo_001",
            merchant_id="merchant_saas",
            amount=99.0,
            failure_reason="card_expired",
            failure_code="card_expired",
            processor_code="PCODE_5100",
            backup_methods_available=2,
        )
        return {"customer": customer, "failure": failure, "scenario": scenario}

    elif scenario == "risk_conflict":
        customer = Customer(
            id="cust_demo_002",
            name="James Wilson",
            email="james@example.com",
            phone="+1987654321",
            tenure_months=18,
            ltv_estimate=2160.0,
            subscription_monthly=120.0,
            payment_success_count=16,
            chargeback_count=3,
            complaint_count=2,
            backup_payment_methods=1,
            device_consistency=0.88,
            geography_consistency=0.92,
            segment=CustomerSegment.MID_LTV_TRANSIENT,
        )
        failure = PaymentFailure(
            id="fail_demo_002",
            subscription_id="sub_789abc",
            customer_id="cust_demo_002",
            merchant_id="merchant_saas",
            amount=120.0,
            failure_reason="insufficient_funds",
            failure_code="insufficient_funds",
            processor_code="PCODE_5100",
            backup_methods_available=1,
        )
        return {"customer": customer, "failure": failure, "scenario": scenario}

    elif scenario == "low_value_skip":
        customer = Customer(
            id="cust_demo_003",
            name="Alex Lee",
            email="alex@example.com",
            phone="+1555555555",
            tenure_months=2,
            ltv_estimate=48.0,
            subscription_monthly=9.99,
            payment_success_count=1,
            chargeback_count=1,
            complaint_count=0,
            backup_payment_methods=0,
            device_consistency=0.72,
            geography_consistency=0.85,
            segment=CustomerSegment.LOW_LTV_AT_RISK,
        )
        failure = PaymentFailure(
            id="fail_demo_003",
            subscription_id="sub_def456",
            customer_id="cust_demo_003",
            merchant_id="merchant_saas",
            amount=9.99,
            failure_reason="fraud_blocked",
            failure_code="fraud_check",
            processor_code="PCODE_4800",
            backup_methods_available=0,
        )
        return {"customer": customer, "failure": failure, "scenario": scenario}

    # Default: random
    return {"customer": generate_customer(), "failure": generate_failure(generate_customer())}
