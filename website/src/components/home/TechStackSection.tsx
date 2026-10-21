import React from 'react';
import { Server, Database, Cpu, Layout, Box, Sparkles, CheckCircle2 } from 'lucide-react';

const TECH_GROUPS = [
  {
    category: 'Backend Microservices',
    icon: Server,
    color: 'text-cyan-400',
    techs: [
      { name: 'FastAPI', desc: 'Asynchronous Python web framework' },
      { name: 'Uvicorn', desc: 'High-performance ASGI server runtime' },
      { name: 'Pydantic v2', desc: 'Strict schema validation & serialization' },
      { name: 'WebSockets', desc: 'Real-time telemetry event streaming' },
    ],
  },
  {
    category: 'Machine Learning & NLP',
    icon: Cpu,
    color: 'text-indigo-400',
    techs: [
      { name: 'Scikit-learn', desc: 'LinearSVC & CalibratedClassifierCV' },
      { name: 'TF-IDF Vectorizer', desc: 'Sublinear TF word & char n-grams' },
      { name: 'Shannon Entropy', desc: 'Confidence uncertainty estimation' },
      { name: 'Joblib / Model Registry', desc: 'Cryptographic SHA-256 persistence' },
    ],
  },
  {
    category: 'Persistence & Ingestion',
    icon: Database,
    color: 'text-emerald-400',
    techs: [
      { name: 'MongoDB 7', desc: 'Document store for sessions, events, alerts' },
      { name: 'Motor', desc: 'Non-blocking async MongoDB client' },
      { name: 'Cowrie Collector', desc: 'Incremental file-pointer JSON tailer' },
      { name: 'Mongomock', desc: 'Zero-dependency in-memory mock testing' },
    ],
  },
  {
    category: 'Frontend Command Center',
    icon: Layout,
    color: 'text-sky-400',
    techs: [
      { name: 'React 19', desc: 'Modern reactive component hierarchy' },
      { name: 'Vite 8', desc: 'Instant HMR & lightning production builds' },
      { name: 'Tailwind CSS', desc: 'Futuristic dark SOC design system' },
      { name: 'Lucide Icons & Recharts', desc: 'Interactive charts & SVG topologies' },
    ],
  },
  {
    category: 'Isolation & Containerization',
    icon: Box,
    color: 'text-purple-400',
    techs: [
      { name: 'Cowrie Honeypot', desc: 'Emulated virtual SSH shell (Port 2222)' },
      { name: 'Docker Compose', desc: '4-service orchestrated stack' },
      { name: 'Read-Only Volumes', desc: 'Immutable log mounting for zero host risk' },
      { name: '127.0.0.1 Binding', desc: 'Strict localhost binding security policy' },
    ],
  },
  {
    category: 'Optional AI Intelligence',
    icon: Sparkles,
    color: 'text-amber-400',
    techs: [
      { name: 'Google Gemini Flash', desc: 'Semantic intent fallback on novel probes' },
      { name: 'Official google-genai SDK', desc: 'Structured adversary report generation' },
      { name: 'Zero-Crash Fallback', desc: 'Operates 100% offline if AI key is absent' },
      { name: 'Paramiko SSH', desc: 'Automated live telemetry demonstration' },
    ],
  },
];

export const TechStackSection: React.FC = () => {
  return (
    <section className="py-24 bg-[#070b16] border-t border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16 space-y-3">
          <div className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-400">
            Engineered Stack
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Built on Battle-Tested Open Source Technologies
          </h2>
          <p className="text-slate-400 text-sm sm:text-base leading-relaxed">
            Every layer of INT-AWARE is built with modern, performant, and secure libraries. Zero proprietary lock-in.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {TECH_GROUPS.map((group, idx) => {
            const Icon = group.icon;
            return (
              <div
                key={idx}
                className="p-6 rounded-2xl bg-[#090e1c] border border-slate-800 space-y-4 hover:border-slate-700 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-slate-800/80 flex items-center justify-center">
                    <Icon className={`w-4 h-4 ${group.color}`} />
                  </div>
                  <h3 className="text-sm font-bold text-white tracking-tight">{group.category}</h3>
                </div>

                <div className="space-y-2.5 pt-1">
                  {group.techs.map((tech, tIdx) => (
                    <div
                      key={tIdx}
                      className="p-2.5 rounded-lg bg-[#060913] border border-slate-800/80 flex items-start justify-between gap-2"
                    >
                      <div>
                        <div className="text-xs font-bold text-slate-200 font-mono">{tech.name}</div>
                        <div className="text-[11px] text-slate-400">{tech.desc}</div>
                      </div>
                      <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0 mt-0.5" />
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
