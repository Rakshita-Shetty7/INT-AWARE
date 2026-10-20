import React from 'react';

const INTENT_COLORS = {
  RECONNAISSANCE: 'bg-cyan-950/60 text-cyan-400 border-cyan-800/60',
  DISCOVERY: 'bg-blue-950/60 text-blue-400 border-blue-800/60',
  CREDENTIAL_ACCESS: 'bg-amber-950/60 text-amber-400 border-amber-800/60',
  EXECUTION: 'bg-red-950/60 text-red-400 border-red-800/60',
  PRIVILEGE_ESCALATION: 'bg-purple-950/60 text-purple-400 border-purple-800/60',
  PERSISTENCE: 'bg-indigo-950/60 text-indigo-400 border-indigo-800/60',
  EXPLOITATION: 'bg-rose-950/70 text-rose-400 border-rose-800/70 font-semibold',
  EXFILTRATION: 'bg-fuchsia-950/60 text-fuchsia-400 border-fuchsia-800/60',
  CLEANUP: 'bg-teal-950/60 text-teal-400 border-teal-800/60',
  OTHER: 'bg-slate-900 text-slate-400 border-slate-700/80',
};

export default function IntentBadge({ intent }) {
  const norm = (intent || 'OTHER').toUpperCase();
  const style = INTENT_COLORS[norm] || INTENT_COLORS.OTHER;

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs border font-mono tracking-wider ${style}`}>
      {norm}
    </span>
  );
}
