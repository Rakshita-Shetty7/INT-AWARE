"""
Tests for Phase 7 Attacker Intelligence, AI Session Analysis, MITRE ATT&CK Mapping, and Advanced Analytics.

The API-level tests here use an in-memory MongoDB (mongomock) with a seeded session
so they are fully deterministic and do not depend on a live database or ingested data.
"""

from datetime import datetime, timezone

import mongomock
import pytest
from fastapi.testclient import TestClient

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
from backend.app.services.gemini_session_analyst import GeminiSessionAnalyst
from backend.app.services.mitre_mapper import MitreMapper
from backend.app.services.persistence_service import PersistenceService


# --------------------------------------------------------------------------- #
# Fixtures & seeding                                                          #
# --------------------------------------------------------------------------- #
@pytest.fixture
def mock_service():
    client = mongomock.MongoClient()
    db = client["test_phase7_db"]
    return PersistenceService(db=db)


@pytest.fixture
def client(mock_service):
    app.dependency_overrides[get_persistence_service] = lambda: mock_service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def seed_session(service: PersistenceService, session_id: str = "s_phase7") -> str:
    """Seeds one multi-stage attacker session (recon -> discovery -> credential access)."""
    steps = [
        ("uname -a", IntentCategory.RECONNAISSANCE, AttackStage.RECONNAISSANCE, 10, RiskSeverity.LOW),
        ("cat /etc/passwd", IntentCategory.DISCOVERY, AttackStage.DISCOVERY, 40, RiskSeverity.MEDIUM),
        ("cat /etc/shadow", IntentCategory.CREDENTIAL_ACCESS, AttackStage.CREDENTIAL_ACCESS, 80, RiskSeverity.CRITICAL),
    ]
    for i, (cmd, intent, stage, score, severity) in enumerate(steps):
        ev = NormalizedEvent(
            event_id=f"{session_id}_e{i}",
            timestamp=datetime(2026, 8, 19, 10, i, 0, tzinfo=timezone.utc),
            session_id=session_id,
            source_ip="10.10.10.5",
            event_type="command_input",
            command=cmd,
        )
        cls = HybridClassification(
            intent=intent,
            attack_stage=stage,
            confidence=0.92,
            source=ClassificationSource.RULE,
            rule_evidence=[cmd],
            timestamp=datetime.now(timezone.utc),
        )
        risk = RiskAssessment(risk_score=score, severity=severity, contributing_factors=[])
        service.save_event(ev, cls, risk)

    sess_intel = SessionIntelligence(
        session_id=session_id,
        source_ip="10.10.10.5",
        dominant_intent=IntentCategory.CREDENTIAL_ACCESS,
        current_attack_stage=AttackStage.CREDENTIAL_ACCESS,
        risk_score=80,
        severity=RiskSeverity.CRITICAL,
        last_updated=datetime.now(timezone.utc),
    )
    service.update_session(sess_intel, SessionFeatures(session_id=session_id, total_events=len(steps)))
    return session_id


# --------------------------------------------------------------------------- #
# Pure-unit tests (no DB)                                                      #
# --------------------------------------------------------------------------- #
def test_mitre_mapper_techniques_for_intent():
    rec_techs = MitreMapper.get_techniques_for_intent("RECONNAISSANCE")
    assert len(rec_techs) > 0
    assert any(t["technique_id"] == "T1592" for t in rec_techs)
    assert rec_techs[0]["tactic"] == "Reconnaissance"

    disc_techs = MitreMapper.get_techniques_for_intent("DISCOVERY")
    assert len(disc_techs) > 0
    assert any(t["technique_id"] == "T1082" for t in disc_techs)


def test_mitre_mapper_session_mapping():
    session_doc = {
        "session_id": "test_sess_mitre_01",
        "dominant_intent": "CREDENTIAL_ACCESS",
        "intent_sequence": ["RECONNAISSANCE", "DISCOVERY", "CREDENTIAL_ACCESS"]
    }
    events = [
        {"command": "whoami", "intent": "RECONNAISSANCE"},
        {"command": "cat /etc/passwd", "intent": "DISCOVERY"},
        {"command": "cat /etc/shadow", "intent": "CREDENTIAL_ACCESS"}
    ]
    mapped = MitreMapper.map_session(session_doc, events)
    tech_ids = [t["technique_id"] for t in mapped]
    assert "T1592" in tech_ids or "T1082" in tech_ids or "T1003" in tech_ids


def test_gemini_session_analyst_deterministic_fallback():
    analyst = GeminiSessionAnalyst(enabled=False)
    session_doc = {
        "session_id": "sess_det_001",
        "dominant_intent": "DISCOVERY",
        "current_attack_stage": "DISCOVERY",
        "risk_score": 35,
        "source_ip": "10.10.10.5",
        "command_count": 3,
        "unique_commands": ["ls -la", "uname -a", "id"],
        "key_evidence": ["OS version fingerprinting"]
    }
    events = [
        {"timestamp": datetime.now(timezone.utc).isoformat(), "command": "uname -a", "intent": "RECONNAISSANCE"},
        {"timestamp": datetime.now(timezone.utc).isoformat(), "command": "ls -la", "intent": "DISCOVERY"},
    ]
    report = analyst.analyze_session(session_doc, events)
    assert report.session_id == "sess_det_001"
    assert report.source == "DETERMINISTIC_ANALYST"
    assert len(report.objective) > 0
    assert len(report.summary) > 0
    assert len(report.recommended_action) > 0


# --------------------------------------------------------------------------- #
# API-level tests (mongomock + dependency override + seeded session)          #
# --------------------------------------------------------------------------- #
def test_api_session_analyze_and_mitre_endpoints(client, mock_service):
    session_id = seed_session(mock_service)

    # 1. Session appears in the listing
    sessions_res = client.get("/api/sessions?limit=10")
    assert sessions_res.status_code == 200
    items = sessions_res.json()["items"]
    assert any(s["session_id"] == session_id for s in items)

    # 2. Analyze session
    analyze_res = client.post(f"/api/sessions/{session_id}/analyze")
    assert analyze_res.status_code == 200
    report = analyze_res.json()
    assert report["session_id"] == session_id
    assert "objective" in report
    assert "summary" in report
    assert "attack_progression" in report
    assert "threat_interpretation" in report
    assert "recommended_action" in report
    # Gemini is disabled by default (placeholder key) -> deterministic analyst.
    assert report["source"] in ["GEMINI_AI", "DETERMINISTIC_ANALYST"]

    # 3. MITRE mapping reflects the observed multi-stage behaviour
    mitre_res = client.get(f"/api/sessions/{session_id}/mitre")
    assert mitre_res.status_code == 200
    mitre_data = mitre_res.json()
    assert isinstance(mitre_data, list)
    assert len(mitre_data) > 0
    tech_ids = [t["technique_id"] for t in mitre_data]
    assert "T1592" in tech_ids or "T1082" in tech_ids or "T1003" in tech_ids


def test_api_session_analyze_not_found_returns_404(client):
    res = client.post("/api/sessions/does_not_exist/analyze")
    assert res.status_code == 404


def test_api_advanced_analytics_endpoints(client, mock_service):
    seed_session(mock_service)

    # Stages
    stages_res = client.get("/api/analytics/stages")
    assert stages_res.status_code == 200
    assert isinstance(stages_res.json(), list)

    # Risk distribution — always the 4 canonical buckets
    risk_dist_res = client.get("/api/analytics/risk-distribution")
    assert risk_dist_res.status_code == 200
    risk_data = risk_dist_res.json()
    assert len(risk_data) == 4
    assert risk_data[0]["range"].startswith("0-24")
    # Seeded session has risk_score 80 -> Critical bucket populated.
    critical_bucket = next(b for b in risk_data if b["range"].startswith("75-100"))
    assert critical_bucket["count"] == 1

    # Heatmap
    heatmap_res = client.get("/api/analytics/heatmap")
    assert heatmap_res.status_code == 200
    assert isinstance(heatmap_res.json(), list)


def test_api_risk_distribution_empty_db_returns_four_zeroed_buckets(client):
    """Even with no sessions, the dashboard chart must receive 4 stable buckets."""
    res = client.get("/api/analytics/risk-distribution")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 4
    assert all(b["count"] == 0 for b in data)
    assert all(b["percentage"] == 0.0 for b in data)
