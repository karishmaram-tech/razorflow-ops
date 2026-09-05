import { NavLink } from 'react-router-dom';
import {
  LayoutGrid, Workflow, LineChart, ShieldCheck, ScrollText, Radio,
} from 'lucide-react';
import clsx from 'clsx';
import { useRecoveryState, useRecoveryDispatch } from '../../lib/RecoveryContext';
import Toggle from '../ui/Toggle';

const NAV = [
  { to: '/', label: 'Command center', icon: LayoutGrid, end: true },
  { to: '/strategies', label: 'Strategies', icon: Workflow },
  { to: '/analytics', label: 'Analytics', icon: LineChart },
  { to: '/control-center', label: 'Control center', icon: ShieldCheck },
  { to: '/audit-log', label: 'Audit log', icon: ScrollText },
];

export default function Sidebar() {
  const { isRunning } = useRecoveryState();
  const dispatch = useRecoveryDispatch();

  return (
    <aside className="hidden lg:flex lg:w-60 lg:flex-col lg:border-r lg:border-[var(--color-line)] lg:bg-[var(--color-navy-900)]">
      <div className="flex h-16 items-center gap-2.5 px-5">
        <div className="flex h-7 w-7 items-center justify-center rounded-[var(--radius-xs)] bg-[var(--color-signal)]">
          <Radio size={15} className="text-white" strokeWidth={2.25} />
        </div>
        <div className="leading-tight">
          <p className="text-[14px] font-semibold text-white">RecoveryFlow</p>
          <p className="text-[10.5px] uppercase tracking-wide text-white/45">Revenue recovery</p>
        </div>
      </div>

      <nav className="flex flex-1 flex-col gap-0.5 px-3 py-2">
        {NAV.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) => clsx(
              'flex items-center gap-2.5 rounded-[var(--radius-sm)] px-3 py-2 text-[13.5px] font-medium transition-colors',
              isActive ? 'bg-white/10 text-white' : 'text-white/60 hover:bg-white/5 hover:text-white/90',
            )}
          >
            <Icon size={16} strokeWidth={2} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="mx-3 mb-4 rounded-[var(--radius-md)] border border-white/10 bg-white/5 px-3 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <span className={clsx('h-1.5 w-1.5 rounded-full', isRunning ? 'bg-emerald-400 pulse-dot' : 'bg-white/30')} />
            <span className="text-[12px] font-medium text-white/85">{isRunning ? 'Engine active' : 'Automation paused'}</span>
          </div>
          <Toggle checked={isRunning} onChange={() => dispatch({ type: 'TOGGLE_RUNNING' })} label="Toggle automation" />
        </div>
        <p className="mt-1.5 text-[11px] leading-snug text-white/40">
          Simulated payment data — no production processor is connected.
        </p>
      </div>
    </aside>
  );
}
