import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Radio,
  ArrowLeft,
  Terminal,
  Shield,
  Activity,
  Brain,
  Sparkles,
  Layers,
  ChevronRight,
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  Lightbulb,
  ExternalLink,
  RefreshCw,
} from 'lucide-react';
import api from '../services/api';
import SeverityBadge from '../components/common/SeverityBadge';
import IntentBadge from '../components/common/IntentBadge';
import MitreBadge from '../components/common/MitreBadge';
import RiskIndicator from '../components/common/RiskIndicator';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';

export default function SessionDetailPage() {
  const { sessionId } = useParams();
  const [session, setSession] = useState(null);
  const [events, setEvents] = useState([]);
  const [mitreTechniques, setMitreTechniques] = useState([]);
  const [aiReport, setAiReport] = useState(null);
  const [aiEnabled, setAiEnabled] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchSessionDetails = async () => {
    try {
      setLoading(true);
      setError(null);

      const [sessionData, eventsData, mitreData] = await Promise.all([
        api.getSession(sessionId),
        api.getEvents({ session_id: sessionId, limit: 150 }),
        api.getSessionMitre(sessionId).catch(() => []),
      ]);

      setSession(sessionData);
      setEvents(eventsData.items || []);
      setMitreTechniques(mitreData || []);
    } catch (err) {
      setError(err.message || `Failed to load details for session ${sessionId}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessionDetails();
    api.getHealth()
      .then((health) => setAiEnabled(Boolean(health.gemini_enabled)))
      .catch(() => setAiEnabled(false));
  }, [sessionId]);

  const handleRunAiAnalysis = async () => {
    try {
      setIsAnalyzing(true);
      setAnalysisError(null);
      const report = await api.analyzeSession(sessionId);
      setAiReport(report);
    } catch (err) {
      setAnalysisError(err.message || 'Failed to generate AI session report.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  if (loading) {
    return <LoadingState message={`Retrieving threat trajectory for session ${sessionId}...`} />;
  }

  if (error || !session) {
    return <ErrorState message={error || 'Session not found.'} onRetry={fetchSessionDetails} />;
  }

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Actions */}
      <div className="flex items-center justify-between">
        <Link
          to="/sessions"
          className="inline-flex items-center gap-1.5 text-xs font-mono text-slate-400 hover:text-cyan-400 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Sessions
        </Link>
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-400 font-mono">Session State:</span>
          <span className={`px-2.5 py-0.5 rounded text-[11px] font-mono font-bold ${
            session.is_closed ? 'bg-slate-800 text-slate-400' : 'bg-emerald-950/80 text-emerald-400 border border-emerald-700'
          }`}>
            {session.is_closed ? 'CLOSED' : 'ACTIVE'}
          </span>
        </div>
      </div>

      {/* Hero Header Card */}
      <div className="bg-[#111726] border border-[#1f293d] rounded-lg p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-cyan-950/40 border border-cyan-800/60 rounded text-cyan-400">
              <Radio className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold font-mono text-slate-100">
                  Session: <span className="text-cyan-400">{session.session_id}</span>
                </h1>
              </div>
              <p className="text-xs text-slate-400 font-mono mt-0.5">
                Source IP: <Link to={`/attackers/${session.source_ip}`} className="text-indigo-400 hover:underline font-bold">{session.source_ip || '127.0.0.1'}</Link>
                {session.username && <span> &bull; User: <b className="text-slate-300">{session.username}</b></span>}
                <span> &bull; Protocol: <b className="text-slate-300 uppercase">{session.protocol || 'SSH'}</b></span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4 bg-[#0d121d] border border-[#1f293d] rounded-lg p-3">
            <div>
              <div className="text-[10px] uppercase font-mono text-slate-400">Deterministic Threat Risk</div>
              <RiskIndicator score={session.risk_score} size="lg" />
            </div>
            <div className="border-l border-[#1f293d] pl-4">
              <div className="text-[10px] uppercase font-mono text-slate-400 mb-1">Threat Tier</div>
              <SeverityBadge severity={session.severity} />
            </div>
          </div>
        </div>

        {/* Quick Metrics Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6 pt-6 border-t border-[#1f293d] text-xs font-mono">
          <div>
            <span className="text-slate-500 block text-[11px]">Duration</span>
            <span className="text-slate-200 font-semibold">{session.duration ? `${session.duration.toFixed(1)}s` : '0.0s'}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[11px]">Total Events</span>
            <span className="text-slate-200 font-semibold">{session.total_events}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[11px]">Commands Executed</span>
            <span className="text-cyan-400 font-semibold">{session.command_count} ({session.unique_command_count} unique)</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[11px]">Login Attempts</span>
            <span className="text-amber-400 font-semibold">{session.login_attempt_count}</span>
          </div>
        </div>
      </div>

      {/* FEATURE 2: AI Session Analyst Action Banner */}
      <div className="bg-gradient-to-r from-purple-950/40 via-[#111726] to-cyan-950/40 border border-purple-800/50 rounded-lg p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="p-2 bg-purple-900/60 rounded text-purple-300 flex-shrink-0">
              <Brain className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-purple-200 flex items-center gap-2">
                Google Gemini AI Session Analyst
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-purple-900/80 text-purple-300 border border-purple-700">
                  ASSISTANT
                </span>
              </h3>
              <p className="text-xs text-slate-300 font-sans mt-0.5">
                Generate a structured intelligence assessment of adversary objectives, behavioral patterns, and recommended defensive actions.
              </p>
            </div>
          </div>
          <button
            onClick={handleRunAiAnalysis}
            disabled={isAnalyzing || !aiEnabled}
            title={aiEnabled ? 'Generate a Gemini session report' : 'Gemini AI is unavailable: configure GEMINI_API_KEY'}
            className="inline-flex items-center justify-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-slate-100 rounded text-xs font-mono font-bold transition-all shadow-lg flex-shrink-0"
          >
            {isAnalyzing ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Analyzing Telemetry...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                {aiEnabled
                  ? (aiReport ? 'Re-Analyze Session' : 'Analyze Session with AI')
                  : 'AI Unavailable'}
              </>
            )}
          </button>
        </div>

        {/* AI Report Card */}
        {aiReport && (
          <div className="mt-5 pt-5 border-t border-purple-900/50 space-y-4 text-xs font-mono">
            <div className="flex items-center justify-between">
              <span className="text-purple-300 font-bold uppercase tracking-wider text-[11px]">
                Adversary Assessment Report
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] bg-slate-900 border border-purple-700 text-purple-300">
                Engine: {aiReport.source}
              </span>
            </div>

            <div className="bg-[#0d121d] border border-purple-900/40 rounded p-3.5 space-y-1.5">
              <span className="text-[11px] font-bold text-slate-400 uppercase">Deduced Objective:</span>
              <p className="text-slate-100 font-sans font-medium text-xs">{aiReport.objective}</p>
            </div>

            <div className="bg-[#0d121d] border border-[#1f293d] rounded p-3.5 space-y-1.5">
              <span className="text-[11px] font-bold text-slate-400 uppercase">Session Summary:</span>
              <p className="text-slate-200 font-sans leading-relaxed">{aiReport.summary}</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-[#0d121d] border border-[#1f293d] rounded p-3.5 space-y-2">
                <span className="text-[11px] font-bold text-slate-400 uppercase block">
                  Threat Actor Interpretation:
                </span>
                <p className="text-slate-200 font-sans leading-relaxed">{aiReport.threat_interpretation}</p>
              </div>

              <div className="bg-[#0d121d] border border-emerald-900/40 rounded p-3.5 space-y-2">
                <span className="text-[11px] font-bold text-emerald-400 uppercase flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Recommended Defensive Response:
                </span>
                <p className="text-slate-200 font-sans leading-relaxed">{aiReport.recommended_action}</p>
              </div>
            </div>

            {aiReport.key_evidence && aiReport.key_evidence.length > 0 && (
              <div className="bg-[#0d121d] border border-amber-900/40 rounded p-3.5 space-y-2">
                <span className="text-[11px] font-bold text-amber-400 uppercase">Key Evidence:</span>
                <ul className="space-y-1.5 font-sans text-slate-300">
                  {aiReport.key_evidence.map((evidence, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-amber-400 font-mono font-bold">{idx + 1}.</span>
                      <span>{evidence}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {aiReport.attack_progression && aiReport.attack_progression.length > 0 && (
              <div className="bg-[#0d121d] border border-[#1f293d] rounded p-3.5 space-y-2">
                <span className="text-[11px] font-bold text-slate-400 uppercase">Attack Progression Breakdown:</span>
                <ul className="space-y-1.5 font-sans text-slate-300">
                  {aiReport.attack_progression.map((step, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-cyan-400 font-mono font-bold">{idx + 1}.</span>
                      <span>{step}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {analysisError && (
          <div className="mt-4 p-3 bg-rose-950/50 border border-rose-800 text-rose-300 text-xs font-mono rounded">
            Error generating report: {analysisError}
          </div>
        )}
      </div>

      {/* FEATURE 3: MITRE ATT&CK Mapping & Trajectory */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* MITRE ATT&CK Techniques Card */}
        <div className="bg-[#111726] border border-[#1f293d] rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <Shield className="w-4 h-4 text-cyan-400" />
              Detected MITRE ATT&CK Techniques
            </h2>
            <span className="text-xs font-mono text-cyan-400">{mitreTechniques.length} mapped</span>
          </div>

          {mitreTechniques.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {mitreTechniques.map((tech) => (
                <MitreBadge key={tech.technique_id} technique={tech} />
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-500 font-mono">No specific ATT&CK techniques classified for this session.</p>
          )}
        </div>

        {/* Multi-Stage Attack Progression */}
        <div className="bg-[#111726] border border-[#1f293d] rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <Layers className="w-4 h-4 text-purple-400" />
              Multi-Stage Attack Trajectory
            </h2>
            <IntentBadge intent={session.dominant_intent} />
          </div>

          <div>
            <div className="text-[11px] font-mono text-slate-400 mb-2">Intent Flow:</div>
            <div className="flex items-center gap-1.5 flex-wrap">
              {session.intent_sequence && session.intent_sequence.length > 0 ? (
                session.intent_sequence.map((intName, idx) => (
                  <React.Fragment key={idx}>
                    <span className="bg-[#0d121d] border border-[#1f293d] px-2 py-1 rounded text-[11px] font-mono text-cyan-300">
                      {intName}
                    </span>
                    {idx < session.intent_sequence.length - 1 && (
                      <ChevronRight className="w-3.5 h-3.5 text-slate-600" />
                    )}
                  </React.Fragment>
                ))
              ) : (
                <span className="text-xs text-slate-500 font-mono">No sequence recorded</span>
              )}
            </div>
          </div>

          <div className="pt-3 border-t border-[#1f293d]">
            <div className="text-[11px] font-mono text-slate-400 mb-2">Furthest MITRE Stage Reached:</div>
            <span className="bg-indigo-950/40 border border-indigo-800/60 px-3 py-1.5 rounded text-xs font-mono font-semibold text-indigo-300">
              {session.current_attack_stage}
            </span>
          </div>
        </div>
      </div>

      {/* FEATURE 5: Enhanced Attack Timeline & Command Log */}
      <div className="bg-[#111726] border border-[#1f293d] rounded-lg p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <Terminal className="w-4 h-4 text-emerald-400" />
              Chronological Attack Timeline & Telemetry Log
            </h2>
            <p className="text-xs text-slate-400 font-mono">Sequential honeypot interactions and threat assessments</p>
          </div>
          <span className="text-xs font-mono text-slate-400">{events.length} events</span>
        </div>

        <div className="space-y-3">
          {events.map((ev, idx) => (
            <div
              key={ev.event_id || idx}
              className="bg-[#0d121d] border border-[#1f293d] rounded-md p-3.5 space-y-2 text-xs"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-slate-500 font-mono font-bold">#{idx + 1}</span>
                  <span className="font-mono text-slate-300">
                    {ev.command ? (
                      <code className="bg-[#161f33] text-cyan-300 px-2.5 py-0.5 rounded font-mono font-bold">
                        {ev.command}
                      </code>
                    ) : (
                      <span className="text-slate-400 font-mono">{ev.event_type}</span>
                    )}
                  </span>
                  <IntentBadge intent={ev.intent} />
                  <SeverityBadge severity={ev.severity} />
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-400">
                    Stage: {ev.attack_stage || 'UNKNOWN'}
                  </span>
                </div>
                <div className="flex items-center gap-3 font-mono text-[11px] text-slate-500">
                  <RiskIndicator score={ev.risk_score} size="sm" />
                  <span>{new Date(ev.timestamp).toLocaleTimeString()}</span>
                </div>
              </div>

              {/* AI Reasoning or Rule Evidence */}
              {ev.ai_reason && (
                <div className="bg-purple-950/20 border border-purple-900/40 rounded p-2.5 text-[11px] text-purple-200 font-mono">
                  <span className="text-purple-400 font-bold block mb-0.5">Gemini AI Analysis:</span>
                  {ev.ai_reason}
                </div>
              )}

              {ev.rule_evidence && ev.rule_evidence.length > 0 && !ev.ai_reason && (
                <div className="text-[11px] text-slate-400 font-mono">
                  <span className="text-slate-500">Rule Match:</span> {ev.rule_evidence[0]}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
