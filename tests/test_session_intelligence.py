"""
Unit tests for SessionIntelligenceEngine service.
"""

from datetime import datetime, timezone
import pytest

from backend.app.models.events import NormalizedEvent
from backend.app.models.intent import (
    AttackStage,
    ClassificationSource,
    HybridClassification,
    IntentCategory,
)
from backend.app.models.risk import RiskSeverity
from backend.app.services.session_intelligence import SessionIntelligenceEngine


def make_event(session_id: str, command: str) -> NormalizedEvent:
    return NormalizedEvent(
        event_id=f"ev_{command}",
        timestamp=datetime.now(timezone.utc),
        session_id=session_id,
        event_type="command_input",
        command=command
    )


def make_hybrid_result(intent: IntentCategory, stage: AttackStage) -> HybridClassification:
    return HybridClassification(
        intent=intent,
        attack_stage=stage,
        confidence=0.90,
        source=ClassificationSource.RULE,
        rule_evidence=[f"Rule match for {intent}"],
        timestamp=datetime.now(timezone.utc)
    )


def test_session_lifecycle_progression():
    engine = SessionIntelligenceEngine()
    sess_id = "attacker_sess_01"

    # Step 1: Reconnaissance (whoami)
    ev1 = make_event(sess_id, "whoami")
    c1 = make_hybrid_result(IntentCategory.RECONNAISSANCE, AttackStage.RECONNAISSANCE)
    p1 = engine.update_session(ev1, c1)

    assert p1.dominant_intent == IntentCategory.RECONNAISSANCE
    assert p1.current_attack_stage == AttackStage.RECONNAISSANCE
    assert p1.risk_score >= 10

    # Step 2: Discovery (ls -la /)
    ev2 = make_event(sess_id, "ls -la /")
    c2 = make_hybrid_result(IntentCategory.DISCOVERY, AttackStage.DISCOVERY)
    p2 = engine.update_session(ev2, c2)

    assert p2.current_attack_stage == AttackStage.DISCOVERY
    assert len(p2.intent_sequence) == 2

    # Step 3: Credential Access (cat /etc/shadow)
    ev3 = make_event(sess_id, "cat /etc/shadow")
    c3 = make_hybrid_result(IntentCategory.CREDENTIAL_ACCESS, AttackStage.CREDENTIAL_ACCESS)
    p3 = engine.update_session(ev3, c3)

    assert p3.current_attack_stage == AttackStage.CREDENTIAL_ACCESS
    # Multi-stage progression bonus triggered
    assert p3.risk_score >= 50
    assert p3.severity in (RiskSeverity.HIGH, RiskSeverity.CRITICAL)

    # Step 4: Privilege Escalation (sudo su)
    ev4 = make_event(sess_id, "sudo su")
    c4 = make_hybrid_result(IntentCategory.PRIVILEGE_ESCALATION, AttackStage.PRIVILEGE_ESCALATION)
    p4 = engine.update_session(ev4, c4)

    assert p4.current_attack_stage == AttackStage.PRIVILEGE_ESCALATION
    assert len(p4.stage_sequence) == 4
