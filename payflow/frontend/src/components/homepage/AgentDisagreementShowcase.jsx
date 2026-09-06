import { TrendingUp, ShieldAlert, Calculator, GitBranch, AlertTriangle } from 'lucide-react';
import { Card } from '../ui/Card';
import Badge from '../ui/Badge';

export default function AgentDisagreementShowcase() {
  return (
    <section id="agents" className="border-t border-[var(--color-line)] bg-[var(--color-surface)] py-16">
      <div className="mx-auto max-w-[1100px] px-4 sm:px-6 lg:px-8">
        <div className="max-w-2xl">
          <h2 className="text-[26px] font-semibold text-[var(--color-ink)]">Seven agents. Real disagreement.</h2>
          <p className="mt-3 text-[14.5px] leading-relaxed text-[var(--color-ink-soft)]">
            Investigation, Prediction, Economics, Risk, Strategy, Execution, and Verification each have a
            distinct responsibility — and they don't always point the same way. When they conflict, Strategy
            has to make a real trade-off, not just average the votes.
          </p>
        </div>

        <Card className="mt-8 overflow-hidden">
          <div className="flex items-center justify-between border-b border-[var(--color-line-soft)] px-5 py-3.5">
            <span className="font-mono text-[13px] font-medium text-[var(--color-ink)]">RF-3191 · ₹8,922</span>
            <Badge variant="neutral">Example decision</Badge>
          </div>
          <div className="grid grid-cols-1 divide-y divide-[var(--color-line-soft)] sm:grid-cols-2 sm:divide-x sm:divide-y-0">
            <div className="flex gap-3 px-5 py-4">
              <TrendingUp size={16} className="mt-0.5 shrink-0 text-[var(--color-navy-700)]" />
              <div>
                <p className="text-[12.5px] font-semibold text-[var(--color-ink)]">Prediction Agent</p>
                <p className="mt-0.5 text-[13px] text-[var(--color-ink-soft)]">Recovery probability: 78%</p>
              </div>
            </div>
            <div className="flex gap-3 px-5 py-4">
              <Calculator size={16} className="mt-0.5 shrink-0 text-[var(--color-navy-700)]" />
              <div>
                <p className="text-[12.5px] font-semibold text-[var(--color-ink)]">Economics Agent</p>
                <p className="mt-0.5 text-[13px] text-[var(--color-ink-soft)]">Expected net value: +₹6,974</p>
              </div>
            </div>
            <div className="flex gap-3 px-5 py-4">
              <ShieldAlert size={16} className="mt-0.5 shrink-0 text-[var(--color-danger-600)]" />
              <div>
                <p className="text-[12.5px] font-semibold text-[var(--color-ink)]">Risk Agent</p>
                <p className="mt-0.5 text-[13px] text-[var(--color-ink-soft)]">Customer-friction risk: high (3 prior attempts)</p>
              </div>
            </div>
            <div className="flex gap-3 px-5 py-4">
              <GitBranch size={16} className="mt-0.5 shrink-0 text-[var(--color-navy-700)]" />
              <div>
                <p className="text-[12.5px] font-semibold text-[var(--color-ink)]">Strategy Agent</p>
                <p className="mt-0.5 text-[13px] text-[var(--color-ink-soft)]">Immediate retry rejected</p>
              </div>
            </div>
          </div>
          <div className="flex gap-2.5 border-t border-[var(--color-line-soft)] bg-[var(--color-warning-100)] px-5 py-4">
            <AlertTriangle size={16} className="mt-0.5 shrink-0 text-[var(--color-warning-700)]" />
            <div>
              <p className="text-[13px] font-semibold text-[var(--color-warning-700)]">
                Final decision: escalate to a human specialist.
              </p>
              <p className="mt-1 text-[12.5px] leading-relaxed text-[var(--color-warning-700)]">
                Risk Agent overruled Prediction Agent — recovery odds and net value both looked positive, but
                further automated retries after three prior attempts were judged too likely to damage the
                customer relationship for an unattended action.
              </p>
            </div>
          </div>
        </Card>
      </div>
    </section>
  );
}
