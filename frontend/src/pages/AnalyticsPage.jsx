import React, { useEffect, useState } from 'react';
import { BarChart3, PieChart as PieIcon, Activity, RefreshCw, Grid, Layers, ShieldAlert } from 'lucide-react';
import api from '../services/api';
import IntentDistributionChart from '../components/charts/IntentDistributionChart';
import SeverityChart from '../components/charts/SeverityChart';
import AttackTimeline from '../components/charts/AttackTimeline';
import StageDistributionChart from '../components/charts/StageDistributionChart';
import RiskDistributionChart from '../components/charts/RiskDistributionChart';
import RiskHeatmap from '../components/charts/RiskHeatmap';
import IntentBadge from '../components/common/IntentBadge';
import SeverityBadge from '../components/common/SeverityBadge';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';

export default function AnalyticsPage() {
  const [intents, setIntents] = useState([]);
  const [severities, setSeverities] = useState([]);
  const [timeline, setTimeline] = useState([]);
  const [stages, setStages] = useState([]);
  const [riskDistribution, setRiskDistribution] = useState([]);
  const [heatmapData, setHeatmapData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);

      const [
        intentsRes,
        severitiesRes,
        timelineRes,
        stagesRes,
        riskDistRes,
        heatmapRes,
      ] = await Promise.all([
        api.getIntentAnalytics(),
        api.getSeverityAnalytics(),
        api.getTimelineAnalytics(),
        api.getStageAnalytics(),
        api.getRiskDistribution(),
        api.getRiskHeatmap(),
      ]);

      setIntents(intentsRes || []);
      setSeverities(severitiesRes || []);
      setTimeline(timelineRes || []);
      setStages(stagesRes || []);
      setRiskDistribution(riskDistRes || []);
      setHeatmapData(heatmapRes || []);
    } catch (err) {
      setError(err.message || 'Failed to load threat analytics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  if (loading) {
    return <LoadingState message="Aggregating threat intelligence analytics..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchAnalytics} />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-cyan-400" />
            Threat Intelligence Analytics & Security Insights
          </h1>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Cross-dimensional analysis across Honeypot Telemetry, Behavioral Intent, MITRE Attack Stages, and Risk Scores
          </p>
        </div>
        <button
          onClick={fetchAnalytics}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#111726] border border-[#1f293d] hover:border-cyan-800 text-xs font-mono text-slate-300 hover:text-cyan-300 rounded transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh
        </button>
      </div>

      {/* Main Timeline Chart */}
      <div className="bg-[#111726] border border-[#1f293d] rounded-lg p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <Activity className="w-4 h-4 text-cyan-400" />
              Attack Telemetry Frequency & Active Sessions Over Time
            </h2>
            <p className="text-xs text-slate-400 font-mono">Time-series buckets of honeypot actions and peak risk scores</p>
          </div>
        </div>
        <AttackTimeline data={timeline} />
      </div>

      {/* FEATURE 4: Risk x Intent Matrix Heatmap */}
      <div className="bg-[#111726] border border-[#1f293d] rounded-lg p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <Grid className="w-4 h-4 text-rose-400" />
              Intent &times; Threat Risk Matrix Heatmap
            </h2>
            <p className="text-xs text-slate-400 font-mono">
              Categorical risk intensity, average score, and severity distribution by classified intent
            </p>
          </div>
        </div>
        <RiskHeatmap data={heatmapData} />
      </div>

      {/* Grid: Attack Stage Distribution & Risk Score Buckets */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Attack Stage Progression Distribution */}
        <div className="bg-[#111726] border border-[#1f293d] rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <Layers className="w-4 h-4 text-purple-400" />
                MITRE Attack Stage Distribution
              </h2>
              <p className="text-xs text-slate-400 font-mono">Volume of sessions reaching each tactical lifecycle stage</p>
            </div>
          </div>
          <StageDistributionChart data={stages} />
        </div>

        {/* Threat Risk Distribution Buckets */}
        <div className="bg-[#111726] border border-[#1f293d] rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-amber-400" />
                Threat Risk Score Distribution
              </h2>
              <p className="text-xs text-slate-400 font-mono">Distribution across 4 standardized risk score tiers</p>
            </div>
          </div>
          <RiskDistributionChart data={riskDistribution} />
        </div>
      </div>

      {/* Grid: Intent & Severity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Intent Distribution */}
        <div className="bg-[#111726] border border-[#1f293d] rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <PieIcon className="w-4 h-4 text-cyan-400" />
                Classified Attacker Intent Distribution
              </h2>
              <p className="text-xs text-slate-400 font-mono">Categorical percentage breakdowns</p>
            </div>
          </div>
          <IntentDistributionChart data={intents} />

          {/* Breakdown Table */}
          <div className="border-t border-[#1f293d] pt-4">
            <table className="w-full text-xs text-left">
              <thead className="text-[11px] font-mono uppercase text-slate-500 border-b border-[#1f293d]">
                <tr>
                  <th className="pb-2">Intent Category</th>
                  <th className="pb-2 text-right">Event Count</th>
                  <th className="pb-2 text-right">Share</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1f293d]/50 font-mono">
                {intents.map((item) => (
                  <tr key={item.intent} className="hover:bg-[#0d121d]">
                    <td className="py-2 font-sans">
                      <IntentBadge intent={item.intent} />
                    </td>
                    <td className="py-2 text-right text-slate-200 font-bold">{item.count}</td>
                    <td className="py-2 text-right text-cyan-400">{item.percentage}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Severity Distribution */}
        <div className="bg-[#111726] border border-[#1f293d] rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-amber-400" />
                Session Risk Severity Tiers
              </h2>
              <p className="text-xs text-slate-400 font-mono">Evaluated threat severity breakdown</p>
            </div>
          </div>
          <SeverityChart data={severities} />

          {/* Breakdown Table */}
          <div className="border-t border-[#1f293d] pt-4">
            <table className="w-full text-xs text-left">
              <thead className="text-[11px] font-mono uppercase text-slate-500 border-b border-[#1f293d]">
                <tr>
                  <th className="pb-2">Severity Tier</th>
                  <th className="pb-2 text-right">Session Count</th>
                  <th className="pb-2 text-right">Share</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1f293d]/50 font-mono">
                {severities.map((item) => (
                  <tr key={item.severity} className="hover:bg-[#0d121d]">
                    <td className="py-2 font-sans">
                      <SeverityBadge severity={item.severity} />
                    </td>
                    <td className="py-2 text-right text-slate-200 font-bold">{item.count}</td>
                    <td className="py-2 text-right text-amber-400">{item.percentage}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
