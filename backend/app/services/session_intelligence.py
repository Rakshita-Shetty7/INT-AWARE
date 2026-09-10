"""
Session Intelligence and Attacker Profiling Engine.
Tracks multi-stage progression, determines dominant intent, and evaluates cumulative session risk.
"""

from collections import Counter
from datetime import datetime, timezone
import logging
from typing import Dict, List, Optional

from backend.app.models.events import NormalizedEvent
from backend.app.models.features import SessionFeatures
from backend.app.models.intent import (
    AttackStage,
    HybridClassification,
    IntentCategory,
)
from backend.app.models.risk import RiskAssessment, RiskSeverity
from backend.app.models.session_intelligence import SessionIntelligence
from backend.app.services.risk_engine import INTENT_BASE_WEIGHTS, RiskEngine

logger = logging.getLogger(__name__)

# Lifecycle order for determining the furthest attack stage reached
STAGE_ORDER: List[AttackStage] = [
    AttackStage.UNKNOWN,
    AttackStage.INITIAL_ACCESS,
    AttackStage.RECONNAISSANCE,
    AttackStage.DISCOVERY,
    AttackStage.CREDENTIAL_ACCESS,
    AttackStage.EXECUTION,
    AttackStage.PRIVILEGE_ESCALATION,
    AttackStage.PERSISTENCE,
    AttackStage.EXFILTRATION,
    AttackStage.CLEANUP,
]


class SessionIntelligenceEngine:
    """
    Maintains and updates holistic session profiles tracking multi-step attacker behavior.
    """

    def __init__(self):
        self._session_classifications: Dict[str, List[HybridClassification]] = {}
        self._session_profiles: Dict[str, SessionIntelligence] = {}

    def update_session(
        self,
        event: NormalizedEvent,
        classification: HybridClassification,
        session_features: Optional[SessionFeatures] = None
    ) -> SessionIntelligence:
        """
        Incorporates a newly classified event into the session's historical trajectory
        and recalculates the comprehensive SessionIntelligence profile.
        """
        session_id = event.session_id
        if session_id not in self._session_classifications:
            self._session_classifications[session_id] = []

        self._session_classifications[session_id].append(classification)
        classifications = self._session_classifications[session_id]

        # Extract sequence trajectories
        intent_seq = [c.intent for c in classifications]
        stage_seq = [c.attack_stage for c in classifications]

        # 1. Resolve Dominant Intent (weighted frequency + severity)
        intent_counts = Counter(intent_seq)
        # Filter out OTHER if any specific malicious intent exists
        specific_intents = {k: v for k, v in intent_counts.items() if k != IntentCategory.OTHER}
        if specific_intents:
            # Sort by frequency then by severity weight
            dominant_intent = max(
                specific_intents.keys(),
                key=lambda k: (specific_intents[k], INTENT_BASE_WEIGHTS.get(k, 0))
            )
        else:
            dominant_intent = intent_counts.most_common(1)[0][0] if intent_counts else IntentCategory.OTHER

        # 2. Resolve Current / Furthest Attack Stage
        stage_indices = [STAGE_ORDER.index(s) if s in STAGE_ORDER else 0 for s in stage_seq]
        max_stage_idx = max(stage_indices) if stage_indices else 0
        current_stage = STAGE_ORDER[max_stage_idx]

        # 3. Compute Cumulative Session Risk Score
        cumulative_score = 0
        key_evidence: List[str] = []

        # Sum unique intent weights observed in the session
        unique_intents = set(intent_seq)
        for intent in unique_intents:
            w = INTENT_BASE_WEIGHTS.get(intent, 0)
            cumulative_score += w
            if w > 0:
                key_evidence.append(f"Observed '{intent}' behavior (+{w})")

        # Multi-stage escalation bonus (+15 if attacker executed 2+ distinct advanced stages)
        advanced_stages = {s for s in set(stage_seq) if s not in (AttackStage.UNKNOWN, AttackStage.INITIAL_ACCESS)}
        if len(advanced_stages) >= 2:
            cumulative_score += 15
            key_evidence.append(f"Multi-stage progression across {len(advanced_stages)} stages (+15)")

        # Session feature risk additions
        if session_features:
            if session_features.login_failed_count >= 3:
                cumulative_score += 10
                key_evidence.append(f"Authentication brute-force ({session_features.login_failed_count} failures) (+10)")
            if session_features.command_count >= 5:
                cumulative_score += 5
                key_evidence.append(f"Command execution depth ({session_features.command_count} commands) (+5)")
            if session_features.activity_rate > 2.0 and session_features.total_events > 4:
                cumulative_score += 5
                key_evidence.append(f"Automated activity burst ({session_features.activity_rate} ev/s) (+5)")

        # Clamp cumulative score
        final_risk_score = max(0, min(100, cumulative_score))
        severity = RiskEngine.map_severity(final_risk_score)

        # Average confidence
        confidences = [c.confidence for c in classifications]
        avg_confidence = round(sum(confidences) / len(confidences), 2) if confidences else 0.0

        # Collect top unique rule/AI evidence lines
        for c in classifications:
            for ev in c.rule_evidence:
                if ev not in key_evidence:
                    key_evidence.append(ev)
            if c.ai_reason and c.ai_reason not in key_evidence:
                key_evidence.append(f"AI: {c.ai_reason}")

        profile = SessionIntelligence(
            session_id=session_id,
            source_ip=event.source_ip,
            dominant_intent=dominant_intent,
            current_attack_stage=current_stage,
            intent_sequence=intent_seq,
            stage_sequence=stage_seq,
            risk_score=final_risk_score,
            severity=severity,
            confidence=avg_confidence,
            key_evidence=key_evidence[:10],  # Keep top 10 evidence items
            last_updated=datetime.now(timezone.utc)
        )

        self._session_profiles[session_id] = profile
        return profile

    def get_session_profile(self, session_id: str) -> Optional[SessionIntelligence]:
        """
        Retrieves the profile for a given session.
        """
        return self._session_profiles.get(session_id)

    def get_all_profiles(self) -> Dict[str, SessionIntelligence]:
        """
        Retrieves all active session profiles.
        """
        return dict(self._session_profiles)
