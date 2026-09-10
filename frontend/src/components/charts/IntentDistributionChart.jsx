import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import EmptyState from '../common/EmptyState';
import { PieChart as PieIcon } from 'lucide-react';

const INTENT_COLORS = {
  RECONNAISSANCE: '#06b6d4', // Cyan
  DISCOVERY: '#3b82f6',     // Blue
  CREDENTIAL_ACCESS: '#f59e0b', // Amber
  EXECUTION: '#ef4444',     // Red
  PRIVILEGE_ESCALATION: '#a855f7', // Purple
  PERSISTENCE: '#6366f1',   // Indigo
  EXPLOITATION: '#f43f5e',  // Rose
  EXFILTRATION: '#d946ef',  // Fuchsia
  CLEANUP: '#14b8a6',       // Teal
  OTHER: '#64748b',         // Slate
};

const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-[#111726] border border-[#2e3d5c] p-2.5 rounded shadow-lg text-xs font-mono">
        <p className="font-bold text-slate-200">{data.intent}</p>
        <p className="text-cyan-400">Events: {data.count} ({data.percentage}%)</p>
      </div>
    );
  }
  return null;
};

export default function IntentDistributionChart({ data = [] }) {
  if (!data || data.length === 0) {
    return <EmptyState title="No Classified Intents" message="No intent distribution data available." icon={PieIcon} />;
  }

  const total = data.reduce((sum, d) => sum + (d.count || 0), 0);

  return (
    <div className="w-full">
      {/* Donut */}
      <div className="h-44">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="count"
              nameKey="intent"
              cx="50%"
              cy="50%"
              outerRadius={78}
              innerRadius={46}
              paddingAngle={2}
              stroke="#0a0d14"
              strokeWidth={2}
            >
              {data.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={INTENT_COLORS[entry.intent] || '#64748b'}
                />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* Clean, aligned 2-column legend (replaces recharts' messy wrapping default) */}
      <div className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1.5">
        {data.map((entry) => {
          const pct = total ? Math.round((entry.count / total) * 100) : 0;
          return (
            <div key={entry.intent} className="flex items-center gap-2 min-w-0">
              <span
                className="w-2.5 h-2.5 rounded-sm flex-shrink-0"
                style={{ backgroundColor: INTENT_COLORS[entry.intent] || '#64748b' }}
              />
              <span className="text-[10px] font-mono text-slate-300 truncate" title={entry.intent}>
                {entry.intent}
              </span>
              <span className="text-[10px] font-mono text-slate-500 ml-auto flex-shrink-0 tabular-nums">
                {pct}%
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
