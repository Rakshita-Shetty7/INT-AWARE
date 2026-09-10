import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, ShieldAlert } from 'lucide-react';
import SeverityBadge from '../common/SeverityBadge';
import IntentBadge from '../common/IntentBadge';
import RiskIndicator from '../common/RiskIndicator';
import EmptyState from '../common/EmptyState';

export default function AttackerTable({ attackers = [] }) {
  if (!attackers || attackers.length === 0) {
    return <EmptyState title="No Attacker Profiles" message="No distinct attacker hosts identified." icon={ShieldAlert} />;
  }

  return (
    <div className="overflow-x-auto border border-[#1f293d] rounded-lg bg-[#0d121d]">
      <table className="w-full text-left text-xs text-slate-300">
        <thead className="bg-[#111726] border-b border-[#1f293d] text-[11px] uppercase tracking-wider text-slate-400 font-mono">
          <tr>
            <th className="py-3 px-4">Attacker IP</th>
            <th className="py-3 px-4">Total Sessions</th>
            <th className="py-3 px-4">Total Events</th>
            <th className="py-3 px-4">Peak Risk</th>
            <th className="py-3 px-4">Avg Risk</th>
            <th className="py-3 px-4">Dominant Intent</th>
            <th className="py-3 px-4">Stage</th>
            <th className="py-3 px-4">Severity</th>
            <th className="py-3 px-4">Last Seen</th>
            <th className="py-3 px-4 text-right">Action</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[#1f293d]/60 font-mono">
          {attackers.map((att) => (
            <tr
              key={att.source_ip}
              className="hover:bg-[#161f33]/60 transition-colors"
            >
              <td className="py-3 px-4 font-semibold text-cyan-400">
                <Link to={`/attackers/${att.source_ip}`} className="hover:underline">
                  {att.source_ip}
                </Link>
              </td>
              <td className="py-3 px-4 text-slate-200">
                {att.total_sessions}
              </td>
              <td className="py-3 px-4 text-slate-300">
                {att.total_events}
              </td>
              <td className="py-3 px-4">
                <RiskIndicator score={att.maximum_risk} size="sm" />
              </td>
              <td className="py-3 px-4 text-slate-400">
                {att.average_risk}/100
              </td>
              <td className="py-3 px-4 font-sans">
                <IntentBadge intent={att.dominant_intent} />
              </td>
              <td className="py-3 px-4 text-slate-400 text-[11px]">
                {att.current_stage}
              </td>
              <td className="py-3 px-4 font-sans">
                <SeverityBadge severity={att.severity} />
              </td>
              <td className="py-3 px-4 text-slate-500 text-[11px]">
                {att.last_seen ? new Date(att.last_seen).toLocaleTimeString() : 'N/A'}
              </td>
              <td className="py-3 px-4 text-right">
                <Link
                  to={`/attackers/${att.source_ip}`}
                  className="inline-flex items-center gap-1 px-2.5 py-1 bg-[#111726] border border-[#1f293d] hover:border-cyan-700 text-slate-300 hover:text-cyan-300 rounded text-[11px] font-sans transition-colors"
                >
                  Profile
                  <ArrowRight className="w-3 h-3" />
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
