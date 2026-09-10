import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

const STAGE_COLORS = {
  INITIAL_ACCESS: '#64748b',
  RECONNAISSANCE: '#06b6d4',
  DISCOVERY: '#3b82f6',
  CREDENTIAL_ACCESS: '#eab308',
  EXECUTION: '#f97316',
  PRIVILEGE_ESCALATION: '#ef4444',
  PERSISTENCE: '#a855f7',
  EXPLOITATION: '#ec4899',
  EXFILTRATION: '#f43f5e',
  CLEANUP: '#10b981',
  UNKNOWN: '#475569',
};

export default function StageDistributionChart({ data = [] }) {
  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-xs font-mono text-slate-500">
        No attack stage progression data available.
      </div>
    );
  }

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 10, right: 30, left: 40, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#1f293d" horizontal={false} />
          <XAxis type="number" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} />
          <YAxis
            type="category"
            dataKey="stage"
            stroke="#64748b"
            tick={{ fill: '#cbd5e1', fontSize: 10, fontFamily: 'monospace' }}
            width={110}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#0d121d',
              borderColor: '#1f293d',
              borderRadius: '6px',
              color: '#f8fafc',
              fontSize: '12px',
              fontFamily: 'monospace',
            }}
            formatter={(val, name, item) => [
              `${val} sessions (${item.payload.percentage}%)`,
              'Volume',
            ]}
          />
          <Bar dataKey="count" radius={[0, 4, 4, 0]}>
            {data.map((entry, index) => (
              <Cell
                key={`stage-cell-${index}`}
                fill={STAGE_COLORS[entry.stage] || '#06b6d4'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
