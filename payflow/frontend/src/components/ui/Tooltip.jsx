import { useState } from 'react';

export default function Tooltip({ label, children }) {
  const [open, setOpen] = useState(false);
  return (
    <span
      className="relative inline-flex"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onFocus={() => setOpen(true)}
      onBlur={() => setOpen(false)}
    >
      {children}
      {open && (
        <span
          role="tooltip"
          className="absolute bottom-full left-1/2 z-50 mb-2 w-max max-w-56 -translate-x-1/2 rounded-[var(--radius-sm)] bg-[var(--color-navy-900)] px-2.5 py-1.5 text-[12px] leading-snug text-white shadow-[var(--shadow-raised)]"
        >
          {label}
        </span>
      )}
    </span>
  );
}
