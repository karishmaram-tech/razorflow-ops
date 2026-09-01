# Architecture

## System Overview

The Merchant Payment Operations Intelligence agent is a modular, event-driven system that monitors Razorpay merchant payment operations, detects anomalies, diagnoses root causes, and recommends actions.

## High-Level Architecture

```
                    ┌─────────────────────────────────────┐
                    │           FastAPI Application        │
                    │  ┌─────────┐  ┌──────────────────┐  │
                    │  │  Routes  │  │   Dashboard UI   │  │
                    │  └────┬────┘  └──────────────────┘  │
                    └───────┼──────────────────────────────┘
                            │
                    ┌───────▼───────┐
                    │ Orchestrator  │ ← Scheduled every 15 min
                    │  (6 phases)   │
                    └───────┬───────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │  Settlement  │ │    Refund    │ │   Dispute    │
    │    Agent     │ │    Agent     │ │    Agent     │
    └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
           │                │                │
           ▼                ▼                ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │   Detector   │ │   Detector   │ │   Mapper     │
    │   Classifier │ │   Classifier │ │   Assembler  │
    │   Recommender│ │   Recommender│ │   Predictor  │
    └──────────────┘ └──────────────┘ └──────────────┘
                            │
                    ┌───────▼───────┐
                    │ Explainability│ ← Claude API
                    │    Agent      │
                    └───────────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │PostgreSQL│ │  Redis   │ │  Claude  │
        │   (ORM)  │ │ (cache)  │ │   API    │
        └──────────┘ └──────────┘ └──────────┘
```

## Data Flow

### 1. Ingestion Phase
- Fetch settlements, refunds, disputes created in the last 24 hours
- Filter by merchant ID

### 2. Processing Phase
- **Settlements**: AnomalyDetector → RootCauseClassifier → ActionRecommender
- **Refunds**: AnomalyDetector → RootCauseClassifier → ActionRecommender
- **Disputes**: EvidenceMapper → EvidenceAssembler → WinPredictor

### 3. Aggregation Phase
- Group anomalies by severity (critical, warning, info)
- Extract top recommendations by urgency
- Find next evidence deadline

### 4. Notification Phase
- Filter by merchant's `alert_threshold_severity`
- Route to `notification_channels` (email, SMS, webhook)

### 5. Measurement Phase
- Record anomalies_detected, critical_count, warning_count, notifications_sent
- Write to `evaluation_metrics` table

### 6. Dashboard Phase
- Return `DashboardUpdate` with anomalies, recommendations, impact, summary

## Database Schema

12 tables with UUID primary keys, proper FK relationships, and composite indexes:

| Table | Purpose | Key Relationships |
|-------|---------|-------------------|
| merchants | Merchant profiles | settlements, refunds, disputes, anomalies |
| settlements | Settlement records | → merchant, attempts, anomalies, refunds |
| settlement_attempts | Bank transfer retries | → settlement |
| transactions | Payment transactions | → merchant |
| refunds | Refund records | → merchant, transaction, settlement, dispute |
| disputes | Chargeback records | → merchant, transaction, refund, evidence |
| dispute_evidence | Evidence submissions | → dispute |
| dispute_evidence_templates | Reason code → evidence mapping | — |
| anomalies | Detected issues | → merchant, settlement, refund, dispute |
| diagnoses | Root-cause analysis | → anomaly |
| recommendations | Suggested actions | → anomaly |
| evaluation_metrics | KPI measurements | → merchant |

## Design Decisions

1. **Sync agents, async API**: Agents use sync SQLAlchemy for simplicity; API runs them in thread pool
2. **Unsaved anomalies**: Detectors return unsaved objects; orchestrator decides persistence
3. **Decision trees over ML**: Root-cause classification uses deterministic decision trees with bank code mapping
4. **Fallback explanations**: Claude API failures gracefully degrade to template-based explanations
5. **In-memory rate limiting**: Simple sliding window; production would use Redis

## Scalability Considerations

- **Horizontal**: Multiple API instances behind a load balancer
- **Database**: Connection pooling (pool_size=5, max_overflow=10)
- **Scheduler**: Single-instance only; production would use Celery/APScheduler
- **Caching**: Redis for explanation caching; in-memory fallback for dev
