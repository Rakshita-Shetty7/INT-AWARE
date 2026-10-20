import React from 'react';

export default function RiskIndicator({ score, showBar = true, size = 'md' }) {
  const numScore = Math.max(0, Math.min(100, Number(score) || 0));

  const getColor = (s) => {
    if (s >= 75) return { text: 'text-rose-400', bg: 'bg-rose-500', border: 'border-rose-800' };
    if (s >= 50) return { text: 'text-orange-400', bg: 'bg-orange-500', border: 'border-orange-800' };
    if (s >= 25) return { text: 'text-amber-400', bg: 'bg-amber-500', border: 'border-amber-800' };
    return { text: 'text-emerald-400', bg: 'bg-emerald-500', border: 'border-emerald-800' };
  };

  const colors = getColor(numScore);

  return (
    <div className="flex items-center gap-2">
      <span className={`font-mono font-bold ${colors.text} ${size === 'lg' ? 'text-lg' : 'text-sm'}`}>
        {numScore}<span className="text-slate-500 text-xs font-normal">/100</span>
      </span>
      {showBar && (
        <div className="w-16 h-2 bg-slate-800 rounded-full overflow-hidden border border-slate-700/60 flex-shrink-0">
          <div
            className={`h-full ${colors.bg} transition-all duration-300`}
            style={{ width: `${numScore}%` }}
          />
        </div>
      )}
    </div>
  );
}
