import React, { useState } from 'react';
import {
  Server,
  Database,
  Cpu,
  Layers,
  Activity,
  Shield,
  Radio,
  FileCode,
  ArrowRight,
  Terminal,
} from 'lucide-react';
import { Link } from 'react-router-dom';

interface ArchLayer {
  id: string;
  name: string;
  badge: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  codePath: string;
  ports: string;
  summary: string;
  keyDetails: string[];
}

const ARCH_LAYERS: ArchLayer[] = [
  {
    id: 'cowrie',
    name: '1. Isolated Decoy Honeypot',
    badge: 'Port 2222 · Emulated Shell',
    icon: Radio,
    color: 'text-cyan-400',
    codePath: 'honeypot/var/log/cowrie/cowrie.json',
    ports: '127.0.0.1:2222 -> 2222 (Host local-only)',
    summary:
      'Containerized Cowrie honeypot running an emulated Debian shell. Captures keystrokes, downloaded payload hashes, and session metadata with zero host execution.',
    keyDetails: [
      'Emulated Python shell: commands never execute on the host PC or Docker host.',
      'Logs written to cowrie-logs volume, mounted strictly read-only by the backend.',
      'Binds exclusively to 127.0.0.1 (no external network exposure by default).',
    ],
  },
  {
    id: 'collector',
    name: '2. Ingestion & Normalization',
    badge: 'Async Tail · MD5 Deduplication',
    icon: Layers,
    color: 'text-sky-400',
    codePath: 'backend/app/pipeline.py & cowrie_collector.py',
    ports: 'Internal Python Pipeline Process',
    summary:
      'Continuously tails Cowrie JSON logs with incremental file-pointer tracking. Normalizes events into canonical Pydantic models with MD5 event deduplication.',
    keyDetails: [
      'Resilient polling with exponential backoff on file rotation.',
      'De-duplication cache prevents double-processing of identical session commands.',
      'Sanitizes raw keystrokes into structured NormalizedEvent instances.',
    ],
  },
  {
    id: 'ml_hybrid',
    name: '3. Hybrid ML & Rule Intelligence',
    badge: '94.49% Real Test Accuracy',
    icon: Cpu,
    color: 'text-indigo-400',
    codePath: 'backend/app/ml/classifier.py & rule_engine.py',
    ports: 'LinearSVC + TF-IDF (40k features)',
    summary:
      'Calibrated LinearSVC model with TF-IDF character/word n-grams. Includes Shannon entropy confidence abstention, OOV novelty detection, and optional Google Gemini semantic fallback.',
    keyDetails: [
      'Classifies into 10 MITRE-aligned categories with calibrated probabilities.',
      'Deterministic regex rule layer catches known high-severity attack signatures instantly.',
      'Cryptographic SHA-256 model registry verification prevents model tampering.',
    ],
  },
  {
    id: 'sequence_risk',
    name: '4. Markov Sequences & Risk Engine',
    badge: '0–100 Scale · Threshold >= 75',
    icon: Activity,
    color: 'text-emerald-400',
    codePath: 'backend/app/services/risk_scoring.py & sequence_transition_engine.py',
    ports: 'State-Aware In-Memory Markov Engine',
    summary:
      'Models sequential attack kill chains using empirical transition likelihoods P(Intent_t | Intent_{t-1}). Calculates cumulative session risk and triggers alerts.',
    keyDetails: [
      'Alerts fire on session cumulative risk (floor >= 75 for CRITICAL severity).',
      'Detects out-of-order sequence transitions and lateral leaps.',
      'Maps each step directly to MITRE ATT&CK technique IDs (e.g. T1082, T1003).',
    ],
  },
  {
    id: 'storage_api',
    name: '5. Persistent Storage & FastAPI Core',
    badge: 'MongoDB 7 + Motor + FastAPI',
    icon: Database,
    color: 'text-purple-400',
    codePath: 'backend/app/api/ & persistence_service.py',
    ports: '127.0.0.1:8000 -> 8000',
    summary:
      'Stores sessions, events, attacker profiles, and alerts in MongoDB. Exposes 30+ REST endpoints and WebSocket broadcasting for real-time dashboard updates.',
    keyDetails: [
      'Motor async driver for non-blocking database queries.',
      'REST endpoints under /api/sessions, /api/analytics, /api/alerts, and /api/research.',
      'Automatic WebSocket broadcasting on /ws/events and /ws/alerts.',
    ],
  },
  {
    id: 'frontend_soc',
    name: '6. SOC Command Center UI',
    badge: 'React 19 + Vite + Tailwind',
    icon: Server,
    color: 'text-amber-400',
    codePath: 'frontend/src/ (Vite + React)',
    ports: '127.0.0.1:5173 -> 5173',
    summary:
      'Futuristic dark cybersecurity operations center with real-time attack feed, digital twin replay controls, SVG campaign graph, and AI copilot investigation modal.',
    keyDetails: [
      'Live attack stream updates automatically via WebSocket without manual refresh.',
      'Attack Behavior Digital Twin features command-by-command playback and counterfactual what-if simulation.',
      'Interactive campaign graph visualizes threat IP to MITRE technique clusters.',
    ],
  },
];

export const InteractiveArchitecture: React.FC = () => {
  const [selectedLayer, setSelectedLayer] = useState<ArchLayer>(ARCH_LAYERS[0]);

  return (
    <section id="architecture" className="py-24 bg-[#070b16] border-t border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16 space-y-3">
          <div className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-400">
            System Topology & Data Pipeline
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            End-to-End Threat Intelligence Architecture
          </h2>
          <p className="text-slate-400 text-sm sm:text-base leading-relaxed">
            From honeypot terminal capture to ML intent inference and live SOC command visualization. Click any layer below to inspect its implementation.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left Column: Interactive Layer List */}
          <div className="lg:col-span-6 space-y-3">
            {ARCH_LAYERS.map((layer) => {
              const Icon = layer.icon;
              const isSelected = selectedLayer.id === layer.id;
              return (
                <button
                  key={layer.id}
                  onClick={() => setSelectedLayer(layer)}
                  className={`w-full text-left p-4 rounded-xl border transition-all duration-200 cursor-pointer flex items-center justify-between ${
                    isSelected
                      ? 'bg-[#0e1629] border-cyan-500/70 shadow-lg shadow-cyan-950/50'
                      : 'bg-[#090e1c] border-slate-800 hover:border-slate-700 hover:bg-[#0c1224]'
                  }`}
                >
                  <div className="flex items-center gap-3.5 min-w-0">
                    <div
                      className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${
                        isSelected ? 'bg-cyan-950 border border-cyan-700' : 'bg-slate-800/60'
                      }`}
                    >
                      <Icon className={`w-4 h-4 ${layer.color}`} />
                    </div>
                    <div className="min-w-0">
                      <div className="text-sm font-bold text-white tracking-tight truncate">
                        {layer.name}
                      </div>
                      <div className="text-[11px] font-mono text-slate-400 truncate">
                        {layer.badge}
                      </div>
                    </div>
                  </div>
                  <ArrowRight
                    className={`w-4 h-4 flex-shrink-0 transition-transform ${
                      isSelected ? 'text-cyan-400 translate-x-1' : 'text-slate-600'
                    }`}
                  />
                </button>
              );
            })}
          </div>

          {/* Right Column: Layer Deep-Dive Inspection Card */}
          <div className="lg:col-span-6">
            <div className="glass-panel rounded-2xl p-6 sm:p-8 border-cyan-800/60 shadow-2xl space-y-6">
              <div className="flex items-center justify-between pb-4 border-b border-slate-800">
                <div>
                  <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-400 font-bold block">
                    Architecture Deep-Dive
                  </span>
                  <h3 className="text-xl font-bold text-white mt-1">{selectedLayer.name}</h3>
                </div>
                <span className="px-2.5 py-1 text-xs font-mono rounded-md bg-slate-800 text-slate-300 border border-slate-700">
                  {selectedLayer.badge}
                </span>
              </div>

              {/* Summary */}
              <p className="text-sm text-slate-300 leading-relaxed">
                {selectedLayer.summary}
              </p>

              {/* Code path & ports */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
                <div className="p-3 rounded-lg bg-[#070b16] border border-slate-800">
                  <span className="text-slate-500 block text-[10px] uppercase">Source File</span>
                  <span className="text-cyan-300 truncate block mt-0.5">{selectedLayer.codePath}</span>
                </div>
                <div className="p-3 rounded-lg bg-[#070b16] border border-slate-800">
                  <span className="text-slate-500 block text-[10px] uppercase">Port / Process</span>
                  <span className="text-emerald-400 truncate block mt-0.5">{selectedLayer.ports}</span>
                </div>
              </div>

              {/* Key Details */}
              <div className="space-y-2.5">
                <span className="text-xs font-mono font-bold uppercase text-slate-400 tracking-wider">
                  Key Technical Guarantees
                </span>
                <ul className="space-y-2 text-xs text-slate-300">
                  {selectedLayer.keyDetails.map((detail, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-cyan-400 font-bold mt-0.5">•</span>
                      <span className="leading-relaxed">{detail}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="pt-2 flex items-center justify-between">
                <Link
                  to="/docs/architecture"
                  className="text-xs font-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1.5 transition-colors"
                >
                  <span>Read Full Architecture Documentation</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
                <Link
                  to="/docs/quickstart"
                  className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-cyan-600/90 hover:bg-cyan-500 text-white transition-colors"
                >
                  Try It Out
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
