import React, { useEffect, useState } from 'react';
import { AlertOctagon, RefreshCw, ShieldAlert, ArrowUpRight, ChevronLeft, ChevronRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import SeverityBadge from '../components/common/SeverityBadge';
import IntentBadge from '../components/common/IntentBadge';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import EmptyState from '../components/common/EmptyState';

export default function AlertsPage() {
  const [alerts, setAlerts] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [limit] = useState(15);
  const [status, setStatus] = useState('');
  const [severity, setSeverity] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = { page, limit };
      if (status) params.status = status;
      if (severity) params.severity = severity;

      const data = await api.getAlerts(params);
      setAlerts(data.items || []);
      setTotal(data.total || 0);
      setTotalPages(data.total_pages || 1);
    } catch (err) {
      setError(err.message || 'Failed to fetch threat alerts.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [page, status, severity]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <AlertOctagon className="w-5 h-5 text-rose-400" />
            Security & Threat Alerts
          </h1>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Trigger condition: Threat Risk Score &ge; 75 &bull; Total Alerts: <b className="text-slate-200">{total}</b>
          </p>
        </div>
        <button
          onClick={fetchAlerts}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#111726] border border-[#1f293d] hover:border-rose-800 text-xs font-mono text-slate-300 hover:text-rose-300 rounded transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh
        </button>
      </div>

      {/* Filter Bar */}
      <div className="bg-[#111726] border border-[#1f293d] rounded-lg p-4 flex gap-4 text-xs font-mono">
        <div>
          <label className="block text-[11px] text-slate-400 mb-1">Status</label>
          <select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
            className="bg-[#0d121d] border border-[#1f293d] rounded px-3 py-1.5 text-slate-200 focus:outline-none focus:border-rose-500"
          >
            <option value="">All Statuses</option>
            <option value="OPEN">OPEN</option>
            <option value="INVESTIGATING">INVESTIGATING</option>
            <option value="RESOLVED">RESOLVED</option>
          </select>
        </div>

        <div>
          <label className="block text-[11px] text-slate-400 mb-1">Severity</label>
          <select
            value={severity}
            onChange={(e) => {
              setSeverity(e.target.value);
              setPage(1);
            }}
            className="bg-[#0d121d] border border-[#1f293d] rounded px-3 py-1.5 text-slate-200 focus:outline-none focus:border-rose-500"
          >
            <option value="">All Severities</option>
            <option value="HIGH">HIGH</option>
            <option value="CRITICAL">CRITICAL</option>
          </select>
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <LoadingState message="Fetching security alerts from database..." />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchAlerts} />
      ) : alerts.length === 0 ? (
        <EmptyState
          title="Zero Critical Alerts"
          message="No threat sessions have exceeded the critical risk threshold (75/100)."
          icon={ShieldAlert}
        />
      ) : (
        <div className="space-y-3">
          {alerts.map((alt) => (
            <div
              key={alt.alert_id}
              className="bg-[#111726] border border-rose-900/50 rounded-lg p-4 hover:border-rose-700/80 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-4 text-xs"
            >
              <div className="flex items-start gap-3">
                <div className="p-2 bg-rose-950/60 border border-rose-800/80 rounded text-rose-400 flex-shrink-0">
                  <AlertOctagon className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <span className="font-mono font-bold text-rose-300">{alt.alert_id}</span>
                    <SeverityBadge severity={alt.severity} />
                    <IntentBadge intent={alt.intent} />
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300 uppercase">
                      {alt.status}
                    </span>
                  </div>
                  <p className="text-slate-200 mt-1.5 font-medium">{alt.reason}</p>
                  <div className="flex items-center gap-4 mt-2 text-[11px] text-slate-400 font-mono flex-wrap">
                    <span>IP: <b className="text-slate-300">{alt.source_ip || 'N/A'}</b></span>
                    <span>Session: <b className="text-slate-300">{alt.session_id?.substring(0, 10) || 'unknown'}</b></span>
                    <span>Trigger Risk: <b className="text-rose-400">{alt.risk_score}/100</b></span>
                    <span>Stage: <b className="text-slate-300">{alt.attack_stage}</b></span>
                    <span>Time: {new Date(alt.timestamp).toLocaleString()}</span>
                  </div>
                </div>
              </div>

              <Link
                to={`/sessions/${alt.session_id}`}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#0d121d] border border-[#1f293d] hover:border-cyan-700 text-slate-300 hover:text-cyan-300 rounded font-sans transition-colors flex-shrink-0"
              >
                Inspect Threat Session
                <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          ))}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between border-t border-[#1f293d] pt-4 text-xs font-mono text-slate-400">
              <span>
                Page <b className="text-slate-200">{page}</b> of <b className="text-slate-200">{totalPages}</b>
              </span>
              <div className="flex items-center gap-2">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="px-2.5 py-1 bg-[#111726] border border-[#1f293d] disabled:opacity-40 disabled:cursor-not-allowed hover:border-rose-700 rounded flex items-center gap-1"
                >
                  <ChevronLeft className="w-3.5 h-3.5" /> Prev
                </button>
                <button
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  className="px-2.5 py-1 bg-[#111726] border border-[#1f293d] disabled:opacity-40 disabled:cursor-not-allowed hover:border-rose-700 rounded flex items-center gap-1"
                >
                  Next <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
