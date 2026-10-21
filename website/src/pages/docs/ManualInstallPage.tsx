import React from 'react';
import { Link } from 'react-router-dom';
import { Settings, CheckCircle2, AlertTriangle, ArrowRight, Terminal } from 'lucide-react';
import { CodeBlock } from '../../components/docs/CodeBlock';
import { Callout } from '../../components/docs/Callout';

export const ManualInstallPage: React.FC = () => {
  return (
    <div className="space-y-8">
      <div>
        <div className="text-xs font-mono font-bold uppercase tracking-wider text-amber-400 mb-1">
          Alternative Installation Method
        </div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">
          Manual Installation Guide (Without Docker)
        </h1>
        <p className="text-slate-400 text-sm leading-relaxed mt-2">
          Run the honeypot, backend ingestion pipeline, and frontend dashboard directly on your host machine using Python, Node.js, and local MongoDB.
        </p>
      </div>

      <Callout type="warning" title="When to Use This Method">
        Docker Compose is the recommended path because it manages isolated networking and process supervision automatically. Use this manual guide only if Docker Desktop cannot be installed on your workstation.
      </Callout>

      <div className="space-y-3">
        <h2 className="text-lg font-bold text-white border-b border-slate-800 pb-2">
          Host Prerequisites
        </h2>
        <ul className="space-y-2 text-xs text-slate-300">
          <li className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span><strong>Python 3.12+</strong> with pip and virtualenv support.</span>
          </li>
          <li className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span><strong>Node.js 18+ & npm:</strong> Required for building and serving the React frontend.</span>
          </li>
          <li className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span><strong>MongoDB Community Server 6+:</strong> Running locally on <code>mongodb://localhost:27017</code>.</span>
          </li>
        </ul>
      </div>

      <div className="space-y-6">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-amber-950 border border-amber-700 text-amber-400 flex items-center justify-center text-xs font-mono">1</span>
            Step 1: Python Virtual Environment & Dependencies
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Create an isolated virtual environment at the project root and install all backend requirements:
          </p>
          <CodeBlock
            code={`# On Windows:
python -m venv .venv
.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env

# On Linux/macOS:
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env`}
            language="bash"
            title="Python Virtual Environment"
          />
        </div>

        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-amber-950 border border-amber-700 text-amber-400 flex items-center justify-center text-xs font-mono">2</span>
            Step 2: Terminal 1 — Start Isolated Cowrie Honeypot
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            In your first terminal tab, launch the Python-based Cowrie honeypot daemon on port 2222:
          </p>
          <CodeBlock
            code={`# Windows:
.venv\\Scripts\\python.exe scripts/run_cowrie.py

# Linux/macOS:
python3 scripts/run_cowrie.py`}
            language="bash"
            title="Terminal 1 - Cowrie Honeypot"
          />
        </div>

        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-amber-950 border border-amber-700 text-amber-400 flex items-center justify-center text-xs font-mono">3</span>
            Step 3: Terminal 2 — Start FastAPI Backend with Pipeline
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            In a second terminal, start the FastAPI API server with the background log tailer enabled:
          </p>
          <CodeBlock
            code={`# Windows:
.venv\\Scripts\\python.exe scripts/run_backend.py --host 127.0.0.1 --port 8000 --with-pipeline

# Linux/macOS:
python3 scripts/run_backend.py --host 127.0.0.1 --port 8000 --with-pipeline`}
            language="bash"
            title="Terminal 2 - Backend & Ingestion"
          />
        </div>

        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-amber-950 border border-amber-700 text-amber-400 flex items-center justify-center text-xs font-mono">4</span>
            Step 4: Terminal 3 — Start the Vite React Dashboard
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            In a third terminal, install frontend dependencies and start Vite dev server:
          </p>
          <CodeBlock
            code={`cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173`}
            language="bash"
            title="Terminal 3 - React Dashboard"
          />
          <p className="text-xs text-slate-400 mt-2">
            Open <strong>http://127.0.0.1:5173</strong> in your web browser.
          </p>
        </div>

        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-amber-950 border border-amber-700 text-amber-400 flex items-center justify-center text-xs font-mono">5</span>
            Step 5: Terminal 4 — Stream Live Attack Sequences
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            In a fourth terminal tab, trigger the automated attack simulation:
          </p>
          <CodeBlock
            code={`# Windows:
.venv\\Scripts\\python.exe scripts/demo_all_intents.py

# Linux/macOS:
python3 scripts/demo_all_intents.py`}
            language="bash"
            title="Terminal 4 - Drive Simulation"
          />
        </div>
      </div>

      <div className="pt-4 border-t border-slate-800 flex justify-between items-center text-xs">
        <Link to="/docs/installation/macos" className="text-slate-400 hover:text-white">
          ← macOS Installation Guide
        </Link>
        <Link to="/docs/configuration/env-vars" className="text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1">
          <span>Environment Variables Reference</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
};
