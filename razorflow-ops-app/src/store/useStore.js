import { create } from 'zustand';
import {
  fetchDashboard,
  fetchSettlementDetail,
  fetchRefundDetail,
  fetchDisputeDetail,
  fetchMetrics,
  getMerchantApiKey,
} from '../api/client';

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
      const isDemo = !!(data?._demo);
      set({ dashboard: data, connected: true, demoMode: isDemo, loading: false });
      return data;
    } catch (err) {
      set({ connected: false, loading: false, error: err.message });
      return null;
    }
  },

  loadSettlement: async (id) => {
    set({ loading: true, error: null, settlement: null });
    try {
      const data = await fetchSettlementDetail(id);
      set({ settlement: data, loading: false });
      return data;
    } catch (err) {
      set({ loading: false, error: err.message });
      return null;
    }
  },

  loadRefund: async (id) => {
    set({ loading: true, error: null, refund: null });
    try {
      const data = await fetchRefundDetail(id);
      set({ refund: data, loading: false });
      return data;
    } catch (err) {
      set({ loading: false, error: err.message });
      return null;
    }
  },

  loadDispute: async (id) => {
    set({ loading: true, error: null, dispute: null });
    try {
      const data = await fetchDisputeDetail(id);
      set({ dispute: data, loading: false });
      return data;
    } catch (err) {
      set({ loading: false, error: err.message });
      return null;
    }
  },

  loadMetrics: async () => {
    set({ loading: true, error: null, metrics: null });
    try {
      const data = await fetchMetrics();
      set({ metrics: data, loading: false });
      return data;
    } catch (err) {
      set({ loading: false, error: err.message });
      return null;
    }
  },

  clearError: () => set({ error: null }),
}));

export default useStore;
