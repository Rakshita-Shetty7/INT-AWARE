import React, { useState, useEffect } from 'react';
import {
  Play,
  Pause,
  RotateCcw,
  SkipForward,
  Activity,
  Shield,
  Layers,
  ArrowRight,
  TrendingUp,
  AlertTriangle,
  FileText,
  Key,
  Clock,
  Sparkles,
  Zap,
  CheckCircle2,
  XCircle,
  Download,
} from 'lucide-react';
import api from '../../services/api';
import SeverityBadge from '../common/SeverityBadge';
import IntentBadge from '../common/IntentBadge';
import LoadingState from '../common/LoadingState';
import ErrorState from '../common/ErrorState';

export default function DigitalTwinView({ sessionId }) {
  const [twin, setTwin] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Playback state
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playSpeed, setPlaySpeed] = useState(1500); // ms per step

  // Counterfactual simulation state
  const [cfResult, setCfResult] = useState(null);
  const [cfLoading, setCfLoading] = useState(false);

  // Storyboard download state
  const [storyboard, setStoryboard] = useState(null);
  const [storyboardLoading, setStoryboardLoading] = useState(false);

  const fetchTwin = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getDigitalTwin(sessionId);
      setTwin(data);
      if (data?.timeline?.length > 0) {
        setCurrentStepIndex(data.timeline.length - 1); // default to final state
      }
    } catch (err) {
      setError(err.message || 'Failed to construct Attack Behavior Digital Twin.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTwin();
  }, [sessionId]);

  // Autoplay loop
  useEffect(() => {
    if (!isPlaying || !twin?.timeline?.length) return;

    const interval = setInterval(() => {
      setCurrentStepIndex((prev) => {
        if (prev >= twin.timeline.length - 1) {
          setIsPlaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, playSpeed);

    return () => clearInterval(interval);
  }, [isPlaying, twin, playSpeed]);

  const handleSimulateCounterfactual = async (eventId) => {
    try {
      setCfLoading(true);
      const res = await api.simulateCounterfactual(sessionId, eventId);
      setCfResult(res);
    } catch (err) {
      console.error('Counterfactual simulation failed:', err);
    } finally {
      setCfLoading(false);
    }
  };

  const handleDownloadStoryboard = async () => {
    try {
      setStoryboardLoading(true);
      const sb = await api.getStoryboard(sessionId);
      setStoryboard(sb);

      // Trigger client JSON download
      const blob = new Blob([JSON.stringify(sb, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `incident_storyboard_${sessionId}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Storyboard download failed:', err);
    } finally {
      setStoryboardLoading(false);
    }
  };

  if (loading) {
    return <LoadingState message="Reconstructing Attack Behavior Digital Twin & Trajectory..." />;
  }

  if (error || !twin) {
    return <ErrorState message={error || 'Digital twin data not found.'} onRetry={fetchTwin} />;
  }

  const currentStep = twin.timeline[currentStepIndex] || twin.timeline[0];

  return (
    <div className="space-y-6">
      {/* Top Banner & Playback Header */}
      <div className="bg-[#111726] border border-[#1f293d] p-4 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold text-cyan-400 bg-cyan-950/60 border border-cyan-800/60 px-2 py-0.5 rounded">
              DIGITAL TWIN REPLAY
            </span>
            <span className="text-xs font-mono text-slate-400">
              Session: <strong className="text-slate-200">{twin.session_id}</strong>
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Replay execution step {currentStepIndex + 1} of {twin.total_steps} (Peak Risk: {twin.max_risk_score}/100)
          </p>
        </div>

        {/* Playback Controls */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => setCurrentStepIndex(0)}
            title="Reset to Step 1"
            className="p-2 bg-[#0a0d14] border border-[#1f293d] rounded text-slate-400 hover:text-slate-200"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className="px-4 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white rounded text-xs font-bold font-mono flex items-center gap-1.5 shadow-lg shadow-cyan-950/50"
          >
            {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
            <span>{isPlaying ? 'PAUSE' : 'REPLAY'}</span>
          </button>
          <button
            onClick={() => setCurrentStepIndex(Math.min(twin.total_steps - 1, currentStepIndex + 1))}
            title="Next Step"
            className="p-2 bg-[#0a0d14] border border-[#1f293d] rounded text-slate-400 hover:text-slate-200"
          >
            <SkipForward className="w-4 h-4" />
          </button>

          {/* Speed Selector */}
          <select
            value={playSpeed}
            onChange={(e) => setPlaySpeed(Number(e.target.value))}
            className="bg-[#0a0d14] border border-[#1f293d] text-xs font-mono text-slate-300 rounded px-2 py-1.5 focus:outline-none"
          >
            <option value={2000}>0.5x Speed</option>
            <option value={1200}>1.0x Speed</option>
            <option value={600}>2.0x Speed</option>
          </select>

          <button
            onClick={handleDownloadStoryboard}
            disabled={storyboardLoading}
            className="px-3 py-2 bg-[#162032] border border-[#23324f] hover:border-cyan-700/60 text-slate-200 rounded text-xs font-mono flex items-center gap-1.5 transition-colors"
          >
            <Download className="w-3.5 h-3.5 text-cyan-400" />
            <span>{storyboardLoading ? 'Exporting...' : 'Incident Storyboard'}</span>
          </button>
        </div>
      </div>

      {/* Scrubbing Timeline Slider */}
      <div className="bg-[#0d121d] border border-[#1f293d] p-4 rounded-xl space-y-2">
        <div className="flex justify-between text-xs font-mono text-slate-400">
          <span>Start: Step 1</span>
          <span className="text-cyan-400 font-bold">
            Step {currentStepIndex + 1} / {twin.total_steps}
          </span>
          <span>End: Step {twin.total_steps}</span>
        </div>
        <input
          type="range"
          min={0}
          max={Math.max(0, twin.total_steps - 1)}
          value={currentStepIndex}
          onChange={(e) => {
            setIsPlaying(false);
            setCurrentStepIndex(Number(e.target.value));
          }}
          className="w-full accent-cyan-400 h-2 bg-[#162032] rounded-lg cursor-pointer"
        />
      </div>

      {/* Main Grid: Active Replay Step & Intelligence Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Active Command Execution Card */}
        <div className="lg:col-span-2 bg-[#111726] border border-[#1f293d] rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-[#1e293b] pb-3">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping" />
              <h4 className="text-sm font-bold text-slate-100 font-mono">
                COMMAND EXECUTION TELEMETRY
              </h4>
            </div>
            <span className="text-xs font-mono text-slate-400">
              {new Date(currentStep?.timestamp).toLocaleTimeString()} UTC
            </span>
          </div>

          {/* Terminal Command Output Box */}
          <div className="p-4 bg-[#070a10] border border-[#1b253b] rounded-lg font-mono text-xs space-y-2">
            <div className="flex items-center justify-between text-slate-500 pb-1 border-b border-[#162032]">
              <span>honeypot-ssh-shell [sandboxed]</span>
              <span>Event ID: {currentStep?.event_id}</span>
            </div>
            <div className="text-emerald-400 font-semibold text-sm">
              <span className="text-slate-500">$ </span>
              {currentStep?.command || '<session_event_without_command>'}
            </div>
            {currentStep?.deception_strategy && (
              <div className="pt-2 text-slate-300 border-t border-[#162032]">
                <span className="text-cyan-400 font-bold">Deception Intervention:</span>{' '}
                <span className="text-slate-300">{currentStep.deception_strategy}</span> (Delay: {currentStep.deception_delay_ms || 0}ms)
              </div>
            )}
            {currentStep?.honeytokens?.length > 0 && (
              <div className="text-amber-400 text-[11px] flex items-center gap-1.5">
                <Key className="w-3.5 h-3.5" />
                <span>Canary Honeytoken Injected: {currentStep.honeytokens.join(', ')}</span>
              </div>
            )}
          </div>

          {/* Step Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 bg-[#0a0d14] border border-[#1f293d] rounded-lg">
              <span className="text-[10px] text-slate-500 font-mono uppercase">Intent</span>
              <div className="mt-1">
                <IntentBadge intent={currentStep?.intent} />
              </div>
            </div>
            <div className="p-3 bg-[#0a0d14] border border-[#1f293d] rounded-lg">
              <span className="text-[10px] text-slate-500 font-mono uppercase">Attack Stage</span>
              <div className="text-xs font-mono font-semibold text-slate-200 mt-1 truncate">
                {currentStep?.attack_stage}
              </div>
            </div>
            <div className="p-3 bg-[#0a0d14] border border-[#1f293d] rounded-lg">
              <span className="text-[10px] text-slate-500 font-mono uppercase">Step Risk</span>
              <div className="text-xs font-mono font-bold text-amber-400 mt-1">
                +{currentStep?.step_risk} ({currentStep?.step_severity})
              </div>
            </div>
            <div className="p-3 bg-[#0a0d14] border border-[#1f293d] rounded-lg">
              <span className="text-[10px] text-slate-500 font-mono uppercase">Cumulative Risk</span>
              <div className="text-xs font-mono font-bold text-rose-400 mt-1">
                {currentStep?.cumulative_risk}/100 ({currentStep?.cumulative_severity})
              </div>
            </div>
          </div>

          {/* Action: Counterfactual Simulation Button for this step */}
          <div className="pt-2 flex items-center justify-between border-t border-[#1e293b]">
            <span className="text-xs text-slate-400 font-mono">
              Measure causal risk impact of this specific event:
            </span>
            <button
              onClick={() => handleSimulateCounterfactual(currentStep?.event_id)}
              disabled={cfLoading}
              className="px-3 py-1.5 bg-[#162032] border border-cyan-800/60 hover:bg-cyan-950/60 text-cyan-300 rounded text-xs font-mono flex items-center gap-1.5 transition-colors"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>{cfLoading ? 'Simulating...' : 'Simulate Exclusion'}</span>
            </button>
          </div>

          {/* Counterfactual Result Card (if evaluated) */}
          {cfResult && cfResult.excluded_event_id === currentStep?.event_id && (
            <div className="p-4 bg-cyan-950/30 border border-cyan-700/60 rounded-xl space-y-2 animate-in fade-in">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-wider flex items-center gap-1.5">
                  <TrendingUp className="w-3.5 h-3.5" /> Counterfactual Outcome
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-900/60 text-cyan-300 border border-cyan-700">
                  Rating: {cfResult.criticality_rating}
                </span>
              </div>
              <p className="text-xs text-slate-200 font-sans">{cfResult.causal_explanation}</p>
              <div className="flex gap-4 text-xs font-mono text-slate-300 pt-1">
                <span>Original: {cfResult.original_risk_score} pts</span>
                <span className="text-cyan-400 font-bold">Counterfactual: {cfResult.counterfactual_risk_score} pts</span>
                <span className="text-emerald-400 font-bold">Reduction: -{cfResult.risk_delta} pts ({cfResult.percentage_contribution}%)</span>
              </div>
            </div>
          )}
        </div>

        {/* Right Sidebar: Next-Intent Projections & Kill-Chain Milestones */}
        <div className="space-y-4">
          {/* Next-Intent Prediction Tracker */}
          <div className="p-4 bg-[#111726] border border-[#1f293d] rounded-xl space-y-3">
            <div className="flex items-center justify-between border-b border-[#1e293b] pb-2">
              <span className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                <TrendingUp className="w-3.5 h-3.5 text-cyan-400" /> Next-Intent Projection
              </span>
              <span className="text-[10px] font-mono text-slate-500">
                P(Intent_t+1 | Step {currentStep?.step})
              </span>
            </div>

            <div className="space-y-2">
              {currentStep?.predicted_next_intents?.map((pred, i) => (
                <div key={i} className="p-2.5 bg-[#0a0d14] rounded-lg border border-[#1f293d] flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-cyan-500 font-mono text-xs font-bold">#{i + 1}</span>
                    <span className="text-xs font-mono text-slate-200">{pred.intent}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-16 bg-[#162032] rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-cyan-400 h-full rounded-full"
                        style={{ width: `${(pred.probability || 0) * 100}%` }}
                      />
                    </div>
                    <span className="text-xs font-mono text-cyan-400">
                      {((pred.probability || 0) * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>

            {/* Verification against subsequent observed behavior */}
            {currentStep?.actual_next_intent && (
              <div className="p-2.5 bg-[#0a0d14] rounded-lg border border-[#1f293d] text-xs font-mono space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Actual Subsequent Action:</span>
                  <span className="text-slate-200 font-bold">{currentStep.actual_next_intent}</span>
                </div>
                <div className="flex items-center gap-1.5 pt-1">
                  {currentStep.prediction_hit_top3 ? (
                    <span className="text-emerald-400 flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Hit in Top-3 Markov Projections
                    </span>
                  ) : (
                    <span className="text-amber-400 flex items-center gap-1">
                      <AlertTriangle className="w-3.5 h-3.5" /> Novel Transition Leap
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Kill Chain Stage Milestones */}
          <div className="p-4 bg-[#111726] border border-[#1f293d] rounded-xl space-y-3">
            <span className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-purple-400" /> Stage Milestones ({twin.stage_milestones.length})
            </span>
            <div className="space-y-2">
              {twin.stage_milestones.map((m, idx) => {
                const isPassed = currentStep?.step >= m.first_step;
                return (
                  <div
                    key={idx}
                    className={`p-2.5 rounded-lg border text-xs font-mono transition-colors ${
                      isPassed
                        ? 'bg-[#0e1626] border-cyan-800/60 text-slate-200'
                        : 'bg-[#0a0d14] border-[#1f293d] text-slate-500 opacity-60'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-cyan-400">{m.stage}</span>
                      <span>Step #{m.first_step}</span>
                    </div>
                    {m.trigger_command && (
                      <div className="text-[11px] text-slate-400 truncate mt-1">
                        $ {m.trigger_command}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
