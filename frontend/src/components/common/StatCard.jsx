import React from 'react';

export default function StatCard({ title, value, icon: Icon, color = 'cyan', subtitle, trend }) {
  const colorMap = {
    cyan: 'text-cyan-400 bg-cyan-950/30 border-cyan-800/40',
    blue: 'text-blue-400 bg-blue-950/30 border-blue-800/40',
    emerald: 'text-emerald-400 bg-emerald-950/30 border-emerald-800/40',
    amber: 'text-amber-400 bg-amber-950/30 border-amber-800/40',
    orange: 'text-orange-400 bg-orange-950/30 border-orange-800/40',
    rose: 'text-rose-400 bg-rose-950/30 border-rose-800/40',
    purple: 'text-purple-400 bg-purple-950/30 border-purple-800/40',
  };

  const selectedColor = colorMap[color] || colorMap.cyan;

  return (
    <div className="bg-[#111726] border border-[#1f293d] rounded-lg p-4 shadow-sm hover:border-[#2e3d5c] transition-colors">
      <div className="flex items-center justify-between">
        <span className="text-xs uppercase font-medium tracking-wider text-slate-400">{title}</span>
        {Icon && (
          <div className={`p-2 rounded-md border ${selectedColor}`}>
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>
      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-2xl font-bold font-mono text-slate-100">{value ?? 0}</span>
        {trend && (
          <span className="text-xs text-slate-400">{trend}</span>
        )}
      </div>
      {subtitle && (
        <p className="mt-1 text-xs text-slate-400 truncate">{subtitle}</p>
      )}
    </div>
  );
}
