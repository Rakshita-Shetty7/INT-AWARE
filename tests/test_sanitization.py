"""
Unit tests for data sanitization prior to LLM submission.
"""

from datetime import datetime, timezone
import json
import pytest

from backend.app.models.events import NormalizedEvent
from backend.app.services.gemini_classifier import GeminiClassifier


def test_sanitize_payload_excludes_passwords_and_raw_secrets():
    ev = NormalizedEvent(
        event_id="e_secret",
        timestamp=datetime.now(timezone.utc),
        session_id="s_secret",
        event_type="login_failed",
        username="root",
        command="mysql -u root -p SuperSecretPassword123",
        raw_event={
            "session": "s_secret",
            "username": "root",
            "password": "SuperSecretPassword123",
            "eventid": "cowrie.login.failed"
        }
    )

    payload = GeminiClassifier.sanitize_payload(ev)
    payload_json = json.dumps(payload)

    # Must NOT contain the plain password anywhere in the sanitized payload
    assert "SuperSecretPassword123" not in payload_json
    assert "[REDACTED]" in payload["command"]
    assert "password" not in payload
