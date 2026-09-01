# Demo Guide

## Quick Demo (5 minutes)

### Step 1: Start the system

```bash
# Clone and start
git clone <repo-url>
cd merchant-payment-ops-agent
cp .env.example .env
docker compose up -d

# Verify
curl http://localhost:8000/health
# → {"status":"healthy","service":"merchant-payment-ops-agent",...}
```

### Step 2: Open the dashboard

```
http://localhost:8000/dashboard
```

You'll see:
- KPI cards: Critical anomalies, action items, chargebacks won, time saved
- Anomaly table: Filterable by severity
- Performance metrics: Detection accuracy, win rate gauges
- Impact timeline: Cumulative time saved and revenue charts

### Step 3: Query a settlement

```bash
# Get a settlement ID from test data
curl -H "X-Merchant-API-Key: rzp_merchant_<uuid>" \
     http://localhost:8000/api/settlement/settle_A1B2C3D4E5F6

# Response includes settlement details + diagnosis + recommendation
```

### Step 4: Upload dispute evidence

```bash
curl -X POST http://localhost:8000/api/disp_xxx/evidence \
  -H "X-Merchant-API-Key: rzp_merchant_<uuid>" \
  -H "Content-Type: application/json" \
  -d '{"evidence_type": "proof_of_delivery", "file_url": "https://example.com/proof.pdf"}'

# Response: completeness score updated
```

### Step 5: Check metrics

```bash
curl -H "X-Merchant-API-Key: rzp_merchant_<uuid>" \
     http://localhost:8000/api/metrics

# Response: time_saved_hours, chargebacks_won, detection_accuracy
```

## Demo Scenarios

### Scenario A: Delayed Settlement

**Setup**: Settlement created 5 days ago, status=PENDING

**What happens**:
1. Detector flags `settlement_delayed` (CRITICAL severity)
2. Classifier maps bank code to root cause
3. Recommender suggests `contact_razorpay` (immediate)
4. Dashboard shows red critical card
5. Notification sent to merchant's email

**Dashboard view**:
- KPI: "1" in red critical card
- Anomaly table: Settlement Delayed | 5 days ago | Bank Processing Delay | Contact Razorpay | Open

### Scenario B: Stuck Refund

**Setup**: Refund in PROCESSING for 5 days

**What happens**:
1. Detector flags `refund_stuck` (CRITICAL)
2. Classifier identifies bank processing delay
3. Recommender suggests `contact_customer_bank` (immediate, >4 days)
4. Explainability agent generates: "The ₹2500 refund is taking longer than expected..."

### Scenario C: Incomplete Dispute Evidence

**Setup**: Dispute with reason code 4855 (goods not received), 0% evidence

**What happens**:
1. Mapper identifies 3 required evidence types
2. Assembler finds 0/3 → completeness 0%
3. Predictor calculates win probability: ~57% (base 92% - 15% penalty)
4. Anomaly created: `dispute_evidence_incomplete` (CRITICAL)
5. Dashboard shows evidence gap

**After uploading proof of delivery**:
```bash
curl -X POST http://localhost:8000/api/disp_xxx/evidence \
  -H "X-Merchant-API-Key: rzp_merchant_<uuid>" \
  -H "Content-Type: application/json" \
  -d '{"evidence_type": "proof_of_delivery", "file_url": "..."}'
```
- Completeness jumps to 67%
- Win probability increases to ~82%

## API Explorer

Open `http://localhost:8000/docs` for the interactive Swagger UI where you can:

1. Authenticate with your API key
2. Test all endpoints interactively
3. View request/response schemas
4. Download OpenAPI spec

## Architecture Walkthrough

```
Request → FastAPI Router → Auth Check → Agent Pipeline → Response
                                      ↓
                               Orchestrator → Detect → Classify → Recommend
                                      ↓
                               Database (PostgreSQL)
                                      ↓
                               Metrics Recording
```

## Key Files to Show

| File | What to highlight |
|------|-------------------|
| `src/agents/settlement_agent.py` | 6 detection methods, confidence scoring |
| `src/agents/orchestrator.py` | 6-phase pipeline coordination |
| `src/utils/time_utils.py` | Indian holiday calendar, working-day math |
| `src/utils/bank_codes.py` | 25+ bank response code mappings |
| `ui/dashboard.js` | Chart.js gauges, real-time polling |
