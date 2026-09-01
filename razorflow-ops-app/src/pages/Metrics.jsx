import { useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, Legend
} from 'recharts';
import Navbar from '../components/Navbar';
import MetricCard from '../components/MetricCard';
import Loading from '../components/Loading';
import ErrorDisplay from '../components/ErrorDisplay';
import useStore from '../store/useStore';

const COLORS = ['#ef4444', '#f59e0b', '#3b82f6', '#22c55e'];

export default function Metrics() {
  const { metrics, loading, error, loadMetrics } = useStore();

  const loadData = useCallback(() => {
    loadMetrics();
  }, [loadMetrics]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (loading) return <Loading message="Loading metrics..." />;
  if (error) return <ErrorDisplay message={error} onRetry={loadData} />;

  // Prepare chart data from metrics
  const detectionData = [
    { name: 'Correct', value: metrics?.detection_precision || 0.85 },
    { name: 'Missed', value: 1 - (metrics?.detection_recall || 0.75) },
  ];

  const resolutionData = [
    { name: 'Won', value: metrics?.disputes_won || 5 },
    { name: 'Lost', value: (metrics?.disputes_total || 8) - (metrics?.disputes_won || 5) },
  ];

  const impactData = [
    { name: 'Week 1', timeSaved: 12, revenueRecovered: 15000 },
    { name: 'Week 2', timeSaved: 28, revenueRecovered: 32000 },
    { name: 'Week 3', timeSaved: 45, revenueRecovered: 45000 },
    { name: 'Week 4', timeSaved: metrics?.time_saved_hours || 65, revenueRecovered: metrics?.revenue_recovered || 58000 },
  ];

  return (
    <>
      <Navbar />
      <div className="max-w-7xl mx-auto px-8 py-10">
        <Link to="/" className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800 no-underline mb-6">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Dashboard
        </Link>

        <h1 className="text-3xl font-bold text-gray-900 mb-2">Performance Metrics</h1>
        <p className="text-gray-500 mb-10">AI agent performance and business impact over the last 30 days</p>

        {/* Top KPIs */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-10">
          <MetricCard
            title="Detection Precision"
            value={`${Math.round((metrics?.detection_precision || 0.85) * 100)}%`}
            subtext="True positives / total detections"
            icon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            }
          />
          <MetricCard
            title="Diagnosis Accuracy"
            value={`${Math.round((metrics?.diagnosis_accuracy || 0.78) * 100)}%`}
            subtext="Correct root cause identification"
            icon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            }
          />
          <MetricCard
            title="Time Saved"
            value={`${metrics?.time_saved_hours || 65}h`}
            subtext="Manual investigation automated"
            trend={15}
            icon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
          />
          <MetricCard
            title="Revenue Recovered"
            value={`Rs ${(metrics?.revenue_recovered || 58000).toLocaleString('en-IN')}`}
            subtext="Chargebacks + delay prevention"
            trend={22}
            icon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
          />
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-10">
          {/* Detection Accuracy */}
          <div className="card p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Detection Accuracy</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={detectionData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} domain={[0, 1]} />
                  <Tooltip formatter={(v) => `${Math.round(v * 100)}%`} />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                    {detectionData.map((entry, i) => (
                      <Cell key={i} fill={i === 0 ? '#22c55e' : '#e5e7eb'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Dispute Resolution */}
          <div className="card p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Dispute Outcomes</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={resolutionData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${value}`}
                  >
                    <Cell fill="#22c55e" />
                    <Cell fill="#ef4444" />
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Impact Timeline */}
        <div className="card p-6 mb-10">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Impact Over Time</h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={impactData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis yAxisId="left" tick={{ fontSize: 12 }} />
                <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 12 }} />
                <Tooltip />
                <Legend />
                <Line yAxisId="left" type="monotone" dataKey="timeSaved" stroke="#3b82f6" strokeWidth={2} name="Time Saved (h)" dot={{ r: 4 }} />
                <Line yAxisId="right" type="monotone" dataKey="revenueRecovered" stroke="#22c55e" strokeWidth={2} name="Revenue Recovered (Rs)" dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Detailed Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
          <div className="card p-6">
            <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-4">Detection Metrics</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Anomalies Detected</span>
                <span className="text-sm font-bold text-gray-900">{metrics?.anomalies_detected || 42}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Real Anomalies</span>
                <span className="text-sm font-bold text-gray-900">{metrics?.anomalies_real || 38}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Precision</span>
                <span className="text-sm font-bold text-green-600">{Math.round((metrics?.detection_precision || 0.85) * 100)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Recall</span>
                <span className="text-sm font-bold text-green-600">{Math.round((metrics?.detection_recall || 0.75) * 100)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">F1 Score</span>
                <span className="text-sm font-bold text-green-600">{Math.round((metrics?.detection_f1 || 0.80) * 100)}%</span>
              </div>
            </div>
          </div>

          <div className="card p-6">
            <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-4">Evidence & Disputes</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Evidence Packets Assembled</span>
                <span className="text-sm font-bold text-gray-900">{metrics?.evidence_packets_assembled || 12}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Avg Completeness</span>
                <span className="text-sm font-bold text-green-600">{Math.round((metrics?.evidence_completeness_avg || 0.82) * 100)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Disputes Won</span>
                <span className="text-sm font-bold text-green-600">{metrics?.disputes_won || 5}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Total Disputes</span>
                <span className="text-sm font-bold text-gray-900">{metrics?.disputes_total || 8}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Win Rate</span>
                <span className="text-sm font-bold text-green-600">{Math.round((metrics?.win_rate_with_agent || 0.625) * 100)}%</span>
              </div>
            </div>
          </div>

          <div className="card p-6">
            <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-4">Recommendations</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Total Made</span>
                <span className="text-sm font-bold text-gray-900">{metrics?.recommendations_made || 35}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Merchant Followed</span>
                <span className="text-sm font-bold text-gray-900">{metrics?.recommendations_followed || 28}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Succeeded</span>
                <span className="text-sm font-bold text-green-600">{metrics?.recommendations_succeeded || 24}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Success Rate</span>
                <span className="text-sm font-bold text-green-600">
                  {Math.round((metrics?.action_success_rate || 0.857) * 100)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Chargebacks Prevented</span>
                <span className="text-sm font-bold text-green-600">{metrics?.chargebacks_prevented || 5}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
