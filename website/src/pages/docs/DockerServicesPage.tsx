import React from 'react';
import { Link } from 'react-router-dom';
import { Container, Shield, Network, HardDrive, ArrowRight } from 'lucide-react';
import { CodeBlock } from '../../components/docs/CodeBlock';
import { Callout } from '../../components/docs/Callout';

export const DockerServicesPage: React.FC = () => {
  return (
    <div className="space-y-8">
      <div>
        <div className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-400 mb-1">
          Infrastructure Guide
        </div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">
          Docker Services & Container Topology
        </h1>
        <p className="text-slate-400 text-sm leading-relaxed mt-2">
          Technical inspection of <code>docker-compose.yml</code>, container isolation boundaries, internal network segments, and volume mounts.
        </p>
      </div>

      <div className="space-y-4">
        <h2 className="text-lg font-bold text-white border-b border-slate-800 pb-2">
          Microservices Overview (4 Containers)
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          {/* Service 1: Mongo */}
          <div className="p-4 rounded-xl bg-[#090e1c] border border-slate-800 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-white font-mono text-sm">1. mongo</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">Image: mongo:7</span>
            </div>
            <p className="text-slate-400">
              Official MongoDB 7 image. Persists telemetry, sessions, alerts, and model hashes to the named volume <code>mongo-data</code>.
            </p>
            <div className="p-2 rounded bg-[#060913] text-[11px] font-mono text-emerald-400">
              Security: Intentionally NOT published to the host machine. Accessible only within the internal Docker network.
            </div>
          </div>

          {/* Service 2: Cowrie */}
          <div className="p-4 rounded-xl bg-[#090e1c] border border-slate-800 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-white font-mono text-sm">2. cowrie</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">Port: 127.0.0.1:2222</span>
            </div>
            <p className="text-slate-400">
              Isolated Cowrie SSH honeypot. Emulates a Debian Linux shell with realistic command utilities (ps, uname, wget, cat, etc.).
            </p>
            <div className="p-2 rounded bg-[#060913] text-[11px] font-mono text-cyan-400">
              Security: Zero host execution. Writes audit logs to <code>cowrie-logs</code> volume. Binds strictly to 127.0.0.1.
            </div>
          </div>

          {/* Service 3: API */}
          <div className="p-4 rounded-xl bg-[#090e1c] border border-slate-800 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-white font-mono text-sm">3. api</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">Port: 127.0.0.1:8000</span>
            </div>
            <p className="text-slate-400">
              FastAPI backend running Python 3.12. Includes the background ingestion pipeline, Scikit-learn ML model, and WebSocket server.
            </p>
            <div className="p-2 rounded bg-[#060913] text-[11px] font-mono text-indigo-400">
              Mount: <code>cowrie-logs:/cowrie:ro</code> (Strictly Read-Only mount to ensure data integrity).
            </div>
          </div>

          {/* Service 4: Dashboard */}
          <div className="p-4 rounded-xl bg-[#090e1c] border border-slate-800 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-white font-mono text-sm">4. dashboard</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">Port: 127.0.0.1:5173</span>
            </div>
            <p className="text-slate-400">
              Production Nginx container serving compiled React 19 + Vite SOC Command Center assets.
            </p>
            <div className="p-2 rounded bg-[#060913] text-[11px] font-mono text-amber-400">
              Proxy: Connects to API over internal network for fast static asset caching and WebSocket pass-through.
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <h2 className="text-lg font-bold text-white border-b border-slate-800 pb-2">
          The docker-compose.yml Manifest
        </h2>
        <CodeBlock
          code={`services:
  mongo:
    image: mongo:7
    restart: unless-stopped
    volumes:
      - mongo-data:/data/db

  cowrie:
    image: cowrie/cowrie:latest
    restart: unless-stopped
    ports:
      - "127.0.0.1:2222:2222"     # SSH honeypot (localhost only)
    volumes:
      - cowrie-logs:/cowrie/cowrie-git/var/log/cowrie
      - ./honeypot/etc/userdb.txt:/cowrie/cowrie-git/etc/userdb.txt:ro

  api:
    build:
      context: .
      dockerfile: backend/Dockerfile
    restart: unless-stopped
    env_file: .env
    environment:
      MONGODB_URI: mongodb://mongo:27017
      DATABASE_NAME: intent_deception_db
      COWRIE_LOG_PATH: /cowrie/cowrie.json
      PIPELINE_ENABLED: "true"
      PIPELINE_FROM_BEGINNING: "true"
    ports:
      - "127.0.0.1:8000:8000"
    volumes:
      - cowrie-logs:/cowrie:ro     # read-only view of the honeypot's JSON log
    depends_on:
      - mongo
      - cowrie

  dashboard:
    build:
      context: ./frontend
    restart: unless-stopped
    ports:
      - "127.0.0.1:5173:80"
    depends_on:
      - api

volumes:
  mongo-data:
  cowrie-logs:`}
          language="yaml"
          title="docker-compose.yml"
          showLineNumbers={true}
        />
      </div>

      <div className="pt-4 border-t border-slate-800 flex justify-between items-center text-xs">
        <Link to="/docs/configuration/env-vars" className="text-slate-400 hover:text-white">
          ← Environment Variables
        </Link>
        <Link to="/docs/api" className="text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1">
          <span>REST & WebSocket API Reference</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
};
