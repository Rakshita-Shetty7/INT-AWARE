"""
Unit tests for GeminiClassifier service using mocked official google-genai responses.
"""

from datetime import datetime, timezone
import json
from unittest.mock import MagicMock
import pytest

from backend.app.models.events import NormalizedEvent
from backend.app.models.intent import AttackStage, GeminiClassification, IntentCategory
from backend.app.services.gemini_classifier import GeminiClassifier


def make_event(command: str = "custom_tool -scan") -> NormalizedEvent:
    return NormalizedEvent(
        event_id="test_ev_gemini",
        timestamp=datetime.now(timezone.utc),
        session_id="test_sess_gemini",
        event_type="command_input",
        command=command
    )


def test_gemini_successful_structured_response():
    # Mock client and response
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "intent": "DISCOVERY",
        "attack_stage": "DISCOVERY",
        "confidence": 0.88,
        "reason": "Command custom_tool -scan is enumerating system services",
        "evidence": ["custom_tool invocation", "scan flag passed"]
    })
    mock_client.models.generate_content.return_value = mock_response

    classifier = GeminiClassifier(api_key="valid_key", enabled=True, client=mock_client)
    res = classifier.classify(make_event())

    assert res is not None
    assert isinstance(res, GeminiClassification)
    assert res.intent == IntentCategory.DISCOVERY
    assert res.attack_stage == AttackStage.DISCOVERY
    assert res.confidence == 0.88
    assert "enumerating" in res.reason


def test_gemini_malformed_json_response():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "NOT JSON RESPONSE"
    mock_client.models.generate_content.return_value = mock_response

    classifier = GeminiClassifier(api_key="valid_key", enabled=True, client=mock_client)
    res = classifier.classify(make_event())

    # Must return None safely without crashing
    assert res is None


def test_gemini_api_exception_handling():
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = RuntimeError("API connection timeout")

    classifier = GeminiClassifier(api_key="valid_key", enabled=True, client=mock_client)
    res = classifier.classify(make_event())

    # Must return None safely without raising exception
    assert res is None


def test_gemini_disabled_or_missing_key():
    classifier = GeminiClassifier(api_key="", enabled=False)
    res = classifier.classify(make_event())
    assert res is None
