import { useLocation, useNavigate } from 'react-router-dom';

const TimelineStep = ({ step, isLast }) => (
  <div className="flex gap-4">
    <div className="flex flex-col items-center">
      <div className={`w-3 h-3 rounded-full ${
        step.status === 'completed' ? 'bg-emerald-500' :
        step.status === 'in_progress' ? 'bg-amber-500 animate-pulse' :
        'bg-gray-300'
      }`} />
      {!isLast && <div className="w-px h-full bg-gray-200 my-1" />}
    </div>
    <div className="pb-6">
      <p className="text-sm font-medium text-gray-900">{step.title}</p>
      <p className="text-xs text-gray-500 mt-0.5">{step.description}</p>
      {step.timestamp && (
        <p className="text-xs text-gray-400 mt-1">{step.timestamp}</p>
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
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-500 mb-4">No activity selected</p>
          <button
            onClick={() => navigate('/')}
            className="text-sm text-cyan-600 hover:text-cyan-700 font-medium"
          >
            ← Back to dashboard
          </button>
        </div>
      </div>
    );
  }

  // Generate demo timeline based on activity type
  const timeline = [
    { title: 'Detection', description: `Identified ${activity.type} requiring optimization`, status: 'completed', timestamp: '3 min ago' },
    { title: 'Analysis', description: 'Analyzing available routes and options', status: 'completed', timestamp: '2 min ago' },
    { title: 'Route Selection', description: `Selected optimal route based on cost and speed`, status: 'completed', timestamp: '1 min ago' },
    { title: 'Execution', description: `Executing ${activity.type} automation`, status: activity.status, timestamp: activity.status === 'completed' ? 'Completed' : 'In progress' },
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <div className="border-b border-gray-200 px-8 py-6">
        <button
          onClick={() => navigate('/')}
          className="text-sm text-gray-500 hover:text-gray-700 mb-3 inline-flex items-center gap-1"
        >
          ← Back to dashboard
        </button>
        <h1 className="text-2xl font-bold text-gray-900">{activity.title}</h1>
        <p className="text-sm text-gray-500 mt-1">{activity.description}</p>
      </div>

      <div className="px-8 py-6 max-w-4xl">
        {/* Status Card */}
        <div className={`border rounded-lg p-6 mb-6 ${
          activity.status === 'completed'
            ? 'bg-emerald-50 border-emerald-200'
            : 'bg-amber-50 border-amber-200'
        }`}>
          <div className="flex items-center gap-3 mb-4">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
              activity.status === 'completed' ? 'bg-emerald-100' : 'bg-amber-100'
            }`}>
              {activity.status === 'completed' ? (
                <svg className="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                <svg className="w-5 h-5 text-amber-600 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              )}
            </div>
            <div>
              <p className="font-semibold text-gray-900">
                {activity.status === 'completed' ? 'Automation Completed' : 'Automation In Progress'}
              </p>
              <p className="text-sm text-gray-600">
                {activity.status === 'completed' ? 'This automation has been executed successfully' : 'Processing...'}
              </p>
            </div>
          </div>
          
          {activity.cost_saved > 0 && (
            <div className="flex items-center gap-6 pt-4 border-t border-gray-200">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase">Cost Saved</p>
                <p className="text-lg font-bold text-emerald-600">Rs {activity.cost_saved.toLocaleString('en-IN')}</p>
              </div>
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase">Time</p>
                <p className="text-lg font-bold text-gray-900">{activity.time}</p>
              </div>
            </div>
          )}
        </div>

        {/* Timeline */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-sm font-semibold text-gray-900 mb-4">Execution Timeline</h2>
          {timeline.map((step, idx) => (
            <TimelineStep key={idx} step={step} isLast={idx === timeline.length - 1} />
          ))}
        </div>

        {/* Details */}
        <div className="mt-6 bg-gray-50 border border-gray-200 rounded-lg p-6">
          <h2 className="text-sm font-semibold text-gray-900 mb-4">Details</h2>
          <dl className="space-y-3">
            <div className="flex justify-between">
              <dt className="text-sm text-gray-500">Type</dt>
              <dd className="text-sm font-medium text-gray-900 capitalize">{activity.type}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-sm text-gray-500">Status</dt>
              <dd className={`text-sm font-medium ${activity.status === 'completed' ? 'text-emerald-600' : 'text-amber-600'}`}>
                {activity.status === 'completed' ? 'Completed' : 'In Progress'}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-sm text-gray-500">Description</dt>
              <dd className="text-sm text-gray-900">{activity.description}</dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  );
}
