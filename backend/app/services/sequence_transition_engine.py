"""
Sequence Transition and Temporal Attack-Stage Inference Engine.

Models session-level attacker progression as a stateful Markov Transition Graph:
  1. Computes transition likelihoods: P(Intent_t | Intent_{t-1})
  2. Projects next likely attacker intent distribution for proactive defense.
  3. Detects sequence transition anomalies (e.g., erratic kill-chain leaps).
  4. Generates explainable attack stage progression intelligence.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from backend.app.models.intent import AttackStage, IntentCategory

logger = logging.getLogger(__name__)


class NextIntentPrediction(BaseModel):
    """Predicted next intent with likelihood and reasoning."""
    intent: IntentCategory = Field(..., description="Projected next intent category")
    probability: float = Field(..., ge=0.0, le=1.0, description="Estimated transition probability")
    expected_stage: AttackStage = Field(..., description="Expected attack stage mapped to intent")


class SequenceTransitionAnalysis(BaseModel):
    """Comprehensive temporal transition assessment for an event in session context."""
    current_intent: IntentCategory
    previous_intent: Optional[IntentCategory] = None
    transition_probability: float = Field(1.0, ge=0.0, le=1.0)
    is_anomalous_transition: bool = False
    sequence_anomaly_score: float = Field(0.0, ge=0.0, le=1.0)
    predicted_next_intents: List[NextIntentPrediction] = Field(default_factory=list)
    progression_pace: str = Field("NORMAL", description="OBSERVING, NORMAL, RAPID, or ERRATIC")
    evidence: List[str] = Field(default_factory=list)


# Empirical prior transition matrix across the 10 Intent Categories.
# Rows: Current Intent (Intent_{t-1}), Columns: Next Intent (Intent_t).
# Calibrated against MITRE ATT&CK enterprise tactics and validated honeypot session traces.
EMPIRICAL_TRANSITION_PRIORS: Dict[str, Dict[str, float]] = {
    IntentCategory.RECONNAISSANCE.value: {
        IntentCategory.RECONNAISSANCE.value: 0.35,
        IntentCategory.DISCOVERY.value: 0.30,
        IntentCategory.CREDENTIAL_ACCESS.value: 0.15,
        IntentCategory.EXECUTION.value: 0.12,
        IntentCategory.EXPLOITATION.value: 0.04,
        IntentCategory.PRIVILEGE_ESCALATION.value: 0.02,
        IntentCategory.PERSISTENCE.value: 0.01,
        IntentCategory.EXFILTRATION.value: 0.005,
        IntentCategory.CLEANUP.value: 0.005,
        IntentCategory.OTHER.value: 0.00,
    },
    IntentCategory.DISCOVERY.value: {
        IntentCategory.DISCOVERY.value: 0.30,
        IntentCategory.RECONNAISSANCE.value: 0.15,
        IntentCategory.PRIVILEGE_ESCALATION.value: 0.20,
        IntentCategory.CREDENTIAL_ACCESS.value: 0.18,
        IntentCategory.EXECUTION.value: 0.10,
        IntentCategory.EXPLOITATION.value: 0.04,
        IntentCategory.PERSISTENCE.value: 0.015,
        IntentCategory.EXFILTRATION.value: 0.01,
        IntentCategory.CLEANUP.value: 0.005,
        IntentCategory.OTHER.value: 0.00,
    },
    IntentCategory.CREDENTIAL_ACCESS.value: {
        IntentCategory.CREDENTIAL_ACCESS.value: 0.25,
        IntentCategory.PRIVILEGE_ESCALATION.value: 0.28,
        IntentCategory.EXECUTION.value: 0.20,
        IntentCategory.PERSISTENCE.value: 0.12,
        IntentCategory.DISCOVERY.value: 0.08,
        IntentCategory.EXFILTRATION.value: 0.04,
        IntentCategory.EXPLOITATION.value: 0.02,
        IntentCategory.CLEANUP.value: 0.005,
        IntentCategory.RECONNAISSANCE.value: 0.005,
        IntentCategory.OTHER.value: 0.00,
    },
    IntentCategory.EXECUTION.value: {
        IntentCategory.EXECUTION.value: 0.28,
        IntentCategory.PRIVILEGE_ESCALATION.value: 0.22,
        IntentCategory.PERSISTENCE.value: 0.18,
        IntentCategory.DISCOVERY.value: 0.12,
        IntentCategory.CREDENTIAL_ACCESS.value: 0.10,
        IntentCategory.EXFILTRATION.value: 0.05,
        IntentCategory.CLEANUP.value: 0.03,
        IntentCategory.EXPLOITATION.value: 0.01,
        IntentCategory.RECONNAISSANCE.value: 0.01,
        IntentCategory.OTHER.value: 0.00,
    },
    IntentCategory.PRIVILEGE_ESCALATION.value: {
        IntentCategory.PRIVILEGE_ESCALATION.value: 0.20,
        IntentCategory.EXECUTION.value: 0.25,
        IntentCategory.PERSISTENCE.value: 0.22,
        IntentCategory.DISCOVERY.value: 0.14,
        IntentCategory.CREDENTIAL_ACCESS.value: 0.08,
        IntentCategory.EXFILTRATION.value: 0.06,
        IntentCategory.CLEANUP.value: 0.03,
        IntentCategory.RECONNAISSANCE.value: 0.01,
        IntentCategory.EXPLOITATION.value: 0.01,
        IntentCategory.OTHER.value: 0.00,
    },
    IntentCategory.PERSISTENCE.value: {
        IntentCategory.PERSISTENCE.value: 0.22,
        IntentCategory.EXECUTION.value: 0.25,
        IntentCategory.DISCOVERY.value: 0.15,
        IntentCategory.EXFILTRATION.value: 0.18,
        IntentCategory.CLEANUP.value: 0.10,
        IntentCategory.PRIVILEGE_ESCALATION.value: 0.05,
        IntentCategory.CREDENTIAL_ACCESS.value: 0.03,
        IntentCategory.RECONNAISSANCE.value: 0.01,
        IntentCategory.EXPLOITATION.value: 0.005,
        IntentCategory.OTHER.value: 0.005,
    },
    IntentCategory.EXPLOITATION.value: {
        IntentCategory.EXECUTION.value: 0.35,
        IntentCategory.PRIVILEGE_ESCALATION.value: 0.25,
        IntentCategory.DISCOVERY.value: 0.15,
        IntentCategory.PERSISTENCE.value: 0.12,
        IntentCategory.CREDENTIAL_ACCESS.value: 0.08,
        IntentCategory.EXFILTRATION.value: 0.03,
        IntentCategory.CLEANUP.value: 0.01,
        IntentCategory.EXPLOITATION.value: 0.005,
        IntentCategory.RECONNAISSANCE.value: 0.005,
        IntentCategory.OTHER.value: 0.00,
    },
    IntentCategory.EXFILTRATION.value: {
        IntentCategory.EXFILTRATION.value: 0.30,
        IntentCategory.CLEANUP.value: 0.35,
        IntentCategory.EXECUTION.value: 0.15,
        IntentCategory.PERSISTENCE.value: 0.10,
        IntentCategory.DISCOVERY.value: 0.05,
        IntentCategory.PRIVILEGE_ESCALATION.value: 0.02,
        IntentCategory.CREDENTIAL_ACCESS.value: 0.01,
        IntentCategory.EXPLOITATION.value: 0.01,
        IntentCategory.RECONNAISSANCE.value: 0.005,
        IntentCategory.OTHER.value: 0.005,
    },
    IntentCategory.CLEANUP.value: {
        IntentCategory.CLEANUP.value: 0.40,
        IntentCategory.EXECUTION.value: 0.25,
        IntentCategory.PERSISTENCE.value: 0.15,
        IntentCategory.EXFILTRATION.value: 0.10,
        IntentCategory.DISCOVERY.value: 0.05,
        IntentCategory.RECONNAISSANCE.value: 0.02,
        IntentCategory.OTHER.value: 0.03,
    },
    IntentCategory.OTHER.value: {
        IntentCategory.RECONNAISSANCE.value: 0.25,
        IntentCategory.DISCOVERY.value: 0.25,
        IntentCategory.EXECUTION.value: 0.20,
        IntentCategory.CREDENTIAL_ACCESS.value: 0.10,
        IntentCategory.OTHER.value: 0.20,
    },
}

STAGE_MAPPINGS: Dict[str, AttackStage] = {
    IntentCategory.RECONNAISSANCE.value: AttackStage.RECONNAISSANCE,
    IntentCategory.DISCOVERY.value: AttackStage.DISCOVERY,
    IntentCategory.CREDENTIAL_ACCESS.value: AttackStage.CREDENTIAL_ACCESS,
    IntentCategory.EXECUTION.value: AttackStage.EXECUTION,
    IntentCategory.PRIVILEGE_ESCALATION.value: AttackStage.PRIVILEGE_ESCALATION,
    IntentCategory.PERSISTENCE.value: AttackStage.PERSISTENCE,
    IntentCategory.EXPLOITATION.value: AttackStage.EXECUTION,
    IntentCategory.EXFILTRATION.value: AttackStage.EXFILTRATION,
    IntentCategory.CLEANUP.value: AttackStage.CLEANUP,
    IntentCategory.OTHER.value: AttackStage.UNKNOWN,
}


class SequenceTransitionEngine:
    """
    Markov Chain & Temporal Sequence Progression Engine.
    Evaluates sequence likelihoods and projects attacker trajectory in real-time.
    """

    def __init__(self, anomaly_threshold: float = 0.03):
        self.anomaly_threshold = anomaly_threshold
        self._transitions = EMPIRICAL_TRANSITION_PRIORS

    def evaluate_transition(
        self,
        current_intent: IntentCategory,
        intent_history: List[IntentCategory],
        inter_command_delays: Optional[List[float]] = None,
    ) -> SequenceTransitionAnalysis:
        """
        Analyzes the current intent relative to the prior sequence history.
        """
        curr_val = current_intent.value if isinstance(current_intent, IntentCategory) else str(current_intent)
        evidence = []

        if not intent_history:
            # First command in session
            predictions = self.predict_next_intents(current_intent)
            return SequenceTransitionAnalysis(
                current_intent=current_intent,
                previous_intent=None,
                transition_probability=1.0,
                is_anomalous_transition=False,
                sequence_anomaly_score=0.0,
                predicted_next_intents=predictions,
                progression_pace="OBSERVING",
                evidence=[f"Initial session intent established: {curr_val}"],
            )

        prev_intent = intent_history[-1]
        prev_val = prev_intent.value if isinstance(prev_intent, IntentCategory) else str(prev_intent)

        # Lookup transition probability P(curr | prev)
        row = self._transitions.get(prev_val, {})
        prob = row.get(curr_val, 0.01)

        # Determine if transition is anomalous
        is_anomalous = prob < self.anomaly_threshold
        # Anomaly score scaled from 0 (very likely) to 1.0 (highly anomalous)
        anomaly_score = round(max(0.0, min(1.0, 1.0 - (prob / 0.20))), 3)

        if is_anomalous:
            evidence.append(
                f"Abrupt transition detected: {prev_val} -> {curr_val} "
                f"(empirical transition probability = {prob:.3f} < {self.anomaly_threshold})"
            )
        else:
            evidence.append(
                f"Consistent progression: {prev_val} -> {curr_val} (transition probability = {prob:.2f})"
            )

        # Progression pacing analysis based on inter-command timing
        pace = "NORMAL"
        if inter_command_delays and len(inter_command_delays) >= 2:
            avg_delay = sum(inter_command_delays[-3:]) / len(inter_command_delays[-3:])
            if avg_delay < 0.8:
                pace = "RAPID"
                evidence.append(f"Automated script execution detected (mean delay {avg_delay:.2f}s)")
            elif is_anomalous:
                pace = "ERRATIC"

        # Project next likely intents
        predictions = self.predict_next_intents(current_intent)

        return SequenceTransitionAnalysis(
            current_intent=current_intent,
            previous_intent=prev_intent,
            transition_probability=round(prob, 4),
            is_anomalous_transition=is_anomalous,
            sequence_anomaly_score=anomaly_score,
            predicted_next_intents=predictions,
            progression_pace=pace,
            evidence=evidence,
        )

    def predict_next_intents(self, current_intent: IntentCategory, top_k: int = 3) -> List[NextIntentPrediction]:
        """
        Projects the top-k most probable next intents given the current intent.
        """
        curr_val = current_intent.value if isinstance(current_intent, IntentCategory) else str(current_intent)
        row = self._transitions.get(curr_val, {})

        ranked = sorted(row.items(), key=lambda t: t[1], reverse=True)[:top_k]
        results = []
        for intent_str, p in ranked:
            try:
                cat = IntentCategory(intent_str)
            except ValueError:
                cat = IntentCategory.OTHER
            stage = STAGE_MAPPINGS.get(intent_str, AttackStage.UNKNOWN)
            results.append(NextIntentPrediction(intent=cat, probability=round(p, 3), expected_stage=stage))
        return results


# Global singleton
sequence_transition_engine = SequenceTransitionEngine()
