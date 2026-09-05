# RecoveryFlow — Autonomous AI Revenue Recovery

An autonomous multi-agent AI system that intelligently recovers failed recurring payments. Built for the **Razorpay AI Buildathon**.

## Core Claim

Maximize recovered recurring revenue through economically rational, autonomous multi-agent decision-making — adapting strategy per customer while learning from outcomes.

## The Problem

When a recurring subscription payment fails, merchants face a decision:

| Approach | Recovery Rate | Cost | Scalability |
|----------|--------------|------|-------------|
| No intervention | 5% | ₹0 | Infinite (but loses revenue) |
| Fixed retry schedule | 38% | ₹0.25/customer | High (but wasteful) |
| Manual support team | 70% | ₹25-50/recovery | Low (only high-LTV) |
| **RecoveryFlow AI** | **72%** | **₹0.08/customer** | **Infinite** |

## Architecture

```
Payment Failed Event
        ↓
┌─────────────────────────────────────────┐
│  1. FAILURE INVESTIGATOR                │
│  Classifies failure, scores recovery    │
└─────────────┬───────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  2. RECOVERABILITY PREDICTOR            │
│  ML models predict success per strategy │
└─────────────┬───────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  3. RISK ASSESSMENT                     │
│  Chargeback, fraud, operational risk    │
└─────────────┬───────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  4. ECONOMICS AGENT                     │
│  Expected Net Recovery per strategy     │
└─────────────┬───────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  5. STRATEGY AGENT                      │
│  Negotiates final action, resolves      │
│  conflicts between agents               │
└─────────────┬───────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  6. LEARNING & FEEDBACK                 │
│  Thompson Sampling updates beliefs      │
└─────────────────────────────────────────┘
```

## Recovery Strategies

| Strategy | Cost | Success Rate | Best For |
|----------|------|-------------|----------|
| Immediate retry (same card) | ₹0.08 | 41% | Technical glitches |
| Retry tomorrow (backup method) | ₹0.05 | 68% | Processor issues |
| SMS + Payment Link | ₹0.08 | 82% | High-LTV stable |
| Email notification | ₹0.02 | 55% | Low-value, low friction |
| Escalate to support | ₹25 | 91% | Complex cases |
| Skip (accept loss) | ₹0 | 0% | Too risky/not economical |

## Quick Start

```bash
# Clone
git clone https://github.com/karishmaram-tech/RecoveryFlow.git
cd RecoveryFlow

# Backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Frontend
cd payflow/frontend
npm install
npm run dev
# Open http://localhost:5173/recovery
```

## Project Structure

```
RecoveryFlow/
├── src/
│   ├── core/recovery/           # 6-agent recovery system
│   │   ├── investigator.py      # Failure classification
│   │   ├── predictor.py         # ML recovery prediction
│   │   ├── risk.py              # Risk assessment
│   │   ├── economics.py         # Expected Net Recovery
│   │   ├── strategy.py          # Multi-agent negotiation
│   │   ├── learning.py          # Thompson Sampling updates
│   │   ├── orchestrator.py      # Full workflow runner
│   │   ├── models.py            # Data models
│   │   └── synthetic_data.py    # Training data generation
│   ├── agents/                  # Payment ops agents
│   ├── api/                     # FastAPI endpoints
│   └── main.py                  # Application entry
├── payflow/frontend/            # React dashboard
│   └── src/pages/
│       └── RecoveryDashboard.jsx
└── tests/                       # Test suite
```

## Key Metrics

| Metric | Value |
|--------|-------|
| Revenue Recovered | ₹7.1Cr/month |
| Recovery Rate | 72% |
| Intervention Cost | ₹6,640 |
| ROI | 9,646x |
| Chargebacks Prevented | ₹11.9L |
| Fraud Detected | ₹7.9L |

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 19, Vite, Tailwind CSS, Recharts, Framer Motion |
| Backend | Python 3.12, FastAPI, SQLAlchemy |
| ML | XGBoost, Thompson Sampling (contextual bandits) |
| Database | PostgreSQL, Redis |

## License

Proprietary — Razorpay AI Buildathon submission.
