import { Link } from 'react-router-dom';

function formatRelativeTime(dateStr) {
  if (!dateStr) return '-';
  const now = new Date();
  const date = new Date(dateStr);
  const diffMs = now - date;
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHr = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHr / 24);

  if (diffDay > 0) return `${diffDay} day${diffDay !== 1 ? 's' : ''} ago`;
  if (diffHr > 0) return `${diffHr} hour${diffHr !== 1 ? 's' : ''} ago`;
  if (diffMin > 0) return `${diffMin} min${diffMin !== 1 ? 's' : ''} ago`;
  return 'just now';
}

const severityBadge = {
  critical: 'bg-red-100 text-red-800',
  warning: 'bg-amber-100 text-amber-800',
  info: 'bg-blue-100 text-blue-800',
};

const typeIcons = {
  settlement_delayed: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  settlement_failed: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  refund_stuck: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
    </svg>
  ),
  dispute_evidence_incomplete: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  ),
  default: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
};

function formatAnomalyType(type) {
  return (type || 'unknown')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function getLinkPath(issue) {
  const id = issue.settlement_id || issue.refund_id || issue.dispute_id ||
    issue.related_settlement_id || issue.related_refund_id || issue.related_dispute_id;
  if (!id) return '#';
  if (issue.related_settlement_id || issue.settlement_id) return `/settlement/${id}`;
  if (issue.related_refund_id || issue.refund_id) return `/refund/${id}`;
  if (issue.related_dispute_id || issue.dispute_id) return `/dispute/${id}`;
  return '#';
}

export default function IssuesTable({ issues = [], maxRows = 20 }) {
  // Normalize field names: API returns 'type' but component uses 'anomaly_type'
  const normalized = issues.map(issue => ({
    ...issue,
    anomaly_type: issue.anomaly_type || issue.type,
    details: issue.details || issue.recommended_action || '',
  }));
  // Deduplicate: group by type + severity, take the first of each
  const seen = new Set();
  const unique = normalized.filter((issue) => {
    const key = `${issue.anomaly_type}-${issue.severity}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
  const displayIssues = unique.slice(0, maxRows);
  const totalCount = unique.length;

  if (!issues.length) {
    return (
      <div className="card p-12 text-center">
        <svg className="w-12 h-12 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p className="text-gray-500 text-lg font-medium">No active issues</p>
        <p className="text-gray-400 text-sm mt-1">All payment operations are running smoothly</p>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden">
      <div className="overflow-x-auto">
      <table className="w-full min-w-[700px]">
        <thead className="bg-gray-50 border-b border-gray-200">
          <tr>
            <th className="px-6 py-3.5 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">
              Issue
            </th>
            <th className="px-6 py-3.5 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">
              Severity
            </th>
            <th className="px-6 py-3.5 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">
              Detected
            </th>
            <th className="px-6 py-3.5 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">
              Root Cause
            </th>
            <th className="px-6 py-3.5 text-right text-xs font-bold text-gray-500 uppercase tracking-wider">
              Action
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {displayIssues.map((issue, idx) => (
            <tr key={issue.id || idx} className="hover:bg-gray-50 transition-colors">
              <td className="px-6 py-4">
                <div className="flex items-center gap-3">
                  <div className={`p-1.5 rounded-lg ${
                    issue.severity === 'critical' ? 'bg-red-50 text-red-500' :
                    issue.severity === 'warning' ? 'bg-amber-50 text-amber-500' :
                    'bg-blue-50 text-blue-500'
                  }`}>
                    {typeIcons[issue.anomaly_type] || typeIcons.default}
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900 text-sm">
                      {formatAnomalyType(issue.anomaly_type || issue.type)}
                    </p>
                    <p className="text-xs text-gray-500 mt-0.5 line-clamp-1">
                      {issue.details || (issue.anomaly_id ? `#${issue.anomaly_id.slice(0, 8)}` : '')}
                    </p>
                  </div>
                </div>
              </td>
              <td className="px-6 py-4">
                <span className={`status-badge ${
                  severityBadge[issue.severity] || severityBadge.info
                }`}>
                  {(issue.severity || 'info').toUpperCase()}
                </span>
              </td>
              <td className="px-6 py-4 text-sm text-gray-600">
                {formatRelativeTime(issue.detected_at)}
              </td>
              <td className="px-6 py-4">
                <span className="text-sm font-medium text-blue-600">
                  {issue.root_cause
                    ? issue.root_cause.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
                    : 'Analyzing...'}
                </span>
              </td>
              <td className="px-6 py-4 text-right">
                <Link
                  to={getLinkPath(issue)}
                  className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-800 font-semibold text-sm no-underline"
                >
                  View
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </Link>
              </td>              </tr>
          ))}
        </tbody>
      </table>
      </div>
      {totalCount > maxRows && (
        <div className="px-6 py-3 bg-gray-50 border-t border-gray-200 text-center">
          <p className="text-sm text-gray-500">
            Showing {maxRows} of {totalCount} unique issues. {totalCount - maxRows} more not shown.
          </p>
        </div>
      )}
    </div>
  );
}
