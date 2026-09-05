import clsx from 'clsx';
import { useCountUp } from '../../lib/useCountUp';
import { formatINR, formatPercent } from '../../lib/format';

export default function StatCard({ label, value, format = 'currency', helpText, tone = 'neutral', trend }) {
  const animated = useCountUp(value);
  const display = format === 'currency'
    ? formatINR(Math.round(animated))
    : format === 'percent'
      ? formatPercent(animated)
      : format === 'multiplier'
        ? `${animated.toFixed(1)}×`
        : Math.round(animated).toLocaleString('en-IN');

  const toneClass = {
    neutral: 'text-[var(--color-ink)]',
    success: 'text-[var(--color-success-700)]',
    danger: 'text-[var(--color-danger-700)]',
    warning: 'text-[var(--color-warning-700)]',
  }[tone];

  return (
    <div className="flex flex-col gap-1.5 rounded-[var(--radius-lg)] border border-[var(--color-line)] bg-[var(--color-surface-raised)] px-4 py-3.5 shadow-[var(--shadow-card)] min-w-0">
      <span className="text-[12px] font-medium text-[var(--color-ink-faint)]">{label}</span>
      <span className={clsx('font-mono text-[22px] font-semibold leading-tight tabular-nums truncate', toneClass)}>
        {display}
      </span>
      {(helpText || trend) && (
        <div className="flex items-center gap-1.5 text-[12px] text-[var(--color-ink-faint)]">
          {trend && (
            <span className={trend.direction === 'up' ? 'text-[var(--color-success-700)]' : 'text-[var(--color-danger-700)]'}>
              {trend.direction === 'up' ? '↑' : '↓'} {trend.value}
            </span>
          )}
          {helpText && <span>{helpText}</span>}
        </div>
      )}
    </div>
  );
}
