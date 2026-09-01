# Setup Guide

## Prerequisites

- Python 3.10+
- Docker & Docker Compose
- PostgreSQL 14+ (or use Docker)
- Redis 7+ (optional, for caching)
- Razorpay test account
- Anthropic API key (Claude)

## Option 1: Docker (recommended)

```bash
# Clone
git clone <repo-url>
cd merchant-payment-ops-agent

# Configure
cp .env.example .env
# Edit .env with your keys

# Start all services
docker compose up -d

# Verify
curl http://localhost:8000/health

# Open dashboard
open http://localhost:8000/dashboard

# API docs
open http://localhost:8000/docs
```

## Option 2: Local Development

```bash
# 1. Start PostgreSQL and Redis
docker compose up postgres redis -d

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure
cp .env.example .env
# Edit .env:
#   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/merchant_ops
#   ANTHROPIC_API_KEY=sk-ant-...
#   RAZORPAY_KEY_ID=rzp_test_...

# 5. Initialize database
python scripts/setup_db.py

# 6. Load test data (optional)
python scripts/load_test_data.py

# 7. Start server
uvicorn src.main:app --reload --port 8000
```

## Database Setup

### Create tables
```bash
python scripts/setup_db.py
```

Options:
- `--skip-drop` — create without dropping
- `--drop-only` — drop all tables
- `--skip-seed` — skip evidence templates

### Load test data
```bash
python scripts/load_test_data.py
```

Generates:
- 100 merchants with varied profiles
- 10-20 settlements per merchant (various statuses)
- 5-10 refunds per merchant
- 3-5 disputes per merchant
- 30 merchants with anomalies + diagnoses
- Edge-case scenarios (delayed, failed, stuck, high dispute rate)

## Configuration Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | — | Async PostgreSQL URL |
| `DATABASE_URL_SYNC` | Yes | — | Sync PostgreSQL URL |
| `ANTHROPIC_API_KEY` | Yes | — | Claude API key |
| `RAZORPAY_KEY_ID` | Yes | — | Razorpay key |
| `RAZORPAY_KEY_SECRET` | Yes | — | Razorpay secret |
| `REDIS_URL` | No | — | Redis connection |
| `ENVIRONMENT` | No | `development` | `development`/`staging`/`production` |
| `LOG_LEVEL` | No | `INFO` | Log level |
| `DEBUG` | No | `false` | Debug mode |
| `API_HOST` | No | `0.0.0.0` | Bind host |
| `API_PORT` | No | `8000` | Bind port |

## Running Tests

```bash
# All tests
pytest -v

# With coverage
pytest -v --cov=src --cov-report=html --cov-report=term

# Specific module
pytest tests/test_settlement_agent.py -v

# Specific test
pytest tests/test_settlement_agent.py::TestDelayedSettlement::test_detect_delayed_settlement_past_deadline -v
```

## Production Deployment

### Environment
```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
```

### Start
```bash
# Docker
docker compose up -d

# Or with gunicorn
gunicorn src.main:app -k uvicorn.workers.UvicornWorker -w 4 --bind 0.0.0.0:8000
```

### Monitoring
- Health: `GET /health`
- Metrics: `GET /api/metrics`
- Dashboard: `GET /dashboard`
