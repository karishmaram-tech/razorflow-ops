import { useEffect, useCallback, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Loading from '../components/Loading';
import ErrorDisplay from '../components/ErrorDisplay';
import RecommendationCard from '../components/RecommendationCard';
import useStore from '../store/useStore';

const statusColors = {
  evidence_pending: 'bg-red-100 text-red-800',
  under_review: 'bg-amber-100 text-amber-800',
  won: 'bg-green-100 text-green-800',
  lost: 'bg-red-100 text-red-800',
  resolved: 'bg-gray-100 text-gray-800',
};

const evidenceColors = {
  proof_of_shipment: 'bg-blue-50 border-blue-200 text-blue-700',
  proof_of_delivery: 'bg-green-50 border-green-200 text-green-700',
  customer_communication: 'bg-purple-50 border-purple-200 text-purple-700',
  invoice: 'bg-amber-50 border-amber-200 text-amber-700',
  auth_proof: 'bg-indigo-50 border-indigo-200 text-indigo-700',
  default: 'bg-gray-50 border-gray-200 text-gray-700',
};

function formatEvidenceType(type) {
  return (type || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

export default function DisputeDetail() {
  const { id } = useParams();
  const { dispute, loading, error, loadDispute } = useStore();
  const [uploadType, setUploadType] = useState('');
  const [uploadUrl, setUploadUrl] = useState('');
  const [uploadMsg, setUploadMsg] = useState('');

  const loadData = useCallback(() => {
    loadDispute(id);
  }, [id, loadDispute]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (loading) return <Loading message="Loading dispute details..." />;
  if (error) return <ErrorDisplay message={error} onRetry={loadData} />;
  if (!dispute) return <ErrorDisplay message="Dispute not found" />;

  const d = dispute.dispute || dispute;
  const evidenceRequirements = dispute.evidence_requirements || [];
  const evidencePacket = dispute.evidence_packet || {};
  const winProb = dispute.win_probability;
  const diagnosis = dispute.diagnosis || {};
  const recommendation = dispute.recommendation || {};
  const anomalies = dispute.anomalies || [];
  const uploadedEvidence = d.evidence || [];

  const evidenceTypes = [
    'proof_of_shipment',
    'proof_of_delivery',
    'customer_communication',
    'invoice',
    'auth_proof',
    'refund_proof',
  ];

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

        <h1 className="text-2xl font-bold text-gray-900 mb-2">Dispute Details</h1>
        <p className="text-gray-500 mb-8">ID: {d.id}</p>

        {/* Key Info */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="card p-5">
            <p className="text-xs font-semibold text-gray-400 uppercase mb-1">Amount</p>
            <p className="text-2xl font-bold text-gray-900">
              Rs {Number(d.amount || 0).toLocaleString('en-IN')}
            </p>
          </div>
          <div className="card p-5">
            <p className="text-xs font-semibold text-gray-400 uppercase mb-1">Status</p>
            <span className={`status-badge ${statusColors[d.current_status] || 'bg-gray-100 text-gray-800'}`}>
              {(d.current_status || 'unknown').replace(/_/g, ' ').toUpperCase()}
            </span>
          </div>
          <div className="card p-5">
            <p className="text-xs font-semibold text-gray-400 uppercase mb-1">Reason Code</p>
            <p className="text-2xl font-bold text-gray-900">{d.reason_code || '-'}</p>
          </div>
          <div className="card p-5">
            <p className="text-xs font-semibold text-gray-400 uppercase mb-1">Win Probability</p>
            <p className={`text-2xl font-bold ${
              winProb >= 0.7 ? 'text-green-600' : winProb >= 0.4 ? 'text-amber-600' : 'text-red-600'
            }`}>
              {winProb !== undefined ? `${Math.round(winProb * 100)}%` : 'N/A'}
            </p>
          </div>
        </div>

        <div className="card p-6 mb-8">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Timeline</h2>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-gray-400 font-semibold">Filed At</p>
              <p className="text-gray-900">{d.filed_at ? new Date(d.filed_at).toLocaleString() : '-'}</p>
            </div>
            <div>
              <p className="text-gray-400 font-semibold">Evidence Deadline</p>
              <p className="text-red-600 font-semibold">
                {d.evidence_deadline ? new Date(d.evidence_deadline).toLocaleString() : '-'}
              </p>
            </div>
            <div>
              <p className="text-gray-400 font-semibold">Resolution Deadline</p>
              <p className="text-gray-900">{d.resolution_deadline ? new Date(d.resolution_deadline).toLocaleString() : '-'}</p>
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

        {/* Evidence Requirements */}
        {evidenceRequirements.length > 0 && (
          <div className="card p-6 mb-8">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Evidence Requirements</h2>
            <div className="space-y-3">
              {evidenceRequirements.map((req, idx) => {
                const isUploaded = uploadedEvidence.some(e => e.evidence_type === req.type);
                return (
                  <div key={idx} className={`flex items-center gap-3 p-3 rounded-lg border ${
                    isUploaded ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'
                  }`}>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      isUploaded ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-500'
                    }`}>
                      {isUploaded ? (
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      ) : (
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                        </svg>
                      )}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-semibold text-gray-900">
                        {formatEvidenceType(req.type)}
                        {req.required && <span className="text-red-500 ml-1">*</span>}
                      </p>
                      {req.examples && (
                        <p className="text-xs text-gray-500 mt-0.5">
                          Examples: {req.examples.join(', ')}
                        </p>
                      )}
                    </div>
                    <span className={`status-badge text-xs ${
                      isUploaded ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {isUploaded ? 'UPLOADED' : 'MISSING'}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Upload Evidence */}
        <div className="card p-6 mb-8">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Upload Evidence</h2>
          <div className="flex gap-3">
            <select
              value={uploadType}
              onChange={(e) => setUploadType(e.target.value)}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Select evidence type...</option>
              {evidenceTypes.map(t => (
                <option key={t} value={t}>{formatEvidenceType(t)}</option>
              ))}
            </select>
            <input
              type="text"
              value={uploadUrl}
              onChange={(e) => setUploadUrl(e.target.value)}
              placeholder="File URL"
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <button className="btn-primary whitespace-nowrap">Upload</button>
          </div>
          {uploadMsg && <p className="text-sm text-green-600 mt-2">{uploadMsg}</p>}
        </div>

        {/* Diagnosis */}
        {diagnosis.root_cause_category && (
          <div className="card p-6 mb-8">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Root Cause Diagnosis</h2>
            <div className="bg-blue-50 rounded-lg p-5 border-l-4 border-blue-500">
              <div className="flex items-center gap-3 mb-2">
                <p className="text-base font-semibold text-gray-900">
                  {diagnosis.root_cause_category.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
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
        )}

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
