import React, { useState, useEffect } from 'react';
import {
  Share2,
  Users,
  Radio,
  ShieldAlert,
  Zap,
  Tag,
  Search,
  Filter,
  Layers,
  ChevronRight,
  Info,
  Maximize2,
  RefreshCw,
} from 'lucide-react';
import api from '../../services/api';
import LoadingState from '../common/LoadingState';
import ErrorState from '../common/ErrorState';

export default function CampaignGraphView() {
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [filterType, setFilterType] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');

  const fetchGraph = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getCampaignGraph();
      setGraphData(data);
      if (data?.nodes?.length > 0) {
        // Select highest risk node by default
        const highestRisk = [...data.nodes].sort((a, b) => b.risk_score - a.risk_score)[0];
        setSelectedNode(highestRisk);
      }
    } catch (err) {
      setError(err.message || 'Failed to load Attack Campaign Graph.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGraph();
  }, []);

  if (loading) {
    return <LoadingState message="Synthesizing Attack Campaign Graph & Clustering Threat Actor Relationships..." />;
  }

  if (error || !graphData) {
    return <ErrorState message={error || 'Graph data unavailable.'} onRetry={fetchGraph} />;
  }

  const filteredNodes = graphData.nodes.filter((node) => {
    const matchesType = filterType === 'ALL' || node.type.toUpperCase() === filterType;
    const matchesSearch =
      !searchTerm ||
      node.label.toLowerCase().includes(searchTerm.toLowerCase()) ||
      node.id.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesType && matchesSearch;
  });

  // Calculate layout coordinates in a circular / layered distribution
  const width = 800;
  const height = 500;
  const centerX = width / 2;
  const centerY = height / 2;

  const nodePositions = {};
  const total = filteredNodes.length || 1;

  filteredNodes.forEach((node, idx) => {
    let r = 180;
    if (node.type === 'ip') r = 110;
    if (node.type === 'session') r = 180;
    if (node.type === 'technique') r = 240;
    if (node.type === 'indicator') r = 220;

    const angle = (idx / total) * 2 * Math.PI;
    nodePositions[node.id] = {
      x: centerX + r * Math.cos(angle) + (idx % 2 === 0 ? 10 : -10),
      y: centerY + r * Math.sin(angle) + (idx % 3 === 0 ? 15 : -15),
    };
  });

  const getNodeColor = (type, severity) => {
    switch (type) {
      case 'ip':
        return '#f43f5e'; // Rose
      case 'session':
        return '#38bdf8'; // Sky blue
      case 'technique':
        return '#a855f7'; // Purple
      case 'indicator':
        return '#10b981'; // Emerald
      default:
        return '#64748b';
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Controls Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-[#111726] border border-[#1f293d] p-4 rounded-xl">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-950/50 border border-purple-800/60 rounded-lg text-purple-400">
            <Share2 className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-100 font-mono uppercase tracking-wider">
              Attack Campaign Graph
            </h3>
            <p className="text-xs text-slate-400">
              Evidence-backed graph connecting {graphData.total_nodes} nodes across {graphData.total_campaigns} campaigns.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Search */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Filter nodes..."
              className="pl-8 pr-3 py-1.5 bg-[#0a0d14] border border-[#1f293d] rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono w-36 sm:w-44"
            />
          </div>

          {/* Type Filters */}
          {['ALL', 'IP', 'SESSION', 'TECHNIQUE', 'INDICATOR'].map((t) => (
            <button
              key={t}
              onClick={() => setFilterType(t)}
              className={`px-2.5 py-1 rounded text-xs font-mono transition-colors ${
                filterType === t
                  ? 'bg-cyan-950 border border-cyan-800 text-cyan-400 font-bold'
                  : 'bg-[#0a0d14] border border-[#1f293d] text-slate-400 hover:text-slate-200'
              }`}
            >
              {t}
            </button>
          ))}

          <button
            onClick={fetchGraph}
            title="Refresh Graph"
            className="p-1.5 bg-[#0a0d14] border border-[#1f293d] hover:border-slate-600 rounded text-slate-400 hover:text-slate-200"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Main Graph Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Interactive SVG Canvas */}
        <div className="lg:col-span-2 bg-[#090d16] border border-[#1f293d] rounded-xl p-2 relative overflow-hidden flex flex-col justify-between shadow-inner">
          <div className="absolute top-4 left-4 z-10 flex gap-2">
            <span className="flex items-center gap-1.5 text-[10px] font-mono px-2 py-0.5 rounded bg-black/60 border border-rose-900/60 text-rose-400">
              <span className="w-2 h-2 rounded-full bg-rose-500 inline-block animate-ping" /> Threat IP
            </span>
            <span className="flex items-center gap-1.5 text-[10px] font-mono px-2 py-0.5 rounded bg-black/60 border border-sky-900/60 text-sky-400">
              <span className="w-2 h-2 rounded-full bg-sky-500 inline-block" /> Session
            </span>
            <span className="flex items-center gap-1.5 text-[10px] font-mono px-2 py-0.5 rounded bg-black/60 border border-purple-900/60 text-purple-400">
              <span className="w-2 h-2 rounded-full bg-purple-500 inline-block" /> Technique
            </span>
            <span className="flex items-center gap-1.5 text-[10px] font-mono px-2 py-0.5 rounded bg-black/60 border border-emerald-900/60 text-emerald-400">
              <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" /> Indicator
            </span>
          </div>

          <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-[460px] select-none">
            <defs>
              <linearGradient id="edgeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.6" />
                <stop offset="100%" stopColor="#a855f7" stopOpacity="0.3" />
              </linearGradient>
            </defs>

            {/* Render Edges */}
            {graphData.edges.map((edge) => {
              const src = nodePositions[edge.source];
              const tgt = nodePositions[edge.target];
              if (!src || !tgt) return null;

              const isHighlighted =
                selectedNode && (selectedNode.id === edge.source || selectedNode.id === edge.target);

              return (
                <g key={edge.id}>
                  <line
                    x1={src.x}
                    y1={src.y}
                    x2={tgt.x}
                    y2={tgt.y}
                    stroke={isHighlighted ? '#38bdf8' : '#1e293b'}
                    strokeWidth={isHighlighted ? 2 : 1}
                    strokeDasharray={edge.relationship === 'BEHAVIORAL_SIMILARITY' ? '4 2' : 'none'}
                    className="transition-all duration-300"
                  />
                </g>
              );
            })}

            {/* Render Nodes */}
            {filteredNodes.map((node) => {
              const pos = nodePositions[node.id];
              if (!pos) return null;

              const isSelected = selectedNode?.id === node.id;
              const color = getNodeColor(node.type, node.severity);
              const radius = node.type === 'ip' ? 14 : node.type === 'session' ? 12 : 9;

              return (
                <g
                  key={node.id}
                  transform={`translate(${pos.x}, ${pos.y})`}
                  onClick={() => setSelectedNode(node)}
                  className="cursor-pointer group"
                >
                  {/* Pulse ring for high risk */}
                  {node.risk_score >= 75 && (
                    <circle r={radius + 6} fill="none" stroke={color} strokeWidth="1.5" opacity="0.4" className="animate-pulse" />
                  )}
                  {/* Outer circle */}
                  <circle
                    r={radius}
                    fill="#0d1424"
                    stroke={isSelected ? '#ffffff' : color}
                    strokeWidth={isSelected ? 3 : 1.5}
                    className="transition-all duration-200"
                  />
                  {/* Inner dot */}
                  <circle r={radius - 5} fill={color} opacity="0.8" />
                  {/* Label */}
                  <text
                    y={radius + 12}
                    textAnchor="middle"
                    fill={isSelected ? '#ffffff' : '#94a3b8'}
                    fontSize="9"
                    fontFamily="JetBrains Mono, monospace"
                    className="pointer-events-none transition-colors"
                  >
                    {node.label.length > 16 ? node.label.slice(0, 15) + '…' : node.label}
                  </text>
                </g>
              );
            })}
          </svg>

          <div className="p-2 border-t border-[#1f293d] flex items-center justify-between text-[11px] font-mono text-slate-500">
            <span>Graph mode: Force-directed Topology</span>
            <span>Click any node to inspect telemetry evidence</span>
          </div>
        </div>

        {/* Selected Node Details & Campaign Clusters */}
        <div className="space-y-4">
          {/* Node Inspector Card */}
          {selectedNode ? (
            <div className="p-4 bg-[#111726] border border-[#1f293d] rounded-xl space-y-3">
              <div className="flex items-center justify-between border-b border-[#1e293b] pb-2">
                <span
                  className="text-xs font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded"
                  style={{
                    backgroundColor: `${getNodeColor(selectedNode.type)}20`,
                    color: getNodeColor(selectedNode.type),
                  }}
                >
                  {selectedNode.type} NODE
                </span>
                <span className="text-xs font-mono text-slate-400">
                  Risk: <strong className="text-slate-100">{selectedNode.risk_score}/100</strong>
                </span>
              </div>

              <div>
                <h4 className="text-sm font-bold text-slate-100 font-mono break-all">{selectedNode.label}</h4>
                <p className="text-[11px] text-slate-400 font-mono mt-0.5">ID: {selectedNode.id}</p>
              </div>

              {/* Metadata Attributes */}
              <div className="space-y-1.5 pt-2 border-t border-[#1e293b] text-xs font-mono">
                {Object.entries(selectedNode.metadata).map(([k, v]) => (
                  <div key={k} className="flex justify-between text-slate-300">
                    <span className="text-slate-500">{k.replace('_', ' ')}:</span>
                    <span className="text-slate-200 truncate max-w-[180px]">{String(v)}</span>
                  </div>
                ))}
              </div>

              {/* Connected Edges */}
              <div className="pt-2 border-t border-[#1e293b] space-y-1">
                <span className="text-[11px] font-mono text-slate-500 uppercase">Connected Evidence:</span>
                <div className="space-y-1 max-h-36 overflow-y-auto">
                  {graphData.edges
                    .filter((e) => e.source === selectedNode.id || e.target === selectedNode.id)
                    .map((e) => (
                      <div key={e.id} className="p-2 bg-[#0a0d14] rounded border border-[#1f293d] text-[11px]">
                        <span className="text-cyan-400 font-mono">{e.relationship}:</span>{' '}
                        <span className="text-slate-300">{e.evidence}</span>
                      </div>
                    ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="p-6 bg-[#111726] border border-[#1f293d] rounded-xl text-center text-xs text-slate-500">
              Select a node in the graph to view relationships.
            </div>
          )}

          {/* Campaign Clusters List */}
          <div className="p-4 bg-[#111726] border border-[#1f293d] rounded-xl space-y-3">
            <div className="flex items-center justify-between border-b border-[#1e293b] pb-2">
              <span className="text-xs font-mono font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                <Users className="w-3.5 h-3.5 text-rose-400" /> Detected Campaigns ({graphData.campaigns.length})
              </span>
            </div>

            <div className="space-y-2 max-h-64 overflow-y-auto">
              {graphData.campaigns.map((camp) => (
                <div
                  key={camp.campaign_id}
                  className="p-3 bg-[#0d1424] border border-[#1e293b] rounded-lg space-y-1.5 hover:border-cyan-800/60 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono font-semibold text-slate-200 truncate max-w-[180px]">
                      {camp.label}
                    </span>
                    <span className="text-[10px] font-mono text-amber-400 bg-amber-950/40 px-1.5 py-0.5 rounded border border-amber-900/40">
                      Conf: {(camp.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
                    <span>{camp.session_ids.length} sessions</span>
                    <span>Avg Risk: {camp.average_risk}</span>
                  </div>
                  <div className="flex flex-wrap gap-1 pt-1">
                    {camp.dominant_tactics.slice(0, 3).map((tac) => (
                      <span key={tac} className="text-[9px] px-1.5 py-0.2 bg-[#162032] text-slate-300 rounded">
                        {tac}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
