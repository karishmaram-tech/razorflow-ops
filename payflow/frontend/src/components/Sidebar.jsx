import { NavLink } from 'react-router-dom';

const NavItem = ({ to, icon, label }) => (
  <NavLink
    to={to}
    className={({ isActive }) =>
      `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
        isActive
          ? 'bg-gradient-to-r from-cyan-500/10 to-cyan-500/5 text-cyan-400 border border-cyan-500/20'
          : 'text-slate-400 hover:bg-white/5 hover:text-slate-200 border border-transparent'
      }`
    }
  >
    <span className="text-base">{icon}</span>
    <span>{label}</span>
  </NavLink>
);

export default function Sidebar() {
  return (
    <div
      className="w-64 bg-[var(--bg-secondary)] border-r border-[var(--border-subtle)] flex flex-col"
      style={{ animation: 'slideInLeft 0.4s ease-out' }}
    >
      {/* Logo */}
      <div className="px-5 py-5 border-b border-[var(--border-subtle)]">
        <div className="flex items-center gap-3">
          <div
            className="w-9 h-9 rounded-xl flex items-center justify-center text-white font-bold text-lg"
            style={{ background: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)' }}
          >
            ⚡
          </div>
          <div>
            <span className="text-sm font-bold text-white tracking-tight">PayFlow</span>
            <div className="text-[10px] text-slate-500 font-medium">Command Center</div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        <div className="px-3 mb-2 text-[10px] font-semibold uppercase tracking-widest text-slate-600">
          Workspace
        </div>
        <NavItem
          to="/"
          icon={
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
          }
          label="Dashboard"
        />
        <NavItem
          to="/settings"
          icon={
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          }
          label="Settings"
        />

        <div className="px-3 mt-6 mb-2 text-[10px] font-semibold uppercase tracking-widest text-slate-600">
          Tools
        </div>
        <NavItem
          to="/docs"
          icon={
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          }
          label="Documentation"
        />
      </nav>

      {/* Footer */}
      <div className="px-3 py-3 border-t border-[var(--border-subtle)]">
        <div className="flex items-center gap-2.5 px-3 py-2.5 bg-emerald-500/5 border border-emerald-500/10 rounded-xl">
          <div className="w-2 h-2 rounded-full bg-emerald-500" style={{ animation: 'pulse 2s infinite' }} />
          <span className="text-xs text-emerald-400 font-medium">All systems optimal</span>
        </div>
      </div>
    </div>
  );
}
