import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Radio, Menu, X, ArrowRight } from 'lucide-react';
import Button from '../ui/Button';

const LINKS = [
  { href: '#product', label: 'Product' },
  { href: '#how-it-works', label: 'How it works' },
  { href: '#agents', label: 'Agents' },
  { href: '#analytics', label: 'Analytics' },
  { href: '#control', label: 'Control' },
];

export default function PublicNav() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-[var(--color-line)] bg-[var(--color-paper)]/90 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-[1200px] items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link to="/" className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-[var(--radius-xs)] bg-[var(--color-navy-800)]">
            <Radio size={15} className="text-white" strokeWidth={2.25} />
          </div>
          <span className="text-[14.5px] font-semibold text-[var(--color-ink)]">RecoveryFlow</span>
        </Link>

        <nav className="hidden items-center gap-1 md:flex">
          {LINKS.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className="rounded-[var(--radius-sm)] px-3 py-2 text-[13.5px] font-medium text-[var(--color-ink-soft)] hover:bg-[var(--color-line-soft)] hover:text-[var(--color-ink)]"
            >
              {l.label}
            </a>
          ))}
        </nav>

        <div className="hidden items-center gap-2 md:flex">
          <Link to="/app/sandbox">
            <Button variant="ghost" size="sm">Open Sandbox</Button>
          </Link>
          <Link to="/app">
            <Button variant="primary" size="sm" icon={ArrowRight}>Enter RecoveryFlow</Button>
          </Link>
        </div>

        <button
          className="flex h-9 w-9 items-center justify-center rounded-[var(--radius-sm)] text-[var(--color-ink)] md:hidden"
          onClick={() => setOpen((v) => !v)}
          aria-label={open ? 'Close menu' : 'Open menu'}
          aria-expanded={open}
        >
          {open ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {open && (
        <div className="border-t border-[var(--color-line)] bg-[var(--color-surface-raised)] px-4 py-4 md:hidden">
          <nav className="flex flex-col gap-1">
            {LINKS.map((l) => (
              <a
                key={l.href}
                href={l.href}
                onClick={() => setOpen(false)}
                className="rounded-[var(--radius-sm)] px-3 py-2.5 text-[14px] font-medium text-[var(--color-ink-soft)] hover:bg-[var(--color-line-soft)]"
              >
                {l.label}
              </a>
            ))}
          </nav>
          <div className="mt-3 flex flex-col gap-2">
            <Link to="/app/sandbox" onClick={() => setOpen(false)}>
              <Button variant="secondary" className="w-full">Open Sandbox</Button>
            </Link>
            <Link to="/app" onClick={() => setOpen(false)}>
              <Button variant="primary" className="w-full" icon={ArrowRight}>Enter RecoveryFlow</Button>
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
