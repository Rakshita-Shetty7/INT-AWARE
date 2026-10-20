import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  Radio,
  Users,
  Terminal,
  ShieldAlert,
  AlertOctagon,
  Flame,
  Activity,
  PieChart as PieIcon,
  BarChart3,
  Wifi,
  Sparkles,
  Share2,
  FlaskConical,
  TrendingUp,
  Cpu,
} from 'lucide-react';
import api from '../services/api';
import useWebSocket from '../hooks/useWebSocket';
import StatCard from '../components/common/StatCard';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import RecentEvents from '../components/dashboard/RecentEvents';
import RecentAlerts from '../components/dashboard/RecentAlerts';
import IntentDistributionChart from '../components/charts/IntentDistributionChart';
import SeverityChart from '../components/charts/SeverityChart';
import AttackTimeline from '../components/charts/AttackTimeline';
import CopilotModal from '../components/copilot/CopilotModal';

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [recentEvents, setRecentEvents] = useState([]);
  const [recentAlerts, setRecentAlerts] = useState([]);
  const [intentData, setIntentData] = useState([]);
  const [severityData, setSeverityData] = useState([]);
  const [timelineData, setTimelineData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [copilotOpen, setCopilotOpen] = useState(false);

  const fetchDashboardData = async (silent = false) => {
    try {
      if (!silent) setLoading(true);
      setError(null);

      const [statsRes, eventsRes, alertsRes, intentsRes, severityRes, timelineRes] =
        await Promise.allSettled([
          api.getDashboardStats(),
          api.getRecentEvents(8),
          api.getAlerts({ limit: 5 }),
          api.getIntentAnalytics(),
          api.getSeverityAnalytics(),
          api.getTimelineAnalytics(),
        ]);

      if (statsRes.status === 'fulfilled') setStats(statsRes.value);
      if (eventsRes.status === 'fulfilled') setRecentEvents(eventsRes.value);
      if (alertsRes.status === 'fulfilled') setRecentAlerts(alertsRes.value.items || []);
      if (intentsRes.status === 'fulfilled') setIntentData(intentsRes.value);
      if (severityRes.status === 'fulfilled') setSeverityData(severityRes.value);
      if (timelineRes.status === 'fulfilled') setTimelineData(timelineRes.value);

      if (statsRes.status === 'rejected') {
        throw new Error(statsRes.reason?.message || 'Failed to reach API server');
      }
    } catch (err) {
      setError(err.message || 'Unable to connect to FastAPI deception backend.');
    } finally {
      if (!silent) setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    // Poll every 8s so the dashboard reflects freshly ingested attacks even if the
    // live WebSocket stream is unavailable (e.g. behind a proxy that drops upgrades).
    const pollId = setInterval(() => fetchDashboardData(true), 8000);
    return () => clearInterval(pollId);
  }, []);

  // ---------------------------------------------------------------------------
  // Real-Time WebSocket Handlers
  // ---------------------------------------------------------------------------

  const handleLiveEvent = useCallback((incomingEvent) => {
    if (!incomingEvent || incomingEvent.type !== 'event') return;

    // 1. Update Recent Ingested Events (Deduplicate by event_id)
    setRecentEvents((prev) => {
      const exists = prev.some((e) => e.event_id === incomingEvent.event_id);
      if (exists) return prev;
      return [incomingEvent, ...prev.slice(0, 7)];
    });

    // 2. Increment stats counters
    setStats((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        total_events: (prev.total_events || 0) + 1,
      };
    });

    // 3. Update intent chart distribution in-place
    setIntentData((prev) => {
      if (!incomingEvent.intent) return prev;
      const targetIntent = incomingEvent.intent;
      const existing = prev.find((item) => item.intent === targetIntent);
      let updated;
      if (existing) {
        updated = prev.map((item) =>
          item.intent === targetIntent ? { ...item, count: item.count + 1 } : item
        );
      } else {
        updated = [...prev, { intent: targetIntent, count: 1, percentage: 0 }];
      }
      const newTotal = updated.reduce((sum, item) => sum + item.count, 0);
      return updated.map((item) => ({
        ...item,
        percentage: Number(((item.count / newTotal) * 100).toFixed(1)),
      }));
    });
  }, []);

  const handleLiveAlert = useCallback((incomingAlert) => {
    if (!incomingAlert || incomingAlert.type !== 'alert') return;

    // Prepend to recent alerts
    setRecentAlerts((prev) => {
      const exists = prev.some((a) => a.alert_id === incomingAlert.alert_id);
      if (exists) return prev;
      return [incomingAlert, ...prev.slice(0, 4)];
    });

    // Increment open alerts & critical count
    setStats((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        open_alerts: (prev.open_alerts || 0) + 1,
        critical_sessions: (prev.critical_sessions || 0) + 1,
      };
    });
  }, []);

  // Connect WebSockets
  useWebSocket('/ws/events', handleLiveEvent);
  useWebSocket('/ws/alerts', handleLiveAlert);

  if (loading && !stats) {
    return <LoadingState message="Connecting to honeypot telemetry stream..." />;
  }

  if (error && !stats) {
    return <ErrorState message={error} onRetry={fetchDashboardData} />;
  }

  return (
    <div className="space-y-6">
      {/* Premium Command Center Banner */}
      <div className="relative overflow-hidden bg-gradient-to-r from-[#0d1424] via-[#111726] to-[#0d1424] border border-cyan-800/50 p-5 rounded-2xl shadow-xl shadow-cyan-950/20">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
              <span className="text-xs font-mono font-bold text-cyan-400 tracking-wider uppercase">
                CYBERSECURITY COMMAND CENTER & ADAPTIVE DECEPTION
              </span>
            </div>
            <h2 className="text-lg font-bold text-slate-100 font-sans">
              Intent-Aware Threat Intelligence & Attacker Profiling Platform
            </h2>
            <p className="text-xs text-slate-400 max-w-2xl font-sans">
              Ground-truth Cowrie honeypot telemetry with Markov transition modeling, ML drift surveillance, and zero-host deception containment.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            <button
              onClick={() => setCopilotOpen(true)}
              className="px-4 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white rounded-lg text-xs font-mono font-semibold flex items-center gap-2 shadow-lg shadow-cyan-950/60 transition-all"
            >
              <Sparkles className="w-4 h-4 text-cyan-200 animate-pulse" />
              <span>Ask AI Copilot</span>
            </button>
            <Link
              to="/analytics"
              className="px-3.5 py-2 bg-[#162032] border border-[#23324f] hover:border-cyan-700/60 text-slate-200 rounded-lg text-xs font-mono flex items-center gap-2 transition-colors"
            >
              <Share2 className="w-3.5 h-3.5 text-cyan-400" />
              <span>Campaign Graph</span>
            </Link>
            <Link
              to="/deception"
              className="px-3.5 py-2 bg-[#162032] border border-[#23324f] hover:border-emerald-700/60 text-slate-200 rounded-lg text-xs font-mono flex items-center gap-2 transition-colors"
            >
              <FlaskConical className="w-3.5 h-3.5 text-emerald-400" />
              <span>Deception Lab</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Top Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <StatCard
          title="Total Sessions"
          value={stats?.total_sessions}
          icon={Radio}
          color="cyan"
          subtitle="Honeypot connections"
        />
        <StatCard
          title="Active Sessions"
          value={stats?.active_sessions}
          icon={Activity}
          color="blue"
          subtitle="Live connections"
        />
        <StatCard
          title="Total Attackers"
          value={stats?.total_attackers}
          icon={Users}
          color="purple"
          subtitle="Distinct source IPs"
        />
        <StatCard
          title="Total Events"
          value={stats?.total_events}
          icon={Terminal}
          color="emerald"
          subtitle="Analyzed actions"
        />
        <StatCard
          title="High Risk"
          value={stats?.high_risk_sessions}
          icon={Flame}
          color="orange"
          subtitle="Risk 50-74"
        />
        <StatCard
          title="Critical Alerts"
          value={stats?.open_alerts}
          icon={AlertOctagon}
          color="rose"
          subtitle="Risk >= 75"
        />
      </div>

      {/* Main Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Attack Activity Timeline */}
        <div className="lg:col-span-2 bg-[#111726] border border-[#1f293d] rounded-lg p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-semibold text-slate-200">Attack Telemetry Timeline</h2>
              <p className="text-xs text-slate-400">Events & active sessions volume</p>
            </div>
            <Activity className="w-4 h-4 text-cyan-400" />
          </div>
          <AttackTimeline data={timelineData} />
        </div>

        {/* Intent Distribution */}
        <div className="bg-[#111726] border border-[#1f293d] rounded-lg p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-semibold text-slate-200">Intent Distribution</h2>
              <p className="text-xs text-slate-400">Classified attacker goals</p>
            </div>
            <PieIcon className="w-4 h-4 text-cyan-400" />
          </div>
          <IntentDistributionChart data={intentData} />
        </div>
      </div>

      {/* Secondary Row: Severity Distribution & Live Alerts / Events */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Severity Distribution */}
        <div className="bg-[#111726] border border-[#1f293d] rounded-lg p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-semibold text-slate-200">Threat Severity Tiers</h2>
              <p className="text-xs text-slate-400">Evaluated session risk levels</p>
            </div>
            <BarChart3 className="w-4 h-4 text-amber-400" />
          </div>
          <SeverityChart data={severityData} />
        </div>

        {/* Recent Alerts */}
        <div className="bg-[#111726] border border-[#1f293d] rounded-lg p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-semibold text-slate-200">High Risk Alerts</h2>
              <p className="text-xs text-slate-400">Threshold: Risk Score &ge; 75</p>
            </div>
            <ShieldAlert className="w-4 h-4 text-rose-400" />
          </div>
          <RecentAlerts alerts={recentAlerts} />
        </div>

        {/* Recent Honeypot Ingested Events */}
        <div className="bg-[#111726] border border-[#1f293d] rounded-lg p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-semibold text-slate-200">Live Ingested Telemetry</h2>
              <p className="text-xs text-slate-400">Streaming real-time actions</p>
            </div>
            <Terminal className="w-4 h-4 text-emerald-400" />
          </div>
          <RecentEvents events={recentEvents} />
        </div>
      </div>
      <CopilotModal isOpen={copilotOpen} onClose={() => setCopilotOpen(false)} />
    </div>
  );
}
