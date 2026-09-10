import React from 'react';
import { AlertOctagon, ShieldAlert, ArrowUpRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import SeverityBadge from '../common/SeverityBadge';
import IntentBadge from '../common/IntentBadge';
import EmptyState from '../common/EmptyState';

export default function RecentAlerts({ alerts = [] }) {
  if (!alerts || alerts.length === 0) {
    return <EmptyState title="No Active Alerts" message="No critical or high-risk alerts have been triggered." icon={ShieldAlert} />;
  }

  return (
    <div className="space-y-2">
      {alerts.map((alt) => (
        <div
          key={alt.alert_id}
          className="bg-rose-950/20 border border-rose-900/40 rounded-md p-3 hover:border-rose-700/60 transition-colors flex items-center justify-between gap-3 text-xs"
        >
          <div className="flex items-start gap-3 min-w-0 flex-1">
            <div className="p-1.5 bg-rose-900/30 border border-rose-700/60 rounded text-rose-400 flex-shrink-0">
              <AlertOctagon className="w-4 h-4" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-mono font-semibold text-rose-200 truncate max-w-full">{alt.alert_id}</span>
                <SeverityBadge severity={alt.severity} />
                <IntentBadge intent={alt.intent} />
              </div>
              <p className="text-slate-300 mt-1 text-[11px] break-words">{alt.reason}</p>
              <div className="flex items-center gap-x-3 gap-y-1 mt-1 text-[10px] text-slate-400 font-mono flex-wrap">
                <span className="truncate">IP: {alt.source_ip || 'N/A'}</span>
                <span>Risk: <b className="text-rose-400">{alt.risk_score}/100</b></span>
                <span className="truncate">Stage: {alt.attack_stage}</span>
              </div>
            </div>
          </div>

          <Link
            to={`/sessions/${alt.session_id}`}
            className="p-1.5 bg-[#111726] border border-[#1f293d] hover:border-cyan-700 text-slate-300 hover:text-cyan-300 rounded transition-colors flex-shrink-0"
            title="Inspect Session"
          >
            <ArrowUpRight className="w-4 h-4" />
          </Link>
        </div>
      ))}
    </div>
  );
}
