import clsx from 'clsx';

export function Card({ className, children, ...props }) {
  return (
    <div
      className={clsx(
        'rounded-[var(--radius-lg)] border border-[var(--color-line)] bg-[var(--color-surface-raised)] shadow-[var(--shadow-card)]',
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({ title, subtitle, action, className }) {
  return (
    <div className={clsx('flex items-start justify-between gap-4 border-b border-[var(--color-line-soft)] px-5 py-4', className)}>
      <div>
        <h3 className="text-[15px] font-semibold text-[var(--color-ink)]">{title}</h3>
        {subtitle && <p className="mt-0.5 text-[13px] text-[var(--color-ink-faint)]">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}
