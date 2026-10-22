import React from 'react';
import { Link } from 'react-router-dom';
import { Zap, Terminal, CheckCircle2, ArrowRight } from 'lucide-react';
import { CodeBlock } from '../../components/docs/CodeBlock';
import { Callout } from '../../components/docs/Callout';

export const QuickstartPage: React.FC = () => {
  return (
    <div className="space-y-8">
      <div>
        <div className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-400 mb-1">
          Fast-Track Setup
        </div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">
          60-Second Quickstart Guide
        </h1>
        <p className="text-slate-400 text-sm leading-relaxed mt-2">
          Spin up the complete deception microservices stack with Docker Compose and stream genuine attack traffic in three commands.
        </p>
      </div>

      <div className="space-y-3">
        <h2 className="text-lg font-bold text-white border-b border-slate-800 pb-2">
          Prerequisites Check
        </h2>
        <ul className="space-y-1.5 text-xs text-slate-300">
          <li className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span><strong>Docker & Docker Compose:</strong> Docker Desktop (Windows/macOS) or Docker Engine (Linux).</span>
          </li>
          <li className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span><strong>Git:</strong> To clone or update the repository.</span>
          </li>
          <li className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span><strong>Python 3.12+ (Optional on Host):</strong> Only needed if driving the attack simulation script locally outside Docker.</span>
          </li>
        </ul>
      </div>

      <div className="space-y-6">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-cyan-950 border border-cyan-700 text-cyan-400 flex items-center justify-center text-xs font-mono">1</span>
            Step 1: Create Your Environment File
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Copy the template environment file to activate default ports and MongoDB settings:
          </p>
          <CodeBlock
            code={`# On Windows (PowerShell):
Copy-Item .env.example .env

# On Linux or macOS:
cp .env.example .env`}
            language="bash"
            title="Create .env"
          />
        </div>

        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-cyan-950 border border-cyan-700 text-cyan-400 flex items-center justify-center text-xs font-mono">2</span>
            Step 2: Launch the Microservices Stack
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Run Docker Compose to build and start MongoDB, Cowrie honeypot, FastAPI backend, and the React SOC dashboard:
          </p>
          <CodeBlock
            code="docker compose up -d --build"
            language="bash"
            title="Start Docker Stack"
          />
          <p className="text-xs text-slate-400 mt-1">
            Check that all four containers report <code>Up</code> or <code>Started</code>:
          </p>
          <CodeBlock
            code="docker compose ps"
            language="bash"
            title="Verify Containers"
          />
        </div>

        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-cyan-950 border border-cyan-700 text-cyan-400 flex items-center justify-center text-xs font-mono">3</span>
            Step 3: Open the SOC Dashboard
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Open your browser and navigate to the live analyst dashboard:
          </p>
          <div className="p-4 rounded-xl bg-[#090e1c] border border-cyan-800/40 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono my-3">
            <div>
              <div className="text-slate-300 font-bold">SOC Command Center:</div>
              <a href="http://127.0.0.1:5173" target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:underline">
                http://127.0.0.1:5173
              </a>
            </div>
            <div>
              <div className="text-slate-300 font-bold">FastAPI Interactive Docs:</div>
              <a href="http://127.0.0.1:8000/docs" target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:underline">
                http://127.0.0.1:8000/docs
              </a>
            </div>
          </div>
          <Callout type="info" title="Empty Dashboard State">
            A honeypot dashboard only shows live data once an attack occurs! Right now the dashboard will be clean and idle until you generate telemetry in Step 4.
          </Callout>
        </div>

        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-cyan-950 border border-cyan-700 text-cyan-400 flex items-center justify-center text-xs font-mono">4</span>
            Step 4: Stream Real Attack Telemetry
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Run the automated attack driver script. It connects over SSH to port 2222 with isolated credentials (<code>root:root</code>) and exercises all 10 intent classes:
          </p>
          <CodeBlock
            code={`# On Windows:
.venv\\Scripts\\python.exe scripts/demo_all_intents.py

# On Linux or macOS:
python3 scripts/demo_all_intents.py`}
            language="bash"
            title="Drive Attack Simulation"
          />
        </div>

        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-cyan-950 border border-cyan-700 text-cyan-400 flex items-center justify-center text-xs font-mono">5</span>
            Step 5: Verify Live End-to-End Pipeline
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Execute the live verification check to confirm model inference and database persistence:
          </p>
          <CodeBlock
            code={`# On Windows:
.venv\\Scripts\\python.exe scripts/verify_live.py

# On Linux or macOS:
python3 scripts/verify_live.py`}
            language="bash"
            title="Live Smoke Test"
          />
        </div>
      </div>

      <div className="pt-4 border-t border-slate-800 flex justify-between items-center text-xs">
        <Link to="/docs" className="text-slate-400 hover:text-white">
          ← Documentation Overview
        </Link>
        <Link to="/docs/installation/windows" className="text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1">
          <span>Windows Installation Guide</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
};
