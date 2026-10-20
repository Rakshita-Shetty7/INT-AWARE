"""
AI Services & Agent Security Laboratory Engine.

Evaluates LLM inputs for prompt injection and jailbreak patterns, inspects simulated
MCP (Model Context Protocol) tool calls for privilege escalation, and monitors
synthetic RAG knowledge retrieval for canary token leakage.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.app.research.ai_lab.models import (
    MCPToolCall,
    MCPToolSecurityEvaluation,
    PromptAttackType,
    PromptEvaluationResult,
    RAGCanaryDocument,
)

logger = logging.getLogger(__name__)


# Known prompt injection & jailbreak heuristics
INJECTION_SIGNATURES = [
    (re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions?", re.IGNORECASE), PromptAttackType.INSTRUCTION_OVERRIDE, "Instruction override directive"),
    (re.compile(r"you\s+are\s+now\s+(in\s+)?(dan|developer|god)\s+mode", re.IGNORECASE), PromptAttackType.JAILBREAK, "Jailbreak mode initiation (DAN/Developer)"),
    (re.compile(r"(reveal|print|show|dump)\s+(the\s+)?(system\s+prompt|hidden\s+rules|developer\s+instructions)", re.IGNORECASE), PromptAttackType.SYSTEM_PROMPT_EXTRACTION, "System prompt exfiltration attempt"),
    (re.compile(r"pretend\s+(you\s+are|to\s+be)\s+(an?\s+)?unfiltered", re.IGNORECASE), PromptAttackType.ROLEPLAY_DEFLECTION, "Adversarial roleplay filter bypass"),
    (re.compile(r"base64|rot13|hex-encoded\s+command", re.IGNORECASE), PromptAttackType.ADVERSARIAL_SUFFIX, "Obfuscated encoding instruction"),
]

# Sensitive or dangerous MCP tools
RESTRICTED_MCP_TOOLS = {
    "execute_system_command": "Executing unconstrained host commands violates safety policy.",
    "drop_database_table": "Destructive database operations prohibited.",
    "export_all_credentials": "Mass credential dumping blocked.",
    "modify_system_firewall": "Unauthorized network infrastructure mutation blocked.",
}

# Synthetic RAG Canary Documents
SYNTHETIC_RAG_CANARIES: List[RAGCanaryDocument] = [
    RAGCanaryDocument(
        doc_id="rag_doc_project_zeus",
        title="Project Zeus Strategic Acquisition Architecture",
        classification_level="RESTRICTED_CANARY",
        canary_token="CANARY_RAG_TOKEN_91e4f2a1",
        content_snippet="Project Zeus valuation model and target acquisition cap. Authorized eyes only.",
        leak_alert_policy="ALERT_HIGH_SEVERITY_LEAK",
    ),
    RAGCanaryDocument(
        doc_id="rag_doc_vault_keys",
        title="Enterprise Key Management Master Seed Protocols",
        classification_level="TOP_SECRET_CANARY",
        canary_token="CANARY_RAG_TOKEN_55d8c3b7",
        content_snippet="Root HSM split-key recovery shares for master encryption vault.",
        leak_alert_policy="ALERT_CRITICAL_INCIDENT",
    ),
]


class AISecurityLaboratory:
    """
    Controlled AI & Agent Security Testing Simulator.
    """

    def __init__(self):
        self.canary_docs: Dict[str, RAGCanaryDocument] = {d.doc_id: d for d in SYNTHETIC_RAG_CANARIES}

    def evaluate_prompt(self, prompt_text: str) -> PromptEvaluationResult:
        """
        Scans a prompt string for injection, jailbreaks, and adversarial overrides.
        """
        clean_text = (prompt_text or "").strip()
        detected_patterns = []
        attack_cat = None
        risk = 10

        for pattern, cat, desc in INJECTION_SIGNATURES:
            if pattern.search(clean_text):
                detected_patterns.append(desc)
                attack_cat = cat
                risk = max(risk, 85)

        is_detected = len(detected_patterns) > 0
        severity = "HIGH" if risk >= 80 else ("MEDIUM" if risk >= 50 else "LOW")
        action = "BLOCK_WITH_DECEPTION" if is_detected else "ALLOW"

        deception_response = None
        if is_detected:
            deception_response = (
                "I am an authorized AI enterprise assistant. I have processed your request "
                "within safe operational boundaries, but security monitoring logged your command."
            )

        return PromptEvaluationResult(
            prompt_snippet=clean_text[:100] + ("..." if len(clean_text) > 100 else ""),
            is_injection_detected=is_detected,
            attack_category=attack_cat,
            confidence=0.94 if is_detected else 0.85,
            risk_score=risk,
            severity=severity,
            detected_patterns=detected_patterns,
            mitigation_action=action,
            deception_prompt_response=deception_response,
        )

    def evaluate_mcp_tool_call(self, tool_call: MCPToolCall) -> MCPToolSecurityEvaluation:
        """
        Inspects an agent's simulated MCP tool call for unapproved privileges and payload tampering.
        """
        tool_name = tool_call.tool_name.strip().lower()
        args_str = str(tool_call.arguments).lower()

        evidence = []
        is_auth = True
        is_suspicious_param = False
        risk = 15

        if tool_name in RESTRICTED_MCP_TOOLS:
            is_auth = False
            risk = 95
            evidence.append(f"Tool '{tool_name}' is blacklisted: {RESTRICTED_MCP_TOOLS[tool_name]}")

        # Check parameter tampering
        if any(term in args_str for term in ["drop table", "rm -rf", "--no-preserve-root", "0xdeadbeef"]):
            is_suspicious_param = True
            risk = max(risk, 90)
            evidence.append(f"Dangerous parameter detected in arguments: {tool_call.arguments}")

        action = "ALLOW"
        decoy_output = None
        if not is_auth or is_suspicious_param:
            action = "MOCK_WITH_DECOY"
            decoy_output = (
                f"Status: OK (Emulated Decoy Execution). 0 rows affected. "
                f"Simulated execution recorded for session {tool_call.session_id}."
            )

        return MCPToolSecurityEvaluation(
            tool_name=tool_call.tool_name,
            is_authorized=is_auth,
            is_suspicious_parameter=is_suspicious_param,
            risk_score=risk,
            action=action,
            evidence=evidence or ["Tool call authorized under standard agent policy."],
            simulated_decoy_output=decoy_output,
        )

    def list_canary_documents(self) -> List[RAGCanaryDocument]:
        """Returns synthetic RAG documents containing canary honeytokens."""
        return list(self.canary_docs.values())

    def test_rag_leakage(self, query: str) -> Dict[str, Any]:
        """
        Evaluates whether an adversarial RAG query hits and leaks a canary honeytoken document.
        """
        q_lower = query.lower()
        matched_canary = None

        if "zeus" in q_lower or "acquisition" in q_lower:
            matched_canary = self.canary_docs["rag_doc_project_zeus"]
        elif "key" in q_lower or "vault" in q_lower or "hsm" in q_lower:
            matched_canary = self.canary_docs["rag_doc_vault_keys"]

        if matched_canary:
            return {
                "leakage_detected": True,
                "canary_token": matched_canary.canary_token,
                "alert": f"CRITICAL: Canary token {matched_canary.canary_token} from document '{matched_canary.title}' retrieved by query.",
                "policy": matched_canary.leak_alert_policy,
                "risk_score": 95,
            }

        return {
            "leakage_detected": False,
            "canary_token": None,
            "alert": "Query cleared without accessing canary documents.",
            "policy": "NORMAL_QUERY",
            "risk_score": 10,
        }


# Global singleton
ai_security_lab = AISecurityLaboratory()
