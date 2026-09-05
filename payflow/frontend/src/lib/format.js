// A hand-rolled Indian-numbering compact formatter. Intl's `notation: 'compact'`
// for en-IN depends on the runtime's bundled ICU data and renders
// inconsistently across browsers (observed producing "T" instead of "K" in
// some headless builds) — so amounts shown on charts and cards are formatted
// deterministically instead of trusting the platform.
export function formatINR(value, { compact = false } = {}) {
  if (compact) {
    const sign = value < 0 ? '-' : '';
    const abs = Math.abs(value);
    if (abs >= 1e7) return `${sign}₹${(abs / 1e7).toFixed(1)}Cr`;
    if (abs >= 1e5) return `${sign}₹${(abs / 1e5).toFixed(1)}L`;
    if (abs >= 1e3) return `${sign}₹${(abs / 1e3).toFixed(1)}K`;
    return `${sign}₹${abs.toFixed(0)}`;
  }
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatPercent(value, digits = 1) {
  return `${value.toFixed(digits)}%`;
}

export function formatClock(date) {
  return new Intl.DateTimeFormat('en-IN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).format(date);
}

export function formatRelative(seconds) {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
  return `${(seconds / 3600).toFixed(1)}h`;
}

export function formatDateShort(date) {
  return new Intl.DateTimeFormat('en-IN', {
    day: '2-digit',
    month: 'short',
  }).format(date);
}
