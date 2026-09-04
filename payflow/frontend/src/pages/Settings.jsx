import { useState } from 'react';

const Toggle = ({ enabled, onChange, label, description }) => (
  <div className="flex items-center justify-between py-3.5">
    <div>
      <p className="text-sm font-medium text-slate-200">{label}</p>
      <p className="text-xs text-slate-500 mt-0.5">{description}</p>
    </div>
    <button
      onClick={() => onChange(!enabled)}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
        enabled ? 'bg-cyan-500' : 'bg-slate-700'
      }`}
    >
      <span
        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
          enabled ? 'translate-x-6' : 'translate-x-1'
        }`}
      />
    </button>
  </div>
);

const ProcessorCard = ({ name, connected, transactions }) => (
  <div className="flex items-center justify-between p-4 bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-xl hover:border-[var(--border-light)] transition-all duration-200">
    <div className="flex items-center gap-3">
      <div className="w-10 h-10 rounded-xl bg-[var(--bg-tertiary)] flex items-center justify-center">
        <span className="text-sm font-bold text-slate-400">{name[0]}</span>
      </div>
      <div>
        <p className="text-sm font-medium text-slate-200">{name}</p>
        <p className="text-xs text-slate-500">{transactions} transactions today</p>
      </div>
    </div>
    <div className="flex items-center gap-2">
      <div className={`w-2 h-2 rounded-full ${connected ? 'bg-emerald-500' : 'bg-slate-600'}`} />
      <span className={`text-xs font-medium ${connected ? 'text-emerald-400' : 'text-slate-500'}`}>
        {connected ? 'Connected' : 'Disconnected'}
      </span>
    </div>
  </div>
);

export default function Settings() {
  const [automations, setAutomations] = useState({
    autoSettle: true,
    disputeAutopilot: true,
    smartRefunds: true,
    notifications: true,
  });

  const [processors] = useState([
    { name: 'Razorpay', connected: true, transactions: 142 },
    { name: 'Stripe', connected: true, transactions: 89 },
    { name: 'Wise', connected: false, transactions: 0 },
  ]);

  const toggleAutomation = (key) => {
    setAutomations(prev => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="min-h-screen bg-[var(--bg-dark)]">
      {/* Header */}
      <div className="border-b border-[var(--border-subtle)] px-8 py-5 bg-[var(--bg-secondary)]/50 backdrop-blur-sm sticky top-0 z-10">
        <h1 className="text-xl font-bold text-white">Settings</h1>
        <p className="text-sm text-slate-500 mt-0.5">Configure automations and processor connections</p>
      </div>

      <div className="px-8 py-6 max-w-3xl">
        {/* Connected Processors */}
        <section className="mb-8">
          <h2 className="text-[11px] font-semibold text-slate-500 uppercase tracking-widest mb-4">Connected Processors</h2>
          <div className="space-y-3">
            {processors.map(proc => (
              <ProcessorCard key={proc.name} {...proc} />
            ))}
          </div>
        </section>

        {/* Automation Toggles */}
        <section className="mb-8">
          <h2 className="text-[11px] font-semibold text-slate-500 uppercase tracking-widest mb-4">Automations</h2>
          <div className="bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-2xl px-5 divide-y divide-[var(--border-subtle)]">
            <Toggle
              enabled={automations.autoSettle}
              onChange={() => toggleAutomation('autoSettle')}
              label="AutoSettle"
              description="Automatically route settlements through optimal processor"
            />
            <Toggle
              enabled={automations.disputeAutopilot}
              onChange={() => toggleAutomation('disputeAutopilot')}
              label="Dispute Autopilot"
              description="Auto-gather evidence and submit claims for high-confidence cases"
            />
            <Toggle
              enabled={automations.smartRefunds}
              onChange={() => toggleAutomation('smartRefunds')}
              label="Smart Refunds"
              description="Route refunds through cheapest payment path"
            />
            <Toggle
              enabled={automations.notifications}
              onChange={() => toggleAutomation('notifications')}
              label="Real-time Notifications"
              description="Get notified when automations complete"
            />
          </div>
        </section>

        {/* API Keys */}
        <section className="mb-8">
          <h2 className="text-[11px] font-semibold text-slate-500 uppercase tracking-widest mb-4">API Keys</h2>
          <div className="bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-2xl p-5">
            <div className="mb-4">
              <label className="block text-sm font-medium text-slate-400 mb-1.5">Razorpay API Key</label>
              <input
                type="password"
                value="rzp_live_••••••••••••"
                readOnly
                className="w-full px-3 py-2.5 border border-[var(--border-subtle)] rounded-xl text-sm bg-[var(--bg-tertiary)] text-slate-300 focus:outline-none focus:border-cyan-500/30"
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-slate-400 mb-1.5">Stripe API Key</label>
              <input
                type="password"
                value="sk_live_••••••••••••"
                readOnly
                className="w-full px-3 py-2.5 border border-[var(--border-subtle)] rounded-xl text-sm bg-[var(--bg-tertiary)] text-slate-300 focus:outline-none focus:border-cyan-500/30"
              />
            </div>
            <p className="text-xs text-slate-600">Contact support to update API keys</p>
          </div>
        </section>

        {/* Slack Integration */}
        <section>
          <h2 className="text-[11px] font-semibold text-slate-500 uppercase tracking-widest mb-4">Integrations</h2>
          <div className="bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-2xl p-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-violet-500/10 flex items-center justify-center">
                  <span className="text-lg">💬</span>
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-200">Slack</p>
                  <p className="text-xs text-slate-500">Send automation notifications to Slack</p>
                </div>
              </div>
              <button className="px-3.5 py-1.5 text-xs font-medium text-cyan-400 border border-cyan-500/20 rounded-lg hover:bg-cyan-500/10 transition-colors">
                Connect
              </button>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
