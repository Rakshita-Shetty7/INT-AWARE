import React from 'react';
import { Link } from 'react-router-dom';
import {
  BookOpen,
  Zap,
  Terminal,
  Cpu,
  Layers,
  ShieldCheck,
  CheckCircle,
  ExternalLink,
  ArrowRight,
} from 'lucide-react';
import { Callout } from '../../components/docs/Callout';

export const DocsOverviewPage: React.FC = () => {
  return (
    <div className="space-y-8">
      <div>
        <div className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-400 mb-1">
          Documentation Portal
        </div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">
          INT-AWARE Platform Documentation
        </h1>
        <p className="text-slate-400 text-sm leading-relaxed mt-2">
          Welcome to the comprehensive installation, architecture, and developer documentation for <strong>INT-AWARE: Intent-Aware Deception System for Real-Time Attacker Profiling</strong>.
        </p>
      </div>

      <Callout type="tip" title="Recommended Path for New Users">
        If you have Docker Desktop installed, jump directly to the{' '}
        <Link to="/docs/quickstart" className="text-cyan-400 underline font-semibold">
          60-Second Quickstart
        </Link>
        . It boots the entire platform using a single compose command.
      </Callout>

      <div className="space-y-4">
        <h2 className="text-xl font-bold text-white border-b border-slate-800 pb-2">
          Platform Architecture Summary
        </h2>
        <p className="text-xs text-slate-300 leading-relaxed">
          INT-AWARE is a research-grade cybersecurity cyber deception system. It deploys an emulated, containerized SSH honeypot (Cowrie), captures attacker interactions with zero host execution, classifies shell commands across 10 MITRE ATT&CK-aligned intent categories using a calibrated LinearSVC ML pipeline, models sequence transitions using Markov chains, and streams live threat intelligence to a real-time SOC dashboard.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
          <div className="p-4 rounded-xl bg-[#090e1c] border border-slate-800 space-y-1.5">
            <div className="text-xs font-bold text-cyan-400 font-mono">PORT 2222 (SSH)</div>
            <div className="text-xs text-white font-semibold">Isolated Cowrie Honeypot</div>
            <div className="text-[11px] text-slate-400">
              Emulated shell container. Commands typed by attackers never touch your host operating system.
            </div>
          </div>

          <div className="p-4 rounded-xl bg-[#090e1c] border border-slate-800 space-y-1.5">
            <div className="text-xs font-bold text-indigo-400 font-mono">PORT 8000 (FASTAPI)</div>
            <div className="text-xs text-white font-semibold">Ingestion & ML Inference Engine</div>
            <div className="text-[11px] text-slate-400">
              Tails honeypot JSON logs, runs TF-IDF + LinearSVC classification, and scores cumulative risk (0–100).
            </div>
          </div>

          <div className="p-4 rounded-xl bg-[#090e1c] border border-slate-800 space-y-1.5">
            <div className="text-xs font-bold text-emerald-400 font-mono">PORT 5173 (REACT UI)</div>
            <div className="text-xs text-white font-semibold">SOC Command Center</div>
            <div className="text-[11px] text-slate-400">
              Interactive dashboard featuring digital twin session replays, SVG campaign graphs, and live threat feeds.
            </div>
          </div>

          <div className="p-4 rounded-xl bg-[#090e1c] border border-slate-800 space-y-1.5">
            <div className="text-xs font-bold text-purple-400 font-mono">PORT 27017 (INTERNAL)</div>
            <div className="text-xs text-white font-semibold">MongoDB Document Store</div>
            <div className="text-[11px] text-slate-400">
              Persists normalized events, session records, attacker profiles, and triggered critical alerts.
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <h2 className="text-xl font-bold text-white border-b border-slate-800 pb-2">
          Documentation Directory
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Link
            to="/docs/quickstart"
            className="p-4 rounded-xl bg-[#090e1c] border border-slate-800 hover:border-cyan-700/60 transition-all group"
          >
            <div className="flex items-center gap-2 text-cyan-400 font-semibold text-xs font-mono mb-1">
              <Zap className="w-3.5 h-3.5" />
              <span>60-Second Quickstart</span>
            </div>
            <p className="text-xs text-slate-400">
              Get the entire stack up and running immediately with Docker Compose.
            </p>
          </Link>

          <Link
            to="/docs/installation/windows"
            className="p-4 rounded-xl bg-[#090e1c] border border-slate-800 hover:border-cyan-700/60 transition-all group"
          >
            <div className="flex items-center gap-2 text-blue-400 font-semibold text-xs font-mono mb-1">
              <Terminal className="w-3.5 h-3.5" />
              <span>Windows Installation</span>
            </div>
            <p className="text-xs text-slate-400">
              Step-by-step PowerShell and Docker Desktop setup on Windows 10/11.
            </p>
          </Link>

          <Link
            to="/docs/installation/linux"
            className="p-4 rounded-xl bg-[#090e1c] border border-slate-800 hover:border-cyan-700/60 transition-all group"
          >
            <div className="flex items-center gap-2 text-emerald-400 font-semibold text-xs font-mono mb-1">
              <Cpu className="w-3.5 h-3.5" />
              <span>Linux Installation</span>
            </div>
            <p className="text-xs text-slate-400">
              Ubuntu, Debian, and RHEL server deployment with Docker Engine.
            </p>
          </Link>

          <Link
            to="/docs/installation/macos"
            className="p-4 rounded-xl bg-[#090e1c] border border-slate-800 hover:border-cyan-700/60 transition-all group"
          >
            <div className="flex items-center gap-2 text-purple-400 font-semibold text-xs font-mono mb-1">
              <Terminal className="w-3.5 h-3.5" />
              <span>macOS Installation</span>
            </div>
            <p className="text-xs text-slate-400">
              Apple Silicon (M1/M2/M3) and Intel Mac Docker instructions.
            </p>
          </Link>

          <Link
            to="/docs/configuration/env-vars"
            className="p-4 rounded-xl bg-[#090e1c] border border-slate-800 hover:border-cyan-700/60 transition-all group"
          >
            <div className="flex items-center gap-2 text-amber-400 font-semibold text-xs font-mono mb-1">
              <Layers className="w-3.5 h-3.5" />
              <span>Environment Variables</span>
            </div>
            <p className="text-xs text-slate-400">
              Configuration reference for database, ports, logging, and optional Gemini AI.
            </p>
          </Link>

          <Link
            to="/docs/api"
            className="p-4 rounded-xl bg-[#090e1c] border border-slate-800 hover:border-cyan-700/60 transition-all group"
          >
            <div className="flex items-center gap-2 text-sky-400 font-semibold text-xs font-mono mb-1">
              <BookOpen className="w-3.5 h-3.5" />
              <span>API Reference</span>
            </div>
            <p className="text-xs text-slate-400">
              Full documentation of all REST endpoints and real-time WebSockets.
            </p>
          </Link>
        </div>
      </div>

      <div className="space-y-4">
        <h2 className="text-xl font-bold text-white border-b border-slate-800 pb-2">
          Security & Zero Host Execution Guarantee
        </h2>
        <p className="text-xs text-slate-300 leading-relaxed">
          The honeypot is designed with strict security isolation:
        </p>
        <ul className="space-y-2 text-xs text-slate-300 list-disc pl-5">
          <li><strong>Cowrie Sandbox:</strong> Keystrokes are handled exclusively inside Cowrie's virtual shell. No shell command is ever evaluated with <code>exec()</code>, <code>subprocess</code>, or <code>system()</code> on your host machine.</li>
          <li><strong>Localhost Binding:</strong> All published ports (2222, 8000, 5173) are bound strictly to <code>127.0.0.1</code>, preventing unsolicited inbound LAN traffic.</li>
          <li><strong>Read-Only Logs:</strong> The backend FastAPI container mounts the honeypot's log directory as <code>:ro</code> (read-only), guaranteeing that telemetry cannot be tampered with.</li>
        </ul>
      </div>
    </div>
  );
};
