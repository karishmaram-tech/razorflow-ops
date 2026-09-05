import { ShieldCheck, Check, X } from 'lucide-react';
import { Card, CardHeader } from '../components/ui/Card';
import Toggle from '../components/ui/Toggle';
import Button from '../components/ui/Button';
import EmptyState from '../components/ui/EmptyState';
import { formatINR } from '../lib/format';
import { useRecoveryState, useRecoveryDispatch } from '../lib/RecoveryContext';

function NumberField({ label, description, value, onChange, prefix, min = 0, max, step = 1 }) {
  return (
    <div className="flex flex-col gap-2 py-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="max-w-sm">
        <p className="text-[13.5px] font-medium text-[var(--color-ink)]">{label}</p>
        <p className="mt-0.5 text-[12.5px] text-[var(--color-ink-faint)]">{description}</p>
      </div>
      <div className="flex items-center gap-1.5 rounded-[var(--radius-sm)] border border-[var(--color-line)] bg-[var(--color-surface)] px-2.5 py-1.5">
        {prefix && <span className="text-[13px] text-[var(--color-ink-faint)]">{prefix}</span>}
        <input
          type="number"
          value={value}
          min={min}
          max={max}
          step={step}
          onChange={(e) => onChange(Number(e.target.value))}
          className="w-24 bg-transparent text-right font-mono text-[13.5px] text-[var(--color-ink)] focus:outline-none"
        />
      </div>
    </div>
  );
}

export default function ControlCenter() {
  const { controls, payments } = useRecoveryState();
  const dispatch = useRecoveryDispatch();
  const pending = payments.filter((p) => p.stage === 'awaiting_approval');

  function update(patch) {
    dispatch({ type: 'UPDATE_CONTROLS', payload: patch });
  }

  return (
    <div className="mx-auto flex max-w-[900px] flex-col gap-5 px-4 py-6 sm:px-6 lg:px-8">
      <div className="flex items-start gap-3">
        <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[var(--color-navy-800)] text-white">
          <ShieldCheck size={17} />
        </div>
        <div>
          <h1 className="text-[20px] font-semibold text-[var(--color-ink)]">Control center</h1>
          <p className="mt-1 text-[13.5px] text-[var(--color-ink-faint)]">
            Autonomous does not mean uncontrolled. Every limit below is enforced before RecoveryFlow takes action.
          </p>
        </div>
      </div>

      <Card>
        <CardHeader
          title="Automatic execution"
          subtitle="When off, every recovery action waits for your approval"
          action={<Toggle checked={controls.autoExecute} onChange={(v) => update({ autoExecute: v })} label="Automatic execution" />}
        />
      </Card>

      <Card>
        <CardHeader title="Autonomy limits" subtitle="Actions outside these bounds are routed to Pending approvals" />
        <div className="divide-y divide-[var(--color-line-soft)] px-5">
          <NumberField
            label="Maximum retry attempts"
            description="Stop retrying a payment automatically after this many attempts."
            value={controls.maxRetryAttempts}
            onChange={(v) => update({ maxRetryAttempts: v })}
            min={1}
            max={6}
          />
          <NumberField
            label="Maximum intervention cost"
            description="The most RecoveryFlow can spend on a single recovery action."
            value={controls.maxInterventionCost}
            onChange={(v) => update({ maxInterventionCost: v })}
            prefix="₹"
            min={0}
            step={5}
          />
          <NumberField
            label="Customer contact limit"
            description="Maximum number of customer-facing messages per payment."
            value={controls.customerContactLimit}
            onChange={(v) => update({ customerContactLimit: v })}
            min={0}
            max={5}
          />
          <NumberField
            label="Confidence threshold"
            description="Decisions below this confidence require human approval."
            value={controls.confidenceThreshold}
            onChange={(v) => update({ confidenceThreshold: v })}
            prefix="%"
            min={0}
            max={100}
          />
          <NumberField
            label="High-value payment threshold"
            description="Payments above this amount are treated with additional caution."
            value={controls.highValueThreshold}
            onChange={(v) => update({ highValueThreshold: v })}
            prefix="₹"
            min={0}
            step={1000}
          />
          <NumberField
            label="Human approval threshold"
            description="Payments above this amount always require manual approval."
            value={controls.humanApprovalThreshold}
            onChange={(v) => update({ humanApprovalThreshold: v })}
            prefix="₹"
            min={0}
            step={1000}
          />
        </div>
      </Card>

      <Card>
        <CardHeader title="Pending approvals" subtitle={`${pending.length} payment${pending.length === 1 ? '' : 's'} waiting on you`} />
        {pending.length === 0 ? (
          <EmptyState icon={ShieldCheck} title="Nothing waiting on you" description="Payments that exceed a threshold above will appear here." />
        ) : (
          <ul className="divide-y divide-[var(--color-line-soft)]">
            {pending.map((p) => (
              <li key={p.id} className="flex items-center justify-between gap-3 px-5 py-3.5">
                <div>
                  <p className="font-mono text-[13.5px] font-medium text-[var(--color-ink)]">{p.id}</p>
                  <p className="text-[12.5px] text-[var(--color-ink-faint)]">
                    {formatINR(p.amount)} · {p.decision ? p.decision.finding : 'Awaiting decision'}
                  </p>
                </div>
                <div className="flex gap-1.5">
                  <Button size="sm" variant="success" icon={Check} onClick={() => dispatch({ type: 'APPROVE_PAYMENT', id: p.id })}>Approve</Button>
                  <Button size="sm" variant="danger" icon={X} onClick={() => dispatch({ type: 'REJECT_PAYMENT', id: p.id })}>Reject</Button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
