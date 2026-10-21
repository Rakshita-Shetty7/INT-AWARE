import React from 'react';
import { Link } from 'react-router-dom';
import { Layers, ShieldCheck, Radio, Database, Cpu, Activity, ArrowRight } from 'lucide-react';
import { CodeBlock } from '../../components/docs/CodeBlock';
import { Callout } from '../../components/docs/Callout';

export const ArchitectureDocsPage: React.FC = () => {
  return (
    <div className="space-y-8">
      <div>
        <div className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-400 mb-1">
          Deep Technical Architecture
        </div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">
          System Architecture & Pipeline Specification
        </h1>
        <p className="text-slate-400 text-sm leading-relaxed mt-2">
          Detailed architectural breakdown of the Cowrie honeypot telemetry collector, feature extraction, calibrated LinearSVC intent classifier, Markov sequence transitions, and risk scoring.
        </p>
      </div>

      <div className="space-y-6">
        <div>
          <h2 className="text-lg font-bold text-white border-b border-slate-800 pb-2">
            1. High-Level Dataflow Pipeline
          </h2>
          <div className="p-4 rounded-xl bg-[#090e1c] border border-slate-800 my-3 font-mono text-xs text-slate-300 leading-loose">
            [Attacker Shell Probe] <br />
            &nbsp;&nbsp;│ (SSH on Port 2222 · Emulated Debian Environment)<br />
            &nbsp;&nbsp;▼<br />
            [Isolated Cowrie Honeypot Container]<br />
            &nbsp;&nbsp;│ (Emitted to cowrie.json log with read-only volume)<br />
            &nbsp;&nbsp;▼<br />
            [Async Cowrie Collector & Deduplicator (MD5)]<br />
            &nbsp;&nbsp;│ (NormalizedEvent Schema: session_id, command, timestamp)<br />
            &nbsp;&nbsp;▼<br />
            [Hybrid Intent Engine]<br />
            &nbsp;&nbsp;├── Regex Rule Engine (High-severity instant signatures)<br />
            &nbsp;&nbsp;├── Calibrated LinearSVC (94.49% held-out test accuracy)<br />
            &nbsp;&nbsp;└── Shannon Entropy Filter + Gemini Semantic Fallback<br />
            &nbsp;&nbsp;▼<br />
            [Markov Sequence Engine & Risk Progression]<br />
            &nbsp;&nbsp;├── Empirical Transition Probability P(Intent_t | Intent_t-1)<br />
            &nbsp;&nbsp;├── Kill-Chain Stage Mapping (Recon → Exfil)<br />
            &nbsp;&nbsp;└── Cumulative Session Risk (0–100 scale, Critical Alert &ge; 75)<br />
            &nbsp;&nbsp;▼<br />
            [Motor Async Persistence & WebSockets]<br />
            &nbsp;&nbsp;├── MongoDB Collections: events, sessions, attackers, alerts<br />
            &nbsp;&nbsp;└── WebSockets: /ws/events, /ws/alerts<br />
            &nbsp;&nbsp;▼<br />
            [React 19 / Vite SOC Command Center (Port 5173)]
          </div>
        </div>

        <div>
          <h2 className="text-lg font-bold text-white border-b border-slate-800 pb-2">
            2. The 10 MITRE-Aligned Intent Classes
          </h2>
          <p className="text-xs text-slate-300 leading-relaxed mt-2">
            Every command executed by an adversary is mapped into one of 10 categorical intent classes:
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono my-3">
            <div className="p-3 rounded-lg bg-[#090e1c] border border-slate-800">
              <span className="text-cyan-400 font-bold block">1. RECONNAISSANCE</span>
              <span className="text-slate-400 font-sans">Initial environmental discovery: <code>uname -a</code>, <code>whoami</code>.</span>
            </div>
            <div className="p-3 rounded-lg bg-[#090e1c] border border-slate-800">
              <span className="text-cyan-400 font-bold block">2. DISCOVERY</span>
              <span className="text-slate-400 font-sans">System/network enumeration: <code>ps aux</code>, <code>netstat -antp</code>, <code>ls -la</code>.</span>
            </div>
            <div className="p-3 rounded-lg bg-[#090e1c] border border-slate-800">
              <span className="text-cyan-400 font-bold block">3. CREDENTIAL_ACCESS</span>
              <span className="text-slate-400 font-sans">Credential dumping: <code>cat /etc/shadow</code>, <code>cat ~/.ssh/id_rsa</code>.</span>
            </div>
            <div className="p-3 rounded-lg bg-[#090e1c] border border-slate-800">
              <span className="text-cyan-400 font-bold block">4. EXECUTION</span>
              <span className="text-slate-400 font-sans">Payload staging & running: <code>wget ...; chmod +x; ./p.sh</code>.</span>
            </div>
            <div className="p-3 rounded-lg bg-[#090e1c] border border-slate-800">
              <span className="text-cyan-400 font-bold block">5. PRIVILEGE_ESCALATION</span>
              <span className="text-slate-400 font-sans">Elevation attempts: <code>sudo su -</code>, <code>sudo -l</code>, SUID abuse.</span>
            </div>
            <div className="p-3 rounded-lg bg-[#090e1c] border border-slate-800">
              <span className="text-cyan-400 font-bold block">6. PERSISTENCE</span>
              <span className="text-slate-400 font-sans">Implanting footholds: <code>crontab -e</code>, modifying <code>authorized_keys</code>.</span>
            </div>
            <div className="p-3 rounded-lg bg-[#090e1c] border border-slate-800">
              <span className="text-cyan-400 font-bold block">7. EXPLOITATION</span>
              <span className="text-slate-400 font-sans">Vulnerability probing: Shellshock, Dirty COW, Log4j string probes.</span>
            </div>
            <div className="p-3 rounded-lg bg-[#090e1c] border border-slate-800">
              <span className="text-cyan-400 font-bold block">8. EXFILTRATION</span>
              <span className="text-slate-400 font-sans">Data theft & packaging: <code>tar czf loot.tar.gz</code>, <code>scp ...</code>.</span>
            </div>
            <div className="p-3 rounded-lg bg-[#090e1c] border border-slate-800">
              <span className="text-cyan-400 font-bold block">9. CLEANUP</span>
              <span className="text-slate-400 font-sans">Anti-forensic log wiping: <code>history -c</code>, <code>rm /var/log/auth.log</code>.</span>
            </div>
            <div className="p-3 rounded-lg bg-[#090e1c] border border-slate-800">
              <span className="text-cyan-400 font-bold block">10. OTHER</span>
              <span className="text-slate-400 font-sans">Benign or unstructured commands: <code>echo hello</code>, <code>clear</code>.</span>
            </div>
          </div>
        </div>

        <div>
          <h2 className="text-lg font-bold text-white border-b border-slate-800 pb-2">
            3. Risk Scoring & Alert Threshold Floor
          </h2>
          <p className="text-xs text-slate-300 leading-relaxed mt-2">
            Risk is evaluated at two distinct granularities:
          </p>
          <ul className="space-y-2 text-xs text-slate-300 list-disc pl-5">
            <li><strong>Event Risk (0–65):</strong> Each individual command is assigned an explainable risk increment based on intent severity (e.g. Reconnaissance adds +10; Exfiltration adds +35). Event risk is deliberately bounded below 65 to prevent single-event false-positive alarms.</li>
            <li><strong>Session Cumulative Risk (0–100):</strong> As the attacker progresses along the kill chain, their session risk accumulates with temporal decay. When session risk hits <strong>&ge; 75</strong>, the engine fires a <code>CRITICAL</code> threat alert and broadcasts it across WebSockets.</li>
          </ul>
        </div>
      </div>

      <div className="pt-4 border-t border-slate-800 flex justify-between items-center text-xs">
        <Link to="/docs/quickstart" className="text-slate-400 hover:text-white">
          ← 60-Second Quickstart
        </Link>
        <Link to="/docs/installation/windows" className="text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1">
          <span>Proceed to Windows Installation</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
};
