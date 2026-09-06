import { NavLink } from 'react-router-dom';
import { LayoutGrid, Workflow, LineChart, ShieldCheck, FlaskConical } from 'lucide-react';
import clsx from 'clsx';

const NAV = [
  { to: '/app', label: 'Center', icon: LayoutGrid, end: true },
  { to: '/app/strategies', label: 'Strategies', icon: Workflow },
  { to: '/app/analytics', label: 'Analytics', icon: LineChart },
  { to: '/app/control-center', label: 'Control', icon: ShieldCheck },
  { to: '/app/sandbox', label: 'Sandbox', icon: FlaskConical },
];

export default function MobileNav() {
  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 flex border-t border-[var(--color-line)] bg-[var(--color-surface-raised)]/95 backdrop-blur lg:hidden">
      {NAV.map(({ to, label, icon: Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          className={({ isActive }) => clsx(
            'flex flex-1 flex-col items-center gap-1 py-2.5 text-[10.5px] font-medium',
            isActive ? 'text-[var(--color-navy-800)]' : 'text-[var(--color-ink-faint)]',
          )}
        >
          <Icon size={18} strokeWidth={2} />
          {label}
        </NavLink>
      ))}
    </nav>
  );
}
