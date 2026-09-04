import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, ResponsiveContainer, Tooltip, XAxis } from 'recharts';

/* ============================================
   ANIMATED COUNTER
   ============================================ */
function useCounter(target, duration = 1000) {
  const [val, setVal] = useState(0);
  const r = useRef(null);
  useEffect(() => {
    const t0 = performance.now();
    const tick = (now) => {
      const p = Math.min((now - t0) / duration, 1);
      setVal(Math.round((1 - Math.pow(1 - p, 3)) * target));
      if (p < 1) r.current = requestAnimationFrame(tick);
    };
    r.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(r.current);
  }, [target, duration]);
  return val;
}

/* ============================================
   DATA
   ============================================ */
const SPARKLINE = Array.from({ length: 24 }, (_, i) => ({ x: i, y: 20 + Math.sin(i * 0.4) * 12 + Math.random() * 8 }));

const AREA_DATA = [
  { m: 'Jan', rev: 18, exp: 12 }, { m: 'Feb', rev: 22, exp: 14 },
  { m: 'Mar', rev: 19, exp: 11 }, { m: 'Apr', rev: 28, exp: 16 },
  { m: 'May', rev: 32, exp: 13 }, { m: 'Jun', rev: 29, exp: 15 },
  { m: 'Jul', rev: 38, exp: 14 }, { m: 'Aug', rev: 42, exp: 17 },
  { m: 'Sep', rev: 45, exp: 15 }, { m: 'Oct', rev: 41, exp: 16 },
  { m: 'Nov', rev: 52, exp: 18 }, { m: 'Dec', rev: 58, exp: 15 },
];

const BAR_DATA = [
  { d: 'Mon', v: 4200 }, { d: 'Tue', v: 3800 }, { d: 'Wed', v: 5100 },
  { d: 'Thu', v: 4600 }, { d: 'Fri', v: 6200 }, { d: 'Sat', v: 3100 }, { d: 'Sun', v: 2800 },
];

const PIE = [
  { n: 'Settlements', v: 68, c: '#2563eb' },
  { n: 'Refunds', v: 15, c: '#7c3aed' },
  { n: 'Disputes', v: 12, c: '#059669' },
  { n: 'Fees', v: 5, c: '#d97706' },
];

const TXS = [
  { id: 1, n: 'Settlement NEFT', d: 'Auto-routed by PayFlow', a: '+₹12,400', t: 'credit', time: '2m', icon: '⚡', c: '#2563eb' },
  { id: 2, n: 'Refund Processed', d: 'Refund #4521 routed', a: '-₹3,200', t: 'debit', time: '15m', icon: '💰', c: '#7c3aed' },
  { id: 3, n: 'Dispute Won', d: 'Chargeback #2891', a: '+₹8,500', t: 'credit', time: '1h', icon: '🛡️', c: '#059669' },
  { id: 4, n: 'Settlement Batch', d: 'Batch #89 — 12 routed', a: '+₹45,000', t: 'credit', time: '2h', icon: '⚡', c: '#2563eb' },
  { id: 5, n: 'Processor Fee', d: 'Razorpay processing', a: '-₹180', t: 'debit', time: '3h', icon: '💳', c: '#d97706' },
  { id: 6, n: 'Smart Refund', d: 'Cheapest path selected', a: '-₹2,100', t: 'debit', time: '4h', icon: '💰', c: '#7c3aed' },
  { id: 7, n: 'Chargeback Alert', d: 'Order #9823 flagged', a: '+₹5,400', t: 'credit', time: '5h', icon: '🛡️', c: '#059669' },
];

const AI = [
  { icon: '💡', title: 'Route Optimization', desc: 'Switch from NEFT to IMPS saves ₹400/txn — projected ₹16K monthly savings', pct: 94 },
  { icon: '⚠️', title: 'Dispute Risk Alert', desc: 'Order #9823 has 78% chance of chargeback — action recommended', pct: 87 },
  { icon: '🎯', title: 'Refund Savings', desc: 'Smart Refund saved ₹640 on 3 refunds this month automatically', pct: 96 },
];

/* ============================================
   ANIMATION VARIANTS
   ============================================ */
const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.06 } } };
const fadeUp = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.23, 1, 0.32, 1] } } };

/* ============================================
   COMPONENTS
   ============================================ */
function Card({ children, className = '', style = {}, hover = true }) {
  return (
    <motion.div
      variants={fadeUp}
      whileHover={hover ? { y: -2, boxShadow: '0 10px 25px -3px rgba(0, 0, 0, 0.08), 0 4px 10px -2px rgba(0, 0, 0, 0.04)' } : undefined}
      className={`rounded-2xl ${className}`}
      style={{ background: '#ffffff', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0, 0, 0, 0.06)', transition: 'all 0.25s cubic-bezier(0.23, 1, 0.32, 1)', ...style }}
    >
      {children}
    </motion.div>
  );
}

/* Hero */
function Hero() {
  const bal = useCounter(343800);
  const chg = useCounter(42975);
  return (
    <motion.div variants={fadeUp} className="relative overflow-hidden rounded-2xl p-6 lg:p-8 mb-6" style={{
      background: 'linear-gradient(135deg, #2563eb 0%, #7c3aed 50%, #ec4899 100%)',
      boxShadow: '0 8px 32px rgba(37, 99, 235, 0.25)',
    }}>
      <div className="absolute top-0 right-0 w-64 h-64 rounded-full" style={{ background: 'radial-gradient(circle, rgba(255,255,255,0.12) 0%, transparent 70%)' }} />
      <div className="absolute bottom-0 left-1/4 w-48 h-48 rounded-full" style={{ background: 'radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%)' }} />

      <div className="relative flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest mb-1" style={{ color: 'rgba(255,255,255,0.7)' }}>Total Balance</p>
          <p className="text-4xl lg:text-5xl font-bold text-white tracking-tight mb-2">
            ₹{bal.toLocaleString('en-IN')}
          </p>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1 text-xs font-semibold bg-white/20 text-white px-2.5 py-1 rounded-full backdrop-blur-sm">
              ↑ ₹{chg.toLocaleString('en-IN')} this month
            </span>
          </div>
        </div>
        <div className="w-full lg:w-52 h-16">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={SPARKLINE}>
              <defs>
                <linearGradient id="spk" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="white" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="white" stopOpacity={0} />
                </linearGradient>
              </defs>
              <Area type="monotone" dataKey="y" stroke="white" strokeWidth={2} fill="url(#spk)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="relative flex gap-3 mt-6">
        {['Send', 'Request', 'Pay', 'Swap'].map((l) => (
          <button key={l} className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold text-white bg-white/15 hover:bg-white/25 backdrop-blur-sm transition-all duration-200 hover:scale-105 active:scale-95 border border-white/10">
            {l}
          </button>
        ))}
      </div>
    </motion.div>
  );
}

/* KPIs */
function KPIs() {
  const data = [
    { l: 'Revenue', v: 343800, p: '₹', s: '', c: 'var(--brand-primary)', ch: '+12.5%' },
    { l: 'Settlements', v: 234000, p: '₹', s: '', c: 'var(--success)', ch: '+8.2%' },
    { l: 'Disputes Won', v: 85, p: '', s: '%', c: '#7c3aed', ch: '+5.1%' },
    { l: 'Time Saved', v: 168, p: '', s: 'h', c: 'var(--warning)', ch: '+23%' },
  ];
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {data.map((k, i) => {
        const val = useCounter(k.v);
        return (
          <motion.div key={k.l} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 + i * 0.06, duration: 0.5, ease: [0.23, 1, 0.32, 1] }}>
            <Card className="p-5 relative overflow-hidden">
              <div className="absolute top-0 left-0 right-0 h-[3px]" style={{ background: k.c, opacity: 0.8 }} />
              <p className="text-[11px] font-semibold uppercase tracking-wider mb-2" style={{ color: '#94a3b8' }}>{k.l}</p>
              <p className="text-2xl lg:text-3xl font-bold" style={{ color: '#0f172a' }}>{k.p}{val.toLocaleString('en-IN')}{k.s}</p>
              <span className="text-xs font-semibold" style={{ color: '#059669' }}>{k.ch}</span>
              <span className="text-[11px] ml-1" style={{ color: '#94a3b8' }}>this month</span>
            </Card>
          </motion.div>
        );
      })}
    </div>
  );
}

/* Revenue Chart */
function RevenueChart() {
  const [p, setP] = useState('year');
  return (
    <Card className="p-6 mb-6">
      <div className="flex items-center justify-between mb-5">
        <div>
          <p className="text-sm font-bold" style={{ color: '#0f172a' }}>Revenue Overview</p>
          <p className="text-xs mt-0.5" style={{ color: '#94a3b8' }}>Automated settlements & refunds</p>
        </div>
        <div className="flex gap-1 p-1 rounded-xl" style={{ background: '#f1f5f9', border: '1px solid #e2e8f0' }}>
          {['week', 'month', 'year'].map((t) => (
            <button key={t} onClick={() => setP(t)} className="px-3 py-1.5 rounded-lg text-[11px] font-semibold transition-all duration-200" style={{
              background: p === t ? '#2563eb' : 'transparent',
              color: p === t ? 'white' : '#94a3b8',
            }}>
              {t[0].toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>
      </div>
      <div className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={AREA_DATA}>
            <defs>
              <linearGradient id="rg" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#2563eb" stopOpacity={0.15} />
                <stop offset="100%" stopColor="#2563eb" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="eg" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#7c3aed" stopOpacity={0.08} />
                <stop offset="100%" stopColor="#7c3aed" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="m" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: 12, fontSize: 12, boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }} />
            <Area type="monotone" dataKey="rev" stroke="#2563eb" strokeWidth={2.5} fill="url(#rg)" />
            <Area type="monotone" dataKey="exp" stroke="#7c3aed" strokeWidth={2} fill="url(#eg)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <div className="flex items-center gap-6 mt-3">
        <div className="flex items-center gap-2"><div className="w-2.5 h-2.5 rounded-full" style={{ background: '#2563eb' }} /><span className="text-[11px]" style={{ color: 'var(--text-secondary)' }}>Revenue</span></div>
        <div className="flex items-center gap-2"><div className="w-2.5 h-2.5 rounded-full" style={{ background: '#7c3aed' }} /><span className="text-[11px]" style={{ color: 'var(--text-secondary)' }}>Expenses</span></div>
      </div>
    </Card>
  );
}

/* Daily + Donut */
function DailyDonut() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-6">
      <Card className="p-6">          <p className="text-sm font-bold mb-4" style={{ color: '#0f172a' }}>Daily Activity</p>
        <div className="h-32">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={BAR_DATA}>
              <defs>
                <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#2563eb" stopOpacity={0.85} />
                  <stop offset="100%" stopColor="#2563eb" stopOpacity={0.3} />
                </linearGradient>
              </defs>
              <XAxis dataKey="d" tick={{ fill: '#94a3b8', fontSize: 10 }} axisLine={false} tickLine={false} />
              <Bar dataKey="v" fill="url(#bg)" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <Card className="p-6">          <p className="text-sm font-bold mb-4" style={{ color: '#0f172a' }}>Asset Allocation</p>
        <div className="flex items-center gap-5">
          <div className="w-28 h-28">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={PIE} cx="50%" cy="50%" innerRadius={30} outerRadius={48} paddingAngle={3} dataKey="v" stroke="none">
                  {PIE.map((e, i) => <Cell key={i} fill={e.c} />)}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex-1 space-y-2.5">
            {PIE.map((d) => (
              <div key={d.n} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full" style={{ background: d.c }} />
                  <span className="text-xs" style={{ color: '#475569' }}>{d.n}</span>
                </div>
                <span className="text-xs font-semibold" style={{ color: '#0f172a' }}>{d.v}%</span>
              </div>
            ))}
          </div>
        </div>
      </Card>
    </div>
  );
}

/* Transactions */
function Transactions() {
  return (
    <Card className="p-6 mb-6">
      <div className="flex items-center justify-between mb-4">          <p className="text-sm font-bold" style={{ color: '#0f172a' }}>Recent Transactions</p>
        <button className="lf-btn lf-btn-ghost text-xs">View all →</button>
      </div>
      <div className="space-y-1">
        {TXS.map((tx, i) => (
          <motion.div key={tx.id} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.04 }}
            className="flex items-center gap-3 px-3 py-3 rounded-xl transition-colors cursor-pointer" style={{ background: 'transparent' }}
            onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-subtle)'}
            onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
          >
            <div className="w-9 h-9 rounded-xl flex items-center justify-center text-sm" style={{ background: `${tx.c}10` }}>{tx.icon}</div>
            <div className="flex-1 min-w-0">
              <p className="text-[13px] font-medium truncate" style={{ color: '#0f172a' }}>{tx.n}</p>
              <p className="text-[11px] truncate" style={{ color: '#94a3b8' }}>{tx.d}</p>
            </div>
            <div className="text-right flex-shrink-0">
              <p className="text-[13px] font-semibold" style={{ color: tx.t === 'credit' ? '#059669' : '#dc2626' }}>{tx.a}</p>
              <p className="text-[10px]" style={{ color: '#94a3b8' }}>{tx.time}</p>
            </div>
          </motion.div>
        ))}
      </div>
    </Card>
  );
}

/* AI Insights */
function Insights() {
  return (
    <Card className="p-6 mb-6">
      <div className="flex items-center gap-2 mb-4">          <div className="w-6 h-6 rounded-lg flex items-center justify-center text-[10px] text-white font-bold" style={{ background: 'linear-gradient(135deg, #2563eb, #7c3aed)' }}>AI</div>
        <p className="text-sm font-bold" style={{ color: '#0f172a' }}>AI Insights</p>
      </div>
      <div className="space-y-3">
        {AI.map((ins, i) => (
          <motion.div key={i} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 + i * 0.08 }}
            className="p-3.5 rounded-xl transition-all duration-200 cursor-pointer" style={{ border: '1px solid var(--border)' }}
            onMouseEnter={(e) => { e.currentTarget.style.borderColor = '#bfdbfe'; e.currentTarget.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.07)'; }}
            onMouseLeave={(e) => { e.currentTarget.style.borderColor = '#e2e8f0'; e.currentTarget.style.boxShadow = 'none'; }}
          >
            <div className="flex items-start gap-2.5">
              <span className="text-base mt-0.5">{ins.icon}</span>
              <div className="flex-1">
                <p className="text-[13px] font-semibold mb-0.5" style={{ color: '#0f172a' }}>{ins.title}</p>
                <p className="text-[11px] leading-relaxed" style={{ color: '#475569' }}>{ins.desc}</p>
              </div>
            </div>
            <div className="flex items-center gap-2 mt-2 ml-7">
              <div className="h-1 flex-1 rounded-full overflow-hidden" style={{ background: '#f1f5f9' }}>
                <div className="h-full rounded-full transition-all duration-500" style={{ width: `${ins.pct}%`, background: 'linear-gradient(90deg, #2563eb, #7c3aed)' }} />
              </div>
              <span className="text-[10px]" style={{ color: '#94a3b8' }}>{ins.pct}%</span>
            </div>
          </motion.div>
        ))}
      </div>
    </Card>
  );
}

/* Notifications */
function Notifications() {
  const items = [
    { t: 'Settlement #1848 routed to NEFT', time: '2m ago', r: false },
    { t: 'Dispute evidence submitted — 92% win rate', time: '15m ago', r: false },
    { t: 'Batch #89 completed — 12/12 optimal', time: '1h ago', r: true },
    { t: 'New processor: Stripe connected', time: '3h ago', r: true },
  ];
  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">          <p className="text-sm font-bold" style={{ color: '#0f172a' }}>Notifications</p>
        <span className="w-5 h-5 rounded-full text-white text-[10px] font-bold flex items-center justify-center" style={{ background: '#2563eb' }}>2</span>
      </div>
      <div className="space-y-2">
        {items.map((n, i) => (
          <div key={i} className="flex items-center gap-3 px-3 py-2.5 rounded-xl"            style={{ background: n.r ? 'transparent' : '#eff6ff',
            border: `1px solid ${n.r ? 'transparent' : '#dbeafe'}`,
          }}>
            <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: n.r ? 'transparent' : '#2563eb' }} />
            <p className="text-[12px] flex-1" style={{ color: n.r ? '#94a3b8' : '#475569' }}>{n.t}</p>
            <span className="text-[10px] flex-shrink-0" style={{ color: '#94a3b8' }}>{n.time}</span>
          </div>
        ))}
      </div>
    </Card>
  );
}

/* ============================================
   MAIN
   ============================================ */
export default function LightDashboard() {
  return (
    <div className="min-h-screen" style={{ background: 'var(--bg-page)' }}>
      <div className="p-6 lg:p-8 max-w-[1400px] mx-auto">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} className="flex items-center justify-between mb-6">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-widest" style={{ color: 'var(--text-muted)' }}>Good evening</p>
            <h1 className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>Command Center</h1>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full" style={{ background: '#ecfdf5', border: '1px solid rgba(5,150,105,0.12)' }}>
              <div className="w-1.5 h-1.5 rounded-full" style={{ background: '#059669', animation: 'lf-pulse-soft 2s infinite' }} />
              <span className="text-[11px] font-medium" style={{ color: '#059669' }}>All systems optimal</span>
            </div>
          </div>
        </motion.div>

        <Hero />
        <KPIs />
        <RevenueChart />
        <DailyDonut />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <Transactions />
          </div>
          <div>
            <Insights />
            <Notifications />
          </div>
        </div>
      </div>
    </div>
  );
}
