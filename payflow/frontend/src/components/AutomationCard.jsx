import { useState } from 'react';

const statusConfig = {
  active: { label: 'Active', color: '#10B981', bg: 'rgba(16,185,129,0.1)' },
  automating: { label: 'Automating', color: '#06B6D4', bg: 'rgba(6,182,212,0.1)' },
  in_progress: { label: 'In Progress', color: '#F59E0B', bg: 'rgba(245,158,11,0.1)' },
  completed: { label: 'Completed', color: '#10B981', bg: 'rgba(16,185,129,0.1)' },
  monitoring: { label: 'Monitoring', color: '#8B5CF6', bg: 'rgba(139,92,246,0.1)' },
};

const typeIcons = {
  settlement_routing: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
    </svg>
  ),
  dispute_autopilot: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
    </svg>
  ),
  refund_routing: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
    </svg>
  ),
  reconciliation: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
    </svg>
  ),
};

export default function AutomationCard({ automation, onToggle }) {
  const [hovered, setHovered] = useState(false);
  const status = statusConfig[automation.status] || statusConfig.active;

  return (
    <div
      className="bg-pf-surface rounded-xl border border-pf-border p-5 transition-all duration-300"
      style={{
        borderColor: hovered ? 'rgba(6,182,212,0.3)' : undefined,
        boxShadow: hovered ? '0 0 20px rgba(6,182,212,0.08)' : undefined,
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg" style={{ background: status.bg, color: status.color }}>
            {typeIcons[automation.type] || typeIcons.settlement_routing}
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">{automation.name}</h3>
            <p className="text-xs text-pf-slate-500 mt-0.5">{automation.description}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded" style={{ background: status.bg, color: status.color }}>
            {status.label}
          </span>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="bg-pf-slate-800/50 rounded-lg p-2.5">
          <p className="text-[10px] text-pf-slate-500 uppercase font-bold">Today</p>
          <p className="text-sm font-bold text-white">{automation.executions_today}</p>
        </div>
        <div className="bg-pf-slate-800/50 rounded-lg p-2.5">
          <p className="text-[10px] text-pf-slate-500 uppercase font-bold">Saved</p>
          <p className="text-sm font-bold text-pf-emerald">Rs {automation.cost_saved_today.toLocaleString()}</p>
        </div>
        <div className="bg-pf-slate-800/50 rounded-lg p-2.5">
          <p className="text-[10px] text-pf-slate-500 uppercase font-bold">Rate</p>
          <p className="text-sm font-bold text-pf-cyan">{automation.metrics?.success_rate ? `${Math.round(automation.metrics.success_rate * 100)}%` : '—'}</p>
        </div>
      </div>

      {/* Toggle */}
      <div className="flex items-center justify-between pt-3 border-t border-pf-border">
        <div className="flex items-center gap-2">
          <div className={`toggle-track ${automation.autopilot ? 'active' : ''}`} onClick={() => onToggle?.(automation.id)}>
            <div className="toggle-thumb" />
          </div>
          <span className="text-xs text-pf-slate-400">
            {automation.autopilot ? 'PayFlow Autopilot' : 'Manual Mode'}
          </span>
        </div>
        <span className="text-[10px] text-pf-slate-600">
          Last: {new Date(automation.last_run).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    </div>
  );
}
