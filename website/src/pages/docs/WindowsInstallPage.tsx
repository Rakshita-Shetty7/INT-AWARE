import React from 'react';
import { Link } from 'react-router-dom';
import { Terminal, CheckCircle2, AlertTriangle, ArrowRight, Shield } from 'lucide-react';
import { CodeBlock } from '../../components/docs/CodeBlock';
import { Callout } from '../../components/docs/Callout';

export const WindowsInstallPage: React.FC = () => {
  return (
    <div className="space-y-8">
      <div>
        <div className="text-xs font-mono font-bold uppercase tracking-wider text-blue-400 mb-1">
          Operating System Guide
        </div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">
          Windows Installation Guide (Docker & WSL2)
        </h1>
        <p className="text-slate-400 text-sm leading-relaxed mt-2">
          Complete, verified walkthrough for setting up the platform on Windows 10 and 11 using PowerShell and Docker Desktop.
        </p>
      </div>

      <div className="space-y-3">
        <h2 className="text-lg font-bold text-white border-b border-slate-800 pb-2">
          1. System Requirements & Prerequisites
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          <div className="p-3.5 rounded-xl bg-[#090e1c] border border-slate-800">
            <span className="font-bold text-slate-200 block">Operating System</span>
            <span className="text-slate-400">Windows 10 64-bit (Build 19041+) or Windows 11</span>
          </div>
          <div className="p-3.5 rounded-xl bg-[#090e1c] border border-slate-800">
            <span className="font-bold text-slate-200 block">Docker Desktop</span>
            <span className="text-slate-400">WSL2 backend enabled (version 4.25+)</span>
          </div>
          <div className="p-3.5 rounded-xl bg-[#090e1c] border border-slate-800">
            <span className="font-bold text-slate-200 block">Memory & CPU</span>
            <span className="text-slate-400">Minimum 4 GB RAM (8 GB recommended), 2+ cores</span>
          </div>
          <div className="p-3.5 rounded-xl bg-[#090e1c] border border-slate-800">
            <span className="font-bold text-slate-200 block">Python (Host Driver)</span>
            <span className="text-slate-400">Python 3.12+ (tick "Add Python to PATH" on install)</span>
          </div>
        </div>
      </div>

      <div className="space-y-6">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-blue-950 border border-blue-700 text-blue-400 flex items-center justify-center text-xs font-mono">1</span>
            Step 1: Install & Verify Docker Desktop on Windows
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Download Docker Desktop from{' '}
            <a href="https://www.docker.com/products/docker-desktop/" target="_blank" rel="noopener noreferrer" className="text-cyan-400 underline">
              docker.com
            </a>
            . During installation, ensure the <strong>"Use WSL 2 instead of Hyper-V"</strong> option is checked. Once installed, start Docker Desktop and wait until the status in the bottom-left corner displays <strong>"Engine running"</strong>.
          </p>
          <p className="text-xs text-slate-400 mt-2">
            Open <strong>PowerShell</strong> (press <kbd className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-200">Win + X</kbd> → Terminal / PowerShell) and verify Docker:
          </p>
          <CodeBlock
            code="docker --version; docker compose version"
            language="powershell"
            title="PowerShell - Check Docker"
          />
        </div>

        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-blue-950 border border-blue-700 text-blue-400 flex items-center justify-center text-xs font-mono">2</span>
            Step 2: Clone or Open the Repository
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Open the repository directory in PowerShell:
          </p>
          <CodeBlock
            code={`# Navigate to the project root:
cd intent-aware-deception`}
            language="powershell"
            title="PowerShell - Navigate to Project"
          />
        </div>

        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-blue-950 border border-blue-700 text-blue-400 flex items-center justify-center text-xs font-mono">3</span>
            Step 3: Create the Environment File
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Use PowerShell's <code>Copy-Item</code> to create <code>.env</code> from <code>.env.example</code>:
          </p>
          <CodeBlock
            code="Copy-Item .env.example .env"
            language="powershell"
            title="PowerShell - Copy .env"
          />
          <Callout type="tip" title="Optional AI Feature">
            The platform is 100% operational on ML + rules out of the box without any API keys. If you wish to enable the optional Gemini semantic layer, open <code>.env</code> and set <code>GEMINI_API_KEY=your_key</code> from Google AI Studio.
          </Callout>
        </div>

        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-blue-950 border border-blue-700 text-blue-400 flex items-center justify-center text-xs font-mono">4</span>
            Step 4: Launch the Microservices Stack
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Execute the Docker Compose command to build and launch all 4 services:
          </p>
          <CodeBlock
            code="docker compose up -d --build"
            language="powershell"
            title="PowerShell - Start Stack"
          />
          <p className="text-xs text-slate-400 mt-1">
            First launch takes ~2–3 minutes to pull base images and compile assets. Confirm status:
          </p>
          <CodeBlock
            code="docker compose ps"
            language="powershell"
            title="PowerShell - Check Status"
          />
        </div>

        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-blue-950 border border-blue-700 text-blue-400 flex items-center justify-center text-xs font-mono">5</span>
            Step 5: Access the Dashboard & API
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono my-3">
            <div className="p-4 rounded-xl bg-[#090e1c] border border-cyan-800/40">
              <span className="text-slate-400 block text-[11px]">SOC Command Center</span>
              <a href="http://127.0.0.1:5173" target="_blank" rel="noopener noreferrer" className="text-cyan-400 font-bold hover:underline">
                http://127.0.0.1:5173
              </a>
            </div>
            <div className="p-4 rounded-xl bg-[#090e1c] border border-indigo-800/40">
              <span className="text-slate-400 block text-[11px]">FastAPI Swagger Docs</span>
              <a href="http://127.0.0.1:8000/docs" target="_blank" rel="noopener noreferrer" className="text-indigo-400 font-bold hover:underline">
                http://127.0.0.1:8000/docs
              </a>
            </div>
          </div>
        </div>

        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-blue-950 border border-blue-700 text-blue-400 flex items-center justify-center text-xs font-mono">6</span>
            Step 6: Stream Simulated Attack Traffic
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Set up the local attack driver helper (one-time setup):
          </p>
          <CodeBlock
            code={`python -m venv .venv
.venv\\Scripts\\python.exe -m pip install -r requirements.txt
.venv\\Scripts\\python.exe scripts/demo_all_intents.py`}
            language="powershell"
            title="PowerShell - Attack Driver"
          />
          <p className="text-xs text-slate-400 mt-2">
            Watch the live dashboard at <code>http://127.0.0.1:5173</code> update instantly as commands arrive!
          </p>
        </div>

        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-blue-950 border border-blue-700 text-blue-400 flex items-center justify-center text-xs font-mono">7</span>
            (Optional) Attack the Honeypot Manually via SSH
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Windows 10/11 includes OpenSSH by default. You can connect directly:
          </p>
          <CodeBlock
            code={`ssh root@127.0.0.1 -p 2222
# Password: root`}
            language="powershell"
            title="PowerShell - Manual SSH Attack"
          />
          <p className="text-xs text-slate-400 mt-1">
            Type commands like <code>uname -a</code>, <code>cat /etc/shadow</code>, and <code>whoami</code>. Cowrie emulates the output safely with zero host execution. Type <code>exit</code> when done.
          </p>
        </div>
      </div>

      {/* Common Windows Troubleshooting */}
      <div className="space-y-4 pt-6 border-t border-slate-800">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-amber-400" />
          Common Windows & PowerShell Errors
        </h2>

        <div className="space-y-3 text-xs">
          <div className="p-4 rounded-xl bg-[#090e1c] border border-slate-800 space-y-1.5">
            <div className="font-bold text-rose-400 font-mono">
              Error: "File ... cannot be loaded because running scripts is disabled on this system"
            </div>
            <div className="text-slate-300">
              <strong>Cause:</strong> PowerShell's default script execution policy prevents running virtual environment scripts.
            </div>
            <div className="text-slate-400">
              <strong>Solution:</strong> Open PowerShell as Administrator and run:
            </div>
            <CodeBlock
              code="Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser"
              language="powershell"
            />
          </div>

          <div className="p-4 rounded-xl bg-[#090e1c] border border-slate-800 space-y-1.5">
            <div className="font-bold text-rose-400 font-mono">
              Error: "Bind for 127.0.0.1:2222 failed: port is already allocated"
            </div>
            <div className="text-slate-300">
              <strong>Cause:</strong> Another application (e.g. an existing Cowrie or SSH daemon) is already using port 2222.
            </div>
            <div className="text-slate-400">
              <strong>Solution:</strong> Find and stop the process:
            </div>
            <CodeBlock
              code={`Get-NetTCPConnection -LocalPort 2222
# Or stop the running Docker stack:
docker compose down`}
              language="powershell"
            />
          </div>

          <div className="p-4 rounded-xl bg-[#090e1c] border border-slate-800 space-y-1.5">
            <div className="font-bold text-rose-400 font-mono">
              Error: "Cannot connect to the Docker daemon"
            </div>
            <div className="text-slate-300">
              <strong>Cause:</strong> Docker Desktop is closed or starting up.
            </div>
            <div className="text-slate-400">
              <strong>Solution:</strong> Launch Docker Desktop from the Start Menu and wait until the status displays "Engine running".
            </div>
          </div>
        </div>
      </div>

      <div className="pt-4 border-t border-slate-800 flex justify-between items-center text-xs">
        <Link to="/docs/quickstart" className="text-slate-400 hover:text-white">
          ← 60-Second Quickstart
        </Link>
        <Link to="/docs/installation/linux" className="text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1">
          <span>Linux Installation Guide</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
};
