"""
AI Session Analyst Service.
Generates comprehensive cybersecurity investigations and threat interpretations
using Google Gemini API with robust deterministic fallbacks.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.config import is_gemini_api_key_configured, settings

logger = logging.getLogger(__name__)


class SessionAnalysisReport(BaseModel):
    """
    Structured threat intelligence report generated for a specific attacker session.
    """
    session_id: str
    objective: str = Field(description="Primary deduced objective of the attacker")
    summary: str = Field(description="Executive summary of the session behavior")
    attack_progression: List[str] = Field(default_factory=list, description="Chronological stage progression")
    key_evidence: List[str] = Field(default_factory=list, description="Critical behavioral indicators observed")
    threat_interpretation: str = Field(description="Deep interpretation of attacker intent and profile")
    recommended_action: str = Field(description="Actionable defensive response recommendations")
    source: str = Field(default="GEMINI_AI", description="Generation engine source (GEMINI_AI or DETERMINISTIC_ANALYST)")


SESSION_ANALYST_SYSTEM_PROMPT = """
You are a Principal Cyber Threat Intelligence Analyst examining high-fidelity honeypot telemetry.
Analyze the provided attacker session telemetry and provide a structured threat assessment.

Output strictly valid JSON matching this schema:
{
  "objective": "Concise summary of what the adversary was trying to achieve",
  "summary": "2-3 sentences explaining the full sequence of actions",
  "attack_progression": ["Step 1: Initial access...", "Step 2: Reconnaissance...", "Step 3: Discovery..."],
  "key_evidence": ["Evidence point 1", "Evidence point 2"],
  "threat_interpretation": "Assessment of threat actor capability, automation vs human, and operational intent",
  "recommended_action": "Defensive containment and hardening steps to mitigate this threat vector"
}

Rules:
1. Base all findings strictly on the provided commands, timeline, and features.
2. Do not invent or hallucinate actions that were not executed.
3. Be professional, direct, and actionable.
"""


class GeminiSessionAnalyst:
    """
    Analyzes holistic honeypot sessions using Google Gemini with deterministic fallback.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
        enabled: Optional[bool] = None,
        client: Optional[Any] = None
    ):
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.model_name = model or settings.GEMINI_MODEL
        self.timeout = timeout if timeout is not None else settings.GEMINI_TIMEOUT
        self.enabled = enabled if enabled is not None else settings.GEMINI_ENABLED
        self._client = client

    def _get_client(self) -> Optional[Any]:
        if self._client is not None:
            return self._client
        if not self.enabled or not is_gemini_api_key_configured(self.api_key):
            return None
        try:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
            return self._client
        except Exception as e:
            logger.warning("Failed to initialize google-genai Client for Session Analyst: %s", e)
            return None

    @staticmethod
    def _sanitize_session_context(session_doc: Dict[str, Any], events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extracts and sanitizes session context, removing passwords or sensitive credentials.
        """
        sanitized_commands = []
        for ev in events:
            cmd = ev.get("command")
            if cmd:
                # Remove passwords or tokens
                import re
                cmd = re.sub(r"(-p\s+)(\S+)", r"\1[REDACTED]", cmd)
                sanitized_commands.append({
                    "timestamp": str(ev.get("timestamp")),
                    "command": cmd,
                    "intent": ev.get("intent", "OTHER"),
                    "risk_score": ev.get("risk_score", 0),
                    "stage": ev.get("attack_stage", "UNKNOWN")
                })

        return {
            "session_id": session_doc.get("session_id"),
            "source_ip": session_doc.get("source_ip", "127.0.0.1"),
            "protocol": session_doc.get("protocol", "SSH"),
            "username": session_doc.get("username", "unknown"),
            "duration_seconds": session_doc.get("duration", 0),
            "dominant_intent": session_doc.get("dominant_intent", "OTHER"),
            "current_attack_stage": session_doc.get("current_attack_stage", "INITIAL_ACCESS"),
            "risk_score": session_doc.get("risk_score", 0),
            "severity": session_doc.get("severity", "LOW"),
            "intent_sequence": session_doc.get("intent_sequence", []),
            "stage_sequence": session_doc.get("stage_sequence", []),
            "command_count": session_doc.get("command_count", 0),
            "unique_commands": session_doc.get("unique_commands", []),
            "commands_executed": sanitized_commands
        }

    def _generate_deterministic_analysis(
        self,
        session_doc: Dict[str, Any],
        events: List[Dict[str, Any]]
    ) -> SessionAnalysisReport:
        """
        Generates deterministic analysis when Gemini is unavailable or disabled.
        """
        session_id = session_doc.get("session_id", "unknown")
        dom_intent = session_doc.get("dominant_intent", "OTHER")
        stage = session_doc.get("current_attack_stage", "INITIAL_ACCESS")
        risk = session_doc.get("risk_score", 0)
        source_ip = session_doc.get("source_ip", "127.0.0.1")
        cmd_count = session_doc.get("command_count", 0)
        unique_cmds = session_doc.get("unique_commands", [])

        # Deduce objective
        intent_objectives = {
            "RECONNAISSANCE": "Gathering system host specifications, OS kernel version, and operating environment parameters.",
            "DISCOVERY": "Mapping filesystem hierarchies, installed software components, and configuration files.",
            "CREDENTIAL_ACCESS": "Targeting authentication databases, user credentials, and security tokens.",
            "EXECUTION": "Attempting remote code execution and payload staging in temporary paths.",
            "PRIVILEGE_ESCALATION": "Attempting local privilege escalation to acquire root/superuser permissions.",
            "PERSISTENCE": "Attempting to plant persistence backdoors or scheduled jobs for recurring access.",
            "EXPLOITATION": "Firing vulnerability exploits against system daemons.",
            "EXFILTRATION": "Attempting to archive and exfiltrate internal system data to remote hosts.",
            "CLEANUP": "Attempting to purge shell history and audit logs to evade detection.",
            "OTHER": "Establishing initial SSH connection and exploring command interpreter."
        }
        objective = intent_objectives.get(dom_intent, "Performing exploratory probing against honeypot services.")

        # Summary
        summary = (
            f"Adversary from {source_ip} established an interactive session executing {cmd_count} command(s). "
            f"The primary classified intent is {dom_intent} reaching the {stage} attack stage with a threat risk score of {risk}/100."
        )

        # Progression
        progression = []
        stages_observed = session_doc.get("stage_sequence") or [stage]
        for i, stg in enumerate(stages_observed, 1):
            progression.append(f"Phase {i}: Reached {stg} stage via targeted command activity.")

        # Evidence
        evidence = session_doc.get("key_evidence") or []
        if not evidence and unique_cmds:
            evidence = [f"Executed commands: {', '.join(unique_cmds[:4])}"]

        # Interpretation
        if risk >= 75:
            threat_interpretation = "High-severity adversarial campaign displaying weaponized intent or evasion techniques."
            rec_action = f"Immediately block source IP {source_ip} on edge firewalls, inspect potential credential compromise, and isolate affected subnet."
        elif risk >= 40:
            threat_interpretation = "Moderate threat actor or automated bot executing discovery and reconnaissance scripts."
            rec_action = f"Add {source_ip} to threat watchlists, rotate credentials for user '{session_doc.get('username')}', and review intrusion telemetry."
        else:
            threat_interpretation = "Low-risk reconnaissance probe or automated credential testing bot."
            rec_action = "Maintain monitoring, verify honeypot containment, and record telemetry in threat database."

        return SessionAnalysisReport(
            session_id=session_id,
            objective=objective,
            summary=summary,
            attack_progression=progression,
            key_evidence=evidence,
            threat_interpretation=threat_interpretation,
            recommended_action=rec_action,
            source="DETERMINISTIC_ANALYST"
        )

    def analyze_session(
        self,
        session_doc: Dict[str, Any],
        events: List[Dict[str, Any]]
    ) -> SessionAnalysisReport:
        """
        Executes comprehensive session analysis via Gemini, falling back to deterministic analyst.
        """
        session_id = session_doc.get("session_id", "unknown")
        client = self._get_client()

        if client is None:
            logger.info("Gemini disabled or API key absent. Generating deterministic session analysis.")
            return self._generate_deterministic_analysis(session_doc, events)

        sanitized_context = self._sanitize_session_context(session_doc, events)
        prompt = f"Analyze the following honeypot attacker session telemetry:\n\n{json.dumps(sanitized_context, indent=2)}"

        try:
            from google.genai import types

            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SESSION_ANALYST_SYSTEM_PROMPT,
                    temperature=0.2,
                    response_mime_type="application/json"
                )
            )

            if response and response.text:
                parsed = json.loads(response.text)
                return SessionAnalysisReport(
                    session_id=session_id,
                    objective=parsed.get("objective", "Adversary host probing"),
                    summary=parsed.get("summary", "Session analyzed by Gemini."),
                    attack_progression=parsed.get("attack_progression", []),
                    key_evidence=parsed.get("key_evidence", []),
                    threat_interpretation=parsed.get("threat_interpretation", "Threat actor analysis."),
                    recommended_action=parsed.get("recommended_action", "Implement monitoring."),
                    source="GEMINI_AI"
                )
        except Exception as err:
            logger.warning("Gemini session analysis failed (%s). Falling back to deterministic analyst.", err)

        return self._generate_deterministic_analysis(session_doc, events)


# Global singleton
gemini_session_analyst = GeminiSessionAnalyst()
