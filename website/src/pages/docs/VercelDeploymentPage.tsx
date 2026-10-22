import React from 'react';
import { Link } from 'react-router-dom';
import {
  Globe,
  Server,
  Database,
  Shield,
  Layers,
  Terminal,
  ArrowRight,
  AlertTriangle,
  CheckCircle2,
  Lock,
} from 'lucide-react';
import { CodeBlock } from '../../components/docs/CodeBlock';
import { Callout } from '../../components/docs/Callout';

export const VercelDeploymentPage: React.FC = () => {
  return (
    <div className="space-y-8">
      <div>
        <div className="text-xs font-mono font-bold uppercase tracking-wider text-emerald-400 mb-1">
          Production Architecture & Hosting
        </div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">
          Vercel Deployment & Architectural Boundaries
        </h1>
        <p className="text-slate-400 text-sm leading-relaxed mt-2">
          Technical specifications for deploying the public documentation website and SOC frontend on Vercel, paired with persistent container hosting for the ML pipeline, honeypot, and database.
        </p>
      </div>

      <Callout type="warning" title="Architectural Boundary Notice">
        Vercel is an edge / serverless frontend platform. The <strong>Cowrie SSH honeypot</strong> (listening on TCP port 2222), <strong>daemon log tailer</strong>, <strong>FastAPI service</strong>, and <strong>MongoDB store</strong> require persistent TCP networking, filesystem tailing, and long-lived memory state. These backend services must run on container/VM hosting (e.g., Render, Railway, AWS ECS, or a Linux VPS), while Vercel hosts the static React frontends.
      </Callout>

      {/* Topology Architecture Diagram */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-white border-b border-slate-800 pb-2">
          1. Distributed Production Topology
        </h2>
        <div className="p-4 rounded-xl bg-[#090e1c] border border-slate-800 font-mono text-xs text-slate-300 leading-relaxed">
          <div className="text-cyan-400 font-bold mb-2">Frontend Tier (Vercel Edge Network):</div>
          • Public Documentation Website (Vite + React 19 + TypeScript)<br />
          • SOC Dashboard UI (Vite + React 19 + Tailwind CSS)<br />
          • Client-side routing with SPA fallback (<code className="text-emerald-400">vercel.json</code>)<br />
          <br />
          <div className="text-indigo-400 font-bold mb-2">Backend Tier (Persistent Container Host: Railway / Render / VPS):</div>
          • FastAPI Application (<code className="text-slate-200">uvicorn backend.app.main:app</code>)<br />
          • Calibrated LinearSVC ML Model & Rule Hybrid Classifier<br />
          • WebSockets for live telemetry (<code className="text-slate-200">/ws/events</code>, <code className="text-slate-200">/ws/alerts</code>)<br />
          <br />
          <div className="text-purple-400 font-bold mb-2">Data & Honeypot Tier:</div>
          • MongoDB Atlas or Managed Replica Set (M0 free tier or dedicated cluster)<br />
          • Cowrie Honeypot Container (on dedicated VPS or cloud VM with public port 2222)
        </div>
      </div>

      {/* Preparing the Frontend for Vercel */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-white border-b border-slate-800 pb-2">
          2. Vercel Configuration Settings
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left border-collapse font-mono">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400">
                <th className="p-2.5">Configuration Property</th>
                <th className="p-2.5">Documentation Website (website/)</th>
                <th className="p-2.5">SOC Dashboard (frontend/)</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-slate-800/60 text-slate-300">
                <td className="p-2.5 text-cyan-400">Framework Preset</td>
                <td className="p-2.5">Vite</td>
                <td className="p-2.5">Vite</td>
              </tr>
              <tr className="border-b border-slate-800/60 text-slate-300">
                <td className="p-2.5 text-cyan-400">Root Directory</td>
                <td className="p-2.5"><code className="text-slate-200">website</code></td>
                <td className="p-2.5"><code className="text-slate-200">frontend</code></td>
              </tr>
              <tr className="border-b border-slate-800/60 text-slate-300">
                <td className="p-2.5 text-cyan-400">Build Command</td>
                <td className="p-2.5"><code className="text-slate-200">npm run build</code> (tsc && vite build)</td>
                <td className="p-2.5"><code className="text-slate-200">npm run build</code> (vite build)</td>
              </tr>
              <tr className="border-b border-slate-800/60 text-slate-300">
                <td className="p-2.5 text-cyan-400">Output Directory</td>
                <td className="p-2.5"><code className="text-slate-200">dist</code></td>
                <td className="p-2.5"><code className="text-slate-200">dist</code></td>
              </tr>
              <tr className="border-b border-slate-800/60 text-slate-300">
                <td className="p-2.5 text-cyan-400">Node.js Version</td>
                <td className="p-2.5">20.x or 22.x</td>
                <td className="p-2.5">20.x or 22.x</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* vercel.json Specification */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-white border-b border-slate-800 pb-2">
          3. Single-Page Application (SPA) Routing (<code className="text-cyan-400">vercel.json</code>)
        </h2>
        <p className="text-xs text-slate-300 leading-relaxed">
          To prevent HTTP 404 Not Found errors when refreshing browser routes (e.g. <code>/sessions/apt01</code> or <code>/docs/model-performance</code>), a <code>vercel.json</code> rewrite configuration file is committed at the project root:
        </p>

        <CodeBlock
          code={`{
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "X-XSS-Protection", "value": "1; mode=block" }
      ]
    }
  ]
}`}
          language="json"
          title="vercel.json (SPA Rewrites & Security Headers)"
        />
      </div>

      {/* Production Environment Variables */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-white border-b border-slate-800 pb-2">
          4. Production Environment Variables (Zero Secrets Exposed)
        </h2>
        <p className="text-xs text-slate-300 leading-relaxed">
          Configure these environment variables in your Vercel Project Dashboard (<strong>Settings → Environment Variables</strong>):
        </p>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left border-collapse font-mono">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400">
                <th className="p-2.5">Variable Name</th>
                <th className="p-2.5">Target Value / Format</th>
                <th className="p-2.5">Sensitivity</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-slate-800/60 text-slate-300">
                <td className="p-2.5 text-cyan-400">VITE_API_BASE_URL</td>
                <td className="p-2.5"><code className="text-slate-200">https://api.yourdomain.com/api</code></td>
                <td className="p-2.5 text-emerald-400">Public URL</td>
              </tr>
              <tr className="border-b border-slate-800/60 text-slate-300">
                <td className="p-2.5 text-cyan-400">VITE_WS_BASE_URL</td>
                <td className="p-2.5"><code className="text-slate-200">wss://api.yourdomain.com</code></td>
                <td className="p-2.5 text-emerald-400">Public WebSocket</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="text-xs text-slate-400">
          <em>Important:</em> Never set database credentials, honeypot passwords, or Google Gemini API keys in Vercel frontend variables. Backend secrets belong strictly in the server environment (Render / Railway / VPS).
        </p>
      </div>

      {/* Backend CORS Configuration */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-white border-b border-slate-800 pb-2">
          5. Backend CORS Configuration for Vercel Domain
        </h2>
        <p className="text-xs text-slate-300 leading-relaxed">
          In your production backend configuration (<code>.env</code> on the backend container host), add your deployed Vercel domain to the CORS whitelist:
        </p>

        <CodeBlock
          code={`# In backend host .env:
CORS_ORIGINS=["https://your-project.vercel.app", "https://your-custom-domain.com"]`}
          language="bash"
          title="Backend Production CORS Configuration"
        />
      </div>

      <div className="pt-4 border-t border-slate-800 flex justify-between items-center text-xs">
        <Link to="/docs/configuration/docker-services" className="text-slate-400 hover:text-white">
          ← Docker Compose Topology
        </Link>
        <Link to="/docs/troubleshooting" className="text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1">
          <span>Troubleshooting & FAQ</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
};