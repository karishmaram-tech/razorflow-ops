import { Play, Sparkles, X } from 'lucide-react';
import { Card } from '../ui/Card';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import { formatINR, formatPercent } from '../../lib/format';
import { useRecoveryState, useRecoveryDispatch } from '../../lib/RecoveryContext';

export default function RecoverySimulation() {
  const { demoMode, demoResult, payments } = useRecoveryState();
  const dispatch = useRecoveryDispatch();
  const activeDemoCount = demoMode ? payments.filter((p) => p.stage !== 'resolved').length : 0;

  return (
    <Card className="overflow-hidden border-[var(--color-navy-800)]/15 bg-gradient-to-br from-[var(--color-navy-900)] to-[var(--color-navy-800)] text-white">
      <div className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="max-w-md">
          <div className="flex items-center gap-2 text-[12px] font-medium text-white/60">
            <Sparkles size={14} />
            Recovery simulation
          </div>
          <h3 className="mt-1 text-[17px] font-semibold">Watch RecoveryFlow recover revenue</h3>
          <p className="mt-1 text-[13px] leading-relaxed text-white/60">
            Runs 14 simulated failed payments through the full agent pipeline and reports what was recovered.
          </p>
        </div>
        <Button
          variant="secondary"
          size="lg"
          icon={Play}
          className="border-white/20 bg-white/10 text-white hover:bg-white/20 shrink-0"
          onClick={() => dispatch({ type: 'RUN_DEMO' })}
          disabled={demoMode}
        >
          {demoMode ? `Running · ${activeDemoCount} in flight` : 'Run recovery simulation'}
        </Button>
      </div>

      {demoResult && (
        <div className="border-t border-white/10 bg-black/10 px-5 py-5 tick-in">
          <div className="flex items-center justify-between">
            <p className="text-[12.5px] font-medium uppercase tracking-wide text-white/50">Simulation result</p>
            <button
              onClick={() => dispatch({ type: 'DISMISS_DEMO_RESULT' })}
              aria-label="Dismiss result"
              className="text-white/40 hover:text-white/80"
            >
              <X size={15} />
            </button>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
            <div>
              <p className="text-[11px] text-white/50">Recovered revenue</p>
              <p className="font-mono text-[19px] font-semibold">{formatINR(demoResult.recoveredAmount)}</p>
            </div>
            <div>
              <p className="text-[11px] text-white/50">Recovery rate</p>
              <p className="font-mono text-[19px] font-semibold">{formatPercent(demoResult.recoveryRate)}</p>
            </div>
            <div>
              <p className="text-[11px] text-white/50">Net recovery</p>
              <p className="font-mono text-[19px] font-semibold">{formatINR(demoResult.netRecovery)}</p>
            </div>
            <div>
              <p className="text-[11px] text-white/50">Escalated</p>
              <p className="font-mono text-[19px] font-semibold">{demoResult.escalated}</p>
            </div>
          </div>
          <div className="mt-4 flex items-start gap-2 rounded-[var(--radius-sm)] border border-white/10 bg-white/5 px-3.5 py-3">
            <Badge variant="navy" className="bg-white/15 text-white">Learned</Badge>
            <p className="text-[12.5px] leading-relaxed text-white/75">
              {demoResult.delayedRate > demoResult.immediateRate
                ? `Delayed retries outperformed immediate retries by ${(demoResult.delayedRate - demoResult.immediateRate).toFixed(1)} points in this run — the model will weight timing more heavily for similar failures.`
                : `Immediate retries outperformed delayed retries by ${(demoResult.immediateRate - demoResult.delayedRate).toFixed(1)} points in this run for the failures encountered.`}
            </p>
          </div>
        </div>
      )}
    </Card>
  );
}
