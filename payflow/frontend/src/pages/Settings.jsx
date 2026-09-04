import { useState } from 'react';

const Toggle = ({ enabled, onChange, label, description }) => (
  <div className="flex items-center justify-between py-3">
    <div>
      <p className="text-sm font-medium text-gray-900">{label}</p>
      <p className="text-xs text-gray-500">{description}</p>
    </div>
    <button
      onClick={() => onChange(!enabled)}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
        enabled ? 'bg-cyan-500' : 'bg-gray-300'
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
  <div className="flex items-center justify-between p-4 bg-white border border-gray-200 rounded-lg">
    <div className="flex items-center gap-3">
      <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center">
        <span className="text-lg font-bold text-gray-600">{name[0]}</span>
      </div>
      <div>
        <p className="text-sm font-medium text-gray-900">{name}</p>
        <p className="text-xs text-gray-500">{transactions} transactions today</p>
      </div>
    </div>
    <div className="flex items-center gap-2">
      <div className={`w-2 h-2 rounded-full ${connected ? 'bg-emerald-500' : 'bg-gray-300'}`} />
      <span className="text-xs font-medium text-gray-600">
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
    <div className="min-h-screen bg-white">
      {/* Header */}
      <div className="border-b border-gray-200 px-8 py-6">
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-sm text-gray-500 mt-1">Configure automations and processor connections</p>
      </div>

      <div className="px-8 py-6 max-w-3xl">
        {/* Connected Processors */}
        <section className="mb-8">
          <h2 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-4">Connected Processors</h2>
          <div className="space-y-3">
            {processors.map(proc => (
              <ProcessorCard key={proc.name} {...proc} />
            ))}
          </div>
        </section>

        {/* Automation Toggles */}
        <section className="mb-8">
          <h2 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-4">Automations</h2>
          <div className="bg-white border border-gray-200 rounded-lg px-4 divide-y divide-gray-100">
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
          <h2 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-4">API Keys</h2>
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">Razorpay API Key</label>
              <input
                type="password"
                value="rzp_live_••••••••••••"
                readOnly
                className="w-full px-3 py-2 border border-gray-200 rounded-md text-sm bg-gray-50"
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">Stripe API Key</label>
              <input
                type="password"
                value="sk_live_••••••••••••"
                readOnly
                className="w-full px-3 py-2 border border-gray-200 rounded-md text-sm bg-gray-50"
              />
            </div>
            <p className="text-xs text-gray-500">Contact support to update API keys</p>
          </div>
        </section>

        {/* Slack Integration */}
        <section>
          <h2 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-4">Integrations</h2>
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
                  <span className="text-lg">💬</span>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">Slack</p>
                  <p className="text-xs text-gray-500">Send automation notifications to Slack</p>
                </div>
              </div>
              <button className="px-3 py-1.5 text-xs font-medium text-cyan-600 border border-cyan-200 rounded-md hover:bg-cyan-50">
                Connect
              </button>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
