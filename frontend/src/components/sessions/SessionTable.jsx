import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Terminal } from 'lucide-react';
import SeverityBadge from '../common/SeverityBadge';
import IntentBadge from '../common/IntentBadge';
import RiskIndicator from '../common/RiskIndicator';
import EmptyState from '../common/EmptyState';

export default function SessionTable({ sessions = [] }) {
  if (!sessions || sessions.length === 0) {
    return <EmptyState title="No Sessions Found" message="No attacker sessions matching the query criteria." />;
  }

  return (
    <div className="overflow-x-auto border border-[#1f293d] rounded-lg bg-[#0d121d]">
      <table className="w-full text-left text-xs text-slate-300">
        <thead className="bg-[#111726] border-b border-[#1f293d] text-[11px] uppercase tracking-wider text-slate-400 font-mono">
          <tr>
            <th className="py-3 px-4">Session ID</th>
            <th className="py-3 px-4">Source IP</th>
            <th className="py-3 px-4">Dominant Intent</th>
            <th className="py-3 px-4">Attack Stage</th>
            <th className="py-3 px-4">Risk</th>
            <th className="py-3 px-4">Severity</th>
            <th className="py-3 px-4 text-center">Events / Cmds</th>
            <th className="py-3 px-4">Last Seen</th>
            <th className="py-3 px-4 text-right">Action</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[#1f293d]/60 font-mono">
          {sessions.map((sess) => (
            <tr
              key={sess.session_id}
              className="hover:bg-[#161f33]/60 transition-colors"
            >
              <td className="py-3 px-4 font-semibold text-cyan-400">
                <Link to={`/sessions/${sess.session_id}`} className="hover:underline">
                  {sess.session_id?.substring(0, 10) || 'unknown'}
                </Link>
              </td>
              <td className="py-3 px-4 text-slate-200">
                {sess.source_ip || '127.0.0.1'}
              </td>
              <td className="py-3 px-4 font-sans">
                <IntentBadge intent={sess.dominant_intent} />
              </td>
              <td className="py-3 px-4 text-slate-400 text-[11px]">
                {sess.current_attack_stage}
              </td>
              <td className="py-3 px-4">
                <RiskIndicator score={sess.risk_score} size="sm" />
              </td>
              <td className="py-3 px-4 font-sans">
                <SeverityBadge severity={sess.severity} />
              </td>
              <td className="py-3 px-4 text-center text-slate-400">
                <span>{sess.total_events}</span> / <span className="text-cyan-300">{sess.command_count}</span>
              </td>
              <td className="py-3 px-4 text-slate-500 text-[11px]">
                {sess.last_seen ? new Date(sess.last_seen).toLocaleTimeString() : 'N/A'}
              </td>
              <td className="py-3 px-4 text-right">
                <Link
                  to={`/sessions/${sess.session_id}`}
                  className="inline-flex items-center gap-1 px-2.5 py-1 bg-[#111726] border border-[#1f293d] hover:border-cyan-700 text-slate-300 hover:text-cyan-300 rounded text-[11px] font-sans transition-colors"
                >
                  Inspect
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
