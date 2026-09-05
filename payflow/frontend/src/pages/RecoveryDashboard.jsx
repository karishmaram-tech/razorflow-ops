import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { LineChart, Line, AreaChart, Area, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid } from 'recharts';

/* ═══════════════════════════════════════════════════════════
   RECOVERYFLOW — Nexus-Inspired AI Automation Dashboard
   ═══════════════════════════════════════════════════════════ */

// ─── COLORS ───────────────────────────────────────────────
const C = {
  bg: '#09090b',
  sidebar: '#0c0c0f',
  card: '#18181b',
  cardHover: '#1e1e22',
  cardBorder: 'rgba(63, 63, 70, 0.5)',
  text: '#fafafa',
  textSecondary: '#a1a1aa',
  textMuted: '#52525b',
  primary: '#6366f1',
  primaryLight: '#818cf8',
  emerald: '#10b981',
  amber: '#f59e0b',
  rose: '#f43f5e',
  cyan: '#06b6d4',
  violet: '#8b5cf6',
  blue: '#3b82f6',
};

const AGENT_COLORS = {
  investigator: '#06b6d4',
  predictor: '#8b5cf6',
  risk: '#f43f5e',
  economics: '#10b981',
  strategy: '#6366f1',
  learning: '#f59e0b',
};

const AGENT_ICONS = {
  investigator: '🔍',
  predictor: '🧠',
  risk: '🛡️',
  economics: '💰',
  strategy: '🎯',
  learning: '📈',
};

// ─── PERFORMANCE DATA ─────────────────────────────────────
const PERFORMANCE_DATA = [
  { time: '00:00', efficiency: 72, recovered: 12, failed: 3 },
  { time: '02:00', efficiency: 74, recovered: 15, failed: 4 },
  { time: '04:00', efficiency: 71, recovered: 11, failed: 5 },
  { time: '06:00', efficiency: 78, recovered: 18, failed: 3 },
  { time: '08:00', efficiency: 82, recovered: 24, failed: 4 },
  { time: '10:00', efficiency: 85, recovered: 28, failed: 2 },
  { time: '12:00', efficiency: 88, recovered: 32, failed: 3 },
  { time: '14:00', efficiency: 86, recovered: 30, failed: 4 },
  { time: '16:00', efficiency: 91, recovered: 35, failed: 2 },
  { time: '18:00', efficiency: 89, recovered: 33, failed: 3 },
  { time: '20:00', efficiency: 92, recovered: 36, failed: 1 },
  { time: '22:00', efficiency: 94, recovered: 38, failed: 2 },
];

const AGENT_PERFORMANCE = [
  { time: '00:00', investigator: 88, predictor: 82, risk: 95, economics: 90, strategy: 85, learning: 78 },
  { time: '04:00', investigator: 90, predictor: 84, risk: 94, economics: 91, strategy: 87, learning: 80 },
  { time: '08:00', investigator: 92, predictor: 88, risk: 96, economics: 93, strategy: 90, learning: 84 },
  { time: '12:00', investigator: 94, predictor: 91, risk: 97, economics: 94, strategy: 92, learning: 87 },
  { time: '16:00', investigator: 93, predictor: 89, risk: 96, economics: 95, strategy: 91, learning: 86 },
  { time: '20:00', investigator: 95, predictor: 92, risk: 98, economics: 96, strategy: 93, learning: 89 },
];

// ─── DEMO SCENARIOS ──────────────────────────────────────
const DEMO_SCENARIOS = [
  {
    name: 'High-Value Recovery',
    subtitle: '3-year SaaS subscriber, card expired',
    customer: { name: 'Sarah Kumar', tenure: 36, ltv: 3564, monthly: 99, segment: 'high_ltv_stable' },
    failure: { reason: 'card_expired', amount: 99 },
    agents: {
      investigator: { status: 'complete', confidence: 91, reasoning: 'Card expired — temporary issue. 3-year tenure, 36 successful payments, zero chargebacks, 2 backup methods.', time: '0.8s' },
      predictor: { status: 'complete', confidence: 82, reasoning: 'SMS + Payment Link: 82% success probability. Best strategy for high-LTV stable segment.', time: '1.2s' },
      risk: { status: 'complete', confidence: 95, reasoning: 'Clean history. Chargeback risk: 1.2%. Fraud: 0.1%. Safe to proceed.', time: '0.6s' },
      economics: { status: 'complete', confidence: 90, reasoning: 'ENR: $1,024 via SMS+Link. ROI: 12,794x. Recommendation: EXECUTE.', time: '0.4s' },
      strategy: { status: 'complete', confidence: 82, reasoning: 'SMS + Payment Link selected. Balances 82% success with scalability. Conflict resolved: all agents agree.', time: '0.3s' },
      learning: { status: 'pending', confidence: 0, reasoning: 'Awaiting outcome to update model.', time: '—' },
    },
    outcome: { result: 'success', recovered: 99, cost: 0.08, time: '45s' },
  },
  {
    name: 'Risk Conflict',
    subtitle: 'Chargeback history, agents disagree',
    customer: { name: 'James Wilson', tenure: 18, ltv: 2160, monthly: 120, segment: 'mid_ltv_transient' },
    failure: { reason: 'insufficient_funds', amount: 120 },
    agents: {
      investigator: { status: 'complete', confidence: 85, reasoning: 'Insufficient funds — likely temporary. 18-month customer but 3 prior chargebacks.', time: '0.9s' },
      predictor: { status: 'complete', confidence: 74, reasoning: 'Support call: 85% success. SMS: 72%. Email: 42%. Moderate confidence.', time: '1.1s' },
      risk: { status: 'complete', confidence: 68, reasoning: 'Chargeback propensity: 6.8%. Elevated risk. Recommend conservative strategy.', time: '0.7s' },
      economics: { status: 'complete', confidence: 88, reasoning: 'ENR: $832 via SMS. Email: $501. Risk-adjusted: email is safer.', time: '0.5s' },
      strategy: { status: 'complete', confidence: 74, reasoning: 'Email only selected. Risk agent flagged CAUTION. Conflict resolved: risk takes priority.', time: '0.4s' },
      learning: { status: 'pending', confidence: 0, reasoning: 'Awaiting outcome.', time: '—' },
    },
    outcome: { result: 'success', recovered: 120, cost: 0.01, time: '2.3h' },
  },
  {
    name: 'Skip — Not Economical',
    subtitle: 'Low-value, high-risk, system says NO',
    customer: { name: 'Alex Lee', tenure: 2, ltv: 48, monthly: 10, segment: 'low_ltv_at_risk' },
    failure: { reason: 'fraud_blocked', amount: 10 },
    agents: {
      investigator: { status: 'complete', confidence: 88, reasoning: 'Fraud blocked. Only 2-month tenure, low LTV, 1 prior chargeback. Not recoverable.', time: '0.5s' },
      predictor: { status: 'complete', confidence: 65, reasoning: 'All strategies below 30% probability. Best: support call at 30%. Low confidence.', time: '0.9s' },
      risk: { status: 'complete', confidence: 72, reasoning: 'Fraud signal active. Chargeback: 8.2%. Total risk: 5.7%. CAUTION.', time: '0.6s' },
      economics: { status: 'complete', confidence: 90, reasoning: 'Negative ENR for most strategies. Email: $3 (barely positive). Recommendation: SKIP.', time: '0.3s' },
      strategy: { status: 'complete', confidence: 88, reasoning: 'SKIP. Recoverability < 25%. Negative EV. High fraud risk. Accepting $10 loss.', time: '0.2s' },
      learning: { status: 'pending', confidence: 0, reasoning: 'No recovery attempted.', time: '—' },
    },
    outcome: { result: 'skipped', recovered: 0, cost: 0, time: 'N/A' },
  },
];

// ─── SIDEBAR ──────────────────────────────────────────────
function Sidebar({ activePage, setActivePage }) {
  const navItems = [
    { id: 'dashboard', icon: '📊', label: 'Dashboard' },
    { id: 'agents', icon: '🤖', label: 'Agents' },
    { id: 'workflows', icon: '⚡', label: 'Workflows' },
    { id: 'analytics', icon: '📈', label: 'Analytics' },
    { id: 'transactions', icon: '💳', label: 'Transactions' },
    { id: 'settings', icon: '⚙️', label: 'Settings' },
  ];

  return (
    <div className="w-[240px] flex-shrink-0 h-screen sticky top-0 flex flex-col"
      style={{ background: C.sidebar, borderRight: `1px solid ${C.cardBorder}` }}>

      {/* Logo */}
      <div className="p-6 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center"
            style={{ background: `linear-gradient(135deg, ${C.primary}, ${C.violet})`, boxShadow: `0 4px 12px ${C.primary}30` }}>
            <span className="text-white font-bold text-sm">R</span>
          </div>
          <div>
            <p className="text-sm font-bold" style={{ color: C.text }}>RecoveryFlow</p>
            <p className="text-[10px]" style={{ color: C.textMuted }}>AI Revenue Recovery</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3">
        {navItems.map(item => (
          <button key={item.id} onClick={() => setActivePage(item.id)}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm mb-1 transition-all duration-200"
            style={{
              background: activePage === item.id ? `${C.primary}15` : 'transparent',
              color: activePage === item.id ? C.primary : C.textSecondary,
              border: `1px solid ${activePage === item.id ? `${C.primary}25` : 'transparent'}`,
            }}>
            <span className="text-base">{item.icon}</span>
            <span className="font-medium">{item.label}</span>
          </button>
        ))}
      </nav>

      {/* Bottom */}
      <div className="p-4 mx-3 mb-4 rounded-xl" style={{ background: `${C.primary}10`, border: `1px solid ${C.primary}20` }}>
        <div className="flex items-center gap-2 mb-2">
          <div className="w-1.5 h-1.5 rounded-full" style={{ background: C.emerald, animation: 'pulse 2s infinite' }} />
          <span className="text-[11px] font-semibold" style={{ color: C.emerald }}>6 Agents Online</span>
        </div>
        <p className="text-[10px]" style={{ color: C.textMuted }}>All systems operational</p>
      </div>

      {/* User */}
      <div className="p-4 flex items-center gap-3" style={{ borderTop: `1px solid ${C.cardBorder}` }}>
        <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold"
          style={{ background: `linear-gradient(135deg, ${C.primary}, ${C.violet})`, color: 'white' }}>
          JD
        </div>
        <div>
          <p className="text-xs font-semibold" style={{ color: C.text }}>John Doe</p>
          <p className="text-[10px]" style={{ color: C.textMuted }}>Admin</p>
        </div>
      </div>
    </div>
  );
}

// ─── AGENT CARD ───────────────────────────────────────────
function AgentCard({ agent, result, isActive, onClick }) {
  const color = AGENT_COLORS[agent];
  return (
    <motion.div
      whileHover={{ y: -2 }}
      onClick={onClick}
      className="p-4 rounded-2xl cursor-pointer transition-all duration-200"
      style={{
        background: isActive ? `${color}10` : C.card,
        border: `1px solid ${isActive ? `${color}30` : C.cardBorder}`,
      }}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl flex items-center justify-center text-sm"
            style={{ background: `${color}15` }}>
            {AGENT_ICONS[agent]}
          </div>
          <div>
            <p className="text-xs font-semibold" style={{ color: C.text }}>
              {agent.charAt(0).toUpperCase() + agent.slice(1)}
            </p>
            <p className="text-[10px]" style={{ color: C.textMuted }}>Agent</p>
          </div>
        </div>
        <div className="px-2 py-0.5 rounded-full text-[10px] font-semibold"
          style={{
            background: result?.status === 'complete' ? `${C.emerald}15` : `${C.amber}15`,
            color: result?.status === 'complete' ? C.emerald : C.amber,
          }}>
          {result?.status === 'complete' ? '● ACTIVE' : '○ PENDING'}
        </div>
      </div>

      {result && (
        <>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-[10px]" style={{ color: C.textMuted }}>Confidence</span>
            <span className="text-xs font-bold" style={{ color }}>{result.confidence}%</span>
          </div>
          <div className="h-1.5 rounded-full overflow-hidden mb-2" style={{ background: `${color}15` }}>
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${result.confidence}%` }}
              transition={{ duration: 0.8, ease: [0.23, 1, 0.32, 1] }}
              className="h-full rounded-full"
              style={{ background: `linear-gradient(90deg, ${color}, ${color}80)` }}
            />
          </div>
          <p className="text-[10px]" style={{ color: C.textMuted }}>Time: {result.time}</p>
        </>
      )}
    </motion.div>
  );
}

// ─── ACTIVITY ITEM ────────────────────────────────────────
function ActivityItem({ item, index }) {
  const typeColors = {
    success: C.emerald,
    running: C.primary,
    skip: C.amber,
    failed: C.rose,
  };
  const color = typeColors[item.type] || C.primary;

  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
      className="flex items-center gap-3 p-3 rounded-xl transition-all duration-200"
      style={{ cursor: 'pointer' }}
      onMouseEnter={e => e.currentTarget.style.background = C.cardHover}
      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
    >
      <div className="w-8 h-8 rounded-xl flex items-center justify-center text-sm flex-shrink-0"
        style={{ background: `${AGENT_COLORS[item.agent]}15` }}>
        {AGENT_ICONS[item.agent]}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium truncate" style={{ color: C.text }}>{item.title}</p>
        <p className="text-[10px] truncate" style={{ color: C.textMuted }}>{item.detail}</p>
      </div>
      <div className="flex items-center gap-2 flex-shrink-0">
        <span className="text-[10px]" style={{ color: C.textMuted }}>{item.time}</span>
        <div className="w-1.5 h-1.5 rounded-full" style={{ background: color }} />
      </div>
    </motion.div>
  );
}

// ─── STAT CARD ────────────────────────────────────────────
function StatCard({ label, value, change, color, icon, delay = 0 }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.4 }}
      className="p-5 rounded-2xl transition-all duration-200"
      style={{ background: C.card, border: `1px solid ${C.cardBorder}` }}
      onMouseEnter={e => { e.currentTarget.style.borderColor = `${color}40`; e.currentTarget.style.transform = 'translateY(-2px)'; }}
      onMouseLeave={e => { e.currentTarget.style.borderColor = C.cardBorder; e.currentTarget.style.transform = 'translateY(0)'; }}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-[11px] font-medium" style={{ color: C.textMuted }}>{label}</span>
        <div className="w-7 h-7 rounded-lg flex items-center justify-center text-xs"
          style={{ background: `${color}15` }}>
          {icon}
        </div>
      </div>
      <p className="text-2xl font-bold mb-1" style={{ color: C.text }}>{value}</p>
      {change && (
        <span className="text-[11px] font-semibold" style={{ color: change.startsWith('+') ? C.emerald : C.rose }}>
          {change} <span style={{ color: C.textMuted, fontWeight: 400 }}>vs last week</span>
        </span>
      )}
    </motion.div>
  );
}

// ─── CUSTOM TOOLTIP ───────────────────────────────────────
function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="px-3 py-2 rounded-xl text-xs" style={{ background: C.card, border: `1px solid ${C.cardBorder}` }}>
      <p className="font-semibold mb-1" style={{ color: C.text }}>{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color }}>{p.name}: {p.value}%</p>
      ))}
    </div>
  );
}

// ─── MAIN DASHBOARD ──────────────────────────────────────
export default function RecoveryDashboard() {
  const [activePage, setActivePage] = useState('dashboard');
  const [activeScenario, setActiveScenario] = useState(0);
  const [activeAgent, setActiveAgent] = useState('investigator');
  const [isRunning, setIsRunning] = useState(false);
  const [agentSteps, setAgentSteps] = useState({});
  const [showOutcome, setShowOutcome] = useState(false);

  const scenario = DEMO_SCENARIOS[activeScenario];

  const runDemo = useCallback(() => {
    setAgentSteps({});
    setShowOutcome(false);
    setIsRunning(true);
    setActiveAgent('investigator');

    const agents = ['investigator', 'predictor', 'risk', 'economics', 'strategy', 'learning'];
    let i = 0;

    const interval = setInterval(() => {
      if (i < agents.length) {
        setAgentSteps(prev => ({ ...prev, [agents[i]]: scenario.agents[agents[i]] }));
        setActiveAgent(agents[i]);
        i++;
      } else {
        clearInterval(interval);
        setShowOutcome(true);
        setIsRunning(false);
      }
    }, 700);
  }, [activeScenario, scenario]);

  const activityItems = [
    { agent: 'strategy', title: 'Sarah K. → SMS+Link sent', detail: '82% success probability', type: 'success', time: '2m ago' },
    { agent: 'economics', title: 'James W. → Email sent', detail: 'Risk-constrained choice', type: 'running', time: '5m ago' },
    { agent: 'risk', title: 'Alex L. → Skipped', detail: 'Negative EV, high fraud risk', type: 'skip', time: '8m ago' },
    { agent: 'investigator', title: 'Priya D. → Analyzing', detail: 'Card expired, temporary', type: 'running', time: '12m ago' },
    { agent: 'predictor', title: 'Chen M. → Probabilities computed', detail: 'Best: SMS at 72%', type: 'running', time: '15m ago' },
    { agent: 'learning', title: 'Model updated', detail: 'Payment link: +2% for high-LTV', type: 'success', time: '18m ago' },
    { agent: 'economics', title: 'Budget check passed', detail: '$80 / $500 monthly limit', type: 'success', time: '22m ago' },
  ];

  return (
    <div className="flex min-h-screen" style={{ background: C.bg, fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" }}>
      <Sidebar activePage={activePage} setActivePage={setActivePage} />

      <main className="flex-1 overflow-auto">
        <div className="p-6 lg:p-8 max-w-[1400px] mx-auto">

          {/* ─── HEADER ──────────────────────────────────── */}
          <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
            className="flex items-center justify-between mb-8 flex-wrap gap-4">
            <div>
              <h1 className="text-2xl font-bold" style={{ color: C.text }}>AI Automation Dashboard</h1>
              <p className="text-sm mt-1" style={{ color: C.textMuted }}>
                Monitor agent performance, workflows, and recovery metrics
              </p>
            </div>
            <div className="flex items-center gap-3">
              <button onClick={runDemo} disabled={isRunning}
                className="px-5 py-2.5 rounded-xl text-xs font-bold transition-all duration-200"
                style={{
                  background: isRunning ? `${C.primary}40` : `linear-gradient(135deg, ${C.primary}, ${C.violet})`,
                  color: 'white', cursor: isRunning ? 'wait' : 'pointer',
                  boxShadow: isRunning ? 'none' : `0 4px 16px ${C.primary}30`,
                }}>
                {isRunning ? '⏳ Running Agents...' : '▶ Run Recovery Demo'}
              </button>
            </div>
          </motion.div>

          {/* ─── STAT CARDS ──────────────────────────────── */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatCard label="Revenue Recovered" value="$854,880" change="+771K vs baseline" color={C.emerald} icon="💰" delay={0.1} />
            <StatCard label="Recovery Rate" value="72%" change="+67% vs naive" color={C.primary} icon="📊" delay={0.15} />
            <StatCard label="Intervention Cost" value="$80" change="-97% vs manual" color={C.amber} icon="⚡" delay={0.2} />
            <StatCard label="ROI" value="9,646x" change="+9646x vs no action" color={C.violet} icon="🚀" delay={0.25} />
          </div>

          {/* ─── MAIN CONTENT: 2-COLUMN ───────────────────── */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">

            {/* LEFT: Performance Graph + Agent Cards */}
            <div className="lg:col-span-2 space-y-6">

              {/* Performance Graph */}
              <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
                className="p-6 rounded-2xl"
                style={{ background: C.card, border: `1px solid ${C.cardBorder}` }}>
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <p className="text-sm font-bold" style={{ color: C.text }}>Agent Efficiency Over Time</p>
                    <p className="text-[11px] mt-0.5" style={{ color: C.textMuted }}>Recovery success rate by hour</p>
                  </div>
                  <div className="flex gap-2">
                    {['24H', '7D', '30D'].map((t, i) => (
                      <button key={t} className="px-3 py-1 rounded-lg text-[10px] font-semibold"
                        style={{
                          background: i === 0 ? `${C.primary}15` : 'transparent',
                          color: i === 0 ? C.primary : C.textMuted,
                          border: `1px solid ${i === 0 ? `${C.primary}25` : 'transparent'}`,
                        }}>
                        {t}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="h-[240px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={PERFORMANCE_DATA}>
                      <defs>
                        <linearGradient id="effGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor={C.primary} stopOpacity={0.3} />
                          <stop offset="100%" stopColor={C.primary} stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(63,63,70,0.3)" />
                      <XAxis dataKey="time" tick={{ fontSize: 10, fill: C.textMuted }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fontSize: 10, fill: C.textMuted }} axisLine={false} tickLine={false} domain={[60, 100]} />
                      <Tooltip content={<CustomTooltip />} />
                      <Area type="monotone" dataKey="efficiency" stroke={C.primary} fill="url(#effGrad)" strokeWidth={2} name="Efficiency" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </motion.div>

              {/* Agent Cards Grid */}
              <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
                <p className="text-sm font-bold mb-4" style={{ color: C.text }}>Agent Status</p>
                <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
                  {Object.keys(AGENT_COLORS).map(agent => (
                    <AgentCard
                      key={agent}
                      agent={agent}
                      result={agentSteps[agent]}
                      isActive={activeAgent === agent}
                      onClick={() => setActiveAgent(agent)}
                    />
                  ))}
                </div>
              </motion.div>
            </div>

            {/* RIGHT: Activity Feed + Agent Detail */}
            <div className="space-y-6">

              {/* Activity Feed */}
              <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }}
                className="p-5 rounded-2xl"
                style={{ background: C.card, border: `1px solid ${C.cardBorder}` }}>
                <div className="flex items-center justify-between mb-4">
                  <p className="text-sm font-bold" style={{ color: C.text }}>Activity Feed</p>
                  <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold"
                    style={{ background: `${C.emerald}15`, color: C.emerald }}>Live</span>
                </div>
                <div className="space-y-1">
                  {activityItems.map((item, i) => <ActivityItem key={i} item={item} index={i} />)}
                </div>
              </motion.div>

              {/* Agent Detail Panel */}
              <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.45 }}
                className="p-5 rounded-2xl"
                style={{ background: C.card, border: `1px solid ${C.cardBorder}` }}>
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-lg">{AGENT_ICONS[activeAgent]}</span>
                  <p className="text-sm font-bold" style={{ color: C.text }}>
                    {activeAgent.charAt(0).toUpperCase() + activeAgent.slice(1)} Agent
                  </p>
                </div>

                {agentSteps[activeAgent] ? (
                  <div>
                    <div className="flex items-center gap-3 mb-3">
                      <div className="flex-1">
                        <p className="text-[10px] mb-1" style={{ color: C.textMuted }}>Confidence</p>
                        <div className="h-2 rounded-full overflow-hidden" style={{ background: `${AGENT_COLORS[activeAgent]}15` }}>
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${agentSteps[activeAgent].confidence}%` }}
                            transition={{ duration: 0.8 }}
                            className="h-full rounded-full"
                            style={{ background: AGENT_COLORS[activeAgent] }}
                          />
                        </div>
                      </div>
                      <span className="text-lg font-bold" style={{ color: AGENT_COLORS[activeAgent] }}>
                        {agentSteps[activeAgent].confidence}%
                      </span>
                    </div>
                    <p className="text-xs leading-relaxed" style={{ color: C.textSecondary }}>
                      {agentSteps[activeAgent].reasoning}
                    </p>
                    <p className="text-[10px] mt-2" style={{ color: C.textMuted }}>
                      Processing time: {agentSteps[activeAgent].time}
                    </p>
                  </div>
                ) : (
                  <p className="text-xs" style={{ color: C.textMuted }}>
                    Run a demo or select an agent to view details.
                  </p>
                )}
              </motion.div>

              {/* Segment Performance */}
              <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.55 }}
                className="p-5 rounded-2xl"
                style={{ background: C.card, border: `1px solid ${C.cardBorder}` }}>
                <p className="text-sm font-bold mb-4" style={{ color: C.text }}>By Segment</p>
                {[
                  { label: 'High-LTV Stable', rate: 92, color: C.emerald, count: 48 },
                  { label: 'Mid-LTV Transient', rate: 57, color: C.primary, count: 88 },
                  { label: 'Low-LTV At-Risk', rate: 30, color: C.amber, count: 28 },
                ].map((seg, i) => (
                  <div key={seg.label} className="mb-3">
                    <div className="flex justify-between mb-1">
                      <span className="text-[11px] font-medium" style={{ color: C.textSecondary }}>{seg.label}</span>
                      <span className="text-[11px] font-bold" style={{ color: seg.color }}>{seg.rate}%</span>
                    </div>
                    <div className="h-1.5 rounded-full overflow-hidden" style={{ background: `${seg.color}15` }}>
                      <motion.div initial={{ width: 0 }} animate={{ width: `${seg.rate}%` }}
                        transition={{ delay: 0.6 + i * 0.1, duration: 0.8, ease: [0.23, 1, 0.32, 1] }}
                        className="h-full rounded-full" style={{ background: seg.color }} />
                    </div>
                    <p className="text-[10px] mt-0.5" style={{ color: C.textMuted }}>{seg.count} recovered</p>
                  </div>
                ))}
              </motion.div>
            </div>
          </div>

          {/* ─── BOTTOM: Scenario Selector + Outcome ──────── */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

            {/* Scenario Selector */}
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }}
              className="p-6 rounded-2xl"
              style={{ background: C.card, border: `1px solid ${C.cardBorder}` }}>
              <p className="text-sm font-bold mb-4" style={{ color: C.text }}>Recovery Scenarios</p>
              <div className="space-y-3">
                {DEMO_SCENARIOS.map((s, i) => (
                  <button key={i} onClick={() => { setActiveScenario(i); setAgentSteps({}); setShowOutcome(false); }}
                    className="w-full p-4 rounded-xl text-left transition-all duration-200"
                    style={{
                      background: i === activeScenario ? `${C.primary}10` : 'transparent',
                      border: `1px solid ${i === activeScenario ? `${C.primary}25` : C.cardBorder}`,
                    }}>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs font-semibold" style={{ color: i === activeScenario ? C.primary : C.text }}>
                          {s.name}
                        </p>
                        <p className="text-[10px] mt-0.5" style={{ color: C.textMuted }}>{s.subtitle}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-xs font-bold" style={{ color: C.text }}>${s.failure.amount}</p>
                        <p className="text-[10px]" style={{ color: C.textMuted }}>{s.customer.segment}</p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </motion.div>

            {/* Outcome */}
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.65 }}
              className="p-6 rounded-2xl"
              style={{ background: C.card, border: `1px solid ${C.cardBorder}` }}>
              <p className="text-sm font-bold mb-4" style={{ color: C.text }}>Recovery Outcome</p>

              {showOutcome && scenario.outcome ? (
                <div>
                  <div className="p-4 rounded-xl mb-4" style={{
                    background: scenario.outcome.result === 'success' ? `${C.emerald}10` :
                                scenario.outcome.result === 'skipped' ? `${C.amber}10` : `${C.rose}10`,
                    border: `1px solid ${scenario.outcome.result === 'success' ? `${C.emerald}25` :
                             scenario.outcome.result === 'skipped' ? `${C.amber}25` : `${C.rose}25`}`,
                  }}>
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">
                        {scenario.outcome.result === 'success' ? '✅' :
                         scenario.outcome.result === 'skipped' ? '🚫' : '❌'}
                      </span>
                      <div>
                        <p className="text-sm font-bold" style={{
                          color: scenario.outcome.result === 'success' ? C.emerald :
                                 scenario.outcome.result === 'skipped' ? C.amber : C.rose
                        }}>
                          {scenario.outcome.result === 'success' ? 'RECOVERED' :
                           scenario.outcome.result === 'skipped' ? 'SKIPPED' : 'FAILED'}
                        </p>
                        {scenario.outcome.recovered > 0 && (
                          <p className="text-xs" style={{ color: C.textSecondary }}>
                            ${scenario.outcome.recovered} recovered in {scenario.outcome.time}
                          </p>
                        )}
                        {scenario.outcome.cost > 0 && (
                          <p className="text-[10px]" style={{ color: C.textMuted }}>
                            Cost: ${scenario.outcome.cost}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-3">
                    <div className="p-3 rounded-xl" style={{ background: `${C.primary}10` }}>
                      <p className="text-[10px]" style={{ color: C.textMuted }}>Strategy</p>
                      <p className="text-xs font-bold" style={{ color: C.text }}>
                        {scenario.agents.strategy.reasoning.split('.')[0]}
                      </p>
                    </div>
                    <div className="p-3 rounded-xl" style={{ background: `${C.emerald}10` }}>
                      <p className="text-[10px]" style={{ color: C.textMuted }}>ENR</p>
                      <p className="text-xs font-bold" style={{ color: C.emerald }}>
                        ${scenario.outcome.recovered > 0 ? (scenario.outcome.recovered * 10).toLocaleString() : '0'}
                      </p>
                    </div>
                    <div className="p-3 rounded-xl" style={{ background: `${C.violet}10` }}>
                      <p className="text-[10px]" style={{ color: C.textMuted }}>Confidence</p>
                      <p className="text-xs font-bold" style={{ color: C.violet }}>
                        {scenario.agents.strategy.confidence}%
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-4xl mb-3">🤖</p>
                  <p className="text-xs" style={{ color: C.textMuted }}>
                    {isRunning ? 'Agents are processing...' : 'Run a demo to see the outcome'}
                  </p>
                </div>
              )}
            </motion.div>
          </div>

          {/* ─── COMPARISON TABLE ─────────────────────────── */}
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.7 }}
            className="mt-8 p-6 rounded-2xl"
            style={{ background: C.card, border: `1px solid ${C.cardBorder}` }}>
            <p className="text-sm font-bold mb-4" style={{ color: C.text }}>RecoveryFlow vs Baseline</p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[
                { label: 'No Intervention', recovered: '5%', revenue: '$59,400', cost: '$0', net: '$59,400', color: C.rose },
                { label: 'Fixed Retry', recovered: '38%', revenue: '$451,440', cost: '$250', net: '$356,150', color: C.amber },
                { label: 'RecoveryFlow', recovered: '72%', revenue: '$854,880', cost: '$80', net: '$831,040', color: C.emerald },
              ].map((col) => (
                <div key={col.label} className="p-4 rounded-xl" style={{
                  background: `${col.color}08`, border: `1px solid ${col.color}20`,
                }}>
                  <p className="text-sm font-bold mb-3" style={{ color: col.color }}>{col.label}</p>
                  {[
                    ['Recovery Rate', col.recovered],
                    ['Revenue', col.revenue],
                    ['Cost', col.cost],
                    ['Net Recovery', col.net],
                  ].map(([k, v]) => (
                    <div key={k} className="flex justify-between py-1.5"
                      style={{ borderBottom: '1px solid rgba(63,63,70,0.2)' }}>
                      <span className="text-[11px]" style={{ color: C.textMuted }}>{k}</span>
                      <span className="text-[11px] font-semibold" style={{ color: C.text }}>{v}</span>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </main>

      <style>{`@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }`}</style>
    </div>
  );
}
