const severityStyles = {
  critical: {
    border: 'border-l-4 border-l-red-500',
    icon: 'text-red-500',
    iconBg: 'bg-red-50',
  },
  warning: {
    border: 'border-l-4 border-l-amber-500',
    icon: 'text-amber-500',
    iconBg: 'bg-amber-50',
  },
  success: {
    border: 'border-l-4 border-l-green-500',
    icon: 'text-green-500',
    iconBg: 'bg-green-50',
  },
  default: {
    border: 'border-l-4 border-l-blue-500',
    icon: 'text-blue-500',
    iconBg: 'bg-blue-50',
  },
};

const severityIcons = {
  critical: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
    </svg>
  ),
  warning: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  success: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  default: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  ),
};

export default function KPICard({ label, value, subtext, severity = 'default', icon }) {
  const styles = severityStyles[severity] || severityStyles.default;

  return (
    <div className={`card p-6 ${styles.border}`}>
      <div className="flex items-start justify-between mb-3">
        <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">{label}</p>
        <div className={`p-1.5 rounded-lg ${styles.iconBg} ${styles.icon}`}>
          {icon || severityIcons[severity] || severityIcons.default}
        </div>
      </div>
      <p className="text-3xl font-bold text-gray-900 mb-1">{value}</p>
      <p className="text-sm text-gray-500">{subtext}</p>
    </div>
  );
}
