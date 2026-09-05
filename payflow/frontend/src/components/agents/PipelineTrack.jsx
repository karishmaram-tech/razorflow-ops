import clsx from 'clsx';
import { DISPLAY_STEPS, stepIndex } from '../../lib/stages';

export default function PipelineTrack({ payment, compact = false }) {
  const current = stepIndex(payment.stage);
  const isRejectedOrFailed = payment.stage === 'resolved' && !payment.outcome?.recovered;

  return (
    <div className="flex items-center" aria-label="Recovery pipeline progress">
      {DISPLAY_STEPS.map((step, i) => {
        const done = i < current || (i === current && payment.stage === 'resolved');
        const active = i === current && payment.stage !== 'resolved';
        const isLast = i === DISPLAY_STEPS.length - 1;
        let dotClass = 'bg-[var(--color-line)]';
        if (done) dotClass = isRejectedOrFailed && isLast ? 'bg-[var(--color-danger-600)]' : 'bg-[var(--color-success-600)]';
        if (active) dotClass = 'bg-[var(--color-navy-700)]';

        return (
          <div key={step.key} className="flex items-center">
            <span
              className={clsx(
                'block rounded-full transition-colors duration-300',
                compact ? 'h-1.5 w-1.5' : 'h-2 w-2',
                dotClass,
                active && 'pulse-dot',
              )}
              title={step.label}
            />
            {!isLast && (
              <span
                className={clsx(
                  'transition-colors duration-300',
                  compact ? 'h-px w-3' : 'h-px w-5',
                  done ? 'bg-[var(--color-success-600)]/50' : 'bg-[var(--color-line)]',
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
