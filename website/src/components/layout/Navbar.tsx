import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Shield,
  BookOpen,
  Terminal,
  Layers,
  Sparkles,
  Menu,
  X,
  ExternalLink,
  ChevronDown,
} from 'lucide-react';
import { GithubIcon } from '../common/GithubIcon';

export const Navbar: React.FC = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [installDropdownOpen, setInstallDropdownOpen] = useState(false);
  const location = useLocation();

  const isHome = location.pathname === '/';

  const scrollToSection = (id: string) => {
    if (isHome) {
      const el = document.getElementById(id);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth' });
        setMobileMenuOpen(false);
        return;
      }
    }
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-[#060913]/85 backdrop-blur-md border-b border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-600 to-indigo-600 p-0.5 shadow-lg shadow-cyan-950/60 group-hover:scale-105 transition-transform">
            <div className="w-full h-full bg-[#0a0f1d] rounded-[10px] flex items-center justify-center">
              <Shield className="w-4 h-4 text-cyan-400 group-hover:text-cyan-300 transition-colors" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-base tracking-tight font-sans text-slate-100 group-hover:text-white transition-colors">
                INT-AWARE
              </span>
              <span className="px-1.5 py-0.5 text-[10px] font-mono font-semibold bg-cyan-950/80 text-cyan-400 border border-cyan-800/50 rounded">
                v1.0
              </span>
            </div>
            <span className="text-[10px] text-slate-400 hidden sm:block font-mono">
              Intent-Aware Deception System
            </span>
          </div>
        </Link>

        {/* Desktop Navigation Links */}
        <nav className="hidden md:flex items-center gap-1 text-sm font-medium text-slate-300">
          <Link
            to="/"
            className={`px-3 py-1.5 rounded-lg hover:text-white hover:bg-slate-800/40 transition-colors ${
              location.pathname === '/' ? 'text-cyan-400 font-semibold' : ''
            }`}
          >
            Home
          </Link>

          {isHome ? (
            <button
              onClick={() => scrollToSection('features')}
              className="px-3 py-1.5 rounded-lg hover:text-white hover:bg-slate-800/40 transition-colors cursor-pointer"
            >
              Features
            </button>
          ) : (
            <Link
              to="/#features"
              className="px-3 py-1.5 rounded-lg hover:text-white hover:bg-slate-800/40 transition-colors"
            >
              Features
            </Link>
          )}

          {isHome ? (
            <button
              onClick={() => scrollToSection('architecture')}
              className="px-3 py-1.5 rounded-lg hover:text-white hover:bg-slate-800/40 transition-colors cursor-pointer"
            >
              Architecture
            </button>
          ) : (
            <Link
              to="/docs/architecture"
              className="px-3 py-1.5 rounded-lg hover:text-white hover:bg-slate-800/40 transition-colors"
            >
              Architecture
            </Link>
          )}

          {/* Installation Dropdown */}
          <div className="relative">
            <button
              onMouseEnter={() => setInstallDropdownOpen(true)}
              onClick={() => setInstallDropdownOpen(!installDropdownOpen)}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg hover:text-white hover:bg-slate-800/40 transition-colors cursor-pointer"
            >
              <span>Installation</span>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
            </button>

            {installDropdownOpen && (
              <div
                onMouseLeave={() => setInstallDropdownOpen(false)}
                className="absolute top-full left-0 mt-1 w-56 rounded-xl bg-[#090e1c] border border-slate-800 p-2 shadow-2xl z-50 space-y-1"
              >
                <Link
                  to="/docs/quickstart"
                  onClick={() => setInstallDropdownOpen(false)}
                  className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs hover:bg-cyan-950/40 hover:text-cyan-300 text-slate-300 transition-colors"
                >
                  <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                  <div>
                    <div className="font-semibold">60-Sec Quickstart</div>
                    <div className="text-[10px] text-slate-500">Fastest 1-command setup</div>
                  </div>
                </Link>
                <Link
                  to="/docs/installation/windows"
                  onClick={() => setInstallDropdownOpen(false)}
                  className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs hover:bg-cyan-950/40 hover:text-cyan-300 text-slate-300 transition-colors"
                >
                  <Terminal className="w-3.5 h-3.5 text-blue-400" />
                  <div>
                    <div className="font-semibold">Windows (WSL2 / Docker)</div>
                    <div className="text-[10px] text-slate-500">PowerShell & Docker Desktop</div>
                  </div>
                </Link>
                <Link
                  to="/docs/installation/linux"
                  onClick={() => setInstallDropdownOpen(false)}
                  className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs hover:bg-cyan-950/40 hover:text-cyan-300 text-slate-300 transition-colors"
                >
                  <Layers className="w-3.5 h-3.5 text-emerald-400" />
                  <div>
                    <div className="font-semibold">Linux (Ubuntu / Debian / RHEL)</div>
                    <div className="text-[10px] text-slate-500">Docker Engine & systemd</div>
                  </div>
                </Link>
                <Link
                  to="/docs/installation/macos"
                  onClick={() => setInstallDropdownOpen(false)}
                  className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs hover:bg-cyan-950/40 hover:text-cyan-300 text-slate-300 transition-colors"
                >
                  <Terminal className="w-3.5 h-3.5 text-purple-400" />
                  <div>
                    <div className="font-semibold">macOS (Apple Silicon & Intel)</div>
                    <div className="text-[10px] text-slate-500">M1/M2/M3 Docker setup</div>
                  </div>
                </Link>
              </div>
            )}
          </div>

          <Link
            to="/docs"
            className={`px-3 py-1.5 rounded-lg hover:text-white hover:bg-slate-800/40 transition-colors ${
              location.pathname.startsWith('/docs') ? 'text-cyan-400 font-semibold' : ''
            }`}
          >
            Documentation
          </Link>
        </nav>

        {/* Right Action Buttons */}
        <div className="hidden sm:flex items-center gap-3">
          <a
            href="https://github.com/Rakshita-Shetty7/INT-AWARE"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-3 py-1.5 text-xs font-mono font-medium rounded-lg border border-slate-800 hover:border-slate-700 bg-[#0a0f1d] hover:bg-slate-800/50 text-slate-300 hover:text-white transition-all shadow-sm"
          >
            <GithubIcon className="w-4 h-4 text-slate-400" />
            <span>GitHub</span>
          </a>

          <Link
            to="/docs/quickstart"
            className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-semibold rounded-lg bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white shadow-lg shadow-cyan-950/80 transition-all cursor-pointer"
          >
            <span>Get Started</span>
          </Link>
        </div>

        {/* Mobile menu trigger */}
        <div className="flex md:hidden">
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-[#070b16] border-b border-slate-800 px-4 pt-3 pb-6 space-y-3">
          <Link
            to="/"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-lg text-sm font-medium text-slate-300 hover:bg-slate-800/60 hover:text-cyan-400"
          >
            Home
          </Link>
          <Link
            to="/docs"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-lg text-sm font-medium text-slate-300 hover:bg-slate-800/60 hover:text-cyan-400"
          >
            Documentation Portal
          </Link>
          <Link
            to="/docs/quickstart"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-lg text-sm font-medium text-slate-300 hover:bg-slate-800/60 hover:text-cyan-400"
          >
            60-Second Quickstart
          </Link>
          <div className="pt-2 border-t border-slate-800/60 space-y-1">
            <span className="px-3 text-[11px] font-mono font-bold uppercase text-slate-500 tracking-wider">
              Installation Guides
            </span>
            <Link
              to="/docs/installation/windows"
              onClick={() => setMobileMenuOpen(false)}
              className="block px-3 py-1.5 text-xs text-slate-400 hover:text-cyan-300"
            >
              Windows (WSL2 / Docker)
            </Link>
            <Link
              to="/docs/installation/linux"
              onClick={() => setMobileMenuOpen(false)}
              className="block px-3 py-1.5 text-xs text-slate-400 hover:text-cyan-300"
            >
              Linux (Ubuntu / Debian / RHEL)
            </Link>
            <Link
              to="/docs/installation/macos"
              onClick={() => setMobileMenuOpen(false)}
              className="block px-3 py-1.5 text-xs text-slate-400 hover:text-cyan-300"
            >
              macOS (Apple Silicon & Intel)
            </Link>
            <Link
              to="/docs/installation/manual"
              onClick={() => setMobileMenuOpen(false)}
              className="block px-3 py-1.5 text-xs text-slate-400 hover:text-cyan-300"
            >
              Manual Setup (Without Docker)
            </Link>
          </div>
          <div className="pt-3 border-t border-slate-800/60 flex items-center justify-between">
            <a
              href="https://github.com/Rakshita-Shetty7/INT-AWARE"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-xs font-mono text-slate-400 hover:text-white"
            >
              <GithubIcon className="w-4 h-4" />
              <span>GitHub Repo</span>
              <ExternalLink className="w-3 h-3" />
            </a>
            <Link
              to="/docs/quickstart"
              onClick={() => setMobileMenuOpen(false)}
              className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-cyan-600 text-white"
            >
              Get Started
            </Link>
          </div>
        </div>
      )}
    </header>
  );
};
