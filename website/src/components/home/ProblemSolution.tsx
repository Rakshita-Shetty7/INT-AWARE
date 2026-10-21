import React from 'react';
import { AlertCircle, CheckCircle2, ShieldAlert, Cpu, ArrowRight } from 'lucide-react';

export const ProblemSolution: React.FC = () => {
  return (
    <section className="py-20 bg-[#070b16] border-y border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16 space-y-3">
          <div className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-400">
            Cybersecurity Paradigm Shift
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            From Passive Log Traps to Active Attacker Profiling
          </h2>
          <p className="text-slate-400 text-sm sm:text-base leading-relaxed">
            Legacy honeypots act as passive log collectors that drown security teams in unranked command dumps. INT-AWARE transforms telemetry into intent-conditioned threat intelligence.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-stretch">
          {/* Legacy Honeypots */}
          <div className="rounded-2xl p-6 sm:p-8 bg-[#0a0f1d] border border-rose-950/60 shadow-xl space-y-6 flex flex-col justify-between">
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-rose-950/50 border border-rose-800/50 flex items-center justify-center">
                  <AlertCircle className="w-5 h-5 text-rose-400" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white">Traditional Honeypots</h3>
                  <p className="text-xs font-mono text-rose-400/90">Passive & Uncontextualized</p>
                </div>
              </div>

              <p className="text-sm text-slate-400 leading-relaxed">
                Conventional honeypots capture attacker keystrokes into raw flat JSON or syslog files without semantics or sequence intelligence.
              </p>

              <ul className="space-y-3 text-sm text-slate-300">
                <li className="flex items-start gap-2.5">
                  <span className="text-rose-500 font-bold mt-0.5">✕</span>
                  <span><strong>Zero Intent Understanding:</strong> Commands like <code>whoami</code> and <code>tar czf</code> are stored as equal raw strings with no intent awareness.</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="text-rose-500 font-bold mt-0.5">✕</span>
                  <span><strong>Manual Analyst Fatigue:</strong> SOC analysts must manually reconstruct kill chains hours or days after the breach event.</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="text-rose-500 font-bold mt-0.5">✕</span>
                  <span><strong>Static Alerting:</strong> Either alerts on every probe (alert fatigue) or only alerts after catastrophic exfiltration.</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="text-rose-500 font-bold mt-0.5">✕</span>
                  <span><strong>No Transition Modeling:</strong> Cannot predict what stage or objective the adversary is advancing toward next.</span>
                </li>
              </ul>
            </div>

            <div className="p-3.5 rounded-xl bg-rose-950/20 border border-rose-900/30 text-xs font-mono text-rose-300/80">
              Outcome: High analyst overhead, delayed triage, and loss of early kill-chain interception opportunities.
            </div>
          </div>

          {/* INT-AWARE System */}
          <div className="rounded-2xl p-6 sm:p-8 bg-[#0a1224] border border-cyan-800/50 shadow-2xl space-y-6 flex flex-col justify-between glow-cyan">
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-cyan-950/80 border border-cyan-600/50 flex items-center justify-center">
                  <CheckCircle2 className="w-5 h-5 text-cyan-400" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white">INT-AWARE Solution</h3>
                  <p className="text-xs font-mono text-cyan-400">Real-Time Intent Profiling & Machine Learning</p>
                </div>
              </div>

              <p className="text-sm text-slate-300 leading-relaxed">
                An end-to-end cyber deception pipeline that scores, categorizes, and tracks adversary behaviors in real time across the MITRE ATT&CK matrix.
              </p>

              <ul className="space-y-3 text-sm text-slate-200">
                <li className="flex items-start gap-2.5">
                  <span className="text-cyan-400 font-bold mt-0.5">✓</span>
                  <span><strong>Calibrated Intent Classification:</strong> Calibrated LinearSVC + TF-IDF classifies commands into 10 MITRE-aligned intent categories with <strong>94.49% real held-out accuracy</strong>.</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="text-cyan-400 font-bold mt-0.5">✓</span>
                  <span><strong>Cumulative Risk Escalation:</strong> Tracks session risk dynamically on a 0–100 scale, triggering automated alerts when risk hits ≥ 75.</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="text-cyan-400 font-bold mt-0.5">✓</span>
                  <span><strong>Markov Sequence Transition Engine:</strong> Evaluates attack progression likelihoods and detects anomalous leaps across kill-chain stages.</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="text-cyan-400 font-bold mt-0.5">✓</span>
                  <span><strong>Zero Host Execution Guarantee:</strong> Attacker commands are contained strictly within Cowrie's emulated virtual shell.</span>
                </li>
              </ul>
            </div>

            <div className="p-3.5 rounded-xl bg-cyan-950/40 border border-cyan-800/40 text-xs font-mono text-cyan-300 flex items-center justify-between">
              <span>Outcome: Instantaneous SOC visibility, digital twin replays & automated attacker dossiers.</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
