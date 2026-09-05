import {
  Search, TrendingUp, Calculator, ShieldAlert, GitBranch, Zap, CheckCircle2, AlertTriangle,
} from 'lucide-react';
import { AGENTS } from '../../lib/domain';
import { formatClock } from '../../lib/format';

const ICONS = {
  investigation: Search,
  prediction: TrendingUp,
  economics: Calculator,
  risk: ShieldAlert,
  strategy: GitBranch,
  execution: Zap,
  verification: CheckCircle2,
};

const AGENT_MAP = Object.fromEntries(AGENTS.map((a) => [a.key, a]));

export default function AgentTraceList({ trace }) {
  if (!trace.length) {
    return <p className="px-5 py-6 text-[13px] text-[var(--color-ink-faint)]">Awaiting the first agent evaluation.</p>;
  }

  return (
    <ol className="divide-y divide-[var(--color-line-soft)]">
      {trace.map((entry, i) => {
        const meta = AGENT_MAP[entry.agent];
        const Icon = ICONS[entry.agent] || CheckCircle2;
        return (
          <li key={`${entry.agent}-${i}`} className="flex gap-3.5 px-5 py-4 tick-in">
            <div className="flex flex-col items-center">
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-[var(--color-line)] bg-[var(--color-surface)] text-[var(--color-navy-700)]">
                <Icon size={15} strokeWidth={2} />
              </span>
              {i < trace.length - 1 && <span className="mt-1 w-px flex-1 bg-[var(--color-line-soft)]" />}
            </div>
            <div className="min-w-0 flex-1 pb-1">
              <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-0.5">
                <p className="text-[13.5px] font-semibold text-[var(--color-ink)]">
                  {meta?.name || entry.title}
                </p>
                <span className="font-mono text-[11px] text-[var(--color-ink-faint)]">{formatClock(entry.timestamp)}</span>
              </div>
              {meta?.role && <p className="mt-0.5 text-[12px] text-[var(--color-ink-faint)]">{meta.role}</p>}
              <p className="mt-1.5 text-[13.5px] leading-relaxed text-[var(--color-ink)]">{entry.finding}</p>

              {typeof entry.confidence === 'number' && (
                <div className="mt-2 flex items-center gap-2">
                  <div className="h-1.5 w-28 overflow-hidden rounded-full bg-[var(--color-line-soft)]">
                    <div
                      className="h-full rounded-full bg-[var(--color-navy-600)]"
                      style={{ width: `${entry.confidence}%` }}
                    />
                  </div>
                  <span className="font-mono text-[11px] text-[var(--color-ink-faint)]">{entry.confidence}% confidence</span>
                </div>
              )}

              {entry.evidence?.length > 0 && (
                <ul className="mt-2 space-y-1">
                  {entry.evidence.map((ev, j) => (
                    <li key={j} className="flex gap-1.5 text-[12.5px] text-[var(--color-ink-soft)]">
                      <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-[var(--color-ink-faint)]" />
                      {ev}
                    </li>
                  ))}
                </ul>
              )}

              {entry.disagreement && (
                <div className="mt-2.5 flex gap-2 rounded-[var(--radius-sm)] border border-[var(--color-warning-600)]/35 bg-[var(--color-warning-100)] px-3 py-2.5">
                  <AlertTriangle size={15} className="mt-0.5 shrink-0 text-[var(--color-warning-700)]" />
                  <p className="text-[12.5px] leading-relaxed text-[var(--color-warning-700)]">
                    <span className="font-semibold">{entry.disagreement.from} overruled {entry.disagreement.against}: </span>
                    {entry.disagreement.note}
                  </p>
                </div>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
