import React, { useState } from 'react';
import {
  BookOpen,
  Terminal,
  ShieldAlert,
  Server,
  Layers,
  Code2,
  Cpu,
  FileCode,
  Copy,
  Check,
  Search,
  ExternalLink,
  ChevronRight,
  ShieldCheck,
  Zap,
  Globe,
  Database,
  Lock,
} from 'lucide-react';

const DOC_SECTIONS = [
  {
    id: 'overview',
    title: 'Platform Overview',
    icon: Globe,
    items: [
      { id: 'intro', title: 'Introduction & Philosophy' },
      { id: 'architecture', title: 'System Architecture' },
      { id: 'zero-host', title: 'Zero Host Execution Safety' },
    ],
  },
  {
    id: 'decoys',
    title: 'Decoys & Runtimes',
    icon: Server,
    items: [
      { id: 'supported-protocols', title: 'Supported Protocols' },
      { id: 'yaml-syntax', title: 'Low-Code YAML Decoys' },
      { id: 'adaptive-deception', title: 'Adaptive Deception & Tar-Pits' },
    ],
  },
  {
    id: 'honeytokens',
    title: 'Honeytokens & Canaries',
    icon: Lock,
    items: [
      { id: 'token-types', title: 'Canary Credential Types' },
      { id: 'tripwire-monitoring', title: 'Tripwires & Alert Routing' },
    ],
  },
  {
    id: 'ai-analyst',
    title: 'Attacker Profiling & AI',
    icon: Cpu,
    items: [
      { id: 'intent-classifier', title: '10-Class Intent Classification' },
      { id: 'markov-transitions', title: 'Markov Attack Transitions' },
      { id: 'caronte-analyst', title: 'Caronte AI Threat Analyst' },
    ],
  },
  {
    id: 'research-labs',
    title: 'Research Laboratories',
    icon: ShieldCheck,
    items: [
      { id: 'financial-lab', title: 'Financial Services Security' },
      { id: 'ai-security-lab', title: 'AI Services & Agent Security' },
      { id: 'industrial-swat', title: 'Industrial ICS Lab (SWaT)' },
      { id: 'vuln-cve-lab', title: 'Vulnerability Verification' },
      { id: 'model-drift', title: 'Model Registry & Drift (PSI)' },
    ],
  },
  {
    id: 'api-reference',
    title: 'Deployment & REST API',
    icon: Code2,
    items: [
      { id: 'docker-deployment', title: 'Docker Compose Deployment' },
      { id: 'rest-endpoints', title: 'REST API Specification' },
    ],
  },
];

export default function DocumentationPage() {
  const [activeItem, setActiveItem] = useState('intro');
  const [copiedCode, setCopiedCode] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedCode(id);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  return (
    <div className="flex -mx-6 -my-6 min-h-[calc(100vh-4rem)]">
      {/* Documentation Sidebar */}
      <aside className="w-72 bg-[#0c101a] border-r border-[#1f293d] p-5 flex-shrink-0 overflow-y-auto">
        <div className="flex items-center gap-2.5 pb-4 border-b border-[#1f293d] mb-4">
          <BookOpen className="w-5 h-5 text-cyan-400" />
          <div>
            <h2 className="text-sm font-bold text-slate-100">Docs Portal</h2>
            <p className="text-[10px] text-slate-400 font-mono">Reference & Architecture Guide</p>
          </div>
        </div>

        {/* Search */}
        <div className="relative mb-5">
          <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search documentation..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[#131b2e] border border-[#1f293d] rounded-md pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono"
          />
        </div>

        {/* Navigation Categories */}
        <nav className="space-y-5">
          {DOC_SECTIONS.map((section) => {
            const Icon = section.icon;
            const filteredItems = section.items.filter((item) =>
              item.title.toLowerCase().includes(searchQuery.toLowerCase())
            );
            if (searchQuery && filteredItems.length === 0) return null;

            return (
              <div key={section.id}>
                <div className="flex items-center gap-2 px-2 py-1 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  <Icon className="w-3.5 h-3.5 text-cyan-400/80" />
                  <span>{section.title}</span>
                </div>
                <div className="mt-1 space-y-0.5">
                  {(searchQuery ? filteredItems : section.items).map((item) => (
                    <button
                      key={item.id}
                      onClick={() => setActiveItem(item.id)}
                      className={`w-full text-left px-3 py-1.5 rounded text-xs transition-colors flex items-center justify-between ${
                        activeItem === item.id
                          ? 'bg-cyan-950/50 text-cyan-400 font-semibold border-l-2 border-cyan-400'
                          : 'text-slate-400 hover:text-slate-200 hover:bg-[#131b2e]'
                      }`}
                    >
                      <span>{item.title}</span>
                      {activeItem === item.id && <ChevronRight className="w-3 h-3 text-cyan-400" />}
                    </button>
                  ))}
                </div>
              </div>
            );
          })}
        </nav>
      </aside>

      {/* Main Documentation Viewer */}
      <main className="flex-1 p-8 overflow-y-auto max-w-5xl">
        {activeItem === 'intro' && (
          <div className="space-y-6">
            <div>
              <span className="text-xs font-mono text-cyan-400 uppercase tracking-wider">Platform Overview</span>
              <h1 className="text-3xl font-extrabold text-slate-100 mt-1">
                Intent-Aware Cyber Deception & Real-Time Attacker Profiling
              </h1>
              <p className="text-sm text-slate-300 mt-2 leading-relaxed">
                An enterprise-grade cyber deception platform modeled after advanced low-interaction AI honeypots like
                <span className="text-cyan-400 font-mono"> Beelzebub</span>. Designed from the ground up on the principle of
                <span className="text-emerald-400 font-semibold"> assumed breach</span>, turning network perimeters into
                active intelligence-gathering minefields while maintaining mathematically provable host isolation.
              </p>
            </div>

            <div className="p-4 bg-cyan-950/20 border border-cyan-800/40 rounded-lg">
              <h3 className="text-xs font-semibold text-cyan-300 uppercase tracking-wider flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-cyan-400" />
                The Assumed Breach Paradigm
              </h3>
              <p className="text-xs text-slate-300 mt-1.5 leading-relaxed">
                Traditional defense models assume perimeters remain unbroken until a catastrophic breach occurs.
                Our Intent-Aware Deception System assumes that adversaries are already scanning, probing, or inside the network.
                By populating the infrastructure with alluring low-interaction decoy services (SSH, HTTP, Redis, IoT Telnet, MCP AI Agents)
                and high-fidelity canary credentials, any adversarial contact yields instant, zero-false-positive telemetry.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-[#111726] border border-[#1f293d] rounded-lg">
                <Terminal className="w-5 h-5 text-cyan-400 mb-2" />
                <h4 className="text-sm font-semibold text-slate-200">10-Class Intent AI</h4>
                <p className="text-xs text-slate-400 mt-1">
                  Calibrated LinearSVC classifier categorizing attacker commands in real-time across MITRE-aligned intent stages.
                </p>
              </div>
              <div className="p-4 bg-[#111726] border border-[#1f293d] rounded-lg">
                <Server className="w-5 h-5 text-emerald-400 mb-2" />
                <h4 className="text-sm font-semibold text-slate-200">Low-Code Decoy Fleet</h4>
                <p className="text-xs text-slate-400 mt-1">
                  Declarative YAML runtime simulating services, tar-pit delays (200-800ms), and custom virtual filesystems.
                </p>
              </div>
              <div className="p-4 bg-[#111726] border border-[#1f293d] rounded-lg">
                <Cpu className="w-5 h-5 text-amber-400 mb-2" />
                <h4 className="text-sm font-semibold text-slate-200">Caronte AI Analyst</h4>
                <p className="text-xs text-slate-400 mt-1">
                  Automated threat investigation engine generating MITRE ATT&CK mappings, IOC extractions, and forensic dossiers.
                </p>
              </div>
            </div>
          </div>
        )}

        {activeItem === 'architecture' && (
          <div className="space-y-6">
            <div>
              <span className="text-xs font-mono text-cyan-400 uppercase tracking-wider">Architecture</span>
              <h1 className="text-2xl font-bold text-slate-100 mt-1">System Architecture & Data Flow</h1>
              <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                The platform bridges high-fidelity honeypot event collection, sequence-level intent inference, and real-time deception adaptation.
              </p>
            </div>

            <div className="p-5 bg-[#111726] border border-[#1f293d] rounded-lg font-mono text-xs text-slate-300 overflow-x-auto space-y-2">
              <div className="text-cyan-400 font-bold mb-3">// End-to-End Pipeline Telemetry Flow</div>
              <div>[ Attacker Probe ] --(SSH/HTTP/TCP/MCP)--&gt; [ Isolated Decoy Containers (Cowrie/Beelzebub) ]</div>
              <div className="pl-6 text-slate-500">| (Read-Only JSON Events Stream)</div>
              <div>[ Pipeline Telemetry Ingestion ] --&gt; [ Normalization & Session Chronology Buffer ]</div>
              <div className="pl-6 text-slate-500">|</div>
              <div>[ Calibrated LinearSVC Classifier (94.49%) ] --&gt; Classifies 10-Class Attacker Intent</div>
              <div className="pl-6 text-slate-500">|</div>
              <div>[ Markov Sequence Transition Engine ] --&gt; Projects Next Intent & Anomaly Score</div>
              <div className="pl-6 text-slate-500">|</div>
              <div>[ Adaptive Deception Engine ] --&gt; Injects Honeytokens & Tar-Pit Delays (0 Host Exec)</div>
              <div className="pl-6 text-slate-500">|</div>
              <div>[ Caronte AI Analyst ] --&gt; MITRE ATT&CK Matrix Mapping & Forensic Dossier Synthesis</div>
              <div className="pl-6 text-slate-500">|</div>
              <div>[ MongoDB & WebSockets ] --&gt; Real-Time React Dashboard (Port 5173)</div>
            </div>
          </div>
        )}

        {activeItem === 'zero-host' && (
          <div className="space-y-6">
            <div>
              <span className="text-xs font-mono text-cyan-400 uppercase tracking-wider">Safety Model</span>
              <h1 className="text-2xl font-bold text-slate-100 mt-1">Zero Host Execution Safety Guarantee</h1>
            </div>
            <div className="p-4 bg-red-950/20 border border-red-800/40 rounded-lg space-y-2">
              <div className="flex items-center gap-2 text-red-400 font-semibold text-xs">
                <ShieldAlert className="w-4 h-4" />
                STRICT SECURITY INVARIANT: NEVER PASS COMMANDS TO OS SHELL
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                Many naive honeypots inadvertently execute attacker commands or rely on unrestricted subshells, leading to host takeover.
                In this system, <strong>ZERO host execution is mathematically enforced</strong>:
              </p>
              <ul className="list-disc pl-5 text-xs text-slate-300 space-y-1">
                <li>No command ever invokes <code>subprocess.Popen</code>, <code>os.system</code>, or bash subprocesses on the host.</li>
                <li>All shell feedback is strictly produced via deterministic regular expression matching, sandboxed template generators, or low-interaction LLM prompt wrappers.</li>
                <li>Honeypot containers run unprivileged (UID 1000) inside dedicated Docker bridge networks with no host network namespaces.</li>
                <li>Logs are ingested into the backend API via read-only volume mounts (<code>:ro</code>).</li>
              </ul>
            </div>
          </div>
        )}

        {activeItem === 'supported-protocols' && (
          <div className="space-y-6">
            <div>
              <span className="text-xs font-mono text-cyan-400 uppercase tracking-wider">Decoy Runtimes</span>
              <h1 className="text-2xl font-bold text-slate-100 mt-1">Supported Decoy Protocols & Services</h1>
            </div>

            <div className="space-y-4">
              <div className="p-4 bg-[#111726] border border-[#1f293d] rounded-lg">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-cyan-400 flex items-center gap-2">
                    <Terminal className="w-4 h-4" />
                    SSH Decoy (Port 2222)
                  </h3>
                  <span className="px-2 py-0.5 text-[10px] font-mono bg-emerald-950/50 text-emerald-400 border border-emerald-800/40 rounded">
                    ACTIVE
                  </span>
                </div>
                <p className="text-xs text-slate-300 mt-2">
                  Emulates OpenSSH 8.9p1 Ubuntu-3ubuntu0.6. Traps brute-force authentication, interactive terminal navigation,
                  file searches, and shell execution. Returns synthetic Linux Debian virtual filesystems.
                </p>
              </div>

              <div className="p-4 bg-[#111726] border border-[#1f293d] rounded-lg">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-emerald-400 flex items-center gap-2">
                    <Globe className="w-4 h-4" />
                    HTTP Microservices & Actuator Decoy (Port 8080)
                  </h3>
                  <span className="px-2 py-0.5 text-[10px] font-mono bg-emerald-950/50 text-emerald-400 border border-emerald-800/40 rounded">
                    ACTIVE
                  </span>
                </div>
                <p className="text-xs text-slate-300 mt-2">
                  Simulates cloud Spring Boot / FastAPI backend exposing alluring endpoints (<code>/actuator/env</code>, <code>/swagger-ui</code>,
                  and <code>/api/v1/auth</code>) loaded with canary JWT tokens and masked credentials.
                </p>
              </div>

              <div className="p-4 bg-[#111726] border border-[#1f293d] rounded-lg">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-amber-400 flex items-center gap-2">
                    <Database className="w-4 h-4" />
                    TCP Database Decoy - Redis (Port 6379)
                  </h3>
                  <span className="px-2 py-0.5 text-[10px] font-mono bg-emerald-950/50 text-emerald-400 border border-emerald-800/40 rounded">
                    ACTIVE
                  </span>
                </div>
                <p className="text-xs text-slate-300 mt-2">
                  Speaks native RESP protocol. Traps unauthenticated discovery commands (<code>INFO</code>, <code>CONFIG GET</code>, <code>KEYS *</code>)
                  and serves canary session tokens.
                </p>
              </div>

              <div className="p-4 bg-[#111726] border border-[#1f293d] rounded-lg">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-purple-400 flex items-center gap-2">
                    <Cpu className="w-4 h-4" />
                    Model Context Protocol (MCP) AI Decoy (Port 9090)
                  </h3>
                  <span className="px-2 py-0.5 text-[10px] font-mono bg-emerald-950/50 text-emerald-400 border border-emerald-800/40 rounded">
                    ACTIVE
                  </span>
                </div>
                <p className="text-xs text-slate-300 mt-2">
                  Specialized AI-agent decoy designed to trap LLM tool hijacking, prompt injection exploits, and unauthorized tool calls (<code>execute_bash</code>, <code>query_database</code>).
                </p>
              </div>

              <div className="p-4 bg-[#111726] border border-[#1f293d] rounded-lg">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-rose-400 flex items-center gap-2">
                    <Server className="w-4 h-4" />
                    Telnet IoT Decoy - BusyBox (Port 2323)
                  </h3>
                  <span className="px-2 py-0.5 text-[10px] font-mono bg-emerald-950/50 text-emerald-400 border border-emerald-800/40 rounded">
                    ACTIVE
                  </span>
                </div>
                <p className="text-xs text-slate-300 mt-2">
                  Simulates embedded MIPS/ARM router terminal. Traps automated Mirai botnet brute-force patterns and command injection attempts.
                </p>
              </div>
            </div>
          </div>
        )}

        {activeItem === 'yaml-syntax' && (
          <div className="space-y-6">
            <div>
              <span className="text-xs font-mono text-cyan-400 uppercase tracking-wider">Configuration Reference</span>
              <h1 className="text-2xl font-bold text-slate-100 mt-1">Low-Code YAML Decoy Specification</h1>
              <p className="text-xs text-slate-300 mt-1">
                Define and deploy high-interaction decoys with minimal declarative YAML configurations.
              </p>
            </div>

            <div className="relative bg-[#0d121d] border border-[#1f293d] rounded-lg p-4 font-mono text-xs text-slate-200 overflow-x-auto">
              <button
                onClick={() =>
                  copyToClipboard(
                    `apiVersion: "v1"
protocol: "ssh"
address: ":2222"
description: "Production Linux Bastion Decoy"
serverVersion: "SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.6"
banner: "Debian GNU/Linux 12 (bookworm) - Authorized Access Only"
commands:
  - regex: "^(whoami|id)$"
    handler: "terminal"
    output: "uid=0(root) gid=0(root) groups=0(root)"
  - regex: "^cat /etc/passwd"
    handler: "terminal"
    output: "root:x:0:0:root:/root:/bin/bash\\nadmin:x:1000:1000:Admin:/home/admin:/bin/bash"
tarpit:
  enabled: true
  delayMs: 350
honeytokens:
  - type: "SHADOW_HASH"
    path: "/etc/shadow"
    value: "$2a$12$e8pCanaryRootHashBcryptDeterministicFake2026"
  - type: "AWS_CREDENTIAL"
    path: "/root/.aws/credentials"
    value: "aws_access_key_id=AKIAIOSFODNN7EXAMPLE"`,
                    'yaml-code'
                  )
                }
                className="absolute top-3 right-3 p-1.5 bg-[#172136] hover:bg-[#1e2c47] rounded text-slate-300 transition-colors"
                title="Copy YAML"
              >
                {copiedCode === 'yaml-code' ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
              </button>
              <pre className="text-cyan-300">{`apiVersion: "v1"
protocol: "ssh"
address: ":2222"
description: "Production Linux Bastion Decoy"
serverVersion: "SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.6"
banner: "Debian GNU/Linux 12 (bookworm) - Authorized Access Only"

commands:
  - regex: "^(whoami|id)$"
    handler: "terminal"
    output: "uid=0(root) gid=0(root) groups=0(root)"
  - regex: "^cat /etc/passwd"
    handler: "terminal"
    output: "root:x:0:0:root:/root:/bin/bash\\nadmin:x:1000:1000:Admin:/home/admin:/bin/bash"

tarpit:
  enabled: true
  delayMs: 350

honeytokens:
  - type: "SHADOW_HASH"
    path: "/etc/shadow"
    value: "$2a$12$e8pCanaryRootHashBcryptDeterministicFake2026"
  - type: "AWS_CREDENTIAL"
    path: "/root/.aws/credentials"
    value: "aws_access_key_id=AKIAIOSFODNN7EXAMPLE"`}</pre>
            </div>
          </div>
        )}

        {activeItem === 'token-types' && (
          <div className="space-y-6">
            <div>
              <span className="text-xs font-mono text-cyan-400 uppercase tracking-wider">Canary Traps</span>
              <h1 className="text-2xl font-bold text-slate-100 mt-1">Canary Credential Types & Honeytokens</h1>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 bg-[#111726] border border-[#1f293d] rounded-lg">
                <span className="text-[10px] font-mono text-cyan-400 font-bold uppercase">AWS Cloud Token</span>
                <h4 className="text-sm font-semibold text-slate-100 mt-1">IAM Canary Access Keys</h4>
                <p className="text-xs text-slate-400 mt-1">
                  Synthetic AWS credentials placed in <code>~/.aws/credentials</code>. When probed against AWS STS / S3, alerts are instantly emitted.
                </p>
                <div className="mt-2 p-2 bg-[#0c101a] rounded font-mono text-[11px] text-slate-300">
                  AKIAIOSFODNN7EXAMPLE
                </div>
              </div>

              <div className="p-4 bg-[#111726] border border-[#1f293d] rounded-lg">
                <span className="text-[10px] font-mono text-emerald-400 font-bold uppercase">Linux System</span>
                <h4 className="text-sm font-semibold text-slate-100 mt-1">Bcrypt Shadow Hashes</h4>
                <p className="text-xs text-slate-400 mt-1">
                  Injects synthetic <code>/etc/shadow</code> lines. If an attacker submits this hash to a cracking rig or lateral hash-spraying tool, tripwire triggers.
                </p>
                <div className="mt-2 p-2 bg-[#0c101a] rounded font-mono text-[11px] text-slate-300">
                  $2a$12$e8pCanaryRootHashBcrypt...
                </div>
              </div>

              <div className="p-4 bg-[#111726] border border-[#1f293d] rounded-lg">
                <span className="text-[10px] font-mono text-amber-400 font-bold uppercase">Database Secrets</span>
                <h4 className="text-sm font-semibold text-slate-100 mt-1">PostgreSQL / MySQL Canary URIs</h4>
                <p className="text-xs text-slate-400 mt-1">
                  Embedded in <code>/actuator/env</code> or <code>.env</code> backup files. Connects to isolated honey-databases to log lateral movement attempts.
                </p>
                <div className="mt-2 p-2 bg-[#0c101a] rounded font-mono text-[11px] text-slate-300">
                  postgresql://dba_canary:P@ss...
                </div>
              </div>

              <div className="p-4 bg-[#111726] border border-[#1f293d] rounded-lg">
                <span className="text-[10px] font-mono text-purple-400 font-bold uppercase">AI Vector Stores</span>
                <h4 className="text-sm font-semibold text-slate-100 mt-1">RAG Canary Documents</h4>
                <p className="text-xs text-slate-400 mt-1">
                  High-allure confidential documents injected into AI agent vector databases (Project Zeus, M&A vaults). Triggers immediate exfiltration warnings.
                </p>
                <div className="mt-2 p-2 bg-[#0c101a] rounded font-mono text-[11px] text-slate-300">
                  CANARY_RAG_TOKEN_91e4f2a1
                </div>
              </div>
            </div>
          </div>
        )}

        {activeItem === 'intent-classifier' && (
          <div className="space-y-6">
            <div>
              <span className="text-xs font-mono text-cyan-400 uppercase tracking-wider">Machine Learning</span>
              <h1 className="text-2xl font-bold text-slate-100 mt-1">10-Class Attacker Intent Classification</h1>
              <p className="text-xs text-slate-300 mt-1">
                The primary inference engine mapping observed command strings into MITRE-aligned intent categories.
              </p>
            </div>

            <div className="p-4 bg-[#111726] border border-[#1f293d] rounded-lg space-y-3">
              <h3 className="text-sm font-semibold text-slate-200">The 10 Canonical Intent Classes</h3>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-xs font-mono">
                <div className="p-2 bg-[#0d121d] rounded border border-cyan-800/40 text-cyan-400">1. Reconnaissance</div>
                <div className="p-2 bg-[#0d121d] rounded border border-blue-800/40 text-blue-400">2. Discovery</div>
                <div className="p-2 bg-[#0d121d] rounded border border-amber-800/40 text-amber-400">3. Credential Access</div>
                <div className="p-2 bg-[#0d121d] rounded border border-red-800/40 text-red-400">4. Execution</div>
                <div className="p-2 bg-[#0d121d] rounded border border-purple-800/40 text-purple-400">5. Privilege Escalation</div>
                <div className="p-2 bg-[#0d121d] rounded border border-indigo-800/40 text-indigo-400">6. Persistence</div>
                <div className="p-2 bg-[#0d121d] rounded border border-rose-800/40 text-rose-400">7. Exploitation</div>
                <div className="p-2 bg-[#0d121d] rounded border border-emerald-800/40 text-emerald-400">8. Exfiltration</div>
                <div className="p-2 bg-[#0d121d] rounded border border-slate-700 text-slate-400">9. Cleanup</div>
                <div className="p-2 bg-[#0d121d] rounded border border-slate-700 text-slate-400">10. Other</div>
              </div>
            </div>

            <div className="p-4 bg-[#111726] border border-[#1f293d] rounded-lg">
              <h4 className="text-sm font-semibold text-slate-200">Production Model Metrics (Leakage-Free Cross-Validation)</h4>
              <div className="mt-3 grid grid-cols-3 gap-3 text-center">
                <div className="p-3 bg-[#0d121d] rounded">
                  <div className="text-2xl font-bold font-mono text-cyan-400">94.49%</div>
                  <div className="text-[11px] text-slate-400 mt-1">Test Accuracy</div>
                </div>
                <div className="p-3 bg-[#0d121d] rounded">
                  <div className="text-2xl font-bold font-mono text-emerald-400">0.9229</div>
                  <div className="text-[11px] text-slate-400 mt-1">Macro F1 Score</div>
                </div>
                <div className="p-3 bg-[#0d121d] rounded">
                  <div className="text-2xl font-bold font-mono text-purple-400">0.9450</div>
                  <div className="text-[11px] text-slate-400 mt-1">Weighted F1 Score</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeItem === 'caronte-analyst' && (
          <div className="space-y-6">
            <div>
              <span className="text-xs font-mono text-cyan-400 uppercase tracking-wider">AI Investigation Engine</span>
              <h1 className="text-2xl font-bold text-slate-100 mt-1">Caronte AI Threat Analyst</h1>
              <p className="text-xs text-slate-300 mt-1">
                Autonomous threat investigation engine modeled after Beelzebub's flagship AI Analyst 'Caronte'.
              </p>
            </div>

            <div className="p-4 bg-[#111726] border border-[#1f293d] rounded-lg space-y-3">
              <h3 className="text-sm font-semibold text-slate-200">Autonomous Investigation Capabilities</h3>
              <ul className="list-disc pl-5 text-xs text-slate-300 space-y-2">
                <li><strong>Reconstructs Attack Paths:</strong> Groups disjoint commands into chronological attack chains and correlates multi-session attacker IPs.</li>
                <li><strong>MITRE ATT&CK Matrix Mapping:</strong> Maps observed behaviors to precise tactics and techniques (e.g., T1059.004 Unix Shell, T1082 System Discovery, T1003.008 Shadow Hashes).</li>
                <li><strong>Automated IOC Extraction:</strong> Parses raw command arguments for malicious IPs, external tool transfer URLs, and credential paths.</li>
                <li><strong>Attacker Sophistication Rating:</strong> Distinguishes automated botnet scanners from intermediate script operators and Advanced Persistent Threats (APTs).</li>
                <li><strong>Deception Containment Dossier:</strong> Calculates containment percentages and automatically recommends countermeasure policies.</li>
              </ul>
            </div>
          </div>
        )}

        {activeItem === 'docker-deployment' && (
          <div className="space-y-6">
            <div>
              <span className="text-xs font-mono text-cyan-400 uppercase tracking-wider">Operations</span>
              <h1 className="text-2xl font-bold text-slate-100 mt-1">Docker Compose Deployment Guide</h1>
            </div>

            <div className="relative bg-[#0d121d] border border-[#1f293d] rounded-lg p-4 font-mono text-xs text-slate-200 overflow-x-auto">
              <button
                onClick={() =>
                  copyToClipboard(
                    `# 1. Clone repository
git clone https://github.com/your-org/int-aware-deception.git
cd int-aware-deception

# 2. Build and launch isolated containers
docker compose up -d --build

# 3. Verify container health
docker compose ps

# 4. Open Dashboard
# Browse to: http://localhost:5173
# API Docs: http://localhost:8000/docs`,
                    'deploy-code'
                  )
                }
                className="absolute top-3 right-3 p-1.5 bg-[#172136] hover:bg-[#1e2c47] rounded text-slate-300 transition-colors"
                title="Copy Commands"
              >
                {copiedCode === 'deploy-code' ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
              </button>
              <pre className="text-cyan-300">{`# 1. Inspect repository status
git status

# 2. Build and launch isolated containers
docker compose up -d --build

# 3. Verify container health
docker compose ps

# 4. Access Platform
# Web Dashboard: http://localhost:5173
# FastAPI REST:   http://localhost:8000/api
# Swagger Docs:   http://localhost:8000/docs`}</pre>
            </div>
          </div>
        )}

        {activeItem === 'rest-endpoints' && (
          <div className="space-y-6">
            <div>
              <span className="text-xs font-mono text-cyan-400 uppercase tracking-wider">REST API</span>
              <h1 className="text-2xl font-bold text-slate-100 mt-1">REST API Endpoints Specification</h1>
            </div>

            <div className="space-y-3">
              {[
                { method: 'GET', path: '/api/health', desc: 'System health, database state, and ML model status' },
                { method: 'GET', path: '/api/deception/fleet/summary', desc: 'Summary of active Beelzebub decoys and honeytokens' },
                { method: 'GET', path: '/api/deception/decoys', desc: 'List all active SSH, HTTP, TCP, Telnet, and MCP decoys' },
                { method: 'GET', path: '/api/deception/honeytokens', desc: 'List deployed canary credentials and tripwire statuses' },
                { method: 'POST', path: '/api/deception/caronte/investigate', desc: 'Execute autonomous Caronte AI forensic investigation' },
                { method: 'POST', path: '/api/deception/simulate', desc: 'Simulate safe adaptive deception response for a command' },
                { method: 'GET', path: '/api/research/industrial/invariants', desc: 'List SWaT water treatment physical invariants' },
                { method: 'POST', path: '/api/research/industrial/adversarial-test', desc: 'Run L-infinity bounded sensor spoofing perturbation test' },
                { method: 'GET', path: '/api/research/vuln/benchmarks', desc: 'List curated CVE benchmarks (Log4Shell, regreSSHion, etc.)' },
                { method: 'POST', path: '/api/financial/transfer', desc: 'Execute wire transfer check against canary treasury accounts' },
                { method: 'POST', path: '/api/ai-security/evaluate-prompt', desc: 'Evaluate prompt injection and LLM jailbreak attempts' },
              ].map((ep, idx) => (
                <div key={idx} className="p-3 bg-[#111726] border border-[#1f293d] rounded-lg flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                        ep.method === 'GET'
                          ? 'bg-blue-950/60 text-blue-400 border border-blue-800/40'
                          : 'bg-emerald-950/60 text-emerald-400 border border-emerald-800/40'
                      }`}
                    >
                      {ep.method}
                    </span>
                    <span className="font-mono text-xs text-slate-200">{ep.path}</span>
                  </div>
                  <span className="text-xs text-slate-400">{ep.desc}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
