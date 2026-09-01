# Deployment Guide — razorflow-ops

Complete guide for deploying the Merchant Payment Operations Intelligence agent.

---

## Table of Contents

1. [Environment Variables](#environment-variables)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [AWS Deployment](#aws-deployment)
5. [GCP Deployment](#gcp-deployment)
6. [Kubernetes Deployment](#kubernetes-deployment)
7. [Monitoring & Observability](#monitoring--observability)
8. [Production Checklist](#production-checklist)

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | — | PostgreSQL connection string (async) |
| `DATABASE_URL_SYNC` | Yes | — | PostgreSQL connection string (sync, for scripts) |
| `REDIS_URL` | Yes | — | Redis connection string |
| `CLAUDE_API_KEY` | No | — | Anthropic Claude API key (for LLM explanations) |
| `RAZORPAY_API_KEY` | No | — | Razorpay API key (for live data sync) |
| `ENVIRONMENT` | No | `development` | `development`, `staging`, `production` |
| `LOG_LEVEL` | No | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `SECRET_KEY` | Yes (prod) | — | Random secret for signing |
| `CORS_ORIGINS` | No | `*` | Comma-separated allowed origins |

### Example `.env`

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/razorflow_ops
DATABASE_URL_SYNC=postgresql://user:pass@localhost:5432/razorflow_ops
REDIS_URL=redis://localhost:6379/0
CLAUDE_API_KEY=sk-ant-...
ENVIRONMENT=development
LOG_LEVEL=INFO
```

---

## Local Development

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 7+

### Quick Start

```bash
# 1. Clone and setup
git clone <repo-url>
cd merchant-payment-ops-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Start services (Docker)
docker-compose up -d postgres redis

# 3. Setup database
python scripts/setup_db.py

# 4. Load test data
python scripts/load_test_data.py --merchants 100

# 5. Run application
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 6. Open dashboard
open http://localhost:8000
```

### Running Tests

```bash
# Full test suite
pytest tests/ -v --cov=src --cov-report=html

# Specific test file
pytest tests/test_settlement_agent.py -v

# With coverage
pytest tests/ --cov=src --cov-report=term-missing
```

---

## Docker Deployment

### Development

```bash
# Start all services
docker-compose up -d

# Watch logs
docker-compose logs -f api

# Setup DB + load data
docker-compose exec api python scripts/setup_db.py
docker-compose exec api python scripts/load_test_data.py

# Stop
docker-compose down
```

### Production

```bash
# Build image
docker build -t razorflow-ops:latest .

# Run with env file
docker run -d \
  --name razorflow-ops \
  --env-file .env.production \
  -p 8000:8000 \
  --restart unless-stopped \
  razorflow-ops:latest
```

### Health Check

```bash
curl http://localhost:8000/health
# → {"status": "healthy", "timestamp": "...", "version": "1.0.0"}
```

---

## AWS Deployment

### Option 1: ECS Fargate

```bash
# 1. Create ECR repository
aws ecr create-repository --repository-name razorflow-ops

# 2. Build and push image
docker build -t razorflow-ops .
docker tag razorflow-ops:latest <account>.dkr.ecr.<region>.amazonaws.com/razorflow-ops:latest
docker push <account>.dkr.ecr.<region>.amazonaws.com/razorflow-ops:latest

# 3. Create ECS cluster
aws ecs create-cluster --cluster-name razorflow-ops

# 4. Register task definition (see below)

# 5. Create service
aws ecs create-service \
  --cluster razorflow-ops \
  --service-name razorflow-ops-api \
  --task-definition razorflow-ops:1 \
  --desired-count 2 \
  --launch-type FARGATE
```

### Task Definition Template

```json
{
  "family": "razorflow-ops",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "<account>.dkr.ecr.<region>.amazonaws.com/razorflow-ops:latest",
      "portMappings": [{ "containerPort": 8000 }],
      "environment": [
        { "name": "DATABASE_URL", "value": "<rds-connection-string>" },
        { "name": "REDIS_URL", "value": "<elasticache-url>" },
        { "name": "ENVIRONMENT", "value": "production" }
      ],
      "healthCheck": {
        "command": ["CMD", "curl", "-f", "http://localhost:8000/health"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
```

### AWS RDS Setup

```bash
# Create PostgreSQL 16 instance
aws rds create-db-instance \
  --db-instance-identifier razorflow-ops-db \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 16 \
  --master-username razorflow \
  --master-user-password <secure-password> \
  --allocated-storage 20 \
  --storage-type gp3 \
  --backup-retention-period 7 \
  --multi-az
```

### AWS ElastiCache Setup

```bash
# Create Redis cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id razorflow-ops-redis \
  --engine redis \
  --cache-node-type cache.t3.micro \
  --num-cache-nodes 1
```

---

## GCP Deployment

### Cloud Run

```bash
# 1. Build and deploy
gcloud builds submit --tag gcr.io/<project>/razorflow-ops

# 2. Deploy to Cloud Run
gcloud run deploy razorflow-ops \
  --image gcr.io/<project>/razorflow-ops \
  --platform managed \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars "DATABASE_URL=<cloudsql-connection>,REDIS_URL=<memorystore-url>"
```

### Cloud SQL

```bash
# Create PostgreSQL 16 instance
gcloud sql instances create razorflow-ops-db \
  --database-version=POSTGRES_16 \
  --tier=db-custom-2-8192 \
  --region=asia-south1 \
  --storage-size=20GB \
  --storage-auto-increase

# Create database
gcloud sql databases create razorflow_ops --instance=razorflow-ops-db
```

---

## Kubernetes Deployment

### Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: razorflow-ops
  labels:
    app: razorflow-ops
spec:
  replicas: 2
  selector:
    matchLabels:
      app: razorflow-ops
  template:
    metadata:
      labels:
        app: razorflow-ops
    spec:
      containers:
        - name: api
          image: razorflow-ops:latest
          ports:
            - containerPort: 8000
          envFrom:
            - secretRef:
                name: razorflow-secrets
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
          resources:
            requests:
              cpu: "250m"
              memory: "512Mi"
            limits:
              cpu: "500m"
              memory: "1Gi"
---
apiVersion: v1
kind: Service
metadata:
  name: razorflow-ops
spec:
  type: LoadBalancer
  selector:
    app: razorflow-ops
  ports:
    - port: 80
      targetPort: 8000
```

### Apply

```bash
# Create secrets
kubectl create secret generic razorflow-secrets \
  --from-literal=DATABASE_URL="postgresql+asyncpg://..." \
  --from-literal=REDIS_URL="redis://..." \
  --from-literal=CLAUDE_API_KEY="sk-ant-..."

# Deploy
kubectl apply -f k8s/

# Check status
kubectl get pods -l app=razorflow-ops
kubectl logs -l app=razorflow-ops -f
```

---

## Monitoring & Observability

### Health Check

```bash
curl http://localhost:8000/health
```

### Metrics Endpoint

```bash
curl http://localhost:8000/api/metrics \
  -H "X-Merchant-API-Key: rzp_merchant_<id>"
```

### Logs

Structured JSON logs via `structlog`:

```bash
# Local
uvicorn src.main:app --log-level info

# Docker
docker-compose logs -f api --tail 100
```

### Key Metrics to Monitor

| Metric | Alert Threshold | Description |
|--------|----------------|-------------|
| Response time (p99) | > 2s | API latency |
| Error rate | > 1% | 5xx errors |
| Anomalies detected/hour | > 100 | Spike in anomalies |
| Database connections | > 80% pool | Connection pool exhaustion |
| Memory usage | > 80% | Container memory |

### Recommended Tools

- **APM:** Datadog, New Relic, or AWS X-Ray
- **Logs:** CloudWatch Logs, ELK Stack
- **Alerts:** PagerDuty, OpsGenie
- **Dashboards:** Grafana, CloudWatch Dashboard

---

## Production Checklist

### Before Deployment

- [ ] All tests pass (`pytest tests/`)
- [ ] Code formatted (`black src/ tests/`)
- [ ] Linting passes (`flake8 src/ tests/`)
- [ ] Docker image builds (`docker build -t razorflow-ops .`)
- [ ] Health check works (`curl http://localhost:8000/health`)
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Redis accessible
- [ ] CORS configured for production domains
- [ ] Rate limiting enabled
- [ ] Logging configured for production level

### Security

- [ ] API keys rotated from defaults
- [ ] Database password is strong and unique
- [ ] Redis requires authentication
- [ ] HTTPS enabled (via load balancer/proxy)
- [ ] Secrets stored in vault/secrets manager (not in code)
- [ ] CORS_ORIGINS restricted to allowed domains
- [ ] Rate limiting configured

### Performance

- [ ] Connection pooling configured (pool_size=10, max_overflow=20)
- [ ] Redis caching enabled for LLM explanations
- [ ] Database indexes verified
- [ ] Background task scheduling configured
- [ ] Gunicorn workers set appropriately (2 * CPU + 1)

### Post-Deployment

- [ ] Health check returns 200
- [ ] Dashboard loads at root URL
- [ ] Test all 6 API endpoints
- [ ] Verify notifications are sent
- [ ] Check evaluation metrics are recorded
- [ ] Monitor logs for errors
- [ ] Set up alerts for key metrics
