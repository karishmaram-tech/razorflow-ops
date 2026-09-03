import { useState } from 'react';

export default function KPICardPremium({ label, value, subtext, trend, icon, color = 'cyan' }) {
  const [hovered, setHovered] = useState(false);

  const colors = {
    cyan: { bg: 'rgba(6,182,212,0.08)', border: 'rgba(6,182,212,0.2)', text: '#06B6D4' },
    violet: { bg: 'rgba(139,92,246,0.08)', border: 'rgba(139,92,246,0.2)', text: '#8B5CF6' },
    emerald: { bg: 'rgba(16,185,129,0.08)', border: 'rgba(16,185,129,0.2)', text: '#10B981' },
    amber: { bg: 'rgba(245,158,11,0.08)', border: 'rgba(245,158,11,0.2)', text: '#F59E0B' },
  };
  const c = colors[color] || colors.cyan;

  return (
    <div
      className="relative bg-pf-surface rounded-xl p-5 border border-pf-border transition-all duration-300 cursor-default overflow-hidden"
      style={{
        borderColor: hovered ? c.border : undefined,
        boxShadow: hovered ? `0 0 24px ${c.bg}, 0 4px 12px rgba(0,0,0,0.3)` : '0 2px 8px rgba(0,0,0,0.2)',
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {/* Top gradient line on hover */}
      <div
        className="absolute top-0 left-0 right-0 h-[2px] transition-opacity duration-300"
        style={{
          background: `linear-gradient(90deg, ${c.text}, transparent)`,
          opacity: hovered ? 1 : 0,
        }}
      />

      <div className="flex items-start justify-between mb-3">
        <p className="text-[11px] font-bold text-pf-slate-500 uppercase tracking-wider">{label}</p>
        {icon && (
          <div className="p-1.5 rounded-lg" style={{ background: c.bg }}>
            <span style={{ color: c.text }}>{icon}</span>
          </div>
        )}
      </div>

      <p className="text-[28px] font-bold text-white leading-tight animate-count">{value}</p>

      <div className="flex items-center gap-2 mt-1.5">
        <p className="text-xs text-pf-slate-500">{subtext}</p>
        {trend !== undefined && (
          <span className={`text-xs font-bold ${trend >= 0 ? 'text-pf-emerald' : 'text-pf-red'}`}>
            {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}%
          </span>
        )}
      </div>
    </div>
  );
}
