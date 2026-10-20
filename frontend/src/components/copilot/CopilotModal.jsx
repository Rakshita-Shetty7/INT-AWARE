import React, { useState } from 'react';
import {
  Sparkles,
  X,
  Send,
  ShieldAlert,
  HelpCircle,
  FileText,
  CheckCircle,
  AlertTriangle,
  Terminal,
  Cpu,
  Loader2,
  Copy,
  Check,
} from 'lucide-react';
import api from '../../services/api';

const QUICK_PROMPTS = [
  'Summarize the most critical attack session in the system.',
  'What shadow files, credentials, or keys did attackers attempt to read?',
  'Were any persistence mechanisms or scheduled cron jobs staged?',
  'List all suspicious download URLs and /tmp payload staging artifacts.',
];

export default function CopilotModal({ isOpen, onClose, initialSessionId = null }) {
  const [query, setQuery] = useState('');
  const [sessionId, setSessionId] = useState(initialSessionId || '');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);
  const [copiedId, setCopiedId] = useState(null);

  if (!isOpen) return null;

  const handleQuery = async (customText = null) => {
    const qText = customText || query;
    if (!qText.trim()) return;

    try {
      setLoading(true);
      setError(null);
      const res = await api.queryCopilot({
        query: qText.trim(),
        session_id: sessionId.trim() || undefined,
      });
      setResponse(res);
    } catch (err) {
      setError(err.message || 'Copilot query failed.');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="bg-[#0b101b] border border-cyan-800/60 rounded-xl w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl shadow-cyan-950/50 overflow-hidden">
        {/* Header */}
        <div className="p-4 sm:px-6 bg-[#0d1424] border-b border-[#1e293b] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-cyan-950/60 border border-cyan-700/60 rounded-lg text-cyan-400">
              <Sparkles className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-slate-100 font-mono tracking-wide">
                  EVIDENCE-FIRST AI COPILOT
                </h3>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-cyan-950 border border-cyan-800 text-cyan-400 font-mono">
                  ZERO-FABRICATION
                </span>
              </div>
              <p className="text-xs text-slate-400 font-sans">
                Forensic investigation grounded exclusively in authentic honeypot telemetry with verified citations.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-[#1e293b] rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Query Input & Scope */}
        <div className="p-4 bg-[#0d121d] border-b border-[#1e293b] space-y-3">
          <div className="flex gap-2">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleQuery()}
              placeholder="Ask an investigation question (e.g. 'What commands were run in session...?')"
              className="flex-1 bg-[#111726] border border-[#1f293d] focus:border-cyan-500 rounded-lg px-4 py-2.5 text-sm text-slate-200 placeholder-slate-500 focus:outline-none font-mono"
            />
            <button
              onClick={() => handleQuery()}
              disabled={loading || !query.trim()}
              className="px-5 py-2.5 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 disabled:opacity-50 text-white rounded-lg text-sm font-semibold flex items-center gap-2 transition-all shadow-lg shadow-cyan-900/30"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              <span>Investigate</span>
            </button>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
            <div className="flex items-center gap-2 text-slate-400 font-mono">
              <span className="text-slate-500">Session Filter:</span>
              <input
                type="text"
                value={sessionId}
                onChange={(e) => setSessionId(e.target.value)}
                placeholder="All sessions (or paste session_id)"
                className="bg-[#111726] border border-[#1f293d] rounded px-2 py-1 text-xs text-slate-300 w-48 font-mono focus:outline-none focus:border-cyan-500"
              />
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-[11px] text-slate-500">Suggested:</span>
              {QUICK_PROMPTS.slice(0, 2).map((p, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    setQuery(p);
                    handleQuery(p);
                  }}
                  className="text-[11px] px-2 py-0.5 rounded bg-[#162032] border border-[#23324f] text-slate-300 hover:text-cyan-300 hover:border-cyan-700/60 transition-colors truncate max-w-[200px]"
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
          {error && (
            <div className="p-4 bg-rose-950/40 border border-rose-800/60 rounded-lg text-rose-300 text-sm flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {!response && !loading && (
            <div className="py-12 text-center space-y-4">
              <div className="w-12 h-12 mx-auto rounded-full bg-cyan-950/40 border border-cyan-800/40 flex items-center justify-center text-cyan-400">
                <Terminal className="w-6 h-6" />
              </div>
              <div className="max-w-md mx-auto space-y-1">
                <h4 className="text-sm font-semibold text-slate-200">No Active Query</h4>
                <p className="text-xs text-slate-400">
                  Select a suggested investigation prompt above or ask a targeted question to retrieve cited evidence from MongoDB.
                </p>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-lg mx-auto text-left pt-2">
                {QUICK_PROMPTS.map((p, i) => (
                  <button
                    key={i}
                    onClick={() => {
                      setQuery(p);
                      handleQuery(p);
                    }}
                    className="p-3 bg-[#111726] border border-[#1f293d] hover:border-cyan-700/60 rounded-lg text-xs text-slate-300 hover:text-cyan-300 transition-all flex items-start gap-2"
                  >
                    <span className="text-cyan-500 font-mono">0{i + 1}.</span>
                    <span>{p}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {loading && (
            <div className="py-16 text-center space-y-3">
              <Loader2 className="w-8 h-8 mx-auto text-cyan-400 animate-spin" />
              <p className="text-xs font-mono text-slate-400">
                GATHERING HONEYPOT TELEMETRY & EXTRACTING EVIDENCE CITATIONS...
              </p>
            </div>
          )}

          {response && !loading && (
            <div className="space-y-6">
              {/* Answer narrative */}
              <div className="p-4 bg-[#111726] border border-[#1f293d] rounded-xl space-y-3">
                <div className="flex items-center justify-between border-b border-[#1e293b] pb-2">
                  <span className="text-xs font-mono font-semibold text-cyan-400 uppercase tracking-wider flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-cyan-400" /> Forensic Assessment
                  </span>
                  <span className="text-[10px] font-mono text-slate-500">
                    Engine: {response.model_source}
                  </span>
                </div>
                <div className="text-sm text-slate-200 leading-relaxed whitespace-pre-line font-sans">
                  {response.answer}
                </div>
              </div>

              {/* Verified Facts */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                    <FileText className="w-4 h-4 text-emerald-400" /> Verified Observed Facts ({response.facts.length})
                  </h4>
                  <span className="text-[10px] text-emerald-400 font-mono">STRICT GROUNDING</span>
                </div>
                {response.facts.length === 0 ? (
                  <p className="text-xs text-slate-500 italic">No specific direct command matches in query scope.</p>
                ) : (
                  <div className="space-y-2">
                    {response.facts.map((fact, idx) => (
                      <div
                        key={idx}
                        className="p-3 bg-[#0d1424] border border-emerald-900/40 rounded-lg flex flex-col sm:flex-row sm:items-center justify-between gap-2"
                      >
                        <div className="space-y-1 min-w-0">
                          <p className="text-xs text-slate-200 font-sans">{fact.statement}</p>
                          {fact.evidence_command && (
                            <code className="inline-block text-[11px] font-mono text-emerald-400 bg-black/40 px-2 py-0.5 rounded border border-emerald-900/60 truncate max-w-full">
                              $ {fact.evidence_command}
                            </code>
                          )}
                        </div>
                        <div className="flex items-center gap-2 flex-shrink-0">
                          <span className="text-[10px] font-mono text-slate-400 bg-[#162032] px-2 py-0.5 rounded border border-[#23324f]">
                            ID: {fact.event_id.slice(0, 10)}...
                          </span>
                          <button
                            onClick={() => copyToClipboard(fact.event_id, `fact-${idx}`)}
                            title="Copy Event ID"
                            className="p-1 text-slate-400 hover:text-slate-200 transition-colors"
                          >
                            {copiedId === `fact-${idx}` ? (
                              <Check className="w-3.5 h-3.5 text-emerald-400" />
                            ) : (
                              <Copy className="w-3.5 h-3.5" />
                            )}
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Hypotheses & Uncertainties Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Hypotheses */}
                <div className="p-4 bg-[#111726] border border-amber-900/30 rounded-xl space-y-2">
                  <div className="flex items-center gap-2 text-xs font-mono font-bold text-amber-400 uppercase tracking-wider">
                    <AlertTriangle className="w-4 h-4 text-amber-400" /> Plausible Hypotheses
                  </div>
                  <ul className="space-y-1.5 text-xs text-slate-300">
                    {response.hypotheses.map((h, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-amber-500 font-mono">•</span>
                        <span>{h}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Uncertainties */}
                <div className="p-4 bg-[#111726] border border-purple-900/30 rounded-xl space-y-2">
                  <div className="flex items-center gap-2 text-xs font-mono font-bold text-purple-400 uppercase tracking-wider">
                    <HelpCircle className="w-4 h-4 text-purple-400" /> Operational Uncertainties
                  </div>
                  <ul className="space-y-1.5 text-xs text-slate-300">
                    {response.uncertainties.map((u, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-purple-400 font-mono">•</span>
                        <span>{u}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
