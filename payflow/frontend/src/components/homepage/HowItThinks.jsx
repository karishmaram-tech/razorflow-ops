import { useState } from 'react';
import {
  Search, TrendingUp, Calculator, ShieldAlert, GitBranch, Zap, CheckCircle2, Brain,
} from 'lucide-react';
import { Card } from '../ui/Card';

const STEPS = [
  {
    n: '01', key: 'investigate', label: 'Investigate', icon: Search,
    question: 'What happened?',
    body: 'Classifies the failure using processor codes, issuer response, and this payment\'s attempt history.',
    example: '"Processor code EXPIRED_CARD — retrying the same instrument will not succeed."',
  },
  {
    n: '02', key: 'predict', label: 'Predict', icon: TrendingUp,
    question: 'Can it be recovered?',
    body: 'Scores recovery probability against outcomes on comparable payments from the last 90 days.',
    example: '"Recovery probability: 78%, based on 411 comparable processor-timeout payments."',
  },
  {
    n: '03', key: 'economics', label: 'Economics', icon: Calculator,
    question: 'Is recovery worth pursuing?',
    body: 'Weighs expected recovered value against the real cost of the action being considered.',
    example: '"Gross expected recovery ₹6,980 against a ₹6 action cost — net positive."',
  },
  {
    n: '04', key: 'risk', label: 'Risk', icon: ShieldAlert,
    question: 'What could go wrong?',
    body: 'Flags customer-friction and compliance risk in the proposed action before it\'s taken.',
    example: '"Three prior attempts already made — further silent retries risk annoyance."',
  },
  {
    n: '05', key: 'strategy', label: 'Strategy', icon: GitBranch,
    question: 'What\'s the best action?',
    body: 'Selects the action with the best risk-adjusted expected value — sometimes overruling an earlier agent.',
    example: '"Immediate retry rejected. Delaying 6 hours keeps expected value positive."',
  },
  {
    n: '06', key: 'execute', label: 'Execute', icon: Zap,
    question: 'Take the action.',
    body: 'Carries out the selected action against the processor or notification service.',
    example: '"Delayed retry executed against payment processor."',
  },
  {
    n: '07', key: 'verify', label: 'Verify', icon: CheckCircle2,
    question: 'Did it work?',
    body: 'Confirms the outcome directly with the processor rather than assuming success.',
    example: '"Processor confirmed settlement. Payment recovered."',
  },
  {
    n: '08', key: 'learn', label: 'Learn', icon: Brain,
    question: 'What should change next time?',
    body: 'Feeds the verified outcome back into the prediction model for the next decision cycle.',
    example: '"Delayed retries outperformed immediate retries for this failure type — weight adjusted."',
  },
];

export default function HowItThinks() {
  const [active, setActive] = useState(0);
  const step = STEPS[active];

  return (
    <section id="how-it-works" className="border-t border-[var(--color-line)] py-16">
      <div className="mx-auto max-w-[1100px] px-4 sm:px-6 lg:px-8">
        <div className="max-w-2xl">
          <h2 className="text-[26px] font-semibold text-[var(--color-ink)]">From payment failure to recovery.</h2>
          <p className="mt-3 text-[14.5px] leading-relaxed text-[var(--color-ink-soft)]">
            Every failed payment moves through the same eight-step reasoning pipeline. Select a step to see
            what it's responsible for.
          </p>
        </div>

        <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-[280px_1fr]">
          <div className="flex gap-2 overflow-x-auto pb-2 lg:flex-col lg:overflow-visible lg:pb-0">
            {STEPS.map((s, i) => {
              const Icon = s.icon;
              const isActive = i === active;
              return (
                <button
                  key={s.key}
                  onClick={() => setActive(i)}
                  className={`flex shrink-0 items-center gap-3 rounded-[var(--radius-sm)] border px-3.5 py-2.5 text-left transition-colors lg:shrink ${
                    isActive
                      ? 'border-[var(--color-navy-700)] bg-[var(--color-navy-800)] text-white'
                      : 'border-[var(--color-line)] bg-[var(--color-surface-raised)] text-[var(--color-ink-soft)] hover:border-[var(--color-navy-500)]'
                  }`}
                >
                  <span className={`font-mono text-[11px] ${isActive ? 'text-white/60' : 'text-[var(--color-ink-faint)]'}`}>{s.n}</span>
                  <Icon size={15} strokeWidth={2} />
                  <span className="whitespace-nowrap text-[13px] font-medium">{s.label}</span>
                </button>
              );
            })}
          </div>

          <Card className="p-6">
            <p className="text-[12px] font-medium uppercase tracking-wide text-[var(--color-ink-faint)]">{step.question}</p>
            <h3 className="mt-1 text-[19px] font-semibold text-[var(--color-ink)]">{step.label}</h3>
            <p className="mt-3 max-w-lg text-[14px] leading-relaxed text-[var(--color-ink-soft)]">{step.body}</p>
            <div className="mt-4 rounded-[var(--radius-sm)] border border-[var(--color-line-soft)] bg-[var(--color-surface)] px-4 py-3">
              <p className="text-[11.5px] font-medium uppercase tracking-wide text-[var(--color-ink-faint)]">Example decision</p>
              <p className="mt-1 text-[13.5px] italic text-[var(--color-ink-soft)]">{step.example}</p>
            </div>
          </Card>
        </div>
      </div>
    </section>
  );
}
