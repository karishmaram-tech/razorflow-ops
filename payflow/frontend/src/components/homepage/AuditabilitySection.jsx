import {
  Search, TrendingUp, Calculator, GitBranch, Zap, CheckCircle2,
} from 'lucide-react';
import { Card } from '../ui/Card';

const TIMELINE = [
  { icon: null, label: 'Payment failed', detail: 'RF-2841 · ₹12,499', tone: 'danger' },
  { icon: Search, label: 'Investigation Agent', detail: 'Temporary bank failure' },
  { icon: TrendingUp, label: 'Prediction Agent', detail: '87% recovery probability' },
  { icon: Calculator, label: 'Economics Agent', detail: 'Positive expected value' },
  { icon: GitBranch, label: 'Strategy Agent', detail: 'Delayed retry selected' },
  { icon: Zap, label: 'Execution Agent', detail: 'Action completed' },
  { icon: CheckCircle2, label: 'Verification Agent', detail: 'Payment recovered', tone: 'success' },
];

export default function AuditabilitySection() {
  return (
    <section className="border-t border-[var(--color-line)] py-16">
      <div className="mx-auto max-w-[1100px] px-4 sm:px-6 lg:px-8">
        <div className="max-w-2xl">
          <h2 className="text-[26px] font-semibold text-[var(--color-ink)]">Every decision is traceable.</h2>
          <p className="mt-3 text-[14.5px] leading-relaxed text-[var(--color-ink-soft)]">
            No black box. Every autonomous action can be traced back to the exact reasoning that produced it,
            timestamped and exportable from the Audit Log.
          </p>
        </div>

        <Card className="mt-8 p-6">
          <ol className="relative flex flex-col gap-5 border-l border-[var(--color-line)] pl-6">
            {TIMELINE.map((t, i) => (
              <li key={i} className="relative">
                <span
                  className={`absolute -left-[29px] top-0.5 flex h-4 w-4 items-center justify-center rounded-full border-2 border-[var(--color-surface-raised)] ${
                    t.tone === 'danger'
                      ? 'bg-[var(--color-danger-600)]'
                      : t.tone === 'success'
                        ? 'bg-[var(--color-success-600)]'
                        : 'bg-[var(--color-navy-600)]'
                  }`}
                />
                <p className="text-[13.5px] font-semibold text-[var(--color-ink)]">{t.label}</p>
                <p className="text-[13px] text-[var(--color-ink-faint)]">{t.detail}</p>
              </li>
            ))}
          </ol>
        </Card>
      </div>
    </section>
  );
}
