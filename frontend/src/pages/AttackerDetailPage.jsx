import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Users, ArrowLeft, Shield, Radio, Terminal, Calendar, Layers, Activity } from 'lucide-react';
import api from '../services/api';
import SeverityBadge from '../components/common/SeverityBadge';
import IntentBadge from '../components/common/IntentBadge';
import RiskIndicator from '../components/common/RiskIndicator';
import SessionTable from '../components/sessions/SessionTable';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';

export default function AttackerDetailPage() {
  const { sourceIp } = useParams();
  const [attacker, setAttacker] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAttackerData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [attackerData, sessionsData] = await Promise.all([
        api.getAttacker(sourceIp),
        api.getSessions({ source_ip: sourceIp, limit: 50 }),
      ]);

      setAttacker(attackerData);
      setSessions(sessionsData.items || []);
    } catch (err) {
      setError(err.message || `Failed to retrieve attacker profile for ${sourceIp}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAttackerData();
  }, [sourceIp]);

  if (loading) {
    return <LoadingState message={`Profiling threat activity for host ${sourceIp}...`} />;
  }

  if (error || !attacker) {
    return <ErrorState message={error || 'Attacker profile not found.'} onRetry={fetchAttackerData} />;
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <Link
        to="/attackers"
        className="inline-flex items-center gap-1.5 text-xs font-mono text-slate-400 hover:text-purple-400 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Attacker Profiles
      </Link>

      {/* Attacker Hero Header Card */}
      <div className="bg-[#111726] border border-[#1f293d] rounded-lg p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-purple-950/40 border border-purple-800/60 rounded text-purple-400">
              <Users className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-lg font-bold font-mono text-slate-100">
                Attacker IP: <span className="text-purple-400">{attacker.source_ip}</span>
              </h1>
              <div className="flex items-center gap-3 text-xs text-slate-400 font-mono mt-0.5">
                <span>First Seen: {new Date(attacker.first_seen).toLocaleString()}</span>
                <span>&bull;</span>
                <span>Last Seen: {new Date(attacker.last_seen).toLocaleString()}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4 bg-[#0d121d] border border-[#1f293d] rounded-lg p-3">
            <div>
              <div className="text-[10px] uppercase font-mono text-slate-400">Peak Risk Score</div>
              <RiskIndicator score={attacker.maximum_risk} size="lg" />
            </div>
            <div className="border-l border-[#1f293d] pl-4">
              <div className="text-[10px] uppercase font-mono text-slate-400 mb-1">Threat Tier</div>
              <SeverityBadge severity={attacker.severity} />
            </div>
          </div>
        </div>

        {/* Aggregated Host Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6 pt-6 border-t border-[#1f293d] text-xs font-mono">
          <div>
            <span className="text-slate-500 block text-[11px]">Total Honeypot Sessions</span>
            <span className="text-slate-200 font-semibold">{attacker.total_sessions}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[11px]">Total Ingested Events</span>
            <span className="text-slate-200 font-semibold">{attacker.total_events}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[11px]">Average Risk Score</span>
            <span className="text-amber-400 font-semibold">{attacker.average_risk}/100</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[11px]">Dominant Intent</span>
            <div className="mt-1 font-sans">
              <IntentBadge intent={attacker.dominant_intent} />
            </div>
          </div>
        </div>
      </div>

      {/* Associated Sessions */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Radio className="w-4 h-4 text-cyan-400" />
            Sessions Originating from {attacker.source_ip}
          </h2>
          <span className="text-xs font-mono text-slate-400">{sessions.length} sessions</span>
        </div>
        <SessionTable sessions={sessions} />
      </div>
    </div>
  );
}
