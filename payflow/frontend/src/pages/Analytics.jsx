import { useMemo } from 'react';
import {
  ResponsiveContainer, LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RTooltip,
} from 'recharts';
import { Card, CardHeader } from '../components/ui/Card';
import EmptyState from '../components/ui/EmptyState';
import { LineChart as LineChartIcon } from 'lucide-react';
import { FAILURE_REASONS, PAYMENT_METHODS, STAGE_LABELS } from '../lib/domain';
import { formatINR, formatPercent } from '../lib/format';
import { useRecoveryState } from '../lib/RecoveryContext';

const AXIS_STYLE = { fontSize: 11, fill: 'var(--color-ink-faint)' };

function ChartTooltip({ active, payload, label, formatter }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-[var(--radius-sm)] border border-[var(--color-line)] bg-white px-3 py-2 text-[12px] shadow-[var(--shadow-raised)]">
      <p className="font-medium text-[var(--color-ink)]">{label}</p>
      {payload.map((p, i) => (
        <p key={i} className="text-[var(--color-ink-soft)]">{formatter ? formatter(p.value) : p.value}</p>
      ))}
    </div>
  );
}

export default function Analytics() {
  const { payments } = useRecoveryState();
  const resolved = payments.filter((p) => p.stage === 'resolved' && p.outcome && !p.outcome.rejected);

  const overTime = useMemo(() => {
    const sorted = [...resolved].sort((a, b) => a.resolvedAt - b.resolvedAt);
    let cumulative = 0;
    return sorted.map((p, i) => {
      if (p.outcome.recovered) cumulative += p.amount;
      return { name: `#${i + 1}`, recovered: cumulative };
    });
  }, [resolved]);

  const byFailureType = useMemo(() => Object.entries(FAILURE_REASONS).map(([key, info]) => {
    const set = resolved.filter((p) => p.failureReason === key);
    const recovered = set.filter((p) => p.outcome.recovered);
    return {
      name: info.label,
      rate: set.length ? (recovered.length / set.length) * 100 : 0,
      count: set.length,
    };
  }).filter((d) => d.count > 0), [resolved]);

  const byMethod = useMemo(() => PAYMENT_METHODS.map((method) => {
    const set = resolved.filter((p) => p.method === method);
    const recovered = set.filter((p) => p.outcome.recovered);
    return {
      name: method,
      rate: set.length ? (recovered.length / set.length) * 100 : 0,
      count: set.length,
    };
  }).filter((d) => d.count > 0), [resolved]);

  const funnel = useMemo(() => {
    const order = ['queued', 'investigating', 'predicting', 'evaluating', 'awaiting_approval', 'executing', 'verifying', 'resolved'];
    return order.map((stage) => ({
      name: STAGE_LABELS[stage],
      count: payments.filter((p) => p.stage === stage).length,
    })).filter((d) => d.count > 0);
  }, [payments]);

  if (resolved.length === 0) {
    return (
      <div className="mx-auto max-w-[1100px] px-4 py-6 sm:px-6 lg:px-8">
        <h1 className="text-[20px] font-semibold text-[var(--color-ink)]">Analytics</h1>
        <Card className="mt-4">
          <EmptyState
            icon={LineChartIcon}
            title="No resolved payments yet"
            description="Charts will populate once RecoveryFlow has resolved at least one payment. Try running the recovery simulation from the command center."
          />
        </Card>
      </div>
    );
  }

  return (
    <div className="mx-auto flex max-w-[1100px] flex-col gap-5 px-4 py-6 sm:px-6 lg:px-8">
      <div>
        <h1 className="text-[20px] font-semibold text-[var(--color-ink)]">Analytics</h1>
        <p className="mt-1 text-[13.5px] text-[var(--color-ink-faint)]">Based on {resolved.length} resolved payments in this session.</p>
      </div>

      <Card>
        <CardHeader title="Revenue recovered over time" subtitle="Cumulative, in resolution order" />
        <div className="h-64 px-3 py-4">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={overTime} margin={{ top: 5, right: 16, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="var(--color-line-soft)" vertical={false} />
              <XAxis dataKey="name" tick={AXIS_STYLE} axisLine={{ stroke: 'var(--color-line)' }} tickLine={false} />
              <YAxis tick={AXIS_STYLE} axisLine={false} tickLine={false} tickFormatter={(v) => formatINR(v, { compact: true })} width={64} />
              <RTooltip content={<ChartTooltip formatter={(v) => formatINR(v)} />} />
              <Line type="monotone" dataKey="recovered" stroke="var(--color-navy-700)" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader title="Recovery rate by failure type" />
          <div className="h-64 px-3 py-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={byFailureType} margin={{ top: 5, right: 16, left: 0, bottom: 0 }}>
                <CartesianGrid stroke="var(--color-line-soft)" vertical={false} />
                <XAxis dataKey="name" tick={{ ...AXIS_STYLE, fontSize: 10 }} axisLine={{ stroke: 'var(--color-line)' }} tickLine={false} interval={0} angle={-20} textAnchor="end" height={55} />
                <YAxis tick={AXIS_STYLE} axisLine={false} tickLine={false} tickFormatter={(v) => `${v}%`} width={36} />
                <RTooltip content={<ChartTooltip formatter={(v) => formatPercent(v)} />} />
                <Bar dataKey="rate" fill="var(--color-navy-600)" radius={[3, 3, 0, 0]} maxBarSize={36} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card>
          <CardHeader title="Recovery rate by payment method" />
          <div className="h-64 px-3 py-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={byMethod} margin={{ top: 5, right: 16, left: 0, bottom: 0 }}>
                <CartesianGrid stroke="var(--color-line-soft)" vertical={false} />
                <XAxis dataKey="name" tick={{ ...AXIS_STYLE, fontSize: 10 }} axisLine={{ stroke: 'var(--color-line)' }} tickLine={false} />
                <YAxis tick={AXIS_STYLE} axisLine={false} tickLine={false} tickFormatter={(v) => `${v}%`} width={36} />
                <RTooltip content={<ChartTooltip formatter={(v) => formatPercent(v)} />} />
                <Bar dataKey="rate" fill="var(--color-success-600)" radius={[3, 3, 0, 0]} maxBarSize={36} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      <Card>
        <CardHeader title="Recovery funnel" subtitle="Where every payment sits right now" />
        <div className="h-56 px-3 py-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={funnel} layout="vertical" margin={{ top: 5, right: 24, left: 8, bottom: 0 }}>
              <CartesianGrid stroke="var(--color-line-soft)" horizontal={false} />
              <XAxis type="number" tick={AXIS_STYLE} axisLine={false} tickLine={false} allowDecimals={false} />
              <YAxis type="category" dataKey="name" tick={AXIS_STYLE} axisLine={false} tickLine={false} width={110} />
              <RTooltip content={<ChartTooltip />} />
              <Bar dataKey="count" fill="var(--color-navy-500)" radius={[0, 3, 3, 0]} maxBarSize={18} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  );
}
