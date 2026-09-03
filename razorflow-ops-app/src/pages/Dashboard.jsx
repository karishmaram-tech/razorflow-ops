import { useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import KPICard from '../components/KPICard';
import IssuesTable from '../components/IssuesTable';
import MetricCard from '../components/MetricCard';
import RecommendationCard from '../components/RecommendationCard';
import Loading from '../components/Loading';
import ErrorDisplay from '../components/ErrorDisplay';
import useStore from '../store/useStore';

export default function Dashboard() {
  const { dashboard, connected, demoMode, loading, error, loadDashboard } = useStore();

  const loadData = useCallback(() => {
    loadDashboard();
  }, [loadDashboard]);

  useEffect(() => {
    loadData();
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, [loadData]);

  if (loading && !dashboard) return <Loading message="Loading dashboard..." />;
  if (error && !dashboard) return <ErrorDisplay message={error} onRetry={loadData} />;

  // Extract data from API response
  const critical = dashboard?.critical_anomalies?.length || 0;
  const warnings = dashboard?.warning_anomalies?.length || 0;
  const recommendations = dashboard?.top_recommendations || [];
  const allAnomalies = [
    ...(dashboard?.critical_anomalies || []),
    ...(dashboard?.warning_anomalies || []),
    ...(dashboard?.info_anomalies || []),
  ];
  const impact = dashboard?.impact_summary || {};

  return (
    <>
      <Navbar connected={connected} demoMode={demoMode} />
      <div className="max-w-7xl mx-auto px-8 py-10">
        {demoMode && (
          <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-xl flex items-center gap-3">
            <div className="w-8 h-8 bg-amber-100 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-semibold text-amber-800">Demo Mode — Backend not connected</p>
              <p className="text-xs text-amber-600">Showing sample data. Deploy the backend to see live monitoring.</p>
            </div>
          </div>
        )}
        {/* Header */}
        <div className="flex items-start justify-between mb-10">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Payment Operations Dashboard</h1>
            <p className="text-gray-500 mt-1">
              AI-powered monitoring for settlements, refunds, and disputes
            </p>
          </div>
          <div className="text-right">
            <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium border ${
              connected
                ? 'bg-green-50 border-green-200 text-green-700'
                : 'bg-red-50 border-red-200 text-red-700'
            }`}>
              <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
              {connected ? 'All systems operational' : 'Disconnected'}
            </div>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-10">
          <KPICard
            label="Critical Issues"
            value={critical}
            subtext="Requiring immediate action"
            severity="critical"
          />
          <KPICard
            label="Warnings"
            value={warnings}
            subtext="Monitor closely"
            severity="warning"
          />
          <KPICard
            label="Chargebacks Won"
            value={impact.chargebacks_prevented || 0}
            subtext={`Rs ${impact.revenue_recovered?.toLocaleString() || 0} recovered`}
            severity="success"
          />
          <KPICard
            label="Time Saved"
            value={`${impact.time_saved_hours || 0}h`}
            subtext="AI automation value"
            severity="success"
          />
        </div>

        {/* Issues Table */}
        <div className="mb-10">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-xl font-bold text-gray-900">Active Issues</h2>
            <span className="text-sm text-gray-500">{allAnomalies.length} total</span>
          </div>
          <IssuesTable issues={allAnomalies} />
        </div>

        {/* Recommendations + Next Deadline */}
        {recommendations.length > 0 && (
          <div className="mb-10">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-xl font-bold text-gray-900">Top Recommendations</h2>
              {dashboard?.next_deadline && (
                <div className="flex items-center gap-2 px-3 py-1.5 bg-amber-50 border border-amber-200 rounded-lg">
                  <svg className="w-4 h-4 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="text-sm font-medium text-amber-700">
                    Deadline: {new Date(dashboard.next_deadline).toLocaleDateString()}
                  </span>
                </div>
              )}
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {recommendations.slice(0, 4).map((rec, idx) => (
                <RecommendationCard key={rec.id || idx} recommendation={rec} />
              ))}
            </div>
          </div>
        )}

        {/* Performance Metrics */}
        <div className="mb-10">
          <h2 className="text-xl font-bold text-gray-900 mb-5">Performance Metrics</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <MetricCard
              title="Detection Accuracy"
              value="91%"
              subtext="Real issues detected correctly"
              trend={12}
              icon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              }
            />
            <MetricCard
              title="Dispute Win Rate"
              value="85%"
              subtext="With AI evidence assembly"
              trend={25}
              icon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                </svg>
              }
            />
            <MetricCard
              title="Revenue Recovered"
              value="Rs 45K"
              subtext="Chargebacks won + delays prevented"
              trend={18}
              icon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              }
            />
          </div>
        </div>

        {/* CTA Banner */}
        <div className="bg-gradient-to-br from-blue-50 via-blue-50 to-indigo-50 rounded-xl border border-blue-200 p-8 text-center mb-12">
          <h3 className="text-lg font-bold text-gray-900 mb-2">AI Operations Intelligence Active</h3>
          <p className="text-gray-600 mb-4 max-w-lg mx-auto">
            Three specialized agents are continuously monitoring your payment operations, detecting anomalies, diagnosing root causes, and recommending actions.
          </p>
          <div className="flex items-center justify-center gap-3">
            <Link to="/metrics" className="btn-primary no-underline">
              View Full Metrics
            </Link>
          </div>
        </div>
      </div>
    </>
  );
}
