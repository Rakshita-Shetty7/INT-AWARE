import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Radio,
  Users,
  AlertOctagon,
  BarChart3,
  ExternalLink,
  Code2,
} from 'lucide-react';

const NAV_ITEMS = [
  { path: '/', label: 'Overview', icon: LayoutDashboard },
  { path: '/sessions', label: 'Live Sessions', icon: Radio },
  { path: '/attackers', label: 'Attacker Profiles', icon: Users },
  { path: '/alerts', label: 'Threat Alerts', icon: AlertOctagon },
  { path: '/analytics', label: 'Analytics', icon: BarChart3 },
];

export default function Sidebar() {
  return (
    <aside className="w-64 bg-[#0d121d] border-r border-[#1f293d] flex flex-col justify-between p-4 flex-shrink-0 min-h-[calc(100vh-4rem)]">
      <div className="space-y-1">
        <div className="px-3 py-2 text-[11px] font-semibold tracking-wider text-slate-500 uppercase">
          Security Operations
        </div>
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-cyan-950/40 text-cyan-400 border border-cyan-800/60'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-[#111726]'
                }`
              }
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </div>

      {/* Footer Info */}
      <div className="border-t border-[#1f293d] pt-4 space-y-2">
        <a
          href="/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-between px-3 py-2 text-xs font-mono text-slate-400 hover:text-cyan-400 hover:bg-[#111726] rounded transition-colors"
        >
          <span className="flex items-center gap-2">
            <Code2 className="w-3.5 h-3.5" />
            FastAPI OpenAPI Docs
          </span>
          <ExternalLink className="w-3 h-3" />
        </a>
        <div className="px-3 py-1 text-[10px] text-slate-500 font-mono">
          Vite + React 19 + Tailwind CSS
        </div>
      </div>
    </aside>
  );
}
