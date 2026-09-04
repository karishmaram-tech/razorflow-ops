import { NavLink } from 'react-router-dom';

const NavItem = ({ to, icon, label }) => (
  <NavLink
    to={to}
    className={({ isActive }) =>
      `flex items-center gap-3 px-3.5 py-3 rounded-lg text-sm cursor-pointer transition-all duration-200 border ${
        isActive
          ? 'bg-blue-50 border-cyan-400 text-cyan-600 font-medium'
          : 'border-transparent text-gray-500 hover:bg-gray-50 hover:border-gray-200 hover:text-gray-900'
      }`
    }
  >
    <span className="text-lg">{icon}</span>
    <span>{label}</span>
  </NavLink>
);

export default function Sidebar() {
  return (
    <div
      className="w-64 bg-white border-r border-gray-200 flex flex-col"
      style={{ animation: 'slideInLeft 0.4s ease-out' }}
    >
      {/* Logo */}
      <div className="px-5 py-6 border-b border-gray-100">
        <div className="flex items-center gap-3">
          <div
            className="w-9 h-9 rounded-lg flex items-center justify-center text-white font-bold text-lg"
            style={{ background: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)' }}
          >
            ⚡
          </div>
          <span className="text-base font-semibold text-cyan-500">PayFlow</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-5 space-y-2">
        <NavItem to="/" icon="📊" label="Dashboard" />
        <NavItem to="/settings" icon="⚙️" label="Settings" />
        <NavItem to="/docs" icon="📚" label="Documentation" />
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-gray-100">
        <div className="flex items-center gap-2 px-3 py-2.5 bg-green-50 border border-green-200 rounded-lg">
          <div className="w-2 h-2 rounded-full bg-green-500" style={{ animation: 'pulse 2s infinite' }} />
          <span className="text-xs text-green-600 font-medium">All systems optimal</span>
        </div>
      </div>
    </div>
  );
}
