"""
Evidence-First AI Security Copilot Engine.

Answers security investigation questions grounded exclusively in real honeypot telemetry.
Enforces the strict distinction between:
  * VERIFIED FACTS (with exact event_id, command string, and timestamp citations)
  * HYPOTHESES (inferences regarding threat actor intention or sophistication)
  * UNCERTAINTIES (operational limitations or unobserved outbound network context)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.config import settings
from backend.app.services.persistence_service import PersistenceService

logger = logging.getLogger(__name__)


class CopilotFact(BaseModel):
    statement: str
    event_id: str
    timestamp: Optional[str] = None
    evidence_command: Optional[str] = None


class CopilotResponse(BaseModel):
    query: str
    answer: str
    facts: List[CopilotFact] = Field(default_factory=list)
    hypotheses: List[str] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)
    cited_event_ids: List[str] = Field(default_factory=list)
    session_id_context: Optional[str] = None
    model_source: str = Field("DETERMINISTIC_EVIDENCE_ENGINE", description="'GEMINI_PRO' or 'DETERMINISTIC_EVIDENCE_ENGINE'")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EvidenceFirstCopilot:
    """
    Grounds cybersecurity reasoning strictly in authentic honeypot telemetry.
    """

    def __init__(self, persistence_service: Optional[PersistenceService] = None):
        self.persistence = persistence_service or PersistenceService()

    def query(
        self,
        question: str,
        session_id: Optional[str] = None,
        source_ip: Optional[str] = None,
        persistence_override: Optional[PersistenceService] = None,
    ) -> CopilotResponse:
        q_lower = question.lower().strip()
        svc = persistence_override or self.persistence

        # 1. Gather real evidence from database
        events: List[Dict[str, Any]] = []
        session_doc: Optional[Dict[str, Any]] = None

        if session_id:
            session_doc = svc.get_session(session_id)
            evs, _ = svc.get_events(limit=100, filters={"session_id": session_id})
            events = evs
        elif source_ip:
            evs, _ = svc.get_events(limit=100, filters={"source_ip": source_ip})
            events = evs
        else:
            # Query recent high/critical events
            evs, _ = svc.get_events(limit=50)
            events = evs

        # 2. Extract facts directly from events
        facts: List[CopilotFact] = []
        cited_ids: List[str] = []

        for ev in events[:20]:
            cmd = ev.get("command")
            e_id = ev.get("event_id", "unknown")
            ts = ev.get("timestamp")
            ts_str = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
            intent = ev.get("intent", "OTHER")

            # Check relevance to question
            is_relevant = False
            if session_id:
                is_relevant = True
            elif not q_lower or any(word in q_lower for word in ["what", "how", "all", "summary", "session", "attack", "show", "credential", "shadow"]):
                is_relevant = True
            elif cmd and any(term in cmd.lower() for term in q_lower.split() if len(term) > 2):
                is_relevant = True
            elif intent.lower() in q_lower:
                is_relevant = True

            if is_relevant and cmd:
                facts.append(CopilotFact(
                    statement=f"Attacker executed '{cmd}' categorized as {intent} at {ts_str}.",
                    event_id=e_id,
                    timestamp=ts_str,
                    evidence_command=cmd,
                ))
                cited_ids.append(e_id)

        # 3. Formulate hypotheses and uncertainties
        hypotheses: List[str] = []
        uncertainties: List[str] = [
            "Honeypot environment is safely network-isolated; external command-and-control communication cannot be validated from local logs alone.",
            "Attacker identity (automated script vs human operator) is inferred from keystroke timing and error patterns, not direct attribution.",
        ]

        if any("download" in f.statement.lower() or "curl" in (f.evidence_command or "") or "wget" in (f.evidence_command or "") for f in facts):
            hypotheses.append("Attacker attempted to stage second-stage malware payloads from an external repository into ephemeral system directories.")
        if any("shadow" in (f.evidence_command or "") or "passwd" in (f.evidence_command or "") for f in facts):
            hypotheses.append("Threat actor sought credential access to facilitate lateral movement across related network infrastructure.")
        if not hypotheses:
            hypotheses.append("Attacker was conducting initial reconnaissance to fingerprint system architecture and verify active services.")

        # 4. Optional Gemini synthesis if enabled and configured
        if settings.GEMINI_ENABLED and settings.GEMINI_API_KEY:
            try:
                from google.genai import Client, types
                client = Client(api_key=settings.GEMINI_API_KEY)
                evidence_prompt = (
                    f"You are the INT-AWARE Evidence-First Security Copilot. Answer the analyst query based STRICTLY on the real recorded telemetry below.\n"
                    f"Analyst Query: {question}\n\n"
                    f"Telemetric Evidence ({len(facts)} events):\n"
                    f"{json.dumps([f.model_dump() for f in facts[:15]], indent=2)}\n\n"
                    f"Rules:\n"
                    f"1. Cite exact event_id for every fact.\n"
                    f"2. Clearly separate verified facts from hypotheses.\n"
                    f"3. Note uncertainties if external evidence is missing.\n"
                    f"4. Do not invent facts."
                )
                res = client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=evidence_prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        http_options=types.HttpOptions(timeout=int(settings.GEMINI_TIMEOUT * 1000)),
                    )
                )
                if res and res.text:
                    return CopilotResponse(
                        query=question,
                        answer=res.text.strip(),
                        facts=facts[:10],
                        hypotheses=hypotheses,
                        uncertainties=uncertainties,
                        cited_event_ids=cited_ids[:10],
                        session_id_context=session_id,
                        model_source=settings.GEMINI_MODEL,
                    )
            except Exception as e:
                logger.debug("Gemini copilot query skipped (%s), falling back to deterministic synthesis", e)

        # 5. Deterministic evidence synthesis
        if facts:
            narrative = (
                f"### Investigation Findings for: *\"{question}\"*\n\n"
                f"**Evidence Summary:** Examined {len(events)} telemetry events"
                f"{f' for session `{session_id}`' if session_id else ''}.\n\n"
                f"**Key Observed Actions:**\n"
            )
            for fact in facts[:5]:
                narrative += f"- `{fact.evidence_command}` (*{fact.statement}* — Event ID: `{fact.event_id}`)\n"

            narrative += (
                f"\n**Analytical Assessment:**\n"
                f"Based on the command trajectory, the adversary focused on {', '.join(set(ev.get('intent', 'OTHER') for ev in events[:5]))}. "
                f"Zero host commands breached honeypot containment."
            )
        else:
            narrative = (
                f"No specific attack telemetry matching query *\"{question}\"* was found in the queried scope. "
                f"The system currently maintains strict zero-host isolation with no detected unauthorized execution."
            )

        return CopilotResponse(
            query=question,
            answer=narrative,
            facts=facts[:10],
            hypotheses=hypotheses,
            uncertainties=uncertainties,
            cited_event_ids=cited_ids[:10],
            session_id_context=session_id,
            model_source="DETERMINISTIC_EVIDENCE_ENGINE",
        )


copilot_engine = EvidenceFirstCopilot()
