import React from 'react';
import { Link } from 'react-router-dom';
import { RefreshCw, AlertOctagon, CheckCircle2, ArrowRight, ShieldAlert } from 'lucide-react';
import { CodeBlock } from '../../components/docs/CodeBlock';
import { Callout } from '../../components/docs/Callout';

export const MaintenancePage: React.FC = () => {
  return (
    <div className="space-y-8">
      <div>
        <div className="text-xs font-mono font-bold uppercase tracking-wider text-emerald-400 mb-1">
          Operational Lifecycle
        </div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">
          Stopping, Backups & Maintenance Guide
        </h1>
        <p className="text-slate-400 text-sm leading-relaxed mt-2">
          Safe operational procedures for shutting down, restarting, reading container logs, updating source code, and data retention safety.
        </p>
      </div>

      <div className="space-y-6">
        {/* Section 1: Stopping safely */}
        <div>
          <h2 className="text-lg font-bold text-white border-b border-slate-800 pb-2">
            1. Stopping the Application Safely (Preserving All Data)
          </h2>
          <p className="text-xs text-slate-300 leading-relaxed mt-2">
            To stop all INT-AWARE services without losing any recorded sessions, events, or alerts:
          </p>
          <CodeBlock
            code="docker compose down"
            language="bash"
            title="Safe Shutdown"
          />
          <p className="text-xs text-slate-400">
            This halts all containers but retains the <code>mongo-data</code> and <code>cowrie-logs</code> volumes intact on your machine.
          </p>
        </div>

        {/* Section 2: Restarting */}
        <div>
          <h2 className="text-lg font-bold text-white border-b border-slate-800 pb-2">
            2. Restarting or Updating Services
          </h2>
          <p className="text-xs text-slate-300 leading-relaxed mt-2">
            When you modify python backend code or pull git updates, rebuild the containers:
          </p>
          <CodeBlock
            code="docker compose up -d --build"
            language="bash"
            title="Rebuild & Start"
          />
          <p className="text-xs text-slate-400">
            To restart a single microservice without touching others (for example, after changing an API key in <code>.env</code>):
          </p>
          <CodeBlock
            code={`docker compose restart api
# Or restart frontend dashboard:
docker compose restart dashboard`}
            language="bash"
            title="Selective Restart"
          />
        </div>

        {/* Section 3: Inspecting Logs */}
        <div>
          <h2 className="text-lg font-bold text-white border-b border-slate-800 pb-2">
            3. Inspecting Live Service Logs
          </h2>
          <p className="text-xs text-slate-300 leading-relaxed mt-2">
            Tail logs from all services or a specific container:
          </p>
          <CodeBlock
            code={`# Follow all container logs:
docker compose logs -f

# Follow only the FastAPI pipeline:
docker compose logs -f api

# Follow isolated Cowrie honeypot events:
docker compose logs -f cowrie`}
            language="bash"
            title="Stream Container Logs"
          />
        </div>

        {/* Section 4: Destructive Cleanup */}
        <div>
          <h2 className="text-lg font-bold text-white border-b border-slate-800 pb-2 flex items-center gap-2">
            <AlertOctagon className="w-5 h-5 text-rose-500" />
            4. Destructive Reset (Wiping Stored Telemetry)
          </h2>
          <Callout type="caution" title="Permanent Data Loss Warning">
            The command below deletes Docker volumes (<code>mongo-data</code> and <code>cowrie-logs</code>). All captured attacker sessions, historical alerts, and telemetry records will be <strong>permanently deleted</strong>! Only run this if you intend to start from a completely empty database.
          </Callout>
          <CodeBlock
            code={`# CAUTION: Wipes all captured sessions and restarts with clean empty database:
docker compose down -v
docker compose up -d --build`}
            language="bash"
            title="Destructive Volume Wipe"
          />
        </div>
      </div>

      <div className="pt-4 border-t border-slate-800 flex justify-between items-center text-xs">
        <Link to="/docs/troubleshooting" className="text-slate-400 hover:text-white">
          ← Troubleshooting & FAQ
        </Link>
        <Link to="/docs/contributing" className="text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1">
          <span>Contributing & Developer Guide</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
};
