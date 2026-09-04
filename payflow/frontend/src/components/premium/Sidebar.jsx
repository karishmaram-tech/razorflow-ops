import { NavLink } from 'react-router-dom';
import { motion } from 'framer-motion';

const NAV_ITEMS = [
  { 
    to: '/', label: 'Dashboard', 
    icon: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8"><path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>
  },
  { 
    to: '/analytics', label: 'Analytics',
    icon: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8"><path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>
  },
  { 
    to: '/mobile', label: 'Wallet',
    icon: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8"><path strokeLinecap="round" strokeLinejoin="round" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"/></svg>
  },
  { 
    to: '/softui', label: 'Soft UI',
    icon: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8"><path strokeLinecap="round" strokeLinejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/></svg>
  },
  { 
    to: '/settings', label: 'Settings',
    icon: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8"><path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
  },
];

export default function PremiumSidebar() {
  return (
    <motion.aside
      initial={{ x: -20, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
      className="w-60 flex-shrink-0 flex flex-col h-screen sticky top-0"
      style={{
        background: 'rgba(12, 18, 34, 0.8)',
        backdropFilter: 'blur(24px)',
        borderRight: '1px solid var(--pf-border)',
      }}
    >
      {/* Logo */}
      <div className="px-5 pt-6 pb-4">
        <div className="flex items-center gap-3">
          <div 
            className="w-9 h-9 rounded-xl flex items-center justify-center text-white font-bold text-base"
            style={{ background: 'var(--pf-gradient-primary)' }}
          >
            ⚡
          </div>
          <div>
            <span className="text-[15px] font-bold text-white tracking-tight">PayFlow</span>
          </div>
        </div>
      </div>

      {/* Search */}
      <div className="px-4 mb-4">
        <div className="flex items-center gap-2 px-3 py-2.5 rounded-xl" style={{
          background: 'rgba(255,255,255,0.03)',
          border: '1px solid var(--pf-border)',
        }}>
          <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="var(--pf-text-muted)" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
          </svg>
          <span className="text-xs text-[var(--pf-text-muted)]">Search...</span>
          <span className="ml-auto text-[10px] text-[var(--pf-text-muted)] px-1.5 py-0.5 rounded" style={{ background: 'rgba(255,255,255,0.05)' }}>⌘K</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 space-y-1">
        <p className="px-3 mb-2 text-[10px] font-semibold uppercase tracking-widest text-[var(--pf-text-muted)]">Workspace</p>
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-xl text-[13px] font-medium transition-all duration-200 group ${
                isActive
                  ? 'text-white'
                  : 'text-[var(--pf-text-secondary)] hover:text-white'
              }`
            }
            style={({ isActive }) => isActive ? {
              background: 'rgba(6, 182, 212, 0.08)',
              border: '1px solid rgba(6, 182, 212, 0.15)',
            } : {
              border: '1px solid transparent',
            }}
          >
            <span className="opacity-70 group-hover:opacity-100 transition-opacity">{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* User + Status */}
      <div className="px-3 pb-4 space-y-3">
        <div className="flex items-center gap-2 px-3 py-2 rounded-xl" style={{
          background: 'rgba(16, 185, 129, 0.05)',
          border: '1px solid rgba(16, 185, 129, 0.1)',
        }}>
          <div className="w-2 h-2 rounded-full bg-emerald-500" style={{ animation: 'pf-glow-pulse 2s infinite' }} />
          <span className="text-[11px] text-emerald-400 font-medium">All systems optimal</span>
        </div>
        <div className="flex items-center gap-3 px-3 py-2">
          <div className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold" style={{ background: 'var(--pf-gradient-primary)' }}>K</div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-white truncate">Karishma</p>
            <p className="text-[10px] text-[var(--pf-text-muted)] truncate">karishma@payflow.io</p>
          </div>
        </div>
      </div>
    </motion.aside>
  );
}
