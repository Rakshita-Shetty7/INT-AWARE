import React from 'react';
import { Terminal, Clock, Server } from 'lucide-react';
import IntentBadge from '../common/IntentBadge';
import SeverityBadge from '../common/SeverityBadge';
import RiskIndicator from '../common/RiskIndicator';
import EmptyState from '../common/EmptyState';

const SOURCE_STYLES = {
  HYBRID: 'text-cyan-300 border-cyan-700/60 bg-cyan-950/40',
  ML: 'text-violet-300 border-violet-700/60 bg-violet-950/40',
  RULE: 'text-slate-300 border-slate-600/60 bg-slate-800/40',
  GEMINI: 'text-amber-300 border-amber-700/60 bg-amber-950/40',
  FALLBACK: 'text-rose-300 border-rose-700/60 bg-rose-950/40',
};

function SourceBadge({ source, mlConfidence }) {
  if (!source) return null;
  const key = String(source).replace('ClassificationSource.', '').toUpperCase();
  const style = SOURCE_STYLES[key] || SOURCE_STYLES.RULE;
  const showConf = (key === 'ML' || key === 'HYBRID') && mlConfidence != null;
  return (
    <span
      title={showConf ? `ML calibrated confidence: ${(mlConfidence * 100).toFixed(1)}%` : `Classification source: ${key}`}
      className={`text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded border ${style}`}
    >
      {key}{showConf ? ` ${(mlConfidence * 100).toFixed(0)}%` : ''}
    </span>
  );
}

export default function RecentEvents({ events = [] }) {
  if (!events || events.length === 0) {
    return <EmptyState title="No Recent Events" message="Waiting for honeypot telemetry..." icon={Terminal} />;
  }

  return (
    <div className="space-y-2">
      {events.map((ev) => (
        <div
          key={ev.event_id}
          className="bg-[#0e1320] border border-[#1f293d] rounded-md p-3 hover:border-[#2e3d5c] transition-colors flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs"
        >
          <div className="flex items-start md:items-center gap-3 min-w-0 flex-1">
            <div className="p-1.5 bg-[#161f33] border border-[#2e3d5c]/60 rounded text-cyan-400 font-mono flex-shrink-0">
              <Terminal className="w-3.5 h-3.5" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-mono font-medium text-slate-200 min-w-0">
                  {ev.command ? (
                    <code className="inline-block max-w-full align-bottom truncate bg-[#161f33] px-1.5 py-0.5 rounded text-cyan-300 font-mono">
                      {ev.command.length > 50 ? `${ev.command.substring(0, 50)}...` : ev.command}
                    </code>
                  ) : (
                    <span className="text-slate-400 font-mono">{ev.event_type}</span>
                  )}
                </span>
                <IntentBadge intent={ev.intent} />
                <SeverityBadge severity={ev.severity} />
                <SourceBadge source={ev.classification_source} mlConfidence={ev.ml_confidence} />
              </div>
              <div className="flex items-center gap-x-4 gap-y-1 mt-1 text-[11px] text-slate-400 font-mono flex-wrap">
                <span className="truncate">IP: {ev.source_ip || 'N/A'}</span>
                <span>Session: {ev.session_id ? ev.session_id.substring(0, 8) : 'N/A'}</span>
                {ev.username && <span className="truncate">User: {ev.username}</span>}
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between md:justify-end gap-4 border-t md:border-t-0 border-[#1f293d] pt-2 md:pt-0 flex-shrink-0">
            <RiskIndicator score={ev.risk_score} size="sm" />
            <span className="text-[11px] text-slate-500 font-mono flex items-center gap-1 flex-shrink-0">
              <Clock className="w-3 h-3" />
              {new Date(ev.timestamp).toLocaleTimeString()}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
