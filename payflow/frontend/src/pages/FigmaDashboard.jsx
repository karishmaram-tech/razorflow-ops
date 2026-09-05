import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { AreaChart, Area, BarChart, Bar, ResponsiveContainer, Tooltip, XAxis } from 'recharts';

/* ============================================
   ANIMATED COUNTER
   ============================================ */
function useCounter(target, duration = 1200) {
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
const SPARKLINE = Array.from({ length: 30 }, (_, i) => ({
  x: i, y: 30 + Math.sin(i * 0.3) * 15 + Math.random() * 10,
}));

const AREA_DATA = [
  { m: 'Jan', income: 4200, expense: 2800 }, { m: 'Feb', income: 5100, expense: 3200 },
  { m: 'Mar', income: 4800, expense: 2900 }, { m: 'Apr', income: 6200, expense: 3500 },
  { m: 'May', income: 7100, expense: 3100 }, { m: 'Jun', income: 6800, expense: 3800 },
  { m: 'Jul', income: 8200, expense: 3400 }, { m: 'Aug', income: 9100, expense: 3600 },
  { m: 'Sep', income: 8500, expense: 3200 }, { m: 'Oct', income: 9800, expense: 3900 },
  { m: 'Nov', income: 10200, expense: 3500 }, { m: 'Dec', income: 11500, expense: 3800 },
];

const BAR_DATA = [
  { d: 'Mon', v: 4200 }, { d: 'Tue', v: 3800 }, { d: 'Wed', v: 5100 },
  { d: 'Thu', v: 4600 }, { d: 'Fri', v: 6200 }, { d: 'Sat', v: 3100 }, { d: 'Sun', v: 2800 },
];

const TXS = [
  { id: 1, n: 'Apple Store', d: 'Subscription', a: '-$4.99', t: 'debit', time: 'Today', icon: '🍎', c: '#6366f1' },
  { id: 2, n: 'Salary Deposit', d: 'Monthly salary', a: '+$8,500', t: 'credit', time: 'Today', icon: '💼', c: '#10b981' },
  { id: 3, n: 'Spotify', d: 'Premium plan', a: '-$9.99', t: 'debit', time: 'Yesterday', icon: '🎵', c: '#8b5cf6' },
  { id: 4, n: 'Transfer from John', d: 'Dinner split', a: '+$35.00', t: 'credit', time: 'Yesterday', icon: '👤', c: '#3b82f6' },
  { id: 5, n: 'Amazon', d: 'Electronics', a: '-$129.99', t: 'debit', time: '2 days ago', icon: '📦', c: '#f59e0b' },
  { id: 6, n: 'Freelance Payment', d: 'Project milestone', a: '+$2,400', t: 'credit', time: '3 days ago', icon: '💻', c: '#06b6d4' },
  { id: 7, n: 'Uber', d: 'Ride to airport', a: '-$24.50', t: 'debit', time: '3 days ago', icon: '🚗', c: '#ec4899' },
];

const CARDS_DATA = [
  { id: 1, name: 'Visa Platinum', number: '•••• 4829', balance: '$12,450', color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', expiry: '12/26' },
  { id: 2, name: 'Mastercard Gold', number: '•••• 7631', balance: '$8,320', color: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', expiry: '08/27' },
];

const QUICK_ACTIONS = [
  { icon: '↑', label: 'Send', color: '#6366f1' },
  { icon: '↓', label: 'Receive', color: '#10b981' },
  { icon: '🔄', label: 'Swap', color: '#f59e0b' },
  { icon: '📊', label: 'Invest', color: '#ec4899' },
];

/* ============================================
   ANIMATION VARIANTS
   ============================================ */
const fadeUp = { hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.23, 1, 0.32, 1] } } };

/* ============================================
   SIDEBAR
   ============================================ */
function Sidebar({ collapsed, onToggle }) {
  const [active, setActive] = useState('/');
  const nav = [
    { to: '/', label: 'Overview', icon: '🏠' },
    { to: '/analytics', label: 'Analytics', icon: '📊' },
    { to: '/wallet', label: 'My Wallet', icon: '💳' },
    { to: '/transactions', label: 'Transactions', icon: '📋' },
    { to: '/cards', label: 'Cards', icon: '🃏' },
    { to: '/settings', label: 'Settings', icon: '⚙️' },
  ];

  return (
    <aside style={{
      width: collapsed ? '72px' : '260px',
      background: 'rgba(15, 22, 41, 0.95)',
      borderRight: '1px solid rgba(99, 102, 241, 0.1)',
      padding: collapsed ? '24px 12px' : '24px 16px',
      display: 'flex',
      flexDirection: 'column',
      position: 'sticky',
      top: 0,
      height: '100vh',
      backdropFilter: 'blur(20px)',
      flexShrink: 0,
      transition: 'width 0.3s ease, padding 0.3s ease',
      overflow: 'hidden',
    }}>
      {/* Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '32px', padding: '0 4px', justifyContent: collapsed ? 'center' : 'flex-start' }}>
        <div style={{
          width: '40px', height: '40px', flexShrink: 0,
          background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a78bfa 100%)',
          borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '18px', fontWeight: 700, color: 'white',
          boxShadow: '0 4px 12px rgba(99, 102, 241, 0.3)',
        }}>⚡</div>
        {!collapsed && <span style={{ fontSize: '18px', fontWeight: 700, color: '#f1f5f9', letterSpacing: '-0.3px', whiteSpace: 'nowrap' }}>PayFlow</span>}
      </div>

      {/* Search */}
      {!collapsed && (
        <div style={{
          padding: '10px 12px', borderRadius: '10px',
          background: 'rgba(51, 65, 85, 0.3)', border: '1px solid rgba(99, 102, 241, 0.08)',
          display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '24px', cursor: 'pointer',
        }}>
          <span style={{ color: '#64748b', fontSize: '14px' }}>🔍</span>
          <span style={{ color: '#64748b', fontSize: '13px' }}>Search...</span>
          <span style={{ marginLeft: 'auto', fontSize: '10px', padding: '2px 6px', borderRadius: '4px', background: 'rgba(99, 102, 241, 0.15)', color: '#a78bfa', fontWeight: 600 }}>⌘K</span>
        </div>
      )}

      {/* Navigation */}
      <div style={{ marginBottom: '24px' }}>
        {!collapsed && <div style={{ fontSize: '10px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '1.2px', color: '#64748b', padding: '0 12px', marginBottom: '8px' }}>Menu</div>}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
          {nav.map((item) => (
            <div
              key={item.to}
              style={{
                display: 'flex', alignItems: 'center', gap: '12px',
                padding: collapsed ? '10px 0' : '10px 12px',
                borderRadius: '10px', fontSize: '13px', fontWeight: 500,
                color: active === item.to ? '#a78bfa' : '#94a3b8',
                background: active === item.to ? 'rgba(99, 102, 241, 0.1)' : 'transparent',
                border: active === item.to ? '1px solid rgba(99, 102, 241, 0.2)' : '1px solid transparent',
                cursor: 'pointer', transition: 'all 0.2s ease',
                justifyContent: collapsed ? 'center' : 'flex-start',
              }}
              onClick={() => setActive(item.to)}
              title={collapsed ? item.label : undefined}
            >
              <span style={{ fontSize: '16px', flexShrink: 0 }}>{item.icon}</span>
              {!collapsed && <span style={{ whiteSpace: 'nowrap' }}>{item.label}</span>}
            </div>
          ))}
        </div>
      </div>

      <div style={{ flex: 1 }} />

      {/* Upgrade Card */}
      {!collapsed && (
        <div style={{
          background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.15) 100%)',
          border: '1px solid rgba(99, 102, 241, 0.2)', borderRadius: '12px', padding: '16px', marginBottom: '16px',
        }}>
          <p style={{ fontSize: '12px', fontWeight: 600, color: '#a78bfa', marginBottom: '4px' }}>Upgrade to Pro</p>
          <p style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '12px' }}>Get unlimited transfers and premium features</p>
          <button style={{
            padding: '8px 16px', borderRadius: '10px', border: 'none', fontSize: '12px', fontWeight: 600, cursor: 'pointer',
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', color: 'white', width: '100%',
          }}>Upgrade Now</button>
        </div>
      )}

      {/* User */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '8px', justifyContent: collapsed ? 'center' : 'flex-start' }}>
        <div style={{
          width: '36px', height: '36px', borderRadius: '10px', flexShrink: 0,
          background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: 'white', fontWeight: 700, fontSize: '14px',
        }}>K</div>
        {!collapsed && (
          <div style={{ flex: 1 }}>
            <p style={{ fontSize: '13px', fontWeight: 600, color: '#f1f5f9' }}>Karishma</p>
            <p style={{ fontSize: '11px', color: '#64748b' }}>karishma@payflow.io</p>
          </div>
        )}
      </div>
    </aside>
  );
}

/* ============================================
   HERO BALANCE CARD
   ============================================ */
function HeroBalance() {
  const bal = useCounter(24394);
  return (
    <motion.div variants={fadeUp} style={{
      background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 40%, #a78bfa 100%)',
      borderRadius: '20px', padding: '28px', position: 'relative', overflow: 'hidden',
      marginBottom: '24px', boxShadow: '0 8px 32px rgba(99, 102, 241, 0.25)',
    }}>
      <div style={{ position: 'absolute', top: '-40px', right: '-40px', width: '200px', height: '200px', borderRadius: '50%', background: 'radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%)' }} />
      <div style={{ position: 'absolute', bottom: '-60px', left: '30%', width: '160px', height: '160px', borderRadius: '50%', background: 'radial-gradient(circle, rgba(255,255,255,0.06) 0%, transparent 70%)' }} />

      <div style={{ position: 'relative' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <p style={{ fontSize: '12px', color: 'rgba(255,255,255,0.7)', marginBottom: '8px', fontWeight: 500 }}>Total Balance</p>
            <p style={{ fontSize: 'clamp(28px, 5vw, 42px)', fontWeight: 700, color: 'white', letterSpacing: '-1px', lineHeight: 1 }}>
              ${bal.toLocaleString()}<span style={{ fontSize: 'clamp(16px, 3vw, 24px)', opacity: 0.7 }}>.94</span>
            </p>
          </div>
          <div style={{ padding: '6px 12px', background: 'rgba(16, 185, 129, 0.2)', borderRadius: '20px', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ color: '#34d399', fontSize: '12px' }}>↑</span>
            <span style={{ color: '#34d399', fontSize: '12px', fontWeight: 600 }}>+12.5%</span>
          </div>
        </div>

        <div style={{ height: '60px', marginBottom: '20px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={SPARKLINE}>
              <defs>
                <linearGradient id="heroSpark" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="white" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="white" stopOpacity={0} />
                </linearGradient>
              </defs>
              <Area type="monotone" dataKey="y" stroke="rgba(255,255,255,0.6)" strokeWidth={2} fill="url(#heroSpark)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px' }}>
          {QUICK_ACTIONS.map((a) => (
            <button key={a.label} style={{
              padding: '12px 8px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.15)',
              background: 'rgba(255,255,255,0.1)', backdropFilter: 'blur(10px)',
              color: 'white', fontSize: '11px', fontWeight: 600, cursor: 'pointer',
              display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px',
              transition: 'all 0.2s ease',
            }}
              onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.2)'; e.currentTarget.style.transform = 'translateY(-2px)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.1)'; e.currentTarget.style.transform = 'translateY(0)'; }}
            >
              <span style={{ fontSize: '18px' }}>{a.icon}</span>
              <span>{a.label}</span>
            </button>
          ))}
        </div>
      </div>
    </motion.div>
  );
}

/* ============================================
   KPI CARDS
   ============================================ */
function KPICards() {
  const data = [
    { label: 'Income', value: 8500, prefix: '$', change: '+2.4%', positive: true, color: '#10b981', icon: '📈' },
    { label: 'Expenses', value: 3200, prefix: '$', change: '-1.2%', positive: true, color: '#f59e0b', icon: '📉' },
    { label: 'Savings', value: 5300, prefix: '$', change: '+8.1%', positive: true, color: '#6366f1', icon: '🏦' },
    { label: 'Investments', value: 12400, prefix: '$', change: '+15.3%', positive: true, color: '#ec4899', icon: '📊' },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {data.map((k, i) => {
        const val = useCounter(k.value);
        return (
          <motion.div
            key={k.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 + i * 0.08, duration: 0.5, ease: [0.23, 1, 0.32, 1] }}
            className="p-5 rounded-2xl backdrop-blur-sm"
            style={{
              background: 'rgba(30, 41, 59, 0.5)',
              border: '1px solid rgba(99, 102, 241, 0.08)',
              transition: 'all 0.25s cubic-bezier(0.23, 1, 0.32, 1)',
              cursor: 'pointer',
            }}
            onMouseEnter={(e) => { e.currentTarget.style.borderColor = `${k.color}40`; e.currentTarget.style.transform = 'translateY(-2px)'; }}
            onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'rgba(99, 102, 241, 0.08)'; e.currentTarget.style.transform = 'translateY(0)'; }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
              <p style={{ fontSize: '12px', color: '#94a3b8', fontWeight: 500 }}>{k.label}</p>
              <div style={{
                width: '32px', height: '32px', borderRadius: '8px', flexShrink: 0,
                background: `${k.color}15`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '14px',
              }}>{k.icon}</div>
            </div>
            <p style={{ fontSize: '22px', fontWeight: 700, color: '#f1f5f9', marginBottom: '4px' }}>
              {k.prefix}{val.toLocaleString()}
            </p>
            <span style={{ fontSize: '11px', color: k.positive ? '#10b981' : '#ef4444', fontWeight: 600 }}>
              {k.change} <span style={{ color: '#64748b', fontWeight: 400 }}>vs last month</span>
            </span>
          </motion.div>
        );
      })}
    </div>
  );
}

/* ============================================
   CREDIT CARDS
   ============================================ */
function CreditCards() {
  const [activeCard, setActiveCard] = useState(0);
  return (
    <motion.div variants={fadeUp} style={{ background: 'rgba(30, 41, 59, 0.5)', border: '1px solid rgba(99, 102, 241, 0.08)', borderRadius: '16px', padding: '24px', backdropFilter: 'blur(10px)', marginBottom: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <p style={{ fontSize: '15px', fontWeight: 600, color: '#f1f5f9' }}>My Cards</p>
        <button style={{ padding: '6px 14px', borderRadius: '8px', border: '1px solid rgba(99, 102, 241, 0.2)', background: 'rgba(99, 102, 241, 0.1)', color: '#a78bfa', fontSize: '12px', fontWeight: 600, cursor: 'pointer' }}>+ Add Card</button>
      </div>
      <div style={{ display: 'flex', gap: '16px', overflowX: 'auto', paddingBottom: '8px' }}>
        {CARDS_DATA.map((card, i) => (
          <motion.div key={card.id} whileHover={{ scale: 1.02, y: -4 }} whileTap={{ scale: 0.98 }}
            style={{
              minWidth: '260px', padding: '24px', borderRadius: '16px', background: card.color,
              cursor: 'pointer', position: 'relative', overflow: 'hidden',
              boxShadow: activeCard === i ? '0 8px 24px rgba(99, 102, 241, 0.3)' : '0 4px 12px rgba(0, 0, 0, 0.2)',
              border: activeCard === i ? '2px solid rgba(255,255,255,0.3)' : '2px solid transparent',
            }}
            onClick={() => setActiveCard(i)}
          >
            <div style={{ position: 'absolute', top: '-20px', right: '-20px', width: '100px', height: '100px', borderRadius: '50%', background: 'rgba(255,255,255,0.1)' }} />
            <div style={{ position: 'relative' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '32px' }}>
                <p style={{ fontSize: '14px', fontWeight: 600, color: 'white' }}>{card.name}</p>
                <span style={{ fontSize: '20px' }}>💳</span>
              </div>
              <p style={{ fontSize: '18px', fontWeight: 600, color: 'white', letterSpacing: '2px', marginBottom: '16px' }}>{card.number}</p>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
                <div>
                  <p style={{ fontSize: '10px', color: 'rgba(255,255,255,0.6)', marginBottom: '2px' }}>Balance</p>
                  <p style={{ fontSize: '20px', fontWeight: 700, color: 'white' }}>{card.balance}</p>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <p style={{ fontSize: '10px', color: 'rgba(255,255,255,0.6)', marginBottom: '2px' }}>Expires</p>
                  <p style={{ fontSize: '13px', fontWeight: 600, color: 'white' }}>{card.expiry}</p>
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}

/* ============================================
   CHARTS ROW
   ============================================ */
function ChartsRow() {
  const [period, setPeriod] = useState('Month');
  return (
    <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 mb-6">
      {/* Area Chart */}
      <motion.div variants={fadeUp} className="lg:col-span-3 p-6 rounded-2xl" style={{ background: 'rgba(30, 41, 59, 0.5)', border: '1px solid rgba(99, 102, 241, 0.08)', backdropFilter: 'blur(10px)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '8px' }}>
          <div>
            <p style={{ fontSize: '15px', fontWeight: 600, color: '#f1f5f9', marginBottom: '2px' }}>Income Overview</p>
            <p style={{ fontSize: '12px', color: '#64748b' }}>Revenue & expenses</p>
          </div>
          <div style={{ display: 'flex', gap: '4px', padding: '3px', background: 'rgba(51, 65, 85, 0.3)', borderRadius: '8px' }}>
            {['Week', 'Month', 'Year'].map((t) => (
              <button key={t} onClick={() => setPeriod(t)} style={{
                padding: '6px 12px', borderRadius: '6px', border: 'none', fontSize: '11px', fontWeight: 600, cursor: 'pointer',
                background: period === t ? '#6366f1' : 'transparent', color: period === t ? 'white' : '#64748b', transition: 'all 0.2s',
              }}>{t}</button>
            ))}
          </div>
        </div>
        <div style={{ height: '200px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={AREA_DATA}>
              <defs>
                <linearGradient id="incomeGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#6366f1" stopOpacity={0.3} /><stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="expenseGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#ec4899" stopOpacity={0.15} /><stop offset="100%" stopColor="#ec4899" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="m" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ background: 'rgba(30, 41, 59, 0.95)', border: '1px solid rgba(99, 102, 241, 0.2)', borderRadius: 10, fontSize: 12, color: '#e2e8f0', boxShadow: '0 8px 24px rgba(0,0,0,0.3)' }} />
              <Area type="monotone" dataKey="income" stroke="#6366f1" strokeWidth={2.5} fill="url(#incomeGrad)" />
              <Area type="monotone" dataKey="expense" stroke="#ec4899" strokeWidth={2} fill="url(#expenseGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
        <div style={{ display: 'flex', gap: '20px', marginTop: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><div style={{ width: 8, height: 8, borderRadius: '50%', background: '#6366f1' }} /><span style={{ fontSize: 11, color: '#94a3b8' }}>Income</span></div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><div style={{ width: 8, height: 8, borderRadius: '50%', background: '#ec4899' }} /><span style={{ fontSize: 11, color: '#94a3b8' }}>Expenses</span></div>
        </div>
      </motion.div>

      {/* Bar Chart */}
      <motion.div variants={fadeUp} className="lg:col-span-2 p-6 rounded-2xl" style={{ background: 'rgba(30, 41, 59, 0.5)', border: '1px solid rgba(99, 102, 241, 0.08)', backdropFilter: 'blur(10px)' }}>
        <p style={{ fontSize: '15px', fontWeight: 600, color: '#f1f5f9', marginBottom: '16px' }}>Weekly Activity</p>
        <div style={{ height: '200px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={BAR_DATA}>
              <defs>
                <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#6366f1" stopOpacity={0.9} /><stop offset="100%" stopColor="#6366f1" stopOpacity={0.3} />
                </linearGradient>
              </defs>
              <XAxis dataKey="d" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ background: 'rgba(30, 41, 59, 0.95)', border: '1px solid rgba(99, 102, 241, 0.2)', borderRadius: 10, fontSize: 12, color: '#e2e8f0' }} />
              <Bar dataKey="v" fill="url(#barGrad)" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </motion.div>
    </div>
  );
}

/* ============================================
   TRANSACTIONS
   ============================================ */
function Transactions() {
  return (
    <motion.div variants={fadeUp} className="p-6 rounded-2xl" style={{ background: 'rgba(30, 41, 59, 0.5)', border: '1px solid rgba(99, 102, 241, 0.08)', backdropFilter: 'blur(10px)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <p style={{ fontSize: '15px', fontWeight: 600, color: '#f1f5f9' }}>Recent Transactions</p>
        <button style={{ padding: '6px 14px', borderRadius: '8px', border: 'none', background: 'transparent', color: '#a78bfa', fontSize: '12px', fontWeight: 600, cursor: 'pointer' }}>View All →</button>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {TXS.map((tx, i) => (
          <motion.div key={tx.id} initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }}
            style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '12px', borderRadius: '12px', cursor: 'pointer', transition: 'background 0.2s' }}
            onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(51, 65, 85, 0.3)'; }}
            onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
          >
            <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: `${tx.c}15`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '18px', flexShrink: 0 }}>{tx.icon}</div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <p style={{ fontSize: '13px', fontWeight: 600, color: '#f1f5f9', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{tx.n}</p>
              <p style={{ fontSize: '11px', color: '#64748b' }}>{tx.d}</p>
            </div>
            <div style={{ textAlign: 'right', flexShrink: 0 }}>
              <p style={{ fontSize: '13px', fontWeight: 600, color: tx.t === 'credit' ? '#10b981' : '#ef4444' }}>{tx.a}</p>
              <p style={{ fontSize: '10px', color: '#64748b' }}>{tx.time}</p>
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}

/* ============================================
   MAIN DASHBOARD
   ============================================ */
export default function FigmaDashboard() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div style={{ background: '#0f1629', minHeight: '100vh', fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif", color: '#e2e8f0' }}>
      <div style={{ display: 'flex', minHeight: '100vh' }}>
        <Sidebar collapsed={sidebarCollapsed} onToggle={() => setSidebarCollapsed(!sidebarCollapsed)} />
        <main style={{ flex: 1, padding: '24px 28px', overflowY: 'auto', minWidth: 0 }}>
          {/* Header */}
          <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
            style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <p style={{ fontSize: '11px', color: '#64748b', fontWeight: 500, marginBottom: '4px' }}>Welcome back,</p>
              <h1 style={{ fontSize: '22px', fontWeight: 700, color: '#f1f5f9', letterSpacing: '-0.5px' }}>Karishma 👋</h1>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{ padding: '5px 10px', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.2)', borderRadius: '20px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#10b981', animation: 'pulse 2s infinite' }} />
                <span style={{ fontSize: '11px', color: '#10b981', fontWeight: 600 }}>All systems operational</span>
              </div>
              <div style={{ width: 36, height: 36, borderRadius: 10, background: 'rgba(51, 65, 85, 0.3)', border: '1px solid rgba(99, 102, 241, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', fontSize: 16 }}>🔔</div>
            </div>
          </motion.div>

          <HeroBalance />
          <KPICards />
          <CreditCards />
          <ChartsRow />
          <Transactions />
        </main>
      </div>
      <style>{`@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }`}</style>
    </div>
  );
}
