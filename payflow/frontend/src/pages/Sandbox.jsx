import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  FlaskConical, Play, Zap, RotateCcw, Pause, PlayCircle, X, ArrowRight,
} from 'lucide-react';
import { Card, CardHeader } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import Modal from '../components/ui/Modal';
import { SCENARIOS } from '../lib/domain';
import { formatINR, formatPercent } from '../lib/format';
import { useRecoveryState, useRecoveryDispatch } from '../lib/RecoveryContext';

export default function Sandbox() {
  const { demoMode, demoResult, payments, isRunning } = useRecoveryState();
  const dispatch = useRecoveryDispatch();
  const [scenario, setScenario] = useState('MIXED');
  const [confirmReset, setConfirmReset] = useState(false);

  const activeDemoCount = demoMode ? payments.filter((p) => p.stage !== 'resolved').length : 0;
  const sandboxPayments = payments.filter((p) => p.origin === 'sandbox');

  return (
    <div className="mx-auto flex max-w-[1100px] flex-col gap-5 px-4 py-6 sm:px-6 lg:px-8">
      <div className="flex items-start gap-3">
        <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[var(--color-navy-800)] text-white">
          <FlaskConical size={17} />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-[20px] font-semibold text-[var(--color-ink)]">Sandbox</h1>
            <Badge variant="warning">Synthetic data</Badge>
          </div>
          <p className="mt-1 max-w-xl text-[13.5px] text-[var(--color-ink-faint)]">
            Generate synthetic failed payments and watch them move through RecoveryFlow's real seven-agent
            pipeline. Nothing here touches a production processor — but the decision engine, controls, and
            audit log are the same ones running the live Command Center.
          </p>
        </div>
      </div>

      <Card>
        <CardHeader title="Generate synthetic events" subtitle="Choose a failure scenario to test how RecoveryFlow responds" />
        <div className="flex flex-col gap-4 px-5 py-4">
          <div className="flex flex-col gap-1.5">
            <label htmlFor="scenario" className="text-[12.5px] font-medium text-[var(--color-ink-soft)]">Scenario</label>
            <select
              id="scenario"
              value={scenario}
              onChange={(e) => setScenario(e.target.value)}
              className="w-full max-w-sm rounded-[var(--radius-sm)] border border-[var(--color-line)] bg-[var(--color-surface)] px-3 py-2 text-[13.5px] text-[var(--color-ink)] focus:outline-none"
            >
              {SCENARIOS.map((s) => (
                <option key={s.key} value={s.key}>{s.label}</option>
              ))}
            </select>
          </div>

          <div className="flex flex-wrap gap-2">
            <Button
              variant="secondary"
              icon={Zap}
              onClick={() => dispatch({ type: 'GENERATE_PAYMENT', scenario })}
            >
              Generate failed payment
            </Button>
            <Button
              variant="secondary"
              icon={Zap}
              onClick={() => dispatch({ type: 'GENERATE_BATCH', scenario, count: 10 })}
            >
              Generate batch of 10
            </Button>
            <Button
              variant="primary"
              icon={Play}
              onClick={() => dispatch({ type: 'START_RECOVERY', scenario, count: 14 })}
              disabled={demoMode}
            >
              {demoMode ? `Processing · ${activeDemoCount} in flight` : 'Start recovery'}
            </Button>
          </div>

          <div className="flex flex-wrap items-center gap-2 border-t border-[var(--color-line-soft)] pt-4">
            <Button
              variant="secondary"
              size="sm"
              icon={isRunning ? Pause : PlayCircle}
              onClick={() => dispatch({ type: 'TOGGLE_RUNNING' })}
            >
              {isRunning ? 'Pause automation' : 'Resume automation'}
            </Button>
            <Button variant="ghost" size="sm" icon={RotateCcw} onClick={() => setConfirmReset(true)}>
              Reset simulation
            </Button>
            <span className="text-[12.5px] text-[var(--color-ink-faint)]">
              {sandboxPayments.length} sandbox-generated payment{sandboxPayments.length === 1 ? '' : 's'} in the current pipeline
            </span>
          </div>
        </div>
      </Card>

      {demoResult && (
        <Card className="overflow-hidden">
          <CardHeader
            title="Simulation result"
            subtitle="Results from the last batch — not a real-world performance claim"
            action={(
              <button
                onClick={() => dispatch({ type: 'DISMISS_DEMO_RESULT' })}
                aria-label="Dismiss result"
                className="text-[var(--color-ink-faint)] hover:text-[var(--color-ink)]"
              >
                <X size={16} />
              </button>
            )}
          />
          <div className="grid grid-cols-2 gap-4 px-5 py-4 sm:grid-cols-4">
            <div>
              <p className="text-[11px] text-[var(--color-ink-faint)]">Recovered revenue</p>
              <p className="font-mono text-[19px] font-semibold text-[var(--color-ink)]">{formatINR(demoResult.recoveredAmount)}</p>
            </div>
            <div>
              <p className="text-[11px] text-[var(--color-ink-faint)]">Recovery rate</p>
              <p className="font-mono text-[19px] font-semibold text-[var(--color-ink)]">{formatPercent(demoResult.recoveryRate)}</p>
            </div>
            <div>
              <p className="text-[11px] text-[var(--color-ink-faint)]">Net recovery</p>
              <p className="font-mono text-[19px] font-semibold text-[var(--color-ink)]">{formatINR(demoResult.netRecovery)}</p>
            </div>
            <div>
              <p className="text-[11px] text-[var(--color-ink-faint)]">Escalated</p>
              <p className="font-mono text-[19px] font-semibold text-[var(--color-ink)]">{demoResult.escalated}</p>
            </div>
          </div>
          <div className="mx-5 mb-5 flex items-start gap-2 rounded-[var(--radius-sm)] border border-[var(--color-line)] bg-[var(--color-surface)] px-3.5 py-3">
            <Badge variant="navy">Simulation result</Badge>
            <p className="text-[12.5px] leading-relaxed text-[var(--color-ink-soft)]">
              {demoResult.delayedRate > demoResult.immediateRate
                ? `In this run, delayed retries recovered ${(demoResult.delayedRate - demoResult.immediateRate).toFixed(1)} points more often than immediate retries for the failures encountered.`
                : `In this run, immediate retries recovered ${(demoResult.immediateRate - demoResult.delayedRate).toFixed(1)} points more often than delayed retries for the failures encountered.`}
            </p>
          </div>
        </Card>
      )}

      <Card className="flex flex-wrap items-center justify-between gap-3 px-5 py-4">
        <p className="text-[13px] text-[var(--color-ink-soft)]">
          Everything generated here is visible in the live Command Center and Audit Log, using the same limits configured in Control Center.
        </p>
        <Link to="/app" className="flex shrink-0 items-center gap-1.5 text-[13px] font-medium text-[var(--color-navy-700)] hover:text-[var(--color-navy-800)]">
          Open Command Center
          <ArrowRight size={14} />
        </Link>
      </Card>

      <Modal
        open={confirmReset}
        onClose={() => setConfirmReset(false)}
        title="Reset the simulation?"
        footer={(
          <>
            <Button variant="secondary" onClick={() => setConfirmReset(false)}>Cancel</Button>
            <Button
              variant="danger"
              onClick={() => { dispatch({ type: 'RESET_SIMULATION' }); setConfirmReset(false); }}
            >
              Reset everything
            </Button>
          </>
        )}
      >
        <p className="text-[13.5px] text-[var(--color-ink-soft)]">
          This clears every payment, activity entry, and audit record in the current session, including
          anything generated by the live Command Center. Your Control Center limits are kept. This cannot be undone.
        </p>
      </Modal>
    </div>
  );
}
