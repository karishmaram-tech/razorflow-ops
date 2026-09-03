import { motion } from 'framer-motion';

const statusStyles = {
  automating: { label: 'Automating', color: '#06B6D4', bg: 'rgba(6,182,212,0.1)', pulse: true },
  in_progress: { label: 'In Progress', color: '#F59E0B', bg: 'rgba(245,158,11,0.1)', pulse: true },
  completed: { label: 'Completed', color: '#10B981', bg: 'rgba(16,185,129,0.1)', pulse: false },
  monitoring: { label: 'Monitoring', color: '#8B5CF6', bg: 'rgba(139,92,246,0.1)', pulse: false },
};

const severityIcons = {
  critical: (
    <svg className="w-5 h-5 text-pf-red" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
    </svg>
  ),
  warning: (
    <svg className="w-5 h-5 text-pf-amber" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
};

export default function OperationCard({ operation, index = 0 }) {
  const status = statusStyles[operation.automation_status] || statusStyles.monitoring;

  return (
    <motion.div
      initial={{ opacity: 0, x: -16 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4, delay: index * 0.1, ease: 'easeOut' }}
      whileHover={{ x: 4 }}
      className="bg-pf-surface rounded-xl border border-pf-border p-5 cursor-default"
    >
      <div className="flex items-start gap-3 mb-3">
        <motion.div
          className="p-1.5 rounded-lg bg-pf-red/10 mt-0.5"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: index * 0.1 + 0.2, type: 'spring', stiffness: 400 }}
        >
          {severityIcons[operation.severity] || severityIcons.critical}
        </motion.div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-sm font-semibold text-white truncate">{operation.title}</h3>
            <motion.span
              className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded flex items-center gap-1 shrink-0"
              style={{ background: status.bg, color: status.color }}
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: index * 0.1 + 0.3, type: 'spring' }}
            >
              {status.pulse && <motion.span
                className="w-1.5 h-1.5 rounded-full"
                style={{ background: status.color }}
                animate={{ opacity: [1, 0.3, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
              />}
              {status.label}
            </motion.span>
          </div>
          <p className="text-xs text-pf-slate-400 leading-relaxed">{operation.description}</p>
        </div>
      </div>

      <div className="flex items-center gap-4 mt-4 pt-3 border-t border-pf-border/50">
        {operation.amount > 0 && (
          <div>
            <p className="text-[10px] text-pf-slate-500 uppercase font-bold">Amount</p>
            <p className="text-xs font-semibold text-white">Rs {operation.amount.toLocaleString('en-IN')}</p>
          </div>
        )}
        {operation.estimated_savings > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: index * 0.1 + 0.5 }}
          >
            <p className="text-[10px] text-pf-slate-500 uppercase font-bold">Est. Savings</p>
            <p className="text-xs font-semibold text-pf-emerald">Rs {operation.estimated_savings.toLocaleString('en-IN')}</p>
          </motion.div>
        )}
        <div>
          <p className="text-[10px] text-pf-slate-500 uppercase font-bold">Confidence</p>
          <p className="text-xs font-semibold text-pf-cyan">{Math.round(operation.confidence * 100)}%</p>
        </div>
        <div className="ml-auto">
          <motion.button
            className="px-3 py-1.5 text-xs font-semibold text-pf-cyan bg-pf-cyan/10 hover:bg-pf-cyan/20 border border-pf-cyan/20 rounded-lg"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            View Details →
          </motion.button>
        </div>
      </div>
    </motion.div>
  );
}
