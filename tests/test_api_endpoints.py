"""
Unit and integration tests for FastAPI REST API endpoints.
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
    db = client["test_api_db"]
    return PersistenceService(db=db)


@pytest.fixture
def client(mock_service):
    app.dependency_overrides[get_persistence_service] = lambda: mock_service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def seed_test_data(service: PersistenceService):
    ev = NormalizedEvent(
        event_id="ev_api_01",
        timestamp=datetime.now(timezone.utc),
        session_id="sess_api_01",
        source_ip="192.168.1.50",
        event_type="command_input",
        command="whoami",
        raw_event={"input": "whoami"}
    )
    cls = HybridClassification(
        intent=IntentCategory.RECONNAISSANCE,
        attack_stage=AttackStage.RECONNAISSANCE,
        confidence=0.90,
        source=ClassificationSource.RULE,
        rule_evidence=["Reconnaissance matched"],
        timestamp=datetime.now(timezone.utc)
    )
    risk = RiskAssessment(
        risk_score=15,
        severity=RiskSeverity.LOW,
        contributing_factors=["Base recon"]
    )
    service.save_event(ev, cls, risk)

    sess_intel = SessionIntelligence(
        session_id="sess_api_01",
        source_ip="192.168.1.50",
        dominant_intent=IntentCategory.RECONNAISSANCE,
        current_attack_stage=AttackStage.RECONNAISSANCE,
        risk_score=15,
        severity=RiskSeverity.LOW,
        last_updated=datetime.now(timezone.utc)
    )
    service.update_session(sess_intel, SessionFeatures(session_id="sess_api_01", total_events=1))


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data


def test_dashboard_stats_endpoint(client, mock_service):
    seed_test_data(mock_service)
    response = client.get("/api/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_sessions"] == 1
    assert data["total_events"] == 1
    assert data["total_attackers"] == 1


def test_events_list_and_pagination(client, mock_service):
    seed_test_data(mock_service)
    response = client.get("/api/events?page=1&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["event_id"] == "ev_api_01"


def test_events_filtering(client, mock_service):
    seed_test_data(mock_service)
    # Match filter
    res_match = client.get("/api/events?intent=RECONNAISSANCE")
    assert res_match.status_code == 200
    assert res_match.json()["total"] == 1

    # Non-match filter
    res_nomatch = client.get("/api/events?intent=EXPLOITATION")
    assert res_nomatch.status_code == 200
    assert res_nomatch.json()["total"] == 0


def test_single_event_endpoint_and_404(client, mock_service):
    seed_test_data(mock_service)
    # Valid
    res_valid = client.get("/api/events/ev_api_01")
    assert res_valid.status_code == 200
    assert res_valid.json()["event_id"] == "ev_api_01"

    # 404
    res_404 = client.get("/api/events/non_existent_event_id")
    assert res_404.status_code == 404


def test_sessions_list_and_detail(client, mock_service):
    seed_test_data(mock_service)
    res_list = client.get("/api/sessions")
    assert res_list.status_code == 200
    assert res_list.json()["total"] == 1

    res_detail = client.get("/api/sessions/sess_api_01")
    assert res_detail.status_code == 200
    assert res_detail.json()["session_id"] == "sess_api_01"

    res_404 = client.get("/api/sessions/unknown_session")
    assert res_404.status_code == 404


def test_attackers_list_and_detail(client, mock_service):
    seed_test_data(mock_service)
    res_list = client.get("/api/attackers")
    assert res_list.status_code == 200
    assert res_list.json()["total"] == 1

    res_detail = client.get("/api/attackers/192.168.1.50")
    assert res_detail.status_code == 200
    assert res_detail.json()["source_ip"] == "192.168.1.50"

    res_404 = client.get("/api/attackers/99.99.99.99")
    assert res_404.status_code == 404


def test_alerts_endpoint(client, mock_service):
    # Trigger an alert
    mock_service.create_alert(
        session_id="s_alert",
        source_ip="1.2.3.4",
        timestamp=datetime.now(timezone.utc),
        severity=RiskSeverity.CRITICAL,
        risk_score=80,
        intent=IntentCategory.EXPLOITATION,
        attack_stage=AttackStage.EXECUTION,
        reason="Remote exploit attempt detected"
    )

    res = client.get("/api/alerts")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["risk_score"] == 80
    assert data["items"][0]["status"] == "OPEN"
