import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  BookOpen,
  Zap,
  Layers,
  Terminal,
  Cpu,
  Settings,
  Container,
  Code2,
  HelpCircle,
  RefreshCw,
  GitPullRequest,
  Search,
  CheckCircle,
} from 'lucide-react';

interface DocsSidebarProps {
  onCloseMobile?: () => void;
}

interface DocItem {
  path: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
}

interface DocSection {
  title: string;
  items: DocItem[];
}

export const DOC_SECTIONS: DocSection[] = [
  {
    title: 'Getting Started',
    items: [
      { path: '/docs', label: 'Documentation Overview', icon: BookOpen },
      { path: '/docs/quickstart', label: '60-Second Quickstart', icon: Zap, badge: 'Fastest' },
      { path: '/docs/architecture', label: 'Architecture & Pipeline', icon: Layers },
    ],
  },
  {
    title: 'OS Installation Guides',
    items: [
      { path: '/docs/installation/windows', label: 'Windows (WSL2 / Docker)', icon: Terminal },
      { path: '/docs/installation/linux', label: 'Linux (Ubuntu / Debian / RHEL)', icon: Cpu },
      { path: '/docs/installation/macos', label: 'macOS (Apple Silicon & Intel)', icon: Terminal },
      { path: '/docs/installation/manual', label: 'Manual Setup (Without Docker)', icon: Settings },
    ],
  },
  {
    title: 'Configuration & Services',
    items: [
      { path: '/docs/configuration/env-vars', label: 'Environment Variables', icon: Settings },
      { path: '/docs/configuration/docker-services', label: 'Docker Compose Topology', icon: Container },
    ],
  },
  {
    title: 'API & Telemetry',
    items: [
      { path: '/docs/api', label: 'REST & WebSocket Reference', icon: Code2 },
    ],
  },
  {
    title: 'Operations & Maintenance',
    items: [
      { path: '/docs/troubleshooting', label: 'Troubleshooting & FAQ', icon: HelpCircle },
      { path: '/docs/maintenance', label: 'Stopping, Backups & Cleanup', icon: RefreshCw },
      { path: '/docs/contributing', label: 'Contributing & Verification', icon: GitPullRequest },
    ],
  },
];

export const DocsSidebar: React.FC<DocsSidebarProps> = ({ onCloseMobile }) => {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredSections = DOC_SECTIONS.map((section) => ({
    ...section,
    items: section.items.filter((item) =>
      item.label.toLowerCase().includes(searchQuery.toLowerCase())
    ),
  })).filter((section) => section.items.length > 0);

  return (
    <aside className="w-full h-full flex flex-col bg-[#070b16] border-r border-slate-800/80">
      {/* Search bar */}
      <div className="p-4 border-b border-slate-800/80">
        <div className="relative">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Filter documentation..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[#0a1020] border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/60 focus:ring-1 focus:ring-cyan-500/40 transition-all font-sans"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 text-xs"
            >
              ×
            </button>
          )}
        </div>
      </div>

      {/* Navigation items */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        {filteredSections.map((section, idx) => (
          <div key={idx} className="space-y-1.5">
            <h3 className="px-2.5 text-[11px] font-bold uppercase tracking-wider text-slate-500 font-mono">
              {section.title}
            </h3>
            <div className="space-y-0.5">
              {section.items.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    end={item.path === '/docs'}
                    onClick={onCloseMobile}
                    className={({ isActive }) =>
                      `flex items-center justify-between px-2.5 py-2 rounded-lg text-xs font-medium transition-all ${
                        isActive
                          ? 'bg-cyan-950/50 text-cyan-300 border border-cyan-800/60 shadow-sm font-semibold'
                          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 border border-transparent'
                      }`
                    }
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <Icon className="w-3.5 h-3.5 flex-shrink-0 text-cyan-400" />
                      <span className="truncate">{item.label}</span>
                    </div>
                    {item.badge && (
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-900/60 text-cyan-300 border border-cyan-700/50">
                        {item.badge}
                      </span>
                    )}
                  </NavLink>
                );
              })}
            </div>
          </div>
        ))}

        {filteredSections.length === 0 && (
          <div className="p-4 text-center text-xs text-slate-500">
            No documentation matching "{searchQuery}"
          </div>
        )}
      </div>

      {/* Footer quick verification badge */}
      <div className="p-3 border-t border-slate-800/80 bg-[#090e1c] text-[11px] font-mono text-slate-400 flex items-center justify-between">
        <span className="flex items-center gap-1.5 text-emerald-400">
          <CheckCircle className="w-3.5 h-3.5" />
          162/162 Tests Verified
        </span>
        <span className="text-slate-500">v1.0.0</span>
      </div>
    </aside>
  );
};
