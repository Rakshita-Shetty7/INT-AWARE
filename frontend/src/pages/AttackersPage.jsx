import React, { useEffect, useState } from 'react';
import { Users, Search, RefreshCw, ChevronLeft, ChevronRight } from 'lucide-react';
import api from '../services/api';
import AttackerTable from '../components/attackers/AttackerTable';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';

export default function AttackersPage() {
  const [attackers, setAttackers] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [limit] = useState(15);
  const [sourceIp, setSourceIp] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAttackers = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = { page, limit };
      if (sourceIp.trim()) params.source_ip = sourceIp.trim();

      const data = await api.getAttackers(params);
      setAttackers(data.items || []);
      setTotal(data.total || 0);
      setTotalPages(data.total_pages || 1);
    } catch (err) {
      setError(err.message || 'Failed to fetch attacker profiles from backend.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAttackers();
  }, [page]);

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    fetchAttackers();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Users className="w-5 h-5 text-purple-400" />
            Attacker Host Intelligence Profiles
          </h1>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Total Unique Attacker IPs: <b className="text-slate-200">{total}</b>
          </p>
        </div>
        <button
          onClick={fetchAttackers}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#111726] border border-[#1f293d] hover:border-purple-800 text-xs font-mono text-slate-300 hover:text-purple-300 rounded transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh
        </button>
      </div>

      {/* Search Toolbar */}
      <div className="bg-[#111726] border border-[#1f293d] rounded-lg p-4">
        <form onSubmit={handleSearch} className="flex gap-3 max-w-md text-xs font-mono">
          <div className="relative flex-1">
            <input
              type="text"
              placeholder="Search by IP (e.g. 127.0.0.1)"
              value={sourceIp}
              onChange={(e) => setSourceIp(e.target.value)}
              className="w-full bg-[#0d121d] border border-[#1f293d] rounded px-3 py-1.5 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-purple-500"
            />
            <Search className="w-3.5 h-3.5 text-slate-500 absolute right-2.5 top-2.5" />
          </div>
          <button
            type="submit"
            className="bg-purple-950/60 hover:bg-purple-900/60 border border-purple-700/80 text-purple-300 font-medium py-1.5 px-4 rounded transition-colors"
          >
            Search
          </button>
        </form>
      </div>

      {/* Table */}
      {loading ? (
        <LoadingState message="Fetching attacker host profiles..." />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchAttackers} />
      ) : (
        <>
          <AttackerTable attackers={attackers} />

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
                  className="px-2.5 py-1 bg-[#111726] border border-[#1f293d] disabled:opacity-40 disabled:cursor-not-allowed hover:border-purple-700 rounded flex items-center gap-1"
                >
                  <ChevronLeft className="w-3.5 h-3.5" /> Prev
                </button>
                <button
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  className="px-2.5 py-1 bg-[#111726] border border-[#1f293d] disabled:opacity-40 disabled:cursor-not-allowed hover:border-purple-700 rounded flex items-center gap-1"
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
