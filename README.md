# Merchant Payment Operations Intelligence Agent

AI-powered operations agent for Razorpay merchants. Automates settlement analysis, refund tracking, dispute evidence assembly, and root-cause diagnosis using Claude.

```
┌──────────────────────────────────────────────────────────────┐
│                    FastAPI + React Dashboard                  │
│  /api/dashboard · /api/settlement · /api/refund · /api/dispute │
└────────────────────────┬─────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Settlement  │ │    Refund    │ │   Dispute    │
│   Agent      │ │   Agent      │ │   Agent      │
│ (detect →    │ │ (detect →    │ │ (map →       │
│  classify →  │ │  classify →  │ │  assemble →  │
│  recommend)  │ │  recommend)  │ │  predict)    │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       └────────────────┼────────────────┘
                        ▼
              ┌──────────────────┐
              │   Orchestrator   │
              │ (6-phase cycle)  │
              └────────┬─────────┘
                       ▼
              ┌──────────────────┐
              │   PostgreSQL +   │
              │   Redis Cache    │
              └──────────────────┘
```

## Quick Start

### Docker (recommended)

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env with your Razorpay + Claude keys

# 2. Start everything
docker compose up -d

# 3. Open dashboard
open http://localhost:8000/dashboard

# 4. API docs
open http://localhost:8000/docs
```

### Local Development

```bash
# 1. Prerequisites: Python 3.10+, PostgreSQL, Redis

# 2. Start database
docker compose up postgres redis -d

# 3. Virtual environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 4. Configure
cp .env.example .env
# Edit .env

# 5. Initialize database
python scripts/setup_db.py

# 6. Load test data
python scripts/load_test_data.py

# 7. Run server
uvicorn src.main:app --reload --port 8000

# 8. Run tests
pytest -v --cov=src
```

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/dashboard` | Full merchant dashboard |
| `GET` | `/api/settlement/:id` | Settlement detail + diagnosis |
| `GET` | `/api/refund/:id` | Refund detail + diagnosis |
| `GET` | `/api/dispute/:id` | Dispute + evidence analysis |
| `POST` | `/api/dispute/:id/evidence` | Upload evidence |
| `GET` | `/api/metrics` | Aggregated metrics |

All `/api/*` endpoints require `X-Merchant-API-Key` header.

### Example: Dashboard

```bash
curl -H "X-Merchant-API-Key: rzp_merchant_<your-uuid>" \
     http://localhost:8000/api/dashboard
```

Response:
```json
{
  "merchant_id": "...",
  "critical_anomalies": [...],
  "warning_anomalies": [...],
  "top_recommendations": [...],
  "impact": {
    "time_saved_hours": 12.0,
    "revenue_recovered_inr": 45000.0,
    "chargebacks_won": 3
  },
  "summary": {
    "total_anomalies": 8,
    "critical_count": 2,
    "warning_count": 4,
    "info_count": 2
  }
}
```

### Example: Upload Evidence

```bash
curl -X POST http://localhost:8000/api/dispute/disp_xxx/evidence \
  -H "X-Merchant-API-Key: rzp_merchant_<uuid>" \
  -H "Content-Type: application/json" \
  -d '{"evidence_type": "proof_of_delivery", "file_url": "https://s3.example.com/proof.pdf"}'
```

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | — | Async PostgreSQL connection string |
| `ANTHROPIC_API_KEY` | Yes | — | Claude API key |
| `RAZORPAY_KEY_ID` | Yes | — | Razorpay key ID |
| `RAZORPAY_KEY_SECRET` | Yes | — | Razorpay key secret |
| `REDIS_URL` | No | — | Redis for caching |
| `ENVIRONMENT` | No | `development` | `development` / `staging` / `production` |
| `LOG_LEVEL` | No | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `DEBUG` | No | `false` | Enable SQL logging + docs |

## Testing

```bash
# Full test suite
pytest -v

# With coverage
pytest -v --cov=src --cov-report=html

# Specific module
pytest tests/test_settlement_agent.py -v
```

## Project Structure

```
merchant-payment-ops-agent/
├── src/
│   ├── main.py                 # Application entry point
│   ├── config.py               # Pydantic settings
│   ├── api/
│   │   ├── routes.py           # FastAPI endpoints
│   │   └── schemas.py          # Pydantic request/response models
│   ├── agents/
│   │   ├── settlement_agent.py # Settlement pipeline (detect → classify → recommend)
│   │   ├── refund_agent.py     # Refund pipeline
│   │   ├── dispute_agent.py    # Dispute evidence pipeline
│   │   ├── orchestrator.py     # Central coordinator
│   │   └── explainability.py   # LLM-powered explanations
│   ├── data/
│   │   ├── models.py           # 12 SQLAlchemy ORM models
│   │   ├── database.py         # Async engine + sessions
│   │   └── repository.py       # CRUD operations
│   └── utils/
│       ├── time_utils.py       # Working-day calculations
│       ├── bank_codes.py       # 25+ bank response codes
│       ├── evidence_templates.py # 20+ dispute templates
│       ├── metrics.py          # KPI calculations
│       └── logging.py          # Structured logging setup
├── ui/
│   ├── dashboard.html          # React dashboard layout
│   └── dashboard.js            # Dashboard logic + Chart.js
├── tests/                      # 162+ test cases
├── scripts/
│   ├── setup_db.py             # Database initialization
│   ├── load_test_data.py       # Test data generation
│   └── run_evaluation.py       # Before/after evaluation
├── docs/                       # Detailed documentation
├── .github/workflows/          # CI/CD pipeline
├── docker-compose.yml          # PostgreSQL + Redis + API
├── Dockerfile                  # Production container
├── requirements.txt            # Pinned dependencies
└── .env.example                # Configuration template
```

## Agent Pipelines

### Settlement Pipeline
```
Settlement → AnomalyDetector → RootCauseClassifier → ActionRecommender
             (6 checks)        (bank code mapping)   (decision tree)
```

### Refund Pipeline
```
Refund → AnomalyDetector → RootCauseClassifier → ActionRecommender
         (5 checks)        (bank/reversal codes)  (decision tree)
```

### Dispute Pipeline
```
Dispute → EvidenceMapper → EvidenceAssembler → WinPredictor
          (20+ templates)  (DB + placeholder)   (base rate + adjustments)
```

## License

Proprietary — internal use only.
