import { useState } from 'react';
import { motion } from 'framer-motion';

export default function KPICardPremium({ label, value, subtext, trend, icon, color = 'cyan', index = 0 }) {
  const [hovered, setHovered] = useState(false);

  const colors = {
    cyan: { bg: 'rgba(6,182,212,0.08)', border: 'rgba(6,182,212,0.2)', text: '#06B6D4' },
    violet: { bg: 'rgba(139,92,246,0.08)', border: 'rgba(139,92,246,0.2)', text: '#8B5CF6' },
    emerald: { bg: 'rgba(16,185,129,0.08)', border: 'rgba(16,185,129,0.2)', text: '#10B981' },
    amber: { bg: 'rgba(245,158,11,0.08)', border: 'rgba(245,158,11,0.2)', text: '#F59E0B' },
  };
  const c = colors[color] || colors.cyan;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: index * 0.1, ease: 'easeOut' }}
      whileHover={{ y: -2, scale: 1.01 }}
      onHoverStart={() => setHovered(true)}
      onHoverEnd={() => setHovered(false)}
      className="relative bg-pf-surface rounded-xl p-5 border border-pf-border cursor-default overflow-hidden"
      style={{
        borderColor: hovered ? c.border : undefined,
        boxShadow: hovered ? `0 0 24px ${c.bg}, 0 4px 12px rgba(0,0,0,0.3)` : '0 2px 8px rgba(0,0,0,0.2)',
      }}
    >
      {/* Top gradient line on hover */}
      <motion.div
        className="absolute top-0 left-0 right-0 h-[2px]"
        style={{ background: `linear-gradient(90deg, ${c.text}, transparent)` }}
        initial={{ opacity: 0, scaleX: 0 }}
        animate={{ opacity: hovered ? 1 : 0, scaleX: hovered ? 1 : 0 }}
        transition={{ duration: 0.3 }}
      />

      <div className="flex items-start justify-between mb-3">
        <p className="text-[11px] font-bold text-pf-slate-500 uppercase tracking-wider">{label}</p>
        {icon && (
          <motion.div
            className="p-1.5 rounded-lg"
            style={{ background: c.bg }}
            animate={{ rotate: hovered ? 10 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <span style={{ color: c.text }}>{icon}</span>
          </motion.div>
        )}
      </div>

      <motion.p
        className="text-[28px] font-bold text-white leading-tight"
        key={value}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: index * 0.1 + 0.2 }}
      >
        {value}
      </motion.p>

      <div className="flex items-center gap-2 mt-1.5">
        <p className="text-xs text-pf-slate-500">{subtext}</p>
        {trend !== undefined && (
          <motion.span
            className={`text-xs font-bold ${trend >= 0 ? 'text-pf-emerald' : 'text-pf-red'}`}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3, delay: index * 0.1 + 0.4 }}
          >
            {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}%
          </motion.span>
        )}
      </div>
    </motion.div>
  );
}
