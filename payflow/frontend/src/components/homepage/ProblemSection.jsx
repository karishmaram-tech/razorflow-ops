import { Card } from '../ui/Card';
import Badge from '../ui/Badge';

const EXAMPLES = [
  {
    amount: '₹499',
    context: 'Low-value, low margin subscription',
    verdict: 'No automated intervention',
    reason: 'Expected recovery value doesn\'t clear the cost of acting.',
    variant: 'neutral',
  },
  {
    amount: '₹24,999',
    context: 'Recent temporary bank decline',
    verdict: 'Delayed retry',
    reason: '82% modelled recovery probability once the balance window refreshes.',
    variant: 'success',
  },
  {
    amount: '₹8,500',
    context: 'Third failed attempt this cycle',
    verdict: 'Controlled customer notification',
    reason: 'Further silent retries risk annoying a customer who may already be aware.',
    variant: 'warning',
  },
  {
    amount: '₹45,000',
    context: 'High value, uncertain outcome',
    verdict: 'Routed to human review',
    reason: 'Confidence falls below the threshold for unattended action at this value.',
    variant: 'info',
  },
];

export default function ProblemSection() {
  return (
    <section className="border-t border-[var(--color-line)] bg-[var(--color-surface)] py-16">
      <div className="mx-auto max-w-[1100px] px-4 sm:px-6 lg:px-8">
        <div className="max-w-2xl">
          <h2 className="text-[26px] font-semibold text-[var(--color-ink)]">Failed payments aren't all the same.</h2>
          <p className="mt-3 text-[14.5px] leading-relaxed text-[var(--color-ink-soft)]">
            Some are temporary. Some are permanent. Some are worth pursuing aggressively; others cost more to
            chase than they're worth. Treating every failure with the same retry schedule isn't intelligent
            recovery — it's just noise, some of which actively damages the customer relationship.
          </p>
        </div>

        <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {EXAMPLES.map((ex) => (
            <Card key={ex.amount} className="flex flex-col gap-3 p-4">
              <p className="font-mono text-[20px] font-semibold text-[var(--color-ink)]">{ex.amount}</p>
              <p className="text-[12.5px] text-[var(--color-ink-faint)]">{ex.context}</p>
              <div className="mt-1 border-t border-[var(--color-line-soft)] pt-3">
                <Badge variant={ex.variant}>{ex.verdict}</Badge>
                <p className="mt-2 text-[12.5px] leading-relaxed text-[var(--color-ink-soft)]">{ex.reason}</p>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}
