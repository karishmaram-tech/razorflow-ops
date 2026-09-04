import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, ResponsiveContainer, Tooltip, XAxis } from 'recharts';

/* ============================================
   ANIMATED COUNTER HOOK
   ============================================ */
function useAnimatedCounter(target, duration = 1200) {
  const [value, setValue] = useState(0);
  const ref = useRef(null);

  useEffect(() => {
    let start = 0;
    const startTime = performance.now();
    const animate = (now) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(Math.round(eased * target));
      if (progress < 1) ref.current = requestAnimationFrame(animate);
    };
    ref.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(ref.current);
  }, [target, duration]);

  return value;
}

/* ============================================
   DATA
   ============================================ */
const SPARKLINE_DATA = Array.from({ length: 20 }, (_, i) => ({
  x: i,
  y: 20 + Math.random() * 30 + Math.sin(i * 0.5) * 15,
}));

const AREA_DATA = [
  { name: 'Jan', revenue: 18000, expenses: 12000 },
  { name: 'Feb', revenue: 22000, expenses: 14000 },
  { name: 'Mar', revenue: 19000, expenses: 11000 },
  { name: 'Apr', revenue: 28000, expenses: 16000 },
  { name: 'May', revenue: 32000, expenses: 13000 },
  { name: 'Jun', revenue: 29000, expenses: 15000 },
  { name: 'Jul', revenue: 38000, expenses: 14000 },
  { name: 'Aug', revenue: 42000, expenses: 17000 },
  { name: 'Sep', revenue: 45000, expenses: 15000 },
  { name: 'Oct', revenue: 41000, expenses: 16000 },
  { name: 'Nov', revenue: 52000, expenses: 18000 },
  { name: 'Dec', revenue: 58000, expenses: 15000 },
];

const BAR_DATA = [
  { name: 'M', value: 4200 },
  { name: 'T', value: 3800 },
  { name: 'W', value: 5100 },
  { name: 'T', value: 4600 },
  { name: 'F', value: 6200 },
  { name: 'S', value: 3100 },
  { name: 'S', value: 2800 },
];

const PIE_DATA = [
  { name: 'Settlements', value: 68, color: '#06b6d4' },
  { name: 'Refunds', value: 15, color: '#8b5cf6' },
  { name: 'Disputes', value: 12, color: '#10b981' },
  { name: 'Fees', value: 5, color: '#f59e0b' },
];

const TRANSACTIONS = [
  { id: 1, name: 'Settlement NEFT', desc: 'Auto-routed by PayFlow', amount: '+₹12,400', type: 'credit', time: '2m ago', icon: '⚡', color: '#06b6d4' },
  { id: 2, name: 'Refund Processed', desc: 'Refund #4521 routed', amount: '-₹3,200', type: 'debit', time: '15m ago', icon: '💰', color: '#8b5cf6' },
  { id: 3, name: 'Dispute Won', desc: 'Chargeback #2891', amount: '+₹8,500', type: 'credit', time: '1h ago', icon: '🛡️', color: '#10b981' },
  { id: 4, name: 'Settlement Batch', desc: 'Batch #89 — 12 routed', amount: '+₹45,000', type: 'credit', time: '2h ago', icon: '⚡', color: '#06b6d4' },
  { id: 5, name: 'Processor Fee', desc: 'Razorpay processing', amount: '-₹180', type: 'debit', time: '3h ago', icon: '💳', color: '#f59e0b' },
  { id: 6, name: 'Smart Refund', desc: 'Cheapest path selected', amount: '-₹2,100', type: 'debit', time: '4h ago', icon: '💰', color: '#8b5cf6' },
  { id: 7, name: 'Chargeback Alert', desc: 'Order #9823 flagged', amount: '+₹5,400', type: 'credit', time: '5h ago', icon: '🛡️', color: '#10b981' },
];

const AI_INSIGHTS = [
  { id: 1, type: 'opportunity', title: 'Route优化建议', desc: '将NEFT替换为IMPS可节省₹400/笔，预计月省₹16,000', confidence: 94, icon: '💡' },
  { id: 2, type: 'warning', title: '争议风险预警', desc: '订单#9823有78%概率转为chargeback，建议立即处理', confidence: 87, icon: '⚠️' },
  { id: 3, type: 'savings', title: '退款路径优化', desc: 'Smart Refund本月已为3笔退款节省₹640处理费', confidence: 96, icon: '🎯' },
];

const NOTIFICATIONS = [
  { id: 1, text: 'Settlement #1848 routed to NEFT', time: '2m ago', read: false },
  { id: 2, text: 'Dispute evidence submitted — 92% win rate', time: '15m ago', read: false },
  { id: 3, text: 'Batch #89 completed — 12/12 optimal', time: '1h ago', read: true },
  { id: 4, text: 'New processor: Stripe connected', time: '3h ago', read: true },
];

/* ============================================
   COMPONENTS
   ============================================ */
const stagger = {
  hidden: {},
  show: { transition: { staggerChildren: 0.06 } },
};
const fadeUp = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.23, 1, 0.32, 1] } },
};

function GlassCard({ children, className = '', hover = true, ...props }) {
  return (
    <motion.div
      variants={fadeUp}
      whileHover={hover ? { y: -2, transition: { duration: 0.2 } } : undefined}
      className={`rounded-2xl p-5 ${className}`}
      style={{
        background: 'rgba(12, 18, 34, 0.5)',
        backdropFilter: 'blur(16px)',
        border: '1px solid var(--pf-border)',
        transition: 'border-color 0.2s',
      }}
      onMouseEnter={(e) => hover && (e.currentTarget.style.borderColor = 'var(--pf-border-hover)')}
      onMouseLeave={(e) => hover && (e.currentTarget.style.borderColor = 'var(--pf-border)')}
      {...props}
    >
      {children}
    </motion.div>
  );
}

/* Hero Balance */
function HeroBalance() {
  const balance = useAnimatedCounter(343800);
  const change = useAnimatedCounter(42975);
  const [showBalance, setShowBalance] = useState(true);

  return (
    <div className="relative overflow-hidden rounded-3xl p-6 lg:p-8 mb-6" style={{
      background: 'linear-gradient(135deg, rgba(6,182,212,0.15) 0%, rgba(139,92,246,0.1) 50%, rgba(16,185,129,0.08) 100%)',
      border: '1px solid rgba(6,182,212,0.12)',
    }}>
      {/* Glow orbs */}
      <div className="absolute top-0 right-0 w-64 h-64 rounded-full" style={{ background: 'radial-gradient(circle, rgba(6,182,212,0.08) 0%, transparent 70%)' }} />
      <div className="absolute bottom-0 left-1/3 w-48 h-48 rounded-full" style={{ background: 'radial-gradient(circle, rgba(139,92,246,0.06) 0%, transparent 70%)' }} />

      <div className="relative flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-medium text-[var(--pf-text-secondary)]">Total Balance</span>
            <button onClick={() => setShowBalance(!showBalance)} className="text-[var(--pf-text-muted)] hover:text-white transition-colors">
              {showBalance ? (
                <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
              ) : (
                <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/></svg>
              )}
            </button>
          </div>
          <p className="text-4xl lg:text-5xl font-bold text-white tracking-tight mb-2">
            {showBalance ? `₹${balance.toLocaleString('en-IN')}` : '••••••••'}
          </p>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full">
              <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5"><path strokeLinecap="round" strokeLinejoin="round" d="M5 10l7-7m0 0l7 7m-7-7v18"/></svg>
              +₹{change.toLocaleString('en-IN')}
            </span>
            <span className="text-xs text-[var(--pf-text-muted)]">vs last month</span>
          </div>
        </div>

        {/* Mini sparkline */}
        <div className="w-full lg:w-48 h-16">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={SPARKLINE_DATA}>
              <defs>
                <linearGradient id="sparkGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#06b6d4" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#06b6d4" stopOpacity={0} />
                </linearGradient>
              </defs>
              <Area type="monotone" dataKey="y" stroke="#06b6d4" strokeWidth={2} fill="url(#sparkGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Quick actions */}
      <div className="relative flex gap-3 mt-6">
        {[
          { label: 'Send', icon: '→', gradient: 'from-cyan-500 to-blue-600' },
          { label: 'Request', icon: '←', gradient: 'from-violet-500 to-purple-600' },
          { label: 'Pay', icon: '◉', gradient: 'from-emerald-500 to-green-600' },
          { label: 'Swap', icon: '⇄', gradient: 'from-amber-500 to-orange-600' },
        ].map((a) => (
          <button key={a.label} className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold text-white transition-all duration-200 hover:scale-105 active:scale-95" style={{
            background: 'rgba(255,255,255,0.06)',
            border: '1px solid rgba(255,255,255,0.08)',
          }}>
            <span className="w-6 h-6 rounded-lg flex items-center justify-center text-[10px]" style={{ background: `var(--pf-gradient-primary)` }}>{a.icon}</span>
            {a.label}
          </button>
        ))}
      </div>
    </div>
  );
}

/* KPI Cards */
function KPICards() {
  const kpis = [
    { label: 'Revenue', value: 343800, prefix: '₹', suffix: '', color: 'var(--pf-cyan)', change: '+12.5%', up: true },
    { label: 'Settlements', value: 234000, prefix: '₹', suffix: '', color: 'var(--pf-emerald)', change: '+8.2%', up: true },
    { label: 'Disputes Won', value: 85, prefix: '', suffix: '%', color: 'var(--pf-violet)', change: '+5.1%', up: true },
    { label: 'Time Saved', value: 168, prefix: '', suffix: 'h', color: 'var(--pf-amber)', change: '+23%', up: true },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {kpis.map((kpi, i) => {
        const val = useAnimatedCounter(kpi.value);
        return (
          <motion.div
            key={kpi.label}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 + i * 0.06, duration: 0.5, ease: [0.23, 1, 0.32, 1] }}
          >
            <GlassCard className="relative overflow-hidden">
              {/* Top accent line */}
              <div className="absolute top-0 left-0 right-0 h-[2px]" style={{ background: `linear-gradient(90deg, ${kpi.color}, transparent)` }} />
              <p className="text-[11px] font-semibold uppercase tracking-wider text-[var(--pf-text-muted)] mb-2">{kpi.label}</p>
              <p className="text-2xl lg:text-3xl font-bold text-white mb-1">
                {kpi.prefix}{val.toLocaleString('en-IN')}{kpi.suffix}
              </p>
              <span className="text-xs font-semibold" style={{ color: kpi.up ? 'var(--pf-emerald)' : 'var(--pf-rose)' }}>
                {kpi.change}
              </span>
              <span className="text-[11px] text-[var(--pf-text-muted)] ml-1">this month</span>
            </GlassCard>
          </motion.div>
        );
      })}
    </div>
  );
}

/* Revenue Chart */
function RevenueChart() {
  const [period, setPeriod] = useState('year');

  return (
    <GlassCard className="mb-6">
      <div className="flex items-center justify-between mb-5">
        <div>
          <p className="text-sm font-bold text-white">Revenue Overview</p>
          <p className="text-xs text-[var(--pf-text-muted)] mt-0.5">Automated settlements & refunds</p>
        </div>
        <div className="flex gap-1 p-1 rounded-xl" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--pf-border)' }}>
          {['week', 'month', 'year'].map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className="px-3 py-1.5 rounded-lg text-[11px] font-semibold transition-all duration-200"
              style={{
                background: period === p ? 'rgba(6,182,212,0.15)' : 'transparent',
                color: period === p ? 'var(--pf-cyan)' : 'var(--pf-text-muted)',
                border: period === p ? '1px solid rgba(6,182,212,0.2)' : '1px solid transparent',
              }}
            >
              {p.charAt(0).toUpperCase() + p.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={AREA_DATA}>
            <defs>
              <linearGradient id="revenueGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#06b6d4" stopOpacity={0.25} />
                <stop offset="100%" stopColor="#06b6d4" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="expenseGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.15} />
                <stop offset="100%" stopColor="#8b5cf6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="name" tick={{ fill: '#475569', fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{ background: '#111a2e', border: '1px solid rgba(148,163,184,0.1)', borderRadius: 12, fontSize: 12 }}
              labelStyle={{ color: '#94a3b8' }}
            />
            <Area type="monotone" dataKey="revenue" stroke="#06b6d4" strokeWidth={2} fill="url(#revenueGrad)" />
            <Area type="monotone" dataKey="expenses" stroke="#8b5cf6" strokeWidth={2} fill="url(#expenseGrad)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="flex items-center gap-6 mt-3">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full" style={{ background: '#06b6d4' }} />
          <span className="text-[11px] text-[var(--pf-text-secondary)]">Revenue</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full" style={{ background: '#8b5cf6' }} />
          <span className="text-[11px] text-[var(--pf-text-secondary)]">Expenses</span>
        </div>
      </div>
    </GlassCard>
  );
}

/* Daily Activity Bar Chart */
function DailyActivity() {
  return (
    <GlassCard className="mb-6">
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm font-bold text-white">Daily Activity</p>
        <span className="text-xs text-[var(--pf-text-muted)]">This week</span>
      </div>
      <div className="h-32">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={BAR_DATA}>
            <defs>
              <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#06b6d4" stopOpacity={0.8} />
                <stop offset="100%" stopColor="#06b6d4" stopOpacity={0.2} />
              </linearGradient>
            </defs>
            <XAxis dataKey="name" tick={{ fill: '#475569', fontSize: 10 }} axisLine={false} tickLine={false} />
            <Bar dataKey="value" fill="url(#barGrad)" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </GlassCard>
  );
}

/* Asset Allocation Donut */
function AssetDonut() {
  const total = PIE_DATA.reduce((s, d) => s + d.value, 0);

  return (
    <GlassCard className="mb-6">
      <p className="text-sm font-bold text-white mb-4">Asset Allocation</p>
      <div className="flex items-center gap-5">
        <div className="w-28 h-28">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={PIE_DATA}
                cx="50%"
                cy="50%"
                innerRadius={32}
                outerRadius={50}
                paddingAngle={3}
                dataKey="value"
                stroke="none"
              >
                {PIE_DATA.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="flex-1 space-y-2.5">
          {PIE_DATA.map((d) => (
            <div key={d.name} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full" style={{ background: d.color }} />
                <span className="text-xs text-[var(--pf-text-secondary)]">{d.name}</span>
              </div>
              <span className="text-xs font-semibold text-white">{d.value}%</span>
            </div>
          ))}
        </div>
      </div>
    </GlassCard>
  );
}

/* Transactions */
function TransactionList() {
  return (
    <GlassCard className="mb-6">
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm font-bold text-white">Recent Transactions</p>
        <button className="text-xs text-[var(--pf-cyan)] font-medium hover:underline">View all →</button>
      </div>
      <div className="space-y-1">
        {TRANSACTIONS.map((tx, i) => (
          <motion.div
            key={tx.id}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.04 }}
            className="flex items-center gap-3 px-3 py-3 rounded-xl hover:bg-white/[0.02] transition-colors cursor-pointer"
          >
            <div className="w-9 h-9 rounded-xl flex items-center justify-center text-sm" style={{ background: `${tx.color}10` }}>
              {tx.icon}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-[13px] font-medium text-white truncate">{tx.name}</p>
              <p className="text-[11px] text-[var(--pf-text-muted)] truncate">{tx.desc}</p>
            </div>
            <div className="text-right flex-shrink-0">
              <p className={`text-[13px] font-semibold ${tx.type === 'credit' ? 'text-emerald-400' : 'text-rose-400'}`}>{tx.amount}</p>
              <p className="text-[10px] text-[var(--pf-text-muted)]">{tx.time}</p>
            </div>
          </motion.div>
        ))}
      </div>
    </GlassCard>
  );
}

/* AI Insights */
function AIInsights() {
  return (
    <GlassCard className="mb-6">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-6 h-6 rounded-lg flex items-center justify-center text-[10px]" style={{ background: 'var(--pf-gradient-primary)' }}>🤖</div>
        <p className="text-sm font-bold text-white">AI Insights</p>
      </div>
      <div className="space-y-3">
        {AI_INSIGHTS.map((insight, i) => (
          <motion.div
            key={insight.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 + i * 0.08 }}
            className="p-3.5 rounded-xl cursor-pointer transition-all duration-200 hover:bg-white/[0.02]"
            style={{ border: '1px solid var(--pf-border)' }}
          >
            <div className="flex items-start gap-2.5">
              <span className="text-base mt-0.5">{insight.icon}</span>
              <div className="flex-1">
                <p className="text-[13px] font-semibold text-white mb-0.5">{insight.title}</p>
                <p className="text-[11px] text-[var(--pf-text-secondary)] leading-relaxed">{insight.desc}</p>
              </div>
            </div>
            <div className="flex items-center gap-2 mt-2 ml-7">
              <div className="h-1 flex-1 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.05)' }}>
                <div className="h-full rounded-full" style={{ width: `${insight.confidence}%`, background: insight.type === 'warning' ? 'var(--pf-amber)' : 'var(--pf-cyan)' }} />
              </div>
              <span className="text-[10px] text-[var(--pf-text-muted)]">{insight.confidence}% confidence</span>
            </div>
          </motion.div>
        ))}
      </div>
    </GlassCard>
  );
}

/* Notifications */
function NotificationPanel() {
  return (
    <GlassCard className="mb-6">
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm font-bold text-white">Notifications</p>
        <span className="w-5 h-5 rounded-full bg-[var(--pf-cyan)] text-white text-[10px] font-bold flex items-center justify-center">2</span>
      </div>
      <div className="space-y-2">
        {NOTIFICATIONS.map((n, i) => (
          <div key={n.id} className="flex items-center gap-3 px-3 py-2.5 rounded-xl" style={{
            background: n.read ? 'transparent' : 'rgba(6,182,212,0.04)',
            border: `1px solid ${n.read ? 'transparent' : 'rgba(6,182,212,0.1)'}`,
          }}>
            <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: n.read ? 'transparent' : 'var(--pf-cyan)' }} />
            <p className="text-[12px] text-[var(--pf-text-secondary)] flex-1">{n.text}</p>
            <span className="text-[10px] text-[var(--pf-text-muted)] flex-shrink-0">{n.time}</span>
          </div>
        ))}
      </div>
    </GlassCard>
  );
}

/* ============================================
   MAIN DASHBOARD
   ============================================ */
export default function PremiumDashboard() {
  return (
    <div className="min-h-screen overflow-y-auto" style={{ background: 'var(--pf-bg)' }}>
      <div className="p-6 lg:p-8 max-w-[1400px] mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="flex items-center justify-between mb-6"
        >
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-widest text-[var(--pf-text-muted)] mb-0.5">Good evening</p>
            <h1 className="text-xl font-bold text-white">Command Center</h1>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full" style={{ background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.12)' }}>
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" style={{ animation: 'pf-glow-pulse 2s infinite' }} />
              <span className="text-[11px] font-medium text-emerald-400">All systems optimal</span>
            </div>
          </div>
        </motion.div>

        {/* Hero */}
        <HeroBalance />

        {/* KPIs */}
        <KPICards />

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left 2/3 */}
          <div className="lg:col-span-2">
            <RevenueChart />
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <DailyActivity />
              <AssetDonut />
            </div>
          </div>

          {/* Right 1/3 */}
          <div>
            <AIInsights />
            <NotificationPanel />
          </div>
        </div>

        {/* Full-width transactions */}
        <TransactionList />
      </div>
    </div>
  );
}
