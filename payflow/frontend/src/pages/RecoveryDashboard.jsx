import Badge from '../components/ui/Badge';
import MetricsRow from '../components/dashboard/MetricsRow';
import AttentionTable from '../components/dashboard/AttentionTable';
import LiveActivityFeed from '../components/dashboard/LiveActivityFeed';
import RecoverySimulation from '../components/dashboard/RecoverySimulation';
import { useRecoveryState } from '../lib/RecoveryContext';

export default function RecoveryDashboard() {
  const { payments, activity } = useRecoveryState();

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

      <MetricsRow />

      <RecoverySimulation />

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_380px]">
        <AttentionTable payments={payments} />
        <LiveActivityFeed activity={activity} />
      </div>
    </div>
  );
}
