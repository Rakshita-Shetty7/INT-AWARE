import React from 'react';
import { Link } from 'react-router-dom';
import { Settings, Shield, Lock, ArrowRight } from 'lucide-react';
import { CodeBlock } from '../../components/docs/CodeBlock';
import { Callout } from '../../components/docs/Callout';

export const EnvVarsPage: React.FC = () => {
  return (
    <div className="space-y-8">
      <div>
        <div className="text-xs font-mono font-bold uppercase tracking-wider text-amber-400 mb-1">
          Configuration Reference
        </div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">
          Environment Variables Reference
        </h1>
        <p className="text-slate-400 text-sm leading-relaxed mt-2">
          Comprehensive reference of all application configuration parameters loaded via <code>python-dotenv</code> from the root <code>.env</code> file.
        </p>
      </div>

      <Callout type="warning" title="Secret Management">
        Never commit your <code>.env</code> file containing real API keys or sensitive credentials to version control. The repository's <code>.gitignore</code> intentionally excludes <code>.env</code>.
      </Callout>

      <div className="space-y-4">
        <h2 className="text-lg font-bold text-white border-b border-slate-800 pb-2">
          Environment Variable Reference Table
        </h2>

        <div className="overflow-x-auto rounded-xl border border-slate-800 bg-[#090e1c]">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-[#0c1324] text-slate-300 font-mono">
                <th className="p-3">Variable Name</th>
                <th className="p-3">Default (Docker / Local)</th>
                <th className="p-3">Type</th>
                <th className="p-3">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80 font-mono text-slate-300">
              <tr>
                <td className="p-3 text-cyan-400 font-bold">MONGODB_URI</td>
                <td className="p-3 text-slate-400">mongodb://localhost:27017 (Local)<br />mongodb://mongo:27017 (Docker)</td>
                <td className="p-3 text-indigo-400">string</td>
                <td className="p-3 font-sans text-slate-300">Connection string for the MongoDB instance.</td>
              </tr>
              <tr>
                <td className="p-3 text-cyan-400 font-bold">DATABASE_NAME</td>
                <td className="p-3 text-slate-400">intent_deception_db</td>
                <td className="p-3 text-indigo-400">string</td>
                <td className="p-3 font-sans text-slate-300">MongoDB database name for events, sessions, and alerts.</td>
              </tr>
              <tr>
                <td className="p-3 text-cyan-400 font-bold">COWRIE_LOG_PATH</td>
                <td className="p-3 text-slate-400">./honeypot/var/log/cowrie/cowrie.json</td>
                <td className="p-3 text-indigo-400">path</td>
                <td className="p-3 font-sans text-slate-300">Location of the JSON log emitted by Cowrie. Mounted read-only in Docker.</td>
              </tr>
              <tr>
                <td className="p-3 text-cyan-400 font-bold">ALERT_RISK_THRESHOLD</td>
                <td className="p-3 text-slate-400">75</td>
                <td className="p-3 text-indigo-400">integer</td>
                <td className="p-3 font-sans text-slate-300">Session cumulative risk score floor (0–100) required to trigger a CRITICAL alert.</td>
              </tr>
              <tr>
                <td className="p-3 text-cyan-400 font-bold">RULE_ENGINE_ENABLED</td>
                <td className="p-3 text-slate-400">true</td>
                <td className="p-3 text-indigo-400">boolean</td>
                <td className="p-3 font-sans text-slate-300">Enables deterministic regex rules alongside the ML classification pipeline.</td>
              </tr>
              <tr>
                <td className="p-3 text-cyan-400 font-bold">GEMINI_API_KEY</td>
                <td className="p-3 text-slate-400">"" (empty)</td>
                <td className="p-3 text-indigo-400">string</td>
                <td className="p-3 font-sans text-slate-300">Optional Google Gemini API key for semantic intent fallback and Caronte reports.</td>
              </tr>
              <tr>
                <td className="p-3 text-cyan-400 font-bold">GEMINI_MODEL</td>
                <td className="p-3 text-slate-400">gemini-2.5-flash</td>
                <td className="p-3 text-indigo-400">string</td>
                <td className="p-3 font-sans text-slate-300">Target Gemini model identifier.</td>
              </tr>
              <tr>
                <td className="p-3 text-cyan-400 font-bold">GEMINI_TIMEOUT</td>
                <td className="p-3 text-slate-400">5.0</td>
                <td className="p-3 text-indigo-400">float</td>
                <td className="p-3 font-sans text-slate-300">Maximum seconds to await Gemini API response before falling back to ML/rules.</td>
              </tr>
              <tr>
                <td className="p-3 text-cyan-400 font-bold">GEMINI_ENABLED</td>
                <td className="p-3 text-slate-400">true</td>
                <td className="p-3 text-indigo-400">boolean</td>
                <td className="p-3 font-sans text-slate-300">Toggles the AI copilot and semantic intent assistant.</td>
              </tr>
              <tr>
                <td className="p-3 text-cyan-400 font-bold">SESSION_CACHE_MAX</td>
                <td className="p-3 text-slate-400">5000</td>
                <td className="p-3 text-indigo-400">integer</td>
                <td className="p-3 font-sans text-slate-300">Maximum active sessions kept in process memory to prevent memory leaks.</td>
              </tr>
              <tr>
                <td className="p-3 text-cyan-400 font-bold">PROCESSED_ID_CACHE_MAX</td>
                <td className="p-3 text-slate-400">100000</td>
                <td className="p-3 text-indigo-400">integer</td>
                <td className="p-3 font-sans text-slate-300">Maximum event MD5 hashes stored to deduplicate replay streams.</td>
              </tr>
              <tr>
                <td className="p-3 text-cyan-400 font-bold">CORS_ORIGINS</td>
                <td className="p-3 text-slate-400">http://localhost:5173,http://127.0.0.1:5173</td>
                <td className="p-3 text-indigo-400">string</td>
                <td className="p-3 font-sans text-slate-300">Comma-separated allowed web origins for cross-origin browser requests.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div className="space-y-4">
        <h2 className="text-lg font-bold text-white border-b border-slate-800 pb-2">
          Sample .env Configuration File
        </h2>
        <CodeBlock
          code={`# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=intent_deception_db

# Google Gemini API Configuration (Optional)
GEMINI_API_KEY=AIzaSyD...your_key_here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_TIMEOUT=5.0
GEMINI_ENABLED=true

# Rule Engine Configuration
RULE_ENGINE_ENABLED=true

# Alert Risk Threshold (0-100)
ALERT_RISK_THRESHOLD=75

# Cowrie Honeypot Log Path
COWRIE_LOG_PATH=./honeypot/var/log/cowrie/cowrie.json

# Backend API Configuration
API_HOST=0.0.0.0
API_PORT=8000`}
          language="env"
          title=".env File Contents"
        />
      </div>

      <div className="pt-4 border-t border-slate-800 flex justify-between items-center text-xs">
        <Link to="/docs/installation/manual" className="text-slate-400 hover:text-white">
          ← Manual Installation Guide
        </Link>
        <Link to="/docs/configuration/docker-services" className="text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1">
          <span>Docker Services Topology</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
};
