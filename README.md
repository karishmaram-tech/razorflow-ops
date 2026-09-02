# RazorFlow Ops — Merchant Payment Operations Intelligence Agent

AI-powered operations agent for Razorpay merchants. Automates settlement analysis, refund tracking, dispute evidence assembly, and root-cause diagnosis using Claude.

## 🚀 Live Demo

- **Frontend:** https://razorflow-ops-app.vercel.app
- **Backend API:** https://razorflow-ops-backend.railway.app
- **API Docs:** https://razorflow-ops-backend.railway.app/docs

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                 React Dashboard (Vite + Tailwind)             │
│          http://localhost:3000  /  vercel.app                │
└────────────────────────┬─────────────────────────────────────┘
                         │  Axios + Vite Proxy
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (Python 3.12)              │
│  /api/dashboard · /api/settlement · /api/refund · /api/dispute│
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

## 🎯 Quick Start

### Option 1: Docker (recommended for production)

```bash
# Clone the repo
git clone https://github.com/karishmaram-tech/razorflow-ops.git
cd razorflow-ops/merchant-payment-ops-agent

# Configure environment
cp .env.example .env
# Edit .env with your keys

# Start everything
docker compose up -d

# Verify
curl http://localhost:8000/health
```

### Option 2: Local Development

```bash
# Prerequisites: Python 3.12+, PostgreSQL, Node.js 18+

# Start database
docker compose up postgres redis -d

# Backend setup
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python scripts/setup_db.py
python scripts/generate_demo.py --clean
uvicorn src.main:app --reload --port 8080

# Frontend setup (new terminal)
cd razorflow-ops-app
npm install
npm run dev
# Open http://localhost:3000
```

### Option 3: Deploy to Cloud

```bash
# --- Frontend → Vercel ---
cd razorflow-ops-app
npm install -g vercel
vercel

# --- Backend → Railway ---
cd ../
npm install -g @railway/cli
railway login
railway init
railway up

# --- Update frontend .env.production ---
echo "VITE_API_URL=https://your-app.railway.app" > .env.production
vercel --prod
```

## 📊 Dashboard

Open `http://localhost:3000` (React) or `http://localhost:8080/dashboard` (built-in) to see:

- **59 Critical Anomalies** — settlement delays, stuck refunds, deadline risks
- **118 Warnings** — fee mismatches, partial settlements
- **AI-Powered Recommendations** — wait for retry, contact bank, escalate to Razorpay
- **Impact Metrics** — time saved, revenue recovered, chargebacks prevented

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
curl -H "X-Merchant-API-Key: rzp_merchant_11111111-1111-1111-1111-111111111111" \
     http://localhost:8080/api/dashboard
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
  }
}
```

## 🔧 Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | — | Async PostgreSQL (`postgresql+asyncpg://...`) |
| `DATABASE_URL_SYNC` | Yes | — | Sync PostgreSQL (`postgresql://...`) |
| `ANTHROPIC_API_KEY` | No | — | Claude API key (LLM explainability) |
| `RAZORPAY_KEY_ID` | No | — | Razorpay API key |
| `RAZORPAY_KEY_SECRET` | No | — | Razorpay API secret |
| `REDIS_URL` | No | — | Redis for caching |
| `ENVIRONMENT` | No | `development` | `development` / `staging` / `production` |
| `LOG_LEVEL` | No | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |

## 🧪 Testing

```bash
# Full test suite — 218 tests, 70% coverage
pytest -v

# With coverage report
pytest -v --cov=src --cov-report=html

# Specific module
pytest tests/test_settlement_agent.py -v
```

## 📦 Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18, Vite, Tailwind CSS, Axios |
| **Backend** | Python 3.12, FastAPI, SQLAlchemy, Pydantic |
| **Database** | PostgreSQL 16, Redis 7 |
| **AI** | Claude API (Anthropic) for LLM explainability |
| **Deployment** | Vercel (frontend), Railway (backend), Docker |
| **CI/CD** | GitHub Actions |

## 🏗️ Project Structure

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
│       ├── bank_codes.py       # 30+ bank response codes
│       ├── evidence_templates.py # 20+ dispute templates
│       ├── metrics.py          # KPI calculations
│       └── logging_config.py   # Structured logging
├── razorflow-ops-app/          # React frontend
│   ├── src/
│   │   ├── pages/              # Dashboard, Settlement, Refund, Dispute, Metrics
│   │   ├── components/         # Navbar, KPICard, IssuesTable, etc.
│   │   └── api/                # Axios client with Vite proxy
│   └── vite.config.js          # Dev server + API proxy
├── ui/                         # Built-in dashboard (HTML + Chart.js)
├── tests/                      # 218 test cases
├── scripts/
│   ├── setup_db.py             # Database initialization
│   ├── generate_demo.py        # Demo data generation
│   └── load_test_data.py       # Test data generation
├── docs/                       # Architecture, API, Algorithms docs
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

## 📝 License

Proprietary — internal use only.
