import { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { CheckCircle2 } from 'lucide-react';

const STEPS = [
  { label: 'Payment failed', detail: 'Bank declined', tone: 'danger' },
  { label: 'Investigation', detail: 'Temporary failure detected', tone: 'neutral' },
  { label: 'Prediction', detail: '87% recovery probability', tone: 'neutral' },
  { label: 'Economics', detail: 'Positive expected net value', tone: 'neutral' },
  { label: 'Risk', detail: 'Low customer-friction risk', tone: 'neutral' },
  { label: 'Strategy', detail: 'Delayed retry selected', tone: 'neutral' },
  { label: 'Execution', detail: 'Action completed', tone: 'neutral' },
  { label: 'Verification', detail: 'Payment recovered', tone: 'success' },
];

export default function HeroPipelineVisual() {
  const [index, setIndex] = useState(0);
  const [recoveredTotal, setRecoveredTotal] = useState(287400);

  useEffect(() => {
    const interval = setInterval(() => {
      setIndex((i) => {
        const next = (i + 1) % STEPS.length;
        if (next === 0) {
          setTimeout(() => setRecoveredTotal((v) => v + 12499), 250);
        }
        return next;
      });
    }, 1400);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="w-full max-w-sm rounded-[var(--radius-lg)] border border-[var(--color-line)] bg-[var(--color-surface-raised)] shadow-[var(--shadow-raised)]">
      <div className="flex items-center justify-between border-b border-[var(--color-line-soft)] px-4 py-3">
        <div>
          <p className="font-mono text-[12.5px] font-medium text-[var(--color-ink)]">RF-2841</p>
          <p className="text-[11px] text-[var(--color-ink-faint)]">Example payment · illustrative</p>
        </div>
        <p className="font-mono text-[15px] font-semibold text-[var(--color-ink)]">₹12,499</p>
      </div>

      <div className="flex h-64 flex-col justify-center gap-3 px-5 py-5">
        {STEPS.map((step, i) => {
          const isPast = i < index;
          const isCurrent = i === index;
          if (!isPast && !isCurrent) return null;
          return (
            <motion.div
              key={`${step.label}-${i <= index}`}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: isCurrent ? 1 : 0.35, y: 0 }}
              transition={{ duration: 0.45, ease: 'easeOut' }}
              className="flex items-center gap-2.5"
            >
              <span
                className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] font-semibold ${
                  step.tone === 'danger'
                    ? 'bg-[var(--color-danger-100)] text-[var(--color-danger-700)]'
                    : step.tone === 'success'
                      ? 'bg-[var(--color-success-100)] text-[var(--color-success-700)]'
                      : 'bg-[var(--color-line-soft)] text-[var(--color-navy-700)]'
                }`}
              >
                {step.tone === 'success' ? <CheckCircle2 size={12} /> : i + 1}
              </span>
              <div className="min-w-0">
                <p className={`text-[13px] font-medium ${isCurrent ? 'text-[var(--color-ink)]' : 'text-[var(--color-ink-faint)]'}`}>
                  {step.label}
                </p>
                {isCurrent && (
                  <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.15 }}
                    className="text-[12px] text-[var(--color-ink-faint)]"
                  >
                    {step.detail}
                  </motion.p>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>

      <div className="flex items-center justify-between border-t border-[var(--color-line-soft)] bg-[var(--color-surface)] px-4 py-3">
        <span className="text-[11.5px] text-[var(--color-ink-faint)]">Recovered this session</span>
        <AnimatePresence mode="popLayout">
          <motion.span
            key={recoveredTotal}
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            className="font-mono text-[14px] font-semibold text-[var(--color-success-700)]"
          >
            ₹{recoveredTotal.toLocaleString('en-IN')}
          </motion.span>
        </AnimatePresence>
      </div>
    </div>
  );
}
