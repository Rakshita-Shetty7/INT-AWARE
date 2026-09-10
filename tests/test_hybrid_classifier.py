"""
Unit tests for HybridClassifier service.

The hybrid classifier arbitrates three sources — deterministic rules, the trained
ML model, and (optionally) Gemini. To keep each test deterministic we inject a
controlled ML stub rather than depending on whatever the real model predicts:

  * ``_unavailable_ml()`` simulates a missing model artifact (available == False),
    letting us verify the rule + Gemini degradation contract in isolation.
  * ``_StubML`` returns a fixed MLClassification so the ML arbitration branches
    can be exercised precisely.
"""

from datetime import datetime, timezone
import json
from unittest.mock import MagicMock
import pytest

from backend.app.models.events import NormalizedEvent
from backend.app.models.intent import (
    AttackStage,
    ClassificationSource,
    IntentCategory,
    MLClassification,
)
from backend.app.services.gemini_classifier import GeminiClassifier
from backend.app.services.hybrid_classifier import HybridClassifier
from backend.app.services.rule_classifier import RuleClassifier


def make_event(command: str) -> NormalizedEvent:
    return NormalizedEvent(
        event_id="test_ev_hyb",
        timestamp=datetime.now(timezone.utc),
        session_id="test_sess_hyb",
        event_type="command_input",
        command=command,
    )


class _StubML:
    """Deterministic stand-in for MLIntentClassifier."""

    def __init__(self, result, available=True):
        self._result = result
        self.available = available

    def classify(self, command):
        return self._result if self.available else None


def _unavailable_ml():
    """An ML classifier that behaves as if no model artifact is present."""
    return _StubML(None, available=False)


def _ml(intent: IntentCategory, stage: AttackStage, confidence: float) -> _StubML:
    return _StubML(
        MLClassification(
            intent=intent,
            attack_stage=stage,
            confidence=confidence,
            model_name="stub",
            top_predictions=[{"intent": intent.value, "probability": confidence}],
            evidence=[f"stub predicted {intent.value} @ {confidence}"],
        )
    )


# --------------------------------------------------------------------------- #
# Rule + Gemini behaviour, ML deliberately absent (degradation contract)
# --------------------------------------------------------------------------- #
def test_rule_only_path_when_ml_and_gemini_absent():
    hybrid = HybridClassifier(
        rule_classifier=RuleClassifier(),
        gemini_classifier=GeminiClassifier(enabled=False),
        ml_classifier=_unavailable_ml(),
    )
    res = hybrid.classify(make_event("whoami"))
    assert res.intent == IntentCategory.RECONNAISSANCE
    assert res.attack_stage == AttackStage.RECONNAISSANCE
    assert res.source == ClassificationSource.RULE
    assert len(res.rule_evidence) > 0
    assert res.ml_intent is None


def test_strong_rule_signature_is_authoritative():
    hybrid = HybridClassifier(
        rule_classifier=RuleClassifier(),
        gemini_classifier=GeminiClassifier(enabled=False),
        ml_classifier=_unavailable_ml(),
    )
    # RULE_CRED_02 is a 0.95-confidence signature (>= 0.90 threshold).
    res = hybrid.classify(make_event("cat /root/.ssh/id_rsa"))
    assert res.intent == IntentCategory.CREDENTIAL_ACCESS
    assert res.source == ClassificationSource.RULE
    assert res.confidence >= 0.90


def test_gemini_invoked_when_rule_weak_and_ml_absent():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "intent": "EXPLOITATION",
        "attack_stage": "EXECUTION",
        "confidence": 0.94,
        "reason": "Obfuscated shell payload exploiting memory bug",
        "evidence": ["base64 payload", "eval loop"],
    })
    mock_client.models.generate_content.return_value = mock_response

    hybrid = HybridClassifier(
        rule_classifier=RuleClassifier(),
        gemini_classifier=GeminiClassifier(api_key="valid", enabled=True, client=mock_client),
        ml_classifier=_unavailable_ml(),
    )
    res = hybrid.classify(make_event("eval $(echo aGVsbG8= | base64 -d)"))
    assert res.intent == IntentCategory.EXPLOITATION
    assert res.attack_stage == AttackStage.EXECUTION
    assert res.source in (ClassificationSource.GEMINI, ClassificationSource.HYBRID)
    assert res.ai_reason is not None


def test_graceful_fallback_when_gemini_fails_and_ml_absent():
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("503 Service Unavailable")

    hybrid = HybridClassifier(
        rule_classifier=RuleClassifier(),
        gemini_classifier=GeminiClassifier(api_key="valid", enabled=True, client=mock_client),
        ml_classifier=_unavailable_ml(),
        rule_confidence_threshold=0.99,  # force the Gemini attempt
    )
    res = hybrid.classify(make_event("id"))
    assert res.intent == IntentCategory.RECONNAISSANCE
    assert res.source == ClassificationSource.FALLBACK
    assert len(res.rule_evidence) > 0


# --------------------------------------------------------------------------- #
# ML arbitration branches
# --------------------------------------------------------------------------- #
def test_ml_confident_path_sets_ml_source():
    # A command with no rule signature; ML is confident -> ML source.
    hybrid = HybridClassifier(
        rule_classifier=RuleClassifier(),
        gemini_classifier=GeminiClassifier(enabled=False),
        ml_classifier=_ml(IntentCategory.DISCOVERY, AttackStage.DISCOVERY, 0.90),
    )
    res = hybrid.classify(make_event("nmap -sV 10.0.0.1"))
    assert res.intent == IntentCategory.DISCOVERY
    assert res.source == ClassificationSource.ML
    assert res.ml_intent == IntentCategory.DISCOVERY
    assert res.ml_confidence == pytest.approx(0.90, abs=1e-6)


def test_rule_and_ml_agreement_yields_hybrid():
    # whoami: rule fires RECON@0.88 (< 0.90 threshold), ML agrees -> HYBRID.
    hybrid = HybridClassifier(
        rule_classifier=RuleClassifier(),
        gemini_classifier=GeminiClassifier(enabled=False),
        ml_classifier=_ml(IntentCategory.RECONNAISSANCE, AttackStage.RECONNAISSANCE, 0.90),
    )
    res = hybrid.classify(make_event("whoami"))
    assert res.intent == IntentCategory.RECONNAISSANCE
    assert res.source == ClassificationSource.HYBRID
    assert res.confidence >= 0.88  # max(rule, ml)
    assert res.ml_intent == IntentCategory.RECONNAISSANCE


def test_confident_ml_suppresses_gemini():
    # ML is confident, so Gemini must NOT be consulted (keeps it optional / cheap).
    mock_client = MagicMock()
    hybrid = HybridClassifier(
        rule_classifier=RuleClassifier(),
        gemini_classifier=GeminiClassifier(api_key="valid", enabled=True, client=mock_client),
        ml_classifier=_ml(IntentCategory.EXECUTION, AttackStage.EXECUTION, 0.85),
    )
    res = hybrid.classify(make_event("some novel dropper command"))
    assert res.intent == IntentCategory.EXECUTION
    assert res.source in (ClassificationSource.ML, ClassificationSource.HYBRID)
    mock_client.models.generate_content.assert_not_called()


def test_low_confidence_ml_defers_to_gemini():
    # ML below threshold + weak rule -> Gemini is consulted and wins.
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "intent": "PERSISTENCE",
        "attack_stage": "PERSISTENCE",
        "confidence": 0.9,
        "reason": "installs a backdoor service",
        "evidence": ["service install"],
    })
    mock_client.models.generate_content.return_value = mock_response

    hybrid = HybridClassifier(
        rule_classifier=RuleClassifier(),
        gemini_classifier=GeminiClassifier(api_key="valid", enabled=True, client=mock_client),
        ml_classifier=_ml(IntentCategory.OTHER, AttackStage.UNKNOWN, 0.20),  # below 0.40
    )
    res = hybrid.classify(make_event("weird novel thing"))
    assert res.source in (ClassificationSource.GEMINI, ClassificationSource.HYBRID)
    assert res.intent == IntentCategory.PERSISTENCE
    mock_client.models.generate_content.assert_called_once()
