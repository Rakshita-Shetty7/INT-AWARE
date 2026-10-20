"""
Unit tests for EventNormalizer service.
"""

from datetime import datetime, timezone
import pytest

from backend.app.services.event_normalizer import EventNormalizer


def test_normalize_valid_connect_event():
    raw = {
        "session": "test_sess_01",
        "protocol": "ssh",
        "src_ip": "192.168.1.100",
        "src_port": 54321,
        "dst_ip": "127.0.0.1",
        "dst_port": 2222,
        "eventid": "cowrie.session.connect",
        "timestamp": "2026-08-19T16:42:08.926448Z",
        "message": "New connection"
    }
    event = EventNormalizer.normalize(raw)
    assert event is not None
    assert event.session_id == "test_sess_01"
    assert event.event_type == "session_connect"
    assert event.source_ip == "192.168.1.100"
    assert event.source_port == 54321
    assert event.protocol == "ssh"
    assert event.command is None
    assert event.timestamp.year == 2026
    assert event.timestamp.tzinfo is not None


def test_normalize_valid_login_success_event():
    raw = {
        "session": "test_sess_01",
        "protocol": "ssh",
        "src_ip": "192.168.1.100",
        "username": "root",
        "password": "password123",
        "eventid": "cowrie.login.success",
        "timestamp": "2026-08-19T16:42:09.100000Z",
        "message": "login attempt [root/password123] succeeded"
    }
    event = EventNormalizer.normalize(raw)
    assert event is not None
    assert event.event_type == "login_success"
    assert event.username == "root"


def test_normalize_valid_command_event():
    raw_str = (
        '{"session":"test_sess_01","protocol":"ssh","src_ip":"192.168.1.100",'
        '"input":"uname -a","eventid":"cowrie.command.input",'
        '"timestamp":"2026-08-19T16:42:10.000000Z","message":"CMD: uname -a"}'
    )
    event = EventNormalizer.normalize(raw_str)
    assert event is not None
    assert event.event_type == "command_input"
    assert event.command == "uname -a"


def test_normalize_malformed_json():
    bad_json = '{"session":"test_sess_01", "eventid": "cowrie.command.input", UNTERMINATED'
    event = EventNormalizer.normalize(bad_json)
    assert event is None


def test_normalize_empty_or_whitespace_line():
    assert EventNormalizer.normalize("") is None
    assert EventNormalizer.normalize("   \n\t  ") is None


def test_normalize_missing_optional_fields():
    minimal = {
        "session": "test_sess_min",
        "eventid": "cowrie.session.connect"
    }
    event = EventNormalizer.normalize(minimal)
    assert event is not None
    assert event.session_id == "test_sess_min"
    assert event.source_ip is None
    assert event.source_port is None
    assert event.username is None
    assert event.command is None
    assert event.timestamp is not None


def test_deterministic_event_id():
    raw1 = {
        "session": "sess_100",
        "src_port": 1234,
        "input": "whoami",
        "eventid": "cowrie.command.input",
        "timestamp": "2026-08-19T16:42:10.000000Z",
        "message": "CMD: whoami"
    }
    raw2 = dict(raw1)
    ev1 = EventNormalizer.normalize(raw1)
    ev2 = EventNormalizer.normalize(raw2)
    assert ev1 is not None and ev2 is not None
    assert ev1.event_id == ev2.event_id
