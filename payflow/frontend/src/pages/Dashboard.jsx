import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import useStore from '../store/useStore';

const ActivityRow = ({ activity, onClick }) => (
  <div
    onClick={() => onClick(activity)}
    className="flex items-center justify-between px-4 py-3 border-b border-gray-100 hover:bg-gray-50 cursor-pointer"
  >
    <div className="flex items-center gap-3">
      <div className={`w-2 h-2 rounded-full ${
        activity.status === 'completed' ? 'bg-emerald-500' :
        activity.status === 'in_progress' ? 'bg-amber-500' :
        'bg-gray-300'
      }`} />
      <div>
        <p className="text-sm font-medium text-gray-900">{activity.title}</p>
        <p className="text-xs text-gray-500">{activity.description}</p>
      </div>
    </div>
    <div className="text-right">
      {activity.cost_saved > 0 && (
        <p className="text-sm font-semibold text-emerald-600">+Rs {activity.cost_saved.toLocaleString('en-IN')}</p>
      )}
      <p className="text-xs text-gray-400">{activity.time}</p>
    </div>
  </div>
);

const KPICard = ({ label, value, subtext }) => (
  <div className="bg-white border border-gray-200 rounded-lg p-5">
    <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">{label}</p>
    <p className="text-2xl font-bold text-gray-900 mb-1">{value}</p>
    <p className="text-xs text-gray-500">{subtext}</p>
  </div>
);

export default function Dashboard() {
  const navigate = useNavigate();
  const { demoMode } = useStore();

  const [activity] = useState([
    { id: 1, title: 'Settlement routed to NEFT', description: 'Settlement #1847 — saved Rs 600 vs IMPS', cost_saved: 600, status: 'completed', time: '2 min ago', type: 'settlement' },
    { id: 2, title: 'Dispute evidence submitted', description: 'Dispute #2891 — win probability 92%', cost_saved: 0, status: 'completed', time: '8 min ago', type: 'dispute' },
    { id: 3, title: 'Refund routed to original payment', description: 'Refund #4521 — saved 2% processing fee', cost_saved: 150, status: 'completed', time: '15 min ago', type: 'refund' },
    { id: 4, title: 'Settlement route optimized', description: 'Settlement #1846 — RTGS selected for Rs 50K+', cost_saved: 1200, status: 'completed', time: '22 min ago', type: 'settlement' },
    { id: 5, title: 'Dispute evidence gathering', description: 'Dispute #2895 — collecting transaction records', cost_saved: 0, status: 'in_progress', time: 'Now', type: 'dispute' },
    { id: 6, title: 'Settlement batch processed', description: 'Batch #89 — 12 settlements, 11 routed optimally', cost_saved: 3200, status: 'completed', time: '1 hr ago', type: 'settlement' },
    { id: 7, title: 'Refund routing analyzed', description: 'Refund #4522 — wallet route selected', cost_saved: 85, status: 'completed', time: '1 hr ago', type: 'refund' },
    { id: 8, title: 'Chargeback prevention alert', description: 'Order #9823 — flagged for review', cost_saved: 0, status: 'in_progress', time: '2 hr ago', type: 'dispute' },
  ]);

  const handleActivityClick = (item) => {
    navigate(`/automations/${item.id}`, { state: { activity: item } });
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <div className="border-b border-gray-200 px-8 py-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-sm text-gray-500 mt-1">Monitor automation activity and performance</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 rounded-full">
              <div className="w-2 h-2 rounded-full bg-emerald-500" />
              <span className="text-xs font-medium text-gray-600">All systems operational</span>
            </div>
            {demoMode && (
              <span className="text-xs font-medium text-amber-600 bg-amber-50 px-2.5 py-1 rounded-full border border-amber-200">
                Demo Mode
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="px-8 py-6 max-w-6xl">
        {/* KPI Cards */}
        <div className="grid grid-cols-4 gap-4 mb-8">
          <KPICard
            label="Automations This Month"
            value="487"
            subtext="Settlements + disputes + refunds"
          />
          <KPICard
            label="Cost Saved"
            value="Rs 43,100"
            subtext="12% increase from last month"
          />
          <KPICard
            label="Time Saved"
            value="34.5h"
            subtext="Manual tasks automated"
          />
          <KPICard
            label="Disputes Won"
            value="9/11"
            subtext="85% win rate with automation"
          />
        </div>

        {/* Activity Feed */}
        <div className="bg-white border border-gray-200 rounded-lg">
          <div className="px-4 py-3 border-b border-gray-200">
            <h2 className="text-sm font-semibold text-gray-900">Recent Activity</h2>
            <p className="text-xs text-gray-500 mt-0.5">Real-time automation executions</p>
          </div>
          <div>
            {activity.map((item) => (
              <ActivityRow key={item.id} activity={item} onClick={handleActivityClick} />
            ))}
          </div>
        </div>

        {/* Quick Stats */}
        <div className="mt-8 grid grid-cols-3 gap-4">
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Settlements Today</p>
            <p className="text-xl font-bold text-gray-900">42</p>
            <p className="text-xs text-gray-500 mt-1">97% routed optimally</p>
          </div>
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Active Disputes</p>
            <p className="text-xl font-bold text-gray-900">7</p>
            <p className="text-xs text-gray-500 mt-1">3 evidence packages ready</p>
          </div>
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Pending Refunds</p>
            <p className="text-xl font-bold text-gray-900">12</p>
            <p className="text-xs text-gray-500 mt-1">All routed to cheapest path</p>
          </div>
        </div>
      </div>
    </div>
  );
}
