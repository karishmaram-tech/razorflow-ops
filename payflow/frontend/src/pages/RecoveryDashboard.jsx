import { Link } from 'react-router-dom';
import { FlaskConical, ArrowRight } from 'lucide-react';
import Badge from '../components/ui/Badge';
import MetricsRow from '../components/dashboard/MetricsRow';
import AttentionTable from '../components/dashboard/AttentionTable';
import LiveActivityFeed from '../components/dashboard/LiveActivityFeed';
import { useRecoveryState, useMetrics } from '../lib/RecoveryContext';

export default function RecoveryDashboard() {
  const { payments, activity, isRunning } = useRecoveryState();
  const metrics = useMetrics();

  return (
    <div className="mx-auto flex max-w-[1400px] flex-col gap-5 px-4 py-6 sm:px-6 lg:px-8">
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2.5">
          <h1 className="text-[20px] font-semibold text-[var(--color-ink)]">Recovery command center</h1>
          <Badge variant="neutral">Simulated data</Badge>
        </div>
        <p className="text-[13.5px] text-[var(--color-ink-faint)]">
          Every failed payment below is investigated, scored, and worked automatically within the limits you've set.
        </p>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 rounded-[var(--radius-lg)] border border-[var(--color-line)] bg-[var(--color-surface-raised)] px-4 py-3">
        <div className="flex items-center gap-2.5">
          <span className={`h-2 w-2 rounded-full ${isRunning ? 'bg-[var(--color-success-600)] pulse-dot' : 'bg-[var(--color-ink-faint)]'}`} />
          <span className="text-[13px] font-medium text-[var(--color-ink)]">
            {isRunning ? 'Automation active' : 'Automation paused'}
          </span>
          <span className="text-[13px] text-[var(--color-ink-faint)]">
            · {metrics.activeCount} payment{metrics.activeCount === 1 ? '' : 's'} currently being evaluated
          </span>
        </div>
        <Link
          to="/app/sandbox"
          className="flex items-center gap-1.5 text-[12.5px] font-medium text-[var(--color-navy-700)] hover:text-[var(--color-navy-800)]"
        >
          <FlaskConical size={14} />
          Generate synthetic events in the Sandbox
          <ArrowRight size={13} />
        </Link>
      </div>

      <MetricsRow />

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_380px]">
        <AttentionTable payments={payments} />
        <LiveActivityFeed activity={activity} />
      </div>
    </div>
  );
}
