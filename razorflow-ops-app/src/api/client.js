import axios from 'axios';
import {
  demoDashboard,
  demoSettlement,
  demoRefund,
  demoDispute,
  demoMetrics,
} from './demoData';

const API_URL = import.meta.env.VITE_API_URL || '';
const DEFAULT_MERCHANT_KEY = 'rzp_merchant_11111111-1111-1111-1111-111111111111';

const client = axios.create({
  baseURL: API_URL,
  timeout: 5000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export function setMerchantApiKey(key) {
  localStorage.setItem('razorflow_merchant_key', key);
  client.defaults.headers['X-Merchant-API-Key'] = key;
}

export function getMerchantApiKey() {
  return localStorage.getItem('razorflow_merchant_key') || DEFAULT_MERCHANT_KEY;
}

client.defaults.headers['X-Merchant-API-Key'] = getMerchantApiKey();

client.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || 'API request failed';
    console.error(`[API Error] ${error.config?.url}: ${message}`);
    return Promise.reject(error);
  }
);

// Helper: try API, fall back to demo data
async function withFallback(apiCall, demoData) {
  try {
    const result = await apiCall();
    return result;
  } catch {
    console.log('[RazorFlow] Backend unavailable — using demo data');
    return demoData;
  }
}

export async function fetchDashboard() {
  return withFallback(
    async () => {
      const { data } = await client.get('/api/dashboard');
      return data;
    },
    demoDashboard
  );
}

export async function fetchSettlementDetail(id) {
  return withFallback(
    async () => {
      const { data } = await client.get(`/api/settlement/${id}`);
      return data;
    },
    { ...demoSettlement, id }
  );
}

export async function fetchRefundDetail(id) {
  return withFallback(
    async () => {
      const { data } = await client.get(`/api/refund/${id}`);
      return data;
    },
    { ...demoRefund, id }
  );
}

export async function fetchDisputeDetail(id) {
  return withFallback(
    async () => {
      const { data } = await client.get(`/api/dispute/${id}`);
      return data;
    },
    { ...demoDispute, id }
  );
}

export async function uploadDisputeEvidence(disputeId, evidenceType, fileUrl) {
  const { data } = await client.post(`/api/dispute/${disputeId}/evidence`, {
    evidence_type: evidenceType,
    file_url: fileUrl,
  });
  return data;
}

export async function fetchMetrics() {
  return withFallback(
    async () => {
      const { data } = await client.get('/api/metrics');
      return data;
    },
    demoMetrics
  );
}

export async function healthCheck() {
  try {
    const { data } = await client.get('/health');
    return { ...data, demo_mode: false };
  } catch {
    return { status: 'demo_mode', demo_mode: true };
  }
}

export default client;
