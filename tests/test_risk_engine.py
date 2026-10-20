"""
Unit tests for RiskEngine service.
"""

from datetime import datetime, timezone
import pytest

from backend.app.models.events import NormalizedEvent
from backend.app.models.features import SessionFeatures
from backend.app.models.intent import (
    AttackStage,
    ClassificationSource,
    HybridClassification,
    IntentCategory,
)
from backend.app.models.risk import RiskSeverity
from backend.app.services.risk_engine import RiskEngine


def make_classification(intent: IntentCategory) -> HybridClassification:
    return HybridClassification(
        intent=intent,
        attack_stage=AttackStage.DISCOVERY,
        confidence=0.90,
        source=ClassificationSource.RULE,
        rule_evidence=["test rule match"],
        timestamp=datetime.now(timezone.utc)
    )


def test_base_intent_risk_evaluation():
    ev = NormalizedEvent(
        event_id="e1",
        timestamp=datetime.now(timezone.utc),
        session_id="s1",
        event_type="command_input",
        command="cat /etc/shadow"
    )
    # CREDENTIAL_ACCESS base weight = 25
    cls_cred = make_classification(IntentCategory.CREDENTIAL_ACCESS)
    risk = RiskEngine.evaluate(ev, cls_cred)

    assert risk.risk_score == 25
    assert risk.severity == RiskSeverity.MEDIUM
    assert len(risk.contributing_factors) >= 1


def test_severity_levels_mapping():
    assert RiskEngine.map_severity(0) == RiskSeverity.LOW
    assert RiskEngine.map_severity(24) == RiskSeverity.LOW
    assert RiskEngine.map_severity(25) == RiskSeverity.MEDIUM
    assert RiskEngine.map_severity(49) == RiskSeverity.MEDIUM
    assert RiskEngine.map_severity(50) == RiskSeverity.HIGH
    assert RiskEngine.map_severity(74) == RiskSeverity.HIGH
    assert RiskEngine.map_severity(75) == RiskSeverity.CRITICAL
    assert RiskEngine.map_severity(100) == RiskSeverity.CRITICAL


def test_risk_score_clamping_and_multipliers():
    ev = NormalizedEvent(
        event_id="e_brute",
        timestamp=datetime.now(timezone.utc),
        session_id="s_brute",
        event_type="login_failed"
    )
    # EXFILTRATION base weight = 35 + login_failed = 5
    cls_exfil = make_classification(IntentCategory.EXFILTRATION)

    # Session features with heavy penalties
    sf = SessionFeatures(
        session_id="s_brute",
        login_failed_count=5,  # +10
        activity_rate=5.0,     # +5
        total_events=10,
        command_count=8,       # +5
        distinct_event_types_count=5 # +5
    )

    risk = RiskEngine.evaluate(ev, cls_exfil, sf)
    # 35 (base) + 5 (fail) + 10 (brute) + 5 (burst) + 5 (depth) + 5 (variety) = 65
    assert risk.risk_score == 65
    assert risk.severity == RiskSeverity.HIGH
    assert 0 <= risk.risk_score <= 100
