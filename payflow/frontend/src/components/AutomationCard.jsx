import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

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

export default function AutomationCard({ automation, onToggle, index = 0 }) {
  const [hovered, setHovered] = useState(false);
  const status = statusConfig[automation.status] || statusConfig.active;

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: index * 0.12, ease: 'easeOut' }}
      whileHover={{ y: -3, scale: 1.005 }}
      onHoverStart={() => setHovered(true)}
      onHoverEnd={() => setHovered(false)}
      className="bg-pf-surface rounded-xl border border-pf-border p-5 cursor-default"
      style={{
        borderColor: hovered ? 'rgba(6,182,212,0.3)' : undefined,
        boxShadow: hovered ? '0 0 20px rgba(6,182,212,0.08), 0 8px 24px rgba(0,0,0,0.3)' : '0 2px 8px rgba(0,0,0,0.2)',
        transition: 'border-color 0.3s, box-shadow 0.3s',
      }}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <motion.div
            className="p-2 rounded-lg"
            style={{ background: status.bg, color: status.color }}
            animate={{ rotate: hovered ? 5 : 0 }}
            transition={{ duration: 0.2 }}
          >
            {typeIcons[automation.type] || typeIcons.settlement_routing}
          </motion.div>
          <div>
            <h3 className="text-sm font-semibold text-white">{automation.name}</h3>
            <p className="text-xs text-pf-slate-500 mt-0.5">{automation.description}</p>
          </div>
        </div>
        <motion.span
          className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded shrink-0"
          style={{ background: status.bg, color: status.color }}
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: index * 0.12 + 0.3, type: 'spring', stiffness: 300 }}
        >
          {status.label}
        </motion.span>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        {[
          { label: 'Today', value: automation.executions_today, color: 'text-white' },
          { label: 'Saved', value: `Rs ${automation.cost_saved_today.toLocaleString()}`, color: 'text-pf-emerald' },
          { label: 'Rate', value: automation.metrics?.success_rate ? `${Math.round(automation.metrics.success_rate * 100)}%` : '—', color: 'text-pf-cyan' },
        ].map((metric, i) => (
          <motion.div
            key={metric.label}
            className="bg-pf-slate-800/50 rounded-lg p-2.5"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.12 + 0.2 + i * 0.08, duration: 0.3 }}
          >
            <p className="text-[10px] text-pf-slate-500 uppercase font-bold">{metric.label}</p>
            <p className={`text-sm font-bold ${metric.color}`}>{metric.value}</p>
          </motion.div>
        ))}
      </div>

      {/* Toggle */}
      <div className="flex items-center justify-between pt-3 border-t border-pf-border">
        <div className="flex items-center gap-2">
          <motion.div
            className={`toggle-track ${automation.autopilot ? 'active' : ''}`}
            onClick={() => onToggle?.(automation.id)}
            whileTap={{ scale: 0.95 }}
          >
            <motion.div
              className="toggle-thumb"
              animate={{ x: automation.autopilot ? 20 : 0 }}
              transition={{ type: 'spring', stiffness: 500, damping: 30 }}
            />
          </motion.div>
          <span className="text-xs text-pf-slate-400">
            {automation.autopilot ? 'PayFlow Autopilot' : 'Manual Mode'}
          </span>
        </div>
        <span className="text-[10px] text-pf-slate-600">
          Last: {new Date(automation.last_run).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    </motion.div>
  );
}
