import clsx from 'clsx';

const VARIANTS = {
  primary: 'bg-[var(--color-navy-800)] text-white hover:bg-[var(--color-navy-700)] active:bg-[var(--color-navy-900)]',
  secondary: 'bg-white text-[var(--color-ink)] border border-[var(--color-line)] hover:border-[var(--color-navy-500)] hover:bg-[var(--color-surface)]',
  ghost: 'text-[var(--color-ink-soft)] hover:bg-[var(--color-line-soft)] hover:text-[var(--color-ink)]',
  danger: 'bg-white text-[var(--color-danger-700)] border border-[var(--color-danger-600)]/40 hover:bg-[var(--color-danger-100)]',
  success: 'bg-[var(--color-success-600)] text-white hover:bg-[var(--color-success-700)]',
};

const SIZES = {
  sm: 'h-8 px-3 text-[13px] gap-1.5',
  md: 'h-9 px-3.5 text-sm gap-2',
  lg: 'h-11 px-5 text-[15px] gap-2',
};

export default function Button({
  as: Comp = 'button',
  variant = 'primary',
  size = 'md',
  className,
  icon: Icon,
  children,
  disabled,
  ...props
}) {
  return (
    <Comp
      className={clsx(
        'inline-flex items-center justify-center rounded-[var(--radius-sm)] font-medium transition-colors duration-150',
        'disabled:opacity-45 disabled:cursor-not-allowed',
        VARIANTS[variant],
        SIZES[size],
        className,
      )}
      disabled={disabled}
      {...props}
    >
      {Icon && <Icon size={size === 'lg' ? 18 : 15} strokeWidth={2} />}
      {children}
    </Comp>
  );
}
