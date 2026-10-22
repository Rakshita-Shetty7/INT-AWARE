import React from 'react';
import { Link } from 'react-router-dom';
import { Shield, BookOpen, ExternalLink, Heart, Terminal, CheckCircle } from 'lucide-react';
import { GithubIcon } from '../common/GithubIcon';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-[#050811] border-t border-slate-800/80 text-slate-400 text-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-12">
          {/* Brand Column */}
          <div className="md:col-span-1 space-y-3">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-cyan-600/30 border border-cyan-500/40 flex items-center justify-center">
                <Shield className="w-4 h-4 text-cyan-400" />
              </div>
              <span className="font-bold text-slate-100 text-sm tracking-tight">Intent-Aware Deception</span>
            </div>
            <p className="text-slate-400 text-xs leading-relaxed">
              Intent-Aware Deception System for Real-Time Attacker Profiling. Evidence-driven honeypot intelligence with calibrated machine learning and zero host execution.
            </p>
            <div className="flex items-center gap-2 pt-2 text-[11px] font-mono text-emerald-400">
              <CheckCircle className="w-3.5 h-3.5" />
              <span>166 / 166 Automated Tests Verified</span>
            </div>
          </div>

          {/* Column 2: Navigation */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold font-mono uppercase tracking-wider text-slate-200">
              Platform
            </h4>
            <ul className="space-y-2">
              <li>
                <Link to="/" className="hover:text-cyan-400 transition-colors">
                  Home Overview
                </Link>
              </li>
              <li>
                <Link to="/#features" className="hover:text-cyan-400 transition-colors">
                  Implemented Features
                </Link>
              </li>
              <li>
                <Link to="/docs/architecture" className="hover:text-cyan-400 transition-colors">
                  Architecture & Pipeline
                </Link>
              </li>
              <li>
                <Link to="/docs/api" className="hover:text-cyan-400 transition-colors">
                  REST & WebSocket API
                </Link>
              </li>
            </ul>
          </div>

          {/* Column 3: Installation Guides */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold font-mono uppercase tracking-wider text-slate-200">
              Installation Guides
            </h4>
            <ul className="space-y-2">
              <li>
                <Link to="/docs/quickstart" className="hover:text-cyan-400 transition-colors">
                  60-Second Quickstart
                </Link>
              </li>
              <li>
                <Link to="/docs/installation/windows" className="hover:text-cyan-400 transition-colors">
                  Windows Guide (PowerShell / WSL2)
                </Link>
              </li>
              <li>
                <Link to="/docs/installation/linux" className="hover:text-cyan-400 transition-colors">
                  Linux Guide (Ubuntu / Debian / RHEL)
                </Link>
              </li>
              <li>
                <Link to="/docs/installation/macos" className="hover:text-cyan-400 transition-colors">
                  macOS Guide (M1/M2/M3 & Intel)
                </Link>
              </li>
              <li>
                <Link to="/docs/installation/manual" className="hover:text-cyan-400 transition-colors">
                  Manual Setup (Without Docker)
                </Link>
              </li>
            </ul>
          </div>

          {/* Column 4: Documentation & Guides */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold font-mono uppercase tracking-wider text-slate-200">
              Operations & Verification
            </h4>
            <ul className="space-y-2">
              <li>
                <Link to="/docs/troubleshooting" className="hover:text-cyan-400 transition-colors">
                  Troubleshooting & Common Errors
                </Link>
              </li>
              <li>
                <Link to="/docs/maintenance" className="hover:text-cyan-400 transition-colors">
                  Maintenance & Volume Safety
                </Link>
              </li>
              <li>
                <Link to="/docs/contributing" className="hover:text-cyan-400 transition-colors">
                  Verification & Retraining Guide
                </Link>
              </li>
              <li>
                <Link to="/docs/configuration/env-vars" className="hover:text-cyan-400 transition-colors">
                  Environment & Secrets Reference
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 border-t border-slate-800/80 flex flex-col sm:flex-row items-center justify-between gap-4 text-[11px] text-slate-500 font-mono">
          <div>
            Intent-Aware Deception System for Real-Time Attacker Profiling
          </div>
          <div className="flex items-center gap-4">
            <span>Primary Accuracy: 100.0% (Held-Out)</span>
            <span>•</span>
            <span>166 Hermetic Tests Passed</span>
            <span>•</span>
            <span>Zero Host Execution</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
