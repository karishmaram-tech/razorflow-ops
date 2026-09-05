import { Link, useParams, Navigate } from 'react-router-dom';
import { ArrowLeft, Check, X, CircleAlert, CircleCheck } from 'lucide-react';
import { Card, CardHeader } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import PipelineTrack from '../components/agents/PipelineTrack';
import StatusBadge from '../components/agents/StatusBadge';
import AgentTraceList from '../components/agents/AgentTraceList';
import { FAILURE_REASONS, STRATEGIES } from '../lib/domain';
import { formatINR, formatClock, formatRelative } from '../lib/format';
import { useRecoveryState, useRecoveryDispatch } from '../lib/RecoveryContext';

function ContextField({ label, value }) {
  return (
    <div>
      <p className="text-[11.5px] font-medium uppercase tracking-wide text-[var(--color-ink-faint)]">{label}</p>
      <p className="mt-0.5 text-[13.5px] text-[var(--color-ink)]">{value}</p>
    </div>
  );
}

export default function PaymentDetail() {
  const { id } = useParams();
  const { payments } = useRecoveryState();
  const dispatch = useRecoveryDispatch();
  const payment = payments.find((p) => p.id === id);

  if (!payment) return <Navigate to="/" replace />;

  const info = FAILURE_REASONS[payment.failureReason];

  return (
    <div className="mx-auto flex max-w-[1100px] flex-col gap-5 px-4 py-6 sm:px-6 lg:px-8">
      <Link to="/" className="flex w-fit items-center gap-1.5 text-[13px] font-medium text-[var(--color-ink-soft)] hover:text-[var(--color-ink)]">
        <ArrowLeft size={15} />
        Back to command center
      </Link>

      <Card className="p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="font-mono text-[18px] font-semibold text-[var(--color-ink)]">{payment.id}</h1>
              <StatusBadge payment={payment} />
            </div>
            <p className="mt-1 font-mono text-[24px] font-semibold text-[var(--color-ink)]">{formatINR(payment.amount)}</p>
            <p className="mt-1 text-[13px] text-[var(--color-ink-faint)]">
              {payment.customerRef} · {payment.subscriptionPlan} · {formatClock(payment.createdAt)}
            </p>
          </div>
          <div className="flex flex-col items-end gap-2">
            <PipelineTrack payment={payment} />
            {payment.stage === 'awaiting_approval' && (
              <div className="flex gap-2">
                <Button size="sm" variant="success" icon={Check} onClick={() => dispatch({ type: 'APPROVE_PAYMENT', id: payment.id })}>
                  Approve action
                </Button>
                <Button size="sm" variant="danger" icon={X} onClick={() => dispatch({ type: 'REJECT_PAYMENT', id: payment.id })}>
                  Reject
                </Button>
              </div>
            )}
          </div>
        </div>

        <div className="mt-5 grid grid-cols-2 gap-4 border-t border-[var(--color-line-soft)] pt-4 sm:grid-cols-4">
          <ContextField label="Payment method" value={payment.method} />
          <ContextField label="Processor" value={payment.processor} />
          <ContextField label="Attempt history" value={`${payment.attempts} prior attempt${payment.attempts > 1 ? 's' : ''}`} />
          <ContextField label="Customer tenure" value={`${payment.customerTenureMonths} months`} />
        </div>
      </Card>

      {payment.stage === 'resolved' && payment.outcome && !payment.outcome.rejected && (
        <Card className={`p-5 ${payment.outcome.recovered ? 'border-[var(--color-success-600)]/30 bg-[var(--color-success-100)]/40' : 'border-[var(--color-danger-600)]/25 bg-[var(--color-danger-100)]/30'}`}>
          <div className="flex items-start gap-3">
            {payment.outcome.recovered ? (
              <CircleCheck className="mt-0.5 shrink-0 text-[var(--color-success-700)]" size={20} />
            ) : (
              <CircleAlert className="mt-0.5 shrink-0 text-[var(--color-danger-700)]" size={20} />
            )}
            <div>
              <p className="text-[14.5px] font-semibold text-[var(--color-ink)]">
                {payment.outcome.recovered ? 'Payment recovered' : 'Payment not recovered'}
              </p>
              <div className="mt-1.5 flex flex-wrap gap-x-5 gap-y-1 text-[13px] text-[var(--color-ink-soft)]">
                <span>Strategy: {STRATEGIES[payment.decision.strategyKey].label}</span>
                <span>Time to outcome: {formatRelative(payment.outcome.recoveryTimeMinutes * 60)}</span>
                <span>Net value: {formatINR(payment.outcome.actualNet)}</span>
              </div>
            </div>
          </div>
        </Card>
      )}

      {payment.stage === 'resolved' && payment.outcome?.rejected && (
        <Card className="border-[var(--color-line)] bg-[var(--color-surface)] p-5">
          <p className="text-[14px] font-medium text-[var(--color-ink)]">Rejected by operator</p>
          <p className="mt-1 text-[13px] text-[var(--color-ink-faint)]">No automated action was taken on this payment.</p>
        </Card>
      )}

      <Card>
        <CardHeader title="Why did this payment fail?" />
        <div className="px-5 py-4">
          <div className="flex items-center gap-2">
            <Badge variant="neutral">{info.label}</Badge>
          </div>
          <p className="mt-2.5 text-[13.5px] leading-relaxed text-[var(--color-ink-soft)]">{info.description}</p>
        </div>
      </Card>

      <Card>
        <CardHeader title="Recovery decision" subtitle="Investigation → Prediction → Economics → Risk → Strategy → Execution → Verification" />
        <AgentTraceList trace={payment.trace} />
      </Card>
    </div>
  );
}
