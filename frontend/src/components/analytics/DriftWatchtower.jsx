import React, { useState, useEffect } from 'react';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Cpu,
  HelpCircle,
  Play,
  RotateCcw,
  Sparkles,
  TrendingDown,
  TrendingUp,
  Zap,
} from 'lucide-react';
import api from '../../services/api';
import LoadingState from '../common/LoadingState';
import ErrorState from '../common/ErrorState';

export default function DriftWatchtower() {
  const [driftReport, setDriftReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Command novelty testing state
  const [testCmd, setTestCmd] = useState('sudo -u root /usr/bin/python3 -c "import pty; pty.spawn(\'/bin/bash\')"');
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);

  const fetchDrift = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getDriftReport();
      setDriftReport(data);
    } catch (err) {
      setError(err.message || 'Failed to retrieve drift report.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDrift();
  }, []);

  const handleTestCommand = async () => {
    if (!testCmd.trim()) return;
    try {
      setTesting(true);
      const res = await api.testCommandDrift(testCmd.trim());
      setTestResult(res);
    } catch (err) {
      console.error('Command drift test failed:', err);
    } finally {
      setTesting(false);
    }
  };

  if (loading) {
    return <LoadingState message="Evaluating Concept Drift & Population Stability Index (PSI)..." />;
  }

  if (error || !driftReport) {
    return <ErrorState message={error || 'Drift monitor unavailable.'} onRetry={fetchDrift} />;
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'STABLE':
        return 'text-emerald-400 bg-emerald-950/60 border-emerald-800/60';
      case 'MODERATE_DRIFT':
        return 'text-amber-400 bg-amber-950/60 border-amber-800/60';
      case 'SIGNIFICANT_DRIFT':
        return 'text-rose-400 bg-rose-950/60 border-rose-800/60';
      default:
        return 'text-cyan-400 bg-cyan-950/60 border-cyan-800/60';
    }
  };

  return (
    <div className="space-y-6">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* PSI Status */}
        <div className="p-4 bg-[#111726] border border-[#1f293d] rounded-xl space-y-1">
          <span className="text-[11px] font-mono text-slate-400 uppercase">Population Stability Index</span>
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold font-mono text-slate-100">
              {driftReport.psi_score.toFixed(3)}
            </span>
            <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${getStatusColor(driftReport.drift_status)}`}>
              {driftReport.drift_status}
            </span>
          </div>
          <p className="text-[11px] text-slate-400 font-mono">Thresholds: &lt;0.10 Stable | &gt;0.25 Drift</p>
        </div>

        {/* Mean Prediction Entropy */}
        <div className="p-4 bg-[#111726] border border-[#1f293d] rounded-xl space-y-1">
          <span className="text-[11px] font-mono text-slate-400 uppercase">Mean Shannon Entropy</span>
          <div className="text-2xl font-bold font-mono text-cyan-400">
            {driftReport.mean_prediction_entropy} <span className="text-xs text-slate-500 font-normal">bits</span>
          </div>
          <p className="text-[11px] text-slate-400 font-mono">Sliding window average model uncertainty</p>
        </div>

        {/* Novelty Rate */}
        <div className="p-4 bg-[#111726] border border-[#1f293d] rounded-xl space-y-1">
          <span className="text-[11px] font-mono text-slate-400 uppercase">Novelty / OOD Rate</span>
          <div className="text-2xl font-bold font-mono text-purple-400">
            {(driftReport.novelty_rate * 100).toFixed(1)}%
          </div>
          <p className="text-[11px] text-slate-400 font-mono">Unseen token vocabulary frequency</p>
        </div>

        {/* Evaluation Window Size */}
        <div className="p-4 bg-[#111726] border border-[#1f293d] rounded-xl space-y-1">
          <span className="text-[11px] font-mono text-slate-400 uppercase">Telemetry Observation Window</span>
          <div className="text-2xl font-bold font-mono text-amber-400">
            {driftReport.window_size} <span className="text-xs text-slate-500 font-normal">events</span>
          </div>
          <p className="text-[11px] text-slate-400 font-mono">Bounded FIFO buffer (max 500)</p>
        </div>
      </div>

      {/* SOC Recommendation Banner */}
      <div className="p-4 bg-[#0d1424] border border-cyan-800/60 rounded-xl flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Sparkles className="w-5 h-5 text-cyan-400 flex-shrink-0" />
          <div>
            <h4 className="text-xs font-mono font-bold text-slate-100 uppercase tracking-wider">
              Model Watchtower Recommendation
            </h4>
            <p className="text-xs text-slate-300 mt-0.5">{driftReport.recommendation}</p>
          </div>
        </div>
        <button
          onClick={fetchDrift}
          className="p-1.5 bg-[#162032] border border-[#23324f] hover:border-cyan-600 rounded text-slate-300"
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Interactive Command Novelty & Abstention Lab */}
      <div className="bg-[#111726] border border-[#1f293d] p-5 rounded-xl space-y-4">
        <div className="flex items-center justify-between border-b border-[#1e293b] pb-2">
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-cyan-400" />
            <h4 className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider">
              Interactive Command Novelty & Abstention Tester
            </h4>
          </div>
          <span className="text-[10px] text-slate-500 font-mono">Live TF-IDF + Calibrated LinearSVC</span>
        </div>

        <div className="flex gap-2">
          <input
            type="text"
            value={testCmd}
            onChange={(e) => setTestCmd(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleTestCommand()}
            placeholder="Type any shell command..."
            className="flex-1 bg-[#0a0d14] border border-[#1f293d] focus:border-cyan-500 rounded-lg px-4 py-2 text-xs font-mono text-emerald-400 focus:outline-none"
          />
          <button
            onClick={handleTestCommand}
            disabled={testing || !testCmd.trim()}
            className="px-4 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white rounded text-xs font-mono font-bold flex items-center gap-2"
          >
            <Play className="w-3.5 h-3.5" />
            <span>{testing ? 'Evaluating...' : 'Score Command'}</span>
          </button>
        </div>

        {/* Test Result Display */}
        {testResult && (
          <div className="p-4 bg-[#0a0d14] border border-[#1f293d] rounded-xl space-y-3 animate-in fade-in">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#162032] pb-2">
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono text-slate-400">Predicted Intent:</span>
                <span className="text-xs font-mono font-bold text-cyan-400">
                  {testResult.predicted_intent}
                </span>
                <span className="text-[11px] font-mono text-slate-500">
                  (Stage: {testResult.attack_stage})
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono text-slate-300">
                  Confidence: <strong>{((testResult.confidence || 0) * 100).toFixed(1)}%</strong>
                </span>
                {testResult.should_abstain ? (
                  <span className="text-[10px] px-2 py-0.5 rounded bg-rose-950 border border-rose-800 text-rose-400 font-mono">
                    ABSTENTION RECOMMENDED
                  </span>
                ) : (
                  <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 border border-emerald-800 text-emerald-400 font-mono">
                    CONFIDENT PREDICTION
                  </span>
                )}
              </div>
            </div>

            {/* Metrics Breakdown */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
              <div className="p-2 bg-[#111726] rounded border border-[#1f293d]">
                <span className="text-slate-500 text-[10px]">SHANNON ENTROPY</span>
                <div className="text-slate-200 mt-0.5">{testResult.entropy} bits</div>
              </div>
              <div className="p-2 bg-[#111726] rounded border border-[#1f293d]">
                <span className="text-slate-500 text-[10px]">NOVELTY RATIO</span>
                <div className="text-slate-200 mt-0.5">{((testResult.novelty_score || 0) * 100).toFixed(0)}%</div>
              </div>
              <div className="p-2 bg-[#111726] rounded border border-[#1f293d]">
                <span className="text-slate-500 text-[10px]">IS NOVEL / OOD</span>
                <div className={testResult.is_novel ? 'text-amber-400 mt-0.5' : 'text-slate-400 mt-0.5'}>
                  {testResult.is_novel ? 'TRUE (Unseen tokens)' : 'FALSE'}
                </div>
              </div>
              <div className="p-2 bg-[#111726] rounded border border-[#1f293d]">
                <span className="text-slate-500 text-[10px]">HYBRID FALLBACK</span>
                <div className="text-slate-200 mt-0.5">
                  {testResult.should_abstain ? 'Rule / Gemini Tier' : 'ML Primary'}
                </div>
              </div>
            </div>

            {/* Evidence items */}
            {testResult.evidence?.length > 0 && (
              <div className="space-y-1 pt-1 text-[11px] font-mono text-slate-400">
                {testResult.evidence.map((ev, i) => (
                  <div key={i} className="flex items-center gap-1.5">
                    <span className="text-cyan-500">•</span>
                    <span>{ev}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
