import { NavLink } from 'react-router-dom';

/* ============================================
   ORIGINAL LOGO: Two interlocking waves
   representing payment flow + financial flow
   ============================================ */
function Logo({ size = 32 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" fill="none">
      {/* Background circle with gradient */}
      <defs>
        <linearGradient id="logoGrad" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#2563eb" />
          <stop offset="50%" stopColor="#7c3aed" />
          <stop offset="100%" stopColor="#ec4899" />
        </linearGradient>
      </defs>
      <rect width="40" height="40" rx="12" fill="url(#logoGrad)" />
      {/* Flow wave 1 */}
      <path d="M8 18 C12 14, 16 22, 20 18 C24 14, 28 22, 32 18" stroke="white" strokeWidth="2.5" strokeLinecap="round" fill="none" opacity="0.9" />
      {/* Flow wave 2 */}
      <path d="M8 24 C12 20, 16 28, 20 24 C24 20, 28 28, 32 24" stroke="white" strokeWidth="2.5" strokeLinecap="round" fill="none" opacity="0.6" />
      {/* Arrow tip */}
      <path d="M28 16 L32 18 L28 20" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
    </svg>
  );
}

const NAV = [
  { to: '/', label: 'Dashboard', icon: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8"><path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg> },
  { to: '/analytics', label: 'Analytics', icon: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8"><path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg> },
  { to: '/mobile', label: 'Wallet', icon: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8"><path strokeLinecap="round" strokeLinejoin="round" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"/></svg> },
  { to: '/settings', label: 'Settings', icon: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8"><path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg> },
];

export default function LightSidebar() {
  return (
    <aside
      className="w-60 flex-shrink-0 flex flex-col h-screen sticky top-0"
      style={{
        background: '#ffffff',
        borderRight: '1px solid #e2e8f0',
      }}
    >
      {/* Logo */}
      <div className="px-5 pt-6 pb-5">
        <div className="flex items-center gap-3">
          <Logo size={36} />
          <div>
            <span className="text-[16px] font-bold tracking-tight" style={{ color: 'var(--text-primary)' }}>PayFlow</span>
          </div>
        </div>
      </div>

      {/* Search */}
      <div className="px-4 mb-5">
        <div className="flex items-center gap-2.5 px-3.5 py-2.5 rounded-xl" style={{
          background: '#f1f5f9',
          border: '1px solid #e2e8f0',
        }}>
          <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="#94a3b8" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
          </svg>
          <span className="text-[13px]" style={{ color: '#94a3b8' }}>Search...</span>
          <span className="ml-auto text-[10px] px-1.5 py-0.5 rounded font-medium" style={{ background: '#ffffff', border: '1px solid #e2e8f0', color: '#94a3b8' }}>⌘K</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3">
        <p className="px-3 mb-2 text-[10px] font-semibold uppercase tracking-widest" style={{ color: '#94a3b8' }}>Workspace</p>
        <div className="space-y-0.5">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-[13px] font-medium transition-all duration-200 ${
                  isActive
                    ? 'text-[var(--brand-primary)]'
                    : 'hover:text-[var(--text-primary)]'
                }`
              }
              style={({ isActive }) => ({
                color: isActive ? '#2563eb' : '#475569',
                background: isActive ? '#eff6ff' : 'transparent',
              })}
            >
              <span style={{ opacity: 0.7 }}>{item.icon}</span>
              <span>{item.label}</span>
            </NavLink>
          ))}
        </div>
      </nav>

      {/* Footer */}
      <div className="px-3 pb-4 space-y-3">
        <div className="flex items-center gap-2 px-3 py-2.5 rounded-xl" style={{
          background: '#ecfdf5',
          border: '1px solid rgba(5, 150, 105, 0.12)',
        }}>
          <div className="w-2 h-2 rounded-full" style={{ background: '#059669', animation: 'lf-pulse-soft 2s infinite' }} />
          <span className="text-[11px] font-medium" style={{ color: '#059669' }}>All systems optimal</span>
        </div>
        <div className="flex items-center gap-3 px-3 py-2">
          <div className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold" style={{ background: 'var(--brand-gradient)' }}>K</div>
          <div className="flex-1 min-w-0">
            <p className="text-[12px] font-semibold truncate" style={{ color: '#0f172a' }}>Karishma</p>
            <p className="text-[10px] truncate" style={{ color: '#94a3b8' }}>karishma@payflow.io</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
