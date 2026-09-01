import { useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Loading from '../components/Loading';
import ErrorDisplay from '../components/ErrorDisplay';
import RecommendationCard from '../components/RecommendationCard';
import useStore from '../store/useStore';

const statusColors = {
  success: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  reversed: 'bg-red-100 text-red-800',
  processing: 'bg-blue-100 text-blue-800',
  pending: 'bg-amber-100 text-amber-800',
  initiated: 'bg-gray-100 text-gray-800',
};

const reasonLabels = {
  customer_requested: 'Customer Requested',
  duplicate_charge: 'Duplicate Charge',
  fraud: 'Fraud',
  processing_error: 'Processing Error',
  other: 'Other',
};

export default function RefundDetail() {
  const { id } = useParams();
  const { refund, loading, error, loadRefund } = useStore();

  const loadData = useCallback(() => {
    loadRefund(id);
  }, [id, loadRefund]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (loading) return <Loading message="Loading refund details..." />;
  if (error) return <ErrorDisplay message={error} onRetry={loadData} />;
  if (!refund) return <ErrorDisplay message="Refund not found" />;

  const r = refund.refund || refund;
  const diagnosis = refund.diagnosis || {};
  const recommendation = refund.recommendation || {};
  const anomalies = refund.anomalies || [];

  return (
    <>
      <Navbar />
      <div className="max-w-4xl mx-auto px-8 py-10">
        <Link to="/" className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800 no-underline mb-6">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Dashboard
        </Link>

        <h1 className="text-2xl font-bold text-gray-900 mb-2">Refund Details</h1>
        <p className="text-gray-500 mb-8">ID: {r.id}</p>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="card p-5">
            <p className="text-xs font-semibold text-gray-400 uppercase mb-1">Amount</p>
            <p className="text-2xl font-bold text-gray-900">
              Rs {Number(r.amount || 0).toLocaleString('en-IN')}
            </p>
          </div>
          <div className="card p-5">
            <p className="text-xs font-semibold text-gray-400 uppercase mb-1">Status</p>
            <span className={`status-badge ${statusColors[r.status] || 'bg-gray-100 text-gray-800'}`}>
              {(r.status || 'unknown').toUpperCase()}
            </span>
          </div>
          <div className="card p-5">
            <p className="text-xs font-semibold text-gray-400 uppercase mb-1">Reason</p>
            <p className="text-sm font-medium text-gray-900">
              {reasonLabels[r.reason] || r.reason || '-'}
            </p>
          </div>
          <div className="card p-5">
            <p className="text-xs font-semibold text-gray-400 uppercase mb-1">Initiated By</p>
            <p className="text-sm font-medium text-gray-900 capitalize">
              {(r.initiated_by || '-').replace(/_/g, ' ')}
            </p>
          </div>
        </div>

        <div className="card p-6 mb-8">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Timeline</h2>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-gray-400 font-semibold">Created</p>
              <p className="text-gray-900">{r.created_at ? new Date(r.created_at).toLocaleString() : '-'}</p>
            </div>
            <div>
              <p className="text-gray-400 font-semibold">Expected Completion</p>
              <p className="text-gray-900">{r.expected_completion_at ? new Date(r.expected_completion_at).toLocaleString() : '-'}</p>
            </div>
            <div>
              <p className="text-gray-400 font-semibold">Actual Completion</p>
              <p className="text-gray-900">{r.actual_completion_at ? new Date(r.actual_completion_at).toLocaleString() : 'Pending'}</p>
            </div>
          </div>
        </div>

        {anomalies.length > 0 && (
          <div className="card p-6 mb-8">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Detected Anomalies</h2>
            <div className="space-y-3">
              {anomalies.map((a, idx) => (
                <div key={a.id || idx} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                  <span className={`status-badge ${
                    a.severity === 'critical' ? 'bg-red-100 text-red-800' :
                    a.severity === 'warning' ? 'bg-amber-100 text-amber-800' :
                    'bg-blue-100 text-blue-800'
                  }`}>
                    {(a.severity || 'info').toUpperCase()}
                  </span>
                  <span className="text-sm font-medium text-gray-900">
                    {(a.anomaly_type || 'unknown').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="card p-6 mb-8">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Root Cause Diagnosis</h2>
          <div className="bg-blue-50 rounded-lg p-5 border-l-4 border-blue-500">
            <div className="flex items-center gap-3 mb-2">
              <p className="text-base font-semibold text-gray-900">
                {(diagnosis.root_cause_category || 'Analyzing...').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
              </p>
              {diagnosis.confidence && (
                <span className="text-xs font-semibold text-blue-700 bg-blue-100 px-2 py-0.5 rounded">
                  {Math.round(diagnosis.confidence * 100)}% confidence
                </span>
              )}
            </div>
            <p className="text-sm text-gray-600">
              {diagnosis.explanation_plain_english || 'Diagnosis in progress...'}
            </p>
          </div>
        </div>

        {recommendation.recommendation_text && (
          <div className="mb-8">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Recommended Action</h2>
            <RecommendationCard recommendation={recommendation} />
          </div>
        )}
      </div>
    </>
  );
}
