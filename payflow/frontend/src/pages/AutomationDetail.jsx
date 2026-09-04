import { useLocation, useNavigate } from 'react-router-dom';

const TimelineStep = ({ step, isLast }) => (
  <div className="flex gap-4">
    <div className="flex flex-col items-center">
      <div className={`w-3 h-3 rounded-full ${
        step.status === 'completed' ? 'bg-emerald-500' :
        step.status === 'in_progress' ? 'bg-amber-500' :
        'bg-slate-600'
      }`} style={step.status === 'in_progress' ? { animation: 'pulse 2s infinite' } : {}} />
      {!isLast && <div className="w-px flex-1 bg-[var(--border-subtle)] my-1" />}
    </div>
    <div className="pb-6">
      <p className="text-sm font-medium text-slate-200">{step.title}</p>
      <p className="text-xs text-slate-500 mt-0.5">{step.description}</p>
      {step.timestamp && (
        <p className="text-xs text-slate-600 mt-1">{step.timestamp}</p>
      )}
    </div>
  </div>
);

export default function AutomationDetail() {
  const location = useLocation();
  const navigate = useNavigate();
  const { activity } = location.state || {};

  if (!activity) {
    return (
      <div className="min-h-screen bg-[var(--bg-dark)] flex items-center justify-center">
        <div className="text-center">
          <p className="text-slate-500 mb-4">No activity selected</p>
          <button
            onClick={() => navigate('/')}
            className="text-sm text-cyan-400 hover:text-cyan-300 font-medium transition-colors"
          >
            ← Back to dashboard
          </button>
        </div>
      </div>
    );
  }

  const timeline = [
    { title: 'Detection', description: `Identified ${activity.type} requiring optimization`, status: 'completed', timestamp: '3 min ago' },
    { title: 'Analysis', description: 'Analyzing available routes and options', status: 'completed', timestamp: '2 min ago' },
    { title: 'Route Selection', description: 'Selected optimal route based on cost and speed', status: 'completed', timestamp: '1 min ago' },
    { title: 'Execution', description: `Executing ${activity.type} automation`, status: activity.status, timestamp: activity.status === 'completed' ? 'Completed' : 'In progress' },
  ];

  return (
    <div className="min-h-screen bg-[var(--bg-dark)]">
      {/* Header */}
      <div className="border-b border-[var(--border-subtle)] px-8 py-5 bg-[var(--bg-secondary)]/50 backdrop-blur-sm sticky top-0 z-10">
        <button
          onClick={() => navigate('/')}
          className="text-sm text-slate-500 hover:text-slate-300 mb-2 inline-flex items-center gap-1 transition-colors"
        >
          ← Back to dashboard
        </button>
        <h1 className="text-xl font-bold text-white">{activity.title}</h1>
        <p className="text-sm text-slate-500 mt-0.5">{activity.description}</p>
      </div>

      <div className="px-8 py-6 max-w-4xl">
        {/* Status Card */}
        <div className={`rounded-2xl border p-6 mb-6 ${
          activity.status === 'completed'
            ? 'bg-emerald-500/5 border-emerald-500/20'
            : 'bg-amber-500/5 border-amber-500/20'
        }`} style={{ animation: 'fadeInUp 0.5s ease-out' }}>
          <div className="flex items-center gap-3 mb-4">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
              activity.status === 'completed' ? 'bg-emerald-500/10' : 'bg-amber-500/10'
            }`}>
              {activity.status === 'completed' ? (
                <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                <svg className="w-5 h-5 text-amber-400" style={{ animation: 'spin 2s linear infinite' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              )}
            </div>
            <div>
              <p className="font-semibold text-white">
                {activity.status === 'completed' ? 'Automation Completed' : 'Automation In Progress'}
              </p>
              <p className="text-sm text-slate-400">
                {activity.status === 'completed' ? 'This automation has been executed successfully' : 'Processing...'}
              </p>
            </div>
          </div>
          
          {activity.cost_saved > 0 && (
            <div className="flex items-center gap-6 pt-4 border-t border-[var(--border-subtle)]">
              <div>
                <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-widest">Cost Saved</p>
                <p className="text-lg font-bold text-emerald-400">Rs {activity.cost_saved.toLocaleString('en-IN')}</p>
              </div>
              <div>
                <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-widest">Time</p>
                <p className="text-lg font-bold text-white">{activity.time}</p>
              </div>
            </div>
          )}
        </div>

        {/* Timeline */}
        <div className="bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-2xl p-6 mb-6">
          <h2 className="text-sm font-semibold text-white mb-5">Execution Timeline</h2>
          {timeline.map((step, idx) => (
            <TimelineStep key={idx} step={step} isLast={idx === timeline.length - 1} />
          ))}
        </div>

        {/* Details */}
        <div className="bg-[var(--bg-card)] border border-[var(--border-subtle)] rounded-2xl p-6">
          <h2 className="text-sm font-semibold text-white mb-4">Details</h2>
          <dl className="space-y-3">
            <div className="flex justify-between">
              <dt className="text-sm text-slate-500">Type</dt>
              <dd className="text-sm font-medium text-slate-300 capitalize">{activity.type}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-sm text-slate-500">Status</dt>
              <dd className={`text-sm font-medium ${activity.status === 'completed' ? 'text-emerald-400' : 'text-amber-400'}`}>
                {activity.status === 'completed' ? 'Completed' : 'In Progress'}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-sm text-slate-500">Description</dt>
              <dd className="text-sm text-slate-300">{activity.description}</dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  );
}
