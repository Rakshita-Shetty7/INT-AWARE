import React from 'react';
import IntentBadge from '../common/IntentBadge';
import RiskIndicator from '../common/RiskIndicator';
import { Grid, Flame } from 'lucide-react';

export default function RiskHeatmap({ data = [] }) {
  if (!data || data.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center text-xs font-mono text-slate-500">
        No threat matrix data available.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs text-left">
        <thead className="text-[11px] font-mono uppercase text-slate-400 bg-[#0d121d] border-b border-[#1f293d]">
          <tr>
            <th className="py-2.5 px-3">Intent Category</th>
            <th className="py-2.5 px-3 text-right">Event Count</th>
            <th className="py-2.5 px-3">Average Risk Score</th>
            <th className="py-2.5 px-3 text-right">Peak Risk</th>
            <th className="py-2.5 px-3 text-center">Threat Distribution</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[#1f293d]/60 font-mono">
          {data.map((row) => {
            const riskColor =
              row.average_risk >= 75
                ? 'bg-rose-500'
                : row.average_risk >= 50
                ? 'bg-orange-500'
                : row.average_risk >= 25
                ? 'bg-amber-500'
                : 'bg-emerald-500';

            return (
              <tr key={row.intent} className="hover:bg-[#0d121d]/60 transition-colors">
                <td className="py-3 px-3 font-sans">
                  <IntentBadge intent={row.intent} />
                </td>
                <td className="py-3 px-3 text-right font-bold text-slate-200">
                  {row.event_count}
                </td>
                <td className="py-3 px-3">
                  <div className="flex items-center gap-2">
                    <div className="w-24 bg-slate-800 rounded-full h-2 overflow-hidden">
                      <div
                        className={`h-full ${riskColor}`}
                        style={{ width: `${Math.min(100, row.average_risk)}%` }}
                      />
                    </div>
                    <span className="text-slate-300 font-bold">{row.average_risk}/100</span>
                  </div>
                </td>
                <td className="py-3 px-3 text-right">
                  <span className={`px-2 py-0.5 rounded text-[11px] ${
                    row.max_risk >= 75 ? 'bg-rose-950 text-rose-300 border border-rose-800' :
                    row.max_risk >= 50 ? 'bg-orange-950 text-orange-300 border border-orange-800' :
                    'bg-slate-800 text-slate-300'
                  }`}>
                    {row.max_risk}/100
                  </span>
                </td>
                <td className="py-3 px-3">
                  <div className="flex items-center justify-center gap-1.5 text-[10px]">
                    {row.low > 0 && (
                      <span className="px-1.5 py-0.5 bg-emerald-950/60 text-emerald-400 border border-emerald-800/60 rounded">
                        {row.low} Low
                      </span>
                    )}
                    {row.medium > 0 && (
                      <span className="px-1.5 py-0.5 bg-amber-950/60 text-amber-400 border border-amber-800/60 rounded">
                        {row.medium} Med
                      </span>
                    )}
                    {row.high > 0 && (
                      <span className="px-1.5 py-0.5 bg-orange-950/60 text-orange-400 border border-orange-800/60 rounded">
                        {row.high} High
                      </span>
                    )}
                    {row.critical > 0 && (
                      <span className="px-1.5 py-0.5 bg-rose-950 text-rose-400 border border-rose-800 rounded font-bold">
                        {row.critical} Crit
                      </span>
                    )}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
