# API Reference

Base URL: `http://localhost:8000`

All `/api/*` endpoints require the `X-Merchant-API-Key` header.

## Authentication

```http
X-Merchant-API-Key: rzp_merchant_<merchant-uuid>
```

Format: `rzp_merchant_<uuid>` where UUID matches a merchant in the database.

## Endpoints

### GET /health

Health check. No auth required.

**Response** `200 OK`:
```json
{
  "status": "healthy",
  "service": "merchant-payment-ops-agent",
  "version": "1.0.0",
  "environment": "development"
}
```

---

### GET /api/dashboard

Full merchant dashboard with anomalies, recommendations, impact, and metrics.

**Headers**: `X-Merchant-API-Key: <key>`

**Response** `200 OK`:
```json
{
  "merchant_id": "550e8400-e29b-41d4-a716-446655440000",
  "cycle_at": "2025-06-15T12:00:00",
  "critical_anomalies": [
    {
      "id": "anomaly-uuid",
      "type": "settlement_delayed",
      "severity": "critical",
      "root_cause": "bank_processing_delay",
      "recommended_action": "Contact bank or Razorpay support",
      "detected_at": "2025-06-14T08:00:00"
    }
  ],
  "warning_anomalies": [...],
  "info_anomalies": [...],
  "top_recommendations": [
    {
      "anomaly_id": "...",
      "action": "contact_razorpay",
      "urgency": "critical",
      "timeline": "immediate",
      "success_probability": 0.5,
      "text": "Settlement account may be closed..."
    }
  ],
  "impact": {
    "time_saved_hours": 12.0,
    "revenue_recovered_inr": 45000.0,
    "chargebacks_won": 3,
    "settlement_delays_prevented": 5
  },
  "next_deadline": "2025-06-17T23:59:59",
  "summary": {
    "total_anomalies": 8,
    "critical_count": 2,
    "warning_count": 4,
    "info_count": 2,
    "total_recommendations": 6,
    "unfollowed_recommendations": 4
  }
}
```

---

### GET /api/settlement/{settlement_id}

Settlement details with linked diagnosis and recommendation.

**Response** `200 OK`:
```json
{
  "settlement_id": "settle_A1B2C3D4E5F6",
  "merchant_id": "...",
  "amount": "150000.00",
  "currency": "INR",
  "status": "pending",
  "created_at": "2025-06-10T10:00:00",
  "expected_arrival_at": "2025-06-13T23:59:59",
  "fees": "3000.00",
  "taxes": "540.00",
  "net_amount": "146460.00",
  "diagnosis": {
    "root_cause": "bank_processing_delay",
    "subcategory": "Bank Processing Delay",
    "explanation": "The bank is experiencing processing delays...",
    "confidence": 0.75
  },
  "recommendation": {
    "action": "wait",
    "urgency": "low",
    "timeline": "48_hours",
    "success_probability": 0.9,
    "text": "Your bank is taking a bit longer than usual..."
  }
}
```

**Error** `404 Not Found`:
```json
{"detail": "Settlement settle_xxx not found."}
```

---

### GET /api/refund/{refund_id}

Refund details with linked diagnosis and recommendation.

**Response** `200 OK`:
```json
{
  "refund_id": "rfnd_A1B2C3D4E5F6",
  "merchant_id": "...",
  "transaction_id": "pay_xxx",
  "amount": "2500.00",
  "status": "pending",
  "reason": "customer_requested",
  "created_at": "2025-06-12T14:30:00",
  "diagnosis": {...},
  "recommendation": {...}
}
```

---

### GET /api/dispute/{dispute_id}

Dispute details with evidence analysis and win probability.

**Response** `200 OK`:
```json
{
  "dispute_id": "disp_A1B2C3D4E5F6",
  "merchant_id": "...",
  "transaction_id": "pay_xxx",
  "type": "chargeback",
  "reason_code": "4855",
  "reason_text": "Goods/Services Not Received",
  "amount": "10000.00",
  "current_status": "evidence_pending",
  "evidence_requirements": [
    {"type": "proof_of_shipment", "required": true, "status": "found"},
    {"type": "proof_of_delivery", "required": true, "status": "missing"},
    {"type": "customer_communication", "required": true, "status": "found"}
  ],
  "completeness_score": 66.7,
  "completeness_status": "incomplete",
  "win_probability": 0.72
}
```

---

### POST /api/dispute/{dispute_id}/evidence

Upload evidence for a dispute.

**Request Body**:
```json
{
  "evidence_type": "proof_of_delivery",
  "file_url": "https://s3.example.com/delivery-proof.pdf"
}
```

**Valid evidence types**: `proof_of_shipment`, `proof_of_delivery`, `customer_communication`, `terms_of_service`, `receipt`, `refund_policy`, `other`

**Response** `200 OK`:
```json
{
  "evidence_id": "uuid",
  "dispute_id": "disp_xxx",
  "completeness_updated": true,
  "new_score": 75.0,
  "completeness_status": "mostly_complete"
}
```

**Error** `400 Bad Request`:
```json
{"detail": "Invalid evidence_type 'xyz'. Valid: ['proof_of_shipment', ...]"}
```

---

### GET /api/metrics

Aggregated merchant metrics.

**Response** `200 OK`:
```json
{
  "merchant_id": "...",
  "time_saved_hours": 24.0,
  "chargebacks_won": 5,
  "revenue_recovered": 75000.0,
  "detection_accuracy": 87.5,
  "anomalies_total": 42,
  "anomalies_resolved": 35
}
```

## Error Codes

| Code | Meaning |
|------|---------|
| 400 | Bad request (invalid input) |
| 401 | Invalid or missing API key |
| 404 | Resource not found |
| 429 | Rate limit exceeded (100 req/60s) |
| 500 | Internal server error |
