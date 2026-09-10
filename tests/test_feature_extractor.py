"""
Unit tests for FeatureExtractor service.
"""

from datetime import datetime, timedelta, timezone
import pytest

from backend.app.models.events import NormalizedEvent
from backend.app.services.feature_extractor import FeatureExtractor


def test_extract_event_features_with_command():
    dt = datetime(2026, 8, 19, 16, 42, 10, tzinfo=timezone.utc)
    event = NormalizedEvent(
        event_id="ev_01",
        timestamp=dt,
        session_id="sess_01",
        event_type="command_input",
        command="cat /etc/passwd | grep root"
    )
    features = FeatureExtractor.extract_event_features(event)
    assert features.has_command is True
    assert features.command == "cat /etc/passwd | grep root"
    assert features.command_length == len("cat /etc/passwd | grep root")
    assert features.command_token_count == 5
    assert features.event_type == "command_input"


def test_extract_event_features_no_command():
    dt = datetime(2026, 8, 19, 16, 42, 8, tzinfo=timezone.utc)
    event = NormalizedEvent(
        event_id="ev_02",
        timestamp=dt,
        session_id="sess_01",
        event_type="session_connect"
    )
    features = FeatureExtractor.extract_event_features(event)
    assert features.has_command is False
    assert features.command is None
    assert features.command_length == 0
    assert features.command_token_count == 0


def test_compute_session_features():
    t0 = datetime(2026, 8, 19, 16, 42, 0, tzinfo=timezone.utc)
    t1 = t0 + timedelta(seconds=2)
    t2 = t0 + timedelta(seconds=5)
    t3 = t0 + timedelta(seconds=10)

    events = [
        NormalizedEvent(
            event_id="e1",
            timestamp=t0,
            session_id="s1",
            source_ip="10.0.0.5",
            protocol="ssh",
            event_type="session_connect"
        ),
        NormalizedEvent(
            event_id="e2",
            timestamp=t1,
            session_id="s1",
            source_ip="10.0.0.5",
            username="admin",
            event_type="login_success"
        ),
        NormalizedEvent(
            event_id="e3",
            timestamp=t2,
            session_id="s1",
            source_ip="10.0.0.5",
            event_type="command_input",
            command="whoami"
        ),
        NormalizedEvent(
            event_id="e4",
            timestamp=t3,
            session_id="s1",
            source_ip="10.0.0.5",
            event_type="command_input",
            command="uname -a"
        )
    ]

    sf = FeatureExtractor.compute_session_features("s1", events)
    assert sf.session_id == "s1"
    assert sf.source_ip == "10.0.0.5"
    assert sf.username == "admin"
    assert sf.total_events == 4
    assert sf.command_count == 2
    assert sf.unique_command_count == 2
    assert sf.unique_commands == ["whoami", "uname -a"]
    assert sf.duration_seconds == 10.0
    assert sf.command_intervals == [5.0]
    assert sf.average_command_interval == 5.0
    assert sf.login_success_count == 1
    assert sf.login_attempt_count == 1
    assert sf.distinct_event_types_count == 3
    assert sf.activity_rate == 0.4  # 4 events / 10s
