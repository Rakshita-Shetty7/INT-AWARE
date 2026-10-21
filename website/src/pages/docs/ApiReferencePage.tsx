import React from 'react';
import { Link } from 'react-router-dom';
import { Code2, Globe, Radio, Database, ArrowRight, Zap } from 'lucide-react';
import { CodeBlock } from '../../components/docs/CodeBlock';
import { Callout } from '../../components/docs/Callout';

export const ApiReferencePage: React.FC = () => {
  return (
    <div className="space-y-8">
      <div>
        <div className="text-xs font-mono font-bold uppercase tracking-wider text-sky-400 mb-1">
          Interface Specification
        </div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">
          REST & WebSocket API Reference
        </h1>
        <p className="text-slate-400 text-sm leading-relaxed mt-2">
          Technical documentation for INT-AWARE's FastAPI backend endpoints, request payloads, response schemas, and real-time WebSocket channels.
        </p>
      </div>

      <div className="p-4 rounded-xl bg-[#090e1c] border border-cyan-800/40 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono">
        <div>
          <span className="text-slate-400">Interactive Swagger UI:</span>
          <div className="text-cyan-400 font-bold">http://127.0.0.1:8000/docs</div>
        </div>
        <div>
          <span className="text-slate-400">ReDoc Documentation:</span>
          <div className="text-indigo-400 font-bold">http://127.0.0.1:8000/redoc</div>
        </div>
        <div>
          <span className="text-slate-400">OpenAPI JSON Schema:</span>
          <div className="text-emerald-400 font-bold">http://127.0.0.1:8000/openapi.json</div>
        </div>
      </div>

      {/* Core Endpoint Groups */}
      <div className="space-y-6">
        {/* Group 1: Health & Overview */}
        <div className="space-y-3">
          <h2 className="text-lg font-bold text-white border-b border-slate-800 pb-2 flex items-center gap-2">
            <Globe className="w-4 h-4 text-cyan-400" />
            1. System Health & Dashboard Metrics
          </h2>

          <div className="p-4 rounded-xl bg-[#090e1c] border border-slate-800 space-y-2 text-xs">
            <div className="flex items-center gap-2 font-mono">
              <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 font-bold border border-emerald-800">GET</span>
              <span className="text-white font-bold">/api/health</span>
            </div>
            <p className="text-slate-400">
              Health check reporting MongoDB connection, model registry cryptographic integrity, rule engine status, and Gemini availability.
            </p>
            <CodeBlock
              code={`curl -s http://127.0.0.1:8000/api/health | jq`}
              language="bash"
            />
          </div>

          <div className="p-4 rounded-xl bg-[#090e1c] border border-slate-800 space-y-2 text-xs">
            <div className="flex items-center gap-2 font-mono">
              <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 font-bold border border-emerald-800">GET</span>
              <span className="text-white font-bold">/api/dashboard/stats</span>
            </div>
            <p className="text-slate-400">
              Aggregated SOC metrics: total sessions, active connections, total events, unique attacker IPs, and critical alerts count.
            </p>
          </div>
        </div>

        {/* Group 2: Sessions & Digital Twin */}
        <div className="space-y-3">
          <h2 className="text-lg font-bold text-white border-b border-slate-800 pb-2 flex items-center gap-2">
            <Radio className="w-4 h-4 text-indigo-400" />
            2. Sessions & Attack Behavior Digital Twin
          </h2>

          <div className="p-4 rounded-xl bg-[#090e1c] border border-slate-800 space-y-2 text-xs">
            <div className="flex items-center gap-2 font-mono">
              <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 font-bold border border-emerald-800">GET</span>
              <span className="text-white font-bold">/api/sessions/{`{session_id}`}/digital-twin</span>
            </div>
            <p className="text-slate-400">
              Reconstructs an interactive chronological attack timeline, step-by-step risk escalation, kill-chain milestones, and next-intent evaluation.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-[#090e1c] border border-slate-800 space-y-2 text-xs">
            <div className="flex items-center gap-2 font-mono">
              <span className="px-2 py-0.5 rounded bg-blue-950 text-blue-400 font-bold border border-blue-800">POST</span>
              <span className="text-white font-bold">/api/sessions/{`{session_id}`}/counterfactual</span>
            </div>
            <p className="text-slate-400">
              Simulates a what-if scenario: calculates how excluding a specific command event changes cumulative risk and kill-chain stages without altering database history.
            </p>
            <CodeBlock
              code={`curl -X POST http://127.0.0.1:8000/api/sessions/sess-123/counterfactual \\
  -H "Content-Type: application/json" \\
  -d '{"excluded_event_id": "ev-456"}'`}
              language="bash"
            />
          </div>
        </div>

        {/* Group 3: Analytics & Campaign Graph */}
        <div className="space-y-3">
          <h2 className="text-lg font-bold text-white border-b border-slate-800 pb-2 flex items-center gap-2">
            <Zap className="w-4 h-4 text-purple-400" />
            3. Campaign Graph & Novelty Detection
          </h2>

          <div className="p-4 rounded-xl bg-[#090e1c] border border-slate-800 space-y-2 text-xs">
            <div className="flex items-center gap-2 font-mono">
              <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 font-bold border border-emerald-800">GET</span>
              <span className="text-white font-bold">/api/analytics/campaign-graph</span>
            </div>
            <p className="text-slate-400">
              Returns nodes (IPs, Sessions, MITRE Techniques, Indicators) and relationship edges calculated using Jaccard command overlap clustering.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-[#090e1c] border border-slate-800 space-y-2 text-xs">
            <div className="flex items-center gap-2 font-mono">
              <span className="px-2 py-0.5 rounded bg-blue-950 text-blue-400 font-bold border border-blue-800">POST</span>
              <span className="text-white font-bold">/api/analytics/drift/test-command</span>
            </div>
            <p className="text-slate-400">
              Evaluates an arbitrary shell command against vocabulary novelty (OOV ratio) and Shannon prediction entropy to detect data drift.
            </p>
          </div>
        </div>

        {/* Group 4: WebSockets */}
        <div className="space-y-3">
          <h2 className="text-lg font-bold text-white border-b border-slate-800 pb-2 flex items-center gap-2">
            <Radio className="w-4 h-4 text-emerald-400" />
            4. Real-Time WebSockets
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
            <div className="p-4 rounded-xl bg-[#090e1c] border border-slate-800 space-y-1.5">
              <span className="text-emerald-400 font-bold">ws://127.0.0.1:8000/ws/events</span>
              <p className="text-slate-400 font-sans text-xs">
                Broadcasts every newly ingested and classified command event in real time.
              </p>
            </div>
            <div className="p-4 rounded-xl bg-[#090e1c] border border-slate-800 space-y-1.5">
              <span className="text-rose-400 font-bold">ws://127.0.0.1:8000/ws/alerts</span>
              <p className="text-slate-400 font-sans text-xs">
                Broadcasts critical security alerts fired when a session reaches cumulative risk ≥ 75.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="pt-4 border-t border-slate-800 flex justify-between items-center text-xs">
        <Link to="/docs/configuration/docker-services" className="text-slate-400 hover:text-white">
          ← Docker Services
        </Link>
        <Link to="/docs/troubleshooting" className="text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1">
          <span>Troubleshooting & FAQ</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
};
