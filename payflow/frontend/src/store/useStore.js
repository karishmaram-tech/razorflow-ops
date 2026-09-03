import { create } from 'zustand';
import { fetchCommandCenter, fetchMetrics } from '../api/client';
import { demoCommandCenter, demoMetrics } from '../api/demoData';

const useStore = create((set) => ({
  connected: false,
  demoMode: false,
  loading: false,
  commandCenter: null,
  metrics: null,

  loadCommandCenter: async () => {
    set({ loading: true });
    try {
      const data = await fetchCommandCenter();
      if (!data || !data.kpis) throw new Error('Invalid data');
      set({ commandCenter: data, connected: true, demoMode: !!data._demo, loading: false });
    } catch {
      console.error('[PayFlow] Using demo data');
      set({ commandCenter: demoCommandCenter, connected: true, demoMode: true, loading: false });
    }
  },

  loadMetrics: async () => {
    try {
      const data = await fetchMetrics();
      if (!data || typeof data !== 'object') throw new Error('Invalid metrics');
      set({ metrics: data });
    } catch {
      set({ metrics: demoMetrics });
    }
  },

  toggleAutopilot: (automationId) => {
    set((state) => {
      if (!state.commandCenter) return state;
      const automations = state.commandCenter.automations.map((a) =>
        a.id === automationId ? { ...a, autopilot: !a.autopilot } : a
      );
      return { commandCenter: { ...state.commandCenter, automations } };
    });
  },
}));

export default useStore;
