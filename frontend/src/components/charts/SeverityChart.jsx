import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import EmptyState from '../common/EmptyState';
import { BarChart3 } from 'lucide-react';

const SEVERITY_COLORS = {
  LOW: '#10b981',      // Emerald
  MEDIUM: '#f59e0b',   // Amber
  HIGH: '#f97316',     // Orange
  CRITICAL: '#f43f5e', // Rose
};

const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-[#111726] border border-[#2e3d5c] p-2.5 rounded shadow-lg text-xs font-mono">
        <p className="font-bold text-slate-200">{data.severity}</p>
        <p className="text-slate-300">Sessions: {data.count} ({data.percentage}%)</p>
      </div>
    );
  }
  return null;
};

export default function SeverityChart({ data = [] }) {
  if (!data || data.length === 0) {
    return <EmptyState title="No Severity Metrics" message="No severity tier data available." icon={BarChart3} />;
  }

  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
          <XAxis
            dataKey="severity"
            tick={{ fill: '#8b9bb4', fontSize: 11, fontFamily: 'monospace' }}
            axisLine={{ stroke: '#1f293d' }}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: '#8b9bb4', fontSize: 11, fontFamily: 'monospace' }}
            axisLine={{ stroke: '#1f293d' }}
            tickLine={false}
            allowDecimals={false}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="count" radius={[4, 4, 0, 0]}>
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={SEVERITY_COLORS[entry.severity] || '#64748b'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
