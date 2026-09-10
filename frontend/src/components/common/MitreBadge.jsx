import React from 'react';
import { ExternalLink, Shield } from 'lucide-react';

export default function MitreBadge({ technique }) {
  if (!technique) return null;

  return (
    <div className="inline-flex items-center justify-between gap-2 bg-[#0d121d] border border-[#1f293d] hover:border-cyan-700/80 rounded px-2.5 py-1.5 transition-colors text-xs font-mono">
      <div className="flex items-center gap-2">
        <span className="px-1.5 py-0.5 rounded text-[10px] bg-cyan-950 text-cyan-300 font-bold border border-cyan-800">
          {technique.technique_id}
        </span>
        <span className="text-slate-300 font-sans text-xs">
          {technique.name}
        </span>
      </div>
      {technique.url && (
        <a
          href={technique.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-slate-500 hover:text-cyan-400 flex-shrink-0"
          title={`View ${technique.technique_id} in MITRE ATT&CK Framework`}
        >
          <ExternalLink className="w-3.5 h-3.5" />
        </a>
      )}
    </div>
  );
}
