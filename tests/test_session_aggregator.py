"""
Unit tests for SessionAggregator service.
"""

from datetime import datetime, timezone
import pytest

from backend.app.models.events import NormalizedEvent
from backend.app.services.session_aggregator import SessionAggregator


def test_session_aggregator_incremental_updates():
    aggregator = SessionAggregator()
    t0 = datetime(2026, 8, 19, 16, 42, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 8, 19, 16, 42, 3, tzinfo=timezone.utc)

    # Event 1: Connect
    ev1 = NormalizedEvent(
        event_id="ev_01",
        timestamp=t0,
        session_id="sess_alpha",
        source_ip="192.168.1.50",
        event_type="session_connect"
    )
    s1 = aggregator.add_event(ev1)
    assert s1.total_events == 1
    assert s1.command_count == 0
    assert s1.duration_seconds == 0.0

    # Event 2: Command
    ev2 = NormalizedEvent(
        event_id="ev_02",
        timestamp=t1,
        session_id="sess_alpha",
        source_ip="192.168.1.50",
        event_type="command_input",
        command="id"
    )
    s2 = aggregator.add_event(ev2)
    assert s2.total_events == 2
    assert s2.command_count == 1
    assert s2.unique_commands == ["id"]
    assert s2.duration_seconds == 3.0


def test_session_aggregator_multi_session_isolation():
    aggregator = SessionAggregator()
    t0 = datetime(2026, 8, 19, 16, 42, 0, tzinfo=timezone.utc)

    ev_a = NormalizedEvent(
        event_id="ev_a1",
        timestamp=t0,
        session_id="session_A",
        source_ip="1.1.1.1",
        event_type="command_input",
        command="whoami"
    )
    ev_b = NormalizedEvent(
        event_id="ev_b1",
        timestamp=t0,
        session_id="session_B",
        source_ip="2.2.2.2",
        event_type="command_input",
        command="curl evil.com"
    )

    aggregator.add_event(ev_a)
    aggregator.add_event(ev_b)

    sess_a = aggregator.get_session("session_A")
    sess_b = aggregator.get_session("session_B")

    assert sess_a is not None and sess_b is not None
    assert sess_a.source_ip == "1.1.1.1"
    assert sess_b.source_ip == "2.2.2.2"
    assert sess_a.commands == ["whoami"]
    assert sess_b.commands == ["curl evil.com"]
    assert len(aggregator.get_all_sessions()) == 2


def test_session_aggregator_duplicate_prevention():
    aggregator = SessionAggregator()
    t0 = datetime(2026, 8, 19, 16, 42, 0, tzinfo=timezone.utc)

    ev1 = NormalizedEvent(
        event_id="ev_dup_01",
        timestamp=t0,
        session_id="sess_dup",
        event_type="command_input",
        command="whoami"
    )

    s1 = aggregator.add_event(ev1)
    s2 = aggregator.add_event(ev1)  # Re-adding exact duplicate

    assert s1.total_events == 1
    assert s2.total_events == 1
    assert len(aggregator.get_session_events("sess_dup")) == 1
