"""
Phase B Intelligence and Cyber Deception Engine Tests.

Validates:
  1. Epistemic uncertainty estimation & Shannon prediction entropy.
  2. Out-of-distribution (OOD) novelty detection & calibrated abstention.
  3. Markov sequence transition modeling & next-intent probability projections.
  4. Sequence anomaly detection on erratic kill-chain leaps.
  5. Safe adaptive deception engine (zero host execution, honeytokens, tar-pitting).
  6. Deception & Sequence REST APIs (/api/deception/*).
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock
import mongomock
import pytest
from fastapi.testclient import TestClient

from backend.app.api.dependencies import get_persistence_service
from backend.app.main import app
from backend.app.models.events import NormalizedEvent
from backend.app.models.features import SessionFeatures
from backend.app.models.intent import AttackStage, IntentCategory
from backend.app.services.adaptive_deception_engine import (
    AdaptiveDeceptionEngine,
    DeceptionStrategy,
    adaptive_deception_engine,
)
from backend.app.services.sequence_transition_engine import (
    SequenceTransitionEngine,
    sequence_transition_engine,
)
from backend.app.services.persistence_service import PersistenceService


# ---------------------------------------------------------------------------
# 1. Uncertainty & Novelty Detection Tests
# ---------------------------------------------------------------------------

class TestUncertaintyAndNoveltyDetection:
    """Verifies entropy, novelty detection, and abstention recommendation."""

    def test_ml_classifier_computes_entropy_and_novelty(self):
        from backend.app.ml.intent_ml_classifier import MLIntentClassifier
        clf = MLIntentClassifier()
        if not clf.available:
            pytest.skip("ML model artifact unavailable")

        # Standard in-distribution command
        res_normal = clf.classify("cat /etc/passwd")
        assert res_normal is not None
        assert res_normal.entropy >= 0.0
        assert 0.0 <= res_normal.novelty_score <= 1.0

        # Obfuscated / novel command
        res_novel = clf.classify("zxcvbqwerty987123xyz --unknown-flag-alpha-omega")
        assert res_novel is not None
        assert res_novel.entropy > 0.0
        assert res_novel.novelty_score > 0.0

    def test_hybrid_classifier_propagates_uncertainty(self):
        from backend.app.services.hybrid_classifier import HybridClassifier
        hybrid = HybridClassifier()

        ev = NormalizedEvent(
            event_id="ev_novel_test",
            timestamp=datetime.now(timezone.utc),
            session_id="sess_novel",
            source_ip="192.168.1.100",
            source_port=5555,
            protocol="ssh",
            username="root",
            event_type="command_input",
            command="some_completely_unseen_custom_malware_launcher_binary_xyz",
            raw_event={},
        )
        classification = hybrid.classify(ev)
        assert classification is not None
        assert 0.0 <= classification.uncertainty_score <= 1.0
        assert isinstance(classification.is_novel, bool)
        assert isinstance(classification.should_abstain, bool)


# ---------------------------------------------------------------------------
# 2. Sequence Transition & Next-Intent Projection Tests
# ---------------------------------------------------------------------------

class TestSequenceTransitionEngine:
    """Verifies Markov sequence transitions and anomaly detection."""

    def setup_method(self):
        self.engine = SequenceTransitionEngine()

    def test_initial_session_transition(self):
        analysis = self.engine.evaluate_transition(
            current_intent=IntentCategory.RECONNAISSANCE,
            intent_history=[],
        )
        assert analysis.previous_intent is None
        assert analysis.is_anomalous_transition is False
        assert analysis.sequence_anomaly_score == 0.0
        assert len(analysis.predicted_next_intents) > 0
        # Expected next intents after Reconnaissance
        predicted_names = [p.intent.value for p in analysis.predicted_next_intents]
        assert "DISCOVERY" in predicted_names or "RECONNAISSANCE" in predicted_names

    def test_consistent_kill_chain_progression(self):
        analysis = self.engine.evaluate_transition(
            current_intent=IntentCategory.DISCOVERY,
            intent_history=[IntentCategory.RECONNAISSANCE],
        )
        assert analysis.previous_intent == IntentCategory.RECONNAISSANCE
        assert analysis.is_anomalous_transition is False
        assert analysis.transition_probability >= 0.15

    def test_anomalous_kill_chain_leap(self):
        # Reconnaissance straight to Cleanup without any execution/priv-esc
        analysis = self.engine.evaluate_transition(
            current_intent=IntentCategory.CLEANUP,
            intent_history=[IntentCategory.RECONNAISSANCE],
        )
        assert analysis.is_anomalous_transition is True
        assert analysis.sequence_anomaly_score >= 0.8
        assert any("Abrupt transition" in e for e in analysis.evidence)

    def test_rapid_script_pacing_detection(self):
        delays = [0.2, 0.15, 0.18, 0.22]
        analysis = self.engine.evaluate_transition(
            current_intent=IntentCategory.EXECUTION,
            intent_history=[IntentCategory.RECONNAISSANCE, IntentCategory.DISCOVERY],
            inter_command_delays=delays,
        )
        assert analysis.progression_pace == "RAPID"
        assert any("Automated script execution" in e for e in analysis.evidence)


# ---------------------------------------------------------------------------
# 3. Safe Adaptive Deception Engine Tests
# ---------------------------------------------------------------------------

class TestAdaptiveDeceptionEngine:
    """Verifies deception synthesis and zero-host-execution safety."""

    def setup_method(self):
        self.engine = AdaptiveDeceptionEngine()

    def test_reconnaissance_emulation(self):
        decision = self.engine.select_deception_response(
            command="uname -a",
            intent=IntentCategory.RECONNAISSANCE,
            attack_stage=AttackStage.RECONNAISSANCE,
            session_id="test_sess_01",
        )
        assert decision.strategy == DeceptionStrategy.SIMULATED_SUCCESS
        assert "Linux" in decision.decoy_payload
        assert decision.delay_ms < 100

    def test_credential_access_honeytoken_injection(self):
        decision = self.engine.select_deception_response(
            command="cat /etc/shadow",
            intent=IntentCategory.CREDENTIAL_ACCESS,
            attack_stage=AttackStage.CREDENTIAL_ACCESS,
            session_id="test_sess_01",
        )
        assert decision.strategy == DeceptionStrategy.HONEYTOKEN_INJECTION
        assert len(decision.honeytokens_injected) > 0
        assert "CANARY" in decision.decoy_payload

    def test_discovery_decoy_artifact(self):
        decision = self.engine.select_deception_response(
            command="ls -la /var/www",
            intent=IntentCategory.DISCOVERY,
            attack_stage=AttackStage.DISCOVERY,
            session_id="test_sess_01",
        )
        assert decision.strategy == DeceptionStrategy.DECOY_ARTIFACT
        assert "backup_credentials" in decision.decoy_payload
        assert len(decision.honeytokens_injected) > 0

    def test_execution_tarpit_delay(self):
        decision = self.engine.select_deception_response(
            command="./malware_loader.sh",
            intent=IntentCategory.EXECUTION,
            attack_stage=AttackStage.EXECUTION,
            session_id="test_sess_01",
            risk_score=80,
        )
        assert decision.strategy == DeceptionStrategy.TARPIT_DELAY
        assert decision.delay_ms >= 200


# ---------------------------------------------------------------------------
# 4. Deception REST Router Tests
# ---------------------------------------------------------------------------

class TestDeceptionRouter:
    """Verifies REST endpoints for Deception & Sequence Intelligence."""

    @pytest.fixture
    def client(self):
        client = mongomock.MongoClient()
        db = client["test_phase_b_db"]
        mock_p = PersistenceService(db=db)
        app.dependency_overrides[get_persistence_service] = lambda: mock_p
        with TestClient(app) as c:
            yield c
        app.dependency_overrides.clear()

    def test_get_policies(self, client):
        resp = client.get("/api/deception/policies")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 4
        assert any(p["policy_id"] == "POL_RECON_EMULATION" for p in data)

    def test_simulate_deception(self, client):
        payload = {
            "command": "cat /etc/shadow",
            "intent": "CREDENTIAL_ACCESS",
            "attack_stage": "CREDENTIAL_ACCESS",
            "session_id": "sim_s1",
            "risk_score": 50,
        }
        resp = client.post("/api/deception/simulate", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["strategy"] == "HONEYTOKEN_INJECTION"
        assert len(data["honeytokens_injected"]) > 0

    def test_get_transition_matrix(self, client):
        resp = client.get("/api/deception/transitions/matrix")
        assert resp.status_code == 200
        data = resp.json()
        assert "RECONNAISSANCE" in data
        assert "DISCOVERY" in data["RECONNAISSANCE"]

    def test_evaluate_sequence_transition(self, client):
        payload = {
            "current_intent": "CLEANUP",
            "intent_history": ["RECONNAISSANCE"],
            "inter_command_delays": [1.0],
        }
        resp = client.post("/api/deception/transitions/evaluate", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_anomalous_transition"] is True
        assert len(data["predicted_next_intents"]) > 0
