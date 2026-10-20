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


def test_session_cache_is_bounded_lru():
    """Regression for F6: the engine must not grow memory without bound.
    With a small cap, the least-recently-updated sessions are evicted."""
    engine = SessionIntelligenceEngine(max_sessions=3)
    c = make_hybrid_result(IntentCategory.RECONNAISSANCE, AttackStage.RECONNAISSANCE)

    for i in range(5):
        engine.update_session(make_event(f"sess_{i}", f"cmd_{i}"), c)

    # Only the cap's worth of sessions are retained; the two oldest were evicted.
    assert len(engine.get_all_profiles()) == 3
    assert engine.get_session_profile("sess_0") is None
    assert engine.get_session_profile("sess_1") is None
    assert engine.get_session_profile("sess_4") is not None


def test_session_cache_lru_touch_preserves_recently_updated():
    """An older session that is updated again must survive eviction over a
    session that has been idle longer (true LRU, not plain FIFO)."""
    engine = SessionIntelligenceEngine(max_sessions=2)
    c = make_hybrid_result(IntentCategory.RECONNAISSANCE, AttackStage.RECONNAISSANCE)

    engine.update_session(make_event("A", "a1"), c)
    engine.update_session(make_event("B", "b1"), c)
    # Touch A again so it becomes most-recently-updated.
    engine.update_session(make_event("A", "a2"), c)
    # Adding C evicts B (idle longest), not A.
    engine.update_session(make_event("C", "c1"), c)

    assert engine.get_session_profile("A") is not None
    assert engine.get_session_profile("B") is None
    assert engine.get_session_profile("C") is not None


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
