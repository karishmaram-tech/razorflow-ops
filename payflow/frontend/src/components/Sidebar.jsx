import { Link, useLocation } from 'react-router-dom';

const navSections = [
  {
    label: 'WORKSPACE',
    items: [
      { path: '/', icon: 'command', label: 'Command Center' },
      { path: '/automations', icon: 'zap', label: 'Automations' },
      { path: '/processors', icon: 'layers', label: 'Processors' },
    ],
  },
  {
    label: 'ANALYTICS',
    items: [
      { path: '/metrics', icon: 'bar-chart', label: 'Performance' },
      { path: '/savings', icon: 'trending-up', label: 'Savings Report' },
    ],
  },
];

const icons = {
  command: <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" /></svg>,
  zap: <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>,
  layers: <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>,
  'bar-chart': <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>,
  'trending-up': <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>,
};

export default function Sidebar({ demoMode }) {
  const location = useLocation();

  return (
    <aside className="w-[260px] min-h-screen bg-pf-slate-900 border-r border-pf-border flex flex-col sticky top-0">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-pf-border">
        <Link to="/" className="flex items-center gap-3 no-underline">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #06B6D4, #8B5CF6)' }}>
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <div>
            <span className="text-lg font-bold text-white tracking-tight">PayFlow</span>
            <span className="block text-[10px] text-pf-slate-500 uppercase tracking-widest">Command Center</span>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-3">
        {navSections.map((section) => (
          <div key={section.label} className="mb-5">
            <p className="px-3 mb-2 text-[10px] font-bold text-pf-slate-500 uppercase tracking-widest">{section.label}</p>
            <div className="space-y-0.5">
              {section.items.map((item) => {
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium no-underline transition-all duration-200 ${
                      isActive
                        ? 'bg-pf-cyan/10 text-pf-cyan border-l-2 border-pf-cyan'
                        : 'text-pf-slate-400 hover:text-pf-slate-200 hover:bg-pf-slate-800'
                    }`}
                  >
                    <span className={isActive ? 'text-pf-cyan' : 'text-pf-slate-500'}>{icons[item.icon]}</span>
                    {item.label}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Status */}
      <div className="px-4 py-4 border-t border-pf-border">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-2 h-2 rounded-full bg-pf-emerald status-dot" />
          <span className="text-xs font-medium text-pf-slate-400">All systems optimal</span>
        </div>
        {demoMode && (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-pf-amber/10 border border-pf-amber/20 rounded-lg">
            <div className="w-1.5 h-1.5 rounded-full bg-pf-amber" />
            <span className="text-[10px] font-medium text-pf-amber">Demo Mode</span>
          </div>
        )}
      </div>
    </aside>
  );
}
