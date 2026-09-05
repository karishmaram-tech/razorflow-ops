import { Radio, Search, TrendingUp, Calculator, ShieldAlert, GitBranch, Zap, CheckCircle2 } from 'lucide-react';
import { Card, CardHeader } from '../ui/Card';
import EmptyState from '../ui/EmptyState';
import { formatClock } from '../../lib/format';

const ICONS = {
  system: Radio,
  investigation: Search,
  prediction: TrendingUp,
  economics: Calculator,
  risk: ShieldAlert,
  strategy: GitBranch,
  execution: Zap,
  verification: CheckCircle2,
};

export default function LiveActivityFeed({ activity }) {
  return (
    <Card className="flex flex-col">
      <CardHeader
        title="Live recovery activity"
        subtitle="Every agent action, as it happens"
        action={(
          <span className="flex items-center gap-1.5 text-[11px] font-medium text-[var(--color-success-700)]">
            <span className="h-1.5 w-1.5 rounded-full bg-[var(--color-success-600)] pulse-dot" />
            Live
          </span>
        )}
      />
      <div className="max-h-[420px] flex-1 overflow-y-auto">
        {activity.length === 0 ? (
          <EmptyState icon={Radio} title="No agent activity yet" description="Activity will appear here as payments enter the recovery pipeline." />
        ) : (
          <ul className="divide-y divide-[var(--color-line-soft)]">
            {activity.map((item) => {
              const Icon = ICONS[item.agent] || Radio;
              return (
                <li key={item.id} className="flex items-start gap-3 px-5 py-3 tick-in">
                  <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[var(--color-line-soft)] text-[var(--color-navy-700)]">
                    <Icon size={13} strokeWidth={2} />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-[13px] leading-snug text-[var(--color-ink)]">{item.text}</p>
                    <p className="mt-0.5 font-mono text-[11px] text-[var(--color-ink-faint)]">
                      {formatClock(item.timestamp)} · {item.paymentId}
                    </p>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </Card>
  );
}
