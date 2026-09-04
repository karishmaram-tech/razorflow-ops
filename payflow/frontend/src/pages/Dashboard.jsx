import { useState, useCallback, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import useStore from '../store/useStore';

// Animated counter hook
function useCounter(target, duration = 600) {
  const [value, setValue] = useState(target);
  const prevTarget = useRef(target);

  useEffect(() => {
    if (prevTarget.current === target) return;
    const start = prevTarget.current;
    const startTime = Date.now();
    prevTarget.current = target;

    const animate = () => {
      const now = Date.now();
      const progress = Math.min((now - startTime) / duration, 1);
      const current = Math.round(start + (target - start) * progress);
      setValue(current);
      if (progress < 1) requestAnimationFrame(animate);
    };
    requestAnimationFrame(animate);
  }, [target, duration]);

  return value;
}

const ActivityRow = ({ activity, onClick, index }) => (
  <div
    onClick={() => onClick(activity)}
    className="grid gap-4 px-5 py-3.5 border-b border-gray-100 last:border-b-0 hover:bg-gray-50 cursor-pointer transition-all duration-200 hover:translate-x-0.5"
    style={{
      gridTemplateColumns: '1fr 100px 100px 100px',
      animation: `slideInRight 0.4s ease-out ${index * 0.05}s backwards`,
    }}
  >
    <div>
      <p className="text-[13px] font-medium text-gray-900">{activity.title}</p>
      <p className="text-xs text-gray-500 mt-0.5">{activity.description}</p>
    </div>
    <div>
      {activity.status === 'completed' ? (
        <span className="text-xs font-medium px-2 py-1 rounded bg-green-50 text-green-600">Complete</span>
      ) : (
        <span className="text-xs font-medium px-2 py-1 rounded bg-amber-50 text-amber-600 flex items-center gap-1.5" style={{ animation: 'pulse 2s infinite' }}>
          <span className="spinner" /> Running
        </span>
      )}
    </div>
    <div className="text-[13px] font-semibold text-green-600 text-right">
      {activity.cost_saved > 0 ? `+Rs ${activity.cost_saved.toLocaleString('en-IN')}` : '—'}
    </div>
    <div className="text-xs text-gray-400 text-right">{activity.time}</div>
  </div>
);

const KPICard = ({ label, value, suffix, subtext, index }) => {
  const displayValue = useCounter(value);
  return (
    <div
      className="bg-white border border-gray-200 rounded-xl p-5 relative overflow-hidden cursor-pointer transition-all duration-300 hover:border-cyan-400 hover:-translate-y-0.5"
      style={{
        animation: `fadeInUp 0.5s ease-out ${0.1 + index * 0.05}s both`,
        boxShadow: 'none',
      }}
      onMouseEnter={(e) => { e.currentTarget.style.boxShadow = '0 4px 12px rgba(6, 182, 212, 0.08)'; }}
      onMouseLeave={(e) => { e.currentTarget.style.boxShadow = 'none'; }}
    >
      {/* Top gradient line on hover */}
      <div className="absolute top-0 left-0 right-0 h-[3px] bg-gradient-to-r from-cyan-500 to-transparent opacity-0 hover:opacity-100 transition-opacity" />
      <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">{label}</p>
      <p className="text-[32px] font-bold text-cyan-500 mb-1">
        <span className="counter">{displayValue}</span>
        {suffix}
      </p>
      <p className="text-[13px] text-gray-500">{subtext}</p>
    </div>
  );
};

const AUTOMATION_BUTTONS = [
  { type: 'auto_settle', label: 'Test AutoSettle', icon: '⚡' },
  { type: 'dispute_autopilot', label: 'Test Dispute Autopilot', icon: '🛡️' },
  { type: 'smart_refund', label: 'Test Smart Refund', icon: '💰' },
];

const DEMO_AUTOMATIONS = {
  auto_settle: { title: 'Settlement routed to NEFT', description: 'Settlement #1848 — saved ₹625 vs IMPS', cost_saved: 625 },
  dispute_autopilot: { title: 'Dispute evidence submitted', description: 'Dispute #2892 — win probability 94%', cost_saved: 5200 },
  smart_refund: { title: 'Refund routed to original payment', description: 'Refund #4522 — saved 2.3% processing fee', cost_saved: 165 },
};

export default function Dashboard() {
  const navigate = useNavigate();
  const { demoMode } = useStore();
  const [runningType, setRunningType] = useState(null);
  const [toast, setToast] = useState(null);

  const [kpis, setKpis] = useState({
    automations: 487,
    costSaved: 43000,
    timeSaved: 34,
    disputesWon: 9,
  });

  const [activity, setActivity] = useState([
    { id: 1, title: 'Settlement routed to NEFT', description: 'Settlement #1847 — saved ₹600 vs IMPS', cost_saved: 600, status: 'completed', time: '2 min ago' },
    { id: 2, title: 'Dispute evidence submitted', description: 'Dispute #2891 — win probability 92%', cost_saved: 5000, status: 'completed', time: '8 min ago' },
    { id: 3, title: 'Refund routed to original payment', description: 'Refund #4521 — saved 2% processing fee', cost_saved: 150, status: 'completed', time: '15 min ago' },
    { id: 4, title: 'Settlement routed to NEFT', description: 'Settlement #1846 — saved ₹550 vs IMPS', cost_saved: 550, status: 'completed', time: '22 min ago' },
    { id: 5, title: 'Refund routed to original payment', description: 'Refund #4520 — saved 2.1% processing fee', cost_saved: 140, status: 'completed', time: '28 min ago' },
  ]);

  const runAutomation = useCallback(async (type) => {
    if (runningType) return;
    setRunningType(type);

    const demo = DEMO_AUTOMATIONS[type];
    const newId = Date.now();

    // Add running entry
    setActivity(prev => [{ ...demo, id: newId, status: 'running', time: 'Just now' }, ...prev]);

    // Simulate execution
    await new Promise(r => setTimeout(r, 1500));

    // Complete
    setActivity(prev => prev.map(a => a.id === newId ? { ...a, status: 'completed' } : a));

    // Update KPIs
    setKpis(prev => ({
      ...prev,
      automations: prev.automations + 1,
      costSaved: prev.costSaved + demo.cost_saved,
      disputesWon: type === 'dispute_autopilot' ? prev.disputesWon + 1 : prev.disputesWon,
    }));

    // Show toast
    if (demo.cost_saved > 0) {
      setToast(`✓ ${demo.title}! Saved ₹${demo.cost_saved.toLocaleString('en-IN')}`);
    } else {
      setToast(`✓ ${demo.title}`);
    }
    setTimeout(() => setToast(null), 3000);

    setRunningType(null);
  }, [runningType]);

  const handleActivityClick = (item) => {
    navigate(`/automations/${item.id}`, { state: { activity: item } });
  };

  return (
    <div className="min-h-screen bg-[#f8f9fa]">
      {/* Header */}
      <div
        className="bg-white border-b border-gray-200 px-8 py-5 flex items-center justify-between sticky top-0 z-10"
        style={{ animation: 'slideDown 0.4s ease-out' }}
      >
        <div className="text-xl font-semibold text-gray-900">Dashboard</div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-2 bg-green-50 border border-green-200 rounded-md text-xs text-green-600 font-medium">
            <div className="w-2 h-2 rounded-full bg-green-500" style={{ animation: 'pulse 2s infinite' }} />
            All systems operational
          </div>
          {demoMode && (
            <span className="text-xs font-medium text-amber-600 bg-amber-50 px-2.5 py-1.5 rounded-md border border-amber-200">
              Demo Mode
            </span>
          )}
        </div>
      </div>

      <div className="p-8 max-w-[1400px] mx-auto">
        {/* Page Title */}
        <div
          className="mb-8"
          style={{ animation: 'fadeInUp 0.5s ease-out' }}
        >
          <h1 className="text-[28px] font-semibold text-gray-900 mb-1">Command Center</h1>
          <p className="text-sm text-gray-500">Monitor automation activity and performance</p>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-4 gap-4 mb-8">
          <KPICard
            label="Automations this month"
            value={kpis.automations}
            suffix=""
            subtext="Settlements + disputes + refunds"
            index={0}
          />
          <KPICard
            label="Cost saved"
            value={Math.round(kpis.costSaved / 1000)}
            suffix="K"
            subtext="12% increase from last month"
            index={1}
          />
          <KPICard
            label="Time saved"
            value={kpis.timeSaved}
            suffix="h"
            subtext="Manual tasks automated"
            index={2}
          />
          <KPICard
            label="Disputes won"
            value={kpis.disputesWon}
            suffix="/11"
            subtext="85% win rate with automation"
            index={3}
          />
        </div>

        {/* Action Buttons */}
        <div
          className="flex gap-2 mb-8 flex-wrap"
          style={{ animation: 'fadeInUp 0.5s ease-out 0.3s both' }}
        >
          {AUTOMATION_BUTTONS.map((btn) => (
            <button
              key={btn.type}
              onClick={() => runAutomation(btn.type)}
              disabled={runningType !== null}
              className={`flex items-center gap-1.5 px-4 py-2.5 rounded-lg text-[13px] font-semibold transition-all duration-200 border ${
                runningType === btn.type
                  ? 'bg-cyan-500 text-white border-cyan-500 opacity-60 cursor-not-allowed'
                  : runningType !== null
                  ? 'bg-white text-gray-400 border-gray-200 cursor-not-allowed'
                  : 'bg-cyan-500 text-white border-cyan-500 hover:bg-cyan-600 hover:border-cyan-600 hover:-translate-y-px'
              }`}
            >
              {runningType === btn.type ? (
                <>
                  <span className="spinner" /> Running...
                </>
              ) : (
                <>
                  <span>{btn.icon}</span> {btn.label}
                </>
              )}
            </button>
          ))}
        </div>

        {/* Activity Section */}
        <div style={{ animation: 'fadeInUp 0.5s ease-out 0.35s both' }}>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-gray-900">Recent Activity</h2>
            <span className="text-xs text-cyan-500 cursor-pointer font-medium hover:text-cyan-600 transition-colors">View all →</span>
          </div>

          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
            {/* Table Header */}
            <div
              className="grid gap-4 px-5 py-4 bg-gray-50 border-b border-gray-200 text-xs font-semibold text-gray-400 uppercase tracking-wider"
              style={{ gridTemplateColumns: '1fr 100px 100px 100px' }}
            >
              <div>Action</div>
              <div>Status</div>
              <div className="text-right">Saved</div>
              <div className="text-right">Time</div>
            </div>

            {/* Activity Rows */}
            <div>
              {activity.map((item, idx) => (
                <ActivityRow key={item.id} activity={item} onClick={handleActivityClick} index={idx} />
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Toast */}
      {toast && (
        <div
          className="fixed bottom-6 right-6 bg-white border border-gray-200 border-l-4 border-l-green-500 rounded-lg px-4 py-3.5 text-[13px] shadow-lg z-50"
          style={{ animation: 'slideInUp 0.3s ease-out' }}
        >
          {toast}
        </div>
      )}
    </div>
  );
}
