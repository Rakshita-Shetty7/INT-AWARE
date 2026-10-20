"""
Counterfactual Risk Analysis Engine.

Performs non-destructive "what-if" risk simulations by recalculating session-level
risk scores when specific events or commands are excluded from the observation sequence.

Guarantees:
  * PURE SIMULATION: Zero modifications to historical records in MongoDB.
  * Deterministic and explainable attribution of risk contribution.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.models.intent import IntentCategory
from backend.app.services.risk_engine import INTENT_BASE_WEIGHTS, RiskEngine

logger = logging.getLogger(__name__)


class CounterfactualSimulationResult(BaseModel):
    session_id: str
    excluded_event_id: str
    excluded_command: Optional[str] = None
    excluded_intent: str
    original_risk_score: int
    original_severity: str
    counterfactual_risk_score: int
    counterfactual_severity: str
    risk_delta: int = Field(..., description="Risk score reduction if this event did not occur")
    percentage_contribution: float
    original_stages: List[str]
    counterfactual_stages: List[str]
    stage_dropped: Optional[str] = None
    criticality_rating: str = Field(..., description="CRITICAL, HIGH, MODERATE, or MINIMAL")
    causal_explanation: str


class CounterfactualEngine:
    """
    Simulates counterfactual scenarios to measure the causal impact of individual attack steps.
    """

    @staticmethod
    def simulate_event_exclusion(
        session_doc: Dict[str, Any],
        events: List[Dict[str, Any]],
        excluded_event_id: str,
    ) -> CounterfactualSimulationResult:
        session_id = session_doc.get("session_id", "unknown")
        original_risk = int(session_doc.get("risk_score", 0))
        original_sev = session_doc.get("severity", RiskEngine.map_severity(original_risk))

        # Find the target event
        target_ev = next((ev for ev in events if ev.get("event_id") == excluded_event_id), None)
        if not target_ev:
            # If not found by event_id, treat as no-op
            return CounterfactualSimulationResult(
                session_id=session_id,
                excluded_event_id=excluded_event_id,
                excluded_command=None,
                excluded_intent="UNKNOWN",
                original_risk_score=original_risk,
                original_severity=original_sev,
                counterfactual_risk_score=original_risk,
                counterfactual_severity=original_sev,
                risk_delta=0,
                percentage_contribution=0.0,
                original_stages=session_doc.get("stage_sequence", []),
                counterfactual_stages=session_doc.get("stage_sequence", []),
                stage_dropped=None,
                criticality_rating="MINIMAL",
                causal_explanation=f"Event {excluded_event_id} was not present in session telemetry.",
            )

        excluded_cmd = target_ev.get("command")
        excluded_intent = target_ev.get("intent", "OTHER")

        # Filter out the excluded event
        remaining_events = [ev for ev in events if ev.get("event_id") != excluded_event_id]

        # Recalculate unique intents and stages without the target event
        remaining_intents = set()
        remaining_stages = set()
        for ev in remaining_events:
            int_str = ev.get("intent", "OTHER")
            remaining_intents.add(int_str)
            stg_str = ev.get("attack_stage", "UNKNOWN")
            if stg_str and stg_str != "UNKNOWN":
                remaining_stages.add(stg_str)

        all_original_stages = set()
        for ev in events:
            stg = ev.get("attack_stage", "UNKNOWN")
            if stg and stg != "UNKNOWN":
                all_original_stages.add(stg)

        # Calculate counterfactual score
        base_sum = 0
        for i_str in remaining_intents:
            try:
                cat = IntentCategory(i_str)
                base_sum += INTENT_BASE_WEIGHTS.get(cat, 5)
            except ValueError:
                base_sum += 5

        adv_stages = {"PRIVILEGE_ESCALATION", "PERSISTENCE", "EXFILTRATION", "CLEANUP", "EXECUTION"}
        multi_stage_bonus = 15 if len(remaining_stages.intersection(adv_stages)) >= 2 else 0
        cmd_count = len([ev for ev in remaining_events if ev.get("command")])
        command_depth_bonus = min(15, cmd_count * 2)

        # Brute-force bonus: check if login failures >= 3
        login_fails = len([ev for ev in remaining_events if ev.get("event_type") == "login_failed"])
        brute_bonus = 10 if login_fails >= 3 else 0

        cf_risk = min(100, max(0, base_sum + multi_stage_bonus + command_depth_bonus + brute_bonus))
        cf_sev = RiskEngine.map_severity(cf_risk)

        delta = max(0, original_risk - cf_risk)
        pct = round((delta / original_risk * 100.0), 1) if original_risk > 0 else 0.0

        dropped_stages = all_original_stages - remaining_stages
        stage_dropped = next(iter(dropped_stages), None)

        # Criticality rating
        if delta >= 20 or stage_dropped in adv_stages:
            crit = "CRITICAL"
        elif delta >= 10:
            crit = "HIGH"
        elif delta >= 5:
            crit = "MODERATE"
        else:
            crit = "MINIMAL"

        # Causal narrative
        reasons = []
        if stage_dropped:
            reasons.append(f"Exclusion entirely removes the '{stage_dropped}' kill-chain stage from this session.")
        if delta > 0:
            reasons.append(f"Reduces cumulative threat risk by {delta} points ({pct}% contribution).")
        if original_sev != cf_sev:
            reasons.append(f"Demotes session severity classification from {original_sev} to {cf_sev}.")
        else:
            reasons.append(f"Session severity remains {cf_sev}.")

        return CounterfactualSimulationResult(
            session_id=session_id,
            excluded_event_id=excluded_event_id,
            excluded_command=excluded_cmd,
            excluded_intent=excluded_intent,
            original_risk_score=original_risk,
            original_severity=original_sev,
            counterfactual_risk_score=cf_risk,
            counterfactual_severity=cf_sev,
            risk_delta=delta,
            percentage_contribution=pct,
            original_stages=sorted(list(all_original_stages)),
            counterfactual_stages=sorted(list(remaining_stages)),
            stage_dropped=stage_dropped,
            criticality_rating=crit,
            causal_explanation=" ".join(reasons),
        )


counterfactual_engine = CounterfactualEngine()
