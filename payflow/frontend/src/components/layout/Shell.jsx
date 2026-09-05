import { Outlet } from 'react-router-dom';
import { Radio } from 'lucide-react';
import clsx from 'clsx';
import Sidebar from './Sidebar';
import MobileNav from './MobileNav';
import { useRecoveryState, useRecoveryDispatch } from '../../lib/RecoveryContext';
import Toggle from '../ui/Toggle';

export default function Shell() {
  const { isRunning } = useRecoveryState();
  const dispatch = useRecoveryDispatch();

  return (
    <div className="flex min-h-screen bg-[var(--color-paper)]">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 items-center justify-between border-b border-[var(--color-line)] bg-[var(--color-surface-raised)] px-4 lg:hidden">
          <div className="flex items-center gap-2">
            <div className="flex h-6.5 w-6.5 items-center justify-center rounded-[var(--radius-xs)] bg-[var(--color-navy-800)]">
              <Radio size={13} className="text-white" strokeWidth={2.25} />
            </div>
            <span className="text-[14px] font-semibold">RecoveryFlow</span>
          </div>
          <div className="flex items-center gap-2">
            <span className={clsx('h-1.5 w-1.5 rounded-full', isRunning ? 'bg-[var(--color-success-600)] pulse-dot' : 'bg-[var(--color-ink-faint)]')} />
            <Toggle checked={isRunning} onChange={() => dispatch({ type: 'TOGGLE_RUNNING' })} label="Toggle automation" />
          </div>
        </header>
        <main className="flex-1 overflow-y-auto pb-16 lg:pb-0">
          <Outlet />
        </main>
      </div>
      <MobileNav />
    </div>
  );
}
