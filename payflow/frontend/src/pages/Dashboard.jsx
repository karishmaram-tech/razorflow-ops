import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import useStore from '../store/useStore';

const DEMO_AUTOMATIONS = {
  auto_settle: {
    title: 'Settlement routed to NEFT',
    description: 'Settlement #1847 — saved Rs 600 vs IMPS',
    cost_saved: 600,
    icon: '⚡',
  },
  dispute_autopilot: {
    title: 'Dispute evidence submitted',
    description: 'Dispute #2891 — win probability 92%',
    cost_saved: 0,
    icon: '🛡️',
  },
  smart_refund: {
    title: 'Refund routed to original payment',
    description: 'Refund #4521 — saved 2% processing fee',
    cost_saved: 150,
    icon: '💰',
  },
};

const AUTOMATION_BUTTONS = [
  { type: 'auto_settle', label: 'AutoSettle', icon: '⚡', gradient: 'from-cyan-500 to-blue-600' },
  { type: 'dispute_autopilot', label: 'Dispute Autopilot', icon: '🛡️', gradient: 'from-violet-500 to-purple-600' },
  { type: 'smart_refund', label: 'Smart Refund', icon: '💰', gradient: 'from-emerald-500 to-green-600' },
];

const KPI_CARDS = [
  {
    label: 'Automations this month',
    getValue: (k) => k.automations.toLocaleString(),
    subtext: 'Settlements + disputes + refunds',
    color: 'from-cyan-500/20 to-cyan-500/5',
    borderColor: 'border-cyan-500/20',
    accentColor: 'text-cyan-400',
  },
  {
    label: 'Cost saved',
    getValue: (k) => `Rs ${(k.costSaved / 1000).toFixed(1)}K`,
    subtext: '12% increase from last month',
    color: 'from-emerald-500/20 to-emerald-500/5',
    borderColor: 'border-emerald-500/20',
    accentColor: 'text-emerald-400',
  },
  {
    label: 'Time saved',
    getValue: (k) => `${k.timeSaved}h`,
    subtext: 'Manual tasks automated',
    color: 'from-violet-500/20 to-violet-500/5',
    borderColor: 'border-violet-500/20',
    accentColor: 'text-violet-400',
  },
  {
    label: 'Disputes won',
    getValue: (k) => `${k.disputesWon}/11`,
    subtext: '85% win rate with automation',
    color: 'from-amber-500/20 to-amber-500/5',
    borderColor: 'border-amber-500/20',
    accentColor: 'text-amber-400',
  },
];

const INITIAL_ACTIVITY = [
  { id: 1, title: 'Settlement routed to NEFT', description: 'Settlement #1847 — saved Rs 600 vs IMPS', cost_saved: 600, status: 'completed', time: '2 min ago', type: 'settlement' },
  { id: 2, title: 'Dispute evidence submitted', description: 'Dispute #2891 — win probability 92%', cost_saved: 0, status: 'completed', time: '8 min ago', type: 'dispute' },
  { id: 3, title: 'Refund routed to original payment', description: 'Refund #4521 — saved 2% processing fee', cost_saved: 150, status: 'completed', time: '15 min ago', type: 'refund' },
  { id: 4, title: 'Settlement route optimized', description: 'Settlement #1846 — RTGS selected for Rs 50K+', cost_saved: 1200, status: 'completed', time: '22 min ago', type: 'settlement' },
  { id: 5, title: 'Dispute evidence gathering', description: 'Dispute #2895 — collecting transaction records', cost_saved: 0, status: 'in_progress', time: 'Now', type: 'dispute' },
];

function KPICard({ config, kpis, index }) {
  return (
    <div
      className={`relative overflow-hidden rounded-2xl border ${config.borderColor} bg-gradient-to-br ${config.color} backdrop-blur-sm p-5 transition-all duration-300 hover:-translate-y-1 hover:shadow-lg hover:shadow-black/20 cursor-pointer group`}
      style={{ animation: `fadeInUp 0.5s ease-out ${0.1 + index * 0.05}s both` }}
    >
      <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
      <div className="relative">
        <p className="text-[11px] font-semibold uppercase tracking-widest text-slate-500 mb-2">{config.label}</p>
        <p className={`text-3xl font-bold ${config.accentColor} mb-1`} style={{ animation: 'fadeInUp 0.6s ease-out' }}>
          {config.getValue(kpis)}
        </p>
        <p className="text-xs text-slate-500">{config.subtext}</p>
      </div>
    </div>
  );
}

function ActivityRow({ activity, onClick, index }) {
  const isSettlement = activity.type === 'settlement';
  const isDispute = activity.type === 'dispute';

  return (
    <div
      onClick={() => onClick(activity)}
      className="flex items-center justify-between px-5 py-3.5 border-b border-[var(--border-subtle)] hover:bg-white/[0.02] cursor-pointer transition-all duration-200 group"
      style={{ animation: `slideInRight 0.4s ease-out ${index * 0.05}s backwards` }}
    >
      <div className="flex items-center gap-3.5">
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm ${
          isSettlement ? 'bg-cyan-500/10 text-cyan-400' :
          isDispute ? 'bg-violet-500/10 text-violet-400' :
          'bg-emerald-500/10 text-emerald-400'
        }`}>
          {DEMO_AUTOMATIONS[activity.type]?.icon || '📋'}
        </div>
        <div>
          <p className="text-sm font-medium text-slate-200 group-hover:text-white transition-colors">{activity.title}</p>
          <p className="text-xs text-slate-500 mt-0.5">{activity.description}</p>
        </div>
      </div>
      <div className="flex items-center gap-4">
        {activity.cost_saved > 0 && (
          <p className="text-sm font-semibold text-emerald-400">+Rs {activity.cost_saved.toLocaleString('en-IN')}</p>
        )}
        <div className={`text-[11px] font-medium px-2.5 py-1 rounded-full ${
          activity.status === 'completed'
            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
            : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
        }`}>
          {activity.status === 'completed' ? 'Complete' : 'In Progress'}
        </div>
        <p className="text-xs text-slate-600 w-16 text-right">{activity.time}</p>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const navigate = useNavigate();
  const { demoMode } = useStore();
  const [runningType, setRunningType] = useState(null);
  const [toast, setToast] = useState(null);
  const [activity, setActivity] = useState(INITIAL_ACTIVITY);
  const [kpis, setKpis] = useState({
    automations: 487,
    costSaved: 43100,
    timeSaved: 34.5,
    disputesWon: 9,
  });

  const runAutomation = useCallback(async (type) => {
    if (runningType) return;
    setRunningType(type);

    const demo = DEMO_AUTOMATIONS[type];
    const demoId = `${type}_${Date.now()}`;

    // Add running entry
    const runningEntry = {
      id: demoId,
      title: `${demo.title}...`,
      description: `Running ${type.replace(/_/g, ' ')}...`,
      cost_saved: 0,
      status: 'in_progress',
      time: 'Now',
      type,
    };
    setActivity(prev => [runningEntry, ...prev]);

    // Simulate execution
    await new Promise(r => setTimeout(r, 1200));

    // Complete
    const completedEntry = {
      ...runningEntry,
      title: demo.title,
      description: demo.description,
      cost_saved: demo.cost_saved,
      status: 'completed',
      time: 'Just now',
    };
    setActivity(prev => prev.map(a => a.id === demoId ? completedEntry : a));

    // Update KPIs
    setKpis(prev => ({
      ...prev,
      automations: prev.automations + 1,
      costSaved: prev.costSaved + demo.cost_saved,
    }));

    // Toast
    setToast(`✓ ${demo.title}${demo.cost_saved > 0 ? ` — saved Rs ${demo.cost_saved}` : ''}`);
    setTimeout(() => setToast(null), 3000);
    setRunningType(null);
  }, [runningType]);

  const handleActivityClick = (item) => {
    navigate(`/automations/${item.id}`, { state: { activity: item } });
  };

  return (
    <div className="min-h-screen bg-[var(--bg-dark)]">
      {/* Toast */}
      {toast && (
        <div
          className="fixed bottom-6 right-6 z-50 bg-[var(--bg-card)] border border-[var(--border-light)] border-l-4 border-l-emerald-500 text-slate-200 px-5 py-3.5 rounded-xl shadow-xl text-sm font-medium"
          style={{ animation: 'fadeInUp 0.3s ease-out' }}
        >
          {toast}
        </div>
      )}

      {/* Header */}
      <div className="border-b border-[var(--border-subtle)] px-8 py-5 bg-[var(--bg-secondary)]/50 backdrop-blur-sm sticky top-0 z-10" style={{ animation: 'slideDown 0.4s ease-out' }}>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white">Dashboard</h1>
            <p className="text-sm text-slate-500 mt-0.5">Monitor automation activity and performance</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/20 rounded-full">
              <div className="w-2 h-2 rounded-full bg-emerald-500" style={{ animation: 'pulse 2s infinite' }} />
              <span className="text-xs font-medium text-emerald-400">All systems operational</span>
            </div>
            {demoMode && (
              <span className="text-xs font-medium text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2.5 py-1 rounded-full">
                Demo Mode
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="px-8 py-6 max-w-7xl">
        {/* Page Title */}
        <div className="mb-8" style={{ animation: 'fadeInUp 0.5s ease-out' }}>
          <h2 className="text-2xl font-bold text-white">Command Center</h2>
          <p className="text-sm text-slate-500 mt-1">Automate settlements, disputes, and refunds in real-time</p>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {KPI_CARDS.map((config, i) => (
            <KPICard key={config.label} config={config} kpis={kpis} index={i} />
          ))}
        </div>

        {/* Automation Buttons */}
        <div className="mb-8" style={{ animation: 'fadeInUp 0.5s ease-out 0.3s both' }}>
          <p className="text-[11px] font-semibold uppercase tracking-widest text-slate-600 mb-3">Test Automations</p>
          <div className="flex gap-3 flex-wrap">
            {AUTOMATION_BUTTONS.map((btn) => (
              <button
                key={btn.type}
                onClick={() => runAutomation(btn.type)}
                disabled={runningType !== null}
                className={`flex items-center gap-2 px-5 py-2.5 text-sm font-semibold text-white rounded-xl transition-all duration-200 ${
                  runningType === btn.type
                    ? 'bg-slate-700 cursor-wait opacity-60'
                    : runningType !== null
                    ? 'bg-slate-800 cursor-not-allowed opacity-40'
                    : `bg-gradient-to-r ${btn.gradient} hover:-translate-y-0.5 hover:shadow-lg hover:shadow-black/20 active:translate-y-0`
                }`}
              >
                <span>{btn.icon}</span>
                <span>{runningType === btn.type ? 'Running...' : btn.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Activity Feed */}
        <div className="rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-card)] overflow-hidden mb-8">
          <div className="px-5 py-4 border-b border-[var(--border-subtle)] flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-white">Recent Activity</h2>
              <p className="text-xs text-slate-500 mt-0.5">Real-time automation executions</p>
            </div>
            <button className="text-xs text-cyan-400 font-medium hover:text-cyan-300 transition-colors cursor-pointer">
              View all →
            </button>
          </div>
          <div>
            {activity.map((item, i) => (
              <ActivityRow key={item.id} activity={item} onClick={handleActivityClick} index={i} />
            ))}
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4" style={{ animation: 'fadeInUp 0.5s ease-out 0.35s both' }}>
          {[
            { label: 'Settlements Today', value: '42', sub: '97% routed optimally', color: 'text-cyan-400' },
            { label: 'Active Disputes', value: '7', sub: '3 evidence packages ready', color: 'text-violet-400' },
            { label: 'Pending Refunds', value: '12', sub: 'All routed to cheapest path', color: 'text-emerald-400' },
          ].map((stat) => (
            <div key={stat.label} className="rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-card)] p-5 hover:border-[var(--border-light)] transition-all duration-300 hover:-translate-y-0.5">
              <p className="text-[11px] font-semibold uppercase tracking-widest text-slate-600 mb-2">{stat.label}</p>
              <p className={`text-2xl font-bold ${stat.color}`}>{stat.value}</p>
              <p className="text-xs text-slate-500 mt-1">{stat.sub}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
