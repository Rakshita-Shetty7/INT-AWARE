"""
End-to-End Pipeline test: Raw JSON -> Pipeline -> MongoDB -> FastAPI REST API.
"""

from datetime import datetime, timezone
import json
from fastapi.testclient import TestClient
import mongomock
import pytest

from backend.app.api.dependencies import get_persistence_service
from backend.app.main import app
from backend.app.pipeline import DeceptionPipeline
from backend.app.services.event_normalizer import EventNormalizer
from backend.app.services.persistence_service import PersistenceService


@pytest.fixture
def mock_service():
    client = mongomock.MongoClient()
    db = client["test_e2e_db"]
    return PersistenceService(db=db)


def test_e2e_pipeline_processing_and_api_query(tmp_path, mock_service):
    # Setup temporary cowrie.json log
    log_file = tmp_path / "cowrie.json"

    # Real Cowrie command event JSON
    cowrie_event = {
        "eventid": "cowrie.command.input",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session": "sess_e2e_99",
        "src_ip": "172.16.0.45",
        "src_port": 49152,
        "protocol": "ssh",
        "username": "admin",
        "input": "uname -a"
    }
    log_file.write_text(json.dumps(cowrie_event) + "\n", encoding="utf-8")

    # Create pipeline with mock persistence and no remote Gemini calls during quick unit test
    pipeline = DeceptionPipeline(
        log_path=str(log_file),
        from_beginning=True,
        persistence_service=mock_service,
        enable_gemini=False
    )

    # Ingest event directly through the normalizer and aggregator
    line = json.dumps(cowrie_event)
    norm_event = EventNormalizer.normalize(line)
    assert norm_event is not None
    sess_features = pipeline.aggregator.add_event(norm_event)
    pipeline.process_event(norm_event, sess_features)

    # Verify MongoDB received the event
    saved_event = mock_service.get_event(norm_event.event_id)
    assert saved_event is not None
    assert saved_event["intent"] == "RECONNAISSANCE"
    assert saved_event["command"] == "uname -a"

    # Verify FastAPI REST API returns the event and session
    app.dependency_overrides[get_persistence_service] = lambda: mock_service
    with TestClient(app) as client:
        # Event detail query
        res_ev = client.get(f"/api/events/{norm_event.event_id}")
        assert res_ev.status_code == 200
        data_ev = res_ev.json()
        assert data_ev["intent"] == "RECONNAISSANCE"
        assert data_ev["source_ip"] == "172.16.0.45"

        # Session detail query
        res_sess = client.get("/api/sessions/sess_e2e_99")
        assert res_sess.status_code == 200
        data_sess = res_sess.json()
        assert data_sess["dominant_intent"] == "RECONNAISSANCE"
        assert data_sess["total_events"] == 1

        # Dashboard stats query
        res_stats = client.get("/api/dashboard/stats")
        assert res_stats.status_code == 200
        data_stats = res_stats.json()
        assert data_stats["total_sessions"] == 1
        assert data_stats["total_events"] == 1

    app.dependency_overrides.clear()
