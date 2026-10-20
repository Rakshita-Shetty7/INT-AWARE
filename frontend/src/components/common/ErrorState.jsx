import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export default function ErrorState({ message = 'Failed to load telemetry from backend API.', onRetry }) {
  return (
    <div className="bg-rose-950/20 border border-rose-900/60 rounded-lg p-6 text-center my-4">
      <AlertTriangle className="w-8 h-8 text-rose-400 mx-auto mb-2" />
      <h3 className="text-sm font-semibold text-rose-300">Connection or Processing Error</h3>
      <p className="text-xs text-rose-300/80 mt-1 max-w-md mx-auto">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-4 inline-flex items-center gap-1.5 px-3 py-1.5 bg-rose-900/40 hover:bg-rose-900/60 border border-rose-700/60 rounded text-xs font-medium text-rose-200 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Retry Connection
        </button>
      )}
    </div>
  );
}
