"""
Unit tests for analytics endpoints.
"""

from datetime import datetime, timezone
from fastapi.testclient import TestClient
import mongomock
import pytest

from backend.app.api.dependencies import get_persistence_service
from backend.app.main import app
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
def mock_service():
    client = mongomock.MongoClient()
    db = client["test_analytics_db"]
    return PersistenceService(db=db)


@pytest.fixture
def client(mock_service):
    app.dependency_overrides[get_persistence_service] = lambda: mock_service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def seed_analytics_data(service: PersistenceService):
    # Event 1
    ev1 = NormalizedEvent(
        event_id="e1",
        timestamp=datetime(2026, 8, 19, 10, 0, 0, tzinfo=timezone.utc),
        session_id="s1",
        source_ip="1.1.1.1",
        event_type="command_input",
        command="uname -a"
    )
    cls1 = HybridClassification(
        intent=IntentCategory.RECONNAISSANCE,
        attack_stage=AttackStage.RECONNAISSANCE,
        confidence=0.9,
        source=ClassificationSource.RULE,
        rule_evidence=["recon"],
        timestamp=datetime.now(timezone.utc)
    )
    risk1 = RiskAssessment(risk_score=10, severity=RiskSeverity.LOW, contributing_factors=[])
    service.save_event(ev1, cls1, risk1)

    # Event 2
    ev2 = NormalizedEvent(
        event_id="e2",
        timestamp=datetime(2026, 8, 19, 10, 15, 0, tzinfo=timezone.utc),
        session_id="s1",
        source_ip="1.1.1.1",
        event_type="command_input",
        command="cat /etc/shadow"
    )
    cls2 = HybridClassification(
        intent=IntentCategory.CREDENTIAL_ACCESS,
        attack_stage=AttackStage.CREDENTIAL_ACCESS,
        confidence=0.95,
        source=ClassificationSource.RULE,
        rule_evidence=["cred"],
        timestamp=datetime.now(timezone.utc)
    )
    risk2 = RiskAssessment(risk_score=60, severity=RiskSeverity.HIGH, contributing_factors=[])
    service.save_event(ev2, cls2, risk2)

    # Session
    sess_intel = SessionIntelligence(
        session_id="s1",
        source_ip="1.1.1.1",
        dominant_intent=IntentCategory.CREDENTIAL_ACCESS,
        current_attack_stage=AttackStage.CREDENTIAL_ACCESS,
        risk_score=60,
        severity=RiskSeverity.HIGH,
        last_updated=datetime.now(timezone.utc)
    )
    service.update_session(sess_intel, SessionFeatures(session_id="s1", total_events=2))


def test_intent_analytics_endpoint(client, mock_service):
    seed_analytics_data(mock_service)
    res = client.get("/api/analytics/intents")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    intents = {item["intent"]: item["count"] for item in data}
    assert intents["RECONNAISSANCE"] == 1
    assert intents["CREDENTIAL_ACCESS"] == 1


def test_severity_analytics_endpoint(client, mock_service):
    seed_analytics_data(mock_service)
    res = client.get("/api/analytics/severity")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1
    assert data[0]["severity"] == "HIGH"


def test_timeline_analytics_endpoint(client, mock_service):
    seed_analytics_data(mock_service)
    res = client.get("/api/analytics/timeline")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1
    assert data[0]["event_count"] == 2
    assert data[0]["max_risk"] == 60
