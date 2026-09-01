import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || '';
const DEFAULT_MERCHANT_KEY = 'rzp_merchant_11111111-1111-1111-1111-111111111111';

const client = axios.create({
  baseURL: API_URL,
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

export async function fetchDashboard() {
  const { data } = await client.get('/api/dashboard');
  return data;
}

export async function fetchSettlementDetail(id) {
  const { data } = await client.get(`/api/settlement/${id}`);
  return data;
}

export async function fetchRefundDetail(id) {
  const { data } = await client.get(`/api/refund/${id}`);
  return data;
}

export async function fetchDisputeDetail(id) {
  const { data } = await client.get(`/api/dispute/${id}`);
  return data;
}

export async function uploadDisputeEvidence(disputeId, evidenceType, fileUrl) {
  const { data } = await client.post(`/api/dispute/${disputeId}/evidence`, {
    evidence_type: evidenceType,
    file_url: fileUrl,
  });
  return data;
}

export async function fetchMetrics() {
  const { data } = await client.get('/api/metrics');
  return data;
}

export async function healthCheck() {
  const { data } = await client.get('/health');
  return data;
}

export default client;
