import { useMemo } from 'react';
import { Card, CardHeader } from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import { STRATEGIES } from '../lib/domain';
import { formatINR, formatPercent } from '../lib/format';
import { useRecoveryState } from '../lib/RecoveryContext';

function frictionVariant(friction) {
  if (friction === 'Low') return 'success';
  if (friction === 'Medium') return 'warning';
  if (friction === 'High') return 'danger';
  return 'neutral';
}

export default function Strategies() {
  const { payments } = useRecoveryState();

  const stats = useMemo(() => {
    const resolved = payments.filter((p) => p.stage === 'resolved' && p.decision && !p.outcome?.rejected);
    return Object.keys(STRATEGIES).reduce((acc, key) => {
      const used = resolved.filter((p) => p.decision.strategyKey === key);
      const recovered = used.filter((p) => p.outcome?.recovered);
      acc[key] = {
        used: used.length,
        recovered: recovered.length,
        rate: used.length ? (recovered.length / used.length) * 100 : null,
        avgNet: used.length ? used.reduce((s, p) => s + (p.outcome?.actualNet || 0), 0) / used.length : null,
      };
      return acc;
    }, {});
  }, [payments]);

  const mostUsed = Object.entries(stats).sort((a, b) => b[1].used - a[1].used)[0]?.[0];

  return (
    <div className="mx-auto flex max-w-[1100px] flex-col gap-5 px-4 py-6 sm:px-6 lg:px-8">
      <div>
        <h1 className="text-[20px] font-semibold text-[var(--color-ink)]">Recovery strategies</h1>
        <p className="mt-1 text-[13.5px] text-[var(--color-ink-faint)]">
          Every available action, and how it has actually performed on payments resolved so far.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {Object.entries(STRATEGIES).map(([key, s]) => {
          const st = stats[key];
          return (
            <Card key={key} className={key === mostUsed && st.used > 0 ? 'ring-1 ring-[var(--color-navy-600)]/25' : ''}>
              <CardHeader
                title={s.label}
                subtitle={s.description}
                action={key === mostUsed && st.used > 0 ? <Badge variant="navy">Most used</Badge> : null}
              />
              <div className="grid grid-cols-2 gap-4 px-5 py-4 sm:grid-cols-4">
                <div>
                  <p className="text-[11.5px] font-medium uppercase tracking-wide text-[var(--color-ink-faint)]">Cost</p>
                  <p className="mt-0.5 font-mono text-[14px] text-[var(--color-ink)]">₹{s.cost}</p>
                </div>
                <div>
                  <p className="text-[11.5px] font-medium uppercase tracking-wide text-[var(--color-ink-faint)]">Friction</p>
                  <Badge variant={frictionVariant(s.friction)} className="mt-1">{s.friction}</Badge>
                </div>
                <div>
                  <p className="text-[11.5px] font-medium uppercase tracking-wide text-[var(--color-ink-faint)]">Used</p>
                  <p className="mt-0.5 font-mono text-[14px] text-[var(--color-ink)]">{st.used}</p>
                </div>
                <div>
                  <p className="text-[11.5px] font-medium uppercase tracking-wide text-[var(--color-ink-faint)]">Recovery rate</p>
                  <p className="mt-0.5 font-mono text-[14px] text-[var(--color-ink)]">
                    {st.rate === null ? '—' : formatPercent(st.rate)}
                  </p>
                </div>
              </div>
              {st.avgNet !== null && (
                <div className="border-t border-[var(--color-line-soft)] px-5 py-3 text-[12.5px] text-[var(--color-ink-faint)]">
                  Average net value per payment: <span className="font-mono text-[var(--color-ink-soft)]">{formatINR(st.avgNet)}</span>
                </div>
              )}
            </Card>
          );
        })}
      </div>
    </div>
  );
}
