import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import MetricsRow from '../dashboard/MetricsRow';
import LiveActivityFeed from '../dashboard/LiveActivityFeed';
import { useRecoveryState } from '../../lib/RecoveryContext';

export default function ProductPreview() {
  const { activity } = useRecoveryState();

  return (
    <section id="analytics" className="border-t border-[var(--color-line)] py-16">
      <div className="mx-auto max-w-[1200px] px-4 sm:px-6 lg:px-8">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div className="max-w-xl">
            <div className="flex items-center gap-2">
              <h2 className="text-[26px] font-semibold text-[var(--color-ink)]">The system is already operating.</h2>
              <Badge variant="neutral">Live, simulated data</Badge>
            </div>
            <p className="mt-3 text-[14.5px] leading-relaxed text-[var(--color-ink-soft)]">
              This is the real Command Center, rendering live from the same engine running behind it right
              now — not a screenshot. Numbers below will keep moving as you read this.
            </p>
          </div>
          <Link to="/app">
            <Button size="lg" icon={ArrowRight}>Enter RecoveryFlow</Button>
          </Link>
        </div>

        <div className="mt-8 flex flex-col gap-5">
          <MetricsRow />
          <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1fr_380px]">
            <div className="flex items-center justify-center rounded-[var(--radius-lg)] border border-dashed border-[var(--color-line)] bg-[var(--color-surface)] p-10 text-center">
              <div>
                <p className="text-[14px] font-medium text-[var(--color-ink)]">Payments requiring attention</p>
                <p className="mt-1 max-w-xs text-[13px] text-[var(--color-ink-faint)]">
                  See the full queue, approve or reject pending actions, and inspect any payment's full agent
                  trace inside the Command Center.
                </p>
                <Link to="/app" className="mt-3 inline-flex items-center gap-1.5 text-[13px] font-medium text-[var(--color-navy-700)] hover:text-[var(--color-navy-800)]">
                  Open the queue
                  <ArrowRight size={13} />
                </Link>
              </div>
            </div>
            <LiveActivityFeed activity={activity} />
          </div>
        </div>
      </div>
    </section>
  );
}
