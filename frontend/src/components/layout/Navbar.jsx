import React, { useEffect, useState } from 'react';
import { Shield, Radio, Terminal, Wifi, WifiOff, Brain, Sparkles, Bug, MessageSquare } from 'lucide-react';
import api from '../../services/api';
import useWebSocket from '../../hooks/useWebSocket';
import CopilotModal from '../copilot/CopilotModal';

export default function Navbar() {
  const [health, setHealth] = useState({ status: 'checking', database: 'checking', ml_model: {}, gemini_enabled: false, cowrie_log_present: false });
  const [time, setTime] = useState(new Date().toUTCString());
  const [copilotOpen, setCopilotOpen] = useState(false);

  // Connect to events channel to monitor live streaming status
  const { status: wsStatus } = useWebSocket('/ws/events', () => {});

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(new Date().toUTCString());
    }, 1000);

    const checkHealth = async () => {
      try {
        const data = await api.getHealth();
        setHealth(data);
      } catch (err) {
        setHealth({ status: 'degraded', database: 'disconnected' });
      }
    };

    checkHealth();
    const healthInterval = setInterval(checkHealth, 15000);

    return () => {
      clearInterval(timer);
      clearInterval(healthInterval);
    };
  }, []);

  return (
    <header className="h-16 bg-[#0d121d] border-b border-[#1f293d] px-4 sm:px-6 flex items-center justify-between gap-4 sticky top-0 z-30">
      <div className="flex items-center gap-3 min-w-0">
        <div className="p-2 bg-cyan-950/40 border border-cyan-800/60 rounded-md text-cyan-400 flex-shrink-0">
          <Shield className="w-5 h-5" />
        </div>
        <div className="min-w-0">
          <h1 className="text-sm font-bold tracking-wider text-slate-100 uppercase truncate">
            Intent-Aware Deception System
          </h1>
          <p className="text-[10px] text-slate-400 font-mono tracking-wide truncate">
            REAL-TIME ATTACKER PROFILING & HONEYPOT TELEMETRY
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3 flex-shrink-0">
        {/* System Time */}
        <div className="hidden md:flex items-center gap-2 text-xs font-mono text-slate-400">
          <Terminal className="w-3.5 h-3.5 text-slate-500" />
          <span>{time}</span>
        </div>

        {/* AI Copilot Trigger Button */}
        <button
          onClick={() => setCopilotOpen(true)}
          className="flex items-center gap-1.5 px-3 py-1 bg-gradient-to-r from-cyan-950 to-blue-950 hover:from-cyan-900 hover:to-blue-900 border border-cyan-700/60 text-cyan-300 rounded-full text-xs font-mono font-semibold transition-all shadow-md shadow-cyan-950/40"
        >
          <Sparkles className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
          <span>AI COPILOT</span>
        </button>

        {/* Real-Time WebSocket Streaming Indicator */}
        <div className="flex items-center gap-2 px-3 py-1 bg-[#111726] border border-[#1f293d] rounded-full text-xs font-mono">
          <span className={`w-2 h-2 rounded-full ${
            wsStatus === 'LIVE' ? 'bg-emerald-400 animate-pulse' :
            wsStatus === 'CONNECTING' ? 'bg-amber-400 animate-ping' : 'bg-rose-500'
          }`} />
          <span className={`font-semibold ${
            wsStatus === 'LIVE' ? 'text-emerald-400' :
            wsStatus === 'CONNECTING' ? 'text-amber-400' : 'text-rose-400'
          }`}>
            {wsStatus === 'LIVE' ? 'LIVE STREAM' : wsStatus === 'CONNECTING' ? 'CONNECTING...' : 'DISCONNECTED'}
          </span>
        </div>

        {/* Database Health Status */}
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 bg-[#0d121d] border border-[#1f293d]/80 rounded text-[11px] font-mono text-slate-400">
          <span className={`w-1.5 h-1.5 rounded-full ${health.database === 'connected' ? 'bg-cyan-400' : 'bg-rose-400'}`} />
          <span>DB: {health.database === 'connected' ? 'OK' : 'ERR'}</span>
        </div>

        {/* ML Model Status */}
        <div
          title={health?.ml_model?.available
            ? `Model: ${health.ml_model.model_name} · ${health.ml_model.classes} classes · held-out accuracy ${(health.ml_model.accuracy * 100).toFixed(1)}%`
            : 'ML classifier unavailable (running on rules + AI)'}
          className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 bg-[#0d121d] border border-[#1f293d]/80 rounded text-[11px] font-mono text-slate-400"
        >
          <Brain className={`w-3 h-3 ${health?.ml_model?.available ? 'text-violet-400' : 'text-slate-600'}`} />
          <span>ML: {health?.ml_model?.available
            ? (health.ml_model.accuracy ? `${(health.ml_model.accuracy * 100).toFixed(0)}%` : 'ON')
            : 'OFF'}</span>
        </div>

        {/* Gemini Semantic Layer Status */}
        <div
          title={health?.gemini_enabled ? 'Gemini semantic layer active (novel/ambiguous commands)' : 'Gemini optional layer inactive — system fully operational on rules + ML'}
          className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 bg-[#0d121d] border border-[#1f293d]/80 rounded text-[11px] font-mono text-slate-400"
        >
          <Sparkles className={`w-3 h-3 ${health?.gemini_enabled ? 'text-amber-400' : 'text-slate-600'}`} />
          <span>AI: {health?.gemini_enabled ? 'ON' : 'OFF'}</span>
        </div>

        {/* Honeypot (Cowrie) Feed Status */}
        <div
          title={health?.cowrie_log_present ? `Cowrie honeypot log connected (${health.collector_path})` : 'Cowrie log not yet present'}
          className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 bg-[#0d121d] border border-[#1f293d]/80 rounded text-[11px] font-mono text-slate-400"
        >
          <Bug className={`w-3 h-3 ${health?.cowrie_log_present ? 'text-emerald-400' : 'text-slate-600'}`} />
          <span>HONEYPOT: {health?.cowrie_log_present ? 'FEED' : 'IDLE'}</span>
        </div>
      </div>
      <CopilotModal isOpen={copilotOpen} onClose={() => setCopilotOpen(false)} />
    </header>
  );
}
