import React, { useEffect, useState } from 'react';
import { Radio, Search, Filter, ChevronLeft, ChevronRight, RefreshCw } from 'lucide-react';
import api from '../services/api';
import SessionTable from '../components/sessions/SessionTable';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';

export default function SessionsPage() {
  const [sessions, setSessions] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [limit] = useState(15);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filter States
  const [sourceIp, setSourceIp] = useState('');
  const [severity, setSeverity] = useState('');
  const [intent, setIntent] = useState('');

  const fetchSessions = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        page,
        limit,
      };
      if (sourceIp.trim()) params.source_ip = sourceIp.trim();
      if (severity) params.severity = severity;
      if (intent) params.intent = intent;

      const data = await api.getSessions(params);
      setSessions(data.items || []);
      setTotal(data.total || 0);
      setTotalPages(data.total_pages || 1);
    } catch (err) {
      setError(err.message || 'Failed to fetch sessions from backend.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, [page, severity, intent]);

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    fetchSessions();
  };

  const handleReset = () => {
    setSourceIp('');
    setSeverity('');
    setIntent('');
    setPage(1);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Radio className="w-5 h-5 text-cyan-400" />
            Live & Historical Attacker Sessions
          </h1>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Total Captured Sessions: <b className="text-slate-200">{total}</b>
          </p>
        </div>
        <button
          onClick={fetchSessions}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#111726] border border-[#1f293d] hover:border-cyan-800 text-xs font-mono text-slate-300 hover:text-cyan-300 rounded transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-[#111726] border border-[#1f293d] rounded-lg p-4">
        <form onSubmit={handleSearch} className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 text-xs">
          <div>
            <label className="block text-[11px] font-mono text-slate-400 mb-1">Attacker IP</label>
            <div className="relative">
              <input
                type="text"
                placeholder="e.g. 192.168.1.100"
                value={sourceIp}
                onChange={(e) => setSourceIp(e.target.value)}
                className="w-full bg-[#0d121d] border border-[#1f293d] rounded px-3 py-1.5 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-cyan-500 font-mono"
              />
              <Search className="w-3.5 h-3.5 text-slate-500 absolute right-2.5 top-2.5" />
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-mono text-slate-400 mb-1">Risk Severity</label>
            <select
              value={severity}
              onChange={(e) => {
                setSeverity(e.target.value);
                setPage(1);
              }}
              className="w-full bg-[#0d121d] border border-[#1f293d] rounded px-3 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
            >
              <option value="">All Severities</option>
              <option value="LOW">LOW</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="HIGH">HIGH</option>
              <option value="CRITICAL">CRITICAL</option>
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-mono text-slate-400 mb-1">Dominant Intent</label>
            <select
              value={intent}
              onChange={(e) => {
                setIntent(e.target.value);
                setPage(1);
              }}
              className="w-full bg-[#0d121d] border border-[#1f293d] rounded px-3 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
            >
              <option value="">All Intents</option>
              <option value="RECONNAISSANCE">RECONNAISSANCE</option>
              <option value="DISCOVERY">DISCOVERY</option>
              <option value="CREDENTIAL_ACCESS">CREDENTIAL_ACCESS</option>
              <option value="EXECUTION">EXECUTION</option>
              <option value="PRIVILEGE_ESCALATION">PRIVILEGE_ESCALATION</option>
              <option value="PERSISTENCE">PERSISTENCE</option>
              <option value="EXPLOITATION">EXPLOITATION</option>
              <option value="EXFILTRATION">EXFILTRATION</option>
              <option value="CLEANUP">CLEANUP</option>
              <option value="OTHER">OTHER</option>
            </select>
          </div>

          <div className="flex items-end gap-2">
            <button
              type="submit"
              className="flex-1 bg-cyan-950/60 hover:bg-cyan-900/60 border border-cyan-700/80 text-cyan-300 font-medium py-1.5 px-3 rounded transition-colors"
            >
              Apply Filter
            </button>
            <button
              type="button"
              onClick={handleReset}
              className="bg-[#0d121d] hover:bg-[#161f33] border border-[#1f293d] text-slate-400 py-1.5 px-3 rounded transition-colors"
            >
              Reset
            </button>
          </div>
        </form>
      </div>

      {/* Content */}
      {loading ? (
        <LoadingState message="Fetching session telemetry records..." />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchSessions} />
      ) : (
        <>
          <SessionTable sessions={sessions} />

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
                  className="px-2.5 py-1 bg-[#111726] border border-[#1f293d] disabled:opacity-40 disabled:cursor-not-allowed hover:border-cyan-700 rounded flex items-center gap-1"
                >
                  <ChevronLeft className="w-3.5 h-3.5" /> Prev
                </button>
                <button
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  className="px-2.5 py-1 bg-[#111726] border border-[#1f293d] disabled:opacity-40 disabled:cursor-not-allowed hover:border-cyan-700 rounded flex items-center gap-1"
                >
                  Next <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
