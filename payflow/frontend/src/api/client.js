import axios from 'axios';
import { demoCommandCenter, demoMetrics } from './demoData';

const API_URL = import.meta.env.VITE_API_URL || '';
const DEFAULT_KEY = 'rzp_merchant_11111111-1111-1111-1111-111111111111';

const client = axios.create({
  baseURL: API_URL,
  timeout: 5000,
  headers: { 'Content-Type': 'application/json', 'X-Merchant-API-Key': DEFAULT_KEY },
});

async function withFallback(apiCall, demoData) {
  try {
    const result = await apiCall();
    return result;
  } catch {
    console.log('[PayFlow] Backend unavailable — using demo data');
    return demoData;
  }
}

export async function fetchCommandCenter() {
  return withFallback(async () => {
    const { data } = await client.get('/api/dashboard');
    // Map old API response to new PayFlow format, merge with demo defaults
    const live = data.impact_summary || {};
    const summary = data.summary || {};
    const critCount = summary.critical_count || 0;
    const warnCount = summary.warning_count || 0;
    const totalAnomalies = critCount + warnCount;
    return {
      _demo: false,
      merchant: { name: data.merchant_name || 'QuickCommerce India', plan: 'Growth', autopilot_enabled: true },
      kpis: {
        settlements_optimized: live.resolved_this_month || totalAnomalies || 47,
        cost_saved: live.revenue_recovered || 43100,
        disputes_automated: live.chargebacks_prevented || critCount || 12,
        disputes_won: live.chargebacks_prevented || 9,
        time_saved_hours: live.time_saved_hours || 34.5,
        chargebacks_prevented: live.chargebacks_prevented || 8,
        refunds_routed: 23,
        refund_savings: 4600,
      },
      automations: [
        { id: 'live-1', type: 'settlement_routing', name: 'Settlement Route Optimization', description: 'Routes settlements through optimal payment rails', status: 'active', last_run: new Date().toISOString(), executions_today: 12, cost_saved_today: 3200, avg_savings_pct: 18, autopilot: true, metrics: { neft_routes: 8, imps_routes: 3, rtgs_routes: 1, avg_time_hours: 18, success_rate: 0.97 } },
        { id: 'live-2', type: 'dispute_autopilot', name: 'Dispute Evidence Autopilot', description: 'Auto-gathers evidence and submits claims', status: 'active', last_run: new Date().toISOString(), executions_today: 3, cost_saved_today: 15000, avg_savings_pct: 0, autopilot: true, metrics: { evidence_packets: 3, avg_completeness: 0.89, win_rate: 0.78, submitted_today: 2, pending_review: 1 } },
        { id: 'live-3', type: 'refund_routing', name: 'Smart Refund Routing', description: 'Routes refunds through cheapest payment path', status: 'active', last_run: new Date().toISOString(), executions_today: 8, cost_saved_today: 1600, avg_savings_pct: 12, autopilot: true, metrics: { wallet_routes: 5, bank_routes: 3, avg_completion_hours: 24, success_rate: 0.95 } },
      ],
      critical_operations: (data.critical_anomalies || []).slice(0, 4).map((a, i) => ({
        id: a.id || `op-${i}`,
        type: a.type || a.anomaly_type,
        severity: a.severity,
        title: (a.type || a.anomaly_type || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
        description: a.details || a.recommended_action || '',
        amount: 0,
        detected_at: a.detected_at,
        automation_status: i === 0 ? 'in_progress' : i === 1 ? 'automating' : 'monitoring',
        estimated_savings: 0,
        confidence: a.root_cause_confidence || 0.8,
      })),
      processors: [
        { name: 'Razorpay', status: 'connected', last_sync: new Date().toISOString(), transactions_today: 342 },
      ],
      impact: {
        total_saved_this_month: live.revenue_recovered || 43100,
        total_saved_last_month: 38200,
        improvement_pct: 12.8,
        roi_months: 1.2,
        hours_saved_this_month: live.time_saved_hours || 34.5,
        chargebacks_won: live.chargebacks_prevented || 8,
        chargebacks_total: 11,
        win_rate: 0.727,
      },
      next_deadline: data.next_deadline || new Date(Date.now() + 48 * 3600000).toISOString(),
    };
  }, demoCommandCenter);
}

export async function fetchMetrics() {
  return withFallback(async () => {
    const { data } = await client.get('/api/metrics');
    return { _demo: false, ...data };
  }, demoMetrics);
}

export default client;
