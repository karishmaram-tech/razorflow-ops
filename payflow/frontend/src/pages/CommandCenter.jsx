import { useEffect } from 'react';
import { motion } from 'framer-motion';
import KPICardPremium from '../components/KPICardPremium';
import AutomationCard from '../components/AutomationCard';
import OperationCard from '../components/OperationCard';
import useStore from '../store/useStore';

const StatusBadge = ({ connected, demoMode }) => (
  <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold border ${
    demoMode
      ? 'bg-pf-amber/10 border-pf-amber/20 text-pf-amber'
      : connected
        ? 'bg-pf-emerald/10 border-pf-emerald/20 text-pf-emerald'
        : 'bg-pf-red/10 border-pf-red/20 text-pf-red'
  }`}>
    <span className={`w-2 h-2 rounded-full ${connected ? 'bg-pf-emerald status-dot' : 'bg-pf-red'}`} />
    {demoMode ? 'Demo Mode' : connected ? 'Live' : 'Offline'}
  </div>
);

export default function CommandCenter() {
  const { commandCenter, loading, connected, demoMode, loadCommandCenter, toggleAutopilot } = useStore();

  useEffect(() => { loadCommandCenter(); }, [loadCommandCenter]);

  if (loading || !commandCenter) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="w-12 h-12 rounded-xl mx-auto mb-4 flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #06B6D4, #8B5CF6)' }}>
            <svg className="w-6 h-6 text-white animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </div>
          <p className="text-pf-slate-400 text-sm">Initializing PayFlow...</p>
        </div>
      </div>
    );
  }

  const { kpis, automations, critical_operations, impact, processors, next_deadline } = commandCenter;

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.08 } },
  };

  const sectionVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: 'easeOut' } },
  };

  return (
    <motion.div className="min-h-screen" variants={containerVariants} initial="hidden" animate="visible">
      {/* Hero Header */}
      <div className="relative overflow-hidden border-b border-pf-border">
        <div className="absolute inset-0 opacity-30" style={{ background: 'radial-gradient(ellipse at top left, rgba(6,182,212,0.15), transparent 60%), radial-gradient(ellipse at bottom right, rgba(139,92,246,0.1), transparent 60%)' }} />
        <div className="relative px-8 py-8">
          <div className="flex items-start justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-white mb-1">
                Payment Operations <span className="gradient-text">Command Center</span>
              </h1>
              <p className="text-pf-slate-400 text-sm">
                Autonomous settlement routing, dispute automation, and refund optimization
              </p>
            </div>
            <div className="flex items-center gap-3">
              <StatusBadge connected={connected} demoMode={demoMode} />
              {next_deadline && (
                <div className="flex items-center gap-2 px-3 py-1.5 bg-pf-amber/10 border border-pf-amber/20 rounded-full">
                  <svg className="w-3.5 h-3.5 text-pf-amber" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="text-[10px] font-bold text-pf-amber uppercase">
                    Deadline: {new Date(next_deadline).toLocaleDateString()}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* KPI Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <KPICardPremium
              label="Settlements Optimized"
              value={kpis.settlements_optimized}
              subtext="Routed through optimal path"
              trend={18}
              color="cyan"
              icon={<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" /></svg>}
            />
            <KPICardPremium
              label="Cost Reduced"
              value={`Rs ${(kpis.cost_saved / 1000).toFixed(1)}K`}
              subtext="Settlement + refund savings"
              trend={12}
              color="emerald"
              icon={<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
            />
            <KPICardPremium
              label="Disputes Automated"
              value={kpis.disputes_automated}
              subtext={`${kpis.disputes_won} won automatically`}
              trend={25}
              color="violet"
              icon={<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>}
            />
            <KPICardPremium
              label="Time Saved"
              value={`${kpis.time_saved_hours}h`}
              subtext="Manual tasks automated"
              trend={15}
              color="amber"
              icon={<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
            />
          </div>
        </div>
      </div>

      <div className="px-8 py-6 space-y-8">
        {/* Active Automations */}
        <section>
          <div className="flex items-center justify-between mb-5">
            <div>
              <h2 className="text-lg font-bold text-white">Active Automations</h2>
              <p className="text-xs text-pf-slate-500 mt-0.5">Autonomous execution across all payment operations</p>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 bg-pf-emerald/10 border border-pf-emerald/20 rounded-lg">
              <div className="w-2 h-2 rounded-full bg-pf-emerald status-dot" />
              <span className="text-xs font-semibold text-pf-emerald">
                {automations.filter(a => a.autopilot).length} Active
              </span>
            </div>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {automations.map((auto, idx) => (
              <AutomationCard key={auto.id} automation={auto} onToggle={toggleAutopilot} index={idx} />
            ))}
          </div>
        </section>

        {/* Critical Operations */}
        {critical_operations.length > 0 && (
          <section>
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className="text-lg font-bold text-white">Critical Operations</h2>
                <p className="text-xs text-pf-slate-500 mt-0.5">Issues being handled by PayFlow autopilot</p>
              </div>
              <span className="text-xs font-bold text-pf-red bg-pf-red/10 px-2.5 py-1 rounded-lg">
                {critical_operations.filter(o => o.severity === 'critical').length} Critical
              </span>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {critical_operations.map((op, idx) => (
                <OperationCard key={op.id} operation={op} index={idx} />
              ))}
            </div>
          </section>
        )}

        {/* Impact Summary */}
        <motion.section className="bg-gradient-to-br from-pf-slate-800 to-pf-slate-900 rounded-xl border border-pf-border p-6" variants={sectionVariants}>
          <h2 className="text-lg font-bold text-white mb-4">Monthly Impact</h2>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <p className="text-[10px] text-pf-slate-500 uppercase font-bold mb-1">Total Saved</p>
              <p className="text-2xl font-bold gradient-text">Rs {impact.total_saved_this_month.toLocaleString('en-IN')}</p>
              <p className="text-xs text-pf-emerald font-semibold mt-1">↑ {impact.improvement_pct}% vs last month</p>
            </div>
            <div>
              <p className="text-[10px] text-pf-slate-500 uppercase font-bold mb-1">Chargebacks Won</p>
              <p className="text-2xl font-bold text-white">{impact.chargebacks_won}/{impact.chargebacks_total}</p>
              <p className="text-xs text-pf-emerald font-semibold mt-1">{Math.round(impact.win_rate * 100)}% win rate</p>
            </div>
            <div>
              <p className="text-[10px] text-pf-slate-500 uppercase font-bold mb-1">Hours Saved</p>
              <p className="text-2xl font-bold text-white">{impact.hours_saved_this_month}h</p>
              <p className="text-xs text-pf-slate-500 mt-1">Manual work automated</p>
            </div>
            <div>
              <p className="text-[10px] text-pf-slate-500 uppercase font-bold mb-1">ROI</p>
              <p className="text-2xl font-bold text-pf-emerald">{impact.roi_months}x</p>
              <p className="text-xs text-pf-slate-500 mt-1">Payback in {impact.roi_months} months</p>
            </div>
          </div>
        </motion.section>

        {/* Connected Processors */}
        <motion.section variants={sectionVariants}>
          <h2 className="text-lg font-bold text-white mb-4">Connected Processors</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {processors.map((proc) => (
              <div key={proc.name} className="bg-pf-surface rounded-xl border border-pf-border p-4 flex items-center gap-4">
                <div className="w-10 h-10 rounded-xl bg-pf-cyan/10 flex items-center justify-center">
                  <svg className="w-5 h-5 text-pf-cyan" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-semibold text-white">{proc.name}</p>
                    <span className="w-2 h-2 rounded-full bg-pf-emerald" />
                  </div>
                  <p className="text-xs text-pf-slate-500">{proc.transactions_today} txns today</p>
                </div>
              </div>
            ))}
          </div>
        </motion.section>
      </div>
    </motion.div>
  );
}
