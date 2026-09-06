import { Link } from 'react-router-dom';
import { Radio } from 'lucide-react';

const COLUMNS = [
  {
    title: 'Product',
    links: [
      { label: 'How it works', href: '#how-it-works' },
      { label: 'Command Center', to: '/app' },
      { label: 'Analytics', to: '/app/analytics' },
      { label: 'Control Center', to: '/app/control-center' },
      { label: 'Audit Log', to: '/app/audit-log' },
    ],
  },
  {
    title: 'Resources',
    links: [
      { label: 'Sandbox', to: '/app/sandbox' },
    ],
  },
];

export default function Footer() {
  return (
    <footer className="border-t border-[var(--color-line)] bg-[var(--color-surface)] py-12">
      <div className="mx-auto max-w-[1100px] px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 gap-8 sm:grid-cols-[1.4fr_1fr_1fr]">
          <div>
            <div className="flex items-center gap-2">
              <div className="flex h-6.5 w-6.5 items-center justify-center rounded-[var(--radius-xs)] bg-[var(--color-navy-800)]">
                <Radio size={13} className="text-white" strokeWidth={2.25} />
              </div>
              <span className="text-[14px] font-semibold text-[var(--color-ink)]">RecoveryFlow</span>
            </div>
            <p className="mt-2 max-w-xs text-[13px] leading-relaxed text-[var(--color-ink-faint)]">
              Autonomous revenue recovery for failed payments. A prototype built for demonstration —
              every payment shown across this product is synthetically generated.
            </p>
          </div>
          {COLUMNS.map((col) => (
            <div key={col.title}>
              <p className="text-[12px] font-medium uppercase tracking-wide text-[var(--color-ink-faint)]">{col.title}</p>
              <ul className="mt-3 flex flex-col gap-2">
                {col.links.map((l) => (
                  <li key={l.label}>
                    {l.to ? (
                      <Link to={l.to} className="text-[13.5px] text-[var(--color-ink-soft)] hover:text-[var(--color-ink)]">{l.label}</Link>
                    ) : (
                      <a href={l.href} className="text-[13.5px] text-[var(--color-ink-soft)] hover:text-[var(--color-ink)]">{l.label}</a>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="mt-10 border-t border-[var(--color-line-soft)] pt-6">
          <p className="text-[12px] text-[var(--color-ink-faint)]">
            RecoveryFlow is a prototype. All payment, customer, and outcome data shown is synthetic.
          </p>
        </div>
      </div>
    </footer>
  );
}
