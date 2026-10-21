import React from 'react';
import { Link } from 'react-router-dom';
import { Cpu, CheckCircle2, AlertTriangle, ArrowRight, Server } from 'lucide-react';
import { CodeBlock } from '../../components/docs/CodeBlock';
import { Callout } from '../../components/docs/Callout';

export const LinuxInstallPage: React.FC = () => {
  return (
    <div className="space-y-8">
      <div>
        <div className="text-xs font-mono font-bold uppercase tracking-wider text-emerald-400 mb-1">
          Operating System Guide
        </div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">
          Linux Installation Guide (Ubuntu, Debian, RHEL)
        </h1>
        <p className="text-slate-400 text-sm leading-relaxed mt-2">
          Production and development installation guide for Linux servers and workstations using Docker Engine and Docker Compose v2.
        </p>
      </div>

      <div className="space-y-3">
        <h2 className="text-lg font-bold text-white border-b border-slate-800 pb-2">
          1. Supported Distributions & Prerequisites
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          <div className="p-3.5 rounded-xl bg-[#090e1c] border border-slate-800">
            <span className="font-bold text-slate-200 block">Debian / Ubuntu Family</span>
            <span className="text-slate-400">Ubuntu 22.04 LTS, 24.04 LTS, Debian 11/12</span>
          </div>
          <div className="p-3.5 rounded-xl bg-[#090e1c] border border-slate-800">
            <span className="font-bold text-slate-200 block">Enterprise Linux</span>
            <span className="text-slate-400">RHEL 8/9, Rocky Linux 9, AlmaLinux 9</span>
          </div>
          <div className="p-3.5 rounded-xl bg-[#090e1c] border border-slate-800">
            <span className="font-bold text-slate-200 block">System Architecture</span>
            <span className="text-slate-400">x86_64 / amd64 or aarch64 (ARM64)</span>
          </div>
          <div className="p-3.5 rounded-xl bg-[#090e1c] border border-slate-800">
            <span className="font-bold text-slate-200 block">Resources</span>
            <span className="text-slate-400">2 GB RAM minimum, 10 GB disk space</span>
          </div>
        </div>
      </div>

      <div className="space-y-6">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-emerald-950 border border-emerald-700 text-emerald-400 flex items-center justify-center text-xs font-mono">1</span>
            Step 1: Install Docker Engine & Compose Plugin
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Install the official Docker Engine and compose plugin (Ubuntu/Debian example):
          </p>
          <CodeBlock
            code={`# Update apt package index
sudo apt update && sudo apt install -y ca-certificates curl gnupg

# Add Docker official GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Set up repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker packages
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin`}
            language="bash"
            title="Bash - Install Docker on Ubuntu"
          />
        </div>

        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-emerald-950 border border-emerald-700 text-emerald-400 flex items-center justify-center text-xs font-mono">2</span>
            Step 2: Enable Non-Root User Permissions
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Allow your current user to run Docker commands without prepending <code>sudo</code>:
          </p>
          <CodeBlock
            code={`sudo usermod -aG docker $USER
newgrp docker
docker --version && docker compose version`}
            language="bash"
            title="Bash - User Group Setup"
          />
        </div>

        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-emerald-950 border border-emerald-700 text-emerald-400 flex items-center justify-center text-xs font-mono">3</span>
            Step 3: Clone Repository & Configure Environment
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Clone the repository and copy the environment template:
          </p>
          <CodeBlock
            code={`git clone https://github.com/Rakshita-Shetty7/INT-AWARE.git
cd INT-AWARE
cp .env.example .env`}
            language="bash"
            title="Bash - Clone & Configure"
          />
        </div>

        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-emerald-950 border border-emerald-700 text-emerald-400 flex items-center justify-center text-xs font-mono">4</span>
            Step 4: Launch Microservices Daemon
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Start MongoDB, Cowrie honeypot, FastAPI backend, and the Vite SOC dashboard:
          </p>
          <CodeBlock
            code="docker compose up -d --build"
            language="bash"
            title="Bash - Start Containers"
          />
          <p className="text-xs text-slate-400 mt-1">
            Verify all containers are active:
          </p>
          <CodeBlock
            code="docker compose ps"
            language="bash"
            title="Bash - Check Status"
          />
        </div>

        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-emerald-950 border border-emerald-700 text-emerald-400 flex items-center justify-center text-xs font-mono">5</span>
            Step 5: Drive Real Attack Simulation
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Use Python 3 to stream synthetic attack sequences into Cowrie's port 2222:
          </p>
          <CodeBlock
            code={`python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 scripts/demo_all_intents.py`}
            language="bash"
            title="Bash - Drive Attack Telemetry"
          />
        </div>

        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-emerald-950 border border-emerald-700 text-emerald-400 flex items-center justify-center text-xs font-mono">6</span>
            Step 6: Access Dashboard & OpenAPI Docs
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            If running locally on a desktop, open your browser to:
          </p>
          <ul className="text-xs font-mono space-y-1 text-slate-300 my-2">
            <li>SOC Dashboard: <a href="http://127.0.0.1:5173" className="text-cyan-400 hover:underline">http://127.0.0.1:5173</a></li>
            <li>FastAPI Docs: <a href="http://127.0.0.1:8000/docs" className="text-indigo-400 hover:underline">http://127.0.0.1:8000/docs</a></li>
          </ul>
          <Callout type="info" title="Remote Headless Linux Server Access">
            If hosting on a remote VPS or EC2 instance, create an SSH local port forward to safely view the dashboard without exposing it to the public internet:
            <br />
            <code>ssh -L 5173:127.0.0.1:5173 -L 8000:127.0.0.1:8000 user@your-server-ip</code>
          </Callout>
        </div>
      </div>

      {/* Linux Troubleshooting */}
      <div className="space-y-4 pt-6 border-t border-slate-800">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-amber-400" />
          Common Linux Errors & Solutions
        </h2>

        <div className="space-y-3 text-xs">
          <div className="p-4 rounded-xl bg-[#090e1c] border border-slate-800 space-y-1.5">
            <div className="font-bold text-rose-400 font-mono">
              Error: "Got permission denied while trying to connect to the Docker daemon socket"
            </div>
            <div className="text-slate-300">
              <strong>Cause:</strong> Current user is not in the <code>docker</code> group or the shell session has not refreshed.
            </div>
            <div className="text-slate-400">
              <strong>Solution:</strong> Run <code>sudo usermod -aG docker $USER && newgrp docker</code> or log out and log back in.
            </div>
          </div>

          <div className="p-4 rounded-xl bg-[#090e1c] border border-slate-800 space-y-1.5">
            <div className="font-bold text-rose-400 font-mono">
              Error: "SELinux / Permission denied on volume mount" (RHEL / Rocky / Fedora)
            </div>
            <div className="text-slate-300">
              <strong>Cause:</strong> SELinux blocks container access to mounted project volumes.
            </div>
            <div className="text-slate-400">
              <strong>Solution:</strong> Set container volume label context:
            </div>
            <CodeBlock
              code="chcon -Rt svirt_sandbox_file_t ./honeypot/var/log/cowrie"
              language="bash"
            />
          </div>

          <div className="p-4 rounded-xl bg-[#090e1c] border border-slate-800 space-y-1.5">
            <div className="font-bold text-rose-400 font-mono">
              Notice: Does Cowrie conflict with host SSH daemon?
            </div>
            <div className="text-slate-300">
              <strong>Answer:</strong> No. Host SSH runs on port <code>22</code>. Cowrie honeypot is bound specifically to port <code>2222</code> on <code>127.0.0.1</code>. Both run peacefully side-by-side.
            </div>
          </div>
        </div>
      </div>

      <div className="pt-4 border-t border-slate-800 flex justify-between items-center text-xs">
        <Link to="/docs/installation/windows" className="text-slate-400 hover:text-white">
          ← Windows Installation Guide
        </Link>
        <Link to="/docs/installation/macos" className="text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1">
          <span>macOS Installation Guide</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
};
