import clsx from 'clsx';

const VARIANTS = {
  neutral: 'bg-[var(--color-line-soft)] text-[var(--color-ink-soft)]',
  success: 'bg-[var(--color-success-100)] text-[var(--color-success-700)]',
  warning: 'bg-[var(--color-warning-100)] text-[var(--color-warning-700)]',
  danger: 'bg-[var(--color-danger-100)] text-[var(--color-danger-700)]',
  info: 'bg-[var(--color-info-100)] text-[var(--color-navy-700)]',
  navy: 'bg-[var(--color-navy-800)] text-white',
};

export default function Badge({ children, variant = 'neutral', dot = false, className }) {
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5 rounded-[var(--radius-xs)] px-2 py-0.5 text-[11px] font-medium leading-5',
        VARIANTS[variant],
        className,
      )}
    >
      {dot && <span className="h-1.5 w-1.5 rounded-full bg-current" />}
      {children}
    </span>
  );
}
