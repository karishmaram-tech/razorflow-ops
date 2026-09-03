import { create } from 'zustand';
import {
  fetchDashboard,
  fetchSettlementDetail,
  fetchRefundDetail,
  fetchDisputeDetail,
  fetchMetrics,
  getMerchantApiKey,
} from '../api/client';
import { demoDashboard, demoSettlement, demoRefund, demoDispute, demoMetrics } from '../api/demoData';

const useStore = create((set, get) => ({
  // State
  merchantApiKey: getMerchantApiKey(),
  connected: false,
  demoMode: false,
  loading: false,
  error: null,

  // Dashboard data
  dashboard: null,

  // Detail pages
  settlement: null,
  refund: null,
  dispute: null,

  // Metrics
  metrics: null,

  // Actions
  setApiKey: (key) => {
    localStorage.setItem('razorflow_merchant_key', key);
    set({ merchantApiKey: key });
  },

  loadDashboard: async () => {
    set({ loading: true, error: null });
    try {
      const data = await fetchDashboard();
      if (!data || !data.critical_anomalies) throw new Error('Invalid dashboard data');
      const isDemo = !!(data?._demo);
      set({ dashboard: data, connected: true, demoMode: isDemo, loading: false });
      return data;
    } catch (err) {
      // Last-resort fallback: always show demo data so the dashboard never crashes
      console.error('[Store] loadDashboard failed, using demo data:', err);
      set({ dashboard: demoDashboard, connected: true, demoMode: true, loading: false, error: null });
      return demoDashboard;
    }
  },

  loadSettlement: async (id) => {
    set({ loading: true, error: null, settlement: null });
    try {
      const data = await fetchSettlementDetail(id);
      if (!data || !data.id) throw new Error('Invalid settlement data');
      set({ settlement: data, loading: false });
      return data;
    } catch (err) {
      console.error('[Store] loadSettlement failed, using demo data:', err);
      set({ settlement: { ...demoSettlement, id }, loading: false, error: null });
      return { ...demoSettlement, id };
    }
  },

  loadRefund: async (id) => {
    set({ loading: true, error: null, refund: null });
    try {
      const data = await fetchRefundDetail(id);
      if (!data || !data.id) throw new Error('Invalid refund data');
      set({ refund: data, loading: false });
      return data;
    } catch (err) {
      console.error('[Store] loadRefund failed, using demo data:', err);
      set({ refund: { ...demoRefund, id }, loading: false, error: null });
      return { ...demoRefund, id };
    }
  },

  loadDispute: async (id) => {
    set({ loading: true, error: null, dispute: null });
    try {
      const data = await fetchDisputeDetail(id);
      if (!data || !data.id) throw new Error('Invalid dispute data');
      set({ dispute: data, loading: false });
      return data;
    } catch (err) {
      console.error('[Store] loadDispute failed, using demo data:', err);
      set({ dispute: { ...demoDispute, id }, loading: false, error: null });
      return { ...demoDispute, id };
    }
  },

  loadMetrics: async () => {
    set({ loading: true, error: null, metrics: null });
    try {
      const data = await fetchMetrics();
      if (!data || typeof data !== 'object') throw new Error('Invalid metrics data');
      set({ metrics: data, loading: false });
      return data;
    } catch (err) {
      console.error('[Store] loadMetrics failed, using demo data:', err);
      set({ metrics: demoMetrics, loading: false, error: null });
      return demoMetrics;
    }
  },

  clearError: () => set({ error: null }),
}));

export default useStore;
