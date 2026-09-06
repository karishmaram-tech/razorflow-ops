import { ShieldCheck, Check } from 'lucide-react';
import { Card } from '../ui/Card';

const CONTROLS = [
  'Maximum retry attempts per payment',
  'Maximum spend on a single recovery action',
  'Customer contact limits',
  'Confidence threshold below which a human must approve',
  'High-value payment threshold',
  'A single automatic-execution switch — off means every action waits for approval',
  'Full audit log of every autonomous decision',
  'Pause automation instantly, at any time',
];

export default function TrustSection() {
  return (
    <section id="control" className="border-t border-[var(--color-line)] bg-[var(--color-surface)] py-16">
      <div className="mx-auto max-w-[1100px] px-4 sm:px-6 lg:px-8">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[var(--color-navy-800)] text-white">
            <ShieldCheck size={17} />
          </div>
          <div className="max-w-xl">
            <h2 className="text-[26px] font-semibold text-[var(--color-ink)]">Autonomous doesn't mean uncontrolled.</h2>
            <p className="mt-3 text-[14.5px] leading-relaxed text-[var(--color-ink-soft)]">
              Every action RecoveryFlow takes against a real payment is bounded by limits you set — and every
              action is logged with the reasoning behind it.
            </p>
          </div>
        </div>

        <Card className="mt-8 grid grid-cols-1 gap-x-8 gap-y-3 p-6 sm:grid-cols-2">
          {CONTROLS.map((c) => (
            <div key={c} className="flex items-start gap-2.5">
              <Check size={16} className="mt-0.5 shrink-0 text-[var(--color-success-600)]" />
              <span className="text-[13.5px] text-[var(--color-ink-soft)]">{c}</span>
            </div>
          ))}
        </Card>
      </div>
    </section>
  );
}
