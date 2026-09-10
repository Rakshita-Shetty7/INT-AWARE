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

const BUCKET_COLORS = [
  '#10b981', // Low
  '#f59e0b', // Medium
  '#f97316', // High
  '#f43f5e', // Critical
];

export default function RiskDistributionChart({ data = [] }) {
  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-xs font-mono text-slate-500">
        No risk distribution data available.
      </div>
    );
  }

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          margin={{ top: 10, right: 20, left: -10, bottom: 25 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#1f293d" vertical={false} />
          <XAxis
            dataKey="range"
            stroke="#64748b"
            tick={{ fill: '#cbd5e1', fontSize: 10, fontFamily: 'monospace' }}
            angle={-15}
            textAnchor="end"
          />
          <YAxis
            stroke="#64748b"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            allowDecimals={false}
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
              'Sessions',
            ]}
          />
          <Bar dataKey="count" radius={[4, 4, 0, 0]}>
            {data.map((entry, index) => (
              <Cell
                key={`bucket-cell-${index}`}
                fill={BUCKET_COLORS[index % BUCKET_COLORS.length]}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
