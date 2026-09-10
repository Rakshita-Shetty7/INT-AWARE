import React from 'react';
import { Loader2 } from 'lucide-react';

export default function LoadingState({ message = 'Loading threat intelligence telemetry...' }) {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center">
      <Loader2 className="w-8 h-8 text-cyan-400 animate-spin mb-3" />
      <p className="text-sm text-slate-400 font-mono">{message}</p>
    </div>
  );
}
