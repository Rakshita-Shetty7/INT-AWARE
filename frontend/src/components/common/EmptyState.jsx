import React from 'react';
import { ShieldCheck } from 'lucide-react';

export default function EmptyState({ title = 'No Data Available', message = 'No threat events or sessions recorded yet.', icon: Icon = ShieldCheck }) {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center bg-[#111726]/40 border border-[#1f293d]/60 rounded-lg">
      <Icon className="w-10 h-10 text-slate-500 mb-3" />
      <h3 className="text-sm font-medium text-slate-300">{title}</h3>
      <p className="text-xs text-slate-400 mt-1 max-w-sm">{message}</p>
    </div>
  );
}
