export default function MetricCard({ title, value, subtext, trend, icon }) {
  return (
    <div className="card p-6">
      <div className="flex items-center gap-3 mb-4">
        {icon && (
          <div className="p-2 rounded-lg bg-gray-50 text-gray-400">
            {icon}
          </div>
        )}
        <p className="text-sm font-semibold text-gray-600">{title}</p>
      </div>
      <div className="flex items-end justify-between">
        <div>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {subtext && <p className="text-sm text-gray-500 mt-1">{subtext}</p>}
        </div>
        {trend !== undefined && (
          <div className={`text-sm font-semibold ${trend >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}%
          </div>
        )}
      </div>
    </div>
  );
}
