import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AreaChart, Area, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid } from 'recharts';

/* ═══════════════════════════════════════════════════════════
   RECOVERYFLOW — Sequential AI Automation Dashboard
   Everything flows top-to-bottom, one section at a time.
   All amounts in Indian Rupees (₹).
   ═══════════════════════════════════════════════════════════ */

// ─── COLORS ───────────────────────────────────────────────
const C = {
  bg: '#09090b',
  card: '#18181b',
  cardHover: '#1e1e22',
  border: 'rgba(63, 63, 70, 0.5)',
  text: '#fafafa',
  textSec: '#a1a1aa',
  muted: '#52525b',
  primary: '#6366f1',
  emerald: '#10b981',
  amber: '#f59e0b',
  rose: '#f43f5e',
  cyan: '#06b6d4',
  violet: '#8b5cf6',
};

const AGENT_COLORS = {
  investigator: '#06b6d4',
  predictor: '#8b5cf6',
  risk: '#f43f5e',
  economics: '#10b981',
  strategy: '#6366f1',
  learning: '#f59e0b',
};
const AGENT_ICONS = { investigator: '🔍', predictor: '🧠', risk: '🛡️', economics: '💰', strategy: '🎯', learning: '📈' };
const AGENT_NAMES = { investigator: 'Investigator', predictor: 'Predictor', risk: 'Risk', economics: 'Economics', strategy: 'Strategy', learning: 'Learning' };

// ─── CHART DATA ───────────────────────────────────────────
const PERF_DATA = [
  { time: '12 AM', efficiency: 72 }, { time: '2 AM', efficiency: 74 }, { time: '4 AM', efficiency: 71 },
  { time: '6 AM', efficiency: 78 }, { time: '8 AM', efficiency: 82 }, { time: '10 AM', efficiency: 85 },
  { time: '12 PM', efficiency: 88 }, { time: '2 PM', efficiency: 86 }, { time: '4 PM', efficiency: 91 },
  { time: '6 PM', efficiency: 89 }, { time: '8 PM', efficiency: 92 }, { time: '10 PM', efficiency: 94 },
];

// ─── SCENARIOS ────────────────────────────────────────────
const SCENARIOS = [
  {
    name: 'High-Value Recovery',
    desc: '3-year subscriber, card expired',
    customer: { name: 'Sarah Kumar', tenure: 36, ltv: 295812, monthly: 8217 },
    failure: 'card_expired', amount: 8217,
    agents: {
      investigator: { status: 'done', confidence: 91, text: 'Card expired — temporary issue. 3-year tenure, 36 successful payments, zero chargebacks, 2 backup methods.', time: '0.8s' },
      predictor: { status: 'done', confidence: 82, text: 'SMS + Payment Link: 82% success probability. Best strategy for high-LTV stable segment.', time: '1.2s' },
      risk: { status: 'done', confidence: 95, text: 'Clean history. Chargeback risk: 1.2%. Fraud: 0.1%. Safe to proceed.', time: '0.6s' },
      economics: { status: 'done', confidence: 90, text: 'Expected Net Recovery: ₹84,992 via SMS+Link. ROI: 12,794x. Recommendation: EXECUTE.', time: '0.4s' },
      strategy: { status: 'done', confidence: 82, text: 'SMS + Payment Link selected. Balances 82% success with scalability. All agents agree.', time: '0.3s' },
      learning: { status: 'wait', confidence: 0, text: 'Awaiting outcome to update model.', time: '—' },
    },
    outcome: { result: 'success', amount: 8217, cost: 6.64, time: '45s', enr: 84992 },
  },
  {
    name: 'Risk Conflict',
    desc: 'Chargeback history, agents disagree',
    customer: { name: 'James Wilson', tenure: 18, ltv: 179280, monthly: 9960 },
    failure: 'insufficient_funds', amount: 9960,
    agents: {
      investigator: { status: 'done', confidence: 85, text: 'Insufficient funds — likely temporary. 18-month customer but 3 prior chargebacks elevate concern.', time: '0.9s' },
      predictor: { status: 'done', confidence: 74, text: 'Support call: 85%. SMS: 72%. Email: 42%. Moderate confidence across strategies.', time: '1.1s' },
      risk: { status: 'done', confidence: 68, text: 'Chargeback propensity: 6.8%. Elevated risk. Recommend conservative strategy.', time: '0.7s' },
      economics: { status: 'done', confidence: 88, text: 'Expected Net Recovery: ₹69,056 via SMS. Email: ₹41,583. Risk-adjusted: email is safer.', time: '0.5s' },
      strategy: { status: 'done', confidence: 74, text: 'Email only selected. Risk agent flagged CAUTION. Conflict resolved: risk takes priority over economics.', time: '0.4s' },
      learning: { status: 'wait', confidence: 0, text: 'Awaiting outcome.', time: '—' },
    },
    outcome: { result: 'success', amount: 9960, cost: 0.83, time: '2.3h', enr: 69056 },
  },
  {
    name: 'Skip — Not Economical',
    desc: 'Low-value, high-risk, system says NO',
    customer: { name: 'Alex Lee', tenure: 2, ltv: 3984, monthly: 830 },
    failure: 'fraud_blocked', amount: 830,
    agents: {
      investigator: { status: 'done', confidence: 88, text: 'Fraud blocked. Only 2-month tenure, low LTV, 1 prior chargeback. Not recoverable.', time: '0.5s' },
      predictor: { status: 'done', confidence: 65, text: 'All strategies below 30% probability. Best: support call at 30%. Low confidence.', time: '0.9s' },
      risk: { status: 'done', confidence: 72, text: 'Fraud signal active. Chargeback: 8.2%. Total risk: 5.7%. CAUTION.', time: '0.6s' },
      economics: { status: 'done', confidence: 90, text: 'Negative ENR for most strategies. Email: ₹249 (barely positive). Recommendation: SKIP.', time: '0.3s' },
      strategy: { status: 'done', confidence: 88, text: 'SKIP. Recoverability < 25%. Negative EV. High fraud risk. Accepting ₹830 loss.', time: '0.2s' },
      learning: { status: 'wait', confidence: 0, text: 'No recovery attempted.', time: '—' },
    },
    outcome: { result: 'skipped', amount: 0, cost: 0, time: 'N/A', enr: 0 },
  },
];

// ─── HELPERS ──────────────────────────────────────────────
function fmtINR(n) {
  if (n >= 10000000) return `₹${(n / 10000000).toFixed(1)}Cr`;
  if (n >= 100000) return `₹${(n / 100000).toFixed(1)}L`;
  if (n >= 1000) return `₹${n.toLocaleString('en-IN')}`;
  return `₹${n}`;
}

function ChartTip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="px-3 py-2 rounded-xl text-xs" style={{ background: C.card, border: `1px solid ${C.border}` }}>
      <p className="font-semibold mb-1" style={{ color: C.text }}>{label}</p>
      <p style={{ color: C.primary }}>Efficiency: {payload[0].value}%</p>
    </div>
  );
}

// ─── SECTION COMPONENT ────────────────────────────────────
function Section({ title, subtitle, children, delay = 0 }) {
  return (
    <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.5, ease: [0.23, 1, 0.32, 1] }}
      className="mb-6">
      {title && (
        <div className="mb-4">
          <h2 className="text-base font-bold" style={{ color: C.text }}>{title}</h2>
          {subtitle && <p className="text-xs mt-0.5" style={{ color: C.muted }}>{subtitle}</p>}
        </div>
      )}
      {children}
    </motion.div>
  );
}

// ══════════════════════════════════════════════════════════
// MAIN DASHBOARD
// ══════════════════════════════════════════════════════════
export default function RecoveryDashboard() {
  const [scenarioIdx, setScenarioIdx] = useState(0);
  const [activeAgent, setActiveAgent] = useState(null);
  const [steps, setSteps] = useState({});
  const [running, setRunning] = useState(false);
  const [showOutcome, setShowOutcome] = useState(false);

  const sc = SCENARIOS[scenarioIdx];

  const runDemo = useCallback(() => {
    setSteps({});
    setActiveAgent(null);
    setShowOutcome(false);
    setRunning(true);

    const order = ['investigator', 'predictor', 'risk', 'economics', 'strategy', 'learning'];
    let i = 0;
    const iv = setInterval(() => {
      if (i < order.length) {
        const a = order[i];
        setSteps(prev => ({ ...prev, [a]: sc.agents[a] }));
        setActiveAgent(a);
        i++;
      } else {
        clearInterval(iv);
        setShowOutcome(true);
        setRunning(false);
      }
    }, 700);
  }, [scenarioIdx, sc]);

  return (
    <div style={{ background: C.bg, minHeight: '100vh', fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif", color: C.text }}>
      <div className="max-w-[720px] mx-auto px-4 py-8">

        {/* ── 1. HEADER ──────────────────────────────────── */}
        <Section delay={0}>
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ background: `linear-gradient(135deg, ${C.primary}, ${C.violet})`, boxShadow: `0 4px 16px ${C.primary}30` }}>
              <span className="text-white font-bold text-lg">R</span>
            </div>
            <div>
              <h1 className="text-xl font-bold" style={{ color: C.text }}>RecoveryFlow</h1>
              <p className="text-xs" style={{ color: C.muted }}>Autonomous AI Revenue Recovery</p>
            </div>
            <div className="ml-auto flex items-center gap-2 px-3 py-1.5 rounded-full"
              style={{ background: `${C.emerald}10`, border: `1px solid ${C.emerald}20` }}>
              <div className="w-1.5 h-1.5 rounded-full" style={{ background: C.emerald, animation: 'pulse 2s infinite' }} />
              <span className="text-[11px] font-medium" style={{ color: C.emerald }}>6 Agents Online</span>
            </div>
          </div>
        </Section>

        {/* ── 2. WHAT IS RECOVERYFLOW ─────────────────────── */}
        <Section title="What is RecoveryFlow?" subtitle="Intelligent multi-agent system that recovers failed recurring payments" delay={0.1}>
          <div className="p-5 rounded-2xl" style={{ background: C.card, border: `1px solid ${C.border}` }}>
            <p className="text-sm leading-relaxed mb-4" style={{ color: C.textSec }}>
              When a subscription payment fails, most merchants just retry blindly — recovering only <span style={{ color: C.rose }}>30-40%</span> of revenue.
              RecoveryFlow uses <span style={{ color: C.primary }}>6 specialized AI agents</span> that investigate, predict, assess risk, calculate economics, negotiate strategy, and learn from outcomes.
            </p>
            <div className="grid grid-cols-3 gap-3">
              {[
                { label: 'Without Recovery', val: '5%', color: C.rose },
                { label: 'Naive Retry', val: '38%', color: C.amber },
                { label: 'RecoveryFlow', val: '72%', color: C.emerald },
              ].map(s => (
                <div key={s.label} className="p-3 rounded-xl text-center" style={{ background: `${s.color}10`, border: `1px solid ${s.color}20` }}>
                  <p className="text-xl font-bold" style={{ color: s.color }}>{s.val}</p>
                  <p className="text-[10px] mt-1" style={{ color: C.muted }}>{s.label}</p>
                </div>
              ))}
            </div>
          </div>
        </Section>

        {/* ── 3. KEY METRICS ─────────────────────────────── */}
        <Section title="Key Metrics" subtitle="Monthly performance across all merchants" delay={0.15}>
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: 'Revenue Recovered', val: '₹7.1Cr', sub: '+₹6.4Cr vs baseline', color: C.emerald, icon: '💰' },
              { label: 'Recovery Rate', val: '72%', sub: '+67% vs naive retry', color: C.primary, icon: '📊' },
              { label: 'Intervention Cost', val: '₹6,640', sub: '-97% vs manual support', color: C.amber, icon: '⚡' },
              { label: 'ROI', val: '9,646x', sub: 'Return on every ₹1 spent', color: C.violet, icon: '🚀' },
            ].map((m, i) => (
              <motion.div key={m.label}
                initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 + i * 0.05, duration: 0.4 }}
                className="p-4 rounded-2xl"
                style={{ background: C.card, border: `1px solid ${C.border}` }}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-medium" style={{ color: C.muted }}>{m.label}</span>
                  <span className="text-sm">{m.icon}</span>
                </div>
                <p className="text-xl font-bold" style={{ color: C.text }}>{m.val}</p>
                <p className="text-[10px] mt-1" style={{ color: m.color }}>{m.sub}</p>
              </motion.div>
            ))}
          </div>
        </Section>

        {/* ── 4. AGENT EFFICIENCY CHART ───────────────────── */}
        <Section title="Agent Efficiency" subtitle="Recovery success rate over 24 hours" delay={0.25}>
          <div className="p-5 rounded-2xl" style={{ background: C.card, border: `1px solid ${C.border}` }}>
            <div className="h-[180px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={PERF_DATA}>
                  <defs>
                    <linearGradient id="effG" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={C.primary} stopOpacity={0.3} />
                      <stop offset="100%" stopColor={C.primary} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(63,63,70,0.3)" />
                  <XAxis dataKey="time" tick={{ fontSize: 9, fill: C.muted }} axisLine={false} tickLine={false} interval={1} />
                  <YAxis tick={{ fontSize: 9, fill: C.muted }} axisLine={false} tickLine={false} domain={[60, 100]} />
                  <Tooltip content={<ChartTip />} />
                  <Area type="monotone" dataKey="efficiency" stroke={C.primary} fill="url(#effG)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </Section>

        {/* ── 5. HOW IT WORKS — THE 6 AGENTS ──────────────── */}
        <Section title="How It Works" subtitle="6 specialized agents process every failed payment" delay={0.3}>
          <div className="space-y-2">
            {Object.keys(AGENT_COLORS).map((a, i) => (
              <motion.div key={a}
                initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.35 + i * 0.05 }}
                className="flex items-center gap-3 p-3 rounded-xl"
                style={{ background: C.card, border: `1px solid ${C.border}` }}>
                <div className="w-8 h-8 rounded-lg flex items-center justify-center text-sm flex-shrink-0"
                  style={{ background: `${AGENT_COLORS[a]}15` }}>
                  {AGENT_ICONS[a]}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold" style={{ color: C.text }}>{AGENT_NAMES[a]}</p>
                  <p className="text-[10px]" style={{ color: C.muted }}>
                    {a === 'investigator' && 'Classifies failure, scores recoverability'}
                    {a === 'predictor' && 'Models success probability per strategy'}
                    {a === 'risk' && 'Evaluates chargeback and fraud risk'}
                    {a === 'economics' && 'Calculates expected net recovery'}
                    {a === 'strategy' && 'Negotiates final action across agents'}
                    {a === 'learning' && 'Updates models from outcomes'}
                  </p>
                </div>
                <div className="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold"
                  style={{ background: `${AGENT_COLORS[a]}20`, color: AGENT_COLORS[a] }}>
                  {i + 1}
                </div>
              </motion.div>
            ))}
          </div>
        </Section>

        {/* ── 6. RUN A DEMO ───────────────────────────────── */}
        <Section title="Run a Demo" subtitle="Watch all 6 agents process a failed payment in real-time" delay={0.4}>
          <div className="p-5 rounded-2xl" style={{ background: C.card, border: `1px solid ${C.border}` }}>

            {/* Scenario picker */}
            <div className="flex gap-2 mb-4">
              {SCENARIOS.map((s, i) => (
                <button key={i} onClick={() => { setScenarioIdx(i); setSteps({}); setActiveAgent(null); setShowOutcome(false); }}
                  className="px-3 py-1.5 rounded-lg text-[11px] font-semibold transition-all"
                  style={{
                    background: i === scenarioIdx ? `${C.primary}20` : 'transparent',
                    color: i === scenarioIdx ? C.primary : C.muted,
                    border: `1px solid ${i === scenarioIdx ? `${C.primary}30` : C.border}`,
                  }}>
                  {s.name}
                </button>
              ))}
            </div>

            {/* Customer info */}
            <div className="flex gap-4 mb-4 p-3 rounded-xl" style={{ background: 'rgba(24,24,27,0.8)' }}>
              {[
                ['Customer', sc.customer.name],
                ['Tenure', `${sc.customer.tenure}mo`],
                ['LTV', fmtINR(sc.customer.ltv)],
                ['Failed', fmtINR(sc.amount)],
                ['Reason', sc.failure.replace(/_/g, ' ')],
              ].map(([k, v]) => (
                <div key={k} className="text-center">
                  <p className="text-[9px]" style={{ color: C.muted }}>{k}</p>
                  <p className="text-[11px] font-semibold" style={{ color: C.text }}>{v}</p>
                </div>
              ))}
            </div>

            {/* Run button */}
            <button onClick={runDemo} disabled={running}
              className="w-full py-3 rounded-xl text-sm font-bold transition-all duration-200 mb-4"
              style={{
                background: running ? `${C.primary}40` : `linear-gradient(135deg, ${C.primary}, ${C.violet})`,
                color: 'white', cursor: running ? 'wait' : 'pointer',
                boxShadow: running ? 'none' : `0 4px 16px ${C.primary}30`,
              }}>
              {running ? '⏳ Agents Processing...' : '▶ Run Recovery Demo'}
            </button>

            {/* Agent steps — sequential */}
            <div className="space-y-2">
              {Object.keys(AGENT_COLORS).map((a) => {
                const step = steps[a];
                const isActive = activeAgent === a;
                const isDone = step?.status === 'done';
                const isWait = step?.status === 'wait';
                const color = AGENT_COLORS[a];

                return (
                  <motion.div key={a}
                    initial={false}
                    animate={{
                      borderColor: isActive ? `${color}40` : isDone ? `${color}20` : C.border,
                      background: isActive ? `${color}08` : C.card,
                    }}
                    className="p-3 rounded-xl border transition-all duration-300">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm">{AGENT_ICONS[a]}</span>
                      <span className="text-xs font-semibold" style={{ color: isDone || isActive ? color : C.muted }}>
                        {AGENT_NAMES[a]}
                      </span>
                      <span className="ml-auto text-[9px] px-2 py-0.5 rounded-full font-semibold"
                        style={{
                          background: isDone ? `${C.emerald}15` : isActive ? `${color}15` : `${C.muted}15`,
                          color: isDone ? C.emerald : isActive ? color : C.muted,
                        }}>
                        {isDone ? '✓ DONE' : isActive ? '● RUNNING' : isWait ? '○ WAITING' : '— QUEUED'}
                      </span>
                    </div>
                    {step && (
                      <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}
                        transition={{ duration: 0.3 }}>
                        {/* Confidence bar */}
                        {step.confidence > 0 && (
                          <div className="flex items-center gap-2 mb-1.5">
                            <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: `${color}15` }}>
                              <motion.div initial={{ width: 0 }} animate={{ width: `${step.confidence}%` }}
                                transition={{ duration: 0.6 }} className="h-full rounded-full" style={{ background: color }} />
                            </div>
                            <span className="text-[10px] font-bold" style={{ color }}>{step.confidence}%</span>
                          </div>
                        )}
                        <p className="text-[11px] leading-relaxed" style={{ color: C.textSec }}>{step.text}</p>
                        <p className="text-[9px] mt-1" style={{ color: C.muted }}>Time: {step.time}</p>
                      </motion.div>
                    )}
                  </motion.div>
                );
              })}
            </div>

            {/* Outcome */}
            {showOutcome && (
              <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                className="mt-4 p-4 rounded-xl" style={{
                  background: sc.outcome.result === 'success' ? `${C.emerald}10` : `${C.amber}10`,
                  border: `1px solid ${sc.outcome.result === 'success' ? `${C.emerald}25` : `${C.amber}25`}`,
                }}>
                <div className="flex items-center gap-3 mb-3">
                  <span className="text-2xl">{sc.outcome.result === 'success' ? '✅' : '🚫'}</span>
                  <div>
                    <p className="text-sm font-bold" style={{ color: sc.outcome.result === 'success' ? C.emerald : C.amber }}>
                      {sc.outcome.result === 'success' ? 'PAYMENT RECOVERED' : 'RECOVERY SKIPPED'}
                    </p>
                    {sc.outcome.amount > 0 && (
                      <p className="text-xs" style={{ color: C.textSec }}>
                        {fmtINR(sc.outcome.amount)} recovered in {sc.outcome.time} · Cost: {fmtINR(sc.outcome.cost)}
                      </p>
                    )}
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  <div className="p-2 rounded-lg" style={{ background: `${C.primary}10` }}>
                    <p className="text-[9px]" style={{ color: C.muted }}>Strategy</p>
                    <p className="text-[11px] font-bold" style={{ color: C.text }}>SMS + Link</p>
                  </div>
                  <div className="p-2 rounded-lg" style={{ background: `${C.emerald}10` }}>
                    <p className="text-[9px]" style={{ color: C.muted }}>Net Recovery</p>
                    <p className="text-[11px] font-bold" style={{ color: C.emerald }}>{fmtINR(sc.outcome.enr)}</p>
                  </div>
                  <div className="p-2 rounded-lg" style={{ background: `${C.violet}10` }}>
                    <p className="text-[9px]" style={{ color: C.muted }}>Confidence</p>
                    <p className="text-[11px] font-bold" style={{ color: C.violet }}>{sc.agents.strategy.confidence}%</p>
                  </div>
                </div>
              </motion.div>
            )}
          </div>
        </Section>

        {/* ── 7. SEGMENT PERFORMANCE ──────────────────────── */}
        <Section title="Performance by Customer Segment" subtitle="Recovery rates across different customer types" delay={0.5}>
          <div className="space-y-3">
            {[
              { label: 'High-LTV Stable', rate: 92, count: 48, color: C.emerald, desc: 'Long-tenure, consistent payments' },
              { label: 'Mid-LTV Transient', rate: 57, count: 88, color: C.primary, desc: 'Moderate value, some churn risk' },
              { label: 'Low-LTV At-Risk', rate: 30, count: 28, color: C.amber, desc: 'New or low-value, high uncertainty' },
            ].map((seg, i) => (
              <div key={seg.label} className="p-4 rounded-2xl" style={{ background: C.card, border: `1px solid ${C.border}` }}>
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <p className="text-xs font-semibold" style={{ color: C.text }}>{seg.label}</p>
                    <p className="text-[10px]" style={{ color: C.muted }}>{seg.desc}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold" style={{ color: seg.color }}>{seg.rate}%</p>
                    <p className="text-[10px]" style={{ color: C.muted }}>{seg.count} recovered</p>
                  </div>
                </div>
                <div className="h-2 rounded-full overflow-hidden" style={{ background: `${seg.color}15` }}>
                  <motion.div initial={{ width: 0 }} animate={{ width: `${seg.rate}%` }}
                    transition={{ delay: 0.6 + i * 0.1, duration: 0.8, ease: [0.23, 1, 0.32, 1] }}
                    className="h-full rounded-full" style={{ background: seg.color }} />
                </div>
              </div>
            ))}
          </div>
        </Section>

        {/* ── 8. RISK MANAGED ─────────────────────────────── */}
        <Section title="Risk Managed" subtitle="Revenue protected by intelligent risk assessment" delay={0.55}>
          <div className="p-5 rounded-2xl" style={{ background: C.card, border: `1px solid ${C.border}` }}>
            {[
              { label: 'High chargeback risk', count: 12, rev: '₹11.9L', icon: '⚠️' },
              { label: 'Fraud signals detected', count: 8, rev: '₹7.9L', icon: '🛡️' },
              { label: 'New customer, low confidence', count: 15, rev: '₹14.9L', icon: '👤' },
              { label: 'Cost exceeded value', count: 21, rev: '₹10.4L', icon: '💸' },
            ].map((r, i) => (
              <div key={r.label} className="flex items-center gap-3 py-3"
                style={{ borderBottom: i < 3 ? `1px solid ${C.border}` : 'none' }}>
                <span className="text-sm">{r.icon}</span>
                <div className="flex-1">
                  <p className="text-xs font-medium" style={{ color: C.text }}>{r.label}</p>
                  <p className="text-[10px]" style={{ color: C.muted }}>{r.count} cases avoided</p>
                </div>
                <span className="text-xs font-semibold" style={{ color: C.amber }}>{r.rev}</span>
              </div>
            ))}
          </div>
        </Section>

        {/* ── 9. COMPARISON ───────────────────────────────── */}
        <Section title="RecoveryFlow vs Alternatives" subtitle="Why multi-agent AI beats every other approach" delay={0.6}>
          <div className="space-y-3">
            {[
              { label: 'No Intervention', rate: '5%', rev: '₹49.3L', cost: '₹0', net: '₹49.3L', color: C.rose, icon: '🚫' },
              { label: 'Fixed Retry Schedule', rate: '38%', rev: '₹3.75Cr', cost: '₹20,750', net: '₹2.96Cr', color: C.amber, icon: '🔄' },
              { label: 'Manual Support Team', rate: '70%', rev: '₹5.82Cr', cost: '₹4.15L', net: '₹5.41Cr', color: C.cyan, icon: '👨‍💼' },
              { label: 'RecoveryFlow AI', rate: '72%', rev: '₹7.10Cr', cost: '₹6,640', net: '₹6.89Cr', color: C.emerald, icon: '🤖' },
            ].map((col) => (
              <div key={col.label} className="p-4 rounded-2xl" style={{
                background: `${col.color}08`, border: `1px solid ${col.color}20`,
              }}>
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-sm">{col.icon}</span>
                  <p className="text-sm font-bold" style={{ color: col.color }}>{col.label}</p>
                </div>
                {[
                  ['Recovery Rate', col.rate],
                  ['Revenue', col.rev],
                  ['Cost', col.cost],
                  ['Net Recovery', col.net],
                ].map(([k, v]) => (
                  <div key={k} className="flex justify-between py-1.5" style={{ borderBottom: `1px solid ${col.color}10` }}>
                    <span className="text-[11px]" style={{ color: C.muted }}>{k}</span>
                    <span className="text-[11px] font-semibold" style={{ color: C.text }}>{v}</span>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </Section>

        {/* ── FOOTER ──────────────────────────────────────── */}
        <Section delay={0.7}>
          <div className="text-center py-6">
            <p className="text-xs" style={{ color: C.muted }}>Built for Razorpay AI Buildathon · RecoveryFlow v1.0</p>
          </div>
        </Section>
      </div>

      <style>{`@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }`}</style>
    </div>
  );
}
