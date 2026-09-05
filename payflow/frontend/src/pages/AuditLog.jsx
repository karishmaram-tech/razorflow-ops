import { ScrollText, Download } from 'lucide-react';
import { Card, CardHeader } from '../components/ui/Card';
import Button from '../components/ui/Button';
import EmptyState from '../components/ui/EmptyState';
import Badge from '../components/ui/Badge';
import { formatClock } from '../lib/format';
import { useRecoveryState } from '../lib/RecoveryContext';

function outcomeVariant(outcome) {
  if (outcome === 'Recovered') return 'success';
  if (outcome === 'Not recovered') return 'danger';
  if (outcome === 'Pending') return 'info';
  return 'neutral';
}

export default function AuditLog() {
  const { audit } = useRecoveryState();

  function exportCsv() {
    const header = ['Timestamp', 'Payment', 'Agent', 'Decision', 'Reason', 'Action', 'Outcome'];
    const rows = audit.map((a) => [
      a.timestamp.toISOString(), a.paymentId, a.agent, a.decision, a.reason, a.action, a.outcome,
    ]);
    const csv = [header, ...rows]
      .map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(','))
      .join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `recoveryflow-audit-log-${Date.now()}.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="mx-auto flex max-w-[1200px] flex-col gap-5 px-4 py-6 sm:px-6 lg:px-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-[20px] font-semibold text-[var(--color-ink)]">Audit log</h1>
          <p className="mt-1 text-[13.5px] text-[var(--color-ink-faint)]">Every autonomous action, traceable back to the reasoning behind it.</p>
        </div>
        <Button variant="secondary" icon={Download} onClick={exportCsv} disabled={audit.length === 0}>
          Export report
        </Button>
      </div>

      <Card>
        {audit.length === 0 ? (
          <EmptyState
            icon={ScrollText}
            title="No audit events yet"
            description="Actions taken by RecoveryFlow's agents will be logged here as they happen."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[880px] text-left text-[13px]">
              <thead>
                <tr className="border-b border-[var(--color-line-soft)] text-[11.5px] uppercase tracking-wide text-[var(--color-ink-faint)]">
                  <th className="px-5 py-2.5 font-medium">Time</th>
                  <th className="px-3 py-2.5 font-medium">Payment</th>
                  <th className="px-3 py-2.5 font-medium">Agent</th>
                  <th className="px-3 py-2.5 font-medium">Decision</th>
                  <th className="px-3 py-2.5 font-medium">Reason</th>
                  <th className="px-3 py-2.5 font-medium">Action</th>
                  <th className="px-5 py-2.5 font-medium">Outcome</th>
                </tr>
              </thead>
              <tbody>
                {audit.map((a) => (
                  <tr key={a.id} className="border-b border-[var(--color-line-soft)] last:border-0 hover:bg-[var(--color-surface)]">
                    <td className="whitespace-nowrap px-5 py-3 font-mono text-[12px] text-[var(--color-ink-faint)]">{formatClock(a.timestamp)}</td>
                    <td className="whitespace-nowrap px-3 py-3 font-mono text-[12.5px] text-[var(--color-ink)]">{a.paymentId}</td>
                    <td className="whitespace-nowrap px-3 py-3 text-[var(--color-ink-soft)]">{a.agent}</td>
                    <td className="whitespace-nowrap px-3 py-3 text-[var(--color-ink)]">{a.decision}</td>
                    <td className="px-3 py-3 text-[var(--color-ink-soft)]">{a.reason}</td>
                    <td className="whitespace-nowrap px-3 py-3 text-[var(--color-ink-soft)]">{a.action}</td>
                    <td className="whitespace-nowrap px-5 py-3"><Badge variant={outcomeVariant(a.outcome)}>{a.outcome}</Badge></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
