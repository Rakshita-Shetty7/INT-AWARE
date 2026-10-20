import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';
import EmptyState from '../common/EmptyState';
import { Activity } from 'lucide-react';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-[#111726] border border-[#2e3d5c] p-2.5 rounded shadow-lg text-xs font-mono">
        <p className="font-bold text-slate-300">{label}</p>
        <p className="text-cyan-400">Events: {payload[0].value}</p>
        {payload[1] && <p className="text-indigo-400">Active Sessions: {payload[1].value}</p>}
      </div>
    );
  }
  return null;
};

export default function AttackTimeline({ data = [] }) {
  if (!data || data.length === 0) {
    return <EmptyState title="No Timeline Data" message="No attack time-series events recorded." icon={Activity} />;
  }

  const formattedData = data.map((d) => ({
    ...d,
    formattedTime: d.timestamp ? new Date(d.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'N/A',
  }));

  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={formattedData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
          <defs>
            <linearGradient id="eventGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0} />
            </linearGradient>
            <linearGradient id="sessionGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f293d" vertical={false} />
          <XAxis
            dataKey="formattedTime"
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
          <Area
            type="monotone"
            dataKey="event_count"
            stroke="#06b6d4"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#eventGradient)"
            name="Events"
          />
          <Area
            type="monotone"
            dataKey="session_count"
            stroke="#6366f1"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#sessionGradient)"
            name="Sessions"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
