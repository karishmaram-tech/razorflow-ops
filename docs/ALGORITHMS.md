# Algorithms

## Settlement Anomaly Detection

### Delay Detection
```
expected_arrival = created_at + T+2 working days (skip weekends + Indian holidays)
if current_time > expected_arrival AND status != "success":
    hours_late = (current_time - expected_arrival).hours
    severity = CRITICAL if hours_late > 24 else WARNING if hours_late > 12 else INFO
```

### Partial Settlement
```
expected_net = sum(transactions) - sum(refunds) - fees - taxes
shortfall_pct = (expected_net - actual_net) / expected_net * 100
if shortfall_pct > 5%:  → anomaly
```

### Fee Mismatch
```
expected_fee = amount × 2% (standard Razorpay rate)
deviation_pct = abs(actual_fee - expected_fee) / expected_fee * 100
if deviation_pct > 10%:  → anomaly
```

### Reconciliation Gap
```
expected_gross = sum(transactions) - fees - taxes
variance_pct = abs(expected_gross - settlement_amount) / expected_gross * 100
if variance_pct > 1%:  → anomaly
```

## Root-Cause Classification

### Confidence Scoring
```
base_confidence = 0.85 (known non-retryable) | 0.75 (known retryable) | 0.40 (unknown)
confidence = base_confidence
if same_code_seen_before:  confidence ×= 1.20
if multiple_attempts:       confidence ×= 1.10
if peak_hours (9AM-6PM):   confidence ×= 1.15
confidence = min(confidence, 0.99)
```

### Decision Tree (Settlement)
```
if status == FAILED:
    root_cause = bank_code_mapping[response_code].category
elif status == PENDING AND past_deadline:
    root_cause = bank_code_mapping[response_code].category OR "unknown_delay"
elif status == PARTIAL:
    root_cause = "amount_shortfall_{pct}pct"
```

## Win Probability Prediction (Disputes)

### Base Rate
From `evidence_templates.py` — historical win rates per reason code:
- 4855 (not received): 92%
- 4842 (duplicate): 90%
- 4849 (unauthorized): 45%
- 10.1 (EMV fraud): 30%

### Adjustments
```
probability = base_rate
if completeness >= 90%:  probability += 0.10
elif completeness >= 75%: probability += 0.05
else:                     probability -= 0.15

if avg_relevance > 0.8 AND verified_pct > 0.5:  probability += 0.05
if avg_relevance < 0.5 OR verified_pct < 0.2:   probability -= 0.10

probability = clamp(probability, 0.01, 0.99)
```

## Working-Day Calculations

### Settlement T+2
```
start = next_working_day(created_at.date())
if created_at.hour >= 18:  # 6 PM cutoff
    start = next_working_day(start + 1 day)
arrival = add_working_days(start, 2)
return arrival.combine(23:59:59)
```

### Holiday Calendar
- 40+ Indian bank holidays for 2024-2026
- Fixed: Republic Day, Independence Day, Gandhi Jayanti, Christmas
- Lunar: Diwali, Holi, Eid, Maha Shivaratri
- Weekend + holiday exclusion applied recursively

## Action Recommendation

### Decision Tree (Settlement)
```
root_cause → (action, timeline, probability, urgency)
  insufficient_funds  → (WAIT, 24h, 0.95, LOW)
  bank_processing     → (WAIT, 48h, 0.90, LOW)
  account_closed      → (CONTACT_RAZORPAY, immediate, 0.50, CRITICAL)
  fraud_block         → (CONTACT_RAZORPAY, immediate, 0.40, CRITICAL)

override: if SETTLEMENT_FAILED type → always CONTACT_RAZORPAY + immediate
```

### Probability Blending
```
final_prob = base_prob × (0.7 + 0.3 × diagnosis_confidence) × 0.7
           + historical_success_rate × 0.3
final_prob = clamp(final_prob, 0.10, 0.99)
```

## Evidence Completeness

```
completeness = (found_required / total_required) × 100
  ≥ 90%  → "complete"
  75-89% → "mostly_complete"
  < 75%  → "incomplete"
```

## Business Impact Calculation

```
time_saved = Σ(anomaly_time_estimate)  # 2h settlement, 1.5h refund, 3h dispute
revenue = chargebacks_won × ₹15,000 + delays_prevented × ₹1,000
support = resolved_count × 0.5 tickets × ₹200
cost_savings = time_saved × ₹500/hr + revenue + support
```
