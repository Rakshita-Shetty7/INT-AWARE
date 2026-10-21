import React, { useState } from 'react';
import { Terminal, Copy, Check, ArrowRight, ExternalLink, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';

export const QuickstartPreview: React.FC = () => {
  const [activeOS, setActiveOS] = useState<'windows' | 'linux' | 'macos'>('windows');
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const osCommands = {
    windows: [
      {
        step: '1. Create Environment File',
        desc: 'Creates a working configuration with sensible defaults.',
        cmd: 'Copy-Item .env.example .env',
      },
      {
        step: '2. Launch the Stack with Docker',
        desc: 'Builds and boots MongoDB, Cowrie honeypot, FastAPI, and Vite frontend.',
        cmd: 'docker compose up -d --build',
      },
      {
        step: '3. Drive Live Attack Simulation',
        desc: 'Connects to isolated Cowrie over SSH (2222) and exercises all 10 intent classes.',
        cmd: '.venv\\Scripts\\python.exe scripts/demo_all_intents.py',
      },
    ],
    linux: [
      {
        step: '1. Create Environment File',
        desc: 'Creates a working configuration with sensible defaults.',
        cmd: 'cp .env.example .env',
      },
      {
        step: '2. Launch the Stack with Docker',
        desc: 'Builds and boots MongoDB, Cowrie honeypot, FastAPI, and Vite frontend.',
        cmd: 'docker compose up -d --build',
      },
      {
        step: '3. Drive Live Attack Simulation',
        desc: 'Connects to isolated Cowrie over SSH (2222) and exercises all 10 intent classes.',
        cmd: 'python3 scripts/demo_all_intents.py',
      },
    ],
    macos: [
      {
        step: '1. Create Environment File',
        desc: 'Creates a working configuration with sensible defaults.',
        cmd: 'cp .env.example .env',
      },
      {
        step: '2. Launch the Stack with Docker',
        desc: 'Builds and boots MongoDB, Cowrie honeypot, FastAPI, and Vite frontend.',
        cmd: 'docker compose up -d --build',
      },
      {
        step: '3. Drive Live Attack Simulation',
        desc: 'Connects to isolated Cowrie over SSH (2222) and exercises all 10 intent classes.',
        cmd: 'python3 scripts/demo_all_intents.py',
      },
    ],
  };

  const handleCopy = async (cmd: string, idx: number) => {
    try {
      await navigator.clipboard.writeText(cmd);
      setCopiedIndex(idx);
      setTimeout(() => setCopiedIndex(null), 2000);
    } catch (err) {
      console.error('Failed to copy: ', err);
    }
  };

  const currentSteps = osCommands[activeOS];

  return (
    <section className="py-24 bg-[#060913]">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-12 space-y-3">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-950/60 border border-cyan-800/60 text-xs font-mono text-cyan-400 font-semibold">
            <Sparkles className="w-3.5 h-3.5 text-cyan-300" />
            <span>Zero-Fuss Deployment</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Up and Running in 60 Seconds
          </h2>
          <p className="text-slate-400 text-sm leading-relaxed">
            One Docker command starts the entire microservices stack. No local database installation required.
          </p>
        </div>

        {/* OS Selector Tabs */}
        <div className="flex items-center justify-center gap-2 mb-6">
          <button
            onClick={() => setActiveOS('windows')}
            className={`px-4 py-2 rounded-xl text-xs font-mono font-semibold transition-all cursor-pointer ${
              activeOS === 'windows'
                ? 'bg-cyan-950 text-cyan-300 border border-cyan-700 shadow-lg'
                : 'bg-[#090e1c] text-slate-400 border border-slate-800 hover:text-white'
            }`}
          >
            Windows (PowerShell)
          </button>
          <button
            onClick={() => setActiveOS('linux')}
            className={`px-4 py-2 rounded-xl text-xs font-mono font-semibold transition-all cursor-pointer ${
              activeOS === 'linux'
                ? 'bg-cyan-950 text-cyan-300 border border-cyan-700 shadow-lg'
                : 'bg-[#090e1c] text-slate-400 border border-slate-800 hover:text-white'
            }`}
          >
            Linux (Bash / Zsh)
          </button>
          <button
            onClick={() => setActiveOS('macos')}
            className={`px-4 py-2 rounded-xl text-xs font-mono font-semibold transition-all cursor-pointer ${
              activeOS === 'macos'
                ? 'bg-cyan-950 text-cyan-300 border border-cyan-700 shadow-lg'
                : 'bg-[#090e1c] text-slate-400 border border-slate-800 hover:text-white'
            }`}
          >
            macOS (Terminal)
          </button>
        </div>

        {/* Step-by-step command cards */}
        <div className="space-y-4">
          {currentSteps.map((step, idx) => (
            <div
              key={idx}
              className="p-4 sm:p-5 rounded-2xl bg-[#090e1c] border border-slate-800 hover:border-slate-700 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xl"
            >
              <div className="space-y-1 min-w-0">
                <div className="text-xs font-bold font-mono text-cyan-400">{step.step}</div>
                <div className="text-xs text-slate-400">{step.desc}</div>
                <div className="pt-1.5 font-mono text-xs sm:text-[13px] text-slate-200 bg-[#060913] px-3 py-2 rounded-lg border border-slate-800/80 truncate">
                  {step.cmd}
                </div>
              </div>

              <button
                onClick={() => handleCopy(step.cmd, idx)}
                className="self-start sm:self-center flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-cyan-300 text-xs font-mono font-medium transition-colors cursor-pointer flex-shrink-0"
                aria-label={`Copy step ${idx + 1} command`}
              >
                {copiedIndex === idx ? (
                  <>
                    <Check className="w-4 h-4 text-emerald-400" />
                    <span className="text-emerald-400 font-sans">Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4 text-slate-400" />
                    <span className="font-sans">Copy</span>
                  </>
                )}
              </button>
            </div>
          ))}
        </div>

        {/* Verification endpoints banner */}
        <div className="mt-8 p-5 rounded-2xl bg-gradient-to-r from-cyan-950/40 via-indigo-950/20 to-cyan-950/40 border border-cyan-800/40 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono">
          <div className="space-y-1 text-center sm:text-left">
            <div className="text-slate-200 font-bold">Once running, open your browser:</div>
            <div className="text-slate-400 flex flex-wrap gap-4 justify-center sm:justify-start">
              <span>SOC Dashboard: <strong className="text-cyan-400">http://127.0.0.1:5173</strong></span>
              <span>FastAPI Docs: <strong className="text-indigo-400">http://127.0.0.1:8000/docs</strong></span>
            </div>
          </div>

          <Link
            to="/docs/quickstart"
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs transition-colors flex-shrink-0"
          >
            <span>Full Quickstart Guide</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>
    </section>
  );
};
