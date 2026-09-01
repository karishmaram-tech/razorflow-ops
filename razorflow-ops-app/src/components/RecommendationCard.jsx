const urgencyStyles = {
  critical: { bg: 'bg-red-50', border: 'border-red-200', badge: 'bg-red-100 text-red-800', dot: 'bg-red-500' },
  high: { bg: 'bg-orange-50', border: 'border-orange-200', badge: 'bg-orange-100 text-orange-800', dot: 'bg-orange-500' },
  medium: { bg: 'bg-amber-50', border: 'border-amber-200', badge: 'bg-amber-100 text-amber-800', dot: 'bg-amber-500' },
  low: { bg: 'bg-blue-50', border: 'border-blue-200', badge: 'bg-blue-100 text-blue-800', dot: 'bg-blue-500' },
};

export default function RecommendationCard({ recommendation }) {
  const urgency = recommendation.urgency || 'medium';
  const styles = urgencyStyles[urgency] || urgencyStyles.medium;

  return (
    <div className={`rounded-lg border p-5 ${styles.bg} ${styles.border}`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${styles.dot}`} />
          <span className={`status-badge ${styles.badge}`}>
            {(urgency).toUpperCase()}
          </span>
        </div>
        <span className="text-xs text-gray-500">
          {recommendation.timeline?.replace(/_/g, ' ') || 'N/A'}
        </span>
      </div>

      <p className="text-sm font-semibold text-gray-900 mb-2">
        {recommendation.recommended_action?.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) || 'Action Required'}
      </p>

      <p className="text-sm text-gray-600 mb-3">
        {recommendation.recommendation_text || 'No details available'}
      </p>

      <div className="flex items-center gap-6 text-xs">
        <div>
          <span className="text-gray-500">Success Rate: </span>
          <span className="font-semibold text-gray-900">
            {recommendation.success_probability
              ? `${Math.round(recommendation.success_probability * 100)}%`
              : 'N/A'}
          </span>
        </div>
        <div>
          <span className="text-gray-500">Resolution: </span>
          <span className="font-semibold text-gray-900">
            {recommendation.expected_resolution_time_hours
              ? `${recommendation.expected_resolution_time_hours}h`
              : 'N/A'}
          </span>
        </div>
      </div>
    </div>
  );
}
