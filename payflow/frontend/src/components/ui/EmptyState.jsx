export default function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 px-6 py-14 text-center">
      {Icon && (
        <div className="flex h-11 w-11 items-center justify-center rounded-full bg-[var(--color-line-soft)] text-[var(--color-ink-faint)]">
          <Icon size={20} strokeWidth={1.75} />
        </div>
      )}
      <div className="max-w-xs">
        <p className="text-[14px] font-medium text-[var(--color-ink)]">{title}</p>
        {description && <p className="mt-1 text-[13px] text-[var(--color-ink-faint)]">{description}</p>}
      </div>
      {action}
    </div>
  );
}
