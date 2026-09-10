import React from 'react';

const SEVERITY_STYLES = {
  LOW: 'bg-emerald-950/60 text-emerald-400 border-emerald-800/60',
  MEDIUM: 'bg-amber-950/60 text-amber-400 border-amber-800/60',
  HIGH: 'bg-orange-950/60 text-orange-400 border-orange-800/60',
  CRITICAL: 'bg-rose-950/70 text-rose-400 border-rose-800/80 font-semibold',
  UNKNOWN: 'bg-slate-900 text-slate-400 border-slate-700',
};

export default function SeverityBadge({ severity }) {
  const norm = (severity || 'UNKNOWN').toUpperCase();
  const style = SEVERITY_STYLES[norm] || SEVERITY_STYLES.UNKNOWN;

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded text-xs border tracking-wide uppercase ${style}`}>
      <span className={`w-1.5 h-1.5 rounded-full mr-1.5 ${
        norm === 'CRITICAL' ? 'bg-rose-400 animate-pulse' :
        norm === 'HIGH' ? 'bg-orange-400' :
        norm === 'MEDIUM' ? 'bg-amber-400' : 'bg-emerald-400'
      }`} />
      {norm}
    </span>
  );
}
