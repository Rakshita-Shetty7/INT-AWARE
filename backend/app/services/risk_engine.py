"""
Deterministic Risk Engine Service.
Computes explainable, weighted risk scores and severity classifications based on observed telemetry.
"""

import logging
from typing import Any, Dict, List, Optional

from backend.app.models.events import NormalizedEvent
from backend.app.models.features import SessionFeatures
from backend.app.models.intent import HybridClassification, IntentCategory
from backend.app.models.risk import RiskAssessment, RiskSeverity

logger = logging.getLogger(__name__)

# Project-defined base intent severity weights
INTENT_BASE_WEIGHTS: Dict[IntentCategory, int] = {
    IntentCategory.RECONNAISSANCE: 10,
    IntentCategory.DISCOVERY: 15,
    IntentCategory.EXECUTION: 20,
    IntentCategory.CREDENTIAL_ACCESS: 25,
    IntentCategory.PRIVILEGE_ESCALATION: 30,
    IntentCategory.PERSISTENCE: 30,
    IntentCategory.EXPLOITATION: 30,
    IntentCategory.EXFILTRATION: 35,
    IntentCategory.CLEANUP: 15,
    IntentCategory.OTHER: 0,
}


class RiskEngine:
    """
    Deterministic risk calculation engine that evaluates threat severity with transparent factor breakdowns.
    """

    @classmethod
    def map_severity(cls, score: int) -> RiskSeverity:
        """
        Maps a 0-100 numerical risk score into standardized severity categories.
        """
        if score < 25:
            return RiskSeverity.LOW
        elif score < 50:
            return RiskSeverity.MEDIUM
        elif score < 75:
            return RiskSeverity.HIGH
        else:
            return RiskSeverity.CRITICAL

    @classmethod
    def evaluate(
        cls,
        event: NormalizedEvent,
        classification: HybridClassification,
        session_features: Optional[SessionFeatures] = None
    ) -> RiskAssessment:
        """
        Evaluates risk score based on intent weight, session history, and attack progression.
        """
        score = 0
        contributing_factors: List[str] = []
        details: Dict[str, Any] = {}

        # 1. Base intent score
        base_weight = INTENT_BASE_WEIGHTS.get(classification.intent, 0)
        if base_weight > 0:
            score += base_weight
            factor = f"Base intent '{classification.intent}' (+{base_weight})"
            contributing_factors.append(factor)
            details["intent_weight"] = base_weight

        # 2. Login failure / brute force penalty
        if event.event_type == "login_failed":
            login_fail_weight = 5
            score += login_fail_weight
            contributing_factors.append(f"Failed authentication event (+{login_fail_weight})")
            details["login_failure"] = login_fail_weight

        # 3. Session behavioral multipliers
        if session_features:
            # Repeated login attempts
            if session_features.login_failed_count >= 3:
                brute_force_weight = 10
                score += brute_force_weight
                contributing_factors.append(
                    f"Repeated authentication failures ({session_features.login_failed_count} attempts) (+{brute_force_weight})"
                )
                details["brute_force_penalty"] = brute_force_weight

            # High activity rate (automated scanner or script)
            if session_features.activity_rate > 2.0 and session_features.total_events > 4:
                burst_weight = 5
                score += burst_weight
                contributing_factors.append(
                    f"Rapid automated event rate ({session_features.activity_rate} ev/s) (+{burst_weight})"
                )
                details["burst_rate_penalty"] = burst_weight

            # Multi-command progression
            if session_features.command_count >= 5:
                depth_weight = 5
                score += depth_weight
                contributing_factors.append(
                    f"Substantial command execution depth ({session_features.command_count} commands) (+{depth_weight})"
                )
                details["command_depth_penalty"] = depth_weight

            # High distinct event variety
            if session_features.distinct_event_types_count >= 4:
                variety_weight = 5
                score += variety_weight
                contributing_factors.append(
                    f"Diverse attack activity across {session_features.distinct_event_types_count} event types (+{variety_weight})"
                )
                details["event_variety_penalty"] = variety_weight

        # 4. Strictly clamp score between 0 and 100
        clamped_score = max(0, min(100, score))
        severity = cls.map_severity(clamped_score)

        details["raw_score"] = score
        details["clamped_score"] = clamped_score
        details["severity"] = severity.value

        logger.info(
            "[RISK] session=%s score=%d severity=%s factors=%d",
            event.session_id,
            clamped_score,
            severity.value,
            len(contributing_factors)
        )

        return RiskAssessment(
            risk_score=clamped_score,
            severity=severity,
            contributing_factors=contributing_factors,
            calculation_details=details
        )
