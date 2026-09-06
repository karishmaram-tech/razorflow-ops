import { Link } from 'react-router-dom';
import { Inbox, Check, X, ChevronRight } from 'lucide-react';
import { Card, CardHeader } from '../ui/Card';
import Button from '../ui/Button';
import EmptyState from '../ui/EmptyState';
import PipelineTrack from '../agents/PipelineTrack';
import StatusBadge from '../agents/StatusBadge';
import { FAILURE_REASONS } from '../../lib/domain';
import { formatINR } from '../../lib/format';
import { useRecoveryDispatch } from '../../lib/RecoveryContext';

export default function AttentionTable({ payments }) {
  const dispatch = useRecoveryDispatch();
  const relevant = payments
    .filter((p) => p.stage !== 'resolved')
    .sort((a, b) => (a.stage === 'awaiting_approval' ? -1 : 1) - (b.stage === 'awaiting_approval' ? -1 : 1))
    .slice(0, 9);

  return (
    <Card>
      <CardHeader
        title="Payments requiring attention"
        subtitle="In flight or awaiting your approval"
      />
      {relevant.length === 0 ? (
        <EmptyState
          icon={Inbox}
          title="No failed payments in the queue"
          description="RecoveryFlow will list payments here the moment a charge fails."
        />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-[13px]">
            <thead>
              <tr className="border-b border-[var(--color-line-soft)] text-[11.5px] uppercase tracking-wide text-[var(--color-ink-faint)]">
                <th className="px-5 py-2.5 font-medium">Payment</th>
                <th className="px-3 py-2.5 font-medium">Failure reason</th>
                <th className="px-3 py-2.5 font-medium">Pipeline</th>
                <th className="px-3 py-2.5 font-medium">Status</th>
                <th className="px-3 py-2.5 font-medium">Expected net</th>
                <th className="px-5 py-2.5 font-medium text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {relevant.map((p) => (
                <tr key={p.id} className="border-b border-[var(--color-line-soft)] last:border-0 hover:bg-[var(--color-surface)]">
                  <td className="px-5 py-3">
                    <Link to={`/app/payments/${p.id}`} className="group flex flex-col hover:underline">
                      <span className="font-mono text-[13px] font-medium text-[var(--color-ink)]">{p.id}</span>
                      <span className="font-mono text-[12px] text-[var(--color-ink-faint)]">{formatINR(p.amount)}</span>
                    </Link>
                  </td>
                  <td className="px-3 py-3 text-[var(--color-ink-soft)]">{FAILURE_REASONS[p.failureReason].label}</td>
                  <td className="px-3 py-3"><PipelineTrack payment={p} compact /></td>
                  <td className="px-3 py-3"><StatusBadge payment={p} /></td>
                  <td className="px-3 py-3 font-mono text-[var(--color-ink-soft)]">
                    {p.economics ? formatINR(p.economics.expectedNet) : '—'}
                  </td>
                  <td className="px-5 py-3">
                    <div className="flex items-center justify-end gap-1.5">
                      {p.stage === 'awaiting_approval' ? (
                        <>
                          <Button size="sm" variant="success" icon={Check} onClick={() => dispatch({ type: 'APPROVE_PAYMENT', id: p.id })}>
                            Approve
                          </Button>
                          <Button size="sm" variant="danger" icon={X} onClick={() => dispatch({ type: 'REJECT_PAYMENT', id: p.id })}>
                            Reject
                          </Button>
                        </>
                      ) : (
                        <Link to={`/app/payments/${p.id}`}>
                          <Button size="sm" variant="ghost" icon={ChevronRight}>Inspect</Button>
                        </Link>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}
