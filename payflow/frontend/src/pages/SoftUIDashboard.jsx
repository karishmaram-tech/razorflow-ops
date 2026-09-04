import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  TrendingUp, TrendingDown, CreditCard, Receipt,
  Users, DollarSign, ArrowUpRight, ArrowDownRight,
  Settings, Home, BarChart3, Bell, Search, Zap
} from 'lucide-react';

/* ============================================
   SOFT UI DESIGN TOKENS
   ============================================ */
const neu = {
  bg: '#e0e5ec',
  light: 'rgba(255, 255, 255, 0.85)',
  dark: 'rgba(163, 177, 198, 0.60)',
  text: '#4a5568',
  muted: '#8896ab',
  accent: '#7c6fff',
  raised: '-6px -6px 14px rgba(255, 255, 255, 0.85), 6px 6px 14px rgba(163, 177, 198, 0.60)',
  raisedLg: '-8px -8px 20px rgba(255, 255, 255, 0.9), 8px 8px 20px rgba(163, 177, 198, 0.65)',
  pressed: 'inset 4px 4px 10px rgba(163, 177, 198, 0.60), inset -4px -4px 10px rgba(255, 255, 255, 0.85)',
  floating: '-10px -10px 24px rgba(255, 255, 255, 0.95), 10px 10px 24px rgba(163, 177, 198, 0.70)',
};

/* ============================================
   KPI CARD DATA
   ============================================ */
const KPI_DATA = [
  {
    label: 'Total Revenue',
    value: '₹3,43,800',
    change: '+12.5%',
    trend: 'up',
    icon: DollarSign,
    gradient: 'linear-gradient(135deg, #667eea, #764ba2)',
  },
  {
    label: 'Settlements',
    value: '₹2,34,000',
    change: '+8.2%',
    trend: 'up',
    icon: CreditCard,
    gradient: 'linear-gradient(135deg, #f093fb, #f5576c)',
  },
  {
    label: 'Refunds',
    value: '₹51,500',
    change: '-3.1%',
    trend: 'down',
    icon: Receipt,
    gradient: 'linear-gradient(135deg, #4facfe, #00f2fe)',
  },
  {
    label: 'Active Users',
    value: '2,451',
    change: '+18.7%',
    trend: 'up',
    icon: Users,
    gradient: 'linear-gradient(135deg, #43e97b, #38f9d7)',
  },
];

/* ============================================
   TRANSACTIONS
   ============================================ */
const TRANSACTIONS = [
  { id: 1, name: 'Settlement NEFT', amount: '+₹12,400', time: '2 min ago', color: '#43e97b' },
  { id: 2, name: 'Refund Processed', amount: '-₹3,200', time: '15 min ago', color: '#f5576c' },
  { id: 3, name: 'Dispute Won', amount: '+₹8,500', time: '1 hr ago', color: '#667eea' },
  { id: 4, name: 'Processor Fee', amount: '-₹180', time: '3 hr ago', color: '#f093fb' },
  { id: 5, name: 'Settlement Batch', amount: '+₹45,000', time: '4 hr ago', color: '#4facfe' },
];

/* ============================================
   NEU COMPONENTS
   ============================================ */
function NeuCard({ children, className = '', style = {}, pressed = false }) {
  return (
    <div
      className={`rounded-2xl ${className}`}
      style={{
        background: neu.bg,
        boxShadow: pressed ? neu.pressed : neu.raised,
        ...style,
      }}
    >
      {children}
    </div>
  );
}

function NeuButton({ children, onClick, active = false, className = '' }) {
  const [isPressed, setIsPressed] = useState(false);

  return (
    <button
      onClick={onClick}
      onMouseDown={() => setIsPressed(true)}
      onMouseUp={() => setIsPressed(false)}
      onMouseLeave={() => setIsPressed(false)}
      className={`rounded-xl px-5 py-3 font-semibold text-sm transition-all duration-150 ${className}`}
      style={{
        background: neu.bg,
        color: isPressed || active ? neu.accent : neu.text,
        boxShadow: isPressed ? neu.pressed : neu.raised,
        border: 'none',
        cursor: 'pointer',
      }}
    >
      {children}
    </button>
  );
}

function NeuInput({ placeholder = 'Search...', icon: Icon }) {
  return (
    <div className="relative">
      {Icon && (
        <Icon className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: neu.muted }} />
      )}
      <input
        type="text"
        placeholder={placeholder}
        className="w-full rounded-xl py-3 text-sm outline-none"
        style={{
          background: neu.bg,
          color: neu.text,
          boxShadow: neu.pressed,
          border: 'none',
          paddingLeft: Icon ? '42px' : '18px',
          paddingRight: '18px',
        }}
      />
    </div>
  );
}

/* ============================================
   KPI CARD
   ============================================ */
function KPICard({ data, index }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1, type: 'spring', damping: 20 }}
    >
      <NeuCard className="p-5 overflow-hidden relative" style={{ minHeight: '140px' }}>
        {/* Gradient accent stripe */}
        <div
          className="absolute top-0 left-0 w-full h-1 rounded-t-2xl"
          style={{ background: data.gradient }}
        />

        <div className="flex items-start justify-between mb-4">
          <div className="w-11 h-11 rounded-xl flex items-center justify-center text-white"
            style={{ background: data.gradient, boxShadow: `0 4px 15px ${data.gradient.includes('#667eea') ? 'rgba(102, 126, 234, 0.4)' : data.gradient.includes('#f093fb') ? 'rgba(240, 147, 251, 0.4)' : data.gradient.includes('#4facfe') ? 'rgba(79, 172, 254, 0.4)' : 'rgba(67, 233, 123, 0.4)'}` }}>
            <data.icon className="w-5 h-5" />
          </div>
          <div className="flex items-center gap-1 text-xs font-semibold"
            style={{ color: data.trend === 'up' ? '#43e97b' : '#f5576c' }}>
            {data.trend === 'up' ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
            {data.change}
          </div>
        </div>

        <p className="text-xs font-semibold uppercase tracking-wider mb-1" style={{ color: neu.muted }}>
          {data.label}
        </p>
        <p className="text-2xl font-bold" style={{ color: neu.text }}>
          {data.value}
        </p>
      </NeuCard>
    </motion.div>
  );
}

/* ============================================
   SIDEBAR
   ============================================ */
function Sidebar() {
  const [active, setActive] = useState('dashboard');

  const items = [
    { id: 'dashboard', label: 'Dashboard', icon: Home },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'billing', label: 'Billing', icon: CreditCard },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <div
      className="w-64 min-h-screen p-5 flex flex-col"
      style={{ background: neu.bg, boxShadow: `${neu.raised} inset` }}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 mb-10 px-2">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold text-lg"
          style={{ background: 'linear-gradient(135deg, #667eea, #764ba2)', boxShadow: '0 4px 15px rgba(102, 126, 234, 0.4)' }}
        >
          ⚡
        </div>
        <div>
          <span className="text-sm font-bold" style={{ color: neu.text }}>PayFlow</span>
          <p className="text-[10px]" style={{ color: neu.muted }}>Command Center</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 space-y-2">
        {items.map((item) => (
          <button
            key={item.id}
            onClick={() => setActive(item.id)}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-150 text-left"
            style={{
              background: neu.bg,
              color: active === item.id ? neu.accent : neu.muted,
              boxShadow: active === item.id ? neu.pressed : 'none',
              border: 'none',
              cursor: 'pointer',
            }}
          >
            <item.icon className="w-4 h-4" />
            {item.label}
          </button>
        ))}
      </nav>

      {/* Status */}
      <NeuCard pressed className="p-3 mt-4">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full" style={{ background: '#43e97b' }} />
          <span className="text-xs font-medium" style={{ color: '#43e97b' }}>All systems optimal</span>
        </div>
      </NeuCard>
    </div>
  );
}

/* ============================================
   CHART
   ============================================ */
function SpendingChart() {
  const days = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];
  const values = [65, 40, 80, 55, 90, 35, 70];
  const max = Math.max(...values);

  return (
    <NeuCard className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <p className="text-sm font-bold" style={{ color: neu.text }}>Revenue Overview</p>
          <p className="text-xs" style={{ color: neu.muted }}>Weekly performance</p>
        </div>
        <div className="flex gap-2">
          <NeuButton active>Week</NeuButton>
          <NeuButton>Month</NeuButton>
        </div>
      </div>

      <div className="flex items-end justify-between gap-3 h-40">
        {days.map((day, i) => (
          <div key={i} className="flex-1 flex flex-col items-center gap-2">
            <div
              className="w-full rounded-xl transition-all duration-500"
              style={{
                height: `${(values[i] / max) * 100}%`,
                background: i === 4
                  ? 'linear-gradient(180deg, #667eea, #764ba2)'
                  : `linear-gradient(180deg, rgba(124, 111, 255, 0.2), rgba(124, 111, 255, 0.05))`,
                boxShadow: i === 4 ? '0 4px 15px rgba(102, 126, 234, 0.3)' : 'none',
              }}
            />
            <span className="text-[10px] font-semibold" style={{ color: i === 4 ? neu.accent : neu.muted }}>
              {day}
            </span>
          </div>
        ))}
      </div>
    </NeuCard>
  );
}

/* ============================================
   TRANSACTIONS LIST
   ============================================ */
function TransactionList() {
  return (
    <NeuCard className="p-6">
      <div className="flex items-center justify-between mb-5">
        <div>
          <p className="text-sm font-bold" style={{ color: neu.text }}>Recent Transactions</p>
          <p className="text-xs" style={{ color: neu.muted }}>Last 24 hours</p>
        </div>
        <NeuButton>View All</NeuButton>
      </div>

      <div className="space-y-3">
        {TRANSACTIONS.map((tx, i) => (
          <motion.div
            key={tx.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.1 }}
          >
            <NeuCard className="p-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center"
                  style={{
                    background: neu.bg,
                    boxShadow: neu.pressed,
                  }}
                >
                  <div className="w-3 h-3 rounded-full" style={{ background: tx.color }} />
                </div>
                <div>
                  <p className="text-sm font-semibold" style={{ color: neu.text }}>{tx.name}</p>
                  <p className="text-xs" style={{ color: neu.muted }}>{tx.time}</p>
                </div>
              </div>
              <span className="text-sm font-bold" style={{ color: tx.amount.startsWith('+') ? '#43e97b' : '#f5576c' }}>
                {tx.amount}
              </span>
            </NeuCard>
          </motion.div>
        ))}
      </div>
    </NeuCard>
  );
}

/* ============================================
   MAIN DASHBOARD
   ============================================ */
export default function SoftUIDashboard() {
  return (
    <div className="flex min-h-screen" style={{ background: neu.bg }}>
      <Sidebar />

      <div className="flex-1 p-8 overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest mb-1" style={{ color: neu.muted }}>
              Welcome back
            </p>
            <h1 className="text-2xl font-bold" style={{ color: neu.text }}>Command Center</h1>
          </div>
          <div className="w-72">
            <NeuInput placeholder="Search..." icon={Search} />
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {KPI_DATA.map((kpi, i) => (
            <KPICard key={kpi.label} data={kpi} index={i} />
          ))}
        </div>

        {/* Chart + Transactions */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <SpendingChart />
          </div>
          <div>
            <TransactionList />
          </div>
        </div>
      </div>
    </div>
  );
}
