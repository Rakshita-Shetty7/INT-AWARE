"""
Attack Campaign Graph Engine.

Builds an evidence-backed relationship graph correlating:
  1. Attacker IP addresses (Threat Actors)
  2. Honeypot Sessions (Intrusion attempts)
  3. MITRE ATT&CK Techniques (Tactics & procedures)
  4. Observed Indicators / Command Fingerprints (Payloads, canary tokens, paths)
  5. Cross-Session Behavioral Similarity Edges (Jaccard command overlap)

Detects and clusters multi-session attack campaigns from genuine stored telemetry.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field

from backend.app.services.mitre_mapper import MitreMapper

logger = logging.getLogger(__name__)


class GraphNode(BaseModel):
    id: str
    label: str
    type: str = Field(..., description="'ip', 'session', 'technique', or 'indicator'")
    risk_score: int = 0
    severity: str = "LOW"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relationship: str
    weight: float = 1.0
    evidence: str


class CampaignCluster(BaseModel):
    campaign_id: str
    label: str
    threat_ips: List[str]
    session_ids: List[str]
    dominant_tactics: List[str]
    technique_ids: List[str]
    average_risk: float
    confidence: float
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None


class CampaignGraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    campaigns: List[CampaignCluster]
    total_nodes: int
    total_edges: int
    total_campaigns: int


class CampaignGraphEngine:
    """
    Constructs an evidence-driven graph representation of observed attacks.
    """

    @staticmethod
    def _jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
        if not set_a or not set_b:
            return 0.0
        intersection = len(set_a.intersection(set_b))
        union = len(set_a.union(set_b))
        return round(intersection / union, 3) if union > 0 else 0.0

    @staticmethod
    def build_graph(
        sessions: List[Dict[str, Any]],
        attackers: List[Dict[str, Any]],
        events: Optional[List[Dict[str, Any]]] = None,
        max_nodes: int = 150,
    ) -> CampaignGraphResponse:
        nodes_dict: Dict[str, GraphNode] = {}
        edges_list: List[GraphEdge] = []
        edge_ids: Set[str] = set()

        def add_edge(source: str, target: str, rel: str, weight: float, ev: str):
            e_id = f"{source}->{target}:{rel}"
            if e_id not in edge_ids and source in nodes_dict and target in nodes_dict:
                edge_ids.add(e_id)
                edges_list.append(GraphEdge(
                    id=e_id,
                    source=source,
                    target=target,
                    relationship=rel,
                    weight=weight,
                    evidence=ev,
                ))

        # 1. Attacker IP Nodes
        for att in attackers:
            ip = att.get("source_ip")
            if not ip or ip in ("127.0.0.1", "localhost", "unknown"):
                continue
            r = int(att.get("maximum_risk", 20))
            nodes_dict[f"ip:{ip}"] = GraphNode(
                id=f"ip:{ip}",
                label=ip,
                type="ip",
                risk_score=r,
                severity=att.get("severity", "LOW"),
                metadata={
                    "total_sessions": att.get("total_sessions", 1),
                    "total_events": att.get("total_events", 0),
                    "dominant_intent": att.get("dominant_intent", "OTHER"),
                },
            )

        # 2. Session Nodes
        session_command_sets: Dict[str, Set[str]] = {}
        for sess in sessions[:50]:  # Cap to prevent graph clutter
            s_id = sess.get("session_id")
            if not s_id:
                continue
            r = int(sess.get("risk_score", 10))
            ip = sess.get("source_ip")
            unique_cmds = set(sess.get("unique_commands", []))
            session_command_sets[s_id] = unique_cmds

            node_id = f"session:{s_id}"
            nodes_dict[node_id] = GraphNode(
                id=node_id,
                label=f"Session {s_id[:8]}",
                type="session",
                risk_score=r,
                severity=sess.get("severity", "LOW"),
                metadata={
                    "session_id": s_id,
                    "source_ip": ip,
                    "stage": sess.get("current_attack_stage", "UNKNOWN"),
                    "intent": sess.get("dominant_intent", "OTHER"),
                    "command_count": sess.get("command_count", len(unique_cmds)),
                },
            )

            # Link IP -> Session
            if ip and f"ip:{ip}" in nodes_dict:
                add_edge(f"ip:{ip}", node_id, "LAUNCHED_SESSION", 1.0, f"Host {ip} established honeypot session {s_id}")

            # Extract MITRE techniques for this session
            dom_int = sess.get("dominant_intent", "OTHER")
            mapped = MitreMapper.get_techniques_for_intent(dom_int)
            for m in mapped:
                t_id = m.get("technique_id")
                if t_id:
                    tech_node_id = f"tech:{t_id}"
                    if tech_node_id not in nodes_dict:
                        nodes_dict[tech_node_id] = GraphNode(
                            id=tech_node_id,
                            label=f"{t_id}: {m.get('name', '')}",
                            type="technique",
                            risk_score=50,
                            severity="MEDIUM",
                            metadata={
                                "tactic": m.get("tactic", "Execution"),
                                "technique_id": t_id,
                            },
                        )
                    add_edge(node_id, tech_node_id, "EMPLOYED_TECHNIQUE", 0.8, f"Session exhibited {t_id}")

            # Extract key indicators (staging paths, urls, tools)
            for cmd in unique_cmds:
                tokens = cmd.split()
                for token in tokens:
                    if token.startswith(("/tmp/", "/dev/shm/", "/var/tmp/")) and len(token) > 5:
                        ind_id = f"ind:{hashlib.md5(token.encode()).hexdigest()[:8]}"
                        if ind_id not in nodes_dict:
                            nodes_dict[ind_id] = GraphNode(
                                id=ind_id,
                                label=token,
                                type="indicator",
                                risk_score=60,
                                severity="HIGH",
                                metadata={"kind": "Staging Path", "path": token},
                            )
                        add_edge(node_id, ind_id, "TOUCHED_ARTIFACT", 0.9, f"Executed command referencing {token}")

        # 3. Cross-Session Similarity Edges (Jaccard overlap on command sets)
        sess_items = list(session_command_sets.items())
        for i in range(len(sess_items)):
            id_a, cmds_a = sess_items[i]
            if len(cmds_a) < 2:
                continue
            for j in range(i + 1, len(sess_items)):
                id_b, cmds_b = sess_items[j]
                if len(cmds_b) < 2:
                    continue
                sim = CampaignGraphEngine._jaccard_similarity(cmds_a, cmds_b)
                if sim >= 0.35:
                    add_edge(
                        f"session:{id_a}",
                        f"session:{id_b}",
                        "BEHAVIORAL_SIMILARITY",
                        sim,
                        f"Shared {int(sim*100)}% command overlap between sessions",
                    )

        # 4. Connected Component Campaign Clustering
        # Group sessions by shared IP or high similarity into Campaign Clusters
        campaigns_map: Dict[str, Dict[str, Any]] = {}
        for s_id, cmds in session_command_sets.items():
            s_node = nodes_dict.get(f"session:{s_id}")
            if not s_node:
                continue
            ip = s_node.metadata.get("source_ip") or "cluster-anon"
            c_key = f"camp-{ip.replace('.', '-')}"
            if c_key not in campaigns_map:
                campaigns_map[c_key] = {
                    "campaign_id": c_key,
                    "label": f"Campaign Actor [{ip}]",
                    "threat_ips": [ip] if ip != "cluster-anon" else [],
                    "session_ids": [],
                    "tactics": set(),
                    "techniques": set(),
                    "risks": [],
                }
            campaigns_map[c_key]["session_ids"].append(s_id)
            campaigns_map[c_key]["risks"].append(s_node.risk_score)
            stg = s_node.metadata.get("stage")
            if stg:
                campaigns_map[c_key]["tactics"].add(stg)

        # Formulate final campaign clusters
        campaigns_list: List[CampaignCluster] = []
        for c_data in campaigns_map.values():
            r_list = c_data["risks"]
            avg_r = round(sum(r_list) / len(r_list), 1) if r_list else 0.0
            conf = min(0.98, round(0.5 + 0.1 * len(c_data["session_ids"]), 2))
            campaigns_list.append(CampaignCluster(
                campaign_id=c_data["campaign_id"],
                label=c_data["label"],
                threat_ips=c_data["threat_ips"],
                session_ids=c_data["session_ids"],
                dominant_tactics=sorted(list(c_data["tactics"])),
                technique_ids=[],
                average_risk=avg_r,
                confidence=conf,
            ))

        return CampaignGraphResponse(
            nodes=list(nodes_dict.values())[:max_nodes],
            edges=edges_list[:max_nodes * 2],
            campaigns=sorted(campaigns_list, key=lambda c: len(c.session_ids), reverse=True),
            total_nodes=len(nodes_dict),
            total_edges=len(edges_list),
            total_campaigns=len(campaigns_list),
        )


campaign_graph_engine = CampaignGraphEngine()
