import React from 'react';
import {
  Radio,
  Brain,
  GitBranch,
  Layers,
  Share2,
  FlaskConical,
  ShieldCheck,
  Zap,
  Lock,
} from 'lucide-react';
import { Link } from 'react-router-dom';

const FEATURES = [
  {
    icon: Radio,
    color: 'text-cyan-400',
    borderColor: 'hover:border-cyan-500/50',
    title: 'Real-Time SSH Honeypot Telemetry',
    subtitle: 'Isolated Cowrie Ingestion Engine',
    description:
      'Listens on port 2222 via a containerized Cowrie honeypot. Ingests authentication probes, terminal commands, and session lifecycle events with read-only volume mounting and zero host execution.',
    badge: 'Core Ingestion',
  },
  {
    icon: Brain,
    color: 'text-sky-400',
    borderColor: 'hover:border-sky-500/50',
    title: 'Calibrated Intent ML Pipeline',
    subtitle: 'Calibrated LinearSVC · 10 Intent Classes',
    description:
      'Deploys a calibrated LinearSVC classifier with TF-IDF character and word n-grams across 10 attacker intent categories (Reconnaissance to Exfiltration), complete with Shannon entropy confidence scoring.',
    badge: 'Machine Learning',
  },
  {
    icon: GitBranch,
    color: 'text-indigo-400',
    borderColor: 'hover:border-indigo-500/50',
    title: 'Markov Transition Modeling',
    subtitle: 'Adversary Kill-Chain Projection',
    description:
      'Analyzes sequential attacker progression across MITRE ATT&CK stages. Calculates empirical transition probabilities, detects abnormal sequence leaps, and projects probable next intents.',
    badge: 'Sequence Intelligence',
  },
  {
    icon: Layers,
    color: 'text-emerald-400',
    borderColor: 'hover:border-emerald-500/50',
    title: 'Attack Behavior Digital Twin',
    subtitle: 'Chronological Session Replay',
    description:
      'Reconstructs full interactive session timelines with playback controls (1x, 2x, 5x), cumulative risk scrubbing, next-intent accuracy verification, and counterfactual risk delta simulation.',
    badge: 'Digital Twin',
  },
  {
    icon: Share2,
    color: 'text-purple-400',
    borderColor: 'hover:border-purple-500/50',
    title: 'Attack Campaign Graph',
    subtitle: 'Multi-Entity Graph Topology',
    description:
      'Correlates threat actors across sessions, observed IP indicators, MITRE techniques, and behavioral similarities using Jaccard command overlap clustering on an interactive SVG canvas.',
    badge: 'Threat Topology',
  },
  {
    icon: FlaskConical,
    color: 'text-amber-400',
    borderColor: 'hover:border-amber-500/50',
    title: 'Controlled Research Security Labs',
    subtitle: 'Industrial, Financial & AI Guardrails',
    description:
      'Authoritative sandboxes for testing Modbus/SCADA physical invariants, financial wire fraud canary detection, and LLM prompt injection / MCP tool-call policy enforcement.',
    badge: 'Research Labs',
  },
];

export const FeaturesGrid: React.FC = () => {
  return (
    <section id="features" className="py-24 bg-[#060913] relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16 space-y-3">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-950/60 border border-cyan-800/60 text-xs font-mono text-cyan-400 font-semibold">
            <Zap className="w-3.5 h-3.5" />
            <span>Production-Grade Architecture</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Engineered for Modern Cyber Threat Operations
          </h2>
          <p className="text-slate-400 text-sm sm:text-base leading-relaxed">
            Every feature is backed by genuine backend microservices, real scikit-learn models, persistent MongoDB collections, and live WebSocket broadcasting.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {FEATURES.map((feature, idx) => {
            const Icon = feature.icon;
            return (
              <div
                key={idx}
                className={`glass-panel rounded-2xl p-6 flex flex-col justify-between transition-all duration-300 ${feature.borderColor} hover:bg-[#0a1122] hover:-translate-y-1 shadow-lg`}
              >
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="w-10 h-10 rounded-xl bg-slate-800/60 border border-slate-700/60 flex items-center justify-center">
                      <Icon className={`w-5 h-5 ${feature.color}`} />
                    </div>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800/80 text-slate-300 border border-slate-700/60">
                      {feature.badge}
                    </span>
                  </div>

                  <div>
                    <h3 className="text-base font-bold text-white tracking-tight">{feature.title}</h3>
                    <div className="text-xs font-mono text-slate-400 mt-0.5">{feature.subtitle}</div>
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed">
                    {feature.description}
                  </p>
                </div>

                <div className="pt-4 mt-4 border-t border-slate-800/60 flex items-center justify-between text-xs font-mono text-slate-400">
                  <span className="flex items-center gap-1 text-slate-500">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
                    Verified In Repo
                  </span>
                  <Link
                    to="/docs/architecture"
                    className="text-cyan-400 hover:text-cyan-300 transition-colors"
                  >
                    View Details →
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
