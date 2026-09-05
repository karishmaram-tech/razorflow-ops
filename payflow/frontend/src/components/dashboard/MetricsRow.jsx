import StatCard from '../ui/StatCard';
import { useMetrics } from '../../lib/RecoveryContext';

export default function MetricsRow() {
  const m = useMetrics();

  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-3 xl:grid-cols-6">
      <StatCard label="Revenue at risk" value={m.revenueAtRisk} helpText={`${m.activeCount} in pipeline`} />
      <StatCard label="Expected recovery" value={m.expectedRecovery} tone="neutral" helpText="Probability-weighted" />
      <StatCard label="Recovered revenue" value={m.recoveredRevenue} tone="success" helpText={`${m.recoveredCount} payments`} />
      <StatCard label="Recovery rate" value={m.recoveryRate} format="percent" tone={m.recoveryRate >= 60 ? 'success' : 'neutral'} helpText={`of ${m.resolvedCount} resolved`} />
      <StatCard label="Net recovery" value={m.netRecovery} tone={m.netRecovery >= 0 ? 'success' : 'danger'} helpText="After action cost" />
      <StatCard label="ROI" value={m.roi} format="multiplier" tone={m.roi >= 0 ? 'success' : 'danger'} helpText="Net recovered per ₹ spent" />
    </div>
  );
}
