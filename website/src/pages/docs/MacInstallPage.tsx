import React from 'react';
import { Link } from 'react-router-dom';
import { Terminal, CheckCircle2, AlertTriangle, ArrowRight, Laptop } from 'lucide-react';
import { CodeBlock } from '../../components/docs/CodeBlock';
import { Callout } from '../../components/docs/Callout';

export const MacInstallPage: React.FC = () => {
  return (
    <div className="space-y-8">
      <div>
        <div className="text-xs font-mono font-bold uppercase tracking-wider text-purple-400 mb-1">
          Operating System Guide
        </div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">
          macOS Installation Guide (Apple Silicon & Intel)
        </h1>
        <p className="text-slate-400 text-sm leading-relaxed mt-2">
          Step-by-step instructions for running the platform on macOS Ventura, Sonoma, and Sequoia across Apple Silicon (M1/M2/M3/M4) and Intel Macs.
        </p>
      </div>

      <div className="space-y-3">
        <h2 className="text-lg font-bold text-white border-b border-slate-800 pb-2">
          1. System Requirements & Apple Silicon Notes
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          <div className="p-3.5 rounded-xl bg-[#090e1c] border border-slate-800">
            <span className="font-bold text-slate-200 block">Apple Silicon (M1/M2/M3/M4)</span>
            <span className="text-slate-400">Native arm64 execution supported. Docker Desktop handles multi-arch emulation seamlessly.</span>
          </div>
          <div className="p-3.5 rounded-xl bg-[#090e1c] border border-slate-800">
            <span className="font-bold text-slate-200 block">Intel Mac (x86_64)</span>
            <span className="text-slate-400">Standard x86_64 image execution natively supported.</span>
          </div>
          <div className="p-3.5 rounded-xl bg-[#090e1c] border border-slate-800">
            <span className="font-bold text-slate-200 block">Memory Allocation</span>
            <span className="text-slate-400">Allocate at least 4 GB RAM to Docker Desktop (Settings → Resources).</span>
          </div>
          <div className="p-3.5 rounded-xl bg-[#090e1c] border border-slate-800">
            <span className="font-bold text-slate-200 block">macOS Versions</span>
            <span className="text-slate-400">macOS 12 (Monterey), 13 (Ventura), 14 (Sonoma), 15 (Sequoia)</span>
          </div>
        </div>
      </div>

      <div className="space-y-6">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-purple-950 border border-purple-700 text-purple-400 flex items-center justify-center text-xs font-mono">1</span>
            Step 1: Install Docker Desktop for Mac
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Install Docker Desktop using Homebrew or direct download:
          </p>
          <CodeBlock
            code={`# Using Homebrew:
brew install --cask docker

# Or download dmg from docker.com (Choose Apple Silicon or Intel as appropriate)`}
            language="bash"
            title="macOS - Install Docker"
          />
          <p className="text-xs text-slate-400 mt-1">
            Open Docker from your Applications folder. Ensure Docker Desktop reports <strong>"Engine running"</strong> in the top menu bar.
          </p>
        </div>

        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-purple-950 border border-purple-700 text-purple-400 flex items-center justify-center text-xs font-mono">2</span>
            Step 2: Clone the Repository & Configure Environment
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Open Terminal and clone the project:
          </p>
          <CodeBlock
            code={`# Navigate to project directory:
cd intent-aware-deception
cp .env.example .env`}
            language="bash"
            title="macOS - Configure Environment"
          />
        </div>

        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-purple-950 border border-purple-700 text-purple-400 flex items-center justify-center text-xs font-mono">3</span>
            Step 3: Start the Docker Microservices
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Build and boot MongoDB, Cowrie, FastAPI backend, and the Vite frontend:
          </p>
          <CodeBlock
            code="docker compose up -d --build"
            language="bash"
            title="macOS - Start Docker Compose"
          />
          <p className="text-xs text-slate-400 mt-1">
            Check the running containers:
          </p>
          <CodeBlock
            code="docker compose ps"
            language="bash"
            title="macOS - Check Containers"
          />
        </div>

        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-purple-950 border border-purple-700 text-purple-400 flex items-center justify-center text-xs font-mono">4</span>
            Step 4: Stream Attack Sequences
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Create a local virtual environment to run the automated attack simulation:
          </p>
          <CodeBlock
            code={`python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 scripts/demo_all_intents.py`}
            language="bash"
            title="macOS - Attack Simulation"
          />
        </div>

        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-purple-950 border border-purple-700 text-purple-400 flex items-center justify-center text-xs font-mono">5</span>
            Step 5: View Live Telemetry in Safari or Chrome
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono my-3">
            <div className="p-4 rounded-xl bg-[#090e1c] border border-cyan-800/40">
              <span className="text-slate-400 block text-[11px]">SOC Dashboard</span>
              <a href="http://127.0.0.1:5173" target="_blank" rel="noopener noreferrer" className="text-cyan-400 font-bold hover:underline">
                http://127.0.0.1:5173
              </a>
            </div>
            <div className="p-4 rounded-xl bg-[#090e1c] border border-indigo-800/40">
              <span className="text-slate-400 block text-[11px]">API Swagger UI</span>
              <a href="http://127.0.0.1:8000/docs" target="_blank" rel="noopener noreferrer" className="text-indigo-400 font-bold hover:underline">
                http://127.0.0.1:8000/docs
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* Common macOS Troubleshooting */}
      <div className="space-y-4 pt-6 border-t border-slate-800">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-amber-400" />
          macOS Tips & Common Fixes
        </h2>

        <div className="space-y-3 text-xs">
          <div className="p-4 rounded-xl bg-[#090e1c] border border-slate-800 space-y-1.5">
            <div className="font-bold text-rose-400 font-mono">
              Rosetta 2 Emulation on Apple Silicon
            </div>
            <div className="text-slate-300">
              If Docker prompts that Rosetta is required to run certain legacy x86_64 containers:
            </div>
            <CodeBlock
              code="softwareupdate --install-rosetta"
              language="bash"
            />
          </div>

          <div className="p-4 rounded-xl bg-[#090e1c] border border-slate-800 space-y-1.5">
            <div className="font-bold text-rose-400 font-mono">
              Docker Desktop "Use Virtualization framework" Setting
            </div>
            <div className="text-slate-300">
              In Docker Desktop → Settings → General, ensure <strong>"Use Virtualization framework"</strong> is checked for maximum file system performance when mounting read-only volumes.
            </div>
          </div>
        </div>
      </div>

      <div className="pt-4 border-t border-slate-800 flex justify-between items-center text-xs">
        <Link to="/docs/installation/linux" className="text-slate-400 hover:text-white">
          ← Linux Installation Guide
        </Link>
        <Link to="/docs/installation/manual" className="text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1">
          <span>Manual Setup (Without Docker)</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
};
