import { useEffect } from 'react';
import { X } from 'lucide-react';

export default function Modal({ open, onClose, title, children, footer, width = 'max-w-md' }) {
  useEffect(() => {
    function onKey(e) {
      if (e.key === 'Escape') onClose?.();
    }
    if (open) document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
      <div className="absolute inset-0 bg-[var(--color-navy-900)]/45" onClick={onClose} aria-hidden="true" />
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={`relative w-full ${width} rounded-[var(--radius-lg)] border border-[var(--color-line)] bg-[var(--color-surface-raised)] shadow-[var(--shadow-overlay)] tick-in`}
      >
        <div className="flex items-center justify-between border-b border-[var(--color-line-soft)] px-5 py-4">
          <h3 className="text-[15px] font-semibold text-[var(--color-ink)]">{title}</h3>
          <button
            onClick={onClose}
            aria-label="Close dialog"
            className="rounded-[var(--radius-xs)] p-1 text-[var(--color-ink-faint)] hover:bg-[var(--color-line-soft)] hover:text-[var(--color-ink)]"
          >
            <X size={16} />
          </button>
        </div>
        <div className="max-h-[70vh] overflow-y-auto px-5 py-4">{children}</div>
        {footer && <div className="flex items-center justify-end gap-2 border-t border-[var(--color-line-soft)] px-5 py-3.5">{footer}</div>}
      </div>
    </div>
  );
}
