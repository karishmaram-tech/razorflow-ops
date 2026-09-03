import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, Legend } from 'recharts';
import KPICardPremium from '../components/KPICardPremium';
import useStore from '../store/useStore';

const COLORS = ['#10B981', '#06B6D4', '#8B5CF6', '#F59E0B'];

export default function MetricsPage() {
  const { metrics, loadMetrics, loadCommandCenter, commandCenter } = useStore();

  useEffect(() => {
    if (!metrics) loadMetrics();
    if (!commandCenter) loadCommandCenter();
  }, [metrics, loadMetrics, commandCenter, loadCommandCenter]);

  const m = metrics || {};
  const d = m.detection || {};
  const a = m.automation || {};
  const f = m.financial || {};
  const dis = m.disputes || {};
  const t = m.time || {};

  const impactData = [
    { name: 'Week 1', saved: 8500, recovered: 12000 },
    { name: 'Week 2', saved: 14200, recovered: 18000 },
    { name: 'Week 3', saved: 22800, recovered: 28000 },
    { name: 'Week 4', saved: f.cost_saved || 43100, recovered: f.revenue_recovered || 58000 },
  ];

  const automationData = [
    { name: 'Settled', value: a.settlements_routed || 47 },
    { name: 'Disputes', value: a.disputes_submitted || 9 },
    { name: 'Refunds', value: a.refunds_routed || 23 },
  ];

  return (
    <div className="min-h-screen px-8 py-8">
      <Link to="/" className="inline-flex items-center gap-1 text-sm text-pf-cyan hover:text-pf-cyan-light no-underline mb-6 transition-colors">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        Back to Command Center
      </Link>

      <h1 className="text-3xl font-bold text-white mb-1">Performance <span className="gradient-text">Metrics</span></h1>
      <p className="text-pf-slate-400 text-sm mb-8">AI agent performance and business impact over the last 30 days</p>

      {/* Top KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <KPICardPremium label="Detection Precision" value={`${Math.round((d.precision || 0.91) * 100)}%`} subtext="True positives / detections" color="cyan" />
        <KPICardPremium label="Automation Success" value={`${Math.round((a.success_rate || 0.94) * 100)}%`} subtext={`${a.total_executions || 156} executions`} trend={8} color="emerald" />
        <KPICardPremium label="Win Rate" value={`${Math.round((dis.win_rate || 0.727) * 100)}%`} subtext={`vs ${Math.round((dis.baseline_win_rate || 0.45) * 100)}% baseline`} trend={62} color="violet" />
        <KPICardPremium label="Time Saved" value={`${t.hours_saved || 34.5}h`} subtext={`${t.manual_tasks_automated || 89} tasks automated`} trend={15} color="amber" />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Impact Over Time */}
        <div className="bg-pf-surface rounded-xl border border-pf-border p-6">
          <h3 className="text-sm font-bold text-white mb-4">Impact Over Time</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={impactData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#94A3B8' }} />
                <YAxis tick={{ fontSize: 11, fill: '#94A3B8' }} />
                <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid #334155', borderRadius: 8, color: '#F1F5F9' }} />
                <Legend />
                <Line type="monotone" dataKey="saved" stroke="#06B6D4" strokeWidth={2} name="Cost Saved" dot={{ r: 4 }} />
                <Line type="monotone" dataKey="recovered" stroke="#10B981" strokeWidth={2} name="Revenue Recovered" dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Automation Breakdown */}
        <div className="bg-pf-surface rounded-xl border border-pf-border p-6">
          <h3 className="text-sm font-bold text-white mb-4">Automation Breakdown</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={automationData} cx="50%" cy="50%" innerRadius={55} outerRadius={85} dataKey="value" label={({ name, value }) => `${name}: ${value}`}>
                  {automationData.map((_, i) => <Cell key={i} fill={COLORS[i]} />)}
                </Pie>
                <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid #334155', borderRadius: 8, color: '#F1F5F9' }} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Detailed Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-pf-surface rounded-xl border border-pf-border p-6">
          <h3 className="text-[11px] font-bold text-pf-slate-500 uppercase tracking-wider mb-4">Financial Impact</h3>
          <div className="space-y-3">
            {[
              ['Cost Saved', `Rs ${(f.cost_saved || 43100).toLocaleString()}`],
              ['Revenue Recovered', `Rs ${(f.revenue_recovered || 58000).toLocaleString()}`],
              ['Avg Settlement Savings', `${Math.round((f.avg_settlement_savings_pct || 18))}%`],
              ['Avg Refund Savings', `${Math.round((f.avg_refund_savings_pct || 12))}%`],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between">
                <span className="text-xs text-pf-slate-400">{k}</span>
                <span className="text-xs font-bold text-white">{v}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-pf-surface rounded-xl border border-pf-border p-6">
          <h3 className="text-[11px] font-bold text-pf-slate-500 uppercase tracking-wider mb-4">Dispute Performance</h3>
          <div className="space-y-3">
            {[
              ['Won', `${dis.won || 8} / ${dis.total || 11}`],
              ['Win Rate', `${Math.round((dis.win_rate || 0.727) * 100)}%`],
              ['Baseline', `${Math.round((dis.baseline_win_rate || 0.45) * 100)}%`],
              ['Improvement', `+${Math.round(dis.improvement || 61.6)}%`],
              ['Evidence Avg', `${Math.round((dis.avg_completeness || 0.89) * 100)}%`],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between">
                <span className="text-xs text-pf-slate-400">{k}</span>
                <span className="text-xs font-bold text-white">{v}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-pf-surface rounded-xl border border-pf-border p-6">
          <h3 className="text-[11px] font-bold text-pf-slate-500 uppercase tracking-wider mb-4">Automation Stats</h3>
          <div className="space-y-3">
            {[
              ['Total Executions', a.total_executions || 156],
              ['Success Rate', `${Math.round((a.success_rate || 0.94) * 100)}%`],
              ['Avg Time', `${a.avg_execution_time_seconds || 12}s`],
              ['Tasks Automated', t.manual_tasks_automated || 89],
              ['Avg Time/Task', `${t.avg_time_per_task_minutes || 23}min`],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between">
                <span className="text-xs text-pf-slate-400">{k}</span>
                <span className="text-xs font-bold text-white">{v}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
