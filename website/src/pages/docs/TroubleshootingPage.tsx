import React from 'react';
import { Link } from 'react-router-dom';
import { HelpCircle, AlertTriangle, CheckCircle2, ArrowRight } from 'lucide-react';
import { CodeBlock } from '../../components/docs/CodeBlock';
import { Callout } from '../../components/docs/Callout';

export const TroubleshootingPage: React.FC = () => {
  return (
    <div className="space-y-8">
      <div>
        <div className="text-xs font-mono font-bold uppercase tracking-wider text-rose-400 mb-1">
          Support & Diagnostics
        </div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">
          Troubleshooting & Frequently Asked Questions
        </h1>
        <p className="text-slate-400 text-sm leading-relaxed mt-2">
          Diagnostic procedures, symptoms, root causes, and verified solutions for common setup, network, and container errors.
        </p>
      </div>

      <div className="space-y-6">
        {/* Issue 1 */}
        <div className="p-5 rounded-xl bg-[#090e1c] border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-rose-400 font-bold text-sm">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            <span>Dashboard displays "Unable to reach backend" or connection error</span>
          </div>
          <div className="text-xs text-slate-300 leading-relaxed">
            <strong>Symptom:</strong> The Vite dashboard loads at <code>http://127.0.0.1:5173</code>, but stat cards show error states.
          </div>
          <div className="text-xs text-slate-400 leading-relaxed">
            <strong>Root Cause:</strong> The FastAPI container requires ~10–15 seconds on initial boot to verify the MongoDB connection, load Scikit-learn models from disk, and initialize model hashes.
          </div>
          <div className="p-3 rounded-lg bg-[#060913] border border-slate-800 text-xs text-emerald-400 space-y-1">
            <strong>Solution:</strong> Check backend container status and logs:
            <CodeBlock
              code={`docker compose ps
docker compose logs -f api`}
              language="bash"
            />
            Once <code>Application startup complete</code> appears in the log, refresh the browser.
          </div>
        </div>

        {/* Issue 2 */}
        <div className="p-5 rounded-xl bg-[#090e1c] border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-rose-400 font-bold text-sm">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            <span>Port Conflict: "port is already allocated" (2222, 8000, or 5173)</span>
          </div>
          <div className="text-xs text-slate-300 leading-relaxed">
            <strong>Symptom:</strong> <code>docker compose up</code> fails with <code>Bind for 127.0.0.1:2222 failed: port is already allocated</code>.
          </div>
          <div className="text-xs text-slate-400 leading-relaxed">
            <strong>Root Cause:</strong> A previous local run, background python script, or zombie container holds the port open.
          </div>
          <div className="p-3 rounded-lg bg-[#060913] border border-slate-800 text-xs text-emerald-400 space-y-1">
            <strong>Solution:</strong> Kill the conflicting process or shut down all previous containers:
            <CodeBlock
              code={`# On Windows (PowerShell):
Get-NetTCPConnection -LocalPort 2222 | Select-Object OwningProcess

# On Linux or macOS:
sudo lsof -i :2222

# Or stop all running compose stacks:
docker compose down`}
              language="bash"
            />
          </div>
        </div>

        {/* Issue 3 */}
        <div className="p-5 rounded-xl bg-[#090e1c] border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-rose-400 font-bold text-sm">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            <span>Attack script reports: "Could not connect to Cowrie: [Errno 111] Connection refused"</span>
          </div>
          <div className="text-xs text-slate-300 leading-relaxed">
            <strong>Symptom:</strong> Running <code>scripts/demo_all_intents.py</code> fails immediately when initiating SSH handshake.
          </div>
          <div className="text-xs text-slate-400 leading-relaxed">
            <strong>Root Cause:</strong> The Cowrie container is either still initializing Twisted SSH keys or is stopped.
          </div>
          <div className="p-3 rounded-lg bg-[#060913] border border-slate-800 text-xs text-emerald-400 space-y-1">
            <strong>Solution:</strong> Verify the Cowrie container is healthy:
            <CodeBlock
              code={`docker compose logs -f cowrie
# Look for "Ready to accept SSH connections on port 2222"`}
              language="bash"
            />
          </div>
        </div>

        {/* Issue 4 */}
        <div className="p-5 rounded-xl bg-[#090e1c] border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-rose-400 font-bold text-sm">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            <span>AI Badge in Dashboard Navbar Displays "AI: OFF"</span>
          </div>
          <div className="text-xs text-slate-300 leading-relaxed">
            <strong>Symptom:</strong> The navbar top badge reads <code>AI: OFF</code> instead of amber <code>AI: ON</code>.
          </div>
          <div className="text-xs text-slate-400 leading-relaxed">
            <strong>Root Cause:</strong> <code>GEMINI_API_KEY</code> in <code>.env</code> is either empty, commented out, or contains placeholder text.
          </div>
          <div className="p-3 rounded-lg bg-[#060913] border border-slate-800 text-xs text-emerald-400 space-y-1">
            <strong>Solution:</strong>
            <ol className="list-decimal pl-4 space-y-1 mt-1 text-slate-300 font-sans">
              <li>Open <code>.env</code> and add a valid key from Google AI Studio: <code>GEMINI_API_KEY=AIzaSy...</code></li>
              <li>Ensure <code>GEMINI_ENABLED=true</code> is set.</li>
              <li>Restart the API container: <code>docker compose restart api</code></li>
            </ol>
          </div>
        </div>
      </div>

      <div className="pt-4 border-t border-slate-800 flex justify-between items-center text-xs">
        <Link to="/docs/api" className="text-slate-400 hover:text-white">
          ← API Reference
        </Link>
        <Link to="/docs/maintenance" className="text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1">
          <span>Stopping, Backups & Maintenance</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
};
