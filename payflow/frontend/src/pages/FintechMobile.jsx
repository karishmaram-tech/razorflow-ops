import { useState } from 'react';
import {
  Wallet, TrendingUp, ArrowDownRight, ArrowUpRight,
  CreditCard, Send, Receipt, BarChart3, Eye, EyeOff,
  ChevronRight, Sparkles, Shield, Zap
} from 'lucide-react';
import Text3DFlip from '../components/magicui/text-3d-flip';

const TRANSACTIONS = [
  { id: 1, title: 'Settlement NEFT', subtitle: 'Auto-routed by PayFlow', amount: '+₹12,400', type: 'credit', time: '2 min ago', icon: '⚡' },
  { id: 2, title: 'Refund Processed', subtitle: 'Refund #4521 routed', amount: '-₹3,200', type: 'debit', time: '15 min ago', icon: '💰' },
  { id: 3, title: 'Dispute Won', subtitle: 'Chargeback #2891', amount: '+₹8,500', type: 'credit', time: '1 hr ago', icon: '🛡️' },
  { id: 4, title: 'Settlement Batch', subtitle: 'Batch #89 processed', amount: '+₹45,000', type: 'credit', time: '2 hr ago', icon: '⚡' },
  { id: 5, title: 'Processor Fee', subtitle: 'Razorpay processing', amount: '-₹180', type: 'debit', time: '3 hr ago', icon: '💳' },
];

const ASSETS = [
  { name: 'Settlements', value: 68, color: '#06b6d4', amount: '₹2,34,000' },
  { name: 'Refunds', value: 15, color: '#8b5cf6', amount: '₹51,500' },
  { name: 'Disputes', value: 12, color: '#10b981', amount: '₹41,200' },
  { name: 'Fees', value: 5, color: '#f59e0b', amount: '₹17,100' },
];

const QUICK_ACTIONS = [
  { label: 'Send', icon: Send, color: 'from-cyan-500 to-blue-600' },
  { label: 'Request', icon: ArrowDownRight, color: 'from-violet-500 to-purple-600' },
  { label: 'Pay', icon: CreditCard, color: 'from-emerald-500 to-green-600' },
  { label: 'More', icon: Receipt, color: 'from-amber-500 to-orange-600' },
];

function BalanceCard() {
  const [showBalance, setShowBalance] = useState(true);
  
  return (
    <div className="relative overflow-hidden rounded-3xl p-6 mx-4 mb-6" style={{
      background: 'linear-gradient(135deg, #0e7490 0%, #0891b2 30%, #06b6d4 60%, #22d3ee 100%)',
      boxShadow: '0 8px 32px rgba(6, 182, 212, 0.3)',
    }}>
      {/* Background decoration */}
      <div className="absolute top-0 right-0 w-48 h-48 rounded-full opacity-10"
        style={{ background: 'radial-gradient(circle, white 0%, transparent 70%)', transform: 'translate(30%, -30%)' }}
      />
      <div className="absolute bottom-0 left-0 w-32 h-32 rounded-full opacity-10"
        style={{ background: 'radial-gradient(circle, white 0%, transparent 70%)', transform: 'translate(-20%, 20%)' }}
      />
      
      <div className="relative">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center backdrop-blur-sm">
              <Wallet className="w-4 h-4 text-white" />
            </div>
            <span className="text-sm font-medium text-white/80">PayFlow Balance</span>
          </div>
          <button onClick={() => setShowBalance(!showBalance)} className="text-white/70 hover:text-white transition-colors">
            {showBalance ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
          </button>
        </div>
        
        <div className="mb-6">
          {showBalance ? (
            <Text3DFlip
              className="text-4xl font-bold text-white tracking-tight"
              textClassName="text-4xl font-bold text-white tracking-tight"
              flipTextClassName="text-4xl font-bold text-white tracking-tight"
              rotateDirection="top"
              staggerDuration={0.02}
              staggerFrom="first"
              transition={{ type: 'spring', damping: 20, stiffness: 150 }}
            >
              ₹3,43,800
            </Text3DFlip>
          ) : (
            <p className="text-4xl font-bold text-white tracking-tight">••••••••</p>
          )}
          <div className="flex items-center gap-2 mt-2">
            <TrendingUp className="w-3.5 h-3.5 text-emerald-300" />
            <span className="text-xs text-white/70">
              <span className="text-emerald-300 font-semibold">+12.5%</span> from last month
            </span>
          </div>
        </div>
        
        <div className="flex gap-3">
          {QUICK_ACTIONS.map((action) => (
            <button key={action.label} className="flex-1 flex flex-col items-center gap-1.5 py-3 rounded-2xl bg-white/10 hover:bg-white/20 backdrop-blur-sm transition-all duration-200 active:scale-95">
              <div className={`w-9 h-9 rounded-xl bg-gradient-to-br ${action.color} flex items-center justify-center shadow-lg`}>
                <action.icon className="w-4 h-4 text-white" />
              </div>
              <span className="text-[11px] font-medium text-white/80">{action.label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function AssetAllocation() {
  const total = ASSETS.reduce((sum, a) => sum + a.value, 0);
  
  return (
    <div className="mx-4 mb-6 rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-card)] p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-white">Asset Allocation</h3>
        <span className="text-[10px] text-slate-500 font-medium">Auto-balanced by PayFlow</span>
      </div>
      
      {/* Progress bar */}
      <div className="flex h-2 rounded-full overflow-hidden mb-4 bg-[var(--bg-tertiary)]">
        {ASSETS.map((asset) => (
          <div
            key={asset.name}
            className="transition-all duration-500"
            style={{ width: `${asset.value}%`, backgroundColor: asset.color }}
          />
        ))}
      </div>
      
      <div className="space-y-3">
        {ASSETS.map((asset) => (
          <div key={asset.name} className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: asset.color }} />
              <span className="text-sm text-slate-300">{asset.name}</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-sm font-semibold text-white">{asset.amount}</span>
              <span className="text-xs text-slate-500 w-8 text-right">{asset.value}%</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function SpendingChart() {
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const values = [65, 40, 80, 55, 90, 35, 70];
  const minVal = Math.min(...values) * 0.5;
  const max = Math.max(...values);
  
  return (
    <div className="mx-4 mb-6 rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-card)] p-5">
      <div className="flex items-center justify-between mb-5">
        <h3 className="text-sm font-semibold text-white">This Week</h3>
        <div className="flex items-center gap-1 text-xs text-emerald-400 font-medium">
          <TrendingUp className="w-3 h-3" />
          <span>+23%</span>
        </div>
      </div>
      
      <div className="flex items-end justify-between gap-2 h-28">
        {days.map((day, i) => (
          <div key={day} className="flex-1 flex flex-col items-center gap-1.5">
            <div className="w-full rounded-lg transition-all duration-500" style={{
              height: `${((values[i] - minVal) / (max - minVal)) * 100}%`,
              background: i === 4 ? 'linear-gradient(180deg, #06b6d4, #0891b2)' : 'var(--bg-tertiary)',
              animation: `fadeInUp 0.5s ease-out ${i * 0.05}s both`,
            }} />
            <span className={`text-[10px] font-medium ${i === 4 ? 'text-cyan-400' : 'text-slate-600'}`}>{day}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function Transactions() {
  return (
    <div className="mx-4 mb-6 rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-card)] overflow-hidden">
      <div className="flex items-center justify-between px-5 py-4 border-b border-[var(--border-subtle)]">
        <h3 className="text-sm font-semibold text-white">Transactions</h3>
        <button className="text-xs text-cyan-400 font-medium flex items-center gap-1 hover:text-cyan-300 transition-colors">
          View all <ChevronRight className="w-3 h-3" />
        </button>
      </div>
      
      {TRANSACTIONS.map((tx, i) => (
        <div key={tx.id} className="flex items-center justify-between px-5 py-3.5 border-b border-[var(--border-subtle)] last:border-b-0 hover:bg-white/[0.02] transition-colors"
          style={{ animation: `slideInRight 0.4s ease-out ${i * 0.05}s backwards` }}>
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-base ${
              tx.type === 'credit' ? 'bg-emerald-500/10' : 'bg-red-500/10'
            }`}>
              {tx.icon}
            </div>
            <div>
              <p className="text-sm font-medium text-slate-200">{tx.title}</p>
              <p className="text-[11px] text-slate-500 mt-0.5">{tx.subtitle}</p>
            </div>
          </div>
          <div className="text-right">
            <p className={`text-sm font-semibold ${tx.type === 'credit' ? 'text-emerald-400' : 'text-red-400'}`}>
              {tx.amount}
            </p>
            <p className="text-[10px] text-slate-600 mt-0.5">{tx.time}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

function StatsRow() {
  const stats = [
    { label: 'Saved this month', value: '₹43.1K', icon: Sparkles, color: 'text-emerald-400' },
    { label: 'Disputes won', value: '85%', icon: Shield, color: 'text-violet-400' },
    { label: 'Automations', value: '487', icon: Zap, color: 'text-cyan-400' },
  ];
  
  return (
    <div className="mx-4 mb-6 grid grid-cols-3 gap-3">
      {stats.map((stat) => (
        <div key={stat.label} className="rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-card)] p-4 text-center">
          <stat.icon className={`w-5 h-5 mx-auto mb-2 ${stat.color}`} />
          <p className={`text-lg font-bold ${stat.color}`}>{stat.value}</p>
          <p className="text-[10px] text-slate-500 mt-0.5 leading-tight">{stat.label}</p>
        </div>
      ))}
    </div>
  );
}

export default function FintechMobile() {
  return (
    <div className="min-h-screen bg-[var(--bg-dark)]">
      {/* Mobile header */}
      <div className="sticky top-0 z-10 bg-[var(--bg-secondary)]/80 backdrop-blur-xl border-b border-[var(--border-subtle)] px-5 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center"
              style={{ background: 'linear-gradient(135deg, #06b6d4, #0891b2)' }}>
              <Zap className="w-4 h-4 text-white" />
            </div>
            <div>
              <Text3DFlip
                className="text-sm font-bold text-white"
                textClassName="text-sm font-bold text-white"
                flipTextClassName="text-sm font-bold text-white"
                rotateDirection="top"
                staggerDuration={0.03}
                staggerFrom="first"
                transition={{ type: 'spring', damping: 25, stiffness: 160 }}
              >
                PayFlow
              </Text3DFlip>
              <p className="text-[10px] text-slate-500">Wealth Manager</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-[var(--bg-tertiary)] flex items-center justify-center">
              <BarChart3 className="w-4 h-4 text-slate-400" />
            </div>
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-white text-xs font-bold">
              K
            </div>
          </div>
        </div>
      </div>
      
      {/* Content */}
      <div className="py-4 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 64px)' }}>
        <BalanceCard />
        <StatsRow />
        <AssetAllocation />
        <SpendingChart />
        <Transactions />
      </div>
    </div>
  );
}
