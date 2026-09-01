import { useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Loading from '../components/Loading';
import ErrorDisplay from '../components/ErrorDisplay';
import RecommendationCard from '../components/RecommendationCard';
import useStore from '../store/useStore';

const statusColors = {
  failed: 'bg-red-100 text-red-800',
  pending: 'bg-amber-100 text-amber-800',
  partial: 'bg-orange-100 text-orange-800',
  initiated: 'bg-blue-100 text-blue-800',
  success: 'bg-green-100 text-green-800',
};

export default function SettlementDetail() {
  const { id } = useParams();
  const { settlement, loading, error, loadSettlement } = useStore();

  const loadData = useCallback(() => {
    loadSettlement(id);
  }, [id, loadSettlement]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (loading) return <Loading message="Loading settlement details..." />;
  if (error) return <ErrorDisplay message={error} onRetry={loadData} />;
  if (!settlement) return <ErrorDisplay message="Settlement not found" />;

  const s = settlement.settlement || settlement;
  const diagnosis = settlement.diagnosis || {};
  const recommendation = settlement.recommendation || {};
  const anomalies = settlement.anomalies || [];

  return (
    <>
      <Navbar />
      <div className="max-w-4xl mx-auto px-8 py-10">
        {/* Breadcrumb */}
        <Link to="/" className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800 no-underline mb-6">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Dashboard
        </Link>

        <h1 className="text-2xl font-bold text-gray-900 mb-2">Settlement Details</h1>
        <p className="text-gray-500 mb-8">ID: {s.id}</p>

        {/* Key Info Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="card p-5">
            <p className="text-xs font-semibold text-gray-400 uppercase mb-1">Amount</p>
            <p className="text-2xl font-bold text-gray-900">
              Rs {Number(s.amount || 0).toLocaleString('en-IN')}
            </p>
          </div>
          <div className="card p-5">
            <p className="text-xs font-semibold text-gray-400 uppercase mb-1">Status</p>
            <span className={`status-badge ${statusColors[s.status] || 'bg-gray-100 text-gray-800'}`}>
              {(s.status || 'unknown').toUpperCase()}
            </span>
          </div>
          <div className="card p-5">
            <p className="text-xs font-semibold text-gray-400 uppercase mb-1">Net Amount</p>
            <p className="text-2xl font-bold text-gray-900">
              Rs {Number(s.net_amount || s.amount || 0).toLocaleString('en-IN')}
            </p>
          </div>
          <div className="card p-5">
            <p className="text-xs font-semibold text-gray-400 uppercase mb-1">Fees</p>
            <p className="text-2xl font-bold text-gray-900">
              Rs {Number(s.fees || 0).toLocaleString('en-IN')}
            </p>
          </div>
        </div>

        {/* Timeline */}
        <div className="card p-6 mb-8">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Timeline</h2>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-gray-400 font-semibold">Created</p>
              <p className="text-gray-900">{s.created_at ? new Date(s.created_at).toLocaleString() : '-'}</p>
            </div>
            <div>
              <p className="text-gray-400 font-semibold">Expected Arrival</p>
              <p className="text-gray-900">{s.expected_arrival_at ? new Date(s.expected_arrival_at).toLocaleString() : '-'}</p>
            </div>
            <div>
              <p className="text-gray-400 font-semibold">Actual Arrival</p>
              <p className="text-gray-900">{s.actual_arrival_at ? new Date(s.actual_arrival_at).toLocaleString() : 'Pending'}</p>
            </div>
          </div>
        </div>

        {/* Anomalies */}
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

        {/* Diagnosis */}
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
            <p className="text-sm text-gray-600 mb-3">
              {diagnosis.explanation_plain_english || 'Diagnosis in progress...'}
            </p>
            {diagnosis.causal_chain && (
              <div className="flex items-center gap-2 text-xs text-gray-500">
                {diagnosis.causal_chain.map((step, i) => (
                  <span key={i} className="flex items-center gap-2">
                    <span className="font-medium">{step.cause || step}</span>
                    {i < diagnosis.causal_chain.length - 1 && (
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    )}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Recommendation */}
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
